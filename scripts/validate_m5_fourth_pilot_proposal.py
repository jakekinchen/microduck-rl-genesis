#!/usr/bin/env python3
"""Fail-closed validator for the non-authorizing M5 fourth-pilot proposal."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROPOSAL = ROOT / "experiments/m5/fourth-pilot-proposal-v1.json"
SCHEMA = ROOT / "experiments/m5/fourth-pilot-proposal-v1.schema.json"

EXPECTED_PROPOSAL_FILE_SHA256 = (
    "0513d276aa6ca591e5a4232ffe914a5b9107910a7366b397a77e421df3a09ec2"
)
EXPECTED_PROPOSAL_SEMANTIC_SHA256 = (
    "692f1d3d884b8e47ef485f0a9eb9974f6e25cb305965f89fe940850367281b5d"
)
EXPECTED_SCHEMA_FILE_SHA256 = (
    "3de9591c32e40d7bb24114e9e592b6241408332fdc34de6161eaea12d149d027"
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _semantic_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _git(*args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(ROOT), *args], text=True
    ).strip()


def validate_proposal(proposal: Any, *, verify_local_inputs: bool) -> None:
    _assert(isinstance(proposal, dict), "proposal must be an object")
    _assert(
        proposal.get("compute_authorized") is False,
        "compute_authorized must remain false",
    )
    _assert(
        _semantic_sha256(proposal) == EXPECTED_PROPOSAL_SEMANTIC_SHA256,
        "proposal semantic binding drift",
    )

    authority = proposal["authority"]
    _assert(authority["manager_authority_present"] is False, "Manager authority drift")
    _assert(authority["proposal_grants_compute"] is False, "proposal authority drift")
    _assert(
        proposal["execution"]["launch_allowed_in_this_proposal"] is False,
        "launch authority drift",
    )
    _assert(
        proposal["catalog_snapshot"]["proposal_evidence_only"] is True,
        "catalog evidence boundary drift",
    )

    catalog = proposal["catalog_snapshot"]
    workspace = proposal["workspace"]
    limits = proposal["limits"]
    _assert(workspace["count"] == catalog["gpu_count"] == 1, "GPU/workspace count drift")
    _assert(workspace["parallel"] == 1, "parallel workspace drift")
    _assert(workspace["fallback_allowed"] is False, "fallback became allowed")
    _assert(workspace["second_workspace_allowed"] is False, "second workspace became allowed")
    _assert(workspace["substitute_type_allowed"] is False, "substitution became allowed")
    _assert(catalog["stoppable"] is False, "stoppability drift")
    _assert(catalog["rebootable"] is False, "rebootability drift")
    _assert(
        limits["hard_cost_usd"]
        == limits["hard_elapsed_hours_create_to_delete"]
        * limits["maximum_price_per_hour_usd"],
        "cost ceiling is inconsistent with time and price",
    )
    _assert(
        limits["hard_elapsed_seconds_create_to_delete"]
        == limits["hard_elapsed_hours_create_to_delete"] * 3600,
        "elapsed ceilings disagree",
    )
    _assert(limits["harness_timeout_seconds"] < 7200, "inner timeout must be below outer ceiling")

    execution = proposal["execution"]
    _assert(
        execution["ordered_gates"]
        == [
            "authority_enabled_full_suite",
            "four_public_development_smokes",
            "normalized_onnx_retention",
        ],
        "suite/smoke/export order drift",
    )
    _assert(execution["suite"]["must_pass_before_any_smoke"] is True, "suite-first gate drift")
    _assert(execution["suite"]["authority_enabled"] is True, "suite authority drift")
    _assert(len(execution["public_development_smokes"]) == 4, "smoke count drift")
    for smoke in execution["public_development_smokes"]:
        _assert(smoke["num_envs"] == 64, "smoke environment count drift")
        _assert(smoke["max_iterations"] == 5, "smoke iteration count drift")
        _assert(smoke["normalized_onnx"].endswith(".normalized.onnx"), "ONNX retention drift")

    failure = proposal["failure_receipt"]
    teardown = proposal["teardown"]
    _assert(all(failure.values()), "failure receipt requirement disabled")
    _assert(all(teardown.values()), "teardown requirement disabled")
    _assert(len(proposal["prohibited"]) == 13, "prohibition set drift")

    if not verify_local_inputs:
        return

    _assert(_file_sha256(PROPOSAL) == EXPECTED_PROPOSAL_FILE_SHA256, "proposal byte hash drift")
    _assert(_file_sha256(SCHEMA) == EXPECTED_SCHEMA_FILE_SHA256, "proposal schema byte hash drift")
    for binding in (
        proposal["inputs"]["pilot_harness"],
        proposal["inputs"]["runtime_contract"],
        proposal["inputs"]["requirements_lock"],
    ):
        expected = binding["sha256"].removeprefix("sha256:")
        _assert(_file_sha256(ROOT / binding["path"]) == expected, f"input hash drift: {binding['path']}")

    correction = authority["accepted_correction_commit"]
    reviewer_head = authority["accepted_reviewer_head"]
    _assert(_git("rev-parse", correction) == correction, "accepted correction commit drift")
    _assert(_git("rev-parse", reviewer_head) == reviewer_head, "accepted Reviewer/HEAD drift")
    subprocess.check_call(
        ["git", "-C", str(ROOT), "merge-base", "--is-ancestor", correction, reviewer_head]
    )
    subprocess.check_call(
        ["git", "-C", str(ROOT), "merge-base", "--is-ancestor", reviewer_head, "HEAD"]
    )

    harness = (ROOT / proposal["inputs"]["pilot_harness"]["path"]).read_text()
    _assert(harness.index("run_logged full-suite") < harness.index("run_logged genesis-walking"), "harness is not suite-first")
    for required in ("--num-envs 64", "--max-iterations 5", "--env.scene.num-envs 64", "--agent.max-iterations 5"):
        _assert(required in harness, f"harness smoke binding missing: {required}")


def validate_repository() -> None:
    proposal = json.loads(PROPOSAL.read_text())
    validate_proposal(proposal, verify_local_inputs=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--proposal", type=Path, default=PROPOSAL)
    args = parser.parse_args()
    proposal = json.loads(args.proposal.read_text())
    validate_proposal(proposal, verify_local_inputs=args.proposal.resolve() == PROPOSAL.resolve())
    print("M5 fourth-pilot proposal validated: compute_authorized=false")


if __name__ == "__main__":
    main()
