"""Reject promotion or drift in the retained community-authority search."""

from __future__ import annotations

import json
import hashlib
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from artifact_contract.community_search import validate_community_search_receipt

RECEIPT = ROOT / "receipts/m6/provenance/20260904-community-rough-walk-e"
validate_community_search_receipt(RECEIPT)


def rejected(filename: str, mutate) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        copied = Path(temporary) / "receipt"
        shutil.copytree(RECEIPT, copied)
        target = copied / filename
        value = json.loads(target.read_text())
        mutate(value)
        target.write_text(json.dumps(value))
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        manifest = copied / "SHA256SUMS"
        lines = manifest.read_text().splitlines()
        manifest.write_text("\n".join(
            f"{digest}  ./{filename}" if line.endswith(f"  ./{filename}") else line
            for line in lines
        ) + "\n")
        try:
            validate_community_search_receipt(copied)
        except AssertionError:
            return
        raise AssertionError("invalid community-authority search mutation accepted")


rejected("SEARCH_RESULT.json", lambda value: value.__setitem__("result", "roles_resolved"))
rejected("SEARCH_RESULT.json", lambda value: value["actions"].__setitem__("onnx_loaded", True))
rejected("wandb-public-search.json", lambda value: value.__setitem__("disposition", "checkpoint_accepted"))
rejected("github-history-summary.json", lambda value: value.__setitem__("pagination_limit_reached", False))

print("M6 community authority search and negative promotion probes verified")
