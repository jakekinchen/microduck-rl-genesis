"""Negative and positive validation for the frozen M5 experiment contract."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from experiments.m5.contract import expand_matrix, validate_contract, validate_lock

contract = json.loads((ROOT / "experiments/m5/contract-v1.json").read_text())
validate_contract(contract, ROOT, check_external=False)
validate_lock(ROOT)
matrix = expand_matrix(contract)
committed_matrix = json.loads((ROOT / "experiments/m5/execution-matrix-v1.json").read_text())
assert committed_matrix == matrix
assert matrix["row_count"] == 32
assert matrix["heldout_seeds_included"] is False
assert matrix["resource_authorized"] is False
assert matrix["pilot_resource_authorized"] is False
assert matrix["candidate_or_heldout_execution_authorized"] is False
assert {row["state"] for row in matrix["rows"]} == {"planned_not_executed"}


def rejected(mutator) -> None:
    candidate = copy.deepcopy(contract)
    mutator(candidate)
    try:
        validate_contract(candidate, ROOT, check_external=False)
    except AssertionError:
        return
    raise AssertionError("invalid M5 contract mutation was accepted")


rejected(lambda value: value["bindings"].__setitem__("evaluator/core.py", "sha256:" + "0" * 64))
rejected(lambda value: value["tasks"][0]["candidate_comparison_seeds"].__setitem__(0, 51001))
rejected(lambda value: value["tasks"][0]["backends"][0].__setitem__("candidate_iterations", 11999))
rejected(lambda value: value["tasks"][0]["checkpoint_transitions"].append(294912001))
rejected(lambda value: value["bindings"].pop("evaluator/success.py"))
rejected(lambda value: value.__setitem__("state", "pilot_authorized"))
rejected(lambda value: value["blocking_gates"].pop())
rejected(lambda value: value["bindings"].pop("environments/cuda/runtime-v1.json"))
rejected(lambda value: value["resource_proposal"].__setitem__("authorization", "full_authorized"))
rejected(lambda value: value["resource_proposal"]["container"].__setitem__("manifest_digest", "sha256:" + "0" * 64))
rejected(lambda value: value["resource_proposal"].__setitem__("proposed_type", "H100"))
rejected(lambda value: value["resource_proposal"].__setitem__("pilot_cost_ceiling_usd", 4.0))
rejected(lambda value: value["resource_proposal"].__setitem__("candidate_or_heldout_execution_authorized", True))
rejected(lambda value: value["resource_proposal"].__setitem__("stoppable", True))
rejected(lambda value: value["resource_proposal"].__setitem__("cloud", "shadeform"))
rejected(lambda value: value["resource_proposal"].__setitem__("provider", "hyperstack"))
rejected(lambda value: value["resource_proposal"]["container"].__setitem__("tag_for_humans_only", "latest"))
rejected(lambda value: value["resource_proposal"]["container"].__setitem__("platform", "linux/arm64"))
rejected(lambda value: value["resource_proposal"]["container"].__setitem__("inspection_command", "true"))
rejected(lambda value: value["resource_proposal"].__setitem__("workspace_count", 2))
rejected(lambda value: value["resource_proposal"].__setitem__("inventory_precondition", "none"))
rejected(lambda value: value["resource_proposal"].__setitem__("fallback_allowed", True))
rejected(lambda value: value["resource_proposal"].__setitem__("provisioning", ["true"]))
rejected(lambda value: value["resource_proposal"].__setitem__("pilot_contents", []))
rejected(lambda value: value["resource_proposal"].__setitem__("recovery_before_teardown", []))
rejected(lambda value: value["resource_proposal"].__setitem__("full_cuda_authorization_condition", "automatic"))
rejected(lambda value: value["resource_proposal"].__setitem__("teardown", ["true"]))
rejected(lambda value: value["resource_proposal"].__setitem__("unreviewed_extra", True))
print("M5 immutable experiment contract and negative drift probes verified")
