"""Validate real immutable candidates while retaining incomplete-role blockers."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from artifact_contract.validator import validate_policy_manifest, validate_resolution_bundle

CANDIDATES = ROOT / "artifact_contract/real-candidates"
OFFICIAL = CANDIDATES / "official-alpha-walking-088524a"
COMMUNITY = CANDIDATES / "community-rough-walk-e-fa7b27e"

official = validate_resolution_bundle(OFFICIAL, "official")
community = validate_resolution_bundle(COMMUNITY, "community")

assert official["bindings"]["normalized_onnx"]["sha256"] == "sha256:e36332d383997d51401897734cd3e79cf5038406feddb18b4d57ecfb141daa6c"
assert official["validation"]["bound_roles"] == ["license", "normalized_onnx"]
assert official["validation"]["missing_roles"] == ["bam", "evaluator", "evidence", "exporter", "model", "normalizer", "source_checkpoint", "task"]
assert community["bindings"]["normalized_onnx"]["sha256"] == "sha256:5aa423bd693e431b19e2ead77f99cbae6184e40a529eb2f7c1b4f85bb7f57040"
assert community["validation"]["bound_roles"] == ["bam", "exporter", "license", "model", "normalized_onnx", "task"]
assert community["validation"]["missing_roles"] == ["evaluator", "evidence", "normalizer", "source_checkpoint"]

for resolution in (official, community):
    assert resolution["validation"]["policy_manifest_v2"] == "rejected_incomplete"
    assert resolution["validation"]["formal_manifest_emitted"] is False
    assert resolution["authority"] == "none"

try:
    validate_policy_manifest(OFFICIAL / "policy-manifest-v2-resolution.json", "official")
except AssertionError:
    pass
else:
    raise AssertionError("an incomplete role-resolution report was accepted as policy manifest v2")


def rejected(source: Path, mutate) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        copied = Path(temporary) / "candidate"
        shutil.copytree(source, copied)
        resolution_path = copied / "policy-manifest-v2-resolution.json"
        value = json.loads(resolution_path.read_text())
        mutate(value, copied)
        resolution_path.write_text(json.dumps(value))
        try:
            validate_resolution_bundle(copied, value["source_class"])
        except AssertionError:
            return
        raise AssertionError("invalid real-candidate resolution mutation accepted")


rejected(OFFICIAL, lambda value, _: value["bindings"]["normalized_onnx"].__setitem__("sha256", "sha256:" + "0" * 64))
rejected(OFFICIAL, lambda value, _: value["bindings"]["task"].__setitem__("blockers", []))
rejected(COMMUNITY, lambda value, _: value["lifecycle"].__setitem__("activation", "authorized"))
rejected(COMMUNITY, lambda value, _: value.__setitem__("authority", "artifact_attributed"))
rejected(COMMUNITY, lambda value, _: value["bindings"]["exporter"]["source"].__setitem__("url", "https://example.invalid/export.py"))
rejected(COMMUNITY, lambda _value, copied: (copied / "unbound.bin").write_bytes(b"unbound"))

print("real official/community bytes resolved against manifest v2 with missing roles fail-closed")
