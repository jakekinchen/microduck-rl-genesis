"""Validate retained local/remote provenance archaeology without policy execution."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ACCEPTED_BASE = "321f0a9396b7596e62a0834d79c167a9fe8ce32a"
CORRECTION_BASE = "18e79c6a727d503cb03e30ff90c7708b95ab0b9c"
GENESIS_INTRO = "8659972a88cb6d6eab89ace269ef585bb172a581"
GENESIS_TREE = "313ea430f69061d643820288d1be988d5c5e729e"
BALL_SOURCE = "84790795a6647f7dbd2353f53f7263229d7b7051"
BALL_SOURCE_TREE = "0b5d3766442f3c2bb1405c2a61dff75c6891eb40"
BALL_LATER_CHANGE = "7831c5142f93cc863327ae607bf0d262d127c767"
LICENSE_DECLARATION = "fc1697699c478ed4f67373808a23caccc6bed785"
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
UNRESOLVED = {
    "demo/apercu.gif": "missing: production source receipt, file-level media license, and digest-bound depicted-asset attribution",
    "demo/microduck-parcours-30s.mp4": "missing: production source receipt, file-level media license, and digest-bound depicted-asset attribution",
    "policies/backlash.onnx": "missing: source checkpoint, training run, exporter invocation, normalizer provenance, and file-level policy license",
    "policies/rough.onnx": "missing: source checkpoint, training run, exporter invocation, normalizer provenance, and file-level policy license",
    "policies/velocity.onnx": "missing: source checkpoint, training run, exporter invocation, normalizer provenance, and file-level policy license",
}
ACTIONS = {
    "target_artifact_downloaded": False,
    "onnx_imported_or_parsed": False,
    "onnx_loaded": False,
    "policy_executed": False,
    "evaluation_performed": False,
    "training_performed": False,
    "publication_performed": False,
    "activation_performed": False,
    "compute_provisioned": False,
    "credentials_used": False,
}
HISTORY_SCOPE = {
    "kind": "exact_commit_ancestry",
    "commit": ACCEPTED_BASE,
    "commit_count": 150,
    "first_parent_commit_count": 150,
    "dynamic_refs_excluded": True,
    "public_branches_audited_separately": True,
}
CHECKPOINT_PATHS = [
    "receipts/apple-baseline/20260901T215219Z-2ce72a94/backflip/model_0.pt",
    "receipts/apple-baseline/20260901T215219Z-2ce72a94/backflip/model_4.pt",
    "receipts/apple-baseline/20260901T215219Z-2ce72a94/walking/model_0.pt",
    "receipts/apple-baseline/20260901T215219Z-2ce72a94/walking/model_4.pt",
]
MEDIA_FILES = {
    "demo/apercu.gif": {
        "sha256": TARGETS["demo/apercu.gif"][1],
        "format": "gif", "codec": "gif", "width": 760, "height": 414,
        "duration_seconds": 9.0, "frame_count": 108,
        "generic_encoder_tags": [], "author_tag": None, "copyright_tag": None,
        "source_receipt_tag": None, "authority": "none",
    },
    "demo/microduck-parcours-30s.mp4": {
        "sha256": TARGETS["demo/microduck-parcours-30s.mp4"][1],
        "format": "mov,mp4,m4a,3gp,3g2,mj2", "codec": "h264", "width": 1600, "height": 872,
        "duration_seconds": 30.0, "frame_count": 1500,
        "generic_encoder_tags": ["Lavf61.1.100", "Lavc61.3.100 libx264"],
        "author_tag": None, "copyright_tag": None, "source_receipt_tag": None,
        "authority": "none",
    },
}
REMOTE_REPOSITORIES = {
    "Macmachi/microduck-rl-genesis": {
        "branches": {"main": "9d1f213879650f2623e3bbd7bf06fe63dbf71a10"},
        "tags": [], "releases": [], "actions_artifact_count": 0,
        "target_files_changed_only_in_root_commit": True,
        "latest_commit_disposition": "adds cloud/ to ignored account-specific campaign automation; supplies no retained campaign artifact",
    },
    "jakekinchen/microduck-rl-genesis": {
        "branches": {"main": "3257775beeeb8b1df646dd295bf84e34967e42ec"},
        "tags": [], "releases": [], "actions_artifact_count": 0,
        "target_files_changed_only_in_root_commit": True,
    },
    "meniuniu/microduck-rl-genesis": {
        "branches": {"main": "9fa4b270023b8b9b50809fa6dc15a28996f5c724", "codex/macos-metal": "1082c025f3ce102fbd8f75a2e94897b293535098"},
        "tags": [], "releases": [], "actions_artifact_count": 0,
        "target_files_changed_only_in_root_commit": True,
        "separate_policy": "policies/microduck_walk_macos_scratch_seed1.onnx",
        "separate_policy_sha256": "ece00bc0169e7daafe7d2071f1f42eb461c6a31e5614a798ae1a824d3a3a5388",
        "separate_policy_disposition": "different digest and lineage; does not resolve any original target",
        "original_policy_statement": "inference-only positive controls; not outputs or evidence from the macOS run",
    },
}
LICENSE = {
    "declared_license": "CC-BY-SA-NC",
    "local_evidence_path": "microduck/assets/LICENSE-ASSETS.md",
    "local_evidence_sha256": "7b0bb41adae491f8834e9ef154d16b527ead819ab3b9d9a7aeb5868862dae500",
    "upstream_declaration_revision": LICENSE_DECLARATION,
    "upstream_declaration_tree": "86e21fa46cf9846be5fbfc89c67cc07c1c5608e4",
    "upstream_declaration_parent": "1e79c29c97d8b38aee9eefde77a545860ba7658e",
    "upstream_declaration_readme_blob": "728e4c52e88d7fe52882ceb67246ea2a8b5a2c8e",
    "upstream_declaration_readme_sha256": "460bff8b51422f3b28215d545c1cb70d2659a6bdf0bcd610d0654c9f05476d53",
    "upstream_declaration_ball_blob": "42c3278eb5f5498e8204bc9696bf223c810e7d2e",
    "scope": "3D model files",
    "later_declared_revision": OFFICIAL_COMMIT,
    "later_declared_readme_sha256": "13b2fee4370e773d1f4b63f463e7d6a8f26049db264cebf2ef181dadd2784a81",
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
    _assert(result.get("schema_version") == "microduck.m6-local-provenance-archaeology/v2", "search schema drift")
    _assert(result.get("correction_base") == CORRECTION_BASE and result.get("history_base") == ACCEPTED_BASE, "base binding drift")
    _assert(result.get("result") == "ball_source_resolved_five_files_still_missing", "search result promoted")
    _assert(result.get("ball") == {
        "path": BALL_LOCAL_PATH, "old_status": "partial", "new_status": "complete",
        "source_revision": BALL_SOURCE, "source_path": BALL_SOURCE_PATH,
        "byte_identical": True, "sha256": BALL_SHA256,
        "license_declaration_revision": LICENSE_DECLARATION,
        "later_upstream_change": BALL_LATER_CHANGE,
    }, "ball result drift")
    _assert(result.get("unresolved") == UNRESOLVED, "unresolved target evidence drift")
    _assert(result.get("inventory_after") == {"total_files": 70, "complete": 65, "partial": 0, "missing": 5, "fully_resolved": False}, "inventory result drift")
    _assert(result.get("actions") == ACTIONS, "action boundary drift")

    chain = _load(directory, "ball-source-chain.json")
    _assert(chain.get("schema_version") == "microduck.ball-source-chain/v2", "ball chain schema drift")
    intro = chain.get("genesis_introduction", {})
    source = chain.get("exact_public_source", {})
    later = chain.get("later_upstream_state", {})
    _assert((intro.get("commit"), intro.get("tree"), intro.get("git_blob_sha1")) == (GENESIS_INTRO, GENESIS_TREE, "42c3278eb5f5498e8204bc9696bf223c810e7d2e"), "Genesis ball introduction drift")
    _assert((source.get("commit"), source.get("tree"), source.get("sha256")) == (BALL_SOURCE, BALL_SOURCE_TREE, BALL_SHA256), "public ball source drift")
    _assert(later.get("change_commit") == BALL_LATER_CHANGE and later.get("declared_inventory_revision") == OFFICIAL_COMMIT, "later ball state drift")
    _assert(chain.get("license") == LICENSE, "ball license evidence drift")
    _assert(chain.get("verified_relations") == {
        "source_is_ancestor_of_license_declaration": True,
        "license_declaration_is_ancestor_of_later_change": True,
        "source_is_ancestor_of_declared_inventory_revision": True,
        "only_ball_path_change_between_source_and_declared_revision": BALL_LATER_CHANGE,
        "genesis_and_source_git_blob_identical": True,
        "genesis_and_source_sha256_identical": True,
        "unresolved_local_transform": False,
    }, "ball relation drift")
    history = _load(directory, "genesis-target-history.json")
    _assert(history.get("schema_version") == "microduck.genesis-target-history/v2", "history schema drift")
    _assert(history.get("history_scope") == HISTORY_SCOPE, "stable history scope drift")
    _assert(history.get("common_introduction_commit") == GENESIS_INTRO and history.get("common_introduction_parent_count") == 0, "common introduction drift")
    observed_targets = {item["path"]: (item["git_blob_sha1"], item["sha256"], item["size_bytes"]) for item in history.get("targets", [])}
    _assert(observed_targets == TARGETS and all(item.get("history_commit_count") == 1 for item in history["targets"]), "target history drift")
    _assert(history.get("reachable_checkpoint_paths") == CHECKPOINT_PATHS, "unrelated checkpoint scope drift")
    _assert(history.get("checkpoint_disposition") == "later five-iteration M0 smoke checkpoints with different digests; none is a source for the three root-commit policies", "checkpoint disposition drift")
    _assert(history.get("root_commit_claim_disposition") == "self-description only; no digest-bound source checkpoint, run receipt, exporter invocation, normalizer source, evaluator evidence, or file-level policy/media license", "root claim disposition drift")

    media = _load(directory, "media-metadata.json")
    _assert(media == {
        "schema_version": "microduck.inert-media-metadata/v2",
        "inspection": "ffprobe container metadata only; no visual-evidence or provenance inference",
        "files": MEDIA_FILES,
        "result": "no_embedded_production_source_or_file_license",
        "authority": "none",
    }, "media evidence drift")

    remote = _load(directory, "remote-authority-search.json")
    _assert(remote == {
        "schema_version": "microduck.public-remote-authority-search/v2",
        "queried_on": "2026-09-04", "authentication": "anonymous_public_only",
        "repositories": REMOTE_REPOSITORIES,
        "search_engine_exact_digest_results": 0,
        "search_engine_exact_filename_result": "root repository only",
        "result": "no_immutable_remote_production_or_license_authority_for_five_targets",
    }, "remote authority evidence drift")

    exclusions = _load(directory, "source-exclusion-summary.json")
    _assert(exclusions == {
        "schema_version": "microduck.source-exclusion-summary/v2",
        "root_commit": GENESIS_INTRO,
        "ignored_training_and_render_paths": ["logs/", "runs/", "videos/", "*.pt", "RAPPORT_NUIT.md", "RESULTATS.md", "run_*.sh", "progress_video.py", "render_course.py", "microduck/course.py", "tools/"],
        "current_upstream_additional_exclusion": "cloud/",
        "root_tree_findings": {
            "source_checkpoint": False, "training_run_receipt": False,
            "artifact_specific_export_receipt": False, "normalizer_source": False,
            "raw_policy_evidence": False, "media_production_chain": False,
            "file_level_policy_license": False, "file_level_media_license": False,
        },
        "retained_self_claims": [
            "root commit message says three trained policies ship",
            "policies/README.md names tasks, iterations, episode lengths, and generic regeneration commands",
            "README.md names campaign metrics and demo content",
        ],
        "disposition": "self_claims_and_explicit_exclusions_are_not_digest_bound_provenance",
    }, "source exclusion evidence drift")

    boundary = (directory / "EVIDENCE_BOUNDARY.txt").read_text()
    _assert("No ONNX policy was imported, parsed, loaded, executed" in boundary and "no credentials were used" in boundary, "evidence boundary drift")

    if root is not None:
        _assert(int(_git(root, "rev-list", "--count", ACCEPTED_BASE)) == 150, "accepted-base ancestry count drift")
        _assert(int(_git(root, "rev-list", "--count", "--first-parent", ACCEPTED_BASE)) == 150, "accepted-base first-parent count drift")
        for path, (blob, digest, size) in TARGETS.items():
            local = root / path
            _assert(local.stat().st_size == size and _sha256(local.read_bytes()) == digest, f"local target drift: {path}")
            observed_blob = _git(root, "rev-parse", f"{GENESIS_INTRO}:{path}").decode().strip()
            _assert(observed_blob == blob, f"Genesis introduction blob drift: {path}")
            history_commits = _git(root, "log", ACCEPTED_BASE, "--follow", "--format=%H", "--", path).decode().splitlines()
            _assert(history_commits == [GENESIS_INTRO], f"stable target history drift: {path}")
        local_ball = (root / BALL_LOCAL_PATH).read_bytes()
        _assert(_sha256(local_ball) == BALL_SHA256, "local ball drift")

    if official_repo is not None:
        source_ball = _git(official_repo, "show", f"{BALL_SOURCE}:{BALL_SOURCE_PATH}")
        later_ball = _git(official_repo, "show", f"{OFFICIAL_COMMIT}:{BALL_SOURCE_PATH}")
        license_readme = _git(official_repo, "show", f"{LICENSE_DECLARATION}:README.md")
        _assert(_sha256(source_ball) == BALL_SHA256, "official source ball drift")
        _assert(_sha256(later_ball) == "eee47ed46f954c25277cb885258ab0bce59335e7439be8152ba08f701c4abc23", "official later ball drift")
        _assert(b'priority="1"' not in source_ball and b'priority="1"' in later_ball, "ball semantic delta drift")
        _assert(_sha256(license_readme) == LICENSE["upstream_declaration_readme_sha256"] and b"3D model files are licensed under Creative Commons BY-SA-NC." in license_readme, "upstream license declaration drift")
        subprocess.run(["git", "-C", str(official_repo), "merge-base", "--is-ancestor", BALL_SOURCE, OFFICIAL_COMMIT], check=True)
        subprocess.run(["git", "-C", str(official_repo), "merge-base", "--is-ancestor", BALL_SOURCE, LICENSE_DECLARATION], check=True)
        subprocess.run(["git", "-C", str(official_repo), "merge-base", "--is-ancestor", LICENSE_DECLARATION, BALL_LATER_CHANGE], check=True)
        changes = _git(official_repo, "rev-list", "--ancestry-path", "--reverse", f"{BALL_SOURCE}..{OFFICIAL_COMMIT}", "--", BALL_SOURCE_PATH).decode().splitlines()
        _assert(changes == [BALL_LATER_CHANGE], "ball ancestry path drift")
    return result
