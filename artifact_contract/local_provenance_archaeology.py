"""Validate retained local/remote provenance archaeology without policy execution."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ACCEPTED_BASE = "321f0a9396b7596e62a0834d79c167a9fe8ce32a"
GENESIS_INTRO = "8659972a88cb6d6eab89ace269ef585bb172a581"
GENESIS_TREE = "313ea430f69061d643820288d1be988d5c5e729e"
BALL_SOURCE = "84790795a6647f7dbd2353f53f7263229d7b7051"
BALL_SOURCE_TREE = "0b5d3766442f3c2bb1405c2a61dff75c6891eb40"
BALL_LATER_CHANGE = "7831c5142f93cc863327ae607bf0d262d127c767"
OFFICIAL_COMMIT = "109e06d4ce4921b635c5609e5304079fc30960ae"
BALL_LOCAL_PATH = "microduck/assets/microduck/ball.xml"
BALL_SOURCE_PATH = "src/mjlab_microduck/robot/microduck/ball.xml"
BALL_SHA256 = "54a455bf454a9b6167655381df91593bbca86695d8d71e29fb6af69454c7c865"
TARGETS = {
    "demo/apercu.gif": ("7f84e0062b408e8b9565dd7003cd40a4f4d9c41e", "eea3bf85da13b859485e342e69d076656838780c2c6421c5298de6fe58eec030", 4387435),
    "demo/microduck-parcours-30s.mp4": ("2ba6e6a5081c2691e4c137f70bf163154f50a14d", "3c380ebba4d1f333a769f10342d132fdb1df2251c9eec89ca718236d80fb5e1e", 5234921),
    "policies/backlash.onnx": ("b386dd537c36805de8e9f86dfc2000c04e5e7a2a", "3f8db8bc2c11b2e41665633c1780af21bae3fda7db229eb5035e6c2d5698c075", 793295),
    "policies/rough.onnx": ("47ed1e389812fe87246f4be4302a714d4bcf93a5", "04261902d3651dc02303e3e9e5ab756062c4d93c45400f431a0ae68b5969185c", 793295),
    "policies/velocity.onnx": ("1afef746646caf89b7366a69a951275c7232546f", "c315b9159a1b6f30976c90074ed6df2a33e7e1d14ef1505aed6c2c673f59061d", 793295),
}


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _load(directory: Path, name: str):
    return json.loads((directory / name).read_text())


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git(repo: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True
    ).stdout


def _validate_manifest(directory: Path) -> None:
    expected = {
        "EVIDENCE_BOUNDARY.txt",
        "SEARCH_RESULT.json",
        "ball-source-chain.json",
        "genesis-target-history.json",
        "media-metadata.json",
        "remote-authority-search.json",
        "source-exclusion-summary.json",
    }
    records = [line.split("  ./", 1) for line in (directory / "SHA256SUMS").read_text().splitlines()]
    _assert(all(len(record) == 2 for record in records), "invalid receipt manifest syntax")
    paths = [record[1] for record in records]
    _assert(paths == sorted(paths) and set(paths) == expected, "receipt manifest coverage or order drift")
    actual = {path.name for path in directory.iterdir() if path.is_file() and path.name != "SHA256SUMS"}
    _assert(actual == expected, "receipt payload set drift")
    for digest, relative in records:
        _assert(_sha256((directory / relative).read_bytes()) == digest, f"receipt digest mismatch: {relative}")


def validate_local_provenance_archaeology(
    directory: Path, root: Path | None = None, official_repo: Path | None = None
) -> dict:
    _validate_manifest(directory)
    result = _load(directory, "SEARCH_RESULT.json")
    _assert(result.get("schema_version") == "microduck.m6-local-provenance-archaeology/v1", "search schema drift")
    _assert(result.get("accepted_base") == ACCEPTED_BASE, "accepted base drift")
    _assert(result.get("result") == "ball_source_resolved_five_files_still_missing", "search result promoted")
    ball = result.get("ball", {})
    _assert(ball.get("old_status") == "partial" and ball.get("new_status") == "complete", "ball status drift")
    _assert(ball.get("source_revision") == BALL_SOURCE and ball.get("byte_identical") is True, "ball source drift")
    _assert(ball.get("sha256") == BALL_SHA256 and ball.get("later_upstream_change") == BALL_LATER_CHANGE, "ball chain drift")
    _assert(set(result.get("unresolved", {})) == set(TARGETS), "unresolved target coverage drift")
    _assert(all(value.startswith("missing:") for value in result["unresolved"].values()), "unresolved target promoted")
    _assert(result.get("inventory_after") == {"total_files": 70, "complete": 65, "partial": 0, "missing": 5, "fully_resolved": False}, "inventory result drift")
    _assert(result.get("actions") and all(value is False for value in result["actions"].values()), "prohibited action recorded")

    chain = _load(directory, "ball-source-chain.json")
    _assert(chain.get("schema_version") == "microduck.ball-source-chain/v1", "ball chain schema drift")
    intro = chain.get("genesis_introduction", {})
    source = chain.get("exact_public_source", {})
    later = chain.get("later_upstream_state", {})
    _assert((intro.get("commit"), intro.get("tree"), intro.get("git_blob_sha1")) == (GENESIS_INTRO, GENESIS_TREE, "42c3278eb5f5498e8204bc9696bf223c810e7d2e"), "Genesis ball introduction drift")
    _assert((source.get("commit"), source.get("tree"), source.get("sha256")) == (BALL_SOURCE, BALL_SOURCE_TREE, BALL_SHA256), "public ball source drift")
    _assert(later.get("change_commit") == BALL_LATER_CHANGE and later.get("declared_inventory_revision") == OFFICIAL_COMMIT, "later ball state drift")
    _assert(chain.get("verified_relations") == {
        "source_is_ancestor_of_declared_inventory_revision": True,
        "only_ball_path_change_between_source_and_declared_revision": BALL_LATER_CHANGE,
        "genesis_and_source_git_blob_identical": True,
        "genesis_and_source_sha256_identical": True,
        "unresolved_local_transform": False,
    }, "ball relation drift")
    _assert(chain.get("license", {}).get("declared_license") == "CC-BY-SA-NC", "ball license drift")

    history = _load(directory, "genesis-target-history.json")
    _assert(history.get("reachable_commit_count") == 153, "reachable history scope drift")
    _assert(history.get("common_introduction_commit") == GENESIS_INTRO and history.get("common_introduction_parent_count") == 0, "common introduction drift")
    observed_targets = {item["path"]: (item["git_blob_sha1"], item["sha256"], item["size_bytes"]) for item in history.get("targets", [])}
    _assert(observed_targets == TARGETS and all(item.get("history_commit_count") == 1 for item in history["targets"]), "target history drift")
    _assert(len(history.get("reachable_checkpoint_paths", [])) == 4 and all("apple-baseline" in path for path in history["reachable_checkpoint_paths"]), "unrelated checkpoint scope drift")

    media = _load(directory, "media-metadata.json")
    _assert(media.get("result") == "no_embedded_production_source_or_file_license" and media.get("authority") == "none", "media metadata promoted")
    _assert(set(media.get("files", {})) == {"demo/apercu.gif", "demo/microduck-parcours-30s.mp4"}, "media coverage drift")
    _assert(all(value.get("author_tag") is None and value.get("copyright_tag") is None and value.get("source_receipt_tag") is None for value in media["files"].values()), "media metadata authority fabricated")

    remote = _load(directory, "remote-authority-search.json")
    _assert(remote.get("authentication") == "anonymous_public_only", "remote search authentication drift")
    _assert(remote.get("result") == "no_immutable_remote_production_or_license_authority_for_five_targets", "remote result promoted")
    _assert(set(remote.get("repositories", {})) == {"Macmachi/microduck-rl-genesis", "jakekinchen/microduck-rl-genesis", "meniuniu/microduck-rl-genesis"}, "remote coverage drift")
    _assert(all(not value["tags"] and not value["releases"] and value["actions_artifact_count"] == 0 for value in remote["repositories"].values()), "remote artifact authority appeared")
    _assert(remote["repositories"]["meniuniu/microduck-rl-genesis"]["separate_policy_disposition"].startswith("different digest"), "separate fork policy conflated")

    exclusions = _load(directory, "source-exclusion-summary.json")
    _assert(exclusions.get("disposition") == "self_claims_and_explicit_exclusions_are_not_digest_bound_provenance", "source exclusions promoted")
    _assert(exclusions.get("root_tree_findings") and not any(exclusions["root_tree_findings"].values()), "missing source material fabricated")
    _assert("*.pt" in exclusions.get("ignored_training_and_render_paths", []) and "tools/" in exclusions["ignored_training_and_render_paths"], "source exclusion coverage drift")

    boundary = (directory / "EVIDENCE_BOUNDARY.txt").read_text()
    _assert("No ONNX policy was imported, parsed, loaded, executed" in boundary and "no credentials were used" in boundary, "evidence boundary drift")

    if root is not None:
        for path, (blob, digest, size) in TARGETS.items():
            local = root / path
            _assert(local.stat().st_size == size and _sha256(local.read_bytes()) == digest, f"local target drift: {path}")
            observed_blob = _git(root, "rev-parse", f"{GENESIS_INTRO}:{path}").decode().strip()
            _assert(observed_blob == blob, f"Genesis introduction blob drift: {path}")
        local_ball = (root / BALL_LOCAL_PATH).read_bytes()
        _assert(_sha256(local_ball) == BALL_SHA256, "local ball drift")

    if official_repo is not None:
        source_ball = _git(official_repo, "show", f"{BALL_SOURCE}:{BALL_SOURCE_PATH}")
        later_ball = _git(official_repo, "show", f"{OFFICIAL_COMMIT}:{BALL_SOURCE_PATH}")
        _assert(_sha256(source_ball) == BALL_SHA256, "official source ball drift")
        _assert(_sha256(later_ball) == "eee47ed46f954c25277cb885258ab0bce59335e7439be8152ba08f701c4abc23", "official later ball drift")
        _assert(b'priority="1"' not in source_ball and b'priority="1"' in later_ball, "ball semantic delta drift")
        subprocess.run(["git", "-C", str(official_repo), "merge-base", "--is-ancestor", BALL_SOURCE, OFFICIAL_COMMIT], check=True)
        changes = _git(official_repo, "rev-list", "--ancestry-path", "--reverse", f"{BALL_SOURCE}..{OFFICIAL_COMMIT}", "--", BALL_SOURCE_PATH).decode().splitlines()
        _assert(changes == [BALL_LATER_CHANGE], "ball ancestry path drift")
    return result
