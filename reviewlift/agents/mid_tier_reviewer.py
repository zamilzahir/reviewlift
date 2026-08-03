import json
import re
import requests
from reviewlift.core.models import ReviewResult, ReviewFinding

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "mistral"


def _extract_json_array(text: str, key: str) -> list | None:
    """Extract a JSON array value for `key`, using bracket matching."""
    match = re.search(rf'"{key}"\s*:\s*\[', text)
    if not match:
        return None
    start = match.end() - 1
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "[":
            depth += 1
        elif text[i] == "]":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    return None
    return None


def _extract_findings(text: str) -> list[dict]:
    result = _extract_json_array(text, "findings")
    return result if isinstance(result, list) else []


def _extract_confidence(text: str) -> float:
    match = re.search(r'"confidence"\s*:\s*([0-9]*\.?[0-9]+)(?=\s*[,}\]])', text)
    if match:
        try:
            value = float(match.group(1))
            return min(1.0, max(0.0, value))
        except ValueError:
            pass
    return 0.5


def _parse_findings(raw_findings: list) -> list[ReviewFinding]:
    findings = []
    for item in raw_findings:
        if not isinstance(item, dict):
            continue
        try:
            findings.append(ReviewFinding(**item))
        except (TypeError, KeyError):
            continue
    return findings


class MidTierReviewerAgent:
    """Calls a local Ollama model (mistral) to review a code diff for moderate-complexity issues."""

    def review(self, chunk: str) -> ReviewResult:
        prompt = f"""You are a code reviewer. Review this diff for logic issues, edge cases, and moderate complexity concerns.
Respond with a single JSON object and nothing else, in this exact format:
{{"findings": [{{"file": "filename", "line": 1, "message": "short description", "severity": "info"}}], "confidence": 0.8}}

Diff:
{chunk}
"""
        try:
            response = requests.post(
                OLLAMA_URL,
                json={"model": MODEL_NAME, "prompt": prompt, "stream": False},
                timeout=45,
            )
            response.raise_for_status()
            raw_text = response.json().get("response", "")

            findings = _parse_findings(_extract_findings(raw_text))
            confidence = _extract_confidence(raw_text)

            return ReviewResult(findings=findings, confidence=confidence, model_used="mid_tier")

        except (requests.RequestException, KeyError, TypeError) as e:
            print(f"[mid_tier_reviewer] fallback due to: {e}")
            return ReviewResult(findings=[], confidence=0.0, model_used="mid_tier_error")