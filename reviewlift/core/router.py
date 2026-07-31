"""Routing logic: decides which reviewer tier handles a chunk, with confidence-based escalation."""

# Confidence below this means "not sure enough" — escalate to the next tier.
CONFIDENCE_THRESHOLD = 0.6

# Simple heuristic: certain keywords in a diff suggest it touches risky logic
# (auth, security, database, payments) and should skip straight to a higher tier.
HIGH_RISK_KEYWORDS = ["auth", "password", "token", "sql", "payment", "security", "encrypt"]


def classify_chunk(chunk: str) -> str:
    """Classify a diff chunk as 'low', 'mid', or 'advanced' before any model runs,
    based on simple heuristics. This is the FIRST routing decision — confidence-based
    escalation can still bump it higher after a tier actually reviews it."""
    lowered = chunk.lower()
    if any(keyword in lowered for keyword in HIGH_RISK_KEYWORDS):
        return "advanced"
    return "low"


def next_tier(current_tier: str) -> str | None:
    """Given the tier that just reviewed a chunk, return the next tier to escalate to,
    or None if already at the top tier."""
    order = ["low", "mid", "advanced"]
    idx = order.index(current_tier)
    if idx + 1 < len(order):
        return order[idx + 1]
    return None


def should_escalate(confidence: float) -> bool:
    """Decide whether a chunk's result confidence is low enough to escalate."""
    return confidence < CONFIDENCE_THRESHOLD