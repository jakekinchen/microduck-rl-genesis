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
assert inventory["summary"] == {"total_files": 70, "complete": 65, "partial": 0, "missing": 5, "fully_resolved": False}
ball = next(item for item in inventory["files"] if item["path"].endswith("/ball.xml"))
assert ball["provenance_status"] == "complete" and ball["source"] == {
    "byte_identical": True,
    "path": "src/mjlab_microduck/robot/microduck/ball.xml",
    "repository": "https://github.com/pollen-robotics/microduck_rl.git",
    "revision": "84790795a6647f7dbd2353f53f7263229d7b7051",
    "sha256": "sha256:54a455bf454a9b6167655381df91593bbca86695d8d71e29fb6af69454c7c865",
}
assert ball["source_history"] == {
    "later_change_commit": "7831c5142f93cc863327ae607bf0d262d127c767",
    "later_declared_revision": "109e06d4ce4921b635c5609e5304079fc30960ae",
    "selection": "exact public upstream bytes predating a later upstream-only contact-priority change",
}
actuator = next(item for item in inventory["files"] if item["artifact_class"] == "actuator_parameter")
assert actuator["provenance_status"] == "complete" and actuator["source"] == {
    "byte_identical": True,
    "path": "bam/params/xl330/m6.json",
    "repository": "https://github.com/Rhoban/bam.git",
    "revision": "62bd8ce12154340be97e06f7f41a0ca8f116d967",
    "sha256": "sha256:61c699362fb3fabdde93eeba5e1ad3bf4ef9ca2f71d03e316b1924ff005b20d3",
}
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
actuator_index = next(index for index, item in enumerate(inventory["files"]) if item["artifact_class"] == "actuator_parameter")
ball_index = next(index for index, item in enumerate(inventory["files"]) if item["path"].endswith("/ball.xml"))
rejected(lambda value: value["files"][policy_index].__setitem__("provenance_status", "complete"))
rejected(lambda value: value["files"][actuator_index]["source"].__setitem__("path", "bam/params/xl330/m5.json"))
rejected(lambda value: value["files"][ball_index]["source"].__setitem__("revision", "109e06d4ce4921b635c5609e5304079fc30960ae"))
rejected(lambda value: value["lifecycle"].__setitem__("evaluation", "completed"))
print("file-level MJCF/mesh/policy/dataset/media provenance and negative statuses verified")
