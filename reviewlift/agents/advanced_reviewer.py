import json
import re
import os
from dotenv import load_dotenv
from anthropic import Anthropic
from reviewlift.core.models import ReviewResult, ReviewFinding

load_dotenv()

MODEL_NAME = "claude-haiku-4-5-20251001"

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


def _extract_json_array(text: str, key: str) -> list | None:
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
    return 0.9


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


class AdvancedReviewerAgent:
    """Calls the Claude API (Haiku 4.5) to review a code diff for complex logic and security issues."""

    def review(self, chunk: str) -> ReviewResult:
        prompt = f"""You are a senior code reviewer. Review this diff for logic errors, security vulnerabilities, and edge cases.
Respond with a single JSON object and nothing else, in this exact format:
{{"findings": [{{"file": "filename", "line": 1, "message": "short description", "severity": "critical"}}], "confidence": 0.9}}

Diff:
{chunk}
"""
        try:
            response = client.messages.create(
                model=MODEL_NAME,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}],
            )
            raw_text = response.content[0].text

            findings = _parse_findings(_extract_findings(raw_text))
            confidence = _extract_confidence(raw_text)

            return ReviewResult(findings=findings, confidence=confidence, model_used="advanced")

        except Exception as e:
            print(f"[advanced_reviewer] fallback due to: {e}")
            return ReviewResult(findings=[], confidence=0.0, model_used="advanced_error")