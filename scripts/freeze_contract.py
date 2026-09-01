#!/usr/bin/env python3
"""Generate or verify deterministic snapshots of the local Microduck contract.

The snapshots are a candidate, repo-local contract. Cross-backend authority is
earned only when the official mjlab adapter and the reference evaluator consume
the same fixtures successfully.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_source_module(name: str, path: Path):
    """Load a pure-data source module without importing microduck.__init__."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


C = load_source_module("microduck_contract_constants", ROOT / "microduck" / "constants.py")
V = load_source_module("microduck_contract_velocity_cfg", ROOT / "microduck" / "velocity_cfg.py")

CONTRACT_ROOT = ROOT / "microduck_contract"
ROBOT_ASSET_ROOT = ROOT / "microduck" / "assets" / "microduck"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def stable_bundle(files: dict[str, str]) -> str:
    payload = "".join(f"{name}\0{digest}\n" for name, digest in sorted(files.items()))
    return f"sha256:{hashlib.sha256(payload.encode()).hexdigest()}"


def asset_bundle() -> dict[str, str]:
    files: dict[str, str] = {}
    for path in sorted(ROBOT_ASSET_ROOT.rglob("*")):
        # Contract locks describe source assets, never interpreter caches.  In
        # particular, compileall and normal imports may create __pycache__
        # entries under this tree; hashing those would make the lock depend on
        # the local Python build and command order.
        if (
            path.is_file()
            and "__pycache__" not in path.parts
            and path.suffix not in {".pyc", ".pyo"}
        ):
            files[path.relative_to(ROOT).as_posix()] = sha256(path)
    return files


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def snapshots() -> dict[Path, bytes]:
    assets = asset_bundle()
    common = {
        "schema_version": "microduck.model-lock/v1",
        "authority": "candidate-repo-local",
        "asset_bundle_sha256": stable_bundle(assets),
        "files": assets,
    }
    models = {
        "microduck-walk-v1": "microduck/assets/microduck/robot_walk.xml",
        "microduck-allcollisions-v1": "microduck/assets/microduck/robot_allcollisions.xml",
        "microduck-rollers-v1": "microduck/assets/microduck/robot_allcollisions_rollers.xml",
    }

    output: dict[Path, bytes] = {}
    for model_id, model_path in models.items():
        value = dict(common)
        value.update(
            {
                "model_id": model_id,
                "root_model": model_path,
                "root_sha256": sha256(ROOT / model_path),
            }
        )
        output[CONTRACT_ROOT / "model" / f"{model_id}.lock.json"] = json_bytes(value)

    observation = {
        "schema_version": "microduck.interface/v1",
        "interface_id": "microduck.obs.v1",
        "authority": "candidate-repo-local",
        "dtype": "float32",
        "shape": [1, C.NUM_OBS],
        "layout": [{"name": name, "size": size} for name, size in C.OBS_LAYOUT],
        "joint_order": list(C.JOINT_NAMES),
        "home_joint_position_rad": list(C.DEFAULT_JOINT_POS),
    }
    action = {
        "schema_version": "microduck.interface/v1",
        "interface_id": "microduck.action.v1",
        "authority": "candidate-repo-local",
        "dtype": "float32",
        "shape": [1, C.NUM_ACTIONS],
        "joint_order": list(C.JOINT_NAMES),
        "semantics": "unfiltered_delta_from_home_rad",
        "scale": V.ACTION_SCALE,
    }
    control = {
        "schema_version": "microduck.control/v1",
        "control_id": "microduck.control.50hz.v1",
        "authority": "candidate-repo-local",
        "control_hz": round(1.0 / (V.SIM_DT * V.DECIMATION)),
        "physics_dt_s": V.SIM_DT,
        "decimation": V.DECIMATION,
        "action_filter": "none",
    }
    output[CONTRACT_ROOT / "interface" / "observation-v1.json"] = json_bytes(observation)
    output[CONTRACT_ROOT / "interface" / "action-v1.json"] = json_bytes(action)
    output[CONTRACT_ROOT / "interface" / "control-v1.json"] = json_bytes(control)

    bam_source = Path(C.BAM_XL330_M6_JSON)
    bam = {
        "schema_version": "microduck.actuator-lock/v1",
        "actuator_id": "bam-m6-xl330-v1",
        "authority": "candidate-repo-local",
        "behavior_profile": "mjlab-deployed-v1",
        "parameter_file": bam_source.relative_to(ROOT).as_posix(),
        "parameter_sha256": sha256(bam_source),
        "firmware_kp": C.BAM_KP_FW,
        "supply_voltage_range_v": list(C.BAM_VIN_RANGE),
        "supply_voltage_floor_v": C.BAM_VIN_MIN,
        "voltage_drop_resistance_range_ohm": list(C.BAM_VIN_DROP_RESISTANCE_RANGE),
        "current_limit_a": C.XL330_MAX_CURRENT,
        "command_delay_physics_steps": [C.BAM_DELAY_MIN_LAG, C.BAM_DELAY_MAX_LAG],
        "golden_vectors": None,
        "cross_backend_conformance": "pending",
    }
    output[CONTRACT_ROOT / "actuator" / "bam-m6-xl330-v1.lock.json"] = json_bytes(bam)
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if snapshots differ")
    args = parser.parse_args()

    failures: list[str] = []
    for path, expected in snapshots().items():
        if args.check:
            actual = path.read_bytes() if path.exists() else b""
            if actual != expected:
                failures.append(path.relative_to(ROOT).as_posix())
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(expected)

    if failures:
        print("Contract snapshots are stale or missing:")
        for failure in failures:
            print(f"  - {failure}")
        print("Run: python scripts/freeze_contract.py")
        return 1
    print("Contract snapshots verified." if args.check else "Contract snapshots updated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
