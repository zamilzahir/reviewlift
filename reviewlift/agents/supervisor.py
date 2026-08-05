from reviewlift.agents.advanced_reviewer import AdvancedReviewerAgent
from reviewlift.agents.low_tier_reviewer import LowTierReviewerAgent
from reviewlift.agents.mid_tier_reviewer import MidTierReviewerAgent
from reviewlift.core.models import CostReport, ReviewResult
from reviewlift.core.router import classify_chunk, next_tier, should_escalate
from reviewlift.core.tracing import Tracer


class Supervisor:
    def __init__(self):
        self.tiers = {"low": LowTierReviewerAgent(), "mid": MidTierReviewerAgent(), "advanced": AdvancedReviewerAgent()}
        self.tracer = Tracer()

    def _review_chunk(self, chunk: str):
        tier = classify_chunk(chunk)
        chunk_cost = CostReport()
        while True:
            result = self.tiers[tier].review(chunk)
            if tier == "advanced":
                chunk_cost.smart_calls += 1
            else:
                chunk_cost.free_calls += 1
            chunk_cost.total_cost_usd += result.cost_usd
            chunk_cost.seconds_elapsed += result.seconds_elapsed

            escalate = should_escalate(result.confidence)
            escalated_to = next_tier(tier) if escalate else None
            self.tracer.log_call(tier, result.model_used, result.confidence, result.cost_usd,
                                  result.seconds_elapsed, escalated_to is not None)
            if escalated_to is None:
                return result, chunk_cost
            tier = escalated_to

    def review(self, diff: str):
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
            cost_report.total_cost_usd += chunk_cost.total_cost_usd
            cost_report.seconds_elapsed += chunk_cost.seconds_elapsed
        return merged, cost_report