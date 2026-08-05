# ReviewLift routing rules

This document is the policy ReviewLift's Supervisor actually runs on — not a description of the code, but a record of *why* the thresholds and keywords are set where they are, and what the real benchmark data says about the tradeoffs.

## 1. Confidence threshold

CONFIDENCE_THRESHOLD = 0.6

If a tier's self-reported confidence falls below 0.6, the Supervisor escalates to the next tier rather than accepting that tier's answer.

**Why 0.6, not something else:** this is a deliberately conservative threshold — closer to "escalate unless fairly sure" than "escalate only when very unsure." The cost of a false negative (a missed bug shipped to production) is judged higher than the cost of an unnecessary escalation (a few extra cents and seconds).

**Known limitation — confirmed, not theoretical:** confidence-based escalation only catches cases where a model knows it doesn't know. It has no defense against a model being confidently wrong. During testing, the low tier (phi3) returned confidence: 1.0 on a diff that removed a divide-by-zero check, and completely missed the bug — flagging an unrelated, vague issue instead. Because 1.0 is well above 0.6, nothing escalated. A second run of the identical PR later did escalate (through a lower-confidence pass) and caught the real bug. This inconsistency is a real, observed property of small local models self-reporting confidence, not a bug in the routing logic. It's documented here rather than patched silently, since fixing it would require a second, confidence-independent escalation trigger (e.g. size/complexity heuristics) — noted as a possible next step, not yet implemented.

## 2. High-risk keywords

HIGH_RISK_KEYWORDS = [
    "auth", "password", "token", "sql", "payment", "security", "encrypt",
    "eval(", "exec(", "api_key", "secret",
]

Any diff chunk containing one of these (case-insensitive substring match) skips the low/mid tiers entirely and goes straight to the advanced tier, regardless of confidence.

**Why these specific keywords:** each maps to a category of bug where a wrong or missed review has outsized real-world cost — authentication bypass, credential leakage, injection attacks (SQL and code injection via eval/exec), and payment handling. These are exactly the categories where "the free model was probably fine" is not an acceptable risk tradeoff, so the policy pays for the expensive model unconditionally rather than leaving it to a confidence check that might not fire.

**Known limitation:** this is a substring match on lowercased text, not static analysis. It will both over-trigger (e.g. a comment mentioning "password" in an unrelated context still routes to advanced) and can miss genuinely risky code that doesn't happen to use these literal words. It's a cheap, effective heuristic — not a substitute for deeper analysis.

## 3. Three routing modes

The Supervisor supports three modes, used to benchmark the adaptive policy against its two extremes:

- free_only — never pays for the advanced tier. Starts at low, allowed one escalation to mid, capped there.
- smart_only — always pays. Every chunk goes straight to advanced.
- adaptive (the real system) — router picks the starting tier by keyword match, confidence-based escalation governs everything after.

## 4. What the real benchmark shows

Run across all 4 planted-bug PRs (buggy-calculator#1 through #4), 3 modes each, 12 total runs, real Ollama and Claude Haiku 4.5 calls:

| Mode | Total cost | Avg time/PR | Avg findings/PR |
|---|---|---|---|
| free_only | $0.00 | 9.56s | 1.25 |
| smart_only | $0.00403 | 2.24s | 2.0 |
| adaptive | $0.002518 | 5.32s | 2.0 |

- Cost saved vs. smart-only: 37.5%
- Findings caught vs. smart-only: 100% — adaptive matched smart-only's bug detection exactly, across this dataset.
- Speed vs. smart-only: adaptive was slower, not faster (0.42x — i.e. took more than 2x as long on average). This is the honest tradeoff: when a chunk needs to escalate, it pays the latency of trying a lower tier first before reaching advanced. The policy trades wall-clock time for cost savings, not both. This was not the outcome anticipated in the original proposal's illustrative example, and is reported here as a measured result rather than adjusted to look better than it is.

**Bottom line:** the adaptive policy delivers the accuracy of the expensive-only setup at meaningfully lower cost, at the price of some latency. Whether that tradeoff is worth it depends on whether a team values review turnaround time or spend more — a real decision, not a strictly-better-in-every-way result.

## 5. Where this could go next

- Replace pure confidence-threshold escalation with a second, independent trigger (diff size, changed-function risk) to catch confidently-wrong low-tier reviews.
- Expand the keyword list based on false-negative analysis over a larger PR sample, rather than the 11 keywords chosen up front.
- Investigate why adaptive runs slower than expected — potential parallelism improvements in how escalation chains are scheduled across files within a single PR.
