"""Validate the terminal official-walking authority result and safe inspector."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "microduck_contract/policies/official-walking-authority-v1.json"
LOCK = ROOT / "microduck_contract/policies/official-walking-authority-v1.lock.json"
SCHEMA = ROOT / "microduck_contract/policies/official-walking-authority-v1.schema.json"
INSPECTOR = ROOT / "scripts/inspect_onnx_authority.py"

spec = importlib.util.spec_from_file_location("onnx_authority_inspector", INSPECTOR)
assert spec is not None and spec.loader is not None
inspector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inspector)

value = json.loads(RESULT.read_text())
schema = json.loads(SCHEMA.read_text())
assert schema["properties"]["schema_version"]["const"] == value["schema_version"]
assert schema["properties"]["result_id"]["const"] == value["result_id"]
assert value["status"] == "official_policy_authority_missing"
assert len(value["missing_authority"]) >= 5
assert all(action is False for action in value["actions"].values())

candidates = {item["candidate_id"]: item for item in value["candidates"]}
hub = candidates["official-huggingface-alpha-walking-current"]
official = candidates["official-runtime-alpha-walking-current"]
assert hub["disposition"] == "rejected_provenance_incomplete"
assert hub["sha256"] == official["sha256"]
assert hub["manifest_binding"]["obs_len"] == 61
assert hub["manifest_binding"]["action_len"] == 14
assert official["disposition"] == "rejected_provenance_incomplete"
assert official["inspection"]["input"]["shape"] == [1, 61]
assert official["inspection"]["output"]["shape"] == [1, 14]
assert official["inspection"]["normalizer_frontend"]["detected"]
assert official["inspection"]["metadata_run_path"] == "None"
assert candidates["genesis-repository-velocity"]["disposition"] == "rejected_not_official_mjlab"
assert candidates["genesis-m0-apple-smoke-walking"]["disposition"] == "rejected_not_official_mjlab"

lock = json.loads(LOCK.read_text())
assert lock["result_id"] == value["result_id"]
assert lock["status"] == value["status"]
assert lock["result_sha256"] == inspector.sha256_bytes(RESULT.read_bytes())

# Exercise only protobuf parsing against the retained synthetic fixture. An
# explicitly supplied official artifact is also checked against the frozen
# digest, but never executed.
fixture = inspector.inspect(ROOT / "tests/fixtures/evaluator/zero-policy.onnx")
assert fixture["inspection_mode"] == "protobuf_structure_only_no_execute"
assert fixture["inputs"][0]["shape"] == [1, 61]
assert fixture["outputs"][0]["shape"] == [1, 14]

external = os.environ.get("OFFICIAL_WALKING_ONNX")
if external:
    observed = inspector.inspect(Path(external))
    assert observed["sha256"] == official["sha256"]
    assert observed["inputs"][0]["shape"] == [1, 61]
    assert observed["outputs"][0]["shape"] == [1, 14]
    assert observed["normalizer_frontend"]["detected"]

print(
    "official walking authority verified: terminal missing-authority result, "
    "official artifact not executed"
)
