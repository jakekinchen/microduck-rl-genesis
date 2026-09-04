"""Admission and receipt helpers for first-party development artifacts."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PLAN_PATH = Path(__file__).with_name("development-plan-v1.json")
RECEIPT_ROOT = ROOT / "receipts/first-party-development"
ORIGIN = "first_party_local_from_scratch"


class AdmissionError(RuntimeError):
    """The artifact is not the exact first-party run admitted by this route."""


def stable_json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def _inside(path: Path, parent: Path) -> Path:
    path = path if path.is_absolute() else ROOT / path
    parent = parent.resolve()
    try:
        path.absolute().relative_to(parent)
    except ValueError as exc:
        raise AdmissionError(f"path escapes admitted root: {path}") from exc
    cursor = path.absolute()
    while cursor != parent:
        if cursor.is_symlink():
            raise AdmissionError(f"symlink rejected in admitted path: {cursor}")
        cursor = cursor.parent
    resolved = path.resolve(strict=False)
    try:
        resolved.relative_to(parent)
    except ValueError as exc:
        raise AdmissionError(f"resolved path escapes admitted root: {path}") from exc
    return resolved


def validate_plan(plan: dict[str, Any]) -> None:
    expected = {
        "schema_version": "microduck.first-party-development-plan/v1",
        "origin": ORIGIN,
        "task": "walking",
        "seed": 26090401,
        "resume": None,
        "physics_backend": "metal",
        "learner_device": "mps",
        "num_environments": 1024,
        "learning_iterations": 100,
        "steps_per_environment_per_iteration": 24,
        "planned_transitions": 2_457_600,
        "maximum_training_wall_seconds": 1800,
        "rough": False,
        "backlash": False,
    }
    for key, value in expected.items():
        if plan.get(key) != value:
            raise AdmissionError(f"development plan drift: {key}")
    if plan["planned_transitions"] != (
        plan["num_environments"]
        * plan["learning_iterations"]
        * plan["steps_per_environment_per_iteration"]
    ):
        raise AdmissionError("planned transition arithmetic mismatch")
    if plan["evaluation"]["held_out"] or plan["evaluation"]["repeat_count"] != 2:
        raise AdmissionError("development plan attempted held-out or non-repeated evaluation")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def require_clean_source() -> str:
    if git("status", "--porcelain", "--untracked-files=all"):
        raise AdmissionError("first-party run requires a clean committed source tree")
    return git("rev-parse", "HEAD^{commit}")


def validate_artifact_admission(path: Path) -> dict[str, Any]:
    path = _inside(path, RECEIPT_ROOT)
    if not path.is_file():
        raise AdmissionError(f"missing artifact admission: {path}")
    record = load_json(path)
    if record.get("schema_version") != "microduck.first-party-artifact-admission/v1":
        raise AdmissionError("wrong artifact-admission schema")
    if record.get("origin") != ORIGIN or record.get("resume") is not None:
        raise AdmissionError("artifact is not a first-party from-scratch run")
    source_revision = record.get("source_revision", "")
    try:
        git("cat-file", "-e", f"{source_revision}^{{commit}}")
    except subprocess.CalledProcessError as exc:
        raise AdmissionError("artifact source revision is not a local commit") from exc
    for field in ("frozen_run", "training_config", "checkpoint"):
        entry = record[field]
        candidate = _inside(Path(entry["path"]), path.parent)
        if not candidate.is_file() or sha256(candidate) != entry["sha256"]:
            raise AdmissionError(f"admitted {field} digest mismatch")
    frozen = load_json(_inside(Path(record["frozen_run"]["path"]), path.parent))
    if frozen.get("source_revision") != source_revision:
        raise AdmissionError("frozen-run source revision mismatch")
    for source_path, expected in frozen.get("source_files", {}).items():
        current = _inside(Path(source_path), ROOT)
        if not current.is_file() or sha256(current) != expected:
            raise AdmissionError(f"current source differs from admitted run: {source_path}")
        committed = subprocess.check_output(
            ["git", "show", f"{source_revision}:{source_path}"], cwd=ROOT
        )
        actual = "sha256:" + hashlib.sha256(committed).hexdigest()
        if actual != expected:
            raise AdmissionError(f"committed source differs from admitted run: {source_path}")
    return record


def validate_export_admission(
    admission_path: Path,
    log_dir: Path,
    checkpoint: Path,
    output: Path,
    normalizer_output: Path,
    parity_output: Path,
) -> dict[str, Any]:
    record = validate_artifact_admission(admission_path)
    receipt = admission_path.resolve().parent
    exact = {
        "training_config": _inside(log_dir / "cfgs.pkl", receipt),
        "checkpoint": _inside(checkpoint, receipt),
        "policy_output": _inside(output, receipt),
        "normalizer_output": _inside(normalizer_output, receipt),
        "parity_output": _inside(parity_output, receipt),
    }
    for name, candidate in exact.items():
        if os.fspath(candidate.relative_to(ROOT)) != record[name]["path"]:
            raise AdmissionError(f"{name} path differs from frozen admission")
    return record


def validate_evaluation_admission(path: Path, policy: Path) -> dict[str, Any]:
    path = _inside(path, RECEIPT_ROOT)
    record = load_json(path)
    if record.get("schema_version") != "microduck.first-party-evaluation-admission/v1":
        raise AdmissionError("wrong evaluation-admission schema")
    if record.get("origin") != ORIGIN or record.get("held_out"):
        raise AdmissionError("evaluation origin or visibility rejected")
    artifact = validate_artifact_admission(path.parent / "ARTIFACT_ADMISSION.json")
    if record.get("artifact_admission_sha256") != sha256(path.parent / "ARTIFACT_ADMISSION.json"):
        raise AdmissionError("evaluation-to-artifact admission mismatch")
    policy = _inside(policy, path.parent)
    if os.fspath(policy.relative_to(ROOT)) != record["policy"]["path"]:
        raise AdmissionError("evaluation policy path mismatch")
    if sha256(policy) != record["policy"]["sha256"]:
        raise AdmissionError("evaluation policy digest mismatch")
    if record["checkpoint"]["sha256"] != artifact["checkpoint"]["sha256"]:
        raise AdmissionError("evaluation checkpoint digest mismatch")
    return record
