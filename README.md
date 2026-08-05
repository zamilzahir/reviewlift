# ReviewLift

A cost-saving AI code reviewer. Instead of sending every PR through an expensive model, ReviewLift routes simple checks to a free local model, escalates to a mid-tier local model when unsure, and reserves the paid cloud model for genuinely high-risk or low-confidence cases.

Real numbers, not projections: benchmarked across 4 planted-bug GitHub PRs, ReviewLift's adaptive routing matched the expensive-only setup's bug detection exactly (100% findings parity) at 37.5% lower cost. Full results in rules.md.

## Architecture

GitHub PR
    |
MCP server (real GitHub API fetch)
    |
Supervisor: splits diff into one task per file
    |
    -----------------------------------------
    |                 |                      |
LowTierReviewer   MidTierReviewer      AdvancedReviewer
(phi3, local,     (mistral, local,     (Claude Haiku 4.5,
 free)             free)                cloud, paid)
    |                 |                      |
    low confidence? --escalate--> low confidence? --escalate-->
    -----------------------------------------
                       |
              Workers run concurrently (one per file)
                       |
              Merged review + cost report + trace

- MCP server (reviewlift/tools/mcp_server.py) - a real FastMCP server exposing get_diff and list_hunks as tools, backed by the actual GitHub REST API. Connectable to any MCP client (Claude Code, Cursor, etc.), not just this CLI.
- Router (reviewlift/core/router.py) - classifies each file's diff by keyword match (auth, sql, eval, secrets, etc.) and decides when to escalate on low confidence. Full policy documented in rules.md.
- Supervisor (reviewlift/agents/supervisor.py) - splits a PR into per-file tasks, dispatches them to worker agents concurrently (ThreadPoolExecutor), merges results. Supports three modes for benchmarking: adaptive (real behavior), free_only, smart_only.
- Reviewer agents (reviewlift/agents/) - three tiers, each calling a real model (two local via Ollama, one via the Anthropic API), with tolerant JSON parsing and graceful fallback on failure.
- Tracing (reviewlift/core/tracing.py) - logs every model call: tier, model, confidence, cost, latency, whether it escalated.
- Cost tracking (reviewlift/core/pricing.py) - real token-based cost computation for the paid tier; local tiers are correctly tracked as $0.

## Setup

### 1. Dependencies

pip3 install anthropic requests python-dotenv mcp pytest --break-system-packages

### 2. Local models

Install Ollama (https://ollama.com), then pull the two local models:

ollama pull phi3
ollama pull mistral

### 3. API keys

Create a .env file in the repo root:

ANTHROPIC_API_KEY=your_key_here
GITHUB_TOKEN=your_token_here

GITHUB_TOKEN is optional but recommended - without it you're capped at 60 GitHub API requests/hour; with it, 5,000/hour. No special scopes needed for public repos.

## Running it

Review a real public GitHub PR:

python3 -m reviewlift.cli review owner/repo#123

Example:

python3 -m reviewlift.cli review zamilzahir/buggy-calculator#1

Output is JSON: findings (file, line, message, severity), overall confidence, a cost report, and a trace summary showing which tiers were called and how many times.

## Running the benchmark

python3 -m reviewlift.benchmark.run_benchmark

Runs a fixed set of test PRs through all three modes (free_only, smart_only, adaptive) and prints a comparison table of cost, time, and findings caught, saving full results to benchmark_results.json. Update BENCHMARK_PRS in reviewlift/benchmark/run_benchmark.py to point at your own test PRs.

## Running tests

python3 -m pytest tests/ -v

48+ tests covering routing logic, JSON parsing/extraction, pricing, each reviewer agent (with mocked network calls), the Supervisor's escalation and concurrent dispatch logic, memory store, CLI error handling, and diff splitting. External calls (Ollama, Claude API, GitHub API) are mocked in tests - no live network access required to run the suite.

## Status

Working end-to-end, benchmarked with real data. All three tiers confirmed firing correctly against live GitHub PRs. See rules.md for the full routing policy, its rationale, and the complete benchmark results, including an honest account of where the adaptive approach trades latency for cost savings rather than winning on both axes.

Known limitations:
- Confidence-based escalation can't catch a model that's confidently wrong (only confirms low self-reported confidence, not correctness) - see rules.md section 1 for a real example encountered during testing.
- Router keyword matching is a substring heuristic, not static analysis - can both over- and under-trigger.
- No persistent memory across CLI invocations yet (in-process only).
- No deployment/containerization yet.

Not yet built: Docker/deployment, OpenAPI or usage-guide docs, a secondary AI feature beyond the core routing pipeline, final presentation materials.

## Tech stack

- Python - agent orchestration, CLI
- Ollama - local model serving (phi3, mistral)
- Anthropic API - Claude Haiku 4.5 for the advanced tier
- MCP (mcp Python SDK) - real tool-server protocol for GitHub PR fetching
- pytest - test suite, all external calls mocked
- GitHub REST API - real PR diff fetching, optionally authenticated via GITHUB_TOKEN
