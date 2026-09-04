#!/usr/bin/env python3
"""Validate a policy bundle by parsing metadata and hashing bytes only."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, os.fspath(ROOT))

from artifact_contract.validator import validate_fixture_bundle, validate_resolution_bundle


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--source-class", choices=("official", "community"), required=True)
    parser.add_argument("--real-resolution", action="store_true")
    args = parser.parse_args()
    if args.real_resolution:
        value = validate_resolution_bundle(args.bundle, args.source_class)
        print(
            "non-executing real-candidate resolution passed: "
            f"{args.source_class}; bound={len(value['validation']['bound_roles'])}; "
            f"missing={len(value['validation']['missing_roles'])}; manifest-v2=rejected-incomplete"
        )
        return 0
    validate_fixture_bundle(args.bundle, args.source_class)
    print(f"non-executing artifact validation passed: {args.source_class} synthetic fixture")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
