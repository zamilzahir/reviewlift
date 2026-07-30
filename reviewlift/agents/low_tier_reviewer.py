from reviewlift.core.models import ReviewResult


class LowTierReviewerAgent:
    """Stub: will call a small local model (e.g. Llama 3 8B) once real integration is added."""

    def review(self, chunk: str) -> ReviewResult:
        return ReviewResult(findings=[], confidence=0.7, model_used="low_tier")