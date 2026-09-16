"""Training-engine command response diagnostic; never replaces native acceptance.

The same final ONNX and visible command schedule run with explicit nominal
actuator/sensor settings. Contacts are Genesis measurements, not MuJoCo forces
recomputed at a copied state. MuJoCo is used only for face-frame kinematics.
"""
import argparse
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def command_at(t, case, suite):
    return case["command"] if suite["move_start_s"] <= t < suite["stop_start_s"] else [0., 0., 0.]


def response_metrics(rows):
    import numpy as np
    moving = [r for r in rows if 2 <= r["time_s"] <= 13]
    stopped = [r for r in rows if r["time_s"] >= 16]
    if not moving:
        raise ValueError("no moving evidence")
    return {
        "duration_s": rows[-1]["time_s"],
        "mean_abs_forward_error_m_s": float(np.mean([abs(r["body_velocity_m_s"][0]-r["command"][0]) for r in moving])),
        "mean_abs_lateral_velocity_m_s": float(np.mean([abs(r["body_velocity_m_s"][1]) for r in moving])),
        "mean_abs_yaw_error_rad_s": float(np.mean([abs(r["yaw_rate_rad_s"]-r["command"][2]) for r in moving])),
        "signed_mean_yaw_error_rad_s": float(np.mean([r["yaw_rate_rad_s"]-r["command"][2] for r in moving])),
        "stop_max_speed_m_s": max((r["speed_m_s"] for r in stopped), default=None),
        "stop_max_yaw_rate_rad_s": max((abs(r["yaw_rate_rad_s"]) for r in stopped), default=None),
        "peak_sole_clearance_m": np.max([r["sole_clearance_m"] for r in moving], axis=0).tolist(),
        "loaded_fraction_left_right": (np.asarray([r["genesis_foot_load_z_n"] for r in moving]) > 1).mean(0).tolist(),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--receipt", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    from scripts.evaluate_laser import digest
    training = json.loads((a.receipt/"training.json").read_text())
    if training["status"] != "completed" or training["variant"] != "walking-v5":
        raise ValueError("completed walking-v5 final export required")
    for name, sha in training["source_sha256"].items():
        if digest(ROOT/name) != sha:
            raise ValueError(f"training source drift: {name}")
    a.output.mkdir(parents=True, exist_ok=False)
    import genesis as gs
    import torch
    import numpy as np
    import mujoco
    from evaluator.core import EvaluatorCore
    from microduck.walking_tracking_env import MicroduckTrackingWalkingEnv
    from microduck.bam_actuator import DelayBuffer
    from experiments.walking.posture import posture_metrics
    torch.set_num_threads(1)
    gs.init(backend=gs.cpu, logging_level="warning", seed=76521)
    env = MicroduckTrackingWalkingEnv(1, demo=True)
    core = EvaluatorCore(a.receipt/"policy.onnx", ROOT/".workspace/bam", "microduck.walking.v1")
    suite = json.loads((ROOT/"experiments/walking/suite-v1.json").read_text())
    reports = []
    for motor, sensor in ((4, 1), (0, 0)):
        for case in (suite["cases"][1], suite["cases"][3]):
            name = f'm{motor}s{sensor}-{case["id"]}'
            env.bam.vin_nominal.fill_(7.35)
            env.bam.vin_drop_resistance.zero_()
            env.bam._delay = DelayBuffer((1, 14), motor, motor, 0, env.device)
            for key, dim in (("base_ang_vel", 3), ("projected_gravity", 3), ("joint_vel", 14)):
                env.obs_delays[key] = DelayBuffer((1, dim), sensor, sensor, 0, env.device)
            env.reset()
            for delay in env.obs_delays.values():
                delay.reset(torch.arange(1, device=env.device))
            env.set_twist(0., 0., 0.)
            obs = env.place([0., 0., .125], yaw=case["yaw"])
            rows, actions = [], []
            for i in range(round(suite["duration_s"]*50)):
                command = command_at(i*.02, case, suite)
                env.set_twist(*command)
                # Current command is not delayed; do not advance sensor history
                # twice by requesting another observation at this boundary.
                observation = obs["policy"].cpu().numpy().copy()
                observation[:, 48:51] = command
                action, _ = core.policy.infer(observation)
                obs, _, done, _ = env.step(torch.from_numpy(action.copy()).to(env.device))
                if bool(done.any()):
                    raise ValueError("numerical reset invalidates diagnostic episode")
                applied = env.actions.cpu().numpy()
                if applied.tobytes() != action.tobytes():
                    raise ValueError("policy action bytes altered")
                qpos = np.r_[env.base_pos[0].cpu().numpy(), env.base_quat[0].cpu().numpy(), env.dof_pos[0].cpu().numpy()]
                core.data.qpos[:] = qpos
                mujoco.mj_kinematics(core.model, core.data)
                face = core.data.site("head_camera").xmat.reshape(3, 3)[:, 0]
                velocity = env.base_lin_vel[0].cpu().numpy()
                row = {"time_s": (i+1)*.02, "command": command,
                    "actor_observation": observation[0].tolist(), "action_rad": action[0].tolist(),
                    "qpos": qpos.tolist(), "face_world": face.tolist(),
                    "body_velocity_m_s": velocity.tolist(), "speed_m_s": float(np.linalg.norm(velocity[:2])),
                    "yaw_rate_rad_s": float(env.base_ang_vel[0, 2]),
                    "sole_clearance_m": env.sole_height[0].cpu().tolist(),
                    "genesis_foot_load_z_n": env.foot_contact_force[0, :, 2].cpu().tolist(),
                    "motor_torque_physics_nm": torch.stack(env.torque_recorder.samples)[:, 0].cpu().tolist()}
                rows.append(row)
                actions.append(action[0].copy())
                if qpos[2] < .07 or float(env.projected_gravity[0, 2]) > -np.cos(np.deg2rad(70)):
                    break
            (a.output/f"{name}.jsonl").write_text("".join(json.dumps(r)+"\n" for r in rows))
            np.save(a.output/f"{name}-actions-float32.npy", np.asarray(actions, np.float32))
            report = {"case_id": name, "response": response_metrics(rows), "posture": posture_metrics(rows)}
            reports.append(report)
            print(json.dumps(report), flush=True)
    result = {"schema": "microduck.walking-genesis-diagnostic/v1", "cases": reports,
        "policy_sha256": digest(a.receipt/"policy.onnx"), "acceptance_eligible": False,
        "physics": {"engine": "Genesis CPU", "floor_masks": [1, 1], "voltage_v": 7.35, "drop_ohm": 0.},
        "boundary": "Training-engine closed-loop diagnostic, not fixed-action cross-engine isolation or gait/physical acceptance. Uses the training motor buffer's first-target fill semantics; native world initially holds HOME for its declared lag. Sole/load are Genesis measurements; face is copied-state kinematics only."}
    (a.output/"diagnosis.json").write_text(json.dumps(result, indent=2)+"\n")
    for name in list(training["source_sha256"])+["scripts/probe_walking_tracking_genesis.py", "experiments/walking/posture.py", "experiments/walking/suite-v1.json", "evaluator/core.py"]:
        dest = a.output/"source"/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT/name, dest)
    shutil.copy2(a.receipt/"policy.onnx", a.output/"policy.onnx")
    (a.output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.relative_to(a.output)}\n" for f in sorted(a.output.rglob("*")) if f.is_file()))


if __name__ == "__main__":
    main()
