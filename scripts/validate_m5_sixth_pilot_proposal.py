#!/usr/bin/env python3
"""Fail-closed validator for the non-authorizing M5 sixth-pilot proposal."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROPOSAL = ROOT / "experiments/m5/sixth-pilot-proposal-v1.json"
SCHEMA = ROOT / "experiments/m5/sixth-pilot-proposal-v1.schema.json"

EXPECTED_PROPOSAL_FILE_SHA256 = "3c6fee263bcffff8c93fc49448e68bab6fc5ac204317df61d8c799328ce03579"
EXPECTED_PROPOSAL_SEMANTIC_SHA256 = "ef5cdaf97fad2b41474c69d3c28c913a5c8c736f167c3a891fc69bc3d5d3a21c"
EXPECTED_SCHEMA_FILE_SHA256 = "4c25f28d4df35a7e4707fde3370ba1e04d485df9b24e861b3bcbf45175c9a059"

SELECTED_TYPE = "a2-highgpu-1g:nvidia-tesla-a100:1"
FAILED_TYPES = {
    "hyperstack_A100_80G",
    "massedcompute_A100_sxm4_80G_DGX",
}


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _semantic_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def _git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()


def validate_harness_price(proposal: Any, harness_text: str) -> None:
    matches = re.findall(r"^PRICE_USD_PER_HOUR=([0-9]+(?:\.[0-9]+)?)$", harness_text, re.MULTILINE)
    _assert(len(matches) == 1, "pilot harness must bind exactly one numeric hourly price")
    harness_price = Decimal(matches[0])
    catalog_price = Decimal(str(proposal["catalog_snapshot"]["price_per_hour_usd"]))
    limit_price = Decimal(str(proposal["limits"]["exact_price_per_hour_usd"]))
    _assert(harness_price == catalog_price, "pilot harness price/catalog rate disagreement")
    _assert(harness_price == limit_price, "pilot harness price/limit rate disagreement")


def validate_harness_self_attestation(proposal: Any, harness_text: str) -> None:
    harness_name = Path(proposal["inputs"]["pilot_harness"]["path"]).name
    required = (
        f'test -s "$INPUT_ROOT/{harness_name}"',
        f'cp "$INPUT_ROOT/{harness_name}" "$RECEIPT_ROOT/{harness_name}"',
        f'sha256sum "$RECEIPT_ROOT/{harness_name}" > "$RECEIPT_ROOT/harness-sha256.txt"',
    )
    for statement in required:
        _assert(harness_text.count(statement) == 1, f"pilot harness self-attestation drift: {statement}")
    for alias in ("run_m5_cuda_pilot.sh", "run_m5_cuda_pilot_5.sh"):
        _assert(alias not in harness_text, f"sixth harness depends on prior alias: {alias}")


def validate_disk_preflight(proposal: Any, harness_text: str) -> None:
    disk = proposal["disk_preflight"]
    _assert(disk["catalog_target_disk_gb"] == proposal["catalog_snapshot"]["target_disk_gb"] == 10, "catalog disk binding drift")
    _assert(disk["capacity_risk_acknowledged"] is True, "disk capacity risk must stay explicit")
    _assert(disk["minimum_free_disk_gb_before_upload"] == 8, "disk preflight threshold drift")
    _assert(disk["repeat_in_harness_before_install"] is True, "in-harness disk preflight disabled")
    _assert(disk["abort_before_upload_if_below_minimum"] is True, "pre-upload disk abort disabled")
    _assert(disk["no_disk_size_assumption"] is True, "disk size assumption introduced")
    _assert("MINIMUM_FREE_DISK_GB=8" in harness_text, "harness disk threshold drift")
    _assert(harness_text.index("run_logged host-disk-preflight") < harness_text.index("run_logged apt-bootstrap"), "disk gate must precede install")


def validate_proposal(proposal: Any, *, verify_local_inputs: bool) -> None:
    _assert(isinstance(proposal, dict), "proposal must be an object")
    _assert(proposal.get("compute_authorized") is False, "compute_authorized must remain false")
    _assert(_semantic_sha256(proposal) == EXPECTED_PROPOSAL_SEMANTIC_SHA256, "proposal semantic binding drift")

    authority = proposal["authority"]
    _assert(authority["manager_authority_present"] is False, "Manager authority drift")
    _assert(authority["proposal_grants_compute"] is False, "proposal authority drift")
    _assert(proposal["execution"]["launch_allowed_in_this_proposal"] is False, "launch authority drift")
    _assert(proposal["catalog_snapshot"]["proposal_evidence_only"] is True, "catalog evidence boundary drift")

    fifth = proposal["fifth_pilot_terminal_boundary"]
    _assert(fifth["classification"] == "terminal_negative", "fifth-pilot classification drift")
    _assert(fifth["failure_stage"] == "workspace-provisioning-connectivity", "fifth-pilot failure stage drift")
    _assert(fifth["retry_allowed"] is False, "fifth-pilot retry became allowed")
    _assert(fifth["shell_reached"] is False, "fifth-pilot shell claim drift")
    _assert(fifth["uploaded_files"] == 0, "fifth-pilot upload count drift")
    _assert(fifth["harness_invocations"] == 0, "fifth-pilot execution drift")

    catalog = proposal["catalog_snapshot"]
    dry_run = proposal["container_dry_run"]
    workspace = proposal["workspace"]
    limits = proposal["limits"]
    _assert(catalog["type"] == dry_run["selected_type"] == SELECTED_TYPE, "catalog/dry-run type drift")
    _assert(catalog["type"] not in FAILED_TYPES, "prior failed exact type selected")
    _assert(catalog["provider"] == catalog["cloud"] == "gcp", "direct-provider selection drift")
    _assert(catalog["arch"] == "x86_64", "architecture drift")
    _assert(catalog["gpu_name"] == "A100", "GPU class drift")
    _assert(catalog["gpu_count"] == 1, "single-GPU boundary drift")
    _assert(catalog["vram_per_gpu_gb"] == catalog["total_vram_gb"] == 40, "VRAM binding drift")
    _assert(catalog["flex_ports"] is True, "flexible-port indicator drift")
    _assert(catalog["stoppable"] is True, "stoppability indicator drift")
    _assert(catalog["rebootable"] is False, "rebootability drift")
    _assert(catalog["connectivity_recovery_indicators_better_than_failed_types"] is True, "selection rationale drift")
    _assert(catalog["shell_readiness_proven"] is False, "catalog must not claim proven shell readiness")
    _assert(catalog["boot_time_seconds"] == 420, "advertised boot-time binding drift")
    _assert(dry_run["container_mode_and_digest_accepted"] is True, "container dry-run gate drift")
    _assert(dry_run["created_workspace"] is False, "dry run claims workspace creation")
    _assert(workspace["count"] == catalog["gpu_count"] == 1, "GPU/workspace count drift")
    _assert(workspace["parallel"] == 1, "parallel workspace drift")
    _assert(workspace["fallback_allowed"] is False, "fallback became allowed")
    _assert(workspace["second_workspace_allowed"] is False, "second workspace became allowed")
    _assert(workspace["substitute_type_allowed"] is False, "substitution became allowed")

    exact_price = Decimal(str(limits["exact_price_per_hour_usd"]))
    hard_hours = Decimal(str(limits["hard_elapsed_hours_create_to_delete"]))
    hard_cost = Decimal(str(limits["hard_cost_usd"]))
    _assert(exact_price == Decimal("4.408062"), "exact catalog rate drift")
    _assert(hard_cost == hard_hours * exact_price == Decimal("8.816124"), "cost ceiling drift")
    _assert(Decimal(str(catalog["price_per_hour_usd"])) == exact_price, "catalog/limit rate drift")
    _assert(limits["hard_elapsed_seconds_create_to_delete"] == int(hard_hours * 3600), "elapsed ceilings disagree")
    _assert(limits["harness_timeout_seconds"] < limits["hard_elapsed_seconds_create_to_delete"], "inner timeout must be below outer ceiling")
    _assert(limits["total_program_envelope_usd"] == 210, "total program envelope drift")
    _assert(limits["proposal_ceiling_within_total_envelope"] is True, "program envelope check disabled")
    _assert(hard_cost <= Decimal(str(limits["total_program_envelope_usd"])), "pilot ceiling exceeds program envelope")

    execution = proposal["execution"]
    _assert(execution["ordered_gates"] == ["authority_enabled_full_suite", "four_public_development_smokes", "normalized_onnx_retention"], "suite/smoke/export order drift")
    _assert(execution["suite"]["must_pass_before_any_smoke"] is True, "suite-first gate drift")
    _assert(execution["suite"]["authority_enabled"] is True, "suite authority drift")
    _assert(len(execution["public_development_smokes"]) == 4, "smoke count drift")
    for smoke in execution["public_development_smokes"]:
        _assert(smoke["num_envs"] == 64, "smoke environment count drift")
        _assert(smoke["max_iterations"] == 5, "smoke iteration count drift")
        _assert(smoke["normalized_onnx"].endswith(".normalized.onnx"), "ONNX retention drift")

    receipt = proposal["failure_receipt"]
    _assert(all(receipt.values()), "failure receipt requirement disabled")
    teardown = proposal["teardown"]
    for key in (
        "delete_exact_workspace_id_only",
        "delete_after_verified_recovery_on_success_or_failure",
        "authenticated_empty_inventory_required",
        "cleanup_requires_no_additional_confirmation",
        "stop_is_available_but_exact_id_delete_remains_required",
    ):
        _assert(teardown[key] is True, f"teardown requirement disabled: {key}")
    _assert(teardown["workspace_is_non_stoppable"] is False, "stoppable workspace classification drift")
    _assert(len(proposal["prohibited"]) == 15, "prohibition set drift")
    _assert("hyperstack_A100_80G_retry" in proposal["prohibited"], "first failed type retry prohibition missing")
    _assert("massedcompute_A100_sxm4_80G_DGX_retry" in proposal["prohibited"], "second failed type retry prohibition missing")

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

    receipt_manifest = ROOT / fifth["receipt"] / "SHA256SUMS"
    _assert(_file_sha256(receipt_manifest) == fifth["receipt_manifest_sha256"].removeprefix("sha256:"), "fifth-pilot receipt manifest drift")

    chain = [
        authority["accepted_correction_commit"],
        authority["accepted_evaluator_reviewer_head"],
        authority["accepted_fifth_proposal_review_commit"],
        authority["consumed_fifth_manager_authorization_commit"],
        authority["accepted_fifth_terminal_executor_commit"],
        authority["accepted_fifth_terminal_reviewer_head"],
    ]
    for commit in chain:
        _assert(_git("rev-parse", commit) == commit, f"commit binding drift: {commit}")
    for parent, child in zip(chain, chain[1:]):
        subprocess.check_call(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", parent, child])
    subprocess.check_call(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", chain[-1], "HEAD"])

    command = dry_run["command"]
    for required in (
        f"--type {SELECTED_TYPE}",
        "--count 1",
        "--parallel 1",
        "--mode container",
        proposal["container"]["immutable_reference"],
        "--dry-run",
    ):
        _assert(required in command, f"dry-run command binding missing: {required}")
    for failed_type in FAILED_TYPES:
        _assert(f"--type {failed_type}" not in command, f"dry run retries failed type: {failed_type}")

    harness = (ROOT / proposal["inputs"]["pilot_harness"]["path"]).read_text()
    validate_harness_price(proposal, harness)
    validate_harness_self_attestation(proposal, harness)
    validate_disk_preflight(proposal, harness)
    _assert(harness.index("run_logged full-suite") < harness.index("run_logged genesis-walking"), "harness is not suite-first")


def validate_repository() -> None:
    validate_proposal(json.loads(PROPOSAL.read_text()), verify_local_inputs=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--proposal", type=Path, default=PROPOSAL)
    args = parser.parse_args()
    proposal = json.loads(args.proposal.read_text())
    validate_proposal(proposal, verify_local_inputs=args.proposal.resolve() == PROPOSAL.resolve())
    print("M5 sixth-pilot proposal validated: compute_authorized=false")


if __name__ == "__main__":
    main()
