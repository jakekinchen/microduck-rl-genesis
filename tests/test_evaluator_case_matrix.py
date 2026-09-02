"""Exercise every frozen evaluator infrastructure case twice."""

from __future__ import annotations

import copy
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, os.fspath(ROOT))

from evaluator.case_matrix import MATRIX_PATH, run_matrix, stable_json_bytes, validate_matrix  # noqa: E402

POLICY = ROOT / "tests/fixtures/evaluator/zero-policy.onnx"
BAM_REPO = os.environ.get("BAM_REPO")

matrix = json.loads(MATRIX_PATH.read_text())
validate_matrix(matrix)
bad = copy.deepcopy(matrix)
bad["cases"][0]["expected_error"] = "wrong"
try:
    validate_matrix(bad)
except AssertionError:
    pass
else:
    raise AssertionError("matrix accepted two expected outcomes")

if not BAM_REPO:
    print("SKIP - BAM_REPO absent; evaluator case matrix unavailable")
    raise SystemExit(0)

first = run_matrix(POLICY, Path(BAM_REPO))
second = run_matrix(POLICY, Path(BAM_REPO))
assert stable_json_bytes(first) == stable_json_bytes(second)
assert first["task_success"] == "not_evaluated"
assert not first["held_out"]
assert len(first["outcomes"]) == 10
by_id = {row["case_id"]: row for row in first["outcomes"]}
assert by_id["matrix.nan-rejection.v1"]["error"] == "non-finite observation"
assert by_id["matrix.deadline.v1"]["report"]["integrity"]["deadline_miss_count"] == 2
assert by_id["matrix.termination.v1"]["report"]["case_metrics"]["terminated"]
assert by_id["matrix.perturbation.v1"]["report"]["case_metrics"]["external_force_physics_steps"] == 20

print("evaluator case matrix verified: 10 cases, 9 required families, byte-identical repeats")
