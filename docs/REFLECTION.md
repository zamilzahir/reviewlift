# Reflection — ReviewLift

**Zamil Zahir · Arbisoft AI-Focused Internship 2026 · Phase 3**

---

## 1. What the project set out to do

ReviewLift tests a specific claim: that routing code review across a tier of models — free local models for simple checks, a paid cloud model only where the code warrants it — can deliver near-expensive-model review quality at meaningfully lower cost.

The point was never just to build a working pipeline. It was to build one and then **measure whether the claim actually holds**, and report the result either way.

---

## 2. Where AI helped most

**Scaffolding and boilerplate.** The initial project structure — agents, core models, tool registry, CLI entrypoint — came together far faster with AI assistance than writing it by hand. Dataclasses, argument parsing, package layout: all mechanical work where AI is reliably good.

**Writing tests.** This was the single biggest time saver. Generating 50 tests covering routing logic, JSON parsing, pricing math, agent behavior with mocked network calls, Supervisor concurrency, and CLI error paths would have taken days manually. AI produced them in minutes, and — importantly — most of them were correct on the first run.

**Catching my own bugs when asked to audit.** When I explicitly asked "audit the cost-tracking logic," AI found a real bug I had not noticed: mid-tier calls (free, local) were being counted in `smart_calls`, the counter meant for paid calls only. The original condition was `if tier == 'low': free else: smart`, which lumped mid in with advanced. Since the entire project's headline claim is a cost comparison, this bug would have quietly corrupted every number in my benchmark. It was found because I asked for an audit, not because it surfaced on its own.

**Explaining unfamiliar territory.** MCP was new to me. AI was useful for understanding the protocol, the difference between a real MCP server and a plain function wrapper, and how a client connects to one over stdio.

---

## 3. Where AI got things wrong

**It initially built the wrong thing and called it MCP.** The first "MCP server" I was given was a plain Python function that called the GitHub REST API. No protocol layer, no tool schema, nothing an MCP client could connect to. It was named `mcp_server.py` and functioned correctly, so it looked right. Only when I pushed back — "won't I need actual GitHub MCP?" — was it acknowledged as not real MCP and rebuilt properly using the official SDK with `FastMCP` and `@mcp.tool()` decorators.

**Lesson:** a plausible-looking implementation with the right filename is not the same as the right implementation. If I hadn't questioned it, the project would have shipped claiming an MCP integration it didn't have.

**It gave me code that never got applied — twice — and I didn't notice.** On two separate occasions, code was generated and I moved on without actually pasting it into the file. The first time, the mocked MCP server stayed in place, so a "live" CLI run returned hardcoded mock data (`app.py`) instead of my real repo's `calculator.py`. The second time, an expanded keyword list never landed, so a PR containing an obvious `eval()` injection was routed to the cheap local model instead of the security-capable one.

**Lesson:** both were caught only by reading the output carefully and noticing it didn't match reality — not by any error message. Nothing crashed. The system did exactly what its actual code said to do; the code just wasn't what I thought it was.

**Small local models are unreliable in a specific way I didn't anticipate.** phi3 returned `confidence: 1.0` on a diff where the divide-by-zero guard had been deliberately removed — and completely missed the bug, flagging something vague and unrelated instead. A second run of the identical PR did escalate and caught it. Same code, same model, opposite outcomes.

This is the most interesting failure in the project, because it exposes a limitation in my own design: **confidence-based escalation only catches models that know they don't know.** It has no defense against a model that is wrong and certain. The escalation mechanism I built is not a safety net for incorrectness — only for admitted uncertainty. That distinction was not obvious to me when I designed it.

**The benchmark silently ran on half the data.** The first full benchmark run reported clean-looking results — 39.9% cost saved, 80% findings parity. Those numbers were wrong, because 6 of 12 runs had failed with "PR not found." Two branches had been pushed to GitHub but their pull requests were never actually opened. The script caught the exceptions and continued, so the summary printed as if it were complete.

**Lesson:** a benchmark that degrades gracefully can produce numbers that look valid while being computed from a partial sample. I only caught it by reading the failure lines above the summary table rather than skipping to the result.

---

## 4. The result I did not expect

My proposal's illustrative chart predicted ReviewLift would be both cheaper **and** faster than sending everything to the expensive model. The real benchmark showed something different:

| Mode | Total cost | Avg time/PR | Avg findings/PR |
|---|---|---|---|
| free_only | $0.00 | 9.56s | 1.25 |
| smart_only | $0.00403 | 2.24s | 2.0 |
| adaptive | $0.002518 | 5.32s | 2.0 |

The cost and quality claims held: **37.5% cheaper, with 100% of the findings smart-only caught.** But adaptive ran **slower**, not faster — roughly 2x the wall-clock time. The reason is structural: escalation means trying a cheap tier, waiting on it, evaluating confidence, and only then reaching the strong model. Going straight to the expensive model skips all of that.

I chose to report this as measured rather than quietly reframe it. The honest conclusion is that ReviewLift **buys cost savings with latency** — not both. Whether that trade is worth taking depends on whether a team values review turnaround or spend more. That is a real engineering decision, not a strictly-better result, and presenting it as one would have been misleading.

---

## 5. What I would do differently

**Verify that generated code actually landed before moving on.** Both silent failures in this project came from the same habit. A quick `cat` on the file, or watching for the expected change in behavior, would have caught both immediately.

**Design the escalation trigger to not depend solely on self-reported confidence.** Given what I observed about phi3's calibration, a second independent trigger — diff size, complexity, whether a change touches exception handling or control flow — would catch the confidently-wrong case that confidence thresholds structurally cannot.

**Validate benchmark inputs before running the benchmark.** A pre-flight check confirming every PR in the list actually exists and returns a non-empty diff would have prevented the half-complete run entirely.

**Question implementations that look right.** The MCP issue is the clearest example. Correct filename, correct function names, working behavior — and still not the thing the requirement asked for.

---

## 6. What I take from this

The engineering was the easier half. Wiring three models together, splitting diffs, dispatching workers concurrently, tracking token costs — all of that is tractable, and AI assistance made it fast.

The harder and more valuable half was **not trusting my own system**. Every meaningful finding in this project — the miscounted costs, the mock data masquerading as live, the mis-routed security bug, the half-empty benchmark, the confidently-wrong local model — came from checking whether the output actually matched what I believed the code was doing. None of them announced themselves. Nothing crashed. The system kept producing plausible, well-formatted, entirely wrong results.

That applies directly to what ReviewLift itself is for. It is a tool that uses AI to check code, built by someone using AI to write code. Both cases share the same failure mode: output that looks right is not evidence that it is right. The measuring, the tests, and the willingness to report an unflattering latency number are what separate a demo from a result.
