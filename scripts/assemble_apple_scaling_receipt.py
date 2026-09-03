#!/usr/bin/env python3
"""Assemble five one-process Apple scaling rows and checksum the receipt."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, os.fspath(ROOT))

from benchmarks.apple_scaling import REQUIRED_SIZES, assemble_sweep, sha256_file


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt-root", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    raw = args.receipt_root / "raw"
    row_paths = [raw / f"{size}.json" for size in REQUIRED_SIZES]
    missing = [str(path) for path in row_paths if not path.is_file()]
    if missing:
        raise SystemExit(f"missing scaling rows: {missing}")
    receipt = assemble_sweep(row_paths, args.run_id)
    output = args.receipt_root / "sweep.json"
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    checksum_paths = sorted(path for path in raw.iterdir() if path.is_file()) + [output]
    checksums = args.receipt_root / "SHA256SUMS"
    lines = [f"{sha256_file(path)}  {path.relative_to(args.receipt_root)}" for path in checksum_paths]
    checksums.write_text("\n".join(lines) + "\n")
    print(output)
    print(checksums)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
