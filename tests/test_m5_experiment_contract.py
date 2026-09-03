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
rejected(lambda value: value["resource_proposal"].__setitem__("authorization", "authorized"))
print("M5 immutable experiment contract and negative drift probes verified")
