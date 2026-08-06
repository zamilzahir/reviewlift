"""Secondary AI feature: natural-language summarization of a review.
Takes the structured findings from the main pipeline and asks the free
local model to produce a short plain-English summary.
"""

import requests

from reviewlift.core.retry import retry_call

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "phi3"


class SummarizerAgent:
    def summarize(self, findings: list[dict], num_files_reviewed: int) -> str:
        if not findings:
            return "No issues found in this review."

        findings_text = "\n".join(
            f"- [{f['severity']}] {f['file']}:{f['line']} — {f['message']}"
            for f in findings
        )
        prompt = f"""Summarize this code review in 2-3 plain-English sentences for a developer
skimming their PR. Be direct and specific about the most important issue.
Do not use JSON or bullet points — just prose.

Findings from {num_files_reviewed} file(s):
{findings_text}

Summary:"""

        try:
            response = retry_call(
                requests.post,
                OLLAMA_URL,
                json={"model": MODEL_NAME, "prompt": prompt, "stream": False},
                timeout=30,
                retries=2,
            )
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except (requests.RequestException, KeyError, TypeError) as e:
            print(f"[summarizer] fallback due to: {e}")
            return f"{len(findings)} issue(s) found across {num_files_reviewed} file(s). (Summary generation unavailable.)"
