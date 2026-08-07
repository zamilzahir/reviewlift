# ReviewLift usage guide / runbook

## 1. Install and setup

Clone and enter the repo:

    git clone https://github.com/zamilzahir/reviewlift.git
    cd reviewlift

Install Python dependencies:

    pip3 install anthropic requests python-dotenv mcp pytest --break-system-packages

Install Ollama (https://ollama.com), then pull the two local models used by the low and mid tiers:

    ollama pull phi3
    ollama pull mistral

Confirm Ollama is running (the CLI expects it at http://localhost:11434):

    curl http://localhost:11434/api/tags

## 2. Required environment variables

Create a .env file in the repo root:

    ANTHROPIC_API_KEY=sk-ant-...
    GITHUB_TOKEN=ghp_...

- ANTHROPIC_API_KEY (required) - used by the advanced tier (Claude Haiku 4.5). Without it, the advanced tier fails cleanly and the CLI exits with code 3.
- GITHUB_TOKEN (optional but recommended) - raises the GitHub API rate limit from 60 requests/hour to 5,000/hour. No special scopes needed for public repos.

.env is git-ignored. Never commit it.

## 3. Available commands and arguments

### reviewlift.cli

    python3 -m reviewlift.cli <command> <pr_id>

| Argument | Required | Description |
|---|---|---|
| command | yes | Must be `review`. Only one command exists currently. |
| pr_id | yes | Pull request identifier in `owner/repo#number` format. |

Example:

    python3 -m reviewlift.cli review zamilzahir/buggy-calculator#2

Reviews exactly one PR. To review several, run the command once per PR.

### reviewlift.benchmark.run_benchmark

    python3 -m reviewlift.benchmark.run_benchmark

Takes no arguments. Runs a fixed list of PRs (defined in BENCHMARK_PRS inside run_benchmark.py) through all three routing modes and writes benchmark_results.json.

### reviewlift.tools.mcp_server

    python3 -m reviewlift.tools.mcp_server

Starts the MCP server on stdio. It will appear to hang - this is correct. MCP servers are launched by a client, not run interactively. Ctrl+C to exit.

## 4. Output schema

    {
      "pr_id": "owner/repo#123",
      "summary": "Plain-English AI-generated summary of the review.",
      "findings": [
        {"file": "path.py", "line": 12, "message": "description", "severity": "info|warning|critical"}
      ],
      "confidence": 0.85,
      "cost_report": {
        "total_cost_usd": 0.0013,
        "free_calls": 2,
        "smart_calls": 1,
        "seconds_elapsed": 5.3
      },
      "trace_summary": {
        "total_calls": 3,
        "calls_by_tier": {"low": 1, "mid": 1, "advanced": 1},
        "escalations": 2,
        "total_cost_usd": 0.0013,
        "total_seconds": 5.3
      }
    }

Progress messages ("fetching and reviewing...", "generating summary...") are written to stderr, so piping stdout to a file gives clean JSON:

    python3 -m reviewlift.cli review owner/repo#1 > result.json

## 5. Running the benchmark pipeline

1. Ensure Ollama is running and both models are pulled.
2. Ensure ANTHROPIC_API_KEY is set (the benchmark makes real paid calls).
3. Confirm every PR listed in BENCHMARK_PRS actually exists as an open pull request, not just a pushed branch.
4. Run:

       python3 -m reviewlift.benchmark.run_benchmark

Expect roughly 2-4 minutes for 12 runs. Results print as a table and save to benchmark_results.json.

## 6. Caching

Identical diff content is cached to .reviewlift_cache.json in the working directory. Re-running against an unchanged PR returns the cached result instantly with zero model calls and zero cost. The CLI prints "cache hit" to stderr when this happens.

To force a fresh review, delete the cache:

    rm .reviewlift_cache.json

## 7. Retry behavior

Each tier retries its model call once (0.5s delay) on transient failure before giving up. A tier that exhausts its retries returns a zero-confidence error result, which then escalates to the next tier normally. Retry is for failed calls; escalation is for low-confidence answers. They are separate mechanisms.

## 8. Common errors and troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'reviewlift'` | Running from the wrong directory | `cd` to the repo root. Confirm with `pwd` - it must end in `/reviewlift` with nothing after it, not `/reviewlift/reviewlift`. |
| `reviewlift: invalid input - PR not found` (exit 2) | The PR number doesn't exist, the repo is private, or the branch was pushed but the pull request was never opened on GitHub | Open the repo's Pull requests tab and confirm the PR exists. A pushed branch alone is not a PR. |
| `reviewlift: configuration error` (exit 3) | ANTHROPIC_API_KEY missing from .env | Add the key to .env in the repo root. |
| `GitHub rate limit hit` | More than 60 unauthenticated requests in an hour | Add GITHUB_TOKEN to .env. |
| `[low_tier_reviewer] fallback after retries` | Ollama isn't running, or the model isn't pulled | Start Ollama; run `ollama pull phi3` and `ollama pull mistral`. |
| Every tier returns an error result, confidence 0.0 | Ollama down AND no valid API key | This is expected graceful degradation, not a crash. Fix whichever service is unavailable. |
| `pytest` reports "collected 0 items" | Running from inside tests/ instead of the repo root | `cd ..` to the repo root. |
| Terminal stuck at `heredoc>` | A pasted multi-line block was truncated before its closing delimiter | Ctrl+C, then re-paste the complete block. |

## 9. What to do when the benchmark pipeline fails

The runner catches per-run exceptions and continues, so a partial failure still produces output. Read the FAILED lines in the terminal to identify which PR/mode combinations broke.

- **Some runs show "PR not found"** - those PRs don't exist or were never opened as pull requests. Create them, then re-run. The whole benchmark must be re-run, since partial results would compare unequal sample sizes.
- **All advanced-tier runs fail** - check ANTHROPIC_API_KEY and account credit balance.
- **All low/mid-tier runs fail** - Ollama isn't running or the models aren't pulled.
- **Runs succeed but findings are 0 everywhere** - check that the diffs actually contain the planted bugs; a merged or closed PR may return an empty or unexpected diff.
- **Results look implausible (e.g. adaptive cheaper than free-only)** - delete .reviewlift_cache.json and re-run. A stale cache entry can return an old result for an unchanged diff.

## 10. Running tests

    python3 -m pytest tests/ -v

50 tests. All external calls (Ollama, Claude API, GitHub API) are mocked, so the suite runs offline with no API key and costs nothing.
