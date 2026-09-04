#!/usr/bin/env python3
"""Validate the retained M6 distribution receipt without importing artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from artifact_contract.distribution import validate_receipt

RECEIPT = ROOT / "receipts/m6/distribution/20260904-local-complete-assets-v1"
ALLOWLIST = ROOT / "artifact_contract/distribution-allowlist-v1.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--receipt", type=Path, default=RECEIPT)
    parser.add_argument("--allowlist", type=Path, default=ALLOWLIST)
    parser.add_argument("--stage", type=Path)
    args = parser.parse_args()
    result = validate_receipt(
        args.receipt.resolve(), args.root.resolve(), args.allowlist.resolve(), args.stage
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
