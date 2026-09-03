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
