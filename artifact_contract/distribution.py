"""Deterministic, provenance-gated local distribution bundle support."""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import subprocess
import tarfile
from pathlib import Path, PurePosixPath
from typing import Any

from artifact_contract.provenance import validate_inventory

SOURCE_REVISION = "c9a610b8005287dc83130660719af94f80274f67"
CORRECTION_BASE = "68b0094f70a57fa0c79a71319d1ebe6ad42fff5e"
INVENTORY_PATH = "artifact_contract/file-provenance-v1.json"
BUNDLE_PREFIX = "microduck-complete-assets-v1"
ALLOWLIST_MEMBER = f"{BUNDLE_PREFIX}/metadata/distribution-allowlist-v1.json"
INVENTORY_MEMBER = f"{BUNDLE_PREFIX}/metadata/file-provenance-v1.json"
REQUIRED_ROLES = [
    "normalized_onnx",
    "normalizer",
    "source_checkpoint",
    "exporter",
    "model",
    "bam",
    "task",
    "evaluator",
    "evidence",
    "license",
]
LIFECYCLE = {
    "retrieval": "local_exact_revision_only",
    "validation": "byte_only",
    "library_stage": "permitted_after_validation",
    "library_import": "not_performed",
    "evaluation": "not_performed",
    "approval": "not_requested",
    "activation": "not_authorized",
    "publication": "not_performed",
}
SUPPORT_PATHS = ["LICENSE", "microduck/assets/LICENSE-ASSETS.md"]


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _canonical(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def _git(root: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True
    ).stdout


def _included_record(item: dict[str, Any]) -> dict[str, Any]:
    record = {
        "path": item["path"],
        "artifact_class": item["artifact_class"],
        "size_bytes": item["size_bytes"],
        "sha256": item["sha256"],
        "declared_license": item["declared_license"],
        "license_evidence": item["license_evidence"],
        "source": item["source"],
    }
    if "source_history" in item:
        record["source_history"] = item["source_history"]
    return record


def _quarantined_record(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": item["path"],
        "artifact_class": item["artifact_class"],
        "size_bytes": item["size_bytes"],
        "sha256": item["sha256"],
        "provenance_status": item["provenance_status"],
        "declared_license": item["declared_license"],
        "blockers": item["blockers"],
        "disposition": "retained_in_repository_excluded_from_distribution",
    }


def build_allowlist(root: Path, inventory: dict[str, Any]) -> dict[str, Any]:
    validate_inventory(inventory, root)
    included = sorted(
        (_included_record(item) for item in inventory["files"] if item["provenance_status"] == "complete"),
        key=lambda item: item["path"],
    )
    quarantined = sorted(
        (_quarantined_record(item) for item in inventory["files"] if item["provenance_status"] != "complete"),
        key=lambda item: item["path"],
    )
    for item in included:
        if (
            item["declared_license"] == "unresolved"
            or item["license_evidence"] is None
            or item["source"] is None
            or item["source"].get("byte_identical") is not True
            or item["source"].get("sha256") != item["sha256"]
        ):
            raise AssertionError(f"complete entry lacks distribution authority: {item['path']}")
    if len(included) != 65 or len(quarantined) != 5:
        raise AssertionError("accepted inventory distribution counts drift")
    support = []
    for relative in SUPPORT_PATHS:
        data = (root / relative).read_bytes()
        support.append({"path": relative, "size_bytes": len(data), "sha256": _sha256(data)})
    open_requirement = {
        "required_roles": REQUIRED_ROLES,
        "status": "open_no_complete_policy_manifest",
        "artifact_acceptance": "none",
    }
    return {
        "schema_version": "microduck.provenance-distribution-allowlist/v1",
        "source_revision": SOURCE_REVISION,
        "inventory": {
            "path": INVENTORY_PATH,
            "sha256": _sha256((root / INVENTORY_PATH).read_bytes()),
            "summary": inventory["summary"],
        },
        "lifecycle": LIFECYCLE,
        "proof_class": "local_distribution_staging_only",
        "policy_manifest_requirements": {
            "official": open_requirement,
            "community": open_requirement,
        },
        "allowlisted_files": included,
        "quarantined_files": quarantined,
        "support_files": support,
        "bundle": {
            "format": "deterministic_tar_gzip",
            "root_prefix": BUNDLE_PREFIX,
            "allowlist_member": ALLOWLIST_MEMBER,
            "inventory_member": INVENTORY_MEMBER,
        },
        "authority": {
            "publication": "not_authorized",
            "policy_import": "not_authorized",
            "policy_execution": "not_authorized",
            "policy_approval": "not_authorized",
            "policy_activation": "not_authorized",
        },
    }


def validate_allowlist(root: Path, allowlist: dict[str, Any]) -> dict[str, Any]:
    inventory_bytes = (root / INVENTORY_PATH).read_bytes()
    inventory = json.loads(inventory_bytes)
    expected = build_allowlist(root, inventory)
    if allowlist != expected:
        raise AssertionError("distribution allowlist drift")
    source_inventory = _git(root, "show", f"{SOURCE_REVISION}:{INVENTORY_PATH}")
    if _sha256(source_inventory) != allowlist["inventory"]["sha256"]:
        raise AssertionError("source revision inventory drift")
    subprocess.run(
        ["git", "-C", str(root), "merge-base", "--is-ancestor", SOURCE_REVISION, "HEAD"],
        check=True,
        capture_output=True,
    )
    return inventory


def _payloads(root: Path, allowlist: dict[str, Any], allowlist_bytes: bytes) -> list[tuple[str, bytes]]:
    payloads = [
        (ALLOWLIST_MEMBER, allowlist_bytes),
        (INVENTORY_MEMBER, (root / INVENTORY_PATH).read_bytes()),
    ]
    records = [*allowlist["support_files"], *allowlist["allowlisted_files"]]
    for record in records:
        payloads.append((f"{BUNDLE_PREFIX}/{record['path']}", (root / record["path"]).read_bytes()))
    return payloads


def build_bundle(root: Path, allowlist_path: Path, output: Path) -> dict[str, Any]:
    allowlist_bytes = allowlist_path.read_bytes()
    allowlist = json.loads(allowlist_bytes)
    validate_allowlist(root, allowlist)
    if allowlist_bytes != _canonical(allowlist):
        raise AssertionError("allowlist is not canonical JSON")
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.USTAR_FORMAT) as archive:
        for name, data in _payloads(root, allowlist, allowlist_bytes):
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mode = 0o644
            info.mtime = 0
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            archive.addfile(info, io.BytesIO(data))
    compressed = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", compresslevel=9, fileobj=compressed, mtime=0) as stream:
        stream.write(raw.getvalue())
    bundle = compressed.getvalue()
    if bundle[:10] != bytes.fromhex("1f8b08000000000002ff"):
        raise AssertionError("portable gzip header drift")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(bundle)
    return {"sha256": _sha256(bundle), "size_bytes": len(bundle)}


def validate_bundle(root: Path, allowlist_path: Path, bundle_path: Path, stage: Path | None = None) -> dict[str, Any]:
    allowlist_bytes = allowlist_path.read_bytes()
    allowlist = json.loads(allowlist_bytes)
    validate_allowlist(root, allowlist)
    expected_payloads = _payloads(root, allowlist, allowlist_bytes)
    with tarfile.open(bundle_path, mode="r:gz") as archive:
        members = archive.getmembers()
        if [member.name for member in members] != [name for name, _ in expected_payloads]:
            raise AssertionError("bundle member coverage or ordering drift")
        observed: list[tuple[str, bytes]] = []
        for member in members:
            path = PurePosixPath(member.name)
            if not member.isfile() or path.is_absolute() or ".." in path.parts:
                raise AssertionError("unsafe bundle member")
            if (member.mode, member.mtime, member.uid, member.gid, member.uname, member.gname) != (0o644, 0, 0, 0, "", ""):
                raise AssertionError("bundle metadata drift")
            handle = archive.extractfile(member)
            if handle is None:
                raise AssertionError("bundle member unreadable")
            observed.append((member.name, handle.read()))
    if observed != expected_payloads:
        raise AssertionError("bundle payload drift")

    bundle = bundle_path.read_bytes()
    result = {
        "sha256": _sha256(bundle),
        "size_bytes": len(bundle),
        "allowlisted_file_count": 65,
        "quarantined_file_count": 5,
        "lifecycle": {
            "retrieval": "exact_local_revision_and_digest_verified",
            "validation": "byte_only_complete",
            "library_stage": "not_requested" if stage is None else "staged_not_imported",
            "library_import": "not_performed",
            "evaluation": "not_performed",
            "approval": "not_requested",
            "activation": "not_authorized",
            "publication": "not_performed",
        },
    }
    if stage is not None:
        if stage.exists() and any(stage.iterdir()):
            raise AssertionError("library stage must be absent or empty")
        stage.mkdir(parents=True, exist_ok=True)
        for name, data in observed:
            relative = PurePosixPath(name).relative_to(BUNDLE_PREFIX)
            destination = stage.joinpath(*relative.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
        marker = {"schema_version": "microduck.library-stage/v1", **result}
        (stage / "LIBRARY-STAGE.json").write_bytes(_canonical(marker))
    return result


def _validate_receipt_manifest(directory: Path, bundle_name: str) -> None:
    expected_names = {"EVIDENCE_BOUNDARY.txt", "SEARCH_RESULT.json", bundle_name}
    actual_names = {path.name for path in directory.iterdir() if path.is_file()}
    if actual_names != expected_names | {"SHA256SUMS"}:
        raise AssertionError("receipt file coverage drift")
    manifest_lines = (directory / "SHA256SUMS").read_text().splitlines()
    observed_names: set[str] = set()
    for line in manifest_lines:
        digest, relative = line.split("  ./", 1)
        if relative in observed_names or len(digest) != 64:
            raise AssertionError("receipt manifest duplicate or malformed entry")
        observed_names.add(relative)
        if hashlib.sha256((directory / relative).read_bytes()).hexdigest() != digest:
            raise AssertionError(f"receipt payload digest drift: {relative}")
    if observed_names != expected_names:
        raise AssertionError("receipt manifest coverage drift")


def _expected_receipt_result(
    allowlist_path: Path,
    bundle_path: Path,
    bundle: dict[str, Any],
    schema_version: str,
    portable: bool,
) -> dict[str, Any]:
    result = {
        "schema_version": schema_version,
        "source_revision": SOURCE_REVISION,
        "allowlist": {"path": "artifact_contract/distribution-allowlist-v1.json", "sha256": _sha256(allowlist_path.read_bytes())},
        "bundle": {"path": bundle_path.name, "sha256": bundle["sha256"], "size_bytes": bundle["size_bytes"], "format": "deterministic_tar_gzip"},
        "inventory": {
            "total_files": 70, "allowlisted_complete": 65,
            "quarantined_partial": 0, "quarantined_missing": 5,
            "fully_resolved": False,
        },
        "verification": {
            "retrieval": "exact_local_revision_and_digest_verified",
            "validation": "byte_only_complete",
            "library_stage": "staged_not_imported",
            "official_policy_manifest": "open_no_complete_policy_manifest",
            "community_policy_manifest": "open_no_complete_policy_manifest",
        },
        "actions": {
            "policy_imported_or_parsed": False, "policy_loaded": False,
            "policy_executed": False, "evaluation_performed": False,
            "approval_requested": False, "activation_authorized": False,
            "publication_performed": False, "credentials_used": False,
            "compute_provisioned": False, "hardware_action_performed": False,
        },
        "result": "local_complete_asset_bundle_staged_publication_not_authorized",
    }
    if portable:
        result.update({
            "correction_base": CORRECTION_BASE,
            "supersedes_receipt": "receipts/m6/distribution/20260904-local-complete-assets-v1",
            "deterministic_encoding": {
                "gzip_header_hex": "1f8b08000000000002ff",
                "gzip_mtime": 0,
                "gzip_os_byte": 255,
                "tar_format": "ustar",
            },
        })
    return result


def _validate_receipt(
    directory: Path,
    root: Path,
    allowlist_path: Path,
    bundle_name: str,
    schema_version: str,
    portable: bool,
    stage: Path | None,
) -> dict[str, Any]:
    _validate_receipt_manifest(directory, bundle_name)

    bundle_path = directory / bundle_name
    bundle = validate_bundle(root, allowlist_path, bundle_path)
    allowlist = json.loads(allowlist_path.read_text())
    expected_result = _expected_receipt_result(allowlist_path, bundle_path, bundle, schema_version, portable)
    if json.loads((directory / "SEARCH_RESULT.json").read_text()) != expected_result:
        raise AssertionError("distribution receipt result drift")
    boundary = (directory / "EVIDENCE_BOUNDARY.txt").read_text()
    for statement in (
        "65 complete provenance records only",
        "quarantined from this bundle",
        "No policy was imported",
        "No\ncredential, hardware, remote publication, or compute action occurred",
        "official and community ten-role policy-manifest requirements remain open",
    ):
        if statement not in boundary:
            raise AssertionError("distribution evidence boundary drift")
    if len(allowlist["allowlisted_files"]) != 65 or len(allowlist["quarantined_files"]) != 5:
        raise AssertionError("distribution result count drift")
    if stage is not None:
        return validate_bundle(root, allowlist_path, bundle_path, stage)
    return expected_result


def validate_legacy_receipt(directory: Path, root: Path, allowlist_path: Path) -> dict[str, Any]:
    return _validate_receipt(
        directory, root, allowlist_path,
        "microduck-complete-assets-v1.tar.gz",
        "microduck.m6-local-distribution-result/v1",
        False,
        None,
    )


def validate_receipt(directory: Path, root: Path, allowlist_path: Path, stage: Path | None = None) -> dict[str, Any]:
    result = _validate_receipt(
        directory, root, allowlist_path,
        "microduck-complete-assets-v2.tar.gz",
        "microduck.m6-local-distribution-result/v2",
        True,
        stage,
    )
    bundle = (directory / "microduck-complete-assets-v2.tar.gz").read_bytes()
    if bundle[:10] != bytes.fromhex("1f8b08000000000002ff"):
        raise AssertionError("portable receipt gzip header drift")
    return result
