"""Validate the retained walking contract without evaluating a policy."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "microduck_contract" / "tasks" / "walking-v1.json"
LOCK = ROOT / "microduck_contract" / "tasks" / "walking-v1.lock.json"
SCHEMA = ROOT / "microduck_contract" / "tasks" / "walking-v1.schema.json"
GENERATOR = ROOT / "scripts" / "generate_walking_semantics.py"

spec = importlib.util.spec_from_file_location("walking_semantics_generator", GENERATOR)
assert spec is not None and spec.loader is not None
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)

value = json.loads(TASK.read_text())
generator.validate_contract(value, verify_local=True)
schema = json.loads(SCHEMA.read_text())
assert value["$schema"] == SCHEMA.name
assert schema["properties"]["schema_version"]["const"] == value["schema_version"]
assert schema["properties"]["task_id"]["const"] == value["task_id"]

shared = value["shared_deployed_contract"]
observation = json.loads(
    (ROOT / "microduck_contract" / "interface" / "observation-v1.json").read_text()
)
action = json.loads(
    (ROOT / "microduck_contract" / "interface" / "action-v1.json").read_text()
)
control = json.loads(
    (ROOT / "microduck_contract" / "interface" / "control-v1.json").read_text()
)
assert shared["actor_observation"]["layout"] == observation["layout"]
assert shared["actor_observation"]["dimension"] == observation["shape"][1] == 61
assert shared["action"]["joint_order"] == action["joint_order"]
assert shared["action"]["dimension"] == action["shape"][1] == 14
assert shared["control"]["control_hz"] == control["control_hz"] == 50
assert value["claim"]["policy_success"] == "not_evaluated"
assert not value["claim"]["training_trajectory_equivalence"]
assert not value["claim"]["physical_authority"]

rough = value["training_only"]["official_mjlab"]["rough_terrain"]
assert rough["source_declared_rows"] == 10
assert rough["source_declared_columns"] == 20
assert rough["effective_rows_after_task_registration"] == 5
assert rough["effective_columns_after_task_registration"] == 5
assert rough["effective_curriculum_after_task_registration"] is False
inventory = {row["field"]: row for row in value["semantic_inventory"]}
assert inventory["training.mass_inertia_randomization"]["classification"] == "versioned-divergence"
assert inventory["reset.base_and_joints"]["classification"] == "versioned-divergence"

lock = json.loads(LOCK.read_text())
assert lock["task_id"] == value["task_id"]
assert lock["acceptance_suite_id"] == value["acceptance"]["suite_id"]
assert lock["task_sha256"] == generator.sha256(TASK)

# Full authority regeneration is optional in the default lightweight runner,
# but becomes mandatory when both clean pinned checkouts are supplied.
official_repo = os.environ.get("OFFICIAL_MICRODUCK_REPO")
bam_repo = os.environ.get("BAM_REPO")
if official_repo and bam_repo:
    subprocess.check_call(
        [
            sys.executable,
            os.fspath(GENERATOR),
            "--official-repo",
            official_repo,
            "--official-commit",
            generator.OFFICIAL_COMMIT,
            "--bam-repo",
            bam_repo,
            "--official-python",
            os.environ.get(
                "OFFICIAL_MJLAB_PYTHON",
                os.fspath(
                    ROOT / "validation" / "official-mjlab" / ".venv" / "bin" / "python"
                ),
            ),
            "--check",
        ]
    )

print(
    "walking semantics verified: 61D/14D/50Hz, "
    f"{len(value['semantic_inventory'])} classified fields, "
    f"{value['acceptance']['aggregation']['required_episode_count']} preregistered cases"
)
