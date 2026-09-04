"""Validate the final local M6 external-authority handoff packet."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from artifact_contract.distribution import validate_receipt
from artifact_contract.validator import validate_resolution_bundle

SOURCE_REVISION = "f22c799a6fc81375588f899da15468087731219d"
PACKET_SHA256 = "897a80891f785d6a519ed3e8aee61ee9269d94d139fe84e3bc2544792afefcc8"
ARCHIVE_SHA256 = "0c92aa28888754d9b6c07a6d92f45f06fae8e7564ad76482ec1aa06a385300d9"
ALLOWLIST_SHA256 = "8b473f6e4f00a1a1644edbf126647d92add6082fe6cecb2d5cdd2386d67857e7"
DESTINATION_TAG = "m6-complete-assets-v2-0c92aa28"
EXPECTED_FILES = {
    "AUTHORITY_PACKET.json",
    "EVIDENCE_BOUNDARY.txt",
    "PUBLICATION-PLAN.md",
    "REPO-OWNED-CLOSURE-AUDIT.md",
    "REQUEST-POLLEN-UNSENT.md",
    "REQUEST-REMIFABRE-WANDB-UNSENT.md",
}
EXPECTED_ACTIONS = {
    "third_party_contacted": False,
    "draft_transmitted": False,
    "github_pushed": False,
    "github_tag_created": False,
    "github_release_created": False,
    "huggingface_repository_created_or_selected": False,
    "huggingface_uploaded": False,
    "credentials_used": False,
    "policy_imported_or_parsed": False,
    "policy_executed_or_evaluated": False,
    "compute_provisioned": False,
    "hardware_action_performed": False,
}
EXPECTED_COVERED = [
    "local_read_and_audit",
    "local_file_edit_and_scoped_commit",
    "deterministic_local_validation",
    "local_byte_only_library_staging",
    "draft_creation_without_transmission",
]
EXPECTED_HUMAN_AUTHORITY = [
    "third_party_contact_or_message_transmission",
    "github_push_tag_or_release",
    "huggingface_repository_selection_or_upload",
    "credential_use_for_public_mutation",
    "policy_import_execution_evaluation_approval_or_activation",
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def _validate_manifest(directory: Path) -> None:
    actual = {path.name for path in directory.iterdir() if path.is_file()}
    if actual != EXPECTED_FILES | {"SHA256SUMS"}:
        raise AssertionError("authority packet receipt coverage drift")
    observed: set[str] = set()
    for line in (directory / "SHA256SUMS").read_text().splitlines():
        digest, relative = line.split("  ./", 1)
        if relative in observed or len(digest) != 64 or _sha256(directory / relative) != digest:
            raise AssertionError("authority packet receipt manifest drift")
        observed.add(relative)
    if observed != EXPECTED_FILES:
        raise AssertionError("authority packet manifest coverage drift")


def validate_authority_handoff(directory: Path, root: Path) -> dict[str, Any]:
    _validate_manifest(directory)
    packet_path = directory / "AUTHORITY_PACKET.json"
    if _sha256(packet_path) != PACKET_SHA256:
        raise AssertionError("authority packet byte identity drift")
    packet = json.loads(packet_path.read_text())
    if packet.get("schema_version") != "microduck.m6-external-authority-handoff/v1" or packet.get("source_revision") != SOURCE_REVISION:
        raise AssertionError("authority packet identity drift")

    source_archive = subprocess.run(
        ["git", "-C", str(root), "show", f"{SOURCE_REVISION}:receipts/m6/distribution/20260904-local-complete-assets-v2/microduck-complete-assets-v2.tar.gz"],
        check=True, capture_output=True,
    ).stdout
    if hashlib.sha256(source_archive).hexdigest() != ARCHIVE_SHA256:
        raise AssertionError("accepted distribution revision drift")
    subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", SOURCE_REVISION, "HEAD"], check=True)
    validate_receipt(
        root / "receipts/m6/distribution/20260904-local-complete-assets-v2",
        root,
        root / "artifact_contract/distribution-allowlist-v1.json",
    )

    candidates = packet.get("candidates", {})
    if set(candidates) != {"official", "community"}:
        raise AssertionError("candidate coverage drift")
    for source_class, record in candidates.items():
        resolution_path = root / record["resolution_path"]
        if "sha256:" + _sha256(resolution_path) != record["resolution_sha256"]:
            raise AssertionError(f"{source_class} resolution digest drift")
        resolution = validate_resolution_bundle(resolution_path.parent, source_class)
        if record["candidate_id"] != resolution["candidate_id"]:
            raise AssertionError(f"{source_class} candidate identity drift")
        if record["bound_roles"] != resolution["validation"]["bound_roles"]:
            raise AssertionError(f"{source_class} bound-role drift")
        missing = resolution["validation"]["missing_roles"]
        if sorted(record["missing_roles"]) != missing:
            raise AssertionError(f"{source_class} missing-role drift")
        for role in missing:
            role_record = record["missing_roles"][role]
            if role_record["blockers"] != resolution["bindings"][role]["blockers"]:
                raise AssertionError(f"{source_class} {role} blocker drift")
            evidence = role_record.get("acceptable_immutable_evidence")
            if not isinstance(evidence, list) or len(evidence) != 1 or not evidence[0]:
                raise AssertionError(f"{source_class} {role} evidence requirement missing")
        if record["manifest_status"] != "rejected_incomplete" or record["authority"] != "none":
            raise AssertionError(f"{source_class} manifest promoted")

    draft_specs = {
        "pollen": ("REQUEST-POLLEN-UNSENT.md", "d9151a6fe8d774d3883663370fdfa891c421215f13751193c96fddf3f37f6a6e"),
        "remifabre_wandb": ("REQUEST-REMIFABRE-WANDB-UNSENT.md", "0066c29a2bf5644ba89ca86c4bfecbd47b4617c6263dabeddb6d894887a24aca"),
    }
    if set(packet.get("drafts", {})) != set(draft_specs):
        raise AssertionError("request draft coverage drift")
    for key, (name, digest) in draft_specs.items():
        if packet["drafts"][key] != {"path": name, "sha256": "sha256:" + digest, "status": "unsent"}:
            raise AssertionError("request draft binding or state drift")
        text = (directory / name).read_text()
        for token in ("checkpoint", "normalizer", "export", "evaluator", "raw evaluation", "license", "immutable"):
            if token not in text.lower():
                raise AssertionError("request draft topic coverage drift")

    expected_plan = {
        "path": "PUBLICATION-PLAN.md",
        "sha256": "sha256:f2239471b76b570f8fe47020ab865ef923db6f02f1c6f0ab8a7a813ec39a6172",
        "github_repository": "https://github.com/jakekinchen/microduck-rl-genesis.git",
        "source_revision": SOURCE_REVISION,
        "expected_origin_main": "3257775beeeb8b1df646dd295bf84e34967e42ec",
        "destination_tag": DESTINATION_TAG,
        "huggingface_repository": "human_confirmation_required",
        "huggingface_revision": DESTINATION_TAG,
        "status": "preregistered_not_authorized_not_executed",
    }
    if packet.get("publication_plan") != expected_plan or _sha256(directory / "PUBLICATION-PLAN.md") != expected_plan["sha256"].removeprefix("sha256:"):
        raise AssertionError("publication plan drift or promotion")
    plan = (directory / "PUBLICATION-PLAN.md").read_text()
    for token in (SOURCE_REVISION, ARCHIVE_SHA256, DESTINATION_TAG, "explicit human authorization", "Re-download", "Stop before mutation"):
        if token not in plan:
            raise AssertionError("publication plan gate coverage drift")

    audit = packet.get("repo_owned_closure_audit")
    if audit != {
        "path": "REPO-OWNED-CLOSURE-AUDIT.md",
        "sha256": "sha256:9f5ada15a0dcdd391d30f5ba16cc5edc14bed9f20dc31a28cf54d0ebe88a843b",
        "roles_closed": [],
        "result": "none_without_origin_or_claim_boundary_change",
    } or _sha256(directory / audit["path"]) != audit["sha256"].removeprefix("sha256:"):
        raise AssertionError("repo-owned closure conclusion drift")

    boundary = packet.get("authority_boundary", {})
    if boundary.get("covered_by_existing_project_authority") != EXPECTED_COVERED or boundary.get("requires_new_explicit_human_authority") != EXPECTED_HUMAN_AUTHORITY:
        raise AssertionError("human authority boundary drift")
    if packet.get("actions") != EXPECTED_ACTIONS:
        raise AssertionError("contact/publication/action state drift")
    if packet.get("decision") != "escalate_stop_external_input_or_publication_authority_required":
        raise AssertionError("external authority stop decision drift")
    if _git(root, "remote", "get-url", "origin") != expected_plan["github_repository"]:
        raise AssertionError("publication source remote drift")
    if _git(root, "rev-parse", "origin/main") != expected_plan["expected_origin_main"]:
        raise AssertionError("preregistered remote base drift")
    if _git(root, "tag", "--list", DESTINATION_TAG):
        raise AssertionError("preregistered publication tag already exists")

    evidence_boundary = (directory / "EVIDENCE_BOUNDARY.txt").read_text()
    for token in ("were not sent", "publication plan was not executed", "No credential", "No\npolicy was imported", "Brev remains empty", "human-owned authority boundaries"):
        if token not in evidence_boundary:
            raise AssertionError("receipt evidence boundary drift")
    distribution = packet.get("accepted_distribution", {})
    if distribution != {
        "archive_path": "receipts/m6/distribution/20260904-local-complete-assets-v2/microduck-complete-assets-v2.tar.gz",
        "archive_sha256": "sha256:" + ARCHIVE_SHA256,
        "archive_size_bytes": 9272643,
        "allowlist_sha256": "sha256:" + ALLOWLIST_SHA256,
        "allowlisted_complete": 65,
        "quarantined_missing": 5,
        "lifecycle": "staged_not_imported",
    }:
        raise AssertionError("accepted local distribution binding drift")
    return packet
