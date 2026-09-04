#!/usr/bin/env python3
"""Validate the frozen M5 contract and optionally emit its non-executing matrix."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, os.fspath(ROOT))

from experiments.m5.contract import expand_matrix, validate_contract, validate_lock


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=ROOT / "experiments/m5/contract-v1.json")
    parser.add_argument("--official-walking-repo", type=Path, default=ROOT.parent / "microduck-rl")
    parser.add_argument("--official-backflip-repo", type=Path, default=ROOT.parent / "microduck-backflip")
    parser.add_argument("--matrix-output", type=Path)
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text())
    validate_contract(contract, ROOT, args.official_walking_repo, args.official_backflip_repo)
    validate_lock(ROOT)
    matrix = expand_matrix(contract)
    if args.matrix_output:
        args.matrix_output.parent.mkdir(parents=True, exist_ok=True)
        args.matrix_output.write_text(json.dumps(matrix, indent=2, sort_keys=True) + "\n")
    print(
        f"M5 contract valid: {matrix['row_count']} planned rows; "
        "second pilot proposed but not authorized; candidate/held-out execution not authorized"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
