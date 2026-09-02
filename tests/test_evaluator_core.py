"""Exercise the independent evaluator core with a deterministic zero policy."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, os.fspath(ROOT))

from evaluator.core import (  # noqa: E402
    EvaluationError,
    EvaluatorCore,
    OnnxPolicy,
    projected_gravity,
    sha256_counter_uniform,
    stable_json_bytes,
)

POLICY = ROOT / "tests/fixtures/evaluator/zero-policy.onnx"
EXPECTED = ROOT / "tests/fixtures/evaluator/home-zero-policy-report.json"
BAM_REPO = os.environ.get("BAM_REPO")

assert np.allclose(projected_gravity(np.array([1.0, 0.0, 0.0, 0.0])), [0, 0, -1])
assert np.array_equal(
    sha256_counter_uniform("case\u000073001", 4),
    sha256_counter_uniform("case\u000073001", 4),
)
assert np.all((sha256_counter_uniform("case\u000073001", 4) >= 0.0) & (sha256_counter_uniform("case\u000073001", 4) < 1.0))
bad_config = dict(json.loads((ROOT / "evaluator/config-v1.json").read_text())["inference"])
bad_config["output_shape"] = [1, 13]
try:
    OnnxPolicy(POLICY, bad_config)
except EvaluationError:
    pass
else:
    raise AssertionError("ONNX shape mismatch was accepted")
if not BAM_REPO:
    print("SKIP - BAM_REPO absent; evaluator core authority checkout unavailable")
    raise SystemExit(0)

first = EvaluatorCore(POLICY, Path(BAM_REPO), "microduck.walking.v1").run_synthetic_smoke()
second = EvaluatorCore(POLICY, Path(BAM_REPO), "microduck.walking.v1").run_synthetic_smoke()
backflip_core = EvaluatorCore(POLICY, Path(BAM_REPO), "microduck.backflip.v1")
assert backflip_core.model.nu == 14
assert backflip_core.model.opt.timestep == 0.005
first_bytes = stable_json_bytes(first)
second_bytes = stable_json_bytes(second)
assert first_bytes == second_bytes
assert first_bytes == EXPECTED.read_bytes()
assert first["proof_class"] == "infrastructure_only"
assert first["classification"] == "infrastructure_pass"
assert first["task_success"] == "not_evaluated"
assert not first["held_out"]
assert first["loop"] == {
    "physics_dt_s": 0.005,
    "control_decimation": 4,
    "control_hz": 50,
    "action_filter": "none",
    "physics_steps": 40,
    "policy_calls": 10,
    "bam_updates": 40,
}
assert first["integrity"]["finite"]
assert first["integrity"]["deadline_miss_count"] == 0
assert first["policy"]["execution_provider"] == "CPUExecutionProvider"

print(
    "evaluator core verified: two byte-identical 40-step reports, "
    "10 CPU ONNX calls, 40 pinned BAM updates"
)
