from unittest.mock import MagicMock, patch
import requests
from reviewlift.agents.low_tier_reviewer import LowTierReviewerAgent
from reviewlift.agents.mid_tier_reviewer import MidTierReviewerAgent
from reviewlift.agents.advanced_reviewer import AdvancedReviewerAgent


def _ollama_response(findings_json, confidence):
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"response": f'{{"findings": {findings_json}, "confidence": {confidence}}}'}
    return mock_resp


def test_low_tier_parses_real_ollama_shaped_response():
    with patch("reviewlift.agents.low_tier_reviewer.requests.post") as post:
        post.return_value = _ollama_response(
            '[{"file": "a.py", "line": 2, "message": "bad name", "severity": "info"}]', 0.85
        )
        result = LowTierReviewerAgent().review("some diff")
    assert result.model_used == "low_tier"
    assert result.confidence == 0.85
    assert result.cost_usd == 0.0
    assert len(result.findings) == 1


def test_low_tier_handles_ollama_down_gracefully():
    with patch("reviewlift.agents.low_tier_reviewer.requests.post") as post:
        post.side_effect = requests.ConnectionError("connection refused")
        result = LowTierReviewerAgent().review("some diff")
    assert result.model_used == "low_tier_error"
    assert result.confidence == 0.0


def test_mid_tier_parses_real_ollama_shaped_response():
    with patch("reviewlift.agents.mid_tier_reviewer.requests.post") as post:
        post.return_value = _ollama_response("[]", 0.6)
        result = MidTierReviewerAgent().review("some diff")
    assert result.model_used == "mid_tier"
    assert result.confidence == 0.6


def test_mid_tier_handles_timeout_gracefully():
    with patch("reviewlift.agents.mid_tier_reviewer.requests.post") as post:
        post.side_effect = requests.Timeout("took too long")
        result = MidTierReviewerAgent().review("some diff")
    assert result.model_used == "mid_tier_error"


def test_advanced_tier_computes_real_cost_from_token_usage():
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text='{"findings": [], "confidence": 0.95}')]
    mock_message.usage.input_tokens = 500
    mock_message.usage.output_tokens = 100
    with patch("reviewlift.agents.advanced_reviewer._get_client") as get_client:
        get_client.return_value.messages.create.return_value = mock_message
        result = AdvancedReviewerAgent().review("some diff touching auth")
    assert result.model_used == "advanced"
    expected_cost = (500 / 1_000_000) * 1.00 + (100 / 1_000_000) * 5.00
    assert result.cost_usd == expected_cost


def test_advanced_tier_missing_api_key_fails_gracefully():
    with patch("reviewlift.agents.advanced_reviewer._get_client") as get_client:
        get_client.side_effect = RuntimeError("ANTHROPIC_API_KEY is not set.")
        result = AdvancedReviewerAgent().review("some diff")
    assert result.model_used == "advanced_error"
    assert result.cost_usd == 0.0