"""Compare Genesis BAM-core against the pinned 14-servo MuJoCo fixture."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, os.fspath(ROOT))

import genesis as gs  # noqa: E402

from microduck.bam_actuator import BamActuator  # noqa: E402
from microduck.constants import (  # noqa: E402
    BAM_KP_FW,
    BAM_XL330_M6_JSON,
    DEFAULT_JOINT_POS,
    JOINT_NAMES,
    MICRODUCK_WALK_XML,
)

FIXTURE = (
    ROOT
    / "microduck_contract"
    / "actuator"
    / "fixtures"
    / "bam-m6-xl330-v1-closed-loop.json"
)
AUTHORITY_COMMIT = "62bd8ce12154340be97e06f7f41a0ca8f116d967"


def main() -> int:
    fixture = json.loads(FIXTURE.read_text())
    cfg = fixture["configuration"]
    assert cfg["joint_order"] == list(JOINT_NAMES)
    assert cfg["home_joint_position_rad"] == list(DEFAULT_JOINT_POS)
    assert fixture["profile"] == "bam-core-v1"
    assert fixture["authority"]["commit"] == AUTHORITY_COMMIT
    assert cfg["physics_dt_s"] == 0.005
    assert cfg["steps"] == 120
    assert cfg["randomization"] == "none"
    assert cfg["command_delay_steps"] == 0

    gs.init(backend=gs.cpu, logging_level="error")
    scene = gs.Scene(
        show_viewer=False,
        sim_options=gs.options.SimOptions(dt=cfg["physics_dt_s"], substeps=1),
        rigid_options=gs.options.RigidOptions(
            batch_dofs_info=True, iterations=100, ls_iterations=50
        ),
    )
    scene.add_entity(gs.morphs.Plane())
    robot = scene.add_entity(gs.morphs.MJCF(file=MICRODUCK_WALK_XML))
    scene.build(n_envs=1)
    joints = {joint.name: joint for joint in robot.joints}
    dofs = [joints[name].dof_start for name in JOINT_NAMES]
    actuator = BamActuator(
        robot,
        dofs,
        1,
        torch.device("cpu"),
        cfg["physics_dt_s"],
        json_path=BAM_XL330_M6_JSON,
        kp_fw=BAM_KP_FW,
        vin_range=(cfg["supply_voltage_v"], cfg["supply_voltage_v"]),
        vin_drop_resistance_range=(0.0, 0.0),
        delay_min_lag=0,
        delay_max_lag=0,
        quadratic_sign_gate=True,
    )
    actuator.vin_nominal[:] = cfg["supply_voltage_v"]
    actuator.vin_drop_resistance = None
    robot.set_pos(torch.tensor([cfg["initial_base_position_m"]]))
    robot.set_quat(torch.tensor([cfg["initial_base_quaternion_wxyz"]]))
    robot.zero_all_dofs_velocity()
    target = torch.tensor(DEFAULT_JOINT_POS, dtype=gs.tc_float).unsqueeze(0)
    robot.set_dofs_position(target, dofs)

    actual_q = []
    actual_z = []
    for _ in range(cfg["steps"]):
        robot.control_dofs_force(actuator.compute(target), dofs)
        scene.step()
        actual_q.append(robot.get_dofs_position(dofs)[0].numpy().copy())
        actual_z.append(float(robot.get_pos()[0, 2]))

    expected_q = np.asarray(
        [row["joint_position_rad"] for row in fixture["trajectory"]]
    )
    expected_z = np.asarray([row["base_z_m"] for row in fixture["trajectory"]])
    actual_q = np.asarray(actual_q)
    actual_z = np.asarray(actual_z)
    joint_error = np.abs(actual_q - expected_q)
    z_error = np.abs(actual_z - expected_z)
    step_60 = 59
    tolerances = fixture["tolerances"]

    per_joint = joint_error.max(axis=0)
    print("maximum joint error over 120 steps:")
    for joint_index, (name, error) in enumerate(
        zip(JOINT_NAMES, per_joint, strict=True)
    ):
        worst_step = int(joint_error[:, joint_index].argmax()) + 1
        print(
            f"  {name:16s} {np.rad2deg(error):.3f} deg "
            f"at step {worst_step:3d}"
        )
    print(f"all-step joint max: {np.rad2deg(joint_error.max()):.3f} deg")
    print(f"step-60 joint max: {np.rad2deg(joint_error[step_60].max()):.3f} deg")
    print(f"all-step base-z max: {z_error.max() * 1000:.3f} mm")
    print(f"step-60 base-z error: {z_error[step_60] * 1000:.3f} mm")

    failures = []
    if joint_error.max() > tolerances["joint_abs_max_rad_all_steps"]:
        step_index, joint_index = np.unravel_index(
            joint_error.argmax(), joint_error.shape
        )
        failures.append(
            f"joint {JOINT_NAMES[joint_index]} at step {step_index + 1}: "
            f"{np.rad2deg(joint_error[step_index, joint_index]):.3f} deg"
        )
    if joint_error[step_60].max() > tolerances["joint_abs_max_rad_at_step_60"]:
        joint_index = int(joint_error[step_60].argmax())
        failures.append(
            f"joint {JOINT_NAMES[joint_index]} at step 60: "
            f"{np.rad2deg(joint_error[step_60, joint_index]):.3f} deg"
        )
    if z_error.max() > tolerances["base_z_abs_max_m_all_steps"]:
        step_index = int(z_error.argmax())
        failures.append(
            f"base_z at step {step_index + 1}: {z_error[step_index] * 1000:.3f} mm"
        )
    if z_error[step_60] > tolerances["base_z_abs_max_m_at_step_60"]:
        failures.append(f"base_z at step 60: {z_error[step_60] * 1000:.3f} mm")
    if failures:
        raise AssertionError("trajectory conformance failed: " + "; ".join(failures))
    print("OK - Genesis BAM-core follows pinned MuJoCo 14-servo fixture")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
