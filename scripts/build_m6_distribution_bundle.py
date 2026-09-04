#!/usr/bin/env python3
"""Build or byte-validate the local M6 provenance distribution bundle."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from artifact_contract.distribution import build_allowlist, build_bundle, validate_bundle


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--allowlist", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--generate", action="store_true")
    parser.add_argument("--stage", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    allowlist = args.allowlist.resolve()
    bundle = args.bundle.resolve()
    if args.generate:
        inventory = json.loads((root / "artifact_contract/file-provenance-v1.json").read_text())
        value = build_allowlist(root, inventory)
        allowlist.parent.mkdir(parents=True, exist_ok=True)
        allowlist.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
        result = build_bundle(root, allowlist, bundle)
    else:
        result = validate_bundle(root, allowlist, bundle, args.stage)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
