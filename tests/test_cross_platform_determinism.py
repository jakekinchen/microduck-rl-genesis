"""Exercise canonical evidence boundaries with measured Darwin/Linux deltas."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evaluator.determinism import (  # noqa: E402
    TRAJECTORY_DECIMAL_PLACES,
    canonical_trajectory_sha256,
    semantic_report_projection,
)
from scripts.reconcile_models import (  # noqa: E402
    COMPILED_MANIFEST_SIGNIFICANT_DIGITS,
    canonical_compiled_manifest,
)

contract = json.loads(
    (ROOT / "tests/fixtures/evaluator/cross-platform-determinism-v1.json").read_text()
)
assert contract["compiled_manifest_significant_digits"] == COMPILED_MANIFEST_SIGNIFICANT_DIGITS
assert contract["trajectory_decimal_places"] == TRAJECTORY_DECIMAL_PLACES


darwin_manifest = {
    "bodies": [{
        "name": "trunk",
        "mass_kg": 0.12345678901234567,
        "inertia_kg_m2": [
            0.00014079887191245798,
            1.1597556037198693e-06,
            3.52458396277689e-07,
        ],
    }],
    "joints": [{"name": "hip", "damping": 0.12345678901234567}],
}
linux_manifest = copy.deepcopy(darwin_manifest)
linux_manifest["bodies"][0]["inertia_kg_m2"] = [
    0.000140798871912458,
    1.159755603719869e-06,
    3.5245839627768903e-07,
]
assert canonical_compiled_manifest(darwin_manifest) == canonical_compiled_manifest(
    linux_manifest
)
semantic_inertia_change = copy.deepcopy(linux_manifest)
semantic_inertia_change["bodies"][0]["inertia_kg_m2"][0] += 1e-9
assert canonical_compiled_manifest(darwin_manifest) != canonical_compiled_manifest(
    semantic_inertia_change
)
non_inertia_tail_change = copy.deepcopy(darwin_manifest)
non_inertia_tail_change["bodies"][0]["mass_kg"] = 0.12345678901234568
assert canonical_compiled_manifest(darwin_manifest) != canonical_compiled_manifest(
    non_inertia_tail_change
)

darwin_rows = [{"case_id": "case", "physics_step": 1, "velocity": [1.0, 1.4779288903810087e-13]}]
linux_rows = [{"case_id": "case", "physics_step": 1, "velocity": [1.0, 0.0]}]
assert canonical_trajectory_sha256(darwin_rows) == canonical_trajectory_sha256(linux_rows)
linux_reordered_fields = [{"velocity": [1.0, 0.0], "physics_step": 1, "case_id": "case"}]
assert canonical_trajectory_sha256(linux_rows) == canonical_trajectory_sha256(
    linux_reordered_fields
)
changed_rows = copy.deepcopy(linux_rows)
changed_rows[0]["velocity"][0] += 1e-8
assert canonical_trajectory_sha256(darwin_rows) != canonical_trajectory_sha256(changed_rows)

darwin_report = {
    "schema_version": "microduck.evaluator-report/v1",
    "runtime": {"mujoco": "3.12.0", "numpy": "2.5.2", "onnxruntime": "1.23.2"},
    "integrity": {"finite": True, "trajectory_sha256": "sha256:" + "1" * 64},
}
linux_report = copy.deepcopy(darwin_report)
linux_report["runtime"]["onnxruntime"] = "1.29.0"
linux_report["integrity"]["trajectory_sha256"] = "sha256:" + "2" * 64
assert semantic_report_projection(darwin_report) == semantic_report_projection(linux_report)

print("cross-platform deterministic evidence canonicalization verified")
