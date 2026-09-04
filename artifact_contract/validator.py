"""Validate manifest and attestation bytes without importing or executing them."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

REQUIRED_ROLES = {
    "normalized_onnx", "normalizer", "source_checkpoint", "exporter", "model",
    "bam", "task", "evaluator", "evidence", "license",
}
RESOLUTION_LIFECYCLE = {
    "download": "performed_immutable_revision",
    "library_import": "not_performed",
    "evaluation": "not_performed",
    "approval": "not_requested",
    "activation": "not_authorized",
}
SYNTHETIC_LIFECYCLE = {
    "download": "synthetic_fixture",
    "library_import": "not_performed",
    "evaluation": "not_performed",
    "approval": "not_requested",
    "activation": "not_authorized",
}
DIGEST_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_bound_path(base: Path, relative: str) -> Path:
    candidate = Path(relative)
    _assert(not candidate.is_absolute() and ".." not in candidate.parts, "binding escapes bundle")
    resolved = (base / candidate).resolve()
    _assert(resolved.parent == base.resolve(), "fixture bindings must be direct bundle files")
    return resolved


def _validate_binding(base: Path, binding: dict[str, Any]) -> Path:
    _assert(DIGEST_RE.fullmatch(binding.get("sha256", "")) is not None, "invalid SHA-256 syntax")
    path = _safe_bound_path(base, binding["path"])
    _assert(path.is_file(), f"missing bound artifact: {binding['path']}")
    _assert(path.stat().st_size == binding.get("size_bytes"), f"size mismatch: {binding['path']}")
    _assert(sha256_file(path) == binding["sha256"], f"digest mismatch: {binding['path']}")
    return path


def validate_policy_manifest(path: Path, expected_source_class: str | None = None) -> dict[str, Any]:
    manifest = json.loads(path.read_text())
    _assert(manifest.get("schema_version") == "microduck.policy-manifest/v2", "policy manifest schema drift")
    _assert(manifest.get("source_class") in {"official", "community"}, "invalid source class")
    if expected_source_class:
        _assert(manifest["source_class"] == expected_source_class, "source class confusion")
    _assert(manifest.get("synthetic_fixture") is True, "this validator slice accepts synthetic fixtures only")
    _assert(set(manifest.get("bindings", {})) == REQUIRED_ROLES, "manifest binding set incomplete")
    for binding in manifest["bindings"].values():
        _validate_binding(path.parent, binding)
    source = manifest["source"]
    _assert(re.fullmatch(r"[0-9a-f]{40}", source.get("commit", "")) is not None, "source commit is not immutable")
    _assert(source.get("run_id") and source.get("exporter_invocation"), "source provenance incomplete")
    interface = manifest["interface"]
    _assert(interface == {"observation_dim": 61, "action_dim": 14, "control_hz": 50, "normalization": "baked_into_onnx_and_separately_bound"}, "interface or normalization drift")
    _assert(manifest.get("lifecycle") == SYNTHETIC_LIFECYCLE, "lifecycle state promoted or conflated")
    _assert(manifest.get("authority") == "synthetic_validation_only", "synthetic fixture gained artifact authority")
    return manifest


def validate_reference_attestation(path: Path, manifest: dict[str, Any]) -> None:
    value = json.loads(path.read_text())
    _assert(value.get("schema_version") == "microduck.reference-attestation/v1", "reference attestation schema drift")
    _assert(value.get("synthetic_fixture") is True, "reference fixture flag missing")
    manifest_path = _validate_binding(path.parent, value["manifest"])
    _assert(manifest_path.name == "policy-manifest-v2.json", "reference attestation bound wrong manifest")
    _assert(value["reference"]["source_class"] == manifest["source_class"], "reference source class confusion")
    _assert(value["reference"]["artifact_sha256"] == manifest["bindings"]["normalized_onnx"]["sha256"], "reference artifact mismatch")
    _assert(value.get("result") == "not_evaluated", "reference fixture promoted evaluation")
    _assert(value.get("grants") == {"task_success": False, "transfer": False, "hardware": False, "activation": False}, "reference evidence granted downstream authority")


def validate_hardware_attestation(path: Path, manifest: dict[str, Any]) -> None:
    value = json.loads(path.read_text())
    _assert(value.get("schema_version") == "microduck.hardware-attestation/v1", "hardware attestation schema drift")
    _assert(value.get("synthetic_fixture") is True, "hardware fixture flag missing")
    manifest_path = _validate_binding(path.parent, value["manifest"])
    _assert(manifest_path.name == "policy-manifest-v2.json", "hardware attestation bound wrong manifest")
    _assert(value["hardware"].get("serial_recorded") is False, "synthetic hardware fixture recorded serial")
    _assert(value.get("approval") == "not_requested", "approval state promoted")
    _assert(value.get("activation") == "not_authorized", "activation state promoted")
    _assert(value.get("result") == "not_executed", "synthetic hardware result promoted")
    _assert(value.get("physical_authority") == "not_granted", "simulation/reference evidence granted physical authority")


def validate_fixture_bundle(directory: Path, expected_source_class: str) -> None:
    manifest = validate_policy_manifest(directory / "policy-manifest-v2.json", expected_source_class)
    reference = directory / "reference-attestation-v1.json"
    hardware = directory / "hardware-attestation-v1.json"
    _assert(reference.is_file() ^ hardware.is_file(), "fixture must contain exactly one attestation type")
    if reference.is_file():
        validate_reference_attestation(reference, manifest)
    else:
        validate_hardware_attestation(hardware, manifest)


def _validate_resolution_source(source: dict[str, Any]) -> None:
    revision = source.get("revision", "")
    _assert(re.fullmatch(r"[0-9a-f]{40}", revision) is not None, "resolution source revision is not immutable")
    _assert(source.get("repository", "").startswith("https://"), "resolution source repository is not HTTPS")
    _assert(source.get("path"), "resolution source path missing")
    _assert(revision in source.get("url", ""), "resolution source URL is not revision-pinned")


def validate_resolution_bundle(directory: Path, expected_source_class: str | None = None) -> dict[str, Any]:
    """Validate a real candidate's bytes and fail-closed v2 role resolution.

    A resolution bundle is not a policy manifest. It records which manifest-v2
    roles can be attributed from immutable bytes and why the remaining roles
    prevent emission of an authoritative ``policy-manifest-v2.json``.
    """

    path = directory / "policy-manifest-v2-resolution.json"
    value = json.loads(path.read_text())
    _assert(value.get("schema_version") == "microduck.policy-manifest-v2-resolution/v1", "resolution schema drift")
    _assert(value.get("target_schema") == "microduck.policy-manifest/v2", "resolution targets wrong manifest schema")
    _assert(value.get("source_class") in {"official", "community"}, "invalid resolution source class")
    if expected_source_class:
        _assert(value["source_class"] == expected_source_class, "resolution source class confusion")
    _assert(value.get("synthetic_fixture") is False, "real candidate marked synthetic")
    _assert(value.get("proof_class") == "immutable_attribution_audit_only", "resolution proof class promoted")
    _assert(value.get("authority") == "none", "incomplete candidate gained authority")
    _assert(value.get("lifecycle") == RESOLUTION_LIFECYCLE, "resolution lifecycle promoted or conflated")

    bindings = value.get("bindings", {})
    _assert(set(bindings) == REQUIRED_ROLES, "resolution binding set incomplete")
    bound_roles: list[str] = []
    missing_roles: list[str] = []
    referenced_paths: list[str] = []
    for role in sorted(REQUIRED_ROLES):
        binding = bindings[role]
        status = binding.get("status")
        if status == "bound":
            _validate_binding(directory, binding)
            _validate_resolution_source(binding.get("source", {}))
            _assert(not binding.get("blockers"), f"bound role retains blockers: {role}")
            bound_roles.append(role)
            referenced_paths.append(binding["path"])
        elif status == "missing":
            _assert(set(binding) == {"status", "blockers"}, f"missing role fabricates a binding: {role}")
            _assert(isinstance(binding["blockers"], list) and binding["blockers"], f"missing role lacks blocker: {role}")
            _assert(all(isinstance(item, str) and item for item in binding["blockers"]), f"invalid blocker: {role}")
            missing_roles.append(role)
        else:
            raise AssertionError(f"invalid role status: {role}")

    supporting = value.get("supporting_files", [])
    _assert(isinstance(supporting, list), "supporting files must be a list")
    for binding in supporting:
        _validate_binding(directory, binding)
        _validate_resolution_source(binding.get("source", {}))
        referenced_paths.append(binding["path"])

    _assert(len(referenced_paths) == len(set(referenced_paths)), "candidate file bound more than once")
    actual_paths = {
        candidate.relative_to(directory).as_posix()
        for candidate in directory.iterdir()
        if candidate.is_file() and candidate.name != path.name
    }
    _assert(set(referenced_paths) == actual_paths, "candidate bundle has missing or unbound files")

    validation = value.get("validation", {})
    _assert(validation.get("bound_roles") == bound_roles, "bound-role summary drift")
    _assert(validation.get("missing_roles") == missing_roles, "missing-role summary drift")
    _assert(validation.get("byte_validation") == "passed", "byte validation not recorded")
    _assert(missing_roles, "complete candidates require the authoritative manifest path")
    _assert(validation.get("policy_manifest_v2") == "rejected_incomplete", "incomplete candidate was not rejected")
    _assert(validation.get("formal_manifest_emitted") is False, "incomplete candidate emitted a formal manifest")
    _assert(not (directory / "policy-manifest-v2.json").exists(), "incomplete candidate contains a formal manifest")

    provenance = value.get("source_provenance", {})
    _assert(provenance.get("status") == "incomplete", "incomplete provenance promoted")
    _assert(isinstance(provenance.get("missing"), list) and provenance["missing"], "source provenance blockers absent")
    return value
