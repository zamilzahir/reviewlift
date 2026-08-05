import argparse
import json
import sys
from dataclasses import asdict

from reviewlift.agents.supervisor import Supervisor
from reviewlift.memory.store import MemoryStore
from reviewlift.tools.mcp_server import get_diff


def run_review(pr_id: str, memory: MemoryStore) -> dict:
    diff = get_diff(pr_id)
    if not diff or not diff.strip():
        raise ValueError(f"No diff content found for '{pr_id}'.")

    supervisor = Supervisor()
    result, cost_report = supervisor.review(diff)

    output = {
        "pr_id": pr_id,
        "findings": [asdict(f) for f in result.findings],
        "confidence": result.confidence,
        "cost_report": asdict(cost_report),
        "trace_summary": supervisor.tracer.summary(),
    }
    memory.save(pr_id, output)
    return output


def main():
    parser = argparse.ArgumentParser(prog="reviewlift")
    parser.add_argument("command", choices=["review"])
    parser.add_argument("pr_id", help="PR id or path to a diff file (mocked for now)")
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