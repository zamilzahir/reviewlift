# ReviewLift

A cost-saving AI code reviewer. Instead of sending every PR through an expensive
model, ReviewLift routes simple checks (style, naming) to a low-tier local model,
moderate checks to a mid-tier cloud model, and hard checks (logic, security) to
an advanced model — escalating automatically when a lower tier isn't confident.

## Architecture

PR comes in --> Supervisor --> splits into chunks
                                   |
                -----------------------------------------
                |                 |                      |
          LowTierReviewer   MidTierReviewer      AdvancedReviewer
          (local model)     (cheap cloud model)   (advanced cloud model)
                |                 |                      |
          low confidence? --escalate--> low confidence? --escalate-->
                -----------------------------------------
                                   |
                         Merged ReviewResult
                         + CostReport

- **Supervisor** (`reviewlift/agents/supervisor.py`) — splits a diff into chunks and routes each to a tiered worker agent.
- **LowTierReviewerAgent / MidTierReviewerAgent / AdvancedReviewerAgent** — do the actual review calls.
- **Tool registry** (`reviewlift/tools/`) — MCP-style tools for reading PR diffs (mocked for now).
- **Memory** (`reviewlift/memory/store.py`) — stores past review results, keyed by PR id.

## Tech choices

- **Python** — fast to prototype agent logic, good LLM SDK support.
- **Low tier: small local model (e.g. Llama 3 8B)** — zero cost, good enough for style/naming checks.
- **Mid tier: free/cheap cloud model (e.g. Groq, Gemini free tier)** — moderate checks without local hardware limits.
- **Advanced tier: a stronger cloud model** — used only for logic/security checks, where mistakes are costly.
- **MCP** — decouples the agents from how PR data is fetched, so the tool layer can later point at real GitHub API calls instead of mocks.

## Status

Scaffold stage — all agent calls are stubbed and return dummy data. Real model
calls and routing/escalation logic land next.

## Running it

    python3 -m reviewlift.cli review pr1