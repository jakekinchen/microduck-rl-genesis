"""Verify deterministic visible-development evaluator artifact bundles."""

from __future__ import annotations

import copy
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from unittest import mock

import numpy as np
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, os.fspath(ROOT))

import evaluator.bundle as bundle_module  # noqa: E402
from evaluator.bundle import FILES, SUITE_PATH, validate_bundle, validate_suite, write_bundle  # noqa: E402
from evaluator.bundle_diagnostics import compare_bundle_bytes, format_bundle_differences  # noqa: E402
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
    original_write_parquet = bundle_module.write_parquet
    original_write_video = bundle_module.write_video
    captured_rows = []
    captured_frames = []

    def infer_with_latency(latency_ms: float):
        def wrapped(policy, observation):
            action, _ = original_infer(policy, observation)
            return action, latency_ms

        return wrapped

    def capture_parquet(rows, path):
        captured_rows.append(copy.deepcopy(rows))
        original_write_parquet(rows, path)

    def capture_video(frames, path):
        captured_frames.append([frame.copy() for frame in frames])
        original_write_video(frames, path)

    outputs = []
    with mock.patch.multiple(
        bundle_module.platform,
        system=mock.Mock(return_value="Linux"),
        machine=mock.Mock(return_value="x86_64"),
        release=mock.Mock(return_value="6.8.0-117-generic"),
        python_version=mock.Mock(return_value="3.12.14"),
    ), mock.patch.object(
        bundle_module, "write_parquet", capture_parquet
    ), mock.patch.object(
        bundle_module, "write_video", capture_video
    ):
        for index, latency_ms in enumerate((25.0, 1.0, 17.0, 3.0, 11.0, 7.0)):
            output = Path(temp) / f"repeat-{index}"
            outputs.append(output)
            with mock.patch.object(
                OnnxPolicy, "infer", infer_with_latency(latency_ms)
            ):
                write_bundle(POLICY, Path(BAM_REPO), output)
    first, second = outputs[:2]
    for output in outputs:
        validate_bundle(output, POLICY)
        differences = compare_bundle_bytes(first, output, FILES)
        assert not differences, format_bundle_differences(differences)
    assert all(rows == captured_rows[0] for rows in captured_rows[1:])
    assert all(
        len(frames) == len(captured_frames[0])
        and all(
            np.array_equal(left, right)
            for left, right in zip(captured_frames[0], frames)
        )
        for frames in captured_frames[1:]
    )

    isolated_parquet_hashes = set()
    isolated_video_hashes = set()
    for index in range(6):
        parquet_path = Path(temp) / f"isolated-{index}.parquet"
        video_path = Path(temp) / f"isolated-{index}.mp4"
        original_write_parquet(captured_rows[0], parquet_path)
        original_write_video(captured_frames[0], video_path)
        isolated_parquet_hashes.add(sha256(parquet_path))
        isolated_video_hashes.add(sha256(video_path))
    assert len(isolated_parquet_hashes) == 1, sorted(isolated_parquet_hashes)
    assert len(isolated_video_hashes) == 1, sorted(isolated_video_hashes)

    first_hashes = {name: sha256(first / name) for name in FILES}
    second_hashes = {name: sha256(second / name) for name in FILES}
    differences = compare_bundle_bytes(first, second, FILES)
    assert not differences, format_bundle_differences(differences)
    assert first_hashes == second_hashes, format_bundle_differences(differences)
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

    changed_json = Path(temp) / "changed-json"
    shutil.copytree(first, changed_json)
    environment = json.loads((changed_json / "environment-lock.json").read_text())
    environment["platform"]["release"] = "diagnostic-drift"
    (changed_json / "environment-lock.json").write_text(
        json.dumps(environment, indent=2, sort_keys=True) + "\n"
    )
    diagnostic = compare_bundle_bytes(first, changed_json, FILES)
    assert [item["name"] for item in diagnostic] == ["environment-lock.json"]
    assert diagnostic[0]["left_sha256"] != diagnostic[0]["right_sha256"]
    assert diagnostic[0]["first_byte_difference"]["offset"] >= 0
    assert diagnostic[0]["json_differences"] == [{
        "path": "$.platform.release",
        "left": "6.8.0-117-generic",
        "right": "diagnostic-drift",
    }]

    changed_parquet = Path(temp) / "changed-parquet"
    shutil.copytree(first, changed_parquet)
    pq.write_table(
        pq.read_table(first / "trajectory.parquet"),
        changed_parquet / "trajectory.parquet",
        compression=None,
    )
    diagnostic = compare_bundle_bytes(first, changed_parquet, FILES)
    assert [item["name"] for item in diagnostic] == ["trajectory.parquet"]
    assert diagnostic[0]["parquet"]["semantic_table_equal"]

    changed_video = Path(temp) / "changed-video"
    shutil.copytree(first, changed_video)
    rollout = changed_video / "rollout.mp4"
    rollout.write_bytes(rollout.read_bytes() + b"diagnostic-container-tail")
    diagnostic = compare_bundle_bytes(first, changed_video, FILES)
    assert [item["name"] for item in diagnostic] == ["rollout.mp4"]
    assert diagnostic[0]["video"]["decoded_frames_equal"]

    changed_frames = Path(temp) / "changed-frames"
    shutil.copytree(first, changed_frames)
    perturbed_frames = [frame.copy() for frame in captured_frames[0]]
    perturbed_frames[0][0:24, 0:24, :] = 255 - perturbed_frames[0][0:24, 0:24, :]
    original_write_video(perturbed_frames, changed_frames / "rollout.mp4")
    diagnostic = compare_bundle_bytes(first, changed_frames, FILES)
    assert [item["name"] for item in diagnostic] == ["rollout.mp4"]
    assert not diagnostic[0]["video"]["decoded_frames_equal"]
    assert diagnostic[0]["video"]["first_decoded_frame_difference"]["frame_index"] == 0
    assert (
        diagnostic[0]["video"]["first_decoded_frame_difference"]["different_values"]
        > 0
    )

    changed_attestation = Path(temp) / "changed-attestation"
    shutil.copytree(first, changed_attestation)
    attestation = json.loads((changed_attestation / "attestation.json").read_text())
    attestation["artifacts"]["rollout.mp4"] = "sha256:" + "0" * 64
    (changed_attestation / "attestation.json").write_text(
        json.dumps(attestation, indent=2, sort_keys=True) + "\n"
    )
    diagnostic = compare_bundle_bytes(first, changed_attestation, FILES)
    assert [item["name"] for item in diagnostic] == ["attestation.json"]
    assert diagnostic[0]["changed_attested_artifacts"] == ["rollout.mp4"]

    with mock.patch.object(bundle_module.imageio, "mimsave") as save_video:
        original_write_video(
            [np.zeros((2, 2, 3), dtype=np.uint8)],
            Path(temp) / "bitexact-probe.mp4",
        )
    output_params = save_video.call_args.kwargs["output_params"]
    assert ["-fflags", "+bitexact"] == output_params[
        output_params.index("-fflags") : output_params.index("-fflags") + 2
    ]
    assert ["-flags:v", "+bitexact"] == output_params[
        output_params.index("-flags:v") : output_params.index("-flags:v") + 2
    ]
    assert output_params[output_params.index("-x264-params") + 1] == (
        "threads=1:lookahead_threads=1:sliced_threads=0:sync-lookahead=0"
    )

print(
    "evaluator bundle verified: five files byte-identical across six same-host runs, "
    "isolated Parquet/MP4 producers stable, diagnostics fail closed, "
    "160 Parquet rows, 40 decoded MP4 frames"
)
