#!/usr/bin/env python3
"""Generate the pinned official-MuJoCo/BAM 14-servo trajectory fixture."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from importlib import metadata
from pathlib import Path

import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_COMMIT = "62bd8ce12154340be97e06f7f41a0ca8f116d967"
AUTHORITY_URL = "https://github.com/Rhoban/bam.git"
PARAMETER_PATH = ROOT / "microduck" / "assets" / "xl330_m6.json"
SCENE_PATH = ROOT / "microduck" / "assets" / "microduck" / "scene_walk.xml"
MODEL_LOCK_PATH = (
    ROOT / "microduck_contract" / "model" / "microduck-walk-v1.lock.json"
)
OPEN_LOOP_FIXTURE_PATH = (
    ROOT
    / "microduck_contract"
    / "actuator"
    / "fixtures"
    / "bam-m6-xl330-v1-open-loop.json"
)
DEFAULT_OUTPUT = (
    ROOT
    / "microduck_contract"
    / "actuator"
    / "fixtures"
    / "bam-m6-xl330-v1-closed-loop.json"
)
JOINT_NAMES = (
    "left_hip_yaw",
    "left_hip_roll",
    "left_hip_pitch",
    "left_knee",
    "left_ankle",
    "neck_pitch",
    "head_pitch",
    "head_yaw",
    "head_roll",
    "right_hip_yaw",
    "right_hip_roll",
    "right_hip_pitch",
    "right_knee",
    "right_ankle",
)
HOME = (
    0.0,
    -0.0873,
    -0.4579,
    -0.0049,
    0.4530,
    0.3491,
    0.3491,
    0.0,
    0.0,
    0.0,
    0.0873,
    0.4579,
    0.0049,
    -0.4530,
)
DT = 0.005
N_STEPS = 120
VIN = 7.35
Z0 = 0.125


def command(*args: str, cwd: Path) -> str:
    return subprocess.check_output(args, cwd=cwd, text=True).strip()


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def verify_open_loop_authority(bam_repo: Path, head: str) -> dict:
    authority = json.loads(OPEN_LOOP_FIXTURE_PATH.read_text())["authority"]
    expected = {
        "commit": head,
        "tree": command("git", "rev-parse", "HEAD^{tree}", cwd=bam_repo),
        "parameter_sha256": sha256(PARAMETER_PATH),
        "bam/model.py": sha256(bam_repo / "bam" / "model.py"),
    }
    observed = {
        "commit": authority["commit"],
        "tree": authority["tree"],
        "parameter_sha256": authority["parameter_sha256"],
        "bam/model.py": authority["source_files"]["bam/model.py"],
    }
    if observed != expected:
        raise SystemExit(
            "closed-loop authority differs from approved open-loop fixture: "
            f"expected {expected}, observed {observed}"
        )
    return authority


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bam-repo", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    bam_repo = args.bam_repo.resolve()
    output = args.output.resolve()
    head = command("git", "rev-parse", "HEAD", cwd=bam_repo)
    if head != AUTHORITY_COMMIT:
        raise SystemExit(f"BAM authority mismatch: expected {AUTHORITY_COMMIT}, got {head}")
    if command("git", "status", "--porcelain", cwd=bam_repo):
        raise SystemExit("BAM authority checkout is dirty")
    open_loop_authority = verify_open_loop_authority(bam_repo, head)

    sys.path.insert(0, os.fspath(bam_repo))
    import bam  # noqa: PLC0415
    from bam.model import load_model  # noqa: PLC0415
    from bam.mujoco import MujocoController  # noqa: PLC0415

    if not Path(bam.__file__).resolve().is_relative_to(bam_repo):
        raise SystemExit(f"Imported BAM from wrong path: {bam.__file__}")

    model = mujoco.MjModel.from_xml_path(os.fspath(SCENE_PATH))
    model.opt.timestep = DT
    data = mujoco.MjData(model)
    for name in JOINT_NAMES:
        actuator = model.actuator(name)
        model.actuator_gaintype[actuator.id] = mujoco.mjtGain.mjGAIN_FIXED
        model.actuator_biastype[actuator.id] = mujoco.mjtBias.mjBIAS_NONE
        model.actuator_gainprm[actuator.id, :] = 0.0
        model.actuator_gainprm[actuator.id, 0] = 1.0
        model.actuator_biasprm[actuator.id, :] = 0.0
        model.actuator_forcerange[actuator.id] = [-10.0, 10.0]

    bam_model = load_model(os.fspath(PARAMETER_PATH))
    bam_model.actuator.kp = 200.0
    bam_model.actuator.vin = VIN
    controller = MujocoController(bam_model, list(JOINT_NAMES), model, data)
    data.qpos[0:3] = [0.0, 0.0, Z0]
    data.qpos[3:7] = [1.0, 0.0, 0.0, 0.0]
    for index, name in enumerate(JOINT_NAMES):
        data.qpos[model.jnt_qposadr[model.joint(name).id]] = HOME[index]
        controller.set_q_target(name, HOME[index])
    data.qvel[:] = 0.0
    mujoco.mj_forward(model, data)

    trajectory = []
    for step in range(N_STEPS):
        controller.update()
        mujoco.mj_step(model, data)
        trajectory.append(
            {
                "step": step + 1,
                "time_s": (step + 1) * DT,
                "base_z_m": float(data.qpos[2]),
                "joint_position_rad": [
                    float(data.qpos[model.jnt_qposadr[model.joint(name).id]])
                    for name in JOINT_NAMES
                ],
            }
        )

    payload = {
        "schema_version": "microduck.bam-closed-loop/v1",
        "profile": "bam-core-v1",
        "authority": {
            "repository_url": AUTHORITY_URL,
            "commit": head,
            "tree": command("git", "rev-parse", "HEAD^{tree}", cwd=bam_repo),
            "bam_mujoco_sha256": sha256(bam_repo / "bam" / "mujoco.py"),
            "bam_model_sha256": sha256(bam_repo / "bam" / "model.py"),
            "parameter_sha256": sha256(PARAMETER_PATH),
            "scene_sha256": sha256(SCENE_PATH),
            "model_lock_sha256": sha256(MODEL_LOCK_PATH),
            "open_loop_fixture_sha256": sha256(OPEN_LOOP_FIXTURE_PATH),
            "open_loop_authority_verified": {
                "parameter_sha256": open_loop_authority["parameter_sha256"],
                "bam_model_sha256": open_loop_authority["source_files"][
                    "bam/model.py"
                ],
            },
        },
        "generation": {
            "script": "scripts/generate_bam_closed_loop_fixture.py",
            "command": (
                "python scripts/generate_bam_closed_loop_fixture.py "
                "--bam-repo <clean-checkout-at-authority-commit>"
            ),
            "mujoco_version": metadata.version("mujoco"),
        },
        "configuration": {
            "physics_dt_s": DT,
            "steps": N_STEPS,
            "supply_voltage_v": VIN,
            "firmware_kp": 200.0,
            "joint_order": list(JOINT_NAMES),
            "home_joint_position_rad": list(HOME),
            "initial_base_position_m": [0.0, 0.0, Z0],
            "initial_base_quaternion_wxyz": [1.0, 0.0, 0.0, 0.0],
            "randomization": "none",
            "command_delay_steps": 0,
        },
        "tolerances": {
            "joint_abs_max_rad_all_steps": float(np.deg2rad(2.0)),
            "joint_abs_max_rad_at_step_60": float(np.deg2rad(3.0)),
            "base_z_abs_max_m_all_steps": 0.01,
            "base_z_abs_max_m_at_step_60": 0.005,
        },
        "trajectory": trajectory,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    try:
        display = output.relative_to(ROOT)
    except ValueError:
        display = output
    print(f"wrote {display} with {len(trajectory)} steps x {len(JOINT_NAMES)} joints")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
