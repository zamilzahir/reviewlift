import concurrent.futures

from reviewlift.agents.advanced_reviewer import AdvancedReviewerAgent
from reviewlift.agents.low_tier_reviewer import LowTierReviewerAgent
from reviewlift.agents.mid_tier_reviewer import MidTierReviewerAgent
from reviewlift.core.diff_split import split_diff_by_file
from reviewlift.core.models import CostReport, ReviewResult
from reviewlift.core.router import classify_chunk, next_tier, should_escalate
from reviewlift.core.tracing import Tracer

MAX_WORKERS = 4
VALID_MODES = ("adaptive", "free_only", "smart_only")


class Supervisor:
    """Splits a PR diff into one task per file, dispatches each to a worker
    concurrently, and merges results.

    mode controls routing, so the same PR can be benchmarked three ways:
    - "adaptive" (default): real ReviewLift behavior — router picks the
      starting tier, escalates on low confidence, up to advanced.
    - "free_only": simulates never paying for the advanced tier. Starts at
      low, always takes one free upgrade to mid, but never reaches advanced.
    - "smart_only": simulates sending everything to the expensive model.
      Every file goes straight to advanced, no escalation loop.
    """

    def __init__(self, max_workers: int = MAX_WORKERS, mode: str = "adaptive"):
        if mode not in VALID_MODES:
            raise ValueError(f"mode must be one of {VALID_MODES}, got '{mode}'")
        self.tiers = {
            "low": LowTierReviewerAgent(),
            "mid": MidTierReviewerAgent(),
            "advanced": AdvancedReviewerAgent(),
        }
        self.tracer = Tracer()
        self.max_workers = max_workers
        self.mode = mode

    def _starting_tier(self, content: str) -> str:
        if self.mode == "smart_only":
            return "advanced"
        if self.mode == "free_only":
            return "low"
        return classify_chunk(content)

    def _next_tier(self, current_tier: str) -> str | None:
        if self.mode == "smart_only":
            return None
        if self.mode == "free_only":
            return "mid" if current_tier == "low" else None
        return next_tier(current_tier)

    def _review_chunk(self, file_name: str, content: str) -> tuple[ReviewResult, CostReport]:
        tier = self._starting_tier(content)
        chunk_cost = CostReport()

        while True:
            result = self.tiers[tier].review(content)

            if tier == "advanced":
                chunk_cost.smart_calls += 1
            else:
                chunk_cost.free_calls += 1
            chunk_cost.total_cost_usd += result.cost_usd
            chunk_cost.seconds_elapsed += result.seconds_elapsed

            if self.mode == "adaptive":
                should_climb = should_escalate(result.confidence)
            elif self.mode == "free_only":
                should_climb = tier == "low"
            else:  # smart_only
                should_climb = False

            escalated_to = self._next_tier(tier) if should_climb else None

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