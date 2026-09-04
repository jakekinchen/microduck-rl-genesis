"""Negative probes for every bound fourth-pilot proposal value."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[1]
PROPOSAL = ROOT / "experiments/m5/fourth-pilot-proposal-v1.json"
VALIDATOR = ROOT / "scripts/validate_m5_fourth_pilot_proposal.py"

spec = importlib.util.spec_from_file_location("validate_m5_fourth_pilot_proposal", VALIDATOR)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

proposal = json.loads(PROPOSAL.read_text())
module.validate_proposal(proposal, verify_local_inputs=True)


def leaf_paths(value: Any, path: tuple[Any, ...] = ()) -> Iterator[tuple[Any, ...]]:
    if isinstance(value, dict):
        for key, item in value.items():
            yield from leaf_paths(item, path + (key,))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from leaf_paths(item, path + (index,))
    else:
        yield path


def container_paths(value: Any, path: tuple[Any, ...] = ()) -> Iterator[tuple[Any, ...]]:
    if isinstance(value, dict):
        for key, item in value.items():
            yield path + (key,)
            yield from container_paths(item, path + (key,))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield path + (index,)
            yield from container_paths(item, path + (index,))


def parent_at(value: Any, path: tuple[Any, ...]) -> tuple[Any, Any]:
    current = value
    for key in path[:-1]:
        current = current[key]
    return current, path[-1]


def mutated_scalar(value: Any) -> Any:
    if isinstance(value, bool):
        return not value
    if isinstance(value, int):
        return value + 1
    if isinstance(value, float):
        return value + 0.01
    if isinstance(value, str):
        return value + "-drift"
    raise AssertionError(f"unsupported scalar type: {type(value)}")


def rejected(candidate: Any) -> None:
    try:
        module.validate_proposal(candidate, verify_local_inputs=False)
    except AssertionError:
        return
    raise AssertionError("mutated fourth-pilot proposal was accepted")


scalar_probes = 0
for path in leaf_paths(proposal):
    candidate = copy.deepcopy(proposal)
    parent, key = parent_at(candidate, path)
    parent[key] = mutated_scalar(parent[key])
    rejected(candidate)
    scalar_probes += 1

deletion_probes = 0
for path in container_paths(proposal):
    candidate = copy.deepcopy(proposal)
    parent, key = parent_at(candidate, path)
    del parent[key]
    rejected(candidate)
    deletion_probes += 1

candidate = copy.deepcopy(proposal)
candidate["unexpected"] = "field"
rejected(candidate)

candidate = copy.deepcopy(proposal)
candidate["compute_authorized"] = True
try:
    module.validate_proposal(candidate, verify_local_inputs=False)
except AssertionError as exc:
    assert str(exc) == "compute_authorized must remain false"
else:
    raise AssertionError("compute_authorized=true was accepted")

assert scalar_probes >= 100
assert deletion_probes >= scalar_probes

print(
    "M5 fourth-pilot proposal fail-closed probes passed: "
    f"{scalar_probes} scalar mutations, {deletion_probes} deletions, "
    "extra-field and explicit compute-authority rejection"
)
