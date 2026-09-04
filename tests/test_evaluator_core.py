"""Exercise the independent evaluator core with a deterministic zero policy."""

from __future__ import annotations

import json
import os
import sys
from importlib import metadata
from pathlib import Path

import mujoco
import numpy as np
import onnxruntime as ort

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
from evaluator.determinism import (  # noqa: E402
    canonical_trajectory_sha256,
    semantic_report_projection,
)

POLICY = ROOT / "tests/fixtures/evaluator/zero-policy.onnx"
EXPECTED = ROOT / "tests/fixtures/evaluator/home-zero-policy-report.json"
CROSS_PLATFORM = ROOT / "tests/fixtures/evaluator/cross-platform-determinism-v1.json"
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

first_core = EvaluatorCore(POLICY, Path(BAM_REPO), "microduck.walking.v1")
first, first_rows, _ = first_core.run_case(first_core.config["synthetic_smoke"])
second_core = EvaluatorCore(POLICY, Path(BAM_REPO), "microduck.walking.v1")
second, second_rows, _ = second_core.run_case(second_core.config["synthetic_smoke"])
backflip_core = EvaluatorCore(POLICY, Path(BAM_REPO), "microduck.backflip.v1")
assert backflip_core.model.nu == 14
assert backflip_core.model.opt.timestep == 0.005
first_bytes = stable_json_bytes(first)
second_bytes = stable_json_bytes(second)
assert first_bytes == second_bytes
expected = json.loads(EXPECTED.read_text())
cross_platform = json.loads(CROSS_PLATFORM.read_text())
assert stable_json_bytes(semantic_report_projection(first)) == stable_json_bytes(
    semantic_report_projection(expected)
)
assert canonical_trajectory_sha256(first_rows) == cross_platform["home_zero_policy_trajectory_sha256"]
assert canonical_trajectory_sha256(second_rows) == cross_platform["home_zero_policy_trajectory_sha256"]
assert first["runtime"] == {
    "mujoco": mujoco.__version__,
    "numpy": metadata.version("numpy"),
    "onnxruntime": ort.__version__,
}
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
