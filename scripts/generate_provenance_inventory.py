#!/usr/bin/env python3
"""Generate or check the deterministic file-level provenance inventory."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, os.fspath(ROOT))

from artifact_contract.provenance import build_inventory, validate_inventory


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--official-repo", type=Path, default=ROOT.parent / "microduck-rl")
    parser.add_argument("--output", type=Path, default=ROOT / "artifact_contract/file-provenance-v1.json")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    generated = build_inventory(ROOT, args.official_repo)
    if args.check:
        current = json.loads(args.output.read_text())
        if current != generated:
            raise SystemExit("file provenance inventory is stale")
        validate_inventory(current, ROOT, args.official_repo)
        print(f"file provenance inventory verified: {current['summary']}")
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(generated, indent=2, sort_keys=True) + "\n")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
