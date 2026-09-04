#!/usr/bin/env python3
"""Validate the final local M6 external-authority handoff packet."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from artifact_contract.authority_handoff import validate_authority_handoff

RECEIPT = ROOT / "receipts/m6/authority/20260904-external-handoff-v1"


if __name__ == "__main__":
    packet = validate_authority_handoff(RECEIPT, ROOT)
    print(f"M6 authority handoff verified: {packet['decision']}")
