"""Evaluate one admitted first-party policy on frozen visible cases."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import platform
from pathlib import Path
from typing import Any

import imageio.v2 as imageio
import numpy as np
import pyarrow.parquet as pq

from evaluator.bundle import FILES, parquet_table, write_parquet, write_video
from evaluator.core import CONFIG_PATH, EvaluatorCore, sha256, stable_json_bytes
from evaluator.determinism import canonical_trajectory_sha256, semantic_report_projection
from experiments.first_party.development import ROOT, validate_evaluation_admission

SUITE_PATH = Path(__file__).with_name("first-party-development-suite-v1.json")


def validate_suite(suite: dict[str, Any]) -> None:
    if suite.get("schema_version") != "microduck.first-party-evaluator-suite/v1":
        raise AssertionError("wrong first-party suite schema")
    if suite.get("visibility") != "public-development" or suite.get("held_out"):
        raise AssertionError("first-party writer accepts visible development only")
    if suite.get("proof_class") != "first_party_development":
        raise AssertionError("wrong first-party proof class")
    heldout = json.loads((ROOT / "microduck_contract/tasks/walking-v1.json").read_text())["acceptance"]["seeds"]
    seeds = [case["seed"] for case in suite["cases"]]
    if len(seeds) != len(set(seeds)) or set(seeds).intersection(heldout):
        raise AssertionError("development seeds overlap held-out/public acceptance seeds")


def _case_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    root = np.asarray([row["root_position_m"] for row in rows], dtype=np.float64)
    actions = np.asarray([row["action_rad"] for row in rows], dtype=np.float64)
    torques = np.asarray([row["actuator_torque_nm"] for row in rows], dtype=np.float64)
    return {
        "physics_steps": len(rows),
        "duration_s": float(rows[-1]["time_s"]),
        "final_root_position_m": root[-1].tolist(),
        "root_displacement_m": (root[-1] - root[0]).tolist(),
        "minimum_root_height_m": float(root[:, 2].min()),
        "maximum_root_height_m": float(root[:, 2].max()),
        "maximum_absolute_action_rad": float(np.abs(actions).max()),
        "maximum_absolute_actuator_torque_nm": float(np.abs(torques).max()),
    }


def write_bundle(policy: Path, bam_repo: Path, admission: Path, output: Path) -> None:
    admitted = validate_evaluation_admission(admission, policy)
    suite = json.loads(SUITE_PATH.read_text())
    validate_suite(suite)
    if admitted["suite_sha256"] != sha256(SUITE_PATH):
        raise RuntimeError("evaluation suite differs from admission")
    if output.exists() and any(output.iterdir()):
        raise RuntimeError(f"bundle output must be new or empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    reports, rows, frames, metrics = [], [], [], []
    for case_row in suite["cases"]:
        case = {"task_id": suite["task_id"], **case_row}
        core = EvaluatorCore(policy, bam_repo, suite["task_id"], "first_party_development")
        core.model.vis.quality.offsamples = 1
        report, case_rows, case_frames = core.run_case(case, capture_frames=True)
        reports.append(report)
        rows.extend(case_rows)
        frames.extend(case_frames)
        metrics.append({"case_id": case["case_id"], **_case_metrics(case_rows)})
    trajectory = output / "trajectory.parquet"
    rollout = output / "rollout.mp4"
    environment = output / "environment-lock.json"
    evaluation = output / "evaluation.json"
    attestation = output / "attestation.json"
    write_parquet(rows, trajectory)
    # One frame is captured at every 50 Hz control update, so encode at 50 fps.
    write_video(frames, rollout, fps=50)
    environment.write_bytes(stable_json_bytes({
        "schema_version": "microduck.first-party-evaluator-environment/v1",
        "platform": {"system": platform.system(), "machine": platform.machine(), "release": platform.release(), "python": platform.python_version()},
        "packages": {name: importlib.metadata.version(name) for name in ("mujoco", "numpy", "onnxruntime", "pyarrow", "imageio", "imageio-ffmpeg")},
        "apple_requirements_lock_sha256": sha256(ROOT / "environments/apple/requirements.lock"),
        "evaluator_config_sha256": sha256(CONFIG_PATH),
        "evaluator_sources": {"evaluator/core.py": sha256(ROOT / "evaluator/core.py"), "evaluator/first_party_development.py": sha256(Path(__file__))},
        "suite_sha256": sha256(SUITE_PATH),
        "absolute_paths_recorded": False,
    }))
    evaluation.write_bytes(stable_json_bytes({
        "schema_version": "microduck.first-party-evaluation/v1",
        "suite_id": suite["suite_id"], "visibility": "public-development", "held_out": False,
        "proof_class": "first_party_development", "task_success": "not_evaluated",
        "policy_sha256": sha256(policy), "case_reports": reports, "measured_case_metrics": metrics,
        "trajectory": {"row_count": len(rows), "case_count": len(suite["cases"]), "all_finite": all(row["finite"] for row in rows), "canonical_sha256": canonical_trajectory_sha256(rows)},
        "video": {"frame_count": len(frames), "fps": 50, "width": int(frames[0].shape[1]), "height": int(frames[0].shape[0]), "codec": "libx264/yuv420p", "offscreen_samples": 1},
        "artifacts": {"trajectory.parquet": sha256(trajectory), "rollout.mp4": sha256(rollout), "environment-lock.json": sha256(environment)},
        "evidence_boundary": suite["evidence_boundary"],
    }))
    attestation.write_bytes(stable_json_bytes({
        "schema_version": "microduck.first-party-evaluator-attestation/v1",
        "suite_id": suite["suite_id"], "policy_sha256": sha256(policy),
        "artifacts": {name: sha256(output / name) for name in FILES if name != "attestation.json"},
        "proof_class": "first_party_development", "task_success": "not_evaluated", "held_out": False,
    }))
    validate_bundle(output, policy)


def validate_bundle(output: Path, policy: Path) -> None:
    if {path.name for path in output.iterdir() if path.is_file()} != set(FILES):
        raise AssertionError("first-party bundle names mismatch")
    result = json.loads((output / "evaluation.json").read_text())
    attest = json.loads((output / "attestation.json").read_text())
    if result["proof_class"] != "first_party_development" or result["held_out"] or result["task_success"] != "not_evaluated":
        raise AssertionError("first-party development evidence was promoted")
    if attest["policy_sha256"] != sha256(policy):
        raise AssertionError("first-party policy digest mismatch")
    for name, digest in attest["artifacts"].items():
        if sha256(output / name) != digest:
            raise AssertionError(f"first-party artifact digest mismatch: {name}")
    table = pq.read_table(output / "trajectory.parquet")
    if table.num_rows != result["trajectory"]["row_count"]:
        raise AssertionError("trajectory row count mismatch")
    reader = imageio.get_reader(output / "rollout.mp4", "ffmpeg")
    try:
        frames = sum(1 for _ in reader)
    finally:
        reader.close()
    if frames != result["video"]["frame_count"]:
        raise AssertionError("rollout frame count mismatch")


def semantic_projection(result: dict[str, Any]) -> dict[str, Any]:
    projected = json.loads(json.dumps(result))
    projected.pop("artifacts", None)
    for report in projected["case_reports"]:
        report["integrity"].pop("measured_inference_latency_ms", None)
        report["integrity"].pop("deadline_miss_count", None)
        report["integrity"].pop("deadline_latency_source", None)
        report.pop("runtime", None)
    return projected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--bam-repo", required=True, type=Path)
    parser.add_argument("--admission", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    write_bundle(args.policy.resolve(), args.bam_repo.resolve(), args.admission.resolve(), args.output.resolve())
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
