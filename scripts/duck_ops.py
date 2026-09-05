#!/usr/bin/env python3
"""Read-only process preflight and offline development trace comparison."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiment_ops.activity import inspect
from experiment_ops.compare import compare
from experiment_ops.report import render


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    commands = p.add_subparsers(dest="command", required=True)
    for name in ("activity", "guard"):
        sub = commands.add_parser(name, help="Inspect known local training processes; guard exits 3 while busy, 2 if unknown")
        sub.add_argument("--root", type=Path, default=ROOT)
    sub = commands.add_parser("compare", help="Compare retained JSONL traces without running a simulator")
    sub.add_argument("left", type=Path)
    sub.add_argument("right", type=Path)
    sub.add_argument("--position-tolerance-m", type=float, default=1e-6)
    sub.add_argument("--action-width", type=int, default=14)
    sub.add_argument("--output", type=Path, required=True, help="New report directory; existing output is never overwritten")
    args = p.parse_args(argv)
    try:
        if args.command in {"activity", "guard"}:
            result = inspect(args.root)
            print(json.dumps(result, indent=2))
            if result["status"] == "unknown":
                return 2
            return 3 if args.command == "guard" and result["status"] == "busy" else 0
        if args.output.exists():
            raise ValueError("output already exists; use a new comparison directory")
        result = compare(args.left, args.right, position_tolerance_m=args.position_tolerance_m,
                         action_width=args.action_width)
        html = render(result)
        report_bytes = json.dumps(result, indent=2, allow_nan=False) + "\n"
        # Reserve one new leaf after validation. No existing artifact is edited.
        args.output.mkdir(parents=True, exist_ok=False)
        (args.output / "comparison.json").write_text(report_bytes)
        (args.output / "index.html").write_text(html)
        print(json.dumps({"output": str(args.output.resolve()), "cases": len(result["cases"]),
                          "kinds": {c["case_id"]: c["comparison_kind"] for c in result["cases"]},
                          "behavior_acceptance": "not_evaluated"}, indent=2))
        return 0
    except (OSError, ValueError, OverflowError, RecursionError) as error:
        print(json.dumps({"status": "error", "error": str(error)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
