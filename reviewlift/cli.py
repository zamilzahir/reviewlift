import argparse
import json
from dataclasses import asdict

from reviewlift.agents.supervisor import Supervisor
from reviewlift.tools.mcp_server import get_diff


def main():
    parser = argparse.ArgumentParser(prog="reviewlift")
    parser.add_argument("command", choices=["review"])
    parser.add_argument("pr_id", help="PR id or path to a diff file (mocked for now)")
    args = parser.parse_args()

    diff = get_diff(args.pr_id)
    supervisor = Supervisor()
    result, cost_report = supervisor.review(diff)

    output = {
        "findings": [asdict(f) for f in result.findings],
        "confidence": result.confidence,
        "cost_report": asdict(cost_report),
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()