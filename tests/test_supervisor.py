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

def test_multi_file_diff_dispatches_each_file_independently():
    diff = (
        "diff --git a/safe.py b/safe.py\n--- a/safe.py\n+++ b/safe.py\n@@ -1 +1 @@\n-x\n+y\n"
        "diff --git a/auth.py b/auth.py\n--- a/auth.py\n+++ b/auth.py\n@@ -1 +1 @@\n-x\n+password=1\n"
    )
    with patch("reviewlift.agents.low_tier_reviewer.LowTierReviewerAgent.review") as low, \
         patch("reviewlift.agents.advanced_reviewer.AdvancedReviewerAgent.review") as adv:
        low.return_value = ReviewResult(confidence=0.9, model_used="low_tier", cost_usd=0.0, seconds_elapsed=0.1)
        adv.return_value = ReviewResult(confidence=0.95, model_used="advanced", cost_usd=0.001, seconds_elapsed=0.3)

        supervisor = Supervisor()
        result, cost = supervisor.review(diff)

    # safe.py has no risky keyword -> low tier; auth.py has "password" -> advanced tier
    assert cost.free_calls == 1
    assert cost.smart_calls == 1
    assert supervisor.tracer.summary()["total_calls"] == 2


def test_parallel_time_uses_max_not_sum():
    diff = (
        "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n@@ -1 +1 @@\n-x\n+y\n"
        "diff --git a/b.py b/b.py\n--- a/b.py\n+++ b/b.py\n@@ -1 +1 @@\n-x\n+z\n"
    )
    with patch("reviewlift.agents.low_tier_reviewer.LowTierReviewerAgent.review") as low:
        low.return_value = ReviewResult(confidence=0.9, model_used="low_tier", cost_usd=0.0, seconds_elapsed=2.0)
        supervisor = Supervisor()
        result, cost = supervisor.review(diff)

    # Both files take 2.0s but run concurrently — wall time should be ~2.0s, not ~4.0s
    assert cost.seconds_elapsed == 2.0