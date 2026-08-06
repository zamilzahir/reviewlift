"""Benchmark runner: sends the same 4 real PRs through three setups
(free-only, smart-only, ReviewLift's adaptive routing) and reports
cost, time, and bugs caught for each.
"""

import json
import time

from reviewlift.agents.supervisor import Supervisor
from reviewlift.tools.mcp_server import get_diff

BENCHMARK_PRS = [
    "zamilzahir/buggy-calculator#1",
    "zamilzahir/buggy-calculator#2",
    "zamilzahir/buggy-calculator#3",
    "zamilzahir/buggy-calculator#4",
]

MODES = ["free_only", "smart_only", "adaptive"]


def run_single(pr_id: str, mode: str) -> dict:
    diff = get_diff(pr_id)
    supervisor = Supervisor(mode=mode)

    start = time.perf_counter()
    result, cost_report = supervisor.review(diff)
    wall_seconds = time.perf_counter() - start

    return {
        "pr_id": pr_id,
        "mode": mode,
        "num_findings": len(result.findings),
        "min_confidence": result.confidence,
        "cost_usd": cost_report.total_cost_usd,
        "wall_seconds": wall_seconds,
        "free_calls": cost_report.free_calls,
        "smart_calls": cost_report.smart_calls,
        "findings": [
            {"file": f.file, "line": f.line, "message": f.message, "severity": f.severity}
            for f in result.findings
        ],
    }


def run_all() -> list[dict]:
    results = []
    for pr_id in BENCHMARK_PRS:
        for mode in MODES:
            print(f"Running {pr_id} in mode={mode} ...")
            try:
                results.append(run_single(pr_id, mode))
            except Exception as e:
                print(f"  FAILED: {e}")
                results.append({
                    "pr_id": pr_id, "mode": mode, "error": str(e),
                    "num_findings": 0, "cost_usd": 0.0, "wall_seconds": 0.0,
                })
    return results


def summarize(results: list[dict]) -> dict:
    summary = {}
    for mode in MODES:
        mode_results = [r for r in results if r["mode"] == mode]
        n = len(mode_results) or 1
        summary[mode] = {
            "total_cost_usd": round(sum(r["cost_usd"] for r in mode_results), 6),
            "avg_cost_usd": round(sum(r["cost_usd"] for r in mode_results) / n, 6),
            "avg_wall_seconds": round(sum(r["wall_seconds"] for r in mode_results) / n, 3),
            "avg_findings": round(sum(r["num_findings"] for r in mode_results) / n, 2),
            "total_findings": sum(r["num_findings"] for r in mode_results),
        }
    return summary


def print_report(results: list[dict], summary: dict) -> None:
    print("\n" + "=" * 60)
    print("BENCHMARK REPORT")
    print("=" * 60)
    print(f"{'Mode':<12} {'Total Cost':<14} {'Avg Time (s)':<14} {'Avg Findings':<14}")
    print("-" * 60)
    for mode in MODES:
        s = summary[mode]
        print(f"{mode:<12} ${s['total_cost_usd']:<13} {s['avg_wall_seconds']:<14} {s['avg_findings']:<14}")

    smart_cost = summary["smart_only"]["total_cost_usd"]
    adaptive_cost = summary["adaptive"]["total_cost_usd"]
    if smart_cost > 0:
        pct_saved = round((1 - adaptive_cost / smart_cost) * 100, 1)
        print(f"\nCost saved vs smart-only: {pct_saved}%")

    smart_time = summary["smart_only"]["avg_wall_seconds"]
    adaptive_time = summary["adaptive"]["avg_wall_seconds"]
    if smart_time > 0 and adaptive_time > 0:
        speedup = round(smart_time / adaptive_time, 2)
        print(f"Speed vs smart-only: {speedup}x faster")

    if summary["smart_only"]["total_findings"] > 0:
        findings_ratio = round(
            summary["adaptive"]["total_findings"] / summary["smart_only"]["total_findings"] * 100, 1
        )
        print(f"Findings caught vs smart-only: {findings_ratio}%")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    results = run_all()
    summary = summarize(results)
    print_report(results, summary)

    with open("benchmark_results.json", "w") as f:
        json.dump({"results": results, "summary": summary}, f, indent=2)
    print("Full results saved to benchmark_results.json")
