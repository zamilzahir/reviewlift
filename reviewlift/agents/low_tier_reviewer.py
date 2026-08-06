import time

import requests

from reviewlift.core.models import ReviewResult
from reviewlift.core.parsing import extract_confidence, extract_findings, parse_findings
from reviewlift.core.retry import retry_call

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "phi3"


class LowTierReviewerAgent:
    """Calls a local Ollama model (phi3) to review a code diff. Free — runs locally.
    Retries once on transient failure (e.g. Ollama briefly unresponsive) before
    falling back to an error result."""

    def review(self, chunk: str) -> ReviewResult:
        prompt = f"""You are a code reviewer. Review this diff for style and naming issues only.
Respond with a single JSON object and nothing else, in this exact format:
{{"findings": [{{"file": "filename", "line": 1, "message": "short description", "severity": "info"}}], "confidence": 0.8}}

Diff:
{chunk}
"""
        start = time.perf_counter()
        try:
            response = retry_call(
                requests.post,
                OLLAMA_URL,
                json={"model": MODEL_NAME, "prompt": prompt, "stream": False},
                timeout=30,
                retries=2,
            )
            response.raise_for_status()
            raw_text = response.json().get("response", "")

            findings = parse_findings(extract_findings(raw_text))
            confidence = extract_confidence(raw_text)

            return ReviewResult(
                findings=findings,
                confidence=confidence,
                model_used="low_tier",
                cost_usd=0.0,
                seconds_elapsed=time.perf_counter() - start,
            )

        except (requests.RequestException, KeyError, TypeError) as e:
            print(f"[low_tier_reviewer] fallback after retries due to: {e}")
            return ReviewResult(
                findings=[], confidence=0.0, model_used="low_tier_error",
                cost_usd=0.0, seconds_elapsed=time.perf_counter() - start,
            )
