"""Byte-identical action replay through Genesis and native MuJoCo/BAM.

No policy feedback, action assistance or metric fitting. Records every 5-ms
physical sample so contact/dynamics differences cannot hide in 50-Hz averages.
"""
import argparse
import json
from pathlib import Path
import shutil
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--receipt", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--case", default="nominal-20-20ms--turn-left")
    p.add_argument("--steps", type=int, default=100)
    a = p.parse_args()
    if not 1 <= a.steps <= 900:
        raise ValueError("bounded 1..900 control steps")
    import numpy as np
    import torch
    import mujoco
    import genesis as gs
    from experiments.walking.world import WalkingWorld
    from microduck.walking_solver_env import MicroduckSolverAlignedWalkingEnv
    from microduck.bam_actuator import DelayBuffer
    from scripts.evaluate_laser import digest
    suite = json.loads((ROOT/"experiments/walking/suite-v1.json").read_text())
    timing_id, case_id = a.case.split("--", 1)
    timing = next(t for t in suite["timing_profiles"] if t["id"] == timing_id)
    case = next(c for c in suite["cases"] if c["id"] == case_id)
    source = a.receipt/f"{a.case}-actions-float32.npy"
    inputs = np.load(source, allow_pickle=False)[:a.steps]
    if inputs.dtype != np.float32 or inputs.shape != (a.steps, 14) or not np.isfinite(inputs).all():
        raise ValueError("original finite float32 action file required")
    a.output.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(1)
    gs.init(backend=gs.cpu, logging_level="warning", seed=suite["seed"])
    env = MicroduckSolverAlignedWalkingEnv(1, demo=True)
    env.bam.vin_nominal.fill_(7.35)
    env.bam.vin_drop_resistance.zero_()
    ticks = timing["motor_ticks"]
    env.bam._delay = DelayBuffer((1, 14), ticks, ticks, 0, env.device)
    env.reset()
    env.place([0., 0., .125], yaw=case["yaw"])
    # Explicitly align startup history with the native evaluator. This changes
    # no action: before the first command the servo reference is already HOME.
    env.bam._delay(env.default_dof_pos[None].clone())
    world = WalkingWorld(a.receipt/"policy.onnx", ROOT/".workspace/bam", motor_ticks=ticks,
        sensor_ticks=timing["sensor_ticks"], yaw=case["yaw"], seed=suite["seed"])
    c = world.core
    feet = [c.model.geom(f"{side}_foot_collision").id for side in ("left", "right")]
    floor = c.model.geom("floor").id
    applied = [[], []]
    rows = []
    initial_qpos = [np.r_[env.base_pos[0].cpu().numpy(), env.base_quat[0].cpu().numpy(), env.dof_pos[0].cpu().numpy()], c.data.qpos.copy()]
    try:
        for i, action in enumerate(inputs):
            gen_action = torch.from_numpy(action[None].copy()).to(env.device)
            native_action = action.copy()
            if gen_action.cpu().numpy().tobytes() != native_action.tobytes():
                raise ValueError("action bytes changed between engines")
            applied[0].append(gen_action[0].cpu().numpy().copy())
            applied[1].append(native_action.copy())
            gen_target = env.default_dof_pos+gen_action
            native_target = c.home+native_action.astype(np.float64)
            for substep in range(4):
                gen_torque = env.bam.compute(gen_target)
                env.robot.control_dofs_force(gen_torque, env.motors_dof_idx)
                env.scene.step()
                env._refresh_state()
                target = world.motor_delay.step(native_target)
                for j, name in enumerate(c.joint_names):
                    c.controller.set_q_target(name, float(target[j]))
                c.controller.update()
                native_torque = c.data.ctrl.copy()
                mujoco.mj_step(c.model, c.data)
                gen_qpos = np.r_[env.base_pos[0].cpu().numpy(), env.base_quat[0].cpu().numpy(), env.dof_pos[0].cpu().numpy()]
                gen_load = env.robot.get_links_net_contact_force()[0, env.foot_link_idx, 2].cpu().numpy()
                native_load = np.zeros(2)
                for k in range(c.data.ncon):
                    con = c.data.contact[k]
                    if floor not in (int(con.geom1), int(con.geom2)):
                        continue
                    foot = int(con.geom2) if int(con.geom1) == floor else int(con.geom1)
                    if foot in feet:
                        force = np.zeros(6)
                        mujoco.mj_contactForce(c.model, c.data, k, force)
                        native_load[feet.index(foot)] += max(0., float(force[0]))
                if not np.isfinite(np.r_[gen_qpos, c.data.qpos, native_torque, gen_torque.cpu().numpy().ravel()]).all():
                    raise ValueError("nonfinite fixed-action replay")
                rows.append({"time_s": (i*4+substep+1)*.005,
                    "genesis_qpos": gen_qpos.tolist(), "native_qpos": c.data.qpos.tolist(),
                    "genesis_torque_nm": gen_torque[0].cpu().tolist(), "native_torque_nm": native_torque.tolist(),
                    "genesis_last_step_foot_load_z_n": gen_load.tolist(),
                    "native_last_step_foot_normal_n": native_load.tolist(),
                    "root_position_difference_m": float(np.linalg.norm(gen_qpos[:3]-c.data.qpos[:3])),
                    "max_joint_difference_rad": float(np.max(np.abs(gen_qpos[7:]-c.data.qpos[7:]))),
                    "max_motor_torque_difference_nm": float(np.max(np.abs(gen_torque[0].cpu().numpy()-native_torque)))})
    finally:
        world.close()
    np.save(a.output/"original-inputs-float32.npy", inputs)
    np.save(a.output/"applied-actions-float32.npy", np.asarray(applied, np.float32))
    (a.output/"trajectory-200hz.jsonl").write_text("".join(json.dumps(r)+"\n" for r in rows))
    def first(predicate):
        return next((r["time_s"] for r in rows if predicate(r)), None)
    report = {"schema": "microduck.cross-engine-fixed-action-diagnostic/v1",
        "source_action_file": str(source), "source_sha256": digest(source), "control_steps": a.steps,
        "action_bytes_equal": np.asarray(applied[0]).tobytes() == np.asarray(applied[1]).tobytes() == inputs.tobytes(),
        "initial_max_qpos_difference": float(np.max(np.abs(initial_qpos[0]-initial_qpos[1]))),
        "first_root_difference_over_1mm_s": first(lambda r: r["root_position_difference_m"] > .001),
        "first_joint_difference_over_001rad_s": first(lambda r: r["max_joint_difference_rad"] > .01),
        "first_torque_difference_over_001nm_s": first(lambda r: r["max_motor_torque_difference_nm"] > .01),
        "first_genesis_foot_load_over_1n_s": first(lambda r: max(r["genesis_last_step_foot_load_z_n"]) > 1),
        "first_native_foot_load_over_1n_s": first(lambda r: max(r["native_last_step_foot_normal_n"]) > 1),
        "maximum_root_position_difference_m": max(r["root_position_difference_m"] for r in rows),
        "maximum_joint_difference_rad": max(r["max_joint_difference_rad"] for r in rows),
        "solver_parameters": {"integrator": "Euler", "iterations": 100, "ls_iterations": 50, "tolerance": 1e-8, "genesis_mujoco_compatibility": True},
        "constraint_parameters": {"genesis_default_timeconst_s": env.scene.rigid_solver._sol_default_timeconst, "genesis_floor": env.ground.geoms[0].sol_params.cpu().tolist(), "genesis_robot_floor_geoms": [g.sol_params.cpu().tolist() for g in env.robot.geoms if g.contype & 1], "native_floor": np.r_[c.model.geom_solref[floor], c.model.geom_solimp[floor]].tolist(), "native_feet": [np.r_[c.model.geom_solref[g], c.model.geom_solimp[g]].tolist() for g in feet]},
        "physics": {"constraint_timeconst_s": .02, "floor_masks": [1, 1], "voltage_v": 7.35, "drop_ohm": 0., "motor_ticks": ticks, "startup_history": "HOME in both engines"},
        "boundary": "Original saved 50-Hz float32 actions held byte-identically through 200-Hz BAM loops. Sensor lag has no effect in fixed-action replay. Genesis CPU/native MuJoCo differences are observations, not a fit, acceptance or hardware calibration. Force channels are each engine's last integrated-step measurements; Genesis reports link vertical resultant and native reports summed contact normal."}
    (a.output/"audit.json").write_text(json.dumps(report, indent=2)+"\n")
    for name in ("scripts/audit_walking_solver_replay.py", "microduck/walking_ground_env.py", "microduck/walking_contact_env.py", "microduck/walking_solver_env.py", "microduck/walking_tracking_env.py", "microduck/walking_posture_env.py", "microduck/walking_controlled_env.py", "microduck/walking_env.py", "microduck/velocity_env.py", "microduck/bam_actuator.py", "microduck/constants.py", "experiments/walking/world.py", "evaluator/core.py"):
        dest = a.output/"source"/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT/name, dest)
    (a.output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.relative_to(a.output)}\n" for f in sorted(a.output.rglob("*")) if f.is_file()))
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
