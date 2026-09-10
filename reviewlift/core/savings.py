"""Estimates cost savings for a single review by comparing what was actually
spent against what the same work would have cost if every file had been sent
straight to the advanced (paid) tier.

The baseline is an estimate, not a second real run: it assumes each reviewed
file would have cost roughly what an average advanced-tier call costs. Real
per-mode comparison lives in the benchmark, not here.
"""

# Average observed cost of one advanced-tier call, from the 4-PR benchmark.
AVG_ADVANCED_CALL_USD = 0.001324


def estimate_savings(free_calls: int, smart_calls: int, actual_cost_usd: float) -> dict:
    """Return a savings summary for one review run."""
    files_reviewed = free_calls + smart_calls
    if files_reviewed == 0:
        return {
            "actual_cost_usd": 0.0,
            "smart_only_cost_usd": 0.0,
            "saved_usd": 0.0,
            "saved_percent": 0.0,
        }

    smart_only_cost = files_reviewed * AVG_ADVANCED_CALL_USD
    saved = max(0.0, smart_only_cost - actual_cost_usd)
    pct = (saved / smart_only_cost * 100) if smart_only_cost > 0 else 0.0

    return {
        "actual_cost_usd": round(actual_cost_usd, 6),
        "smart_only_cost_usd": round(smart_only_cost, 6),
        "saved_usd": round(saved, 6),
        "saved_percent": round(pct, 1),
    }
