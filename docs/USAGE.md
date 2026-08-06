# ReviewLift usage guide

## Reviewing a PR

python3 -m reviewlift.cli review owner/repo#123

Example:

python3 -m reviewlift.cli review zamilzahir/buggy-calculator#1

## Output schema

pr_id, summary (plain-English AI-generated summary), findings (file, line, message, severity), confidence, cost_report (total_cost_usd, free_calls, smart_calls, seconds_elapsed), trace_summary (total_calls, calls_by_tier, escalations, total_cost_usd, total_seconds)

## Environment variables

- ANTHROPIC_API_KEY (required) - for the advanced tier (Claude Haiku 4.5)
- GITHUB_TOKEN (optional, recommended) - raises GitHub API rate limit from 60/hr to 5000/hr

## Caching

Identical diff content is cached to .reviewlift_cache.json in the working directory. Re-running the CLI against the same PR returns the cached result instantly with zero model calls and zero cost.

## Retry behavior

Each tier retries once on transient network failure (Ollama briefly unresponsive, Claude API timeout) before falling back to an error result for that tier, which then escalates normally.

## Running the benchmark

python3 -m reviewlift.benchmark.run_benchmark

## Running tests

python3 -m pytest tests/ -v

## MCP server (standalone)

python3 -m reviewlift.tools.mcp_server

Exposes get_diff(pr_id) and list_hunks(diff) as MCP tools over stdio.
