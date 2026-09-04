"""Negative probes for every bound fifth-pilot proposal value."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[1]
PROPOSAL = ROOT / "experiments/m5/fifth-pilot-proposal-v1.json"
VALIDATOR = ROOT / "scripts/validate_m5_fifth_pilot_proposal.py"

spec = importlib.util.spec_from_file_location("validate_m5_fifth_pilot_proposal", VALIDATOR)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

proposal = json.loads(PROPOSAL.read_text())
module.validate_proposal(proposal, verify_local_inputs=True)
harness_text = (ROOT / proposal["inputs"]["pilot_harness"]["path"]).read_text()
module.validate_harness_price(proposal, harness_text)

try:
    module.validate_harness_price(
        proposal,
        harness_text.replace("PRICE_USD_PER_HOUR=1.656", "PRICE_USD_PER_HOUR=1.62"),
    )
except AssertionError as exc:
    assert str(exc) == "pilot harness price/catalog rate disagreement"
else:
    raise AssertionError("historical fourth-pilot rate was accepted by fifth-pilot harness validation")

module.validate_harness_self_attestation(proposal, harness_text)
try:
    module.validate_harness_self_attestation(
        proposal,
        harness_text.replace("run_m5_cuda_pilot_5.sh", "run_m5_cuda_pilot.sh"),
    )
except AssertionError:
    pass
else:
    raise AssertionError("fourth-harness alias was accepted by fifth-pilot self-attestation validation")

with tempfile.TemporaryDirectory(prefix="m5-fifth-harness-native-") as temp_dir:
    temp = Path(temp_dir)
    input_root = temp / "input"
    receipt_root = temp / "receipt"
    tool_root = temp / "bin"
    input_root.mkdir()
    tool_root.mkdir()
    for tool in ("cp", "date", "find", "mkdir", "mktemp", "mv", "python3", "sha256sum", "sort", "tee", "xargs"):
        source = shutil.which(tool)
        assert source is not None, f"required local failure-probe tool unavailable: {tool}"
        (tool_root / tool).symlink_to(source)
    for bundle_name in ("genesis.bundle", "official-walking.bundle", "official-backflip.bundle"):
        (input_root / bundle_name).write_bytes(b"nonempty-local-failure-probe")
    harness_path = ROOT / proposal["inputs"]["pilot_harness"]["path"]
    staged_harness = input_root / harness_path.name
    staged_harness.write_bytes(harness_path.read_bytes())
    result = subprocess.run(
        ["/bin/bash", str(harness_path)],
        env={
            "CONTRACT_COMMIT": "local-failure-probe",
            "INPUT_ROOT": str(input_root),
            "PATH": str(tool_root),
            "RECEIPT_ROOT": str(receipt_root),
            "SOURCE_ROOT": str(temp / "src"),
            "VENV_ROOT": str(temp / "venvs"),
            "WORKSPACE_ROOT": str(temp / "workspace"),
        },
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    terminal = json.loads((receipt_root / "TERMINAL_STATUS.json").read_text())
    assert terminal["failure_stage"] == "host-nvidia-smi"
    retained_harness = receipt_root / harness_path.name
    assert retained_harness.read_bytes() == harness_path.read_bytes()
    expected_harness_sha256 = proposal["inputs"]["pilot_harness"]["sha256"].removeprefix("sha256:")
    assert hashlib.sha256(retained_harness.read_bytes()).hexdigest() == expected_harness_sha256
    assert (receipt_root / "harness-sha256.txt").read_text().split()[0] == expected_harness_sha256
    assert not (input_root / "run_m5_cuda_pilot.sh").exists()
    assert not (receipt_root / "run_m5_cuda_pilot.sh").exists()


def leaf_paths(value: Any, path: tuple[Any, ...] = ()) -> Iterator[tuple[Any, ...]]:
    if isinstance(value, dict):
        for key, item in value.items():
            yield from leaf_paths(item, path + (key,))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from leaf_paths(item, path + (index,))
    else:
        yield path


def all_paths(value: Any, path: tuple[Any, ...] = ()) -> Iterator[tuple[Any, ...]]:
    if isinstance(value, dict):
        for key, item in value.items():
            yield path + (key,)
            yield from all_paths(item, path + (key,))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield path + (index,)
            yield from all_paths(item, path + (index,))


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
        return value + 0.001
    if isinstance(value, str):
        return value + "-drift"
    raise AssertionError(f"unsupported scalar type: {type(value)}")


def rejected(candidate: Any) -> None:
    try:
        module.validate_proposal(candidate, verify_local_inputs=False)
    except AssertionError:
        return
    raise AssertionError("mutated fifth-pilot proposal was accepted")


scalar_probes = 0
for path in leaf_paths(proposal):
    candidate = copy.deepcopy(proposal)
    parent, key = parent_at(candidate, path)
    parent[key] = mutated_scalar(parent[key])
    rejected(candidate)
    scalar_probes += 1

deletion_probes = 0
for path in all_paths(proposal):
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

assert scalar_probes >= 140
assert deletion_probes >= scalar_probes

print(
    "M5 fifth-pilot proposal fail-closed probes passed: "
    f"{scalar_probes} scalar mutations, {deletion_probes} deletions, "
    "extra-field, explicit compute-authority, historical harness-rate, and "
    "fourth-alias rejection with native-name receipt self-attestation"
)
