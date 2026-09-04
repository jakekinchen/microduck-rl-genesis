"""Reject promotion or drift in retained local provenance archaeology."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from artifact_contract.local_provenance_archaeology import validate_local_provenance_archaeology

RECEIPT = ROOT / "receipts/m6/provenance/20260904-local-provenance-archaeology-v2"
validate_local_provenance_archaeology(RECEIPT, ROOT)


def rejected(filename: str, mutate) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        copied = Path(temporary) / "receipt"
        shutil.copytree(RECEIPT, copied)
        target = copied / filename
        value = json.loads(target.read_text())
        mutate(value)
        target.write_text(json.dumps(value))
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        manifest = copied / "SHA256SUMS"
        lines = manifest.read_text().splitlines()
        manifest.write_text("\n".join(
            f"{digest}  ./{filename}" if line.endswith(f"  ./{filename}") else line
            for line in lines
        ) + "\n")
        try:
            validate_local_provenance_archaeology(copied, ROOT)
        except AssertionError:
            return
        raise AssertionError("invalid local provenance archaeology mutation accepted")


rejected("SEARCH_RESULT.json", lambda value: value.__setitem__("result", "all_files_resolved"))
rejected("SEARCH_RESULT.json", lambda value: value["actions"].__setitem__("onnx_loaded", True))
rejected("ball-source-chain.json", lambda value: value["exact_public_source"].__setitem__("commit", "0" * 40))
rejected("ball-source-chain.json", lambda value: value["license"].__setitem__("upstream_declaration_readme_sha256", "0" * 64))
rejected("ball-source-chain.json", lambda value: value["license"].__setitem__("scope", "code only"))
rejected("genesis-target-history.json", lambda value: value["targets"][0].__setitem__("history_commit_count", 2))
rejected("genesis-target-history.json", lambda value: value["history_scope"].__setitem__("commit_count", 153))
rejected("genesis-target-history.json", lambda value: value["history_scope"].__setitem__("dynamic_refs_excluded", False))
rejected("remote-authority-search.json", lambda value: value.__setitem__("result", "policy_authority_found"))
rejected("remote-authority-search.json", lambda value: value["repositories"].pop("meniuniu/microduck-rl-genesis"))
rejected("remote-authority-search.json", lambda value: value["repositories"]["Macmachi/microduck-rl-genesis"].__setitem__("target_files_changed_only_in_root_commit", False))
rejected("remote-authority-search.json", lambda value: value["repositories"]["meniuniu/microduck-rl-genesis"].__setitem__("original_policy_statement", "outputs of the macOS run"))
rejected("remote-authority-search.json", lambda value: value["repositories"]["meniuniu/microduck-rl-genesis"].__setitem__("separate_policy_sha256", "0" * 64))
rejected("media-metadata.json", lambda value: value["files"]["demo/apercu.gif"].__setitem__("sha256", "0" * 64))
rejected("media-metadata.json", lambda value: value["files"]["demo/microduck-parcours-30s.mp4"].__setitem__("authority", "accepted"))

print("M6 local provenance archaeology and negative promotion probes verified")
