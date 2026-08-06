from unittest.mock import patch
import pytest
from reviewlift.cli import run_review
from reviewlift.core.models import ReviewResult
from reviewlift.memory.store import MemoryStore


def test_run_review_raises_value_error_on_empty_diff():
    with patch("reviewlift.cli.get_diff", return_value=""), \
         patch("reviewlift.cli.get_cached", return_value=None):
        with pytest.raises(ValueError):
            run_review("pr1", MemoryStore())


def test_run_review_saves_result_to_memory():
    with patch("reviewlift.cli.get_diff", return_value="diff --git a/a.py b/a.py"), \
         patch("reviewlift.cli.get_cached", return_value=None), \
         patch("reviewlift.cli.set_cached"), \
         patch("reviewlift.agents.low_tier_reviewer.LowTierReviewerAgent.review") as low, \
         patch("reviewlift.agents.summarizer.SummarizerAgent.summarize", return_value="summary"):
        low.return_value = ReviewResult(confidence=0.9, model_used="low_tier", cost_usd=0.0, seconds_elapsed=0.1)
        memory = MemoryStore()
        output = run_review("pr1", memory)
    assert output["pr_id"] == "pr1"
    assert memory.get("pr1") == output


def test_run_review_output_includes_trace_summary():
    with patch("reviewlift.cli.get_diff", return_value="diff --git a/b.py b/b.py"), \
         patch("reviewlift.cli.get_cached", return_value=None), \
         patch("reviewlift.cli.set_cached"), \
         patch("reviewlift.agents.low_tier_reviewer.LowTierReviewerAgent.review") as low, \
         patch("reviewlift.agents.summarizer.SummarizerAgent.summarize", return_value="summary"):
        low.return_value = ReviewResult(confidence=0.9, model_used="low_tier", cost_usd=0.0, seconds_elapsed=0.1)
        output = run_review("pr1", MemoryStore())
    assert "trace_summary" in output
    assert output["trace_summary"]["total_calls"] == 1


def test_run_review_includes_ai_generated_summary():
    with patch("reviewlift.cli.get_diff", return_value="diff --git a/c.py b/c.py"), \
         patch("reviewlift.cli.get_cached", return_value=None), \
         patch("reviewlift.cli.set_cached"), \
         patch("reviewlift.agents.low_tier_reviewer.LowTierReviewerAgent.review") as low, \
         patch("reviewlift.agents.summarizer.SummarizerAgent.summarize", return_value="No major issues.") as summarize:
        low.return_value = ReviewResult(confidence=0.9, model_used="low_tier", cost_usd=0.0, seconds_elapsed=0.1)
        output = run_review("pr1", MemoryStore())
    assert output["summary"] == "No major issues."
    summarize.assert_called_once()


def test_run_review_does_not_crash_when_every_tier_is_unavailable():
    with patch("reviewlift.cli.get_diff", return_value="diff --git a/d.py b/d.py"), \
         patch("reviewlift.cli.get_cached", return_value=None), \
         patch("reviewlift.cli.set_cached"), \
         patch("reviewlift.agents.low_tier_reviewer.LowTierReviewerAgent.review") as low, \
         patch("reviewlift.agents.mid_tier_reviewer.MidTierReviewerAgent.review") as mid, \
         patch("reviewlift.agents.advanced_reviewer.AdvancedReviewerAgent.review") as adv, \
         patch("reviewlift.agents.summarizer.SummarizerAgent.summarize", return_value="No issues found."):
        low.return_value = ReviewResult(confidence=0.0, model_used="low_tier_error")
        mid.return_value = ReviewResult(confidence=0.0, model_used="mid_tier_error")
        adv.return_value = ReviewResult(confidence=0.0, model_used="advanced_error")
        output = run_review("pr1", MemoryStore())
    assert output["confidence"] == 0.0
    assert output["cost_report"]["total_cost_usd"] == 0.0


def test_run_review_returns_cached_result_on_cache_hit():
    cached_output = {"pr_id": "pr1", "summary": "cached", "findings": [], "confidence": 1.0,
                      "cost_report": {}, "trace_summary": {}}
    with patch("reviewlift.cli.get_diff", return_value="diff --git a/e.py b/e.py"), \
         patch("reviewlift.cli.get_cached", return_value=cached_output), \
         patch("reviewlift.agents.low_tier_reviewer.LowTierReviewerAgent.review") as low:
        output = run_review("pr1", MemoryStore())
    assert output == cached_output
    low.assert_not_called()
