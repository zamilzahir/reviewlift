from unittest.mock import patch
from reviewlift.agents.supervisor import Supervisor
from reviewlift.core.models import ReviewResult


def test_confident_low_tier_result_does_not_escalate():
    with patch("reviewlift.agents.low_tier_reviewer.LowTierReviewerAgent.review") as low:
        low.return_value = ReviewResult(confidence=0.9, model_used="low_tier", cost_usd=0.0, seconds_elapsed=0.1)
        supervisor = Supervisor()
        result, cost = supervisor.review("a harmless diff")
    assert result.model_used == "low_tier"
    assert cost.free_calls == 1
    assert cost.smart_calls == 0


def test_low_confidence_escalates_through_all_tiers():
    with patch("reviewlift.agents.low_tier_reviewer.LowTierReviewerAgent.review") as low, \
         patch("reviewlift.agents.mid_tier_reviewer.MidTierReviewerAgent.review") as mid, \
         patch("reviewlift.agents.advanced_reviewer.AdvancedReviewerAgent.review") as adv:
        low.return_value = ReviewResult(confidence=0.1, model_used="low_tier", cost_usd=0.0, seconds_elapsed=0.1)
        mid.return_value = ReviewResult(confidence=0.2, model_used="mid_tier", cost_usd=0.0, seconds_elapsed=0.2)
        adv.return_value = ReviewResult(confidence=0.95, model_used="advanced", cost_usd=0.002, seconds_elapsed=0.5)
        supervisor = Supervisor()
        result, cost = supervisor.review("def helper():\n    return 1")
    assert result.model_used == "advanced"
    assert cost.free_calls == 2
    assert cost.smart_calls == 1
    assert cost.total_cost_usd == 0.002


def test_high_risk_keyword_routes_straight_to_advanced_tier():
    with patch("reviewlift.agents.advanced_reviewer.AdvancedReviewerAgent.review") as adv:
        adv.return_value = ReviewResult(confidence=0.97, model_used="advanced", cost_usd=0.001, seconds_elapsed=0.3)
        supervisor = Supervisor()
        result, cost = supervisor.review("password = user_input")
    assert result.model_used == "advanced"
    assert cost.smart_calls == 1
    assert cost.free_calls == 0


def test_mid_tier_calls_are_not_miscounted_as_paid():
    with patch("reviewlift.agents.low_tier_reviewer.LowTierReviewerAgent.review") as low, \
         patch("reviewlift.agents.mid_tier_reviewer.MidTierReviewerAgent.review") as mid:
        low.return_value = ReviewResult(confidence=0.2, model_used="low_tier", cost_usd=0.0, seconds_elapsed=0.1)
        mid.return_value = ReviewResult(confidence=0.9, model_used="mid_tier", cost_usd=0.0, seconds_elapsed=0.2)
        supervisor = Supervisor()
        result, cost = supervisor.review("a diff")
    assert cost.free_calls == 2
    assert cost.smart_calls == 0