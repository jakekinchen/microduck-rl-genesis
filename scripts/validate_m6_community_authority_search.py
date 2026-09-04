#!/usr/bin/env python3
"""Validate the immutable M6 community-authority search receipt."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, os.fspath(ROOT))

from artifact_contract.community_search import validate_community_search_receipt

RECEIPT = ROOT / "receipts/m6/provenance/20260904-community-rough-walk-e"


if __name__ == "__main__":
    value = validate_community_search_receipt(RECEIPT)
    print(f"M6 community authority search verified: {value['result']}; BAM provenance closed")
