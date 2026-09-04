#!/usr/bin/env python3
"""Validate the immutable M6 local provenance archaeology receipt."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, os.fspath(ROOT))

from artifact_contract.local_provenance_archaeology import validate_local_provenance_archaeology

RECEIPT = ROOT / "receipts/m6/provenance/20260904-local-provenance-archaeology-v2"


if __name__ == "__main__":
    official_repo = Path(os.environ["OFFICIAL_MICRODUCK_REPO"]) if os.environ.get("OFFICIAL_MICRODUCK_REPO") else None
    value = validate_local_provenance_archaeology(RECEIPT, ROOT, official_repo)
    print(f"M6 local provenance archaeology verified: {value['result']}")
