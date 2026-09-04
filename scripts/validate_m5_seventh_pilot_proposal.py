#!/usr/bin/env python3
"""Fail-closed validator for the non-authorizing M5 seventh-pilot proposal."""

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
PROPOSAL = ROOT / "experiments/m5/seventh-pilot-proposal-v1.json"
SCHEMA = ROOT / "experiments/m5/seventh-pilot-proposal-v1.schema.json"

EXPECTED_PROPOSAL_FILE_SHA256 = "714da8cdd4e521e1ba0d088809ff568f29ec909b514d796a2d67c0a1c0564f53"
EXPECTED_PROPOSAL_SEMANTIC_SHA256 = "604eb30d560cbb5045c551af5094dada621d23e0c92697defccccdc6532c8b4c"
EXPECTED_SCHEMA_FILE_SHA256 = "4d38202f7b97971b11af8d0e417fe0cef03ffa3a25b47d9aa1096104cfd970c7"

SELECTED_TYPE = "gpu_1x_a100_sxm4"
FAILED_TYPES = {
    "hyperstack_A100_80G",
    "massedcompute_A100_sxm4_80G_DGX",
    "a2-highgpu-1g:nvidia-tesla-a100:1",
}
UNAVAILABLE_TYPES = {"a100-80gb.1x"}


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
    for alias in ("run_m5_cuda_pilot.sh", "run_m5_cuda_pilot_5.sh", "run_m5_cuda_pilot_6.sh"):
        _assert(alias not in harness_text, f"seventh harness depends on prior alias: {alias}")


def validate_readiness_protocol(proposal: Any, harness_text: str) -> None:
    limits = proposal["limits"]
    protocol = proposal["readiness_protocol"]
    catalog = proposal["catalog_snapshot"]
    _assert(protocol["advertised_boot_time_is_estimate_only"] is True, "boot estimate became readiness proof")
    _assert(protocol["advertised_boot_time_seconds"] == catalog["boot_time_seconds"] == 600, "advertised boot binding drift")
    _assert(protocol["advertised_boot_time_expiry_is_not_terminal"] is True, "boot estimate became terminal deadline")
    _assert(limits["shell_readiness_window_seconds_create_to_probe_success"] == 900, "shell-readiness window drift")
    _assert(protocol["window_starts_at_create_request"] is True, "readiness clock anchor drift")
    _assert(protocol["window_closes_only_after_shell_and_disk_probe_success"] is True, "readiness closure drift")
    _assert(protocol["authenticated_inventory_required"] is True, "authenticated polling disabled")
    _assert(protocol["exact_workspace_id_required"] is True, "exact-ID polling disabled")
    _assert(protocol["required_consecutive_polls"] == limits["readiness_consecutive_poll_count"] == 3, "consecutive-poll count drift")
    _assert(protocol["minimum_seconds_between_qualifying_polls"] == limits["readiness_poll_interval_seconds_minimum"] == 15, "poll interval drift")
    _assert(protocol["qualifying_status"] == {
        "status": "RUNNING",
        "build_status": "COMPLETED",
        "shell_status": "READY",
        "health_status": "HEALTHY",
    }, "qualifying status drift")
    _assert(protocol["regression_resets_consecutive_count"] is True, "readiness regression reset disabled")
    _assert(protocol["noop_shell_probe"]["command"] == "true", "no-op shell probe drift")
    _assert(protocol["noop_shell_probe"]["must_succeed_before_disk_probe"] is True, "shell-before-disk gate disabled")
    _assert(protocol["noop_shell_probe"]["retain_output"] is True, "no-op shell output retention disabled")
    _assert(protocol["disk_probe"]["minimum_free_disk_gib"] == 8, "disk threshold drift")
    _assert(protocol["disk_probe"]["must_succeed_before_upload"] is True, "disk-before-upload gate disabled")
    _assert(protocol["disk_probe"]["retain_output"] is True, "disk output retention disabled")
    _assert(protocol["terminal_on_900_second_window_expiry"] is True, "readiness timeout terminal gate disabled")
    _assert(protocol["post_terminal_ready_must_not_reopen_execution"] is True, "post-terminal execution reopening allowed")
    _assert(protocol["upload_before_all_gates_prohibited"] is True, "early upload became allowed")
    _assert("MINIMUM_FREE_DISK_GB=8" in harness_text, "harness disk threshold drift")
    _assert(harness_text.index("run_logged host-disk-preflight") < harness_text.index("run_logged apt-bootstrap"), "harness disk gate must precede install")


def validate_proposal(proposal: Any, *, verify_local_inputs: bool) -> None:
    _assert(isinstance(proposal, dict), "proposal must be an object")
    _assert(proposal.get("compute_authorized") is False, "compute_authorized must remain false")
    _assert(_semantic_sha256(proposal) == EXPECTED_PROPOSAL_SEMANTIC_SHA256, "proposal semantic binding drift")

    authority = proposal["authority"]
    _assert(authority["manager_authority_present"] is False, "Manager authority drift")
    _assert(authority["proposal_grants_compute"] is False, "proposal authority drift")
    _assert(proposal["execution"]["launch_allowed_in_this_proposal"] is False, "launch authority drift")
    _assert(proposal["catalog_snapshot"]["proposal_evidence_only"] is True, "catalog evidence boundary drift")

    sixth = proposal["sixth_pilot_terminal_boundary"]
    _assert(sixth["classification"] == "terminal_negative", "sixth-pilot classification drift")
    _assert(sixth["failure_stage"] == "workspace-provisioning-connectivity", "sixth-pilot failure-stage drift")
    _assert(sixth["retry_allowed"] is False, "sixth-pilot retry became allowed")
    _assert(sixth["usable_shell_before_terminal"] is False, "sixth-pilot shell claim drift")
    _assert(sixth["belated_ready_after_terminal_and_delete_request"] is True, "late-ready boundary drift")
    _assert(sixth["uploaded_files"] == 0, "sixth-pilot upload count drift")
    _assert(sixth["harness_invocations"] == 0, "sixth-pilot harness count drift")

    diagnosis = proposal["readiness_diagnosis"]
    _assert(len(diagnosis["retained_timelines"]) == 3, "readiness timeline count drift")
    _assert([item["pilot"] for item in diagnosis["retained_timelines"]] == [4, 5, 6], "readiness timeline order drift")
    _assert(diagnosis["feedback"]["sent"] is True, "Brev feedback not recorded as sent")
    _assert(diagnosis["feedback"]["secrets_included"] is False, "feedback secret boundary drift")
    _assert("Brev create readiness is not sufficient" in diagnosis["diagnosis"], "readiness diagnosis drift")

    catalog = proposal["catalog_snapshot"]
    dry_run = proposal["container_dry_run"]
    workspace = proposal["workspace"]
    limits = proposal["limits"]
    _assert(catalog["type"] == dry_run["selected_type"] == SELECTED_TYPE, "catalog/dry-run type drift")
    _assert(catalog["type"] not in FAILED_TYPES, "prior failed exact type selected")
    _assert(catalog["previously_used_exact_type"] is False, "selected type is marked previously used")
    _assert(catalog["provider"] == catalog["cloud"] == "lambda-labs", "direct-provider selection drift")
    _assert(catalog["arch"] == "x86_64", "architecture drift")
    _assert(catalog["gpu_name"] == "A100" and catalog["gpu_count"] == 1, "single-A100 boundary drift")
    _assert(catalog["vram_per_gpu_gb"] == catalog["total_vram_gb"] == 40, "VRAM binding drift")
    _assert(catalog["target_disk_gb"] == catalog["disk_min_gb"] == catalog["disk_max_gb"] == 512, "fixed disk binding drift")
    _assert(catalog["practical_fixed_disk"] is True, "practical disk classification drift")
    _assert(catalog["currently_exposed"] is True, "current catalog exposure drift")
    _assert(catalog["stoppable"] is False, "stoppability drift")
    _assert(catalog["rebootable"] is True, "rebootability drift")
    _assert(catalog["flex_ports"] is False, "flexible-port drift")
    _assert(dry_run["container_mode_and_digest_accepted"] is True, "container dry-run gate drift")
    _assert(dry_run["created_workspace"] is False, "dry run claims workspace creation")
    _assert(workspace["count"] == catalog["gpu_count"] == 1, "GPU/workspace count drift")
    _assert(workspace["parallel"] == 1, "parallel workspace drift")
    _assert(workspace["fallback_allowed"] is False, "fallback became allowed")
    _assert(workspace["retry_allowed"] is False, "seventh-pilot retry became allowed")
    _assert(workspace["second_workspace_allowed"] is False, "second workspace became allowed")
    _assert(workspace["substitute_type_allowed"] is False, "substitution became allowed")

    exact_price = Decimal(str(limits["exact_price_per_hour_usd"]))
    hard_hours = Decimal(str(limits["hard_elapsed_hours_create_to_delete"]))
    hard_cost = Decimal(str(limits["hard_cost_usd"]))
    _assert(exact_price == Decimal("2.388"), "exact catalog rate drift")
    _assert(hard_cost == hard_hours * exact_price == Decimal("4.776"), "cost ceiling drift")
    _assert(Decimal(str(catalog["price_per_hour_usd"])) == exact_price, "catalog/limit rate drift")
    _assert(limits["hard_elapsed_seconds_create_to_delete"] == int(hard_hours * 3600), "elapsed ceilings disagree")
    _assert(limits["shell_readiness_window_seconds_create_to_probe_success"] < limits["harness_timeout_seconds"] < limits["hard_elapsed_seconds_create_to_delete"], "nested time ceilings disagree")
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

    _assert(all(proposal["failure_receipt"].values()), "failure receipt requirement disabled")
    teardown = proposal["teardown"]
    for key in (
        "delete_exact_workspace_id_only",
        "delete_after_verified_recovery_on_success_or_failure",
        "authenticated_empty_inventory_required",
        "cleanup_requires_no_additional_confirmation",
        "reboot_is_available_but_exact_id_delete_remains_required",
    ):
        _assert(teardown[key] is True, f"teardown requirement disabled: {key}")
    _assert(teardown["workspace_is_non_stoppable"] is True, "non-stoppable workspace classification drift")
    _assert(len(proposal["prohibited"]) == 18, "prohibition set drift")
    for item in (
        "hyperstack_A100_80G_retry",
        "massedcompute_A100_sxm4_80G_DGX_retry",
        "a2-highgpu-1g:nvidia-tesla-a100:1_retry",
        "a100-80gb.1x_unavailable_substitution",
        "seventh_pilot_retry",
    ):
        _assert(item in proposal["prohibited"], f"retry prohibition missing: {item}")

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

    receipt_manifest = ROOT / sixth["receipt"] / "SHA256SUMS"
    _assert(_file_sha256(receipt_manifest) == sixth["receipt_manifest_sha256"].removeprefix("sha256:"), "sixth-pilot receipt manifest drift")

    chain = [
        authority["accepted_correction_commit"],
        authority["accepted_evaluator_reviewer_head"],
        authority["accepted_sixth_proposal_review_commit"],
        authority["consumed_sixth_manager_authorization_commit"],
        authority["accepted_sixth_terminal_executor_commit"],
        authority["accepted_sixth_terminal_reviewer_head"],
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
    for unavailable_type in UNAVAILABLE_TYPES:
        _assert(f"--type {unavailable_type}" not in command, f"dry run selects unavailable type: {unavailable_type}")

    harness = (ROOT / proposal["inputs"]["pilot_harness"]["path"]).read_text()
    validate_harness_price(proposal, harness)
    validate_harness_self_attestation(proposal, harness)
    validate_readiness_protocol(proposal, harness)
    _assert(harness.index("run_logged full-suite") < harness.index("run_logged genesis-walking"), "harness is not suite-first")


def validate_repository() -> None:
    validate_proposal(json.loads(PROPOSAL.read_text()), verify_local_inputs=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--proposal", type=Path, default=PROPOSAL)
    args = parser.parse_args()
    proposal = json.loads(args.proposal.read_text())
    validate_proposal(proposal, verify_local_inputs=args.proposal.resolve() == PROPOSAL.resolve())
    print("M5 seventh-pilot proposal validated: compute_authorized=false")


if __name__ == "__main__":
    main()
