from reviewlift.agents.low_tier_reviewer import LowTierReviewerAgent
from reviewlift.agents.mid_tier_reviewer import MidTierReviewerAgent
from reviewlift.agents.advanced_reviewer import AdvancedReviewerAgent
from reviewlift.core.models import ReviewResult, CostReport


class Supervisor:
    """Splits a diff into chunks, routes each to a tiered worker agent, merges results."""

    def __init__(self):
        self.low_tier = LowTierReviewerAgent()
        self.mid_tier = MidTierReviewerAgent()
        self.advanced = AdvancedReviewerAgent()

    def review(self, diff: str) -> tuple[ReviewResult, CostReport]:
        # Stub: no real chunking/routing/escalation yet — one chunk, always low tier
        chunks = [diff]
        merged = ReviewResult()
        for chunk in chunks:
            result = self.low_tier.review(chunk)
            merged.findings.extend(result.findings)

        cost_report = CostReport(free_calls=len(chunks))
        return merged, cost_report