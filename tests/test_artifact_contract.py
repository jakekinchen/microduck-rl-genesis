"""Validate synthetic official/community bundles and fail-closed mutations."""

from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from artifact_contract.validator import validate_fixture_bundle, validate_hardware_attestation, validate_policy_manifest, validate_reference_attestation

official = ROOT / "artifact_contract/fixtures/official"
community = ROOT / "artifact_contract/fixtures/community"
validate_fixture_bundle(official, "official")
validate_fixture_bundle(community, "community")


def rejected(bundle: Path, source_class: str, mutate) -> None:
    with tempfile.TemporaryDirectory() as temp:
        copied = Path(temp) / "bundle"
        shutil.copytree(bundle, copied)
        manifest_path = copied / "policy-manifest-v2.json"
        value = json.loads(manifest_path.read_text())
        mutate(value)
        manifest_path.write_text(json.dumps(value))
        try:
            validate_fixture_bundle(copied, source_class)
        except AssertionError:
            return
        raise AssertionError("invalid artifact mutation accepted")


rejected(official, "official", lambda value: value["bindings"].pop("license"))
rejected(official, "official", lambda value: value["bindings"]["normalized_onnx"].__setitem__("sha256", "sha256:" + "0" * 64))
rejected(official, "community", lambda value: None)
rejected(community, "community", lambda value: value["lifecycle"].__setitem__("activation", "authorized"))

with tempfile.TemporaryDirectory() as temp:
    copied = Path(temp) / "official"
    shutil.copytree(official, copied)
    official_manifest = validate_policy_manifest(copied / "policy-manifest-v2.json", "official")
    path = copied / "reference-attestation-v1.json"
    reference = json.loads(path.read_text())
    reference["grants"]["task_success"] = True
    path.write_text(json.dumps(reference))
    try:
        validate_reference_attestation(path, official_manifest)
    except AssertionError:
        pass
    else:
        raise AssertionError("reference attestation granted task success")

with tempfile.TemporaryDirectory() as temp:
    copied = Path(temp) / "community"
    shutil.copytree(community, copied)
    community_manifest = validate_policy_manifest(copied / "policy-manifest-v2.json", "community")
    path = copied / "hardware-attestation-v1.json"
    hardware = json.loads(path.read_text())
    hardware["physical_authority"] = "physically_accepted"
    path.write_text(json.dumps(hardware))
    try:
        validate_hardware_attestation(path, community_manifest)
    except AssertionError:
        pass
    else:
        raise AssertionError("hardware fixture gained physical authority")

print("policy manifest v2 and reference/hardware attestation fixtures verified without execution")
