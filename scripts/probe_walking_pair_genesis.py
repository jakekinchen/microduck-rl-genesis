"""V20 exposed same-pair Genesis diagnostic with measured timing contracts."""
import argparse
from collections import deque
import json
from pathlib import Path
import shutil
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.evaluate_laser import digest
from scripts.evaluate_walking_heading import verify_input_manifest

BASE = ROOT / "receipts/walking/20260906-v18-current"
NATIVE = ROOT / "receipts/walking/20260906-v19-filtered-heading-diagnostic"
FREEZE = ROOT / "experiments/walking/paired-genesis-freeze-v20.json"
CASES = [("long-30-20ms", "forward-20"), ("long-30-20ms", "arc-right"),
         ("nominal-20-20ms", "forward-20")]


def binding():
    verify_input_manifest(BASE)
    covered = set()
    for line in (NATIVE / "SHA256SUMS").read_text().splitlines():
        sha, name = line.split("  ", 1)
        path = (NATIVE / name).resolve()
        if (name in covered or not path.is_relative_to(NATIVE.resolve())
                or digest(path) != sha):
            raise ValueError("native diagnostic manifest mismatch")
        covered.add(name)
    if not {"probe.json", "trajectory.jsonl", "diagnostic-freeze.json", "suites.json"} <= covered:
        raise ValueError("incomplete native diagnostic")
    prior = json.loads((NATIVE / "probe.json").read_text())
    sources = dict(prior["source_sha256"])
    for name, sha in sources.items():
        if digest(ROOT / name) != sha:
            raise ValueError(f"retained source drift: {name}")
    for name in ("scripts/probe_walking_pair_genesis.py",
                 "scripts/probe_walking_tracking_genesis.py",
                 "experiments/walking/PAIRED-GENESIS-v20.md"):
        sources[name] = digest(ROOT / name)
    return {"schema": "microduck.paired-genesis-freeze/v1", "cases": CASES,
            "source_sha256": sources,
            "input_manifests": {str(p.relative_to(ROOT)): digest(p / "SHA256SUMS")
                                for p in (BASE, NATIVE)},
            "policy_sha256": digest(BASE / "policy.onnx"),
            "standing_policy_sha256": digest(BASE / "standing/policy.onnx"),
            "backend": "cpu", "num_envs": 1, "candidate_selection_eligible": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    frozen = binding()
    if args.freeze:
        with FREEZE.open("x") as stream:
            json.dump(frozen, stream, indent=2)
            stream.write("\n")
        return
    if args.output is None:
        parser.error("new output directory required")
    if json.loads(FREEZE.read_text()) != json.loads(json.dumps(frozen)):
        raise ValueError("diagnostic freeze changed")
    args.output.mkdir(parents=True, exist_ok=False)
    result = {**frozen, "schema": "microduck.paired-genesis-diagnostic/v1",
              "status": "starting", "cases": [], "held_out": False,
              "physical_transfer_validated": False,
              "boundary": "Exposed closed-loop engine diagnostic, not fixed-action causality, full gait acceptance or calibrated physics."}
    started = time.monotonic()
    try:
        run(args.output, result)
        if binding() != frozen:
            raise ValueError("source or input changed during diagnostic")
        result["status"] = "completed"
    except BaseException as exc:
        result.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        result["elapsed_s"] = time.monotonic() - started
        (args.output / "probe.json").write_text(json.dumps(result, indent=2) + "\n")
        shutil.copy2(FREEZE, args.output / "diagnostic-freeze.json")
        shutil.copy2(BASE / "suite.json", args.output / "suite.json")
        for name in frozen["source_sha256"]:
            target = args.output / "source" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)
        (args.output / "SHA256SUMS").write_text("".join(
            f"{digest(f)}  {f.relative_to(args.output)}\n"
            for f in sorted(args.output.rglob("*")) if f.is_file() and f.name != "SHA256SUMS"))


def run(output, result):
    import genesis as gs
    import mujoco
    import numpy as np
    import torch
    from evaluator.core import OnnxPolicy, CONFIG_PATH
    from microduck.bam_actuator import DelayBuffer
    from microduck.walking_unbraced_env import MicroduckUnbracedWalkingEnv
    from microduck.filtered_heading_servo import FilteredHeadingServo
    from microduck.standing_env import summed_internal_force
    from experiments.walking.command_ramp import CommandRamp
    from experiments.walking.posture import posture_metrics
    from experiments.walking.heading import evaluate_heading
    from scripts.probe_walking_tracking_genesis import command_at, response_metrics

    torch.set_num_threads(1)
    suite = json.loads((BASE / "suite.json").read_text())
    # Identical ONNX runtime and normalizers to the retained native diagnostic.
    inference = json.loads(CONFIG_PATH.read_text())["inference"]
    policies = {"walking": OnnxPolicy(BASE / "policy.onnx", inference),
                "standing": OnnxPolicy(BASE / "standing/policy.onnx", inference)}
    gs.init(backend=gs.cpu, logging_level="warning", seed=suite["seed"])
    env = MicroduckUnbracedWalkingEnv(1, demo=True,
        model_directory=ROOT / "experiments/walking/models/contact-v11")
    model = mujoco.MjModel.from_xml_path(str(env.robot_xml))
    data = mujoco.MjData(model)
    result["env_cfg"] = env.cfg
    original_step = env.scene.step
    loads = []

    def observed_step():
        value = original_step()
        loads.append(float(summed_internal_force(env.robot.get_contacts(with_entity=env.robot))[0]))
        return value

    env.scene.step = observed_step
    ids = torch.arange(1, device=env.device)
    for timing_id, case_id in CASES:
        timing = next(t for t in suite["timing_profiles"] if t["id"] == timing_id)
        case = next(c for c in suite["cases"] if c["id"] == case_id)
        name = timing_id + "--" + case_id
        motor, sensor = timing["motor_ticks"], timing["sensor_ticks"]
        env.bam._delay = DelayBuffer((1, 14), motor, motor, 0, env.device)
        for key, dim in (("base_ang_vel", 3), ("projected_gravity", 3), ("joint_vel", 14)):
            env.obs_delays[key] = DelayBuffer((1, dim), sensor, sensor, 0, env.device)
        env.reset()
        env.bam.vin_nominal.fill_(7.35)
        env.bam.vin_drop_resistance.zero_()
        for delay in env.obs_delays.values():
            delay.reset(ids)
        env.set_twist(0., 0., 0.)
        obs = env.place([0., 0., .125], yaw=case["yaw"])
        env.bam._delay._buf[:] = env.default_dof_pos
        env.bam._delay._needs_fill[:] = False
        ramp, servo = CommandRamp(), FilteredHeadingServo()
        history, quats = deque(maxlen=2), deque(maxlen=2)
        target_history = deque([env.default_dof_pos.cpu().numpy().copy() for _ in range(motor)])
        actual_delay, targets = env.bam._delay, []

        def checked_delay(target):
            assert target.shape == (1, 14)
            target_history.append(target[0].cpu().numpy().copy())
            expected = target_history.popleft()
            actual = actual_delay(target)
            np.testing.assert_array_equal(actual[0].cpu().numpy(), expected)
            targets.append(actual[0].cpu().tolist())
            return actual

        env.bam._delay = checked_delay
        np.testing.assert_allclose(env.base_pos[0].cpu(), [0, 0, .125], atol=1e-7, rtol=0)
        np.testing.assert_allclose(env.base_quat[0].cpu(), [np.cos(case["yaw"]/2), 0, 0, np.sin(case["yaw"]/2)], atol=1e-7, rtol=0)
        for tensor in (env.dof_vel, env.actions, env.last_actions, env.bam.prev_torque,
                       env.base_lin_vel, env.base_ang_vel, env.encoder_bias, env.head_cmd, env.body_cmd):
            assert not torch.count_nonzero(tensor), "nonzero reset state"
        previous_action = np.zeros(14, np.float32)
        rows, actions = [], []
        with (output / (name + ".jsonl")).open("w") as stream:
            for i in range(900):
                requested = np.asarray(command_at(i*.02, case, suite), np.float32)
                routed = ramp.step(requested)
                mode = "standing" if not np.any(routed) else "walking"
                raw = np.concatenate([env.base_ang_vel[0].cpu(), env.projected_gravity[0].cpu(),
                    (env.dof_pos_enc[0]-env.default_dof_pos).cpu(), env.dof_vel_enc[0].cpu(),
                    previous_action, np.zeros(13, np.float32)]).astype(np.float32)
                history.append(raw.copy())
                quats.append(env.base_quat[0].cpu().numpy().copy())
                delayed = max(0, len(history)-1-sensor)
                command, control = servo.step(routed, quats[delayed])
                expected = raw.copy()
                expected[:6] = history[delayed][:6]
                expected[20:34] = history[delayed][20:34]
                expected[48:51] = command
                observation = obs["policy"].cpu().numpy().copy()
                observation[:, 48:51] = command
                np.testing.assert_array_equal(observation[0], expected)
                assert int(actual_delay._lag[0]) == motor
                assert all(int(d._lag[0]) == sensor for d in env.obs_delays.values())
                action, _ = policies[mode].infer(observation)
                env.set_twist(*command)
                loads.clear(); targets.clear()
                obs, _, done, _ = env.step(torch.from_numpy(action).to(env.device))
                assert not bool(done[0]), "automatic reset invalidates diagnostic"
                assert action.tobytes() == env.actions.cpu().numpy().tobytes(), "altered action"
                assert len(loads) == len(targets) == len(env.torque_recorder.samples) == 4
                qpos = np.r_[env.base_pos[0].cpu(), env.base_quat[0].cpu(), env.dof_pos[0].cpu()]
                data.qpos[:] = qpos
                mujoco.mj_kinematics(model, data)  # geometry only, not another dynamics step
                velocity = env.base_lin_vel[0].cpu().numpy()
                row = {"time_s": (i+1)*.02, "command": requested.tolist(),
                    "routing_command": routed.tolist(), "policy_command": command.tolist(),
                    "actor_mode": mode, "heading_control": control,
                    "actor_observation": observation[0].tolist(), "action_rad": action[0].tolist(),
                    "qpos": qpos.tolist(), "face_world": data.site("head_camera").xmat.reshape(3,3)[:,0].tolist(),
                    "body_velocity_m_s": velocity.tolist(), "speed_m_s": float(np.linalg.norm(velocity[:2])),
                    "yaw_rate_rad_s": float(env.base_ang_vel[0,2]),
                    "sole_clearance_m": env.sole_height[0].cpu().tolist(),
                    "genesis_foot_load_z_n": env.foot_contact_force[0,:,2].cpu().tolist(),
                    "genesis_internal_force_magnitude_sum_n_physics": list(loads),
                    "motor_targets_rad_physics": list(targets),
                    "motor_torque_physics_nm": torch.stack(env.torque_recorder.samples)[:,0].cpu().tolist(),
                    "minimum_actual_joint_margin_rad": float(torch.minimum(env.dof_pos[0]-env.actual_lo, env.actual_hi-env.dof_pos[0]).min()),
                    "tilt_deg": float(np.rad2deg(np.arccos(np.clip(-float(env.projected_gravity[0,2]), -1,1))))}
                assert np.isfinite(np.r_[qpos, velocity, loads, action.ravel()]).all()
                rows.append(row); actions.append(action[0].copy())
                stream.write(json.dumps(row) + "\n")
                previous_action = action[0].copy()
                if qpos[2] < .07 or row["tilt_deg"] > 70:
                    break
        np.save(output / (name + "-actions-float32.npy"), np.asarray(actions, np.float32))
        report = {"case_id": name, "response": response_metrics(rows),
                  "heading": evaluate_heading(rows), "posture": posture_metrics(rows),
                  "all_actor_observations_and_motor_targets_verified": True,
                  "observed_control_steps": len(rows), "observed_physics_steps": len(rows)*4,
                  "complete": len(rows) == 900,
                  "minimum_actual_joint_margin_rad": min(r["minimum_actual_joint_margin_rad"] for r in rows)}
        result["cases"].append(report)
        print(json.dumps(report), flush=True)
        # Restore the buffer before the next reset invokes its reset method.
        env.bam._delay = actual_delay


if __name__ == "__main__":
    main()
