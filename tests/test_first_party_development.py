"""Fail-closed tests for first-party origin, digests, seed, and visibility."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
os.sys.path.insert(0, os.fspath(ROOT))

import train  # noqa: E402
from evaluator.first_party_development import validate_suite  # noqa: E402
from experiments.first_party.development import (  # noqa: E402
    AdmissionError, ORIGIN, RECEIPT_ROOT, git, sha256,
    stable_json_bytes, validate_artifact_admission,
)

with mock.patch.object(train.gs, "init") as init:
    train._init_genesis("metal", 26090401)
    assert init.call_args.kwargs["seed"] == 26090401
    assert init.call_args.kwargs["backend"] == train.gs.metal

suite = json.loads((ROOT / "evaluator/first-party-development-suite-v1.json").read_text())
validate_suite(suite)
bad_suite = json.loads(json.dumps(suite))
bad_suite["held_out"] = True
try:
    validate_suite(bad_suite)
except AssertionError:
    pass
else:
    raise AssertionError("held-out first-party suite accepted")

RECEIPT_ROOT.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix="admission-test-", dir=RECEIPT_ROOT) as temp:
    root = Path(temp)
    frozen = root / "FROZEN_RUN.json"
    config = root / "cfgs.pkl"
    checkpoint = root / "source-checkpoint.pt"
    frozen.write_bytes(stable_json_bytes({
        "source_revision": git("rev-parse", "HEAD^{commit}"),
        "source_files": {"AGENTS.md": sha256(ROOT / "AGENTS.md")},
    }))
    config.write_bytes(b"config")
    checkpoint.write_bytes(b"checkpoint")
    record = {
        "schema_version": "microduck.first-party-artifact-admission/v1",
        "origin": ORIGIN, "resume": None,
        "source_revision": git("rev-parse", "HEAD^{commit}"),
        "frozen_run": {"path": frozen.relative_to(ROOT).as_posix(), "sha256": sha256(frozen)},
        "training_config": {"path": config.relative_to(ROOT).as_posix(), "sha256": sha256(config)},
        "checkpoint": {"path": checkpoint.relative_to(ROOT).as_posix(), "sha256": sha256(checkpoint)},
    }
    admission = root / "ARTIFACT_ADMISSION.json"
    admission.write_bytes(stable_json_bytes(record))
    validate_artifact_admission(admission)
    record["origin"] = "official_download"
    admission.write_bytes(stable_json_bytes(record))
    try:
        validate_artifact_admission(admission)
    except AdmissionError:
        pass
    else:
        raise AssertionError("wrong artifact origin accepted")
    record["origin"] = ORIGIN
    admission.write_bytes(stable_json_bytes(record))
    checkpoint.write_bytes(b"tampered")
    try:
        validate_artifact_admission(admission)
    except AdmissionError:
        pass
    else:
        raise AssertionError("tampered checkpoint accepted")
    checkpoint.unlink()
    checkpoint.symlink_to(ROOT / "tests/fixtures/evaluator/zero-policy.onnx")
    record["checkpoint"]["sha256"] = sha256(checkpoint)
    admission.write_bytes(stable_json_bytes(record))
    try:
        validate_artifact_admission(admission)
    except AdmissionError:
        pass
    else:
        raise AssertionError("symlink checkpoint accepted")

bad_latency = json.loads(json.dumps(suite["cases"][0]))
bad_latency["task_id"] = suite["task_id"]
bad_latency["synthetic_inference_latency_ms"] = 0.0
from evaluator.core import EvaluatorCore  # noqa: E402
with mock.patch.object(EvaluatorCore, "reset"):
    core = object.__new__(EvaluatorCore)
    core.task_id = suite["task_id"]
    core.proof_class = "first_party_development"
    try:
        core.run_case(bad_latency)
    except Exception as exc:
        assert "measured inference latency" in str(exc)
    else:
        raise AssertionError("synthetic first-party latency accepted")

print("first-party development admission verified: seeded init, origin/digest/symlink rejection, held-out boundary")
