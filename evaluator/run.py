#!/usr/bin/env python3
"""Run the bounded evaluator-core smoke and emit its deterministic report."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evaluator.core import EvaluatorCore, stable_json_bytes  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--bam-repo", required=True, type=Path)
    parser.add_argument("--task-id", default="microduck.walking.v1")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = EvaluatorCore(
        args.policy.resolve(), args.bam_repo.resolve(), args.task_id
    ).run_synthetic_smoke()
    payload = stable_json_bytes(report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(payload)
        print(args.output)
    else:
        sys.stdout.buffer.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
