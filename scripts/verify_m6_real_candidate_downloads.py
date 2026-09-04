#!/usr/bin/env python3
"""Re-fetch pinned M6 candidate bytes and compare them without executing them."""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, os.fspath(ROOT))

from artifact_contract.validator import validate_resolution_bundle

CANDIDATES = {
    "official": ROOT / "artifact_contract/real-candidates/official-alpha-walking-088524a",
    "community": ROOT / "artifact_contract/real-candidates/community-rough-walk-e-fa7b27e",
}


def source_records(value: dict) -> list[dict]:
    records = [binding for binding in value["bindings"].values() if binding["status"] == "bound"]
    records.extend(value["supporting_files"])
    return records


def verify_download(record: dict, bundle: Path, timeout: int) -> None:
    request = urllib.request.Request(record["source"]["url"], headers={"User-Agent": "microduck-m6-byte-verifier/1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        downloaded = response.read()
    expected = record["sha256"].removeprefix("sha256:")
    observed = hashlib.sha256(downloaded).hexdigest()
    if observed != expected or len(downloaded) != record["size_bytes"]:
        raise AssertionError(f"remote byte drift: {record['source']['url']}")
    if downloaded != (bundle / record["path"]).read_bytes():
        raise AssertionError(f"committed byte mismatch: {record['path']}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", choices=("all", *CANDIDATES), default="all")
    parser.add_argument("--timeout", type=int, default=60)
    args = parser.parse_args()
    selected = CANDIDATES.items() if args.candidate == "all" else [(args.candidate, CANDIDATES[args.candidate])]
    total = 0
    for source_class, bundle in selected:
        value = validate_resolution_bundle(bundle, source_class)
        for record in source_records(value):
            verify_download(record, bundle, args.timeout)
            total += 1
        print(f"{source_class}: immutable downloads match committed bytes")
    print(f"verified {total} pinned remote files; no downloaded code or policy was executed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
