#!/usr/bin/env python3
"""Consume the pinned BAM fixtures through the official mjlab adapter."""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import os
import re
import subprocess
import sys
from importlib import metadata
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_COMMIT = "62bd8ce12154340be97e06f7f41a0ca8f116d967"
PARAMETER_PATH = ROOT / "microduck" / "assets" / "xl330_m6.json"
ROBOT_PATH = ROOT / "microduck" / "assets" / "microduck" / "robot_walk.xml"
OPEN_FIXTURE = (
    ROOT
    / "microduck_contract"
    / "actuator"
    / "fixtures"
    / "bam-m6-xl330-v1-open-loop.json"
)
CLOSED_FIXTURE = (
    ROOT
    / "microduck_contract"
    / "actuator"
    / "fixtures"
    / "bam-m6-xl330-v1-closed-loop.json"
)
ACTUATOR_LOCK = (
    ROOT / "microduck_contract" / "actuator" / "bam-m6-xl330-v1.lock.json"
)


def command(*args: str, cwd: Path) -> str:
    return subprocess.check_output(args, cwd=cwd, text=True).strip()


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


class ResetProbe:
    def __init__(self) -> None:
        self.env_ids: list[int] | None = None

    def reset(self, env_ids) -> None:
        self.env_ids = env_ids.tolist() if env_ids is not None else None


def check_authority(bam_repo: Path, open_fixture: dict, closed_fixture: dict) -> None:
    head = command("git", "rev-parse", "HEAD", cwd=bam_repo)
    if head != AUTHORITY_COMMIT:
        raise AssertionError(
            f"BAM authority mismatch: expected {AUTHORITY_COMMIT}, got {head}"
        )
    if command("git", "status", "--porcelain", cwd=bam_repo):
        raise AssertionError("BAM authority checkout is dirty")
    authority = open_fixture["authority"]
    expected = {
        "commit": head,
        "tree": command("git", "rev-parse", "HEAD^{tree}", cwd=bam_repo),
        "parameter": sha256(PARAMETER_PATH),
        "bam_model": sha256(bam_repo / "bam" / "model.py"),
        "bam_mjlab": sha256(bam_repo / "bam" / "mjlab.py"),
    }
    observed = {
        "commit": authority["commit"],
        "tree": authority["tree"],
        "parameter": authority["parameter_sha256"],
        "bam_model": authority["source_files"]["bam/model.py"],
        "bam_mjlab": authority["source_files"]["bam/mjlab.py"],
    }
    assert observed == expected, f"open-loop authority mismatch: {observed}"
    closed_authority = closed_fixture["authority"]
    assert closed_authority["commit"] == head
    assert closed_authority["tree"] == expected["tree"]
    assert closed_authority["parameter_sha256"] == expected["parameter"]


def check_runtime() -> dict[str, str]:
    expected = json.loads(ACTUATOR_LOCK.read_text())["official_mjlab_runtime"]
    observed = {name: metadata.version(name) for name in expected}
    assert observed == expected, f"official mjlab runtime mismatch: {observed}"
    return observed


def consume_open_loop(open_fixture: dict, bam_repo: Path) -> None:
    import torch
    from bam.mjlab import BamActuator as AuthorityActuator
    from bam.model import load_model

    authority_path = Path(inspect.getsourcefile(AuthorityActuator) or "").resolve()
    assert authority_path.is_relative_to(bam_repo)
    model = load_model(os.fspath(PARAMETER_PATH))
    model.actuator.kp = open_fixture["generation"]["firmware_kp"]
    deployed = object.__new__(AuthorityActuator)
    deployed._bam_model = model
    tolerance = open_fixture["generation"]["float64_absolute_tolerance"]
    max_errors = {
        "control_voltage_v": 0.0,
        "motor_torque_nm": 0.0,
        "mjlab_deployed_frictionloss_nm": 0.0,
    }
    for row in open_fixture["vectors"]:
        inputs = row["input"]
        expected = row["expected"]
        model.actuator.vin = inputs["vin_v"]
        voltage = model.actuator.compute_control(
            inputs["q_target_rad"],
            inputs["q_rad"],
            inputs["dq_rad_s"],
            open_fixture["generation"]["physics_dt_s"],
        )
        torque = model.actuator.compute_torque(
            voltage, True, inputs["q_rad"], inputs["dq_rad_s"]
        )
        dtype = torch.float64
        velocity = torch.tensor([[inputs["dq_rad_s"]]], dtype=dtype)
        stribeck = torch.exp(
            -torch.pow(
                torch.abs(velocity) / model.dtheta_stribeck.value,
                model.alpha.value,
            )
        )
        friction = AuthorityActuator._compute_friction_budget(
            deployed,
            torch.tensor([[inputs["friction_motor_torque_nm"]]], dtype=dtype),
            torch.tensor([[inputs["friction_external_torque_nm"]]], dtype=dtype),
            stribeck,
        ).item()
        actual = {
            "control_voltage_v": float(voltage),
            "motor_torque_nm": float(torque),
            "mjlab_deployed_frictionloss_nm": float(friction),
        }
        for field, value in actual.items():
            error = abs(value - expected[field])
            max_errors[field] = max(max_errors[field], error)
            assert error <= tolerance, f"{row['id']} {field}: {error:.3e}"

    reset = open_fixture["reset_fixture"]
    deployed._delay_buffer = ResetProbe()
    deployed._prev_motor_torque = torch.tensor(
        reset["prev_motor_torque_before_nm"], dtype=torch.float64
    )
    deployed.vin_tensor = torch.tensor(reset["vin_before_v"], dtype=torch.float64)
    AuthorityActuator.reset(deployed, torch.tensor(reset["env_ids"]))
    assert deployed._prev_motor_torque.tolist() == reset["prev_motor_torque_after_nm"]
    assert deployed.vin_tensor.tolist() == reset["vin_after_v"]
    assert deployed._delay_buffer.env_ids == reset["delay_reset_env_ids"]
    print(f"official mjlab consumed {len(open_fixture['vectors'])} open-loop rows")
    for field, error in max_errors.items():
        print(f"  {field}: max error {error:.3e}")
    print("  selective reset and persistent battery voltage verified")


def consume_closed_loop(closed_fixture: dict) -> None:
    import mujoco
    import torch
    from bam.mjlab import BamActuatorCfg
    from mjlab.entity import EntityArticulationInfoCfg, EntityCfg
    from mjlab.scene import Scene, SceneCfg
    from mjlab.sim import MujocoCfg, Simulation, SimulationCfg
    from mjlab.terrains import TerrainEntityCfg

    cfg = closed_fixture["configuration"]
    joint_names = tuple(cfg["joint_order"])
    home = tuple(cfg["home_joint_position_rad"])
    target_expression = r"^(?:" + "|".join(map(re.escape, joint_names)) + r")$"
    actuator_cfg = BamActuatorCfg(
        json_path=os.fspath(PARAMETER_PATH),
        target_names_expr=(target_expression,),
        kp_fw=cfg["firmware_kp"],
        vin=cfg["supply_voltage_v"],
        stiff_frictionloss=True,
        delay_min_lag=0,
        delay_max_lag=0,
    )
    entity_cfg = EntityCfg(
        spec_fn=lambda: mujoco.MjSpec.from_file(os.fspath(ROBOT_PATH)),
        articulation=EntityArticulationInfoCfg(actuators=(actuator_cfg,)),
    )
    device = "cpu"
    scene = Scene(
        SceneCfg(
            num_envs=1,
            terrain=TerrainEntityCfg(),
            entities={"robot": entity_cfg},
        ),
        device,
    )
    mj_model = scene.compile()
    simulation = Simulation(
        num_envs=1,
        cfg=SimulationCfg(
            mujoco=MujocoCfg(
                timestep=cfg["physics_dt_s"],
                integrator="euler",
                gravity=(0.0, 0.0, -9.81),
            )
        ),
        model=mj_model,
        device=device,
    )
    scene.initialize(simulation.mj_model, simulation.model, simulation.data)
    simulation.expand_model_fields(("dof_frictionloss", "dof_damping"))
    robot = scene["robot"]
    actuator = robot.actuators[0]
    authority_path = Path(inspect.getsourcefile(type(actuator)) or "").resolve()
    assert authority_path.name == "mjlab.py"
    assert type(actuator).__module__ == "bam.mjlab"

    simulation.reset()
    scene.reset()
    target = torch.tensor([home], dtype=torch.float32, device=device)
    root_pose = torch.tensor(
        [[*cfg["initial_base_position_m"], *cfg["initial_base_quaternion_wxyz"]]],
        dtype=torch.float32,
        device=device,
    )
    robot.write_root_link_pose_to_sim(root_pose)
    robot.write_root_link_velocity_to_sim(torch.zeros((1, 6), device=device))
    robot.write_joint_state_to_sim(target, torch.zeros_like(target))
    simulation.forward()
    initial_joint_error = np.abs(
        robot.data.joint_pos[0].detach().cpu().numpy() - np.asarray(home)
    ).max()
    assert initial_joint_error <= 1e-6, f"initial HOME mismatch: {initial_joint_error}"

    actual_q = []
    actual_z = []
    for _ in range(cfg["steps"]):
        robot.set_joint_position_target(target)
        scene.write_data_to_sim()
        simulation.step()
        scene.update(dt=cfg["physics_dt_s"])
        actual_q.append(robot.data.joint_pos[0].detach().cpu().numpy().copy())
        actual_z.append(float(robot.data.root_link_pos_w[0, 2]))

    expected_q = np.asarray(
        [row["joint_position_rad"] for row in closed_fixture["trajectory"]]
    )
    expected_z = np.asarray(
        [row["base_z_m"] for row in closed_fixture["trajectory"]]
    )
    joint_error = np.abs(np.asarray(actual_q) - expected_q)
    z_error = np.abs(np.asarray(actual_z) - expected_z)
    tolerances = closed_fixture["tolerances"]
    step_60 = 59
    failures = []
    print("official mjlab-deployed-v1 trajectory errors:")
    for joint_index, joint_name in enumerate(joint_names):
        worst_step = int(joint_error[:, joint_index].argmax())
        error = joint_error[worst_step, joint_index]
        print(
            f"  {joint_name:16s} {np.rad2deg(error):.3f} deg "
            f"at step {worst_step + 1:3d}"
        )
    if joint_error.max() > tolerances["joint_abs_max_rad_all_steps"]:
        step_index, joint_index = np.unravel_index(
            joint_error.argmax(), joint_error.shape
        )
        failures.append(
            f"joint {joint_names[joint_index]} at step {step_index + 1}: "
            f"{np.rad2deg(joint_error[step_index, joint_index]):.3f} deg"
        )
    if joint_error[step_60].max() > tolerances["joint_abs_max_rad_at_step_60"]:
        joint_index = int(joint_error[step_60].argmax())
        failures.append(
            f"joint {joint_names[joint_index]} at step 60: "
            f"{np.rad2deg(joint_error[step_60, joint_index]):.3f} deg"
        )
    if z_error.max() > tolerances["base_z_abs_max_m_all_steps"]:
        step_index = int(z_error.argmax())
        failures.append(
            f"base_z at step {step_index + 1}: {z_error[step_index] * 1000:.3f} mm"
        )
    if z_error[step_60] > tolerances["base_z_abs_max_m_at_step_60"]:
        failures.append(f"base_z at step 60: {z_error[step_60] * 1000:.3f} mm")
    print(f"  all-step joint max: {np.rad2deg(joint_error.max()):.3f} deg")
    print(f"  step-60 joint max: {np.rad2deg(joint_error[step_60].max()):.3f} deg")
    print(f"  all-step base-z max: {z_error.max() * 1000:.3f} mm")
    print(f"  step-60 base-z error: {z_error[step_60] * 1000:.3f} mm")
    if failures:
        raise AssertionError("official mjlab trajectory failed: " + "; ".join(failures))
    print("official mjlab/MuJoCo Warp CPU consumed the closed-loop fixture")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bam-repo", required=True, type=Path)
    args = parser.parse_args()
    bam_repo = args.bam_repo.resolve()
    open_fixture = json.loads(OPEN_FIXTURE.read_text())
    closed_fixture = json.loads(CLOSED_FIXTURE.read_text())
    check_authority(bam_repo, open_fixture, closed_fixture)
    runtime = check_runtime()
    sys.path.insert(0, os.fspath(bam_repo))
    import bam

    assert Path(bam.__file__).resolve().is_relative_to(bam_repo)
    consume_open_loop(open_fixture, bam_repo)
    consume_closed_loop(closed_fixture)
    print("official runtime:")
    for name, version in runtime.items():
        print(f"  {name}: {version}")
    print("OK - exact pinned official adapter consumed both BAM fixtures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
