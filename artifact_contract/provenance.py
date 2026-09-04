"""Build and validate deterministic file-level license/provenance inventory."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

OFFICIAL_REPOSITORY = "https://github.com/pollen-robotics/microduck_rl.git"
OFFICIAL_COMMIT = "109e06d4ce4921b635c5609e5304079fc30960ae"
ASSET_LICENSE = "CC-BY-SA-NC"
CODE_LICENSE = "Apache-2.0"
BAM_REPOSITORY = "https://github.com/Rhoban/bam.git"
BAM_COMMIT = "62bd8ce12154340be97e06f7f41a0ca8f116d967"
BAM_PARAMETER_PATH = "bam/params/xl330/m6.json"
LIFECYCLE = {
    "download": "not_performed",
    "library_import": "not_performed",
    "evaluation": "not_performed",
    "approval": "not_requested",
    "activation": "not_authorized",
}


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


def local_record(root: Path, path: Path, artifact_class: str) -> dict[str, Any]:
    return {
        "path": path.relative_to(root).as_posix(),
        "artifact_class": artifact_class,
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def build_inventory(root: Path, official_repo: Path) -> dict[str, Any]:
    license_path = root / "microduck/assets/LICENSE-ASSETS.md"
    root_license = root / "LICENSE"
    files: list[dict[str, Any]] = []
    asset_root = root / "microduck/assets/microduck"
    for path in sorted(candidate for candidate in asset_root.rglob("*") if candidate.suffix in {".xml", ".stl"}):
        item = local_record(root, path, "mjcf" if path.suffix == ".xml" else "mesh")
        relative_asset = path.relative_to(asset_root).as_posix()
        source_path = f"src/mjlab_microduck/robot/microduck/{relative_asset}"
        source_bytes = git_blob(official_repo, OFFICIAL_COMMIT, source_path)
        matches = source_bytes == path.read_bytes()
        item.update({
            "declared_license": ASSET_LICENSE,
            "license_evidence": {"path": "microduck/assets/LICENSE-ASSETS.md", "sha256": sha256_file(license_path)},
            "source": {"repository": OFFICIAL_REPOSITORY, "revision": OFFICIAL_COMMIT, "path": source_path, "sha256": sha256_bytes(source_bytes), "byte_identical": matches},
            "provenance_status": "complete" if matches else "partial",
            "blockers": [] if matches else ["local bytes differ from the exact declared upstream revision; transformation provenance is unresolved"],
        })
        files.append(item)

    add_backlash = asset_root / "add_backlash.py"
    add_source_path = "src/mjlab_microduck/robot/microduck/add_backlash.py"
    add_source = git_blob(official_repo, OFFICIAL_COMMIT, add_source_path)
    add_item = local_record(root, add_backlash, "asset_transform_code")
    add_item.update({
        "declared_license": CODE_LICENSE,
        "license_evidence": {"path": "LICENSE", "sha256": sha256_file(root_license)},
        "source": {"repository": OFFICIAL_REPOSITORY, "revision": OFFICIAL_COMMIT, "path": add_source_path, "sha256": sha256_bytes(add_source), "byte_identical": add_source == add_backlash.read_bytes()},
        "provenance_status": "complete" if add_source == add_backlash.read_bytes() else "partial",
        "blockers": [] if add_source == add_backlash.read_bytes() else ["local transform code differs from bound upstream source"],
    })
    files.append(add_item)

    actuator = root / "microduck/assets/xl330_m6.json"
    actuator_source = root / "artifact_contract/real-candidates/community-rough-walk-e-fa7b27e/bam_xl330_m6.json"
    actuator_source_bytes = actuator_source.read_bytes()
    actuator_matches = actuator_source_bytes == actuator.read_bytes()
    actuator_item = local_record(root, actuator, "actuator_parameter")
    actuator_item.update({
        "declared_license": CODE_LICENSE,
        "license_evidence": {"path": "microduck/assets/LICENSE-ASSETS.md", "sha256": sha256_file(license_path)},
        "source": {"repository": BAM_REPOSITORY, "revision": BAM_COMMIT, "path": BAM_PARAMETER_PATH, "sha256": sha256_bytes(actuator_source_bytes), "byte_identical": actuator_matches},
        "provenance_status": "complete" if actuator_matches else "partial",
        "blockers": [] if actuator_matches else ["local actuator parameters differ from the immutable BAM source blob"],
    })
    files.append(actuator_item)

    for path in sorted((root / "policies").glob("*.onnx")):
        item = local_record(root, path, "policy_weight")
        item.update({
            "declared_license": "unresolved",
            "license_evidence": None,
            "source": None,
            "provenance_status": "missing",
            "blockers": ["source checkpoint missing", "training run missing", "exporter invocation missing", "normalizer provenance missing", "file-level policy license missing"],
        })
        files.append(item)

    for path in sorted(list((root / "demo").glob("*.gif")) + list((root / "demo").glob("*.mp4"))):
        item = local_record(root, path, "media")
        item.update({
            "declared_license": "unresolved",
            "license_evidence": None,
            "source": None,
            "provenance_status": "missing",
            "blockers": ["production/source receipt missing", "file-level media license missing", "depicted asset attribution is not bound to the media digest"],
        })
        files.append(item)

    files.sort(key=lambda item: item["path"])
    counts = {status: sum(item["provenance_status"] == status for item in files) for status in ("complete", "partial", "missing")}
    return {
        "schema_version": "microduck.file-provenance-inventory/v1",
        "official_asset_source": {"repository": OFFICIAL_REPOSITORY, "revision": OFFICIAL_COMMIT},
        "lifecycle": LIFECYCLE,
        "dataset_scope": {"paths": [], "status": "absent_no_dataset_files", "claim": "no dataset provenance is invented"},
        "files": files,
        "summary": {"total_files": len(files), **counts, "fully_resolved": counts["partial"] == 0 and counts["missing"] == 0},
        "proof_class": "provenance_inventory_only",
        "artifact_acceptance": "none",
    }


def validate_inventory(inventory: dict[str, Any], root: Path, official_repo: Path | None = None) -> None:
    if inventory.get("schema_version") != "microduck.file-provenance-inventory/v1":
        raise AssertionError("inventory schema drift")
    if inventory.get("lifecycle") != LIFECYCLE:
        raise AssertionError("inventory lifecycle promoted")
    if inventory.get("proof_class") != "provenance_inventory_only" or inventory.get("artifact_acceptance") != "none":
        raise AssertionError("inventory promoted artifact authority")
    expected_paths = {
        path.relative_to(root).as_posix()
        for path in (root / "microduck/assets/microduck").rglob("*")
        if path.suffix in {".xml", ".stl"}
    }
    expected_paths |= {"microduck/assets/microduck/add_backlash.py", "microduck/assets/xl330_m6.json"}
    expected_paths |= {path.relative_to(root).as_posix() for path in (root / "policies").glob("*.onnx")}
    expected_paths |= {path.relative_to(root).as_posix() for path in list((root / "demo").glob("*.gif")) + list((root / "demo").glob("*.mp4"))}
    records = inventory.get("files", [])
    if {item["path"] for item in records} != expected_paths or len(records) != len(expected_paths):
        raise AssertionError("inventory coverage gap or duplicate")
    for item in records:
        path = root / item["path"]
        if not path.is_file() or path.stat().st_size != item["size_bytes"] or sha256_file(path) != item["sha256"]:
            raise AssertionError(f"inventory file drift: {item['path']}")
        status = item["provenance_status"]
        if status == "complete" and item["blockers"]:
            raise AssertionError("complete entry retains blockers")
        if item["artifact_class"] in {"policy_weight", "media"} and status != "missing":
            raise AssertionError("unattributed policy/media falsely marked complete")
        evidence = item.get("license_evidence")
        if evidence and sha256_file(root / evidence["path"]) != evidence["sha256"]:
            raise AssertionError(f"license evidence drift: {item['path']}")
        if official_repo and item["artifact_class"] in {"mjcf", "mesh", "asset_transform_code"}:
            source = item["source"]
            source_bytes = git_blob(official_repo, source["revision"], source["path"])
            if sha256_bytes(source_bytes) != source["sha256"] or (source_bytes == path.read_bytes()) != source["byte_identical"]:
                raise AssertionError(f"upstream source comparison drift: {item['path']}")
        if item["artifact_class"] == "actuator_parameter":
            source = item["source"]
            expected_source = root / "artifact_contract/real-candidates/community-rough-walk-e-fa7b27e/bam_xl330_m6.json"
            source_bytes = expected_source.read_bytes()
            if source != {
                "repository": BAM_REPOSITORY,
                "revision": BAM_COMMIT,
                "path": BAM_PARAMETER_PATH,
                "sha256": sha256_bytes(source_bytes),
                "byte_identical": source_bytes == path.read_bytes(),
            }:
                raise AssertionError("actuator parameter source binding drift")
    counts = {status: sum(item["provenance_status"] == status for item in records) for status in ("complete", "partial", "missing")}
    expected_summary = {"total_files": len(records), **counts, "fully_resolved": counts["partial"] == 0 and counts["missing"] == 0}
    if inventory.get("summary") != expected_summary:
        raise AssertionError("inventory summary drift")
    if inventory.get("dataset_scope") != {"paths": [], "status": "absent_no_dataset_files", "claim": "no dataset provenance is invented"}:
        raise AssertionError("dataset scope invented or promoted")
