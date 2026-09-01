"""Validate retained model reconciliation against current local inputs."""

from __future__ import annotations

import hashlib
import json
import sys
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.reconcile_models import LOCAL_ROOT, compiled_manifest, digest_json  # noqa: E402

REPORT = ROOT / "microduck_contract" / "model" / "reconciliation-v1.json"
LOCK = ROOT / "microduck_contract" / "model" / "reconciliation-v1.lock.json"
AUTHORITY_COMMIT = "109e06d4ce4921b635c5609e5304079fc30960ae"


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    report = json.loads(REPORT.read_text())
    lock = json.loads(LOCK.read_text())
    assert report["schema_version"] == "microduck.model-reconciliation/v1"
    assert report["official_authority"]["commit"] == AUTHORITY_COMMIT
    assert report["generation"]["mujoco_version"] == metadata.version("mujoco")
    assert report["unresolved_divergences"] == []
    assert [row["path"] for row in report["deferred_divergences"]] == ["ball.xml"]
    assert lock["report_sha256"] == sha256(REPORT)
    assert lock["official_commit"] == AUTHORITY_COMMIT

    for row in report["source_comparison"]["files"]:
        path = LOCAL_ROOT / row["path"]
        assert sha256(path) == row["local_sha256"]
        if row["path"] == "ball.xml":
            assert row["classification"] == "unresolved-divergence-outside-slice"
            assert row["local_sha256"] != row["official_sha256"]
        else:
            assert row["classification"] == "byte-identical-input"
            assert row["local_sha256"] == row["official_sha256"]
    for variant, row in report["variants"].items():
        assert row["input_classification"] == "byte-identical-input"
        assert row["compiled_classification"] == "semantically-identical-compiled-model"
        assert row["differing_sections"] == []
        actual = compiled_manifest(LOCAL_ROOT / row["root"])
        assert digest_json(actual) == row["local_manifest_sha256"]
        assert row["local_manifest_sha256"] == row["official_manifest_sha256"]
        print(
            f"{variant}: {actual['counts']['nbody']} bodies, "
            f"{actual['counts']['njnt']} joints, {actual['counts']['nu']} actuators"
        )
    print("OK - retained official/local model reconciliation is current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
