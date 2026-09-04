"""Verify deterministic visible-development evaluator artifact bundles."""

from __future__ import annotations

import copy
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest import mock

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, os.fspath(ROOT))

import evaluator.bundle as bundle_module  # noqa: E402
from evaluator.bundle import FILES, SUITE_PATH, validate_bundle, validate_suite, write_bundle  # noqa: E402
from evaluator.core import OnnxPolicy, sha256  # noqa: E402

POLICY = ROOT / "tests/fixtures/evaluator/zero-policy.onnx"
MANIFEST = ROOT / "tests/fixtures/evaluator/development-bundle-manifest.json"
BAM_REPO = os.environ.get("BAM_REPO")

suite = json.loads(SUITE_PATH.read_text())
validate_suite(suite)
bad_suite = copy.deepcopy(suite)
bad_suite["held_out"] = True
try:
    validate_suite(bad_suite)
except AssertionError:
    pass
else:
    raise AssertionError("visible development writer accepted a held-out suite")

if not BAM_REPO:
    print("SKIP - BAM_REPO absent; evaluator bundle authority checkout unavailable")
    raise SystemExit(0)

expected = json.loads(MANIFEST.read_text())
with tempfile.TemporaryDirectory(prefix="microduck-evaluator-bundle-test-") as temp:
    first = Path(temp) / "first"
    second = Path(temp) / "second"
    original_infer = OnnxPolicy.infer

    def infer_with_latency(latency_ms: float):
        def wrapped(policy, observation):
            action, _ = original_infer(policy, observation)
            return action, latency_ms

        return wrapped

    with mock.patch.multiple(
        bundle_module.platform,
        system=mock.Mock(return_value="Linux"),
        machine=mock.Mock(return_value="x86_64"),
        release=mock.Mock(return_value="6.8.0-117-generic"),
        python_version=mock.Mock(return_value="3.12.14"),
    ):
        with mock.patch.object(OnnxPolicy, "infer", infer_with_latency(25.0)):
            write_bundle(POLICY, Path(BAM_REPO), first)
        with mock.patch.object(OnnxPolicy, "infer", infer_with_latency(1.0)):
            write_bundle(POLICY, Path(BAM_REPO), second)
    validate_bundle(first, POLICY)
    validate_bundle(second, POLICY)
    first_hashes = {name: sha256(first / name) for name in FILES}
    second_hashes = {name: sha256(second / name) for name in FILES}
    assert first_hashes == second_hashes
    if first_hashes["environment-lock.json"] == expected["artifact_sha256"]["environment-lock.json"]:
        assert first_hashes == expected["artifact_sha256"]
    else:
        assert not expected["cross_host_artifact_bytes_claimed"]
    evaluation = json.loads((first / "evaluation.json").read_text())
    environment = json.loads((first / "environment-lock.json").read_text())
    assert environment["platform"] == {
        "machine": "x86_64",
        "python": "3.12.14",
        "release": "6.8.0-117-generic",
        "system": "Linux",
    }
    assert evaluation["suite_id"] == expected["suite_id"]
    assert evaluation["proof_class"] == expected["proof_class"]
    assert evaluation["task_success"] == expected["task_success"]
    assert evaluation["trajectory"]["row_count"] == expected["trajectory_row_count"]
    assert evaluation["video"]["frame_count"] == expected["video_frame_count"]
    assert evaluation["video"]["offscreen_samples"] == 1
    assert all(
        report["integrity"]["deadline_latency_source"] == "synthetic_case_fixture"
        for report in evaluation["case_reports"]
    )
    table = pq.read_table(first / "trajectory.parquet")
    assert table.num_rows == expected["trajectory_row_count"]
    assert table.schema.field("joint_position_rad").type.list_size == 14
    assert table.schema.field("action_rad").type.list_size == 14

print(
    "evaluator bundle verified: five files byte-identical across two same-host runs, "
    "160 Parquet rows, 40 decoded MP4 frames"
)
