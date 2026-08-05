"""Shared parsing helpers for turning raw LLM text into ReviewResult data."""

import json
import re

from reviewlift.core.models import ReviewFinding


def extract_json_array(text: str, key: str) -> list | None:
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


def extract_findings(text: str) -> list[dict]:
    result = extract_json_array(text, "findings")
    return result if isinstance(result, list) else []


def extract_confidence(text: str, default: float = 0.5) -> float:
    match = re.search(r'"confidence"\s*:\s*([0-9]*\.?[0-9]+)(?=\s*[,}\]])', text)
    if match:
        try:
            value = float(match.group(1))
            return min(1.0, max(0.0, value))
        except ValueError:
            pass
    return default


def parse_findings(raw_findings: list) -> list[ReviewFinding]:
    findings = []
    for item in raw_findings:
        if not isinstance(item, dict):
            continue
        try:
            findings.append(ReviewFinding(**item))
        except (TypeError, KeyError):
            continue
    return findings