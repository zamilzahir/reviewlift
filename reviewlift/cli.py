import argparse
import json
import sys
from dataclasses import asdict

from reviewlift.agents.summarizer import SummarizerAgent
from reviewlift.agents.supervisor import Supervisor
from reviewlift.core.cache import get_cached, set_cached
from reviewlift.memory.store import MemoryStore
from reviewlift.tools.mcp_server import get_diff


def run_review(pr_id: str, memory: MemoryStore) -> dict:
    diff = get_diff(pr_id)
    if not diff or not diff.strip():
        raise ValueError(f"No diff content found for '{pr_id}'.")

    cached = get_cached(diff)
    if cached is not None:
        print(f"reviewlift: cache hit for {pr_id} — skipping model calls", file=sys.stderr)
        memory.save(pr_id, cached)
        return cached

    print(f"reviewlift: fetching and reviewing {pr_id} ...", file=sys.stderr)
    supervisor = Supervisor()
    result, cost_report = supervisor.review(diff)

    findings_dicts = [asdict(f) for f in result.findings]
    print(f"reviewlift: generating summary ...", file=sys.stderr)
    summary = SummarizerAgent().summarize(
        findings_dicts, num_files_reviewed=cost_report.free_calls + cost_report.smart_calls
    )

    output = {
        "pr_id": pr_id,
        "summary": summary,
        "findings": findings_dicts,
        "confidence": result.confidence,
        "cost_report": asdict(cost_report),
        "trace_summary": supervisor.tracer.summary(),
    }
    memory.save(pr_id, output)
    set_cached(diff, output)
    return output


def main():
    parser = argparse.ArgumentParser(prog="reviewlift")
    parser.add_argument("command", choices=["review"])
    parser.add_argument("pr_id", help="PR id, e.g. owner/repo#123")
    args = parser.parse_args()

    memory = MemoryStore()
    try:
        output = run_review(args.pr_id, memory)
    except ValueError as e:
        print(f"reviewlift: invalid input — {e}", file=sys.stderr)
        sys.exit(2)
    except RuntimeError as e:
        print(f"reviewlift: configuration error — {e}", file=sys.stderr)
        sys.exit(3)
    except Exception as e:
        print(f"reviewlift: unexpected error — {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
