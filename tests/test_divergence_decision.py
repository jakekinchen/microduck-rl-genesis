"""Validate complete, versioned disposition of all non-exact task semantics."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECISION = ROOT / "microduck_contract/divergence/decision-v1.json"
LOCK = ROOT / "microduck_contract/divergence/decision-v1.lock.json"
SCHEMA = ROOT / "microduck_contract/divergence/decision-v1.schema.json"
GENERATOR = ROOT / "scripts/generate_divergence_decision.py"

spec = importlib.util.spec_from_file_location("divergence_generator", GENERATOR)
assert spec is not None and spec.loader is not None
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)

value = json.loads(DECISION.read_text())
generator.validate(value)
schema = json.loads(SCHEMA.read_text())
assert schema["properties"]["schema_version"]["const"] == value["schema_version"]
assert schema["properties"]["decision_id"]["const"] == value["decision_id"]

expected_keys = set()
for task_path in generator.TASK_PATHS:
    task = json.loads(task_path.read_text())
    expected_keys.update(
        (task["task_id"], row["field"])
        for row in task["semantic_inventory"]
        if row["classification"] != "exact"
    )
actual_keys = {(row["task_id"], row["field"]) for row in value["entries"]}
assert actual_keys == expected_keys
assert value["summary"]["non_exact_entry_count"] == len(expected_keys) == 45
assert value["decision"]["status"] == "recorded_local_not_submitted"
assert not value["decision"]["upstream_submission_performed"]
assert not value["decision"]["publication_performed"]
assert not value["summary"]["training_trajectory_equivalence"]
assert not value["summary"]["task_success_evaluated"]
assert not value["summary"]["physical_authority"]

lock = json.loads(LOCK.read_text())
assert lock["decision_id"] == value["decision_id"]
assert lock["decision_sha256"] == generator.sha256(DECISION)
assert not lock["upstream_submission_performed"]

print(
    "versioned divergence decision verified: "
    f"{len(actual_keys)} non-exact fields, local and not submitted"
)
