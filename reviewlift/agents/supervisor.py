import concurrent.futures

from reviewlift.agents.advanced_reviewer import AdvancedReviewerAgent
from reviewlift.agents.low_tier_reviewer import LowTierReviewerAgent
from reviewlift.agents.mid_tier_reviewer import MidTierReviewerAgent
from reviewlift.core.diff_split import split_diff_by_file
from reviewlift.core.models import CostReport, ReviewResult
from reviewlift.core.router import classify_chunk, next_tier, should_escalate
from reviewlift.core.tracing import Tracer

MAX_WORKERS = 4


class Supervisor:
    """Splits a PR diff into one task per file, dispatches each to a worker
    (running concurrently, not sequentially), and merges the results.

    Each worker owns the full tier-escalation loop for its file: it starts
    at whichever tier the router picks, and climbs to the next tier if the
    current one isn't confident enough — independently of what any other
    worker is doing.
    """

    def __init__(self, max_workers: int = MAX_WORKERS):
        self.tiers = {
            "low": LowTierReviewerAgent(),
            "mid": MidTierReviewerAgent(),
            "advanced": AdvancedReviewerAgent(),
        }
        self.tracer = Tracer()
        self.max_workers = max_workers

    def _review_chunk(self, file_name: str, content: str) -> tuple[ReviewResult, CostReport]:
        """Worker logic: review one file's diff, escalating tiers as needed."""
        tier = classify_chunk(content)
        chunk_cost = CostReport()

        while True:
            result = self.tiers[tier].review(content)

            if tier == "advanced":
                chunk_cost.smart_calls += 1
            else:
                chunk_cost.free_calls += 1
            chunk_cost.total_cost_usd += result.cost_usd
            chunk_cost.seconds_elapsed += result.seconds_elapsed

            escalate = should_escalate(result.confidence)
            escalated_to = next_tier(tier) if escalate else None

            self.tracer.log_call(
                tier=tier,
                model_used=result.model_used,
                confidence=result.confidence,
                cost_usd=result.cost_usd,
                seconds_elapsed=result.seconds_elapsed,
                escalated=escalated_to is not None,
            )

            if escalated_to is None:
                return result, chunk_cost
            tier = escalated_to

    def review(self, diff: str) -> tuple[ReviewResult, CostReport]:
        file_chunks = split_diff_by_file(diff)
        if not file_chunks:
            return ReviewResult(confidence=1.0, model_used="none"), CostReport()

        merged = ReviewResult(confidence=1.0)
        cost_report = CostReport()

        # Workers run concurrently — one file's review doesn't block another's.
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures = {
                pool.submit(self._review_chunk, chunk["file"], chunk["content"]): chunk["file"]
                for chunk in file_chunks
            }
            for future in concurrent.futures.as_completed(futures):
                result, chunk_cost = future.result()
                merged.findings.extend(result.findings)
                merged.confidence = min(merged.confidence, result.confidence)
                merged.model_used = result.model_used
                cost_report.free_calls += chunk_cost.free_calls
                cost_report.smart_calls += chunk_cost.smart_calls
                cost_report.total_cost_usd += chunk_cost.total_cost_usd
                cost_report.seconds_elapsed = max(cost_report.seconds_elapsed, chunk_cost.seconds_elapsed)

        return merged, cost_report