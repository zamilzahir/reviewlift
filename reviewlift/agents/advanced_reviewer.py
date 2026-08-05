import os
import time
from anthropic import Anthropic
from dotenv import load_dotenv
from reviewlift.core.models import ReviewResult
from reviewlift.core.parsing import extract_confidence, extract_findings, parse_findings
from reviewlift.core.pricing import haiku_cost_usd

load_dotenv()
MODEL_NAME = "claude-haiku-4-5-20251001"
_client = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set. Add it to your .env file.")
        _client = Anthropic(api_key=api_key)
    return _client


class AdvancedReviewerAgent:
    def review(self, chunk: str) -> ReviewResult:
        prompt = f"""You are a senior code reviewer. Review this diff for logic errors, security vulnerabilities, and edge cases.
Respond with a single JSON object and nothing else, in this exact format:
{{"findings": [{{"file": "filename", "line": 1, "message": "short description", "severity": "critical"}}], "confidence": 0.9}}

Diff:
{chunk}
"""
        start = time.perf_counter()
        try:
            client = _get_client()
            response = client.messages.create(model=MODEL_NAME, max_tokens=1000, messages=[{"role": "user", "content": prompt}])
            raw_text = response.content[0].text
            cost_usd = haiku_cost_usd(response.usage.input_tokens, response.usage.output_tokens)
            findings = parse_findings(extract_findings(raw_text))
            confidence = extract_confidence(raw_text, default=0.9)
            return ReviewResult(findings=findings, confidence=confidence, model_used="advanced",
                                 cost_usd=cost_usd, seconds_elapsed=time.perf_counter() - start)
        except Exception as e:
            print(f"[advanced_reviewer] fallback due to: {e}")
            return ReviewResult(findings=[], confidence=0.0, model_used="advanced_error",
                                 cost_usd=0.0, seconds_elapsed=time.perf_counter() - start)