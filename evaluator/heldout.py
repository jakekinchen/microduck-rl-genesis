"""Validate and synthetically exercise the blinded held-out protocol."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from evaluator.core import sha256

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = Path(__file__).with_name("heldout-protocol-v1.json")


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamps must include an offset")
    return parsed


def validate_protocol(protocol: dict[str, Any]) -> None:
    if protocol["state"] != "preregistered_unrealized":
        raise AssertionError("held-out protocol was unexpectedly realized")
    if protocol["public_acceptance_seeds_are_held_out"]:
        raise AssertionError("public seeds cannot be called held-out")
    if protocol["candidate_policy_allowed_before_realization"]:
        raise AssertionError("candidate use before realization is forbidden")
    for relative, expected in protocol["bindings"].items():
        if sha256(ROOT / relative) != expected:
            raise AssertionError(f"held-out binding drift: {relative}")


def realize_seeds(
    protocol: dict[str, Any], *, candidate_sha256: str,
    candidate_frozen_at: str, beacon_output: str, beacon_published_at: str,
) -> list[int]:
    validate_protocol(protocol)
    if not candidate_sha256.startswith("sha256:") or len(candidate_sha256) != 71:
        raise ValueError("invalid candidate digest")
    if len(beacon_output) != 128 or any(c not in "0123456789abcdef" for c in beacon_output):
        raise ValueError("invalid beacon output")
    if parse_time(beacon_published_at) <= parse_time(candidate_frozen_at):
        raise ValueError("beacon must be published after candidate freeze")
    task = json.loads((ROOT / "microduck_contract/tasks/walking-v1.json").read_text())
    excluded = set(task["acceptance"]["seeds"])
    for path in (ROOT / "evaluator/development-suite-v1.json", ROOT / "evaluator/case-matrix-v1.json"):
        excluded.update(case["seed"] for case in json.loads(path.read_text())["cases"])
    prefix = (
        protocol["protocol_id"].encode() + b"\0" + candidate_sha256.encode()
        + b"\0" + beacon_output.encode() + b"\0"
    )
    seeds: list[int] = []
    counter = 0
    while len(seeds) < protocol["partition"]["heldout_seed_count"]:
        digest = hashlib.sha256(prefix + counter.to_bytes(8, "big")).digest()
        seed = int.from_bytes(digest[:8], "big") % 2_147_483_646 + 1
        if seed not in excluded and seed not in seeds:
            seeds.append(seed)
        counter += 1
    return seeds
