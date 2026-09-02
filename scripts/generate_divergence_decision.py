#!/usr/bin/env python3
"""Generate the local M1 decision for every non-exact task semantic."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "microduck_contract/divergence/decision-v1.json"
SCHEMA = ROOT / "microduck_contract/divergence/decision-v1.schema.json"
TASK_PATHS = (
    ROOT / "microduck_contract/tasks/walking-v1.json",
    ROOT / "microduck_contract/tasks/backflip-v1.json",
)

# Versioned divergences need a deliberate disposition. Equivalent and
# backend-unavailable rows use classification-wide policies below.
VERSIONED_DECISIONS = {
    ("microduck.walking.v1", "action.input_guard"): "evaluator_normalization_required",
    ("microduck.walking.v1", "observation.critic"): "training_only_non_equivalence",
    ("microduck.walking.v1", "reset.base_and_joints"): "training_only_non_equivalence",
    ("microduck.walking.v1", "termination.rough_bounds"): "independent_evaluator_boundary",
    ("microduck.walking.v1", "training.mass_inertia_randomization"): "deferred_implementation_reconciliation",
    ("microduck.walking.v1", "terrain.rough_realization"): "deferred_implementation_reconciliation",
    ("microduck.walking.v1", "sensing.foot_height"): "independent_evaluator_boundary",
    ("microduck.walking.v1", "sensing.contact"): "independent_evaluator_boundary",
    ("microduck.walking.v1", "execution.step_lifecycle"): "training_only_non_equivalence",
    ("microduck.backflip.v1", "action.input_guard"): "evaluator_normalization_required",
    ("microduck.backflip.v1", "observation.critic"): "training_only_non_equivalence",
    ("microduck.backflip.v1", "commands.twist"): "evaluator_normalization_required",
    ("microduck.backflip.v1", "sensing.contact"): "independent_evaluator_boundary",
    ("microduck.backflip.v1", "training.reward_terms"): "deferred_implementation_reconciliation",
    ("microduck.backflip.v1", "training.mass_inertia_randomization"): "deferred_implementation_reconciliation",
    ("microduck.backflip.v1", "execution.step_lifecycle"): "training_only_non_equivalence",
}

RATIONALE = {
    "accepted_backend_equivalence": (
        "Declarations agree semantically, but backend RNG, sensor, or manager "
        "realization prevents a byte-identical trajectory claim."
    ),
    "evaluator_normalization_required": (
        "The independent evaluator fixes this input or guard explicitly so the "
        "acceptance result does not depend on either training backend."
    ),
    "independent_evaluator_boundary": (
        "The independent C MuJoCo evaluator owns the acceptance realization; "
        "neither training backend may self-attest this field."
    ),
    "deferred_implementation_reconciliation": (
        "The mismatch is retained and versioned for later implementation work; "
        "it blocks training-trajectory equivalence now."
    ),
    "training_only_non_equivalence": (
        "The difference is accepted for this local training lane and explicitly "
        "blocks a training-trajectory-equivalence claim."
    ),
}


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def disposition(task_id: str, field: str, classification: str) -> str:
    if classification == "equivalent":
        return "accepted_backend_equivalence"
    if classification == "backend-specific-unavailable":
        return "independent_evaluator_boundary"
    if classification == "versioned-divergence":
        key = (task_id, field)
        if key not in VERSIONED_DECISIONS:
            raise AssertionError(f"missing explicit versioned decision for {task_id}:{field}")
        return VERSIONED_DECISIONS[key]
    raise AssertionError(f"unexpected non-exact classification: {classification}")


def build() -> dict[str, Any]:
    tasks = [json.loads(path.read_text()) for path in TASK_PATHS]
    entries = []
    seen_versioned = set()
    task_bindings = []
    for path, task in zip(TASK_PATHS, tasks, strict=True):
        task_id = task["task_id"]
        task_bindings.append({
            "task_id": task_id,
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": sha256(path),
            "official_commit": next(
                value["commit"]
                for value in task["authority"].values()
                if isinstance(value, dict) and "commit" in value
            ),
            "semantic_inventory_count": len(task["semantic_inventory"]),
        })
        for row in task["semantic_inventory"]:
            if row["classification"] == "exact":
                continue
            decision = disposition(task_id, row["field"], row["classification"])
            if row["classification"] == "versioned-divergence":
                seen_versioned.add((task_id, row["field"]))
            entries.append({
                "task_id": task_id,
                "field": row["field"],
                "source_classification": row["classification"],
                "source_disposition": row["disposition"],
                "decision": decision,
                "decision_rationale": RATIONALE[decision],
                "blocks_training_trajectory_equivalence": (
                    row["classification"] != "equivalent"
                    or decision == "training_only_non_equivalence"
                ),
                "acceptance_owner": (
                    "independent_c_mujoco_evaluator"
                    if decision in {"evaluator_normalization_required", "independent_evaluator_boundary"}
                    else "frozen_task_contract"
                ),
            })
    unused = set(VERSIONED_DECISIONS) - seen_versioned
    if unused:
        raise AssertionError(f"stale explicit versioned decisions: {sorted(unused)}")
    entries.sort(key=lambda row: (row["task_id"], row["field"]))
    return {
        "$schema": SCHEMA.name,
        "schema_version": "microduck.divergence-decision/v1",
        "decision_id": "microduck.genesis-official-mjlab.local-divergence.v1",
        "decision": {
            "chosen_path": "versioned_local_divergence",
            "status": "recorded_local_not_submitted",
            "upstream_submission_performed": False,
            "publication_performed": False,
            "reason": "Active authority permits local commits but forbids push or public submission.",
            "supersession_rule": "A later version must bind new task digests and explicitly dispose every added, removed, or changed non-exact field.",
        },
        "task_bindings": task_bindings,
        "entries": entries,
        "summary": {
            "non_exact_entry_count": len(entries),
            "by_decision": {
                name: sum(row["decision"] == name for row in entries)
                for name in sorted(RATIONALE)
            },
            "exact_deployed_interface_preserved": True,
            "training_trajectory_equivalence": False,
            "task_success_evaluated": False,
            "held_out_evaluation_performed": False,
            "physical_authority": False,
        },
        "evidence_boundary": (
            "This local decision records compatibility scope and unresolved "
            "differences. It is not an upstream submission, evaluator result, "
            "policy-success result, transfer result, or physical authority."
        ),
    }


def validate(value: dict[str, Any]) -> None:
    expected = build()
    if value != expected:
        raise AssertionError("divergence decision differs from current frozen task inventories")
    if value["decision"]["upstream_submission_performed"]:
        raise AssertionError("no upstream submission is authorized or evidenced")
    if value["decision"]["publication_performed"]:
        raise AssertionError("no publication is authorized or evidenced")
    if value["summary"]["training_trajectory_equivalence"]:
        raise AssertionError("non-exact semantics cannot claim trajectory equivalence")
    entries = value["entries"]
    keys = [(row["task_id"], row["field"]) for row in entries]
    if len(keys) != len(set(keys)):
        raise AssertionError("duplicate divergence decision entry")
    if value["summary"]["non_exact_entry_count"] != len(entries):
        raise AssertionError("stale divergence entry count")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = build()
    validate(expected)
    payload = json_bytes(expected)
    if args.check:
        actual = args.output.read_bytes() if args.output.exists() else b""
        if actual != payload:
            print(f"Divergence decision is stale: {args.output}")
            return 1
        print(f"Divergence decision verified: {len(expected['entries'])} non-exact fields.")
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(payload)
    print(f"Divergence decision written: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
