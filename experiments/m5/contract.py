"""Fail-closed validation and dry-run expansion for the M5 contract."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

REQUIRED_BINDINGS = {
    "microduck/velocity_cfg.py",
    "microduck/backflip_cfg.py",
    "microduck/velocity_env.py",
    "microduck/backflip_env.py",
    "microduck_contract/tasks/walking-v1.json",
    "microduck_contract/tasks/backflip-v1.json",
    "microduck_contract/model/microduck-walk-v1.lock.json",
    "microduck_contract/model/microduck-allcollisions-v1.lock.json",
    "microduck_contract/actuator/bam-m6-xl330-v1.lock.json",
    "microduck_contract/interface/observation-v1.json",
    "microduck_contract/interface/action-v1.json",
    "microduck_contract/interface/control-v1.json",
    "export_onnx.py",
    "environments/apple/requirements.lock",
    "validation/official-mjlab/uv.lock",
    "evaluator/config-v1.json",
    "evaluator/development-suite-v1.json",
    "evaluator/case-matrix-v1.json",
    "evaluator/heldout-protocol-v1.json",
    "evaluator/core.py",
    "evaluator/success.py",
    "microduck_contract/policies/official-walking-authority-v1.json",
}
REQUIRED_GATES = {
    "official_policy_authority_missing",
    "cuda_container_digest_missing",
    "cuda_compute_authorization_missing",
}
EXPECTED_TASKS = {"microduck.walking.v1", "microduck.backflip.v1"}
EXPECTED_BACKENDS = {"genesis-metal-mps", "official-mjlab-cuda"}


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def git_blob(repo: Path, commit: str, path: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(repo), "show", f"{commit}:{path}"],
        check=True,
        capture_output=True,
    ).stdout


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_contract(
    contract: dict[str, Any],
    root: Path,
    official_walking_repo: Path | None = None,
    official_backflip_repo: Path | None = None,
    check_external: bool = True,
) -> None:
    _assert(contract.get("schema_version") == "microduck.m5-experiment-contract/v1", "schema drift")
    _assert(contract.get("state") == "preregistered_blocked", "contract must remain blocked")
    _assert(contract.get("evidence_boundary") == "experiment_infrastructure_only", "evidence boundary promoted")
    gates = {item["id"] for item in contract.get("blocking_gates", []) if item.get("state") == "blocking"}
    _assert(gates == REQUIRED_GATES, "blocking gate drift")

    bindings = contract.get("bindings", {})
    _assert(set(bindings) == REQUIRED_BINDINGS, "bound input set is incomplete or expanded")
    for relative, expected in bindings.items():
        path = root / relative
        _assert(path.is_file(), f"missing bound input: {relative}")
        _assert(sha256_file(path) == expected, f"bound input drift: {relative}")

    authority = json.loads((root / "microduck_contract/policies/official-walking-authority-v1.json").read_text())
    _assert(authority["status"] == "official_policy_authority_missing", "official policy blocker changed without amendment")
    _assert(not authority["actions"]["official_policy_executed"], "unprovenanced official policy was executed")
    heldout = json.loads((root / "evaluator/heldout-protocol-v1.json").read_text())
    _assert(heldout["state"] == "preregistered_unrealized", "held-out protocol was realized")
    _assert(heldout["beacon"]["live_value_committed"] is False, "held-out beacon was committed early")

    repositories = contract["repositories"]
    genesis_commit = repositories["genesis"]["source_commit"]
    subprocess.run(["git", "-C", str(root), "cat-file", "-e", f"{genesis_commit}^{{commit}}"], check=True)
    _assert(repositories["bam"]["source_commit"] == "62bd8ce12154340be97e06f7f41a0ca8f116d967", "BAM authority drift")

    if check_external:
        walking_repo = official_walking_repo or root.parent / "microduck-rl"
        backflip_repo = official_backflip_repo or root.parent / "microduck-backflip"
        for name, repo in (("official_walking", walking_repo), ("official_backflip", backflip_repo)):
            spec = repositories[name]
            _assert(repo.is_dir(), f"missing external authority checkout: {name}")
            _assert(sha256_bytes(git_blob(repo, spec["source_commit"], spec["task_blob"]["path"])) == spec["task_blob"]["sha256"], f"external task drift: {name}")
            _assert(sha256_bytes(git_blob(repo, spec["source_commit"], "pyproject.toml")) == spec["environment"]["pyproject_sha256"], f"external pyproject drift: {name}")
            _assert(sha256_bytes(git_blob(repo, spec["source_commit"], "uv.lock")) == spec["environment"]["uv_lock_sha256"], f"external lock drift: {name}")

    config = contract["training_config"]
    _assert(config["actor"]["hidden_dims"] == [512, 256, 128], "actor architecture drift")
    _assert(config["critic"]["hidden_dims"] == [512, 256, 128], "critic architecture drift")
    _assert(config["rollout_steps_per_env"] == 24, "rollout length drift")
    _assert(config["checkpoint_selection"] == "predetermined_by_transition_count_only", "checkpoint selection is outcome-dependent")
    required_ppo = {"clip_param", "desired_kl", "entropy_coef", "gamma", "lam", "learning_rate", "max_grad_norm", "num_learning_epochs", "num_mini_batches", "schedule", "use_clipped_value_loss", "value_loss_coef"}
    _assert(required_ppo <= set(config["ppo"]), "PPO configuration incomplete")

    tasks = contract.get("tasks", [])
    _assert({task["task_id"] for task in tasks} == EXPECTED_TASKS, "task matrix drift")
    every_seed: list[int] = []
    for task in tasks:
        development = task["development_seeds"]
        candidate = task["candidate_comparison_seeds"]
        _assert(len(development) == 3 and len(candidate) == 5, "seed count drift")
        _assert(not set(development) & set(candidate), "development/candidate seed overlap")
        every_seed.extend(development + candidate)
        task_contract = json.loads((root / task["task_contract"]).read_text())
        public_acceptance = set(task_contract["acceptance"].get("seeds", []))
        _assert(not public_acceptance & set(development + candidate), "training seed overlaps public acceptance seed")
        backends = task["backends"]
        _assert({backend["id"] for backend in backends} == EXPECTED_BACKENDS, "backend matrix drift")
        for backend in backends:
            batch = backend["num_envs"] * backend["rollout_steps_per_env"]
            _assert(batch * backend["development_iterations"] == task["development_transition_budget"], "unequal development transition budget")
            _assert(batch * backend["candidate_iterations"] == task["candidate_transition_budget"], "unequal candidate transition budget")
        checkpoints = task["checkpoint_transitions"]
        _assert(checkpoints == sorted(set(checkpoints)), "checkpoint schedule is not unique and ordered")
        _assert(checkpoints[0] == 0 and checkpoints[-1] == task["candidate_transition_budget"], "checkpoint endpoints drift")
        _assert(len(checkpoints) == 7, "checkpoint count changed after preregistration")
        for checkpoint in checkpoints:
            _assert(all(checkpoint % (backend["num_envs"] * backend["rollout_steps_per_env"]) == 0 for backend in backends), "checkpoint is not shared by exact backend iterations")
    _assert(len(every_seed) == len(set(every_seed)), "seed overlap across tasks")

    evaluator = contract["evaluator"]
    _assert(evaluator["same_evaluator_for_all_backends"] is True, "backend-specific evaluator admitted")
    for key in ("visible_development_suite", "case_matrix", "success_classifier", "heldout_protocol"):
        _assert(evaluator[key] in bindings, f"unbound evaluator input: {key}")
    _assert(evaluator["heldout_state_required_before_candidate_freeze"] == "preregistered_unrealized", "held-out timing rule drift")
    _assert(contract["decision_rules"]["ppo_return_is_success"] is False, "PPO return promoted to success")
    _assert(contract["resource_proposal"]["authorization"] == "proposal_only_not_authorized", "resource proposal became authorization")
    _assert(contract["artifacts"]["checkpoint_export_rule"].startswith("export every predetermined checkpoint"), "late export selection admitted")


def validate_lock(root: Path) -> None:
    lock = json.loads((root / "experiments/m5/contract-v1.lock.json").read_text())
    _assert(lock.get("schema_version") == "microduck.m5-experiment-contract-lock/v1", "contract lock schema drift")
    _assert(lock.get("state") == "preregistered_blocked", "contract lock state drift")
    _assert(lock.get("candidate_or_heldout_execution_authorized") is False, "contract lock granted execution authority")
    for relative, expected in lock.get("bindings", {}).items():
        _assert(sha256_file(root / relative) == expected, f"M5 immutable artifact drift: {relative}")


def expand_matrix(contract: dict[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for task in contract["tasks"]:
        for phase, seed_key, budget_key in (
            ("development", "development_seeds", "development_transition_budget"),
            ("candidate_comparison", "candidate_comparison_seeds", "candidate_transition_budget"),
        ):
            for seed in task[seed_key]:
                for backend in task["backends"]:
                    batch = backend["num_envs"] * backend["rollout_steps_per_env"]
                    budget = task[budget_key]
                    checkpoints = [budget] if phase == "development" else task["checkpoint_transitions"]
                    rows.append({
                        "task_id": task["task_id"],
                        "phase": phase,
                        "seed": seed,
                        "backend_id": backend["id"],
                        "transition_budget": budget,
                        "iterations": budget // batch,
                        "checkpoint_transitions": checkpoints,
                        "checkpoint_iterations": [value // batch for value in checkpoints],
                        "state": "planned_not_executed",
                    })
    return {
        "schema_version": "microduck.m5-execution-matrix/v1",
        "experiment_id": contract["experiment_id"],
        "row_count": len(rows),
        "heldout_seeds_included": False,
        "resource_authorized": False,
        "rows": rows,
    }
