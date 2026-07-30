from reviewlift.core.models import ReviewResult


class AdvancedReviewerAgent:
    """Stub: will call an advanced cloud model (e.g. Claude, GPT-4) once real integration is added."""

    def review(self, chunk: str) -> ReviewResult:
        return ReviewResult(findings=[], confidence=1.0, model_used="advanced")