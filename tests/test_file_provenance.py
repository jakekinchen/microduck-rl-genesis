"""Verify complete file coverage and retained provenance negatives."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from artifact_contract.provenance import validate_inventory

inventory = json.loads((ROOT / "artifact_contract/file-provenance-v1.json").read_text())
validate_inventory(inventory, ROOT)
assert inventory["summary"] == {"total_files": 70, "complete": 63, "partial": 2, "missing": 5, "fully_resolved": False}
ball = next(item for item in inventory["files"] if item["path"].endswith("/ball.xml"))
assert ball["provenance_status"] == "partial" and ball["source"]["byte_identical"] is False
assert all(item["provenance_status"] == "missing" for item in inventory["files"] if item["artifact_class"] in {"policy_weight", "media"})


def rejected(mutator) -> None:
    candidate = copy.deepcopy(inventory)
    mutator(candidate)
    try:
        validate_inventory(candidate, ROOT)
    except AssertionError:
        return
    raise AssertionError("invalid provenance mutation accepted")


rejected(lambda value: value["files"].pop())
rejected(lambda value: value["files"][0].__setitem__("sha256", "sha256:" + "0" * 64))
policy_index = next(index for index, item in enumerate(inventory["files"]) if item["artifact_class"] == "policy_weight")
rejected(lambda value: value["files"][policy_index].__setitem__("provenance_status", "complete"))
rejected(lambda value: value["lifecycle"].__setitem__("evaluation", "completed"))
print("file-level MJCF/mesh/policy/dataset/media provenance and negative statuses verified")
