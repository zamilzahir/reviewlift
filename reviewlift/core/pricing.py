"""Pricing constants for cost accounting. Only the advanced tier (Claude
Haiku 4.5) costs real money — low/mid run on local Ollama, $0 per call.
Rates as of Aug 2026: https://www.anthropic.com/claude/haiku
"""

HAIKU_INPUT_COST_PER_MTOK = 1.00
HAIKU_OUTPUT_COST_PER_MTOK = 5.00


def haiku_cost_usd(input_tokens: int, output_tokens: int) -> float:
    return (input_tokens / 1_000_000) * HAIKU_INPUT_COST_PER_MTOK + (
        output_tokens / 1_000_000
    ) * HAIKU_OUTPUT_COST_PER_MTOK