"""Run and validate the frozen visible evaluator infrastructure case matrix."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from evaluator.core import EvaluationError, EvaluatorCore, sha256, stable_json_bytes

ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = Path(__file__).with_name("case-matrix-v1.json")
REQUIRED_CATEGORIES = {
    "standing", "command_grid", "start_stop_reversal", "perturbation",
    "friction", "joint_margin", "nan", "deadline", "termination",
}


def validate_matrix(matrix: dict[str, Any]) -> None:
    if matrix["schema_version"] != "microduck.evaluator-case-matrix/v1":
        raise AssertionError("unexpected case-matrix schema")
    if matrix["visibility"] != "public-development" or matrix["held_out"]:
        raise AssertionError("case matrix must remain visible development data")
    if matrix["candidate_policy_allowed"] or matrix["proof_class"] != "infrastructure_only":
        raise AssertionError("case matrix cannot evaluate candidate policies")
    categories = {case["category"] for case in matrix["cases"]}
    if categories != REQUIRED_CATEGORIES:
        raise AssertionError(f"case categories mismatch: {sorted(categories)}")
    ids = [case["case_id"] for case in matrix["cases"]]
    seeds = [case["seed"] for case in matrix["cases"]]
    if len(ids) != len(set(ids)) or len(seeds) != len(set(seeds)):
        raise AssertionError("case IDs and seeds must be unique")
    task = json.loads((ROOT / "microduck_contract/tasks/walking-v1.json").read_text())
    if set(seeds).intersection(task["acceptance"]["seeds"]):
        raise AssertionError("visible matrix leaks an acceptance seed")
    for case in matrix["cases"]:
        expected = [key for key in ("expected_classification", "expected_error") if key in case]
        if len(expected) != 1:
            raise AssertionError(f"case must have one expected outcome: {case['case_id']}")


def run_matrix(policy: Path, bam_repo: Path) -> dict[str, Any]:
    matrix = json.loads(MATRIX_PATH.read_text())
    validate_matrix(matrix)
    outcomes = []
    for source_case in matrix["cases"]:
        case = {"task_id": matrix["task_id"], **source_case}
        try:
            report, _, _ = EvaluatorCore(policy, bam_repo, matrix["task_id"]).run_case(case)
        except EvaluationError as error:
            if str(error) != case.get("expected_error"):
                raise AssertionError(f"unexpected evaluator error for {case['case_id']}: {error}") from error
            outcomes.append({"case_id": case["case_id"], "outcome": "rejected", "error": str(error)})
            continue
        expected = case.get("expected_classification")
        if report["classification"] != expected:
            raise AssertionError(
                f"classification mismatch for {case['case_id']}: "
                f"expected {expected}, got {report['classification']}"
            )
        outcomes.append({"case_id": case["case_id"], "outcome": "reported", "report": report})
    return {
        "schema_version": "microduck.evaluator-case-matrix-result/v1",
        "suite_id": matrix["suite_id"],
        "matrix_sha256": sha256(MATRIX_PATH),
        "policy_sha256": sha256(policy),
        "proof_class": "infrastructure_only",
        "task_success": "not_evaluated",
        "held_out": False,
        "outcomes": outcomes,
        "evidence_boundary": matrix["evidence_boundary"],
    }


__all__ = ["MATRIX_PATH", "run_matrix", "stable_json_bytes", "validate_matrix"]
