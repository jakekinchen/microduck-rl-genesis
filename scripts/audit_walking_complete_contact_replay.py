"""V11 complete-model fixed-action replay in both engines, no feedback aid."""
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
    p.add_argument("--steps", type=int, default=250)
    a = p.parse_args()
    if not 1 <= a.steps <= 900:
        raise ValueError("bounded 1..900 steps")
    import numpy as np
    import torch
    import genesis as gs
    from scripts.evaluate_walking_heading import verify_input_manifest
    from scripts.evaluate_laser import digest
    from experiments.walking.collision_world import CompleteContactWalkingWorld
    from microduck.walking_collision_env import MicroduckCompleteContactWalkingEnv
    from microduck.bam_actuator import DelayBuffer
    verify_input_manifest(a.receipt)
    a.output.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(1)
    gs.init(backend=gs.cpu, logging_level="warning", seed=76551)
    env = MicroduckCompleteContactWalkingEnv(1, model_directory=a.output/"model", demo=True)
    suite = json.loads((ROOT/"experiments/walking/tracking-suite-v1.json").read_text())
    results = []
    for case in (suite["cases"][0], suite["cases"][3]):
        name = "nominal-20-20ms--"+case["id"]
        source = a.receipt/f"{name}-actions-float32.npy"
        actions = np.load(source, allow_pickle=False)[:a.steps]
        if actions.shape != (a.steps, 14) or actions.dtype != np.float32 or not np.isfinite(actions).all():
            raise ValueError("complete bounded raw action prefix required")
        env.bam.vin_nominal.fill_(7.35)
        env.bam.vin_drop_resistance.zero_()
        env.bam._delay = DelayBuffer((1, 14), 4, 4, 0, env.device)
        env.reset()
        env.place([0., 0., .125], yaw=case["yaw"])
        env.bam._delay(env.default_dof_pos[None].clone())
        world = CompleteContactWalkingWorld(a.receipt/"policy.onnx", ROOT/".workspace/bam",
                     model_directory=a.output/"model", yaw=case["yaw"], seed=suite["seed"])
        rows = []
        try:
            for i, action in enumerate(actions):
                tensor = torch.from_numpy(action[None].copy()).to(env.device)
                if tensor.cpu().numpy().tobytes() != action.tobytes():
                    raise ValueError("action tensor bytes changed")
                gen_target = env.default_dof_pos+tensor
                for _ in range(4):
                    torque = env.bam.compute(gen_target)
                    env.robot.control_dofs_force(torque, env.motors_dof_idx)
                    env.scene.step()
                native = world.step_command(case["command"] if 1 <= i*.02 < 13 else [0, 0, 0], action_override=action)
                if world.last_action.tobytes() != action.tobytes():
                    raise ValueError("native action bytes changed")
                qg = env.robot.get_qpos()[0].cpu().numpy().copy()
                qn = world.core.data.qpos.copy()
                from evaluator.core import projected_gravity
                tilt = float(np.degrees(np.arccos(np.clip(-projected_gravity(qg[3:7])[2], -1, 1))))
                fell = bool(qg[2] < .07 or tilt > 70)
                rows.append({"time_s": native["time_s"], "genesis_qpos": qg.tolist(), "native_qpos": qn.tolist(),
                             "genesis_fell": fell, "native_fell": world.fell,
                             "root_position_difference_m": float(np.linalg.norm(qg[:3]-qn[:3])),
                             "max_joint_difference_rad": float(np.abs(qg[7:]-qn[7:]).max())})
                if fell or world.fell:
                    break
        finally:
            world.close()
        np.save(a.output/f"{name}-original-actions-float32.npy", actions)
        (a.output/f"{name}.jsonl").write_text("".join(json.dumps(r)+"\n" for r in rows))
        result = {"case_id": name, "source_action_sha256": digest(source), "identical_input_action_bytes": True,
                  "requested_prefix_steps": a.steps, "replayed_steps": len(rows),
                  "genesis_fell": rows[-1]["genesis_fell"], "native_fell": rows[-1]["native_fell"],
                  "final_root_gap_m": rows[-1]["root_position_difference_m"],
                  "first_root_gap_over_1mm_s": next((r["time_s"] for r in rows if r["root_position_difference_m"] > .001), None)}
        results.append(result)
        print(json.dumps(result), flush=True)
    report = {"schema": "microduck.complete-contact-fixed-action-diagnostic/v1", "cases": results,
              "input_manifest_sha256": digest(a.receipt/"SHA256SUMS"),
              "acceptance_eligible": False,
              "boundary": "Original float32 action prefix in both complete-contact-v11 engines with identical 20-ms BAM latency and HOME history. Stops when either engine falls; no continuation after terminal fall. Copied generalized qpos, no derived-state phase ambiguity. Not closed-loop performance, calibrated fidelity or candidate acceptance."}
    (a.output/"audit.json").write_text(json.dumps(report, indent=2)+"\n")
    for name in ("scripts/audit_walking_complete_contact_replay.py", "microduck/walking_collision_env.py",
                 "experiments/walking/collision_world.py", "experiments/walking/collision_model.py",
                 "microduck/walking_contact_env.py", "microduck/velocity_env.py", "microduck/bam_actuator.py",
                 "microduck/constants.py", "experiments/walking/world.py", "experiments/walking/sensor_world.py"):
        dest = a.output/"source"/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT/name, dest)
    (a.output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.relative_to(a.output)}\n" for f in sorted(a.output.rglob("*")) if f.is_file()))


if __name__ == "__main__":
    main()
