# Prompts Log

This log records the AI-assisted prompts used to scaffold ReviewLift, the model used, and what each response produced.

---

### Prompt 1
**Asked:** Scaffold an agent-first Python project for a PR-review routing tool — need a Supervisor agent, worker agents, an MCP tool server, a memory store, and a CLI entrypoint that runs end-to-end on mock data.
**Model:** Claude (Sonnet)
**Result:** Generated the folder structure (`reviewlift/agents/`, `tools/`, `core/`, `memory/`) and the initial data models in `core/models.py` — `ReviewFinding`, `ReviewResult`, `CostReport`. These are plain dataclasses that define the shape of data passed between agents (a finding, a result with confidence, and a cost report).

---

### Prompt 2
**Asked:** Generate three tiered reviewer agent stubs — low tier (local model), mid tier (cheap cloud model), advanced tier (stronger cloud model) — each returning a stubbed `ReviewResult`.
**Model:** Claude (Sonnet)
**Result:** `low_tier_reviewer.py`, `mid_tier_reviewer.py`, `advanced_reviewer.py`. Each has one `review(chunk)` method that currently returns hardcoded dummy findings with a fixed confidence score, since no real model calls are wired in yet. This lets the rest of the pipeline (Supervisor, CLI) be built and tested before real API calls are added.

---

### Prompt 3
**Asked:** Write a Supervisor class that splits a diff into chunks and routes each chunk to the reviewer agents, merging results into one `ReviewResult` plus a `CostReport`.
**Model:** Claude (Sonnet)
**Result:** `supervisor.py` — currently routes every chunk to the low-tier agent only (no real routing/escalation logic yet). This is intentional for the scaffold stage: it proves the pipeline connects end-to-end (CLI → Supervisor → Agent → merged result) before real confidence-based routing is added.

---

### Prompt 4
**Asked:** Create a mock MCP-style tool server exposing `get_diff` and `list_hunks`, plus a registry that lets agents look up tools by name.
**Model:** Claude (Sonnet)
**Result:** `mcp_server.py` returns a hardcoded sample diff instead of hitting a real GitHub API. `registry.py` maps tool names (`"get_diff"`, `"list_hunks"`) to their functions, so agents can call tools without knowing their implementation — the mock can later be swapped for a real GitHub-connected version without changing agent code.

---

### Prompt 5
**Asked:** Write a CLI entrypoint that ties everything together — takes a PR id, fetches the (mock) diff, runs it through the Supervisor, and prints the result as JSON.
**Model:** Claude (Sonnet)
**Result:** `cli.py` — running `python3 -m reviewlift.cli review pr1` fetches the mock diff, runs it through the Supervisor, and prints a JSON object with findings, confidence, and a cost report. Confirmed working end-to-end on mock data.

# Prompts Log

This log records the AI-assisted prompts used to build ReviewLift, the model used, and what each response produced. Continues from the initial scaffold prompts (1-5, already logged).

---

### Prompt 6
**Asked:** Wire a real local model call (phi3 via Ollama) into the low-tier reviewer agent, replacing the stubbed dummy response.
**Model:** Claude (Sonnet)
**Result:** `LowTierReviewerAgent.review()` now sends an HTTP POST to Ollama's `/api/generate` endpoint with a code-review prompt and parses the JSON-shaped response into findings and a confidence score.

---

### Prompt 7
**Asked:** The low-tier agent crashes intermittently — phi3 sometimes returns malformed JSON around otherwise valid data.
**Model:** Claude (Sonnet)
**Result:** Replaced naive `json.loads()` with bracket-matching extraction: find the `"findings":[` key, then walk forward counting bracket depth to locate the true end of the array, so surrounding junk text doesn't break parsing.

---

### Prompt 8
**Asked:** Wire a real local model call (mistral via Ollama) into the mid-tier reviewer agent.
**Model:** Claude (Sonnet)
**Result:** `MidTierReviewerAgent`, structurally identical to the low tier but pointed at `mistral` with a longer timeout (45s vs 30s) and a prompt scoped to logic/edge-case review rather than style.

---

### Prompt 9
**Asked:** Wire the advanced tier to a real Claude Haiku 4.5 API call, computing real cost from actual token usage instead of a placeholder.
**Model:** Claude (Sonnet)
**Result:** `AdvancedReviewerAgent` using the Anthropic SDK; cost computed from `response.usage.input_tokens`/`output_tokens` against Haiku 4.5 per-token pricing.

---

### Prompt 10
**Asked:** The Anthropic client crashes at import time if `ANTHROPIC_API_KEY` is missing, even for code paths that never call the advanced tier — fix it.
**Model:** Claude (Sonnet)
**Result:** Changed to lazy client initialization via `_get_client()`, raising a clear `RuntimeError` only when the advanced tier is actually invoked, not on import.

---

### Prompt 11
**Asked:** Implement router logic that classifies a diff chunk as low/mid/advanced risk based on keywords, plus confidence-based escalation.
**Model:** Claude (Sonnet)
**Result:** `core/router.py` — `HIGH_RISK_KEYWORDS` list, `classify_chunk()`, `next_tier()`, `should_escalate()` with `CONFIDENCE_THRESHOLD = 0.6`.

---

### Prompt 12
**Asked:** Wire the Supervisor to real tier routing and escalation instead of always routing to low tier, and verify with a test diff.
**Model:** Claude (Sonnet)
**Result:** Supervisor correctly routed a low-confidence test diff to low tier, escalated to mid tier on low confidence, and returned the higher-confidence result with correct cost tracking.

---

### Prompt 13
**Asked:** Wire a simple in-memory store into the CLI so review results save per PR id.
**Model:** Claude (Sonnet)
**Result:** `MemoryStore` (`save`/`get` methods) wired into `cli.py`; deliberately in-process only, noted as a known limitation.

---

### Prompt 14
**Asked:** The JSON-extraction logic is duplicated identically across all three reviewer agents — refactor into a shared module.
**Model:** Claude (Sonnet)
**Result:** `core/parsing.py` with `extract_json_array()`, `extract_findings()`, `extract_confidence()`, `parse_findings()`, imported by all three agents instead of copy-pasted.

---

### Prompt 15
**Asked:** Add pricing constants and a cost-calculation function for Claude Haiku 4.5.
**Model:** Claude (Sonnet)
**Result:** `core/pricing.py` — `HAIKU_INPUT_COST_PER_MTOK`/`HAIKU_OUTPUT_COST_PER_MTOK` constants, `haiku_cost_usd()` function.

---

### Prompt 16
**Asked:** Implement the tracing module to log every AI call — tier, model, cost, latency, escalation — currently an empty stub file.
**Model:** Claude (Sonnet)
**Result:** `core/tracing.py` — `TraceEvent`/`Tracer` dataclasses, `log_call()`, `summary()` rollup.

---

### Prompt 17
**Asked:** Audit the Supervisor's cost-tracking logic — confirm free vs. paid calls are counted correctly.
**Model:** Claude (Sonnet)
**Result:** Found a real bug — mid-tier (free, local) calls were being counted in `smart_calls` (meant for paid calls only) because the original logic was `if tier == 'low': free else: smart`. Fixed to `if tier == 'advanced': smart else: free`.

---

### Prompt 18
**Asked:** Add a regression test to prevent the mid-tier cost-miscounting bug from recurring.
**Model:** Claude (Sonnet)
**Result:** `test_mid_tier_calls_are_not_miscounted_as_paid` in `test_supervisor.py`.

---

### Prompt 19
**Asked:** Add top-level error handling to the CLI so it never crashes with a raw traceback, even if every tier fails.
**Model:** Claude (Sonnet)
**Result:** `main()` wraps `run_review()` in try/except for `ValueError`, `RuntimeError`, and a catch-all, each with a clean stderr message and distinct exit code.

---

### Prompt 20
**Asked:** Write a pytest suite covering the router's classification and escalation logic.
**Model:** Claude (Sonnet)
**Result:** `test_router.py` — 9 tests covering keyword detection, case-insensitivity, tier progression, and threshold behavior.

---

### Prompt 21
**Asked:** Write a pytest suite covering the JSON parsing/extraction helpers.
**Model:** Claude (Sonnet)
**Result:** `test_parsing.py` — 12 tests covering clean JSON, surrounding prose, malformed JSON, confidence clamping, and malformed-entry skipping.

---

### Prompt 22
**Asked:** Write a pytest suite covering the pricing calculation.
**Model:** Claude (Sonnet)
**Result:** `test_pricing.py` — 4 tests covering zero tokens, pure input, pure output, and mixed token costs.

---

### Prompt 23
**Asked:** Write a pytest suite covering all three reviewer agents with mocked network calls.
**Model:** Claude (Sonnet)
**Result:** `test_agents.py` — 7 tests covering successful parsing, connection errors, timeouts, and real token-based cost computation for the advanced tier.

---

### Prompt 24
**Asked:** Write a pytest suite covering the Supervisor's escalation and cost-accounting logic.
**Model:** Claude (Sonnet)
**Result:** `test_supervisor.py` (initial version) — 4 tests covering confident-no-escalation, full escalation chain, keyword-forced routing, and the free/smart miscounting regression.

---

### Prompt 25
**Asked:** Write a pytest suite covering the in-memory store.
**Model:** Claude (Sonnet)
**Result:** `test_memory.py` — 3 tests covering save/get round-trip, missing-key lookup, and overwrite behavior.

---

### Prompt 26
**Asked:** Write a pytest suite covering the CLI's error-handling paths.
**Model:** Claude (Sonnet)
**Result:** `test_cli.py` (initial version) — tests for empty-diff `ValueError`, memory persistence, trace-summary inclusion, and graceful degradation when every tier fails.

---

### Prompt 27
**Asked:** `pytest` reports "collected 0 items" and `ModuleNotFoundError: No module named 'reviewlift'" — diagnose.
**Model:** Claude (Sonnet)
**Result:** Diagnosed as a working-directory issue — commands were being run from inside the inner `reviewlift/reviewlift` package folder rather than the outer repo root. Instructed `cd` to the correct root and verified with `pwd`.

---

### Prompt 28
**Asked:** Set up a GitHub personal access token so the MCP server isn't limited to 60 unauthenticated requests/hour.
**Model:** Claude (Sonnet)
**Result:** Walked through generating a classic token with no scopes (public repo read only), adding `GITHUB_TOKEN` to `.env`, and verified via a script hitting GitHub's `/rate_limit` endpoint (confirmed 5000/hr).

---

### Prompt 29
**Asked:** Replace the mocked MCP server (`tools/mcp_server.py`, hardcoded diff regardless of PR id) with a real MCP server using the official `mcp` SDK, fetching actual PR diffs from GitHub.
**Model:** Claude (Sonnet)
**Result:** `FastMCP`-based server exposing `get_diff`/`list_hunks` as real MCP tools, GitHub API calls with optional `GITHUB_TOKEN` auth, clean handling for 404/403/network errors.

---

### Prompt 30
**Asked:** A live CLI run against a real PR still returns mock data (`app.py`, hardcoded diff) — diagnose.
**Model:** Claude (Sonnet)
**Result:** Confirmed via `cat` that the old `MOCK_DIFF` stub was still on disk — the real implementation had been given but never actually pasted into the file. Re-applied it; confirmed fixed via a second live run.

---

### Prompt 31
**Asked:** The router's keyword list missed a real `eval()` injection bug in a test PR — expand it.
**Model:** Claude (Sonnet)
**Result:** Added `eval(`, `exec(`, `api_key`, `secret` to `HIGH_RISK_KEYWORDS`.

---

### Prompt 32
**Asked:** Create a base `calculator.py` for a public benchmark test repo, with correct implementations of add/subtract/multiply/divide/sum_range.
**Model:** Claude (Sonnet)
**Result:** 5-function calculator module, pushed as the initial commit to a new public repo (`buggy-calculator`).

---

### Prompt 33
**Asked:** Create a branch with a deliberately planted divide-by-zero bug (remove the zero-check from `divide()`).
**Model:** Claude (Sonnet)
**Result:** `bug-divide-zero` branch — `divide(a, b)` simplified to `return a / b`, no exception guard.

---

### Prompt 34
**Asked:** The CLI returns "PR not found" for a branch that was definitely pushed — diagnose.
**Model:** Claude (Sonnet)
**Result:** Diagnosed as the pull request never having been opened on GitHub — the git branch existed, but "Create pull request" was never clicked. Walked through opening it via the direct link GitHub provides after a push.

---

### Prompt 35
**Asked:** Run the CLI against real PR #1 and interpret the result.
**Model:** Claude (Sonnet)
**Result:** First run: low tier returned `confidence: 1.0` but missed the actual bug (flagged something unrelated). Second run: escalated low→mid and correctly caught the divide-by-zero issue — documented as evidence of the "confidently wrong" limitation.

---

### Prompt 36
**Asked:** Create a branch with a deliberately planted `eval()` injection vulnerability.
**Model:** Claude (Sonnet)
**Result:** `bug-eval-injection` branch — added a `calculate(expression): return eval(expression)` function.

---

### Prompt 37
**Asked:** PR #2 (the eval-injection PR) routed to low tier instead of advanced tier — diagnose.
**Model:** Claude (Sonnet)
**Result:** Confirmed via `cat router.py` that the earlier keyword expansion (Prompt 31) had been given but never actually applied to the file. Re-applied it and confirmed correct routing on re-run.

---

### Prompt 38
**Asked:** Confirm the advanced tier fires correctly after the keyword fix.
**Model:** Claude (Sonnet)
**Result:** Re-ran PR #2 — confirmed `calls_by_tier: {"advanced": 1}`, nonzero `total_cost_usd` (first live paid call), and a correct finding: *"Use of eval() is a critical security vulnerability."*

---

### Prompt 39
**Asked:** Build a utility that splits a multi-file unified diff into one chunk per file.
**Model:** Claude (Sonnet)
**Result:** `core/diff_split.py` — `split_diff_by_file()`, splitting on `diff --git a/X b/Y` headers, with a fallback for diffs with no recognizable headers.

---

### Prompt 40
**Asked:** Write a pytest suite covering the diff-splitting utility.
**Model:** Claude (Sonnet)
**Result:** `test_diff_split.py` — 4 tests covering two-file splits, single-file diffs, no-header fallback, and empty input.

---

### Prompt 41
**Asked:** Refactor the Supervisor so it splits a PR into one task per file and dispatches each to a worker concurrently, rather than treating the whole diff as one chunk.
**Model:** Claude (Sonnet)
**Result:** Rewrote `Supervisor.review()` to use `ThreadPoolExecutor`, submitting one `_review_chunk()` call per file, running concurrently.

---

### Prompt 42
**Asked:** The merged cost report sums `seconds_elapsed` across concurrently-running files, which overstates wall-clock time — fix it.
**Model:** Claude (Sonnet)
**Result:** Changed to `max()` across workers for elapsed time (correct for concurrency), while cost and call counts remain additive.

---

### Prompt 43
**Asked:** Add a test proving the Supervisor correctly dispatches different files to different tiers within the same PR.
**Model:** Claude (Sonnet)
**Result:** `test_multi_file_diff_dispatches_each_file_independently` — a diff with a "safe" file and a "password"-containing file, verifying one routes low and one routes advanced.

---

### Prompt 44
**Asked:** Add a test proving concurrent execution genuinely reduces wall-clock time (not just relabeling a sequential loop).
**Model:** Claude (Sonnet)
**Result:** `test_parallel_time_uses_max_not_sum` — two files each taking 2.0s (mocked), asserting total elapsed is ~2.0s, not ~4.0s.

---

### Prompt 45
**Asked:** Add mode support (`adaptive`/`free_only`/`smart_only`) to the Supervisor so the same PR can be benchmarked against its own extremes.
**Model:** Claude (Sonnet)
**Result:** Added `mode` parameter, `_starting_tier()`/`_next_tier()` mode-aware logic, `VALID_MODES` validation.

---

### Prompt 46
**Asked:** Verify each mode starts at the correct tier.
**Model:** Claude (Sonnet)
**Result:** Direct script confirming `adaptive→low`, `free_only→low`, `smart_only→advanced`.

---

### Prompt 47
**Asked:** Create a branch with a deliberately planted off-by-one bug in a loop bound.
**Model:** Claude (Sonnet)
**Result:** `bug-off-by-one` branch — `sum_range()`'s loop changed from `range(1, n + 1)` to `range(1, n)`.

---

### Prompt 48
**Asked:** Create a branch with a deliberately hardcoded API secret.
**Model:** Claude (Sonnet)
**Result:** `bug-hardcoded-secret` branch — added `API_KEY = "sk-live-..."` as a module-level constant.

---

### Prompt 49
**Asked:** Build a benchmark runner that sends a fixed set of real PRs through all three modes and reports cost/time/findings for each.
**Model:** Claude (Sonnet)
**Result:** `benchmark/run_benchmark.py` — `run_single()`, `run_all()`, `summarize()`, `print_report()`, saving full results to `benchmark_results.json`.

---

### Prompt 50
**Asked:** The first full benchmark run only completed 6 of 12 combinations — 2 PRs returned "PR not found."
**Model:** Claude (Sonnet)
**Result:** Diagnosed as PRs #3 and #4 having pushed branches but never having had their pull requests opened (same root cause as Prompt 34). Walked through creating both missing PRs.

---

### Prompt 51
**Asked:** Re-run the full benchmark after creating the missing PRs.
**Model:** Claude (Sonnet)
**Result:** All 12 runs completed successfully. Results: adaptive matched smart-only's findings exactly (100% parity) at 37.5% lower cost, with adaptive running slower on average (0.42x — roughly 2x the wall-clock time) due to escalation latency.

---

### Prompt 52
**Asked:** Write `rules.md` documenting the actual routing policy, its rationale, known limitations, and the real benchmark results.
**Model:** Claude (Sonnet)
**Result:** `rules.md` — threshold/keyword reasoning, the documented "confidently wrong" failure case from Prompt 35, the benchmark table, and next-step ideas.

---

### Prompt 53
**Asked:** Rewrite `README.md` to reflect the real architecture and results, replacing the original stub-era description.
**Model:** Claude (Sonnet)
**Result:** New README covering setup, architecture (text diagram), running the CLI/benchmark/tests, real status, and known limitations.

---

### Prompt 54
**Asked:** Draft a status update email to the mentor summarizing progress.
**Model:** Claude (Sonnet)
**Result:** First draft — detailed day-by-day breakdown of scaffold, routing, and full-pipeline/benchmark work.

---

### Prompt 55
**Asked:** Revise the email with a specific dated timeline (July 31 – Aug 4).
**Model:** Claude (Sonnet)
**Result:** Second draft with per-day bullet points; flagged that some earlier dates were inferred, not directly confirmed from the source document.

---

### Prompt 56
**Asked:** Drop the timeline entirely — focus purely on what's been completed (MCP, routing, Supervisor).
**Model:** Claude (Sonnet)
**Result:** Third draft — completion-focused, no dates, mentions the presentation date and that slides are starting.

---

### Prompt 57
**Asked:** Shorten the email further.
**Model:** Claude (Sonnet)
**Result:** Final concise version — four sentences covering the pipeline, MCP, the benchmark result, and what's left.

---

### Prompt 58
**Asked:** Add retry logic so each tier retries once on transient network failure before falling back to an error result.
**Model:** Claude (Sonnet)
**Result:** `core/retry.py` — `retry_call()`, a generic wrapper retrying any function call up to N times with a delay, re-raising the last exception if all attempts fail.

---

### Prompt 59
**Asked:** Wire the retry wrapper into the low-tier reviewer agent.
**Model:** Claude (Sonnet)
**Result:** `LowTierReviewerAgent.review()` now calls `retry_call(requests.post, ...)` instead of calling `requests.post` directly.

---

### Prompt 60
**Asked:** Wire the retry wrapper into the mid-tier reviewer agent.
**Model:** Claude (Sonnet)
**Result:** Same pattern applied to `MidTierReviewerAgent.review()`.

---

### Prompt 61
**Asked:** Wire the retry wrapper into the advanced reviewer agent.
**Model:** Claude (Sonnet)
**Result:** `AdvancedReviewerAgent.review()` now calls `retry_call(client.messages.create, ...)`.

---

### Prompt 62
**Asked:** Add diff-hash-based caching so re-reviewing an identical PR skips model calls entirely.
**Model:** Claude (Sonnet)
**Result:** `core/cache.py` — SHA-256 hash of the diff as a cache key, persisted to `.reviewlift_cache.json` on disk (unlike `MemoryStore`, which is in-process only).

---

### Prompt 63
**Asked:** Add a secondary AI feature: a plain-English summary of the structured findings, for a developer skimming their PR.
**Model:** Claude (Sonnet)
**Result:** `agents/summarizer.py` — `SummarizerAgent.summarize()`, using phi3 to turn a findings list into 2-3 sentences of prose.

---

### Prompt 64
**Asked:** Wire caching, the summarizer, and progress messages into the CLI.
**Model:** Claude (Sonnet)
**Result:** `cli.py` rewritten — checks cache before running the pipeline, calls `SummarizerAgent` after getting findings, prints stderr progress messages during a run, and caches the final output.

---

### Prompt 65
**Asked:** Write an AI-generated usage guide covering CLI usage, output schema, environment variables, caching, and retry behavior.
**Model:** Claude (Sonnet)
**Result:** `docs/USAGE.md`.

---

### Prompt 66
**Asked:** After adding caching, one CLI test fails intermittently with a confidence value from a different test — diagnose.
**Model:** Claude (Sonnet)
**Result:** Diagnosed as disk-cache pollution: several tests used the identical mock diff string, so whichever test ran first populated the real on-disk cache, and later tests received that cached result instead of their own mocks' output.

---

### Prompt 67
**Asked:** Prevent the cache file from being tracked in git.
**Model:** Claude (Sonnet)
**Result:** Added `.reviewlift_cache.json` to `.gitignore`; deleted the existing polluted cache file.

---

### Prompt 68
**Asked:** Rewrite the CLI test suite so every test explicitly bypasses the cache, plus add coverage for the new summary field and cache-hit behavior.
**Model:** Claude (Sonnet)
**Result:** `test_cli.py` rewritten — every test now mocks `get_cached`/`set_cached`; added `test_run_review_includes_ai_generated_summary` and `test_run_review_returns_cached_result_on_cache_hit`.

---

### Prompt 69
**Asked:** Re-run the full test suite after the cache-isolation fix.
**Model:** Claude (Sonnet)
**Result:** 50 passed, 0 failed.

---

### Prompt 70
**Asked:** What does "benchmark" mean in the context of this project?
**Model:** Claude (Sonnet)
**Result:** Explained the benchmark as running the same 4 real PRs through three Supervisor modes, measuring cost/time/findings for each, to empirically test the proposal's central cost-vs-quality claim rather than asserting it.

---

### Prompt 71
**Asked:** Are all 3 LLMs (phi3, mistral, Claude Haiku) genuinely being exercised, or just some of them?
**Model:** Claude (Sonnet)
**Result:** Audited actual CLI run logs — confirmed phi3 and mistral had fired via real PR #1 runs, but Claude Haiku had not yet fired on a live PR at that point (only in isolated tests); recommended a real security-flagged PR to confirm it.

---

### Prompt 72
**Asked:** Will using the MCP server require a GitHub API token?
**Model:** Claude (Sonnet)
**Result:** Explained the rate-limit difference (60/hr unauthenticated vs 5000/hr with a token), confirmed no special scopes are needed for public repos, and noted the code already checks for `GITHUB_TOKEN` automatically.

---

### Prompt 73
**Asked:** Can the MCP server pull any public PR, or only ones owned by my account?
**Model:** Claude (Sonnet)
**Result:** Confirmed `get_diff()` takes `owner/repo#number` with no ownership restriction — any public repo's PR works identically.

---

### Prompt 74
**Asked:** Is the current `mcp_server.py` implementation actually real MCP, or just a REST wrapper labeled as MCP?
**Model:** Claude (Sonnet)
**Result:** Acknowledged the earlier version was a plain Python function, not real MCP — no protocol layer, no tool schema. Rebuilt it using the official `mcp` SDK's `FastMCP` class with `@mcp.tool()` decorators, making it a genuine, connectable MCP server.

---

### Prompt 75
**Asked:** Explain the routing rules briefly.
**Model:** Claude (Sonnet)
**Result:** Summarized the two decision points — the keyword list (instant escalation to advanced) and the 0.6 confidence threshold (escalation on uncertainty) — with the full ladder (low→mid→advanced).

---

### Prompt 76
**Asked:** Other than confidence, what other parameters does the routing decision depend on?
**Model:** Claude (Sonnet)
**Result:** Clarified that only the keyword match and the per-file split (each file gets an independent routing decision) affect routing; everything else (severity, cost, time, tier used, escalation count) is recorded in the output but doesn't feed back into the decision.

---

### Prompt 77
**Asked:** Why does the adaptive mode run slower than smart-only in the benchmark, when the goal was cost savings?
**Model:** Claude (Sonnet)
**Result:** Explained that escalation chains (trying low, then mid, before reaching advanced) add sequential latency that going straight to the expensive tier avoids — documented as an honest, real tradeoff rather than adjusted to look better.

---

### Prompt 78
**Asked:** Doesn't a small local model tend to be confidently wrong most of the time, undermining confidence-based escalation?
**Model:** Claude (Sonnet)
**Result:** Confirmed this as a real, observed limitation (citing the phi3 `confidence: 1.0` / actually-wrong case from Prompt 35), explained why small models often fail at calibrated self-reported confidence, and suggested measuring confidence-vs-correctness across the benchmark data as a citable finding.

---

### Prompt 79
**Asked:** Which of the 4 benchmark PRs is the ideal one to run live during a presentation demo?
**Model:** Claude (Sonnet)
**Result:** Recommended PR #2 (eval-injection) — deterministic keyword-triggered routing (no escalation-timing risk), fast (single Claude call), and an intuitively understandable security finding for a live audience.

---

### Prompt 80
**Asked:** Why does `benchmark_results.json` need to exist as a separate file when the CLI already prints results to the terminal?
**Model:** Claude (Sonnet)
**Result:** Clarified that a single CLI run only ever reviews one PR in one mode (`adaptive`), while the benchmark file is the only persistent record of the 12-run, 3-mode, 4-PR comparison — a fundamentally different, larger operation that terminal scrollback can't reconstruct.

---

### Prompt 81
**Asked:** Does `python3 -m reviewlift.cli review owner/repo#N` review all pull requests, or just the one specified?
**Model:** Claude (Sonnet)
**Result:** Confirmed it reviews only the single PR number given; reviewing all 4 requires either 4 separate CLI invocations or running the benchmark script.

---

### Prompt 82
**Asked:** Diagnose a `heredoc>` stuck prompt in the terminal after pasting a large code block.
**Model:** Claude (Sonnet)
**Result:** Identified the paste as having been cut off before reaching the closing delimiter; instructed `Ctrl+C` to cancel, confirm return to a normal prompt, then re-paste the full block in one motion.

---

### Prompt 83
**Asked:** Diagnose a second `heredoc>` stuck prompt during the mid-tier reviewer file creation.
**Model:** Claude (Sonnet)
**Result:** Same diagnosis and fix as Prompt 82 — confirmed truncated paste, walked through cancel-and-retry.

---

### Prompt 84
**Asked:** Diagnose `ModuleNotFoundError: No module named 'reviewlift'` when running `python3 -m reviewlift.cli`.
**Model:** Claude (Sonnet)
**Result:** Confirmed via `pwd` that the command was being run from inside the `reviewlift/reviewlift` package folder rather than repo root; corrected with `cd` and re-verified.

---

### Prompt 85
**Asked:** Diagnose `pytest` reporting `ERROR: file or directory not found: tests/` despite `tests/` clearly existing.
**Model:** Claude (Sonnet)
**Result:** Confirmed the terminal prompt showed the working directory was already inside `tests/` itself, so the relative path didn't resolve; corrected with `cd ..` back to repo root.

---

### Prompt 86
**Asked:** Diagnose why a `git commit`/`push` sequence appeared to silently do nothing.
**Model:** Claude (Sonnet)
**Result:** Requested `git log -1 --oneline` and `git status` output to confirm the commit had actually landed and the working tree was clean, rather than assuming failure from an ambiguous terminal screenshot.

---

### Prompt 87
**Asked:** Confirm whether `benchmark_results.json` line counts and content matched what the runner script was expected to produce.
**Model:** Claude (Sonnet)
**Result:** Read the pasted screenshot's JSON content directly, cross-checked the `mode`/`cost_usd`/`findings` fields against expected values for `free_only` vs `smart_only` runs of the same PR, and confirmed correctness.

---

### Prompt 88
**Asked:** Should the project incorporate a secondary AI feature, output validation/retry, and caching as first-class requirements rather than skip them?
**Model:** Claude (Sonnet)
**Result:** Agreed to build all three for real rather than treating them as optional, and sequenced them by dependency (retry first, since caching and summarization don't depend on it but are simpler to reason about after retry is in place).

---

### Prompt 89
**Asked:** Bring the full content of `rules.md` as a single copy-pasteable block instead of split across multiple messages.
**Model:** Claude (Sonnet)
**Result:** Consolidated the entire `rules.md` heredoc into one continuous shell command block.

---

### Prompt 90
**Asked:** Bring the full content of `README.md` as a single copy-pasteable block.
**Model:** Claude (Sonnet)
**Result:** Consolidated the entire README heredoc into one block, using plain-text section separators instead of nested code fences (to avoid heredoc-delimiter conflicts).

---

### Prompt 91
**Asked:** Confirm whether Claude Haiku 4.5's current per-token pricing was accurate before using it in `pricing.py`.
**Model:** Claude (Sonnet)
**Result:** Searched current pricing directly rather than relying on training-data memory; confirmed $1/M input, $5/M output tokens, cited as of Aug 2026.

---

### Prompt 92
**Asked:** Why did the Anthropic billing dashboard still show $0.00 spend shortly after a confirmed real paid API call?
**Model:** Claude (Sonnet)
**Result:** Explained dashboard reporting lag (minutes to hours) and that the actual charge (~$0.0013) was small enough to round to $0.00 in a two-decimal display; suggested verifying the API key belonged to the same account being viewed.

---

### Prompt 93
**Asked:** Split the work completed into a 4-day breakdown and draft a completion email in one request.
**Model:** Claude (Sonnet)
**Result:** Provided a caveat that only partial day-by-day content had been directly observed from the source document, then produced a best-effort dated breakdown alongside the requested email draft.

---

### Prompt 94
**Asked:** Regenerate the status email with a shorter subject/body while retaining the four key technical points.
**Model:** Claude (Sonnet)
**Result:** Final compressed version — one paragraph on what's built, one line on the benchmark result, one line on what's left and the presentation date.

---

### Prompt 95
**Asked:** Confirm whether the project currently satisfies all Week 7 program checklist requirements.
**Model:** Claude (Sonnet)
**Result:** Produced a requirement-by-requirement table (done / partial / not built) rather than a single yes/no answer, distinguishing genuinely complete items from ones only partially addressed.

---

### Prompt 96
**Asked:** After the retry/caching/summarizer additions, re-confirm what remains as a core feature gap versus what's just presentation packaging.
**Model:** Claude (Sonnet)
**Result:** Updated the requirement table — marked multi-model routing, secondary AI feature, retry/fallback, caching, and usage docs as done; left only deployment and a true integration/E2E test as genuine core gaps.

---

### Prompt 97
**Asked:** Explain, in easy language, what parameters the system evaluates on, excluding project-timing questions.
**Model:** Claude (Sonnet)
**Result:** Reduced the explanation to two plain-language checks — "does the code contain a risky keyword" and "was the cheap model actually confident" — separating decision-making parameters from output/reporting fields.

---

### Prompt 98
**Asked:** List all other tracked/reported parameters beyond the two that decide routing.
**Model:** Claude (Sonnet)
**Result:** Enumerated severity, cost, latency, model/tier used, escalation count, and file/line location as recorded-but-non-decision-making fields.

---

### Prompt 99
**Asked:** Verify the full pytest suite one final time after all feature additions, before committing.
**Model:** Claude (Sonnet)
**Result:** Confirmed 50 passed, 0 failed; proceeded to commit and push the full retry/caching/summarizer/docs feature batch.

---
