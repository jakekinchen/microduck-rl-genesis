"""Negative probes for every bound seventh-pilot proposal value."""

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
PROPOSAL = ROOT / "experiments/m5/seventh-pilot-proposal-v1.json"
VALIDATOR = ROOT / "scripts/validate_m5_seventh_pilot_proposal.py"

spec = importlib.util.spec_from_file_location("validate_m5_seventh_pilot_proposal", VALIDATOR)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

proposal = json.loads(PROPOSAL.read_text())
module.validate_proposal(proposal, verify_local_inputs=True)
harness_text = (ROOT / proposal["inputs"]["pilot_harness"]["path"]).read_text()

for historical_rate in ("1.62", "1.656", "1.98", "4.408062"):
    try:
        module.validate_harness_price(
            proposal,
            harness_text.replace("PRICE_USD_PER_HOUR=2.388", f"PRICE_USD_PER_HOUR={historical_rate}"),
        )
    except AssertionError as exc:
        assert str(exc) == "pilot harness price/catalog rate disagreement"
    else:
        raise AssertionError(f"historical rate {historical_rate} was accepted")

module.validate_harness_self_attestation(proposal, harness_text)
for old_name in ("run_m5_cuda_pilot.sh", "run_m5_cuda_pilot_5.sh", "run_m5_cuda_pilot_6.sh"):
    try:
        module.validate_harness_self_attestation(
            proposal,
            harness_text.replace("run_m5_cuda_pilot_7.sh", old_name),
        )
    except AssertionError:
        pass
    else:
        raise AssertionError(f"prior harness alias was accepted: {old_name}")

module.validate_readiness_protocol(proposal, harness_text)
candidate = copy.deepcopy(proposal)
candidate["readiness_protocol"]["required_consecutive_polls"] = 2
try:
    module.validate_readiness_protocol(candidate, harness_text)
except AssertionError as exc:
    assert str(exc) == "consecutive-poll count drift"
else:
    raise AssertionError("two-poll readiness protocol was accepted")

candidate = copy.deepcopy(proposal)
candidate["readiness_protocol"]["advertised_boot_time_is_estimate_only"] = False
try:
    module.validate_readiness_protocol(candidate, harness_text)
except AssertionError as exc:
    assert str(exc) == "boot estimate became readiness proof"
else:
    raise AssertionError("advertised boot time was accepted as readiness proof")

candidate = copy.deepcopy(proposal)
candidate["readiness_protocol"]["minimum_seconds_between_qualifying_polls"] = 1
try:
    module.validate_readiness_protocol(candidate, harness_text)
except AssertionError as exc:
    assert str(exc) == "poll interval drift"
else:
    raise AssertionError("weakened readiness poll interval was accepted")

try:
    module.validate_readiness_protocol(
        proposal,
        harness_text.replace("MINIMUM_FREE_DISK_GB=8", "MINIMUM_FREE_DISK_GB=1"),
    )
except AssertionError as exc:
    assert str(exc) == "harness disk threshold drift"
else:
    raise AssertionError("weakened harness disk threshold was accepted")

with tempfile.TemporaryDirectory(prefix="m5-seventh-harness-native-") as temp_dir:
    temp = Path(temp_dir)
    input_root = temp / "input"
    receipt_root = temp / "receipt"
    tool_root = temp / "bin"
    workspace_root = temp / "workspace"
    input_root.mkdir()
    tool_root.mkdir()
    workspace_root.mkdir()
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
            "WORKSPACE_ROOT": str(workspace_root),
        },
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    terminal = json.loads((receipt_root / "TERMINAL_STATUS.json").read_text())
    assert terminal["failure_stage"] == "host-nvidia-smi"
    disk = json.loads((receipt_root / "disk-preflight.json").read_text())
    assert disk["minimum_free_disk_gb"] == 8
    assert disk["passed"] is True
    retained_harness = receipt_root / harness_path.name
    assert retained_harness.read_bytes() == harness_path.read_bytes()
    expected_harness_sha256 = proposal["inputs"]["pilot_harness"]["sha256"].removeprefix("sha256:")
    assert hashlib.sha256(retained_harness.read_bytes()).hexdigest() == expected_harness_sha256
    assert (receipt_root / "harness-sha256.txt").read_text().split()[0] == expected_harness_sha256
    for old_name in ("run_m5_cuda_pilot.sh", "run_m5_cuda_pilot_5.sh", "run_m5_cuda_pilot_6.sh"):
        assert not (input_root / old_name).exists()
        assert not (receipt_root / old_name).exists()


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
    raise AssertionError("mutated seventh-pilot proposal was accepted")


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

candidate = copy.deepcopy(proposal)
candidate["workspace"]["retry_allowed"] = True
rejected(candidate)

for failed_type in sorted(module.FAILED_TYPES | module.UNAVAILABLE_TYPES):
    candidate = copy.deepcopy(proposal)
    candidate["catalog_snapshot"]["type"] = failed_type
    candidate["container_dry_run"]["selected_type"] = failed_type
    candidate["container_dry_run"]["command"] = candidate["container_dry_run"]["command"].replace(
        module.SELECTED_TYPE, failed_type
    )
    rejected(candidate)

assert scalar_probes >= 190
assert deletion_probes >= scalar_probes

print(
    "M5 seventh-pilot proposal fail-closed probes passed: "
    f"{scalar_probes} scalar mutations, {deletion_probes} deletions, "
    "extra-field, explicit compute-authority, seventh-retry, prior-type, "
    "historical-rate, readiness-window, consecutive-poll, poll-interval, "
    "disk-threshold, and prior-alias rejection with native-name receipt self-attestation"
)
