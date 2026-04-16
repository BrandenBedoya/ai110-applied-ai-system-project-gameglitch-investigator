"""
Standalone evaluation script for the GameGlitch Debug Agent.

Runs the agent against all 5 known scenarios, scores results,
and writes a JSON report to eval_results.json.

Usage:
    python eval.py
    python eval.py --verbose
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

if not os.getenv("ANTHROPIC_API_KEY"):
    print("ERROR: ANTHROPIC_API_KEY is not set.")
    print("Create a .env file with: ANTHROPIC_API_KEY=sk-ant-...")
    sys.exit(1)

from src.agent.debug_agent import analyze_code
from src.game.scenarios import SCENARIOS


# ── Scoring ───────────────────────────────────────────────────────────────────


def score_result(result: dict, scenario: dict) -> dict:
    """Score an agent result against a known scenario."""
    report = result["report"].lower()
    keyword_hits = sum(1 for kw in scenario["expected_keywords"] if kw in report)
    keyword_score = keyword_hits / len(scenario["expected_keywords"])
    type_matched = scenario["expected_bug_type"] in report
    overall = 0.5 * keyword_score + 0.5 * float(type_matched)

    return {
        "scenario_id": scenario["id"],
        "scenario_name": scenario["name"],
        "keyword_score": round(keyword_score, 3),
        "keyword_hits": f"{keyword_hits}/{len(scenario['expected_keywords'])}",
        "bug_type_matched": type_matched,
        "overall_score": round(overall, 3),
        "agent_iterations": result["iterations"],
        "tool_calls_made": len(result["tool_calls"]),
    }


# ── Main ──────────────────────────────────────────────────────────────────────


def main(verbose: bool = False) -> None:
    sep = "=" * 64
    print(sep)
    print("  GameGlitch Debug Agent — Reliability Evaluation")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(sep)

    scores = []
    for scenario in SCENARIOS:
        print(f"\nRunning: {scenario['name']} ({scenario['id']})...")
        result = analyze_code(scenario["buggy_code"], "")
        score = score_result(result, scenario)
        scores.append(score)

        status = "PASS" if score["overall_score"] >= 0.5 else "FAIL"
        print(
            f"  [{status}] Score: {score['overall_score']:.0%} | "
            f"Keywords: {score['keyword_hits']} | "
            f"Type matched: {'✓' if score['bug_type_matched'] else '✗'} | "
            f"Iterations: {score['agent_iterations']} | "
            f"Tool calls: {score['tool_calls_made']}"
        )

        if verbose:
            print(f"\n  Agent report preview:\n  {result['report'][:400]}\n")

    avg = sum(s["overall_score"] for s in scores) / len(scores)
    print(f"\n{sep}")
    print(f"  Overall Reliability Score: {avg:.0%}  ({avg:.3f})")
    print(sep)

    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": "claude-sonnet-4-6",
        "scenario_count": len(scores),
        "average_score": round(avg, 3),
        "results": scores,
    }

    with open("eval_results.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print("\nResults saved to eval_results.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate the GameGlitch debug agent.")
    parser.add_argument("--verbose", action="store_true", help="Print full agent reports.")
    args = parser.parse_args()
    main(verbose=args.verbose)
