from reviewlift.agents.low_tier_reviewer import LowTierReviewerAgent
from reviewlift.agents.mid_tier_reviewer import MidTierReviewerAgent
from reviewlift.agents.advanced_reviewer import AdvancedReviewerAgent
from reviewlift.core.models import ReviewResult, CostReport
from reviewlift.core.router import classify_chunk, next_tier, should_escalate


class Supervisor:
    """Splits a diff into chunks, routes each to a tiered worker agent, merges results."""

    def __init__(self):
        self.tiers = {
            "low": LowTierReviewerAgent(),
            "mid": MidTierReviewerAgent(),
            "advanced": AdvancedReviewerAgent(),
        }

    def _review_chunk(self, chunk: str) -> tuple[ReviewResult, CostReport]:
        tier = classify_chunk(chunk)
        chunk_cost = CostReport()

        while True:
            result = self.tiers[tier].review(chunk)
            if tier == "low":
                chunk_cost.free_calls += 1
            else:
                chunk_cost.smart_calls += 1

            if not should_escalate(result.confidence):
                return result, chunk_cost

            escalated = next_tier(tier)
            if escalated is None:
                return result, chunk_cost
            tier = escalated

    def review(self, diff: str) -> tuple[ReviewResult, CostReport]:
        chunks = [diff]
        merged = ReviewResult()
        cost_report = CostReport()

        for chunk in chunks:
            result, chunk_cost = self._review_chunk(chunk)
            merged.findings.extend(result.findings)
            merged.confidence = min(merged.confidence, result.confidence)
            merged.model_used = result.model_used
            cost_report.free_calls += chunk_cost.free_calls
            cost_report.smart_calls += chunk_cost.smart_calls

        return merged, cost_report
