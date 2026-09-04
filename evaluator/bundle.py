"""Write and validate the deterministic five-file evaluator artifact bundle."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any

import imageio.v2 as imageio
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, os.fspath(ROOT))

from evaluator.core import CONFIG_PATH, EvaluatorCore, sha256, stable_json_bytes  # noqa: E402

SUITE_PATH = Path(__file__).with_name("development-suite-v1.json")
FILES = (
    "evaluation.json",
    "trajectory.parquet",
    "rollout.mp4",
    "environment-lock.json",
    "attestation.json",
)
DETERMINISTIC_OFFSCREEN_SAMPLES = 1
DETERMINISTIC_SYNTHETIC_LATENCY_MS = 0.0


def parquet_table(rows: list[dict[str, Any]]) -> pa.Table:
    vector_fields = {
        "root_position_m": 3,
        "root_quaternion_wxyz": 4,
        "joint_position_rad": 14,
        "joint_velocity_rad_s": 14,
        "action_rad": 14,
        "target_position_rad": 14,
        "actuator_torque_nm": 14,
        "twist_command": 3,
    }
    arrays: dict[str, pa.Array] = {
        "case_id": pa.array([row["case_id"] for row in rows], pa.string()),
        "physics_step": pa.array([row["physics_step"] for row in rows], pa.int32()),
        "control_step": pa.array([row["control_step"] for row in rows], pa.int32()),
        "time_s": pa.array([row["time_s"] for row in rows], pa.float64()),
    }
    for name, size in vector_fields.items():
        arrays[name] = pa.array(
            [row[name] for row in rows], type=pa.list_(pa.float64(), size)
        )
    arrays["finite"] = pa.array([row["finite"] for row in rows], pa.bool_())
    return pa.table(arrays)


def write_parquet(rows: list[dict[str, Any]], path: Path) -> None:
    pq.write_table(
        parquet_table(rows),
        path,
        compression="zstd",
        compression_level=9,
        use_dictionary=False,
        write_statistics=True,
        data_page_version="2.0",
        version="2.6",
    )


def write_video(frames: list[np.ndarray], path: Path) -> None:
    if not frames:
        raise RuntimeError("rollout video requires at least one frame")
    imageio.mimsave(
        path,
        frames,
        fps=25,
        codec="libx264",
        quality=8,
        macro_block_size=None,
        ffmpeg_log_level="error",
        output_params=[
            "-threads", "1",
            "-map_metadata", "-1",
            "-metadata", "creation_time=",
            "-metadata", "encoder=microduck-evaluator",
        ],
    )


def validate_suite(suite: dict[str, Any]) -> None:
    if suite["schema_version"] != "microduck.evaluator-suite/v1":
        raise AssertionError("unexpected development suite schema")
    if suite["visibility"] != "public-development" or suite["held_out"]:
        raise AssertionError("this writer accepts visible development cases only")
    if suite["proof_class"] != "infrastructure_only" or suite["candidate_policy_allowed"]:
        raise AssertionError("development bundle cannot inspect a candidate policy")
    task = json.loads((ROOT / "microduck_contract/tasks/walking-v1.json").read_text())
    acceptance_seeds = set(task["acceptance"]["seeds"])
    seeds = [case["seed"] for case in suite["cases"]]
    if len(seeds) != len(set(seeds)) or acceptance_seeds.intersection(seeds):
        raise AssertionError("development and acceptance seeds must be unique and disjoint")
    case_ids = [case["case_id"] for case in suite["cases"]]
    if len(case_ids) != len(set(case_ids)):
        raise AssertionError("development case IDs must be unique")


def write_bundle(policy: Path, bam_repo: Path, output: Path) -> dict[str, Any]:
    suite = json.loads(SUITE_PATH.read_text())
    validate_suite(suite)
    if output.exists() and any(output.iterdir()):
        raise RuntimeError(f"bundle output must be new or empty: {output}")
    output.mkdir(parents=True, exist_ok=True)

    reports = []
    rows: list[dict[str, Any]] = []
    frames: list[np.ndarray] = []
    for case in suite["cases"]:
        case = {
            "task_id": suite["task_id"],
            **case,
            "synthetic_inference_latency_ms": DETERMINISTIC_SYNTHETIC_LATENCY_MS,
        }
        core = EvaluatorCore(policy, bam_repo, suite["task_id"])
        core.model.vis.quality.offsamples = DETERMINISTIC_OFFSCREEN_SAMPLES
        report, case_rows, case_frames = core.run_case(case, capture_frames=True)
        reports.append(report)
        rows.extend(case_rows)
        frames.extend(case_frames)

    trajectory_path = output / "trajectory.parquet"
    video_path = output / "rollout.mp4"
    environment_path = output / "environment-lock.json"
    evaluation_path = output / "evaluation.json"
    attestation_path = output / "attestation.json"
    write_parquet(rows, trajectory_path)
    write_video(frames, video_path)

    environment = {
        "schema_version": "microduck.evaluator-environment/v1",
        "platform": {
            "system": platform.system(),
            "machine": platform.machine(),
            "release": platform.release(),
            "python": platform.python_version(),
        },
        "packages": {
            name: importlib.metadata.version(name)
            for name in ("mujoco", "numpy", "onnxruntime", "pyarrow", "imageio", "imageio-ffmpeg")
        },
        "apple_requirements_lock_sha256": sha256(ROOT / "environments/apple/requirements.lock"),
        "evaluator_config_sha256": sha256(CONFIG_PATH),
        "evaluator_sources": {
            "evaluator/core.py": sha256(ROOT / "evaluator/core.py"),
            "evaluator/bundle.py": sha256(Path(__file__)),
        },
        "suite_sha256": sha256(SUITE_PATH),
        "absolute_paths_recorded": False,
    }
    environment_path.write_bytes(stable_json_bytes(environment))

    evaluation = {
        "schema_version": "microduck.evaluation/v1",
        "suite_id": suite["suite_id"],
        "visibility": suite["visibility"],
        "held_out": False,
        "proof_class": "infrastructure_only",
        "classification": "infrastructure_pass",
        "task_success": "not_evaluated",
        "policy_sha256": sha256(policy),
        "case_reports": reports,
        "artifacts": {
            "trajectory.parquet": sha256(trajectory_path),
            "rollout.mp4": sha256(video_path),
            "environment-lock.json": sha256(environment_path),
        },
        "trajectory": {
            "schema": str(parquet_table(rows).schema),
            "row_count": len(rows),
            "case_count": len(suite["cases"]),
            "all_finite": all(row["finite"] for row in rows),
        },
        "video": {
            "frame_count": len(frames),
            "fps": 25,
            "width": int(frames[0].shape[1]),
            "height": int(frames[0].shape[0]),
            "codec": "libx264/yuv420p",
            "offscreen_samples": DETERMINISTIC_OFFSCREEN_SAMPLES,
            "codec_level_cross_host_byte_determinism": "not_claimed",
        },
        "evidence_boundary": suite["evidence_boundary"],
    }
    evaluation_path.write_bytes(stable_json_bytes(evaluation))

    attestation = {
        "schema_version": "microduck.evaluator-attestation/v1",
        "suite_id": suite["suite_id"],
        "policy_sha256": sha256(policy),
        "artifacts": {
            name: sha256(output / name)
            for name in FILES
            if name != "attestation.json"
        },
        "artifact_count": 4,
        "complete_required_names": list(FILES),
        "proof_class": "infrastructure_only",
        "task_success": "not_evaluated",
        "held_out": False,
    }
    attestation_path.write_bytes(stable_json_bytes(attestation))
    validate_bundle(output, policy)
    return attestation


def validate_bundle(root: Path, policy: Path) -> None:
    names = {path.name for path in root.iterdir() if path.is_file()}
    if names != set(FILES):
        raise AssertionError(f"bundle names mismatch: {sorted(names)}")
    evaluation = json.loads((root / "evaluation.json").read_text())
    environment = json.loads((root / "environment-lock.json").read_text())
    attestation = json.loads((root / "attestation.json").read_text())
    if evaluation["task_success"] != "not_evaluated" or evaluation["held_out"]:
        raise AssertionError("development bundle promoted task or held-out evidence")
    if environment["absolute_paths_recorded"]:
        raise AssertionError("environment lock contains absolute paths")
    if attestation["policy_sha256"] != sha256(policy):
        raise AssertionError("attestation policy digest mismatch")
    for name, digest in attestation["artifacts"].items():
        if sha256(root / name) != digest:
            raise AssertionError(f"artifact digest mismatch: {name}")
    table = pq.read_table(root / "trajectory.parquet")
    if table.num_rows != evaluation["trajectory"]["row_count"]:
        raise AssertionError("Parquet row count mismatch")
    finite = table.column("finite").to_numpy(zero_copy_only=False)
    if not finite.all():
        raise AssertionError("Parquet contains non-finite-state marker")
    reader = imageio.get_reader(root / "rollout.mp4", "ffmpeg")
    try:
        decoded = sum(1 for _ in reader)
    finally:
        reader.close()
    if decoded != evaluation["video"]["frame_count"]:
        raise AssertionError(f"decoded frame count mismatch: {decoded}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--bam-repo", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()
    if args.validate:
        validate_bundle(args.output.resolve(), args.policy.resolve())
    else:
        write_bundle(args.policy.resolve(), args.bam_repo.resolve(), args.output.resolve())
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
