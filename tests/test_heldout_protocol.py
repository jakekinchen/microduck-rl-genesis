"""Verify held-out seeds stay unrealized until post-freeze public randomness."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, os.fspath(ROOT))
from evaluator.heldout import PROTOCOL_PATH, realize_seeds, validate_protocol  # noqa: E402

protocol = json.loads(PROTOCOL_PATH.read_text())
validate_protocol(protocol)
kwargs = {
    "candidate_sha256": "sha256:" + "12" * 32,
    "candidate_frozen_at": "2026-01-01T00:00:00Z",
    "beacon_output": "ab" * 64,
    "beacon_published_at": "2026-01-01T00:01:00Z",
}
first = realize_seeds(protocol, **kwargs)
second = realize_seeds(protocol, **kwargs)
assert first == second and len(first) == 5 and len(set(first)) == 5
public = set(json.loads((ROOT / "microduck_contract/tasks/walking-v1.json").read_text())["acceptance"]["seeds"])
assert not public.intersection(first)
try:
    realize_seeds(protocol, **{**kwargs, "beacon_published_at": "2025-12-31T23:59:59Z"})
except ValueError:
    pass
else:
    raise AssertionError("pre-freeze beacon was accepted")
try:
    realize_seeds(protocol, **{**kwargs, "beacon_output": "not-a-beacon"})
except ValueError:
    pass
else:
    raise AssertionError("malformed beacon was accepted")
assert protocol["state"] == "preregistered_unrealized"
assert not protocol["beacon"]["live_value_committed"]
print("held-out protocol verified: post-freeze derivation only, no live seed realized")
