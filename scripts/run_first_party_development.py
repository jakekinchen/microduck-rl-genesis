#!/usr/bin/env python3
"""Run and verify one provenance-locked first-party Apple development smoke."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, os.fspath(ROOT))

from evaluator.core import sha256, stable_json_bytes  # noqa: E402
from evaluator.first_party_development import (  # noqa: E402
    semantic_projection,
    validate_bundle,
    write_bundle,
)
from experiments.first_party.development import (  # noqa: E402
    ORIGIN,
    PLAN_PATH,
    RECEIPT_ROOT,
    git,
    load_json,
    require_clean_source,
    validate_artifact_admission,
    validate_evaluation_admission,
    validate_plan,
)


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def entry(path: Path) -> dict[str, str]:
    return {"path": relative(path), "sha256": sha256(path)}


def run_logged(command: list[str], log: Path, timeout: int, env: dict[str, str] | None = None) -> float:
    started = time.monotonic()
    with log.open("wb") as stream:
        stream.write(("COMMAND: " + " ".join(command) + "\n").encode())
        stream.flush()
        subprocess.run(command, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT, check=True, timeout=timeout)
    return time.monotonic() - started


def frozen_sources() -> dict[str, str]:
    paths = [
        "train.py", "export_onnx.py", "microduck/velocity_cfg.py",
        "microduck/velocity_env.py", "microduck/constants.py",
        "microduck/terrain.py", "microduck/bam_actuator.py",
        "evaluator/core.py", "evaluator/first_party_development.py",
        "evaluator/first-party-development-suite-v1.json",
        "experiments/first_party/development.py",
        "experiments/first_party/development-plan-v1.json",
        "scripts/run_first_party_development.py",
    ]
    return {name: sha256(ROOT / name) for name in paths}


def authority_inputs() -> dict[str, dict[str, str]]:
    paths = {
        "apple_dependency_lock": ROOT / "environments/apple/requirements.lock",
        "walking_task": ROOT / "microduck_contract/tasks/walking-v1.json",
        "model_lock": ROOT / "microduck_contract/model/microduck-walk-v1.lock.json",
        "bam_lock": ROOT / "microduck_contract/actuator/bam-m6-xl330-v1.lock.json",
        "bam_parameters": ROOT / "microduck/assets/xl330_m6.json",
        "observation_contract": ROOT / "microduck_contract/interface/observation-v1.json",
        "action_contract": ROOT / "microduck_contract/interface/action-v1.json",
        "control_contract": ROOT / "microduck_contract/interface/control-v1.json",
    }
    return {name: entry(path) for name, path in paths.items()}


def write_sums(output: Path) -> None:
    rows = []
    for path in sorted(p for p in output.rglob("*") if p.is_file() and p.name != "SHA256SUMS"):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        rows.append(f"{digest}  ./{path.relative_to(output).as_posix()}")
    (output / "SHA256SUMS").write_text("\n".join(rows) + "\n")


def verify_sums(output: Path) -> None:
    subprocess.run(["shasum", "-a", "256", "-c", "SHA256SUMS"], cwd=output, check=True)


def run(plan_path: Path, output: Path, bam_repo: Path) -> None:
    plan_path = plan_path.resolve()
    plan = load_json(plan_path)
    validate_plan(plan)
    source_revision = require_clean_source()
    output = output.resolve()
    output.relative_to(RECEIPT_ROOT.resolve())
    if output.exists():
        raise RuntimeError(f"refusing existing output: {output}")
    output.mkdir(parents=True)
    log_dir = ROOT / "logs" / plan["plan_id"]
    if log_dir.exists():
        raise RuntimeError(f"refusing existing training log directory: {log_dir}")
    training_dir = output / "training"
    training_dir.mkdir()
    frozen = {
        "schema_version": "microduck.first-party-frozen-run/v1",
        "origin": ORIGIN,
        "source_revision": source_revision,
        "source_tree_clean_before_run": True,
        "plan": entry(plan_path),
        "seed": plan["seed"], "resume": None,
        "num_environments": plan["num_environments"],
        "learning_iterations": plan["learning_iterations"],
        "steps_per_environment_per_iteration": plan["steps_per_environment_per_iteration"],
        "planned_transitions": plan["planned_transitions"],
        "source_files": frozen_sources(),
        "authority_inputs": authority_inputs(),
        "commands": plan["commands"],
        "evidence_boundary": plan["evidence_boundary"],
    }
    frozen_path = output / "FROZEN_RUN.json"
    frozen_path.write_bytes(stable_json_bytes(frozen))
    train_command = [
        sys.executable, "train.py", "--task", "walking", "--physics-backend", "metal",
        "--learner-device", "mps", "--num-envs", str(plan["num_environments"]),
        "--max-iterations", str(plan["learning_iterations"]), "--seed", str(plan["seed"]),
        "--exp-name", plan["plan_id"],
    ]
    env = dict(os.environ)
    env["GS_ENABLE_ZEROCOPY"] = "1"
    training_seconds = run_logged(train_command, output / "training.log", plan["maximum_training_wall_seconds"], env)
    checkpoint_source = log_dir / f"model_{plan['learning_iterations'] - 1}.pt"
    config_source = log_dir / "cfgs.pkl"
    if not checkpoint_source.is_file() or not config_source.is_file():
        raise RuntimeError("training did not emit the expected final checkpoint/config")
    checkpoint = training_dir / "source-checkpoint.pt"
    config = training_dir / "cfgs.pkl"
    shutil.copy2(checkpoint_source, checkpoint)
    shutil.copy2(config_source, config)
    policy = output / "policy.normalized.fixed-batch.onnx"
    normalizer = output / "normalizer.json"
    parity = output / "export-parity.json"
    artifact_admission = {
        "schema_version": "microduck.first-party-artifact-admission/v1",
        "origin": ORIGIN, "resume": None, "source_revision": source_revision,
        "frozen_run": entry(frozen_path), "training_config": entry(config), "checkpoint": entry(checkpoint),
        "policy_output": {"path": relative(policy)},
        "normalizer_output": {"path": relative(normalizer)},
        "parity_output": {"path": relative(parity)},
    }
    artifact_admission_path = output / "ARTIFACT_ADMISSION.json"
    artifact_admission_path.write_bytes(stable_json_bytes(artifact_admission))
    export_command = [
        sys.executable, "export_onnx.py", "--log-dir", os.fspath(training_dir),
        "--checkpoint-file", os.fspath(checkpoint), "--output", os.fspath(policy),
        "--normalizer-output", os.fspath(normalizer), "--parity-output", os.fspath(parity),
        "--fixed-batch", "--first-party-admission", os.fspath(artifact_admission_path),
    ]
    export_seconds = run_logged(export_command, output / "export.log", 300, env)
    parity_result = load_json(parity)
    if not parity_result["random_probe"]["passed"] or not parity_result["real_observation_episode"]["passed"]:
        raise RuntimeError("Torch/ONNX parity gate failed")
    association = {
        "schema_version": "microduck.first-party-export-association/v1",
        "origin": ORIGIN,
        "checkpoint": entry(checkpoint), "normalizer": entry(normalizer),
        "normalized_onnx": entry(policy), "parity": entry(parity),
        "input_shape": [1, 61], "output_shape": [1, 14], "control_hz": 50,
    }
    (output / "EXPORT_ASSOCIATION.json").write_bytes(stable_json_bytes(association))
    suite = ROOT / plan["evaluation"]["suite"]
    evaluation_admission = {
        "schema_version": "microduck.first-party-evaluation-admission/v1",
        "origin": ORIGIN, "held_out": False, "source_revision": source_revision,
        "artifact_admission_sha256": sha256(artifact_admission_path),
        "checkpoint": entry(checkpoint), "policy": entry(policy),
        "normalizer": entry(normalizer), "suite_sha256": sha256(suite),
    }
    evaluation_admission_path = output / "EVALUATION_ADMISSION.json"
    evaluation_admission_path.write_bytes(stable_json_bytes(evaluation_admission))
    evaluation_seconds = []
    for index in (1, 2):
        started = time.monotonic()
        write_bundle(policy, bam_repo.resolve(), evaluation_admission_path, output / f"evaluation-{index}")
        evaluation_seconds.append(time.monotonic() - started)
    first = load_json(output / "evaluation-1/evaluation.json")
    second = load_json(output / "evaluation-2/evaluation.json")
    semantic_equal = semantic_projection(first) == semantic_projection(second)
    trajectory_equal = (output / "evaluation-1/trajectory.parquet").read_bytes() == (output / "evaluation-2/trajectory.parquet").read_bytes()
    video_equal = (output / "evaluation-1/rollout.mp4").read_bytes() == (output / "evaluation-2/rollout.mp4").read_bytes()
    comparison = {
        "schema_version": "microduck.first-party-repeatability/v1",
        "policy_sha256": sha256(policy), "repeat_count": 2,
        "semantic_outputs_equal": semantic_equal,
        "trajectory_parquet_bytes_equal": trajectory_equal,
        "rollout_mp4_bytes_equal": video_equal,
        "canonical_trajectory_sha256": [first["trajectory"]["canonical_sha256"], second["trajectory"]["canonical_sha256"]],
        "measured_inference_latency_retained_not_compared_for_determinism": True,
        "held_out": False, "task_success": "not_evaluated",
    }
    if not semantic_equal or not trajectory_equal:
        raise RuntimeError("repeated evaluator semantic outputs diverged")
    (output / "repeatability.json").write_bytes(stable_json_bytes(comparison))
    result = {
        "schema_version": "microduck.first-party-development-result/v1",
        "result": "bounded_smoke_and_visible_development_evaluation_complete",
        "source_revision": source_revision, "origin": ORIGIN,
        "training": {"transitions": plan["planned_transitions"], "wall_seconds": training_seconds, "checkpoint": entry(checkpoint)},
        "export": {"wall_seconds": export_seconds, "policy": entry(policy), "normalizer": entry(normalizer), "parity": parity_result},
        "evaluation": {"wall_seconds": evaluation_seconds, "repeatability": comparison, "first": first, "second": second},
        "official_or_community_roles_closed": [],
        "evidence_boundary": plan["evidence_boundary"],
    }
    (output / "RESULT.json").write_bytes(stable_json_bytes(result))
    write_sums(output)
    verify(output, bam_repo)


def verify(output: Path, bam_repo: Path) -> None:
    output = output.resolve()
    output.relative_to(RECEIPT_ROOT.resolve())
    verify_sums(output)
    artifact = validate_artifact_admission(output / "ARTIFACT_ADMISSION.json")
    policy = ROOT / load_json(output / "EVALUATION_ADMISSION.json")["policy"]["path"]
    validate_evaluation_admission(output / "EVALUATION_ADMISSION.json", policy)
    validate_bundle(output / "evaluation-1", policy)
    validate_bundle(output / "evaluation-2", policy)
    result = load_json(output / "RESULT.json")
    if result["official_or_community_roles_closed"] or result["evaluation"]["first"]["held_out"]:
        raise RuntimeError("development receipt crossed authority boundary")
    if artifact["origin"] != ORIGIN:
        raise RuntimeError("wrong first-party origin")
    print(f"verified {output}")


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "verify"):
        command = sub.add_parser(name)
        command.add_argument("--output", required=True, type=Path)
        command.add_argument("--bam-repo", required=True, type=Path)
        if name == "run":
            command.add_argument("--plan", type=Path, default=PLAN_PATH)
    args = parser.parse_args()
    if args.command == "run":
        run(args.plan, args.output, args.bam_repo)
    else:
        verify(args.output, args.bam_repo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
