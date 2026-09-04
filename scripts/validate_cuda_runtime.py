#!/usr/bin/env python3
"""Validate the refrozen CUDA contract, and optionally the active runtime."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata as metadata
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
EXPECTED_CONTAINER = "docker.io/nvidia/cuda@sha256:3986465b3dd3b4d602c07061f2cff417e0bfb24810129408d4eb12e111015a6c"
EXPECTED_COMPILE_COMMAND = (
    "uv pip compile --python-platform x86_64-manylinux_2_39 --python-version 3.12 "
    "--torch-backend cu128 --generate-hashes environments/cuda/requirements.in "
    "--output-file environments/cuda/requirements.lock"
)
EXPECTED_PACKAGES = {
    "genesis-world": "1.3.3",
    "mujoco": "3.12.0",
    "rsl-rl-lib": "5.4.2",
    "torch": "2.9.1+cu128",
}
EXPECTED_API = [
    "RigidSolver.dyn_state.dofs.qf_bias",
    "RigidSolver.dyn_state.dofs.qf_constraint",
]


def sha256_bytes(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def sha256_file(file_path: Path) -> str:
    return sha256_bytes(file_path.read_bytes())


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git_blob(root: Path, commit: str, relative: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(root), "show", f"{commit}:{relative}"],
        check=True,
        capture_output=True,
    ).stdout


def validate_contract(contract: dict[str, object], root: Path, check_runtime: bool = False) -> None:
    from experiments.m5.contract import validate_json_schema_instance

    schema = json.loads((root / "environments/cuda/runtime-v1.schema.json").read_text())
    validate_json_schema_instance(contract, schema)
    _assert(contract["state"] == "local_refreeze_review_required", "runtime state drift")
    _assert(contract["platform"] == "linux/amd64", "runtime platform drift")
    _assert(contract["lock_platform"] == "x86_64-manylinux_2_39", "lock platform drift")
    _assert(contract["python"] == "3.12", "Python runtime drift")
    _assert(contract["torch_backend"] == "cu128", "Torch backend drift")
    _assert(contract["packages"] == EXPECTED_PACKAGES, "package version drift")
    _assert(contract["required_api"] == EXPECTED_API, "required Genesis API drift")
    _assert(contract["headless_env"] == {"MUJOCO_GL": "egl", "PYGLET_HEADLESS": "1"}, "headless environment drift")
    _assert(contract["compute_authorized"] is False, "compute authorized by runtime contract")

    container = contract["container"]
    _assert(isinstance(container, dict), "container contract missing")
    _assert(container["immutable_reference"] == EXPECTED_CONTAINER, "container digest drift")
    _assert(container["platform"] == "linux/amd64" and container["glibc"] == "2.39", "container ABI drift")

    lock = contract["requirements_lock"]
    _assert(isinstance(lock, dict), "requirements lock contract missing")
    lock_path = root / str(lock["path"])
    _assert(lock_path.is_file(), "CUDA requirements lock missing")
    _assert(lock["compile_command"] == EXPECTED_COMPILE_COMMAND, "CUDA lock compile command drift")
    _assert(lock["sha256"] == sha256_file(lock_path), "CUDA requirements lock digest drift")
    lock_text = lock_path.read_text()
    for requirement in ("genesis-world==1.3.3", "mujoco==3.12.0", "rsl-rl-lib==5.4.2", "torch==2.9.1+cu128"):
        _assert(f"\n{requirement} " in lock_text, f"locked requirement missing: {requirement}")
    _assert("--hash=sha256:" in lock_text, "hash-locked distributions missing")

    upstream = contract["genesis_upstream"]
    _assert(isinstance(upstream, dict), "Genesis upstream contract missing")
    _assert(upstream["version"] == "1.3.3", "Genesis release drift")
    _assert(upstream["wheel_filename"] == "genesis_world-1.3.3-py3-none-any.whl", "Genesis wheel filename drift")
    _assert(upstream["release_commit"] == "76f8f5b3457e7c6d6a078de2244066f9a8694c45", "Genesis release commit drift")
    _assert(upstream["release_url"] == "https://github.com/Genesis-Embodied-AI/genesis-world/releases/tag/v1.3.3", "Genesis release URL drift")
    _assert(upstream["source_url"] == "https://github.com/Genesis-Embodied-AI/genesis-world/blob/76f8f5b3457e7c6d6a078de2244066f9a8694c45/genesis/engine/solvers/rigid/rigid_solver.py", "Genesis source URL drift")
    _assert(upstream["wheel_sha256"] == "sha256:74fcece3f080d2de86a25da9c26c979c192ed4a115d556133e8103169f74b3bf", "Genesis wheel drift")
    _assert(upstream["rigid_solver_sha256"] == "sha256:39e2af4ca559ece184ad4a12e8e59490f8127c89ced631299767a98ae58fd183", "Genesis solver source drift")

    rejected = contract["rejected_runtime"]
    _assert(isinstance(rejected, dict), "rejected runtime evidence missing")
    _assert(rejected["version"] == "1.2.2" and rejected["required_api_present"] is False, "terminal runtime boundary drift")
    _assert(rejected["wheel_filename"] == "genesis_world-1.2.2-py3-none-any.whl", "rejected wheel filename drift")
    _assert(rejected["wheel_sha256"] == "sha256:567d49f287e597b7118421a8d63ed3259875a5f3906c0a4b8585fc21a9a0fb9a", "rejected wheel drift")
    _assert(rejected["rigid_solver_sha256"] == "sha256:cf664fdc9bc7b7fda5560f12ef4bb56cd4837848d1449327891d2058b5117c7e", "rejected solver source drift")

    consumer = contract["consumer_source"]
    _assert(isinstance(consumer, dict), "consumer source contract missing")
    commit = str(consumer["commit"])
    files = consumer["files"]
    _assert(isinstance(files, dict) and set(files) == {"microduck/bam_actuator.py", "tests/test_external_torque.py"}, "dyn_state consumer set drift")
    for relative, expected in files.items():
        blob = git_blob(root, commit, relative)
        _assert(sha256_bytes(blob) == expected, f"consumer source drift: {relative}")
        _assert(b".dyn_state.dofs.qf_bias" in blob and b".dyn_state.dofs.qf_constraint" in blob, f"required API consumer missing: {relative}")

    preflight = contract["preflight"]
    _assert(isinstance(preflight, dict) and all(preflight.values()), "fail-closed preflight weakened")
    if check_runtime:
        validate_active_runtime(contract)


def validate_active_runtime(contract: dict[str, object], require_cuda: bool = False) -> dict[str, object]:
    import genesis
    import mujoco
    import torch

    installed = {
        "genesis-world": metadata.version("genesis-world"),
        "mujoco": mujoco.__version__,
        "rsl-rl-lib": metadata.version("rsl-rl-lib"),
        "torch": torch.__version__,
    }
    _assert(sys.version_info[:2] == (3, 12), "active Python runtime must be 3.12")
    expected = dict(EXPECTED_PACKAGES)
    if not require_cuda:
        expected["torch"] = expected["torch"].split("+")[0]
        installed["torch"] = installed["torch"].split("+")[0]
    _assert(installed == expected, f"active runtime version drift: {installed}")
    solver_source = Path(genesis.__file__).resolve().parent / "engine/solvers/rigid/rigid_solver.py"
    source = solver_source.read_bytes()
    _assert(sha256_bytes(source) == contract["genesis_upstream"]["rigid_solver_sha256"], "installed Genesis solver source drift")
    _assert(b"self.dyn_state = self.data_manager.dyn_state" in source, "required dyn_state runtime surface missing")
    if require_cuda:
        _assert(sys.platform.startswith("linux") and platform.machine() == "x86_64", "CUDA preflight requires linux/amd64")
        _assert(torch.cuda.is_available(), "Torch CUDA unavailable")
        _assert(torch.version.cuda == "12.8", "Torch CUDA version drift")
        _assert(os.environ.get("MUJOCO_GL") == "egl" and os.environ.get("PYGLET_HEADLESS") == "1", "headless runtime environment missing")
    return {
        "installed": installed,
        "python": platform.python_version(),
        "cuda_available": torch.cuda.is_available(),
        "mode": "cuda" if require_cuda else "local",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=ROOT / "environments/cuda/runtime-v1.json")
    parser.add_argument("--mode", choices=("static", "local", "cuda"), default="static")
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text())
    validate_contract(contract, ROOT, check_runtime=False)
    result: dict[str, object] = {"contract": "valid", "mode": args.mode}
    if args.mode in {"local", "cuda"}:
        result.update(validate_active_runtime(contract, require_cuda=args.mode == "cuda"))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
