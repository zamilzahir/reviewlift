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