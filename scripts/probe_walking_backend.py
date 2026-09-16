"""Deterministic policy response on the selected actual Genesis backend.

Always diagnostic, including for intermediate checkpoints. No policy selection,
physics assistance, normalizer updates, or edits to a running training source.
"""
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
    p.add_argument("--iteration", type=int)
    p.add_argument("--backend", choices=("cpu", "metal"), required=True)
    p.add_argument("--num-envs", type=int, default=1)
    p.add_argument("--training-jitter", action="store_true", help="diagnose the actual rapidly resampled training delay ranges, not fixed device profiles")
    p.add_argument("--full-bank", action="store_true", help="all 21 exposed tracking-heading cases, not the four-case spot check")
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if not a.run_id.replace("-", "").isalnum() or not 1 <= a.num_envs <= 1024:
        p.error("simple run ID and 1..1024 environments required")
    from scripts.evaluate_laser import digest
    from scripts.probe_walking_tracking_genesis import command_at, response_metrics
    folder = ROOT/"logs"/a.run_id
    record = json.loads((folder/"run.json").read_text())
    if record["variant"] not in ("walking-v5", "walking-v6", "walking-v8", "walking-v9"):
        raise ValueError("only source-bound walking v5/v6/v8/v9 supported")
    if a.iteration is None and record["status"] != "completed":
        raise ValueError("running run requires an explicit diagnostic checkpoint")
    checkpoint = folder/(record["checkpoint"] if a.iteration is None else f"model_{a.iteration}.pt")
    checkpoint_sha = digest(checkpoint)
    for name, sha in record["source_sha256"].items():
        if digest(ROOT/name) != sha:
            raise ValueError(f"training source changed: {name}")
    a.output.mkdir(parents=True, exist_ok=False)
    import genesis as gs
    import torch
    import numpy as np
    import mujoco
    from tensordict import TensorDict
    from rsl_rl.models import MLPModel
    from export_onnx import ExportedPolicy
    from microduck.walking_tracking_env import MicroduckTrackingWalkingEnv
    from microduck.walking_contact_env import MicroduckContactTrackingWalkingEnv
    from microduck.bam_actuator import DelayBuffer
    from experiments.walking.posture import posture_metrics
    from experiments.walking.heading import evaluate_heading
    torch.set_num_threads(1)
    cfg = copy.deepcopy(record["train_cfg"])
    cfg["actor"].pop("class_name")
    actor = MLPModel(TensorDict({"policy": torch.zeros(1, 61)}, [1]), cfg["obs_groups"], "actor", 14, **cfg["actor"])
    actor.load_state_dict(torch.load(checkpoint, map_location="cpu", weights_only=True)["actor_state_dict"])
    policy = ExportedPolicy(actor.eval()).eval()
    gs.init(backend=gs.cpu if a.backend == "cpu" else gs.metal, logging_level="warning", seed=76521)
    cls = MicroduckTrackingWalkingEnv if record["variant"] == "walking-v5" else MicroduckContactTrackingWalkingEnv
    if record["variant"] == "walking-v8":
        from microduck.walking_balance_env import MicroduckBalancedWalkingEnv
        cls = MicroduckBalancedWalkingEnv
    if record["variant"] == "walking-v9":
        from microduck.walking_viability_env import MicroduckViableWalkingEnv
        cls = MicroduckViableWalkingEnv
    env = cls(a.num_envs, demo=True)
    model = mujoco.MjModel.from_xml_path(str(env.robot_xml))
    data = mujoco.MjData(model)
    suite_path = "experiments/walking/tracking-suite-v1.json" if a.full_bank else "experiments/walking/suite-v1.json"
    suite = json.loads((ROOT/suite_path).read_text())
    reports = []
    timings = [(t["motor_ticks"], t["sensor_ticks"]) for t in suite["timing_profiles"]] if a.full_bank else ((4, 1), (0, 0))
    if a.training_jitter:
        timings = (("jitter", "jitter"),)
    cases = suite["cases"] if a.full_bank else (suite["cases"][1], suite["cases"][3])
    for motor, sensor in timings:
        for case in cases:
            name = f'training-jitter-{case["id"]}' if a.training_jitter else f'm{motor}s{sensor}-{case["id"]}'
            env.bam.vin_nominal.fill_(7.35)
            env.bam.vin_drop_resistance.zero_()
            motor_parameters = (0, 6, 64) if a.training_jitter else (motor, motor, 0)
            sensor_parameters = (0, 1, 64) if a.training_jitter else (sensor, sensor, 0)
            env.bam._delay = DelayBuffer((a.num_envs, 14), *motor_parameters, env.device)
            for key, dim in (("base_ang_vel", 3), ("projected_gravity", 3), ("joint_vel", 14)):
                env.obs_delays[key] = DelayBuffer((a.num_envs, dim), *sensor_parameters, env.device)
            env.reset()
            for delay in env.obs_delays.values():
                delay.reset(torch.arange(a.num_envs, device=env.device))
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
                if bool(done[0]):
                    raise ValueError("numerical reset invalidates diagnostic")
                if env.actions[0].cpu().numpy().tobytes() != action[0].numpy().tobytes():
                    raise ValueError("policy action bytes altered")
                qpos = np.r_[env.base_pos[0].cpu().numpy(), env.base_quat[0].cpu().numpy(), env.dof_pos[0].cpu().numpy()]
                data.qpos[:] = qpos
                mujoco.mj_kinematics(model, data)
                velocity = env.base_lin_vel[0].cpu().numpy()
                row = {"time_s": (i+1)*.02, "command": command, "qpos": qpos.tolist(),
                    "face_world": data.site("head_camera").xmat.reshape(3, 3)[:, 0].tolist(),
                    "actor_observation": observation[0].tolist(), "action_rad": action[0].tolist(),
                    "body_velocity_m_s": velocity.tolist(), "speed_m_s": float(np.linalg.norm(velocity[:2])),
                    "yaw_rate_rad_s": float(env.base_ang_vel[0, 2]),
                    "sole_clearance_m": env.sole_height[0].cpu().tolist(),
                    "genesis_foot_load_z_n": env.foot_contact_force[0, :, 2].cpu().tolist(),
                    "tilt_deg": float(np.rad2deg(np.arccos(np.clip(-float(env.projected_gravity[0, 2]), -1, 1)))),
                    "minimum_actual_joint_margin_rad": float(torch.minimum(env.dof_pos[0]-env.actual_lo, env.actual_hi-env.dof_pos[0]).min()),
                    "motor_torque_physics_nm": torch.stack(env.torque_recorder.samples)[:, 0].cpu().tolist()}
                rows.append(row)
                actions.append(action[0].numpy().copy())
                if qpos[2] < .07 or row["tilt_deg"] > 70:
                    break
            (a.output/f"{name}.jsonl").write_text("".join(json.dumps(r)+"\n" for r in rows))
            np.save(a.output/f"{name}-actions-float32.npy", np.asarray(actions, np.float32))
            stopped = [r for r in rows if r["time_s"] >= 16]
            report = {"case_id": name, "response": response_metrics(rows), "posture": posture_metrics(rows),
                "heading": evaluate_heading(rows),
                "minimum_actual_joint_margin_rad": min(r["minimum_actual_joint_margin_rad"] for r in rows),
                "stop_max_tilt_deg": max((r["tilt_deg"] for r in stopped), default=None)}
            reports.append(report)
            print(json.dumps(report), flush=True)
    if digest(checkpoint) != checkpoint_sha:
        raise ValueError("checkpoint changed during probe")
    report = {"schema": "microduck.walking-genesis-backend-diagnostic/v5", "cases": reports,
        "heading_passed_cases": sum(case["heading"]["passed"] for case in reports),
        "full_exposed_bank": a.full_bank and not a.training_jitter,
        "all_exposed_commands": a.full_bank, "suite_sha256": digest(ROOT/suite_path),
        "timing_sampling": "training ranges: motor 0..6 resampled each 64 physics ticks; independent sensor buffers 0..1 each 64 control ticks; randomized phases" if a.training_jitter else "constant device profiles per case",
        "checkpoint_sha256": checkpoint_sha, "checkpoint": checkpoint.name, "acceptance_eligible": False,
        "inference": "Torch CPU normalized deterministic mean; same inference path for both physics backends",
        "physics": {"engine": "Genesis", "backend": a.backend, "batch_size": a.num_envs, "observed_env": 0,
            "class": cls.__name__, "constraint_timeconst_s": .01 if record["variant"] == "walking-v5" else .02,
            "floor_masks": [1, 1], "voltage_v": 7.35, "drop_ohm": 0.},
        "boundary": "Deterministic policy response on an explicit backend/batch size and named timing process. Training-jitter mode covers the command bank, NOT the fixed 21-case battery. Not fixed-action isolation, candidate selection, native acceptance or physical transfer."}
    (a.output/"diagnosis.json").write_text(json.dumps(report, indent=2)+"\n")
    shutil.copy2(checkpoint, a.output/"source-checkpoint.pt")
    shutil.copy2(folder/"run.json", a.output/"training-at-probe.json")
    for name in list(record["source_sha256"])+["scripts/probe_walking_backend.py", "scripts/probe_walking_tracking_genesis.py", "experiments/walking/posture.py", "experiments/walking/heading.py", "experiments/walking/HEADING-v1.md", "tests/test_walking_heading.py", suite_path]:
        dest = a.output/"source"/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT/name, dest)
    (a.output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.relative_to(a.output)}\n" for f in sorted(a.output.rglob("*")) if f.is_file()))


if __name__ == "__main__":
    main()
