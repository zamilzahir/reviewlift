from unittest.mock import patch
import pytest
from reviewlift.cli import run_review
from reviewlift.core.models import ReviewResult
from reviewlift.memory.store import MemoryStore


def test_run_review_raises_value_error_on_empty_diff():
    with patch("reviewlift.cli.get_diff", return_value=""):
        with pytest.raises(ValueError):
            run_review("pr1", MemoryStore())


def test_run_review_saves_result_to_memory():
    with patch("reviewlift.cli.get_diff", return_value="diff --git a/x.py b/x.py"), \
         patch("reviewlift.agents.low_tier_reviewer.LowTierReviewerAgent.review") as low:
        low.return_value = ReviewResult(confidence=0.9, model_used="low_tier", cost_usd=0.0, seconds_elapsed=0.1)
        memory = MemoryStore()
        output = run_review("pr1", memory)
    assert output["pr_id"] == "pr1"
    assert memory.get("pr1") == output


def test_run_review_output_includes_trace_summary():
    with patch("reviewlift.cli.get_diff", return_value="diff --git a/x.py b/x.py"), \
         patch("reviewlift.agents.low_tier_reviewer.LowTierReviewerAgent.review") as low:
        low.return_value = ReviewResult(confidence=0.9, model_used="low_tier", cost_usd=0.0, seconds_elapsed=0.1)
        output = run_review("pr1", MemoryStore())
    assert output["trace_summary"]["total_calls"] == 1


def test_run_review_does_not_crash_when_every_tier_is_unavailable():
    with patch("reviewlift.cli.get_diff", return_value="diff --git a/x.py b/x.py"), \
         patch("reviewlift.agents.low_tier_reviewer.LowTierReviewerAgent.review") as low, \
         patch("reviewlift.agents.mid_tier_reviewer.MidTierReviewerAgent.review") as mid, \
         patch("reviewlift.agents.advanced_reviewer.AdvancedReviewerAgent.review") as adv:
        low.return_value = ReviewResult(confidence=0.0, model_used="low_tier_error")
        mid.return_value = ReviewResult(confidence=0.0, model_used="mid_tier_error")
        adv.return_value = ReviewResult(confidence=0.0, model_used="advanced_error")
        output = run_review("pr1", MemoryStore())
    assert output["confidence"] == 0.0
    assert output["cost_report"]["total_cost_usd"] == 0.0