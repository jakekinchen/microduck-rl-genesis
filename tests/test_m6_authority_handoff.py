"""Verify the M6 authority handoff and rehashed promotion rejection."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from artifact_contract.authority_handoff import validate_authority_handoff

RECEIPT = ROOT / "receipts/m6/authority/20260904-external-handoff-v1"
packet = validate_authority_handoff(RECEIPT, ROOT)
assert sorted(packet["candidates"]["official"]["missing_roles"]) == [
    "bam", "evaluator", "evidence", "exporter", "model", "normalizer", "source_checkpoint", "task"
]
assert sorted(packet["candidates"]["community"]["missing_roles"]) == [
    "evaluator", "evidence", "normalizer", "source_checkpoint"
]
assert all(value is False for value in packet["actions"].values())
assert packet["repo_owned_closure_audit"]["roles_closed"] == []


def rehash_result(directory: Path, name: str) -> None:
    digest = hashlib.sha256((directory / name).read_bytes()).hexdigest()
    lines = (directory / "SHA256SUMS").read_text().splitlines()
    (directory / "SHA256SUMS").write_text("\n".join(
        f"{digest}  ./{name}" if line.endswith(f"./{name}") else line for line in lines
    ) + "\n")


def packet_rejected(mutator) -> None:
    with tempfile.TemporaryDirectory(prefix="microduck-authority-packet-mutation-") as temp:
        copied = Path(temp) / "receipt"
        shutil.copytree(RECEIPT, copied)
        path = copied / "AUTHORITY_PACKET.json"
        value = json.loads(path.read_text())
        mutator(value)
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
        rehash_result(copied, path.name)
        try:
            validate_authority_handoff(copied, ROOT)
        except AssertionError:
            return
        raise AssertionError("rehashed authority packet promotion accepted")


def file_rejected(name: str, replacement: str) -> None:
    with tempfile.TemporaryDirectory(prefix="microduck-authority-file-mutation-") as temp:
        copied = Path(temp) / "receipt"
        shutil.copytree(RECEIPT, copied)
        (copied / name).write_text(replacement)
        rehash_result(copied, name)
        try:
            validate_authority_handoff(copied, ROOT)
        except AssertionError:
            return
        raise AssertionError("rehashed authority support-file mutation accepted")


packet_rejected(lambda value: value["candidates"]["official"]["missing_roles"].pop("bam"))
packet_rejected(lambda value: value["candidates"]["community"]["missing_roles"]["evidence"].__setitem__("acceptable_immutable_evidence", []))
packet_rejected(lambda value: value["actions"].__setitem__("third_party_contacted", True))
packet_rejected(lambda value: value["actions"].__setitem__("github_pushed", True))
packet_rejected(lambda value: value["publication_plan"].__setitem__("status", "executed"))
packet_rejected(lambda value: value["repo_owned_closure_audit"]["roles_closed"].append("evaluator"))
packet_rejected(lambda value: value["authority_boundary"]["requires_new_explicit_human_authority"].pop())
packet_rejected(lambda value: value.__setitem__("decision", "continue_local_search"))
file_rejected("REQUEST-POLLEN-UNSENT.md", "sent\n")
file_rejected("PUBLICATION-PLAN.md", "published\n")
file_rejected("REPO-OWNED-CLOSURE-AUDIT.md", "role closed\n")
file_rejected("EVIDENCE_BOUNDARY.txt", "contacted and published\n")

print("M6 external authority handoff and negative promotion probes verified")
