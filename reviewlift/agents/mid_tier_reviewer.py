from reviewlift.core.models import ReviewResult


class MidTierReviewerAgent:
    """Stub: will call a free/cheap cloud model (e.g. Groq, Gemini free tier) once real integration is added."""

    def review(self, chunk: str) -> ReviewResult:
        return ReviewResult(findings=[], confidence=0.85, model_used="mid_tier")