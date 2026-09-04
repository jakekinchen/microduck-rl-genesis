"""Validate the retained public community-authority search without execution."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ARTIFACT_REVISION = "fa7b27eeb5610d3b351362f4bd71691ee8be3d7d"
TRAINING_COMMIT = "6cd45fc7a865299f118f7671142465d377853928"
TRAINING_TREE = "8e6b4f2a9ee405e7091c7b93c25b6b1585d88e22"
BAM_COMMIT = "62bd8ce12154340be97e06f7f41a0ca8f116d967"
POLICY_SHA256 = "5aa423bd693e431b19e2ead77f99cbae6184e40a529eb2f7c1b4f85bb7f57040"
PREVIEW_SHA256 = "dd079687dba782bdf3c0cd63f010b0cfd6d1084024018f6810cb3468d1d1f82a"


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _load(directory: Path, name: str):
    return json.loads((directory / name).read_text())


def _validate_manifest(directory: Path) -> None:
    lines = (directory / "SHA256SUMS").read_text().splitlines()
    records = [line.split("  ./", 1) for line in lines]
    _assert(all(len(record) == 2 for record in records), "invalid receipt manifest syntax")
    paths = [record[1] for record in records]
    actual = sorted(path.name for path in directory.iterdir() if path.is_file() and path.name != "SHA256SUMS")
    _assert(paths == sorted(paths) == actual, "receipt manifest coverage or order drift")
    for digest, relative in records:
        observed = hashlib.sha256((directory / relative).read_bytes()).hexdigest()
        _assert(observed == digest, f"receipt digest mismatch: {relative}")


def validate_community_search_receipt(directory: Path) -> dict:
    _validate_manifest(directory)
    result = _load(directory, "SEARCH_RESULT.json")
    _assert(result.get("schema_version") == "microduck.m6-community-authority-search/v1", "search schema drift")
    _assert(result.get("artifact_revision") == ARTIFACT_REVISION, "artifact revision drift")
    _assert(result.get("training_commit") == TRAINING_COMMIT, "training commit drift")
    _assert(result.get("bam_commit") == BAM_COMMIT, "BAM commit drift")
    _assert(result.get("result") == "community_policy_roles_still_missing", "missing-role result promoted")
    _assert(set(result.get("role_outcomes", {})) == {"source_checkpoint", "normalizer", "evaluator", "evidence", "exporter_provenance"}, "role outcome coverage drift")
    _assert(all(value.startswith(("missing:", "incomplete:")) for value in result["role_outcomes"].values()), "role outcome falsely resolved")
    _assert(result.get("actions") and all(value is False for value in result["actions"].values()), "prohibited action recorded")
    _assert(result["hf_lfs"] == {"policy_sha256": POLICY_SHA256, "policy_size_bytes": 793772, "preview_sha256": PREVIEW_SHA256, "preview_size_bytes": 11412279}, "LFS summary drift")
    gap = result["resolved_adjacent_inventory_gap"]
    _assert(gap.get("byte_identical") is True and gap.get("new_status") == "complete", "adjacent provenance gap not closed exactly")
    _assert(gap.get("source_revision") == BAM_COMMIT and gap.get("sha256") == "61c699362fb3fabdde93eeba5e1ad3bf4ef9ca2f71d03e316b1924ff005b20d3", "adjacent BAM binding drift")

    revision = _load(directory, "hf-revision.json")
    _assert(revision.get("sha") == ARTIFACT_REVISION, "Hugging Face revision response drift")
    _assert({item["rfilename"] for item in revision.get("siblings", [])} == {".gitattributes", "README.md", "manifest.json", "media/preview.mp4", "policy.onnx"}, "Hugging Face revision file set drift")
    hf_tree = _load(directory, "hf-tree.json")
    hf_files = {item["path"]: item for item in hf_tree if item["type"] == "file"}
    _assert(set(hf_files) == {".gitattributes", "README.md", "manifest.json", "media/preview.mp4", "policy.onnx"}, "Hugging Face tree file set drift")
    _assert(hf_files["policy.onnx"]["lfs"] == {"oid": POLICY_SHA256, "size": 793772, "pointerSize": 131}, "policy LFS authority drift")
    _assert(hf_files["media/preview.mp4"]["lfs"]["oid"] == PREVIEW_SHA256, "preview LFS authority drift")

    training_commit = _load(directory, "github-training-commit.json")
    _assert(training_commit.get("sha") == TRAINING_COMMIT, "GitHub commit response drift")
    _assert(training_commit.get("commit", {}).get("tree", {}).get("sha") == TRAINING_TREE, "GitHub tree identity drift")
    training_tree = _load(directory, "github-training-tree.json")
    paths = [item["path"] for item in training_tree.get("tree", [])]
    _assert(training_tree.get("sha") == TRAINING_TREE and training_tree.get("truncated") is False and len(paths) == 251, "GitHub tree coverage drift")
    _assert(not [path for path in paths if path.lower().endswith((".pt", ".pth", ".ckpt", ".onnx"))], "unexpected model/checkpoint appeared in retained tree")
    _assert(not [path for path in paths if path.startswith("results/") or "normaliz" in path.lower() or "evaluator" in path.lower() or "evidence" in path.lower()], "unexpected authority file appeared in retained tree")

    history = _load(directory, "github-history-summary.json")
    _assert(history.get("commits_checked") == 1000 and history.get("pagination_limit_reached") is True, "history scope drift")
    _assert(set(history.get("exact_term_occurrences_in_commit_messages", {}).values()) == {0}, "history summary fabricated an authority hit")
    wandb = _load(directory, "wandb-public-search.json")
    _assert(wandb.get("authentication") == "anonymous_public_only", "W&B search used undeclared authority")
    _assert(wandb.get("anonymous_graphql", {}).get("response") == {"data": {"project": None}}, "W&B public boundary drift")
    _assert(set(wandb.get("direct_file_status", {}).values()) == {404}, "W&B public file unexpectedly promoted")
    _assert(wandb.get("disposition") == "unverifiable_dashboard_rejected", "W&B dashboard accepted without authority")
    return result
