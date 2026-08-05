import time
import requests
from reviewlift.core.models import ReviewResult
from reviewlift.core.parsing import extract_confidence, extract_findings, parse_findings

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "phi3"


class LowTierReviewerAgent:
    def review(self, chunk: str) -> ReviewResult:
        prompt = f"""You are a code reviewer. Review this diff for style and naming issues only.
Respond with a single JSON object and nothing else, in this exact format:
{{"findings": [{{"file": "filename", "line": 1, "message": "short description", "severity": "info"}}], "confidence": 0.8}}

Diff:
{chunk}
"""
        start = time.perf_counter()
        try:
            response = requests.post(OLLAMA_URL, json={"model": MODEL_NAME, "prompt": prompt, "stream": False}, timeout=30)
            response.raise_for_status()
            raw_text = response.json().get("response", "")
            findings = parse_findings(extract_findings(raw_text))
            confidence = extract_confidence(raw_text)
            return ReviewResult(findings=findings, confidence=confidence, model_used="low_tier",
                                 cost_usd=0.0, seconds_elapsed=time.perf_counter() - start)
        except (requests.RequestException, KeyError, TypeError) as e:
            print(f"[low_tier_reviewer] fallback due to: {e}")
            return ReviewResult(findings=[], confidence=0.0, model_used="low_tier_error",
                                 cost_usd=0.0, seconds_elapsed=time.perf_counter() - start)