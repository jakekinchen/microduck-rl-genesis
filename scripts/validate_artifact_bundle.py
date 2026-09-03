#!/usr/bin/env python3
"""Validate a policy bundle by parsing metadata and hashing bytes only."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, os.fspath(ROOT))

from artifact_contract.validator import validate_fixture_bundle


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--source-class", choices=("official", "community"), required=True)
    args = parser.parse_args()
    validate_fixture_bundle(args.bundle, args.source_class)
    print(f"non-executing artifact validation passed: {args.source_class} synthetic fixture")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
