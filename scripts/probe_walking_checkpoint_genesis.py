"""Intermediate v5 training-engine probe, never candidate selection evidence."""
import argparse
import copy
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run-id", required=True)
    p.add_argument("--iteration", type=int, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if not a.run_id.replace("-", "").isalnum() or a.iteration < 0:
        p.error("simple run ID and nonnegative iteration required")
    from scripts.evaluate_laser import digest
    from scripts.probe_walking_tracking_genesis import command_at, response_metrics
    folder = ROOT/"logs"/a.run_id
    record = json.loads((folder/"run.json").read_text())
    if record["variant"] != "walking-v5":
        raise ValueError("this diagnostic is bound to v5")
    checkpoint = folder/f"model_{a.iteration}.pt"
    checkpoint_sha = digest(checkpoint)
    for path, value in record["source_sha256"].items():
        if digest(ROOT/path) != value:
            raise ValueError(f"training source changed: {path}")
    a.output.mkdir(parents=True, exist_ok=False)
    import genesis as gs
    import torch
    import numpy as np
    import mujoco
    from tensordict import TensorDict
    from rsl_rl.models import MLPModel
    from export_onnx import ExportedPolicy
    from microduck.walking_tracking_env import MicroduckTrackingWalkingEnv
    from microduck.bam_actuator import DelayBuffer
    from experiments.walking.posture import posture_metrics
    torch.set_num_threads(1)
    cfg = copy.deepcopy(record["train_cfg"])
    cfg["actor"].pop("class_name")
    actor = MLPModel(TensorDict({"policy": torch.zeros(1, 61)}, [1]), cfg["obs_groups"], "actor", 14, **cfg["actor"])
    actor.load_state_dict(torch.load(checkpoint, map_location="cpu", weights_only=True)["actor_state_dict"])
    policy = ExportedPolicy(actor.eval()).eval()
    gs.init(backend=gs.cpu, logging_level="warning", seed=76521)
    env = MicroduckTrackingWalkingEnv(1, demo=True)
    model = mujoco.MjModel.from_xml_path(str(env.robot_xml))
    data = mujoco.MjData(model)
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
                observation = obs["policy"].cpu().clone()
                observation[:, 48:51] = torch.tensor(command)
                with torch.no_grad():
                    action = policy(observation)
                obs, _, done, _ = env.step(action.to(env.device))
                if bool(done.any()):
                    raise ValueError("numerical reset invalidates diagnostic")
                if env.actions.cpu().numpy().tobytes() != action.numpy().tobytes():
                    raise ValueError("policy actions altered")
                qpos = np.r_[env.base_pos[0].cpu().numpy(), env.base_quat[0].cpu().numpy(), env.dof_pos[0].cpu().numpy()]
                data.qpos[:] = qpos
                mujoco.mj_kinematics(model, data)
                velocity = env.base_lin_vel[0].cpu().numpy()
                row = {"time_s": (i+1)*.02, "command": command,
                    "qpos": qpos.tolist(), "face_world": data.site("head_camera").xmat.reshape(3, 3)[:, 0].tolist(),
                    "actor_observation": observation[0].tolist(), "action_rad": action[0].tolist(),
                    "body_velocity_m_s": velocity.tolist(), "speed_m_s": float(np.linalg.norm(velocity[:2])),
                    "yaw_rate_rad_s": float(env.base_ang_vel[0, 2]),
                    "sole_clearance_m": env.sole_height[0].cpu().tolist(),
                    "genesis_foot_load_z_n": env.foot_contact_force[0, :, 2].cpu().tolist(),
                    "tilt_deg": float(np.rad2deg(np.arccos(np.clip(-float(env.projected_gravity[0, 2]), -1, 1)))),
                    "minimum_actual_joint_margin_rad": float(torch.minimum(env.dof_pos-env.actual_lo, env.actual_hi-env.dof_pos).min()),
                    "motor_torque_physics_nm": torch.stack(env.torque_recorder.samples)[:, 0].cpu().tolist()}
                rows.append(row)
                actions.append(action[0].numpy().copy())
                if qpos[2] < .07 or row["tilt_deg"] > 70:
                    break
            (a.output/f"{name}.jsonl").write_text("".join(json.dumps(r)+"\n" for r in rows))
            np.save(a.output/f"{name}-actions-float32.npy", np.asarray(actions, np.float32))
            stopped = [r for r in rows if r["time_s"] >= 16]
            report = {"case_id": name, "response": response_metrics(rows), "posture": posture_metrics(rows),
                "minimum_actual_joint_margin_rad": min(r["minimum_actual_joint_margin_rad"] for r in rows),
                "stop_max_tilt_deg": max((r["tilt_deg"] for r in stopped), default=None)}
            reports.append(report)
            print(json.dumps(report), flush=True)
    if digest(checkpoint) != checkpoint_sha:
        raise ValueError("checkpoint changed during probe")
    result = {"schema": "microduck.walking-genesis-diagnostic/v1", "cases": reports,
        "checkpoint_sha256": checkpoint_sha, "iteration": a.iteration, "acceptance_eligible": False,
        "inference": "Torch CPU normalized actor; intermediate diagnosis only",
        "physics": {"engine": "Genesis CPU", "floor_masks": [1, 1], "constraint_timeconst_s": .01, "voltage_v": 7.35, "drop_ohm": 0.},
        "boundary": "Closed-loop diagnostic, not fixed-action isolation, native acceptance, candidate selection or physical transfer."}
    (a.output/"diagnosis.json").write_text(json.dumps(result, indent=2)+"\n")
    shutil.copy2(checkpoint, a.output/"source-checkpoint.pt")
    shutil.copy2(folder/"run.json", a.output/"training-at-probe.json")
    for name in list(record["source_sha256"])+["scripts/probe_walking_checkpoint_genesis.py", "scripts/probe_walking_tracking_genesis.py", "experiments/walking/posture.py", "experiments/walking/suite-v1.json"]:
        dest = a.output/"source"/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT/name, dest)
    (a.output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.relative_to(a.output)}\n" for f in sorted(a.output.rglob("*")) if f.is_file()))


if __name__ == "__main__":
    main()
