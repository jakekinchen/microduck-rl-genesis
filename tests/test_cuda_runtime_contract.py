"""Fail-closed checks for the refrozen linux/amd64 CUDA runtime."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "environments/cuda/runtime-v1.json"
LOCK = ROOT / "environments/cuda/requirements.lock"
VALIDATOR = ROOT / "scripts/validate_cuda_runtime.py"


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


spec = importlib.util.spec_from_file_location("validate_cuda_runtime", VALIDATOR)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

runtime = json.loads(RUNTIME.read_text())
module.validate_contract(runtime, ROOT, check_runtime=False)
assert runtime["state"] == "local_refreeze_review_required"
assert runtime["platform"] == "linux/amd64"
assert runtime["python"] == "3.12"
assert runtime["torch_backend"] == "cu128"
assert runtime["packages"] == {
    "genesis-world": "1.3.3",
    "mujoco": "3.12.0",
    "rsl-rl-lib": "5.4.2",
    "torch": "2.9.1+cu128",
}
assert runtime["requirements_lock"]["sha256"] == sha256(LOCK)
assert runtime["genesis_upstream"]["wheel_sha256"] == (
    "sha256:74fcece3f080d2de86a25da9c26c979c192ed4a115d556133e8103169f74b3bf"
)
assert runtime["genesis_upstream"]["release_commit"] == (
    "76f8f5b3457e7c6d6a078de2244066f9a8694c45"
)
assert runtime["required_api"] == [
    "RigidSolver.dyn_state.dofs.qf_bias",
    "RigidSolver.dyn_state.dofs.qf_constraint",
]
assert runtime["headless_env"] == {"MUJOCO_GL": "egl", "PYGLET_HEADLESS": "1"}
assert runtime["compute_authorized"] is False


def rejected(mutator) -> None:
    candidate = copy.deepcopy(runtime)
    mutator(candidate)
    try:
        module.validate_contract(candidate, ROOT, check_runtime=False)
    except AssertionError:
        return
    raise AssertionError("invalid CUDA runtime mutation was accepted")


rejected(lambda value: value.__setitem__("platform", "linux/arm64"))
rejected(lambda value: value.__setitem__("torch_backend", "cpu"))
rejected(lambda value: value["packages"].__setitem__("genesis-world", "1.2.2"))
rejected(lambda value: value["genesis_upstream"].__setitem__("wheel_sha256", "sha256:" + "0" * 64))
rejected(lambda value: value["genesis_upstream"].__setitem__("source_url", "https://example.invalid"))
rejected(lambda value: value["rejected_runtime"].__setitem__("rigid_solver_sha256", "sha256:" + "0" * 64))
rejected(lambda value: value["headless_env"].__setitem__("MUJOCO_GL", "glfw"))
rejected(lambda value: value.__setitem__("compute_authorized", True))

harness = (ROOT / "scripts/run_m5_cuda_pilot.sh").read_text()
assert "environments/cuda/requirements.lock" in harness
assert "--require-hashes" in harness
assert "validate_cuda_runtime.py" in harness
assert "export MUJOCO_GL=egl" in harness
assert "trap finalize_receipt EXIT" in harness

with tempfile.TemporaryDirectory() as temp:
    temp_root = Path(temp)
    receipt = temp_root / "receipt"
    failed = subprocess.run(
        ["bash", str(ROOT / "scripts/run_m5_cuda_pilot.sh")],
        env={
            "CONTRACT_COMMIT": "local-failure-probe",
            "INPUT_ROOT": str(temp_root / "missing-input"),
            "PATH": "/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin",
            "RECEIPT_ROOT": str(receipt),
            "SOURCE_ROOT": str(temp_root / "source"),
            "VENV_ROOT": str(temp_root / "venvs"),
            "WORKSPACE_ROOT": str(temp_root / "workspace"),
        },
        capture_output=True,
        text=True,
    )
    assert failed.returncode != 0
    terminal = json.loads((receipt / "TERMINAL_STATUS.json").read_text())
    assert terminal == {
        "classification": "terminal_negative",
        "exit_code": failed.returncode,
        "failure_stage": "bootstrap",
        "pilot_smoke_pipeline_completed": False,
    }
    assert (receipt / "SHA256SUMS").is_file()
    assert (receipt / "EVIDENCE_BOUNDARY.txt").is_file()

probe_script = ROOT / "scripts/probe_genesis_runtime_wheels.py"
assert probe_script.is_file()
assert "scripts/probe_genesis_runtime_wheels.py" in json.loads(
    (ROOT / "experiments/m5/contract-v1.json").read_text()
)["bindings"]

experiment = json.loads((ROOT / "experiments/m5/contract-v1.json").read_text())
for binding in (
    "environments/cuda/requirements.lock",
    "environments/cuda/runtime-v1.json",
    "environments/cuda/runtime-v1.schema.json",
):
    assert binding in experiment["bindings"]
assert experiment["state"] == "local_runtime_refreeze_review_required"
assert experiment["resource_proposal"]["authorization"] == "proposed_second_pilot_not_authorized"

proposal = json.loads((ROOT / "experiments/m5/second-pilot-proposal-v1.json").read_text())
proposal_schema = json.loads((ROOT / "experiments/m5/second-pilot-proposal-v1.schema.json").read_text())
from experiments.m5.contract import validate_json_schema_instance

validate_json_schema_instance(proposal, proposal_schema)
assert proposal["compute_authorized"] is False
assert proposal["limits"] == {
    "hard_cost_usd": 3.24,
    "hard_elapsed_hours_create_to_delete": 2,
    "harness_timeout_seconds": 4800,
    "price_per_hour_usd": 1.62,
    "workspace_count": 1,
}
assert proposal["runtime_contract"]["requirements_lock_sha256"] == sha256(LOCK)
assert proposal["runtime_contract"]["runtime_contract_sha256"] == sha256(RUNTIME)

receipt_manifest = ROOT / "receipts/m5/pilot/20260903T2334Z-tudexszf6/SHA256SUMS"
assert hashlib.sha256(receipt_manifest.read_bytes()).hexdigest() == (
    "1e8d4948294b4a4c95a8a73c9e0a7c9ab0fcef4c354a2c11ac29f1eb4ce8566b"
)

print("CUDA runtime contract and negative drift probes verified")
