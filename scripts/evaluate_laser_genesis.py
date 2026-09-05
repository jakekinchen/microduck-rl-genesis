"""Same visible laser cases on Genesis to distinguish learning from transfer.

This is a development diagnostic, not independent acceptance. The primary
independent result remains C MuJoCo/BAM in evaluate_laser.py.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.evaluate_laser import SUITE, digest, target_at, summarize
from microduck.laser_task import target_command, world_to_body_xy
from microduck.laser_steering import approach_command


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--evaluation", type=Path, required=True,
                   help="completed local laser evaluation directory")
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    receipt = json.loads((args.evaluation/"evaluation.json").read_text())
    gain = receipt.get("steering", {}).get("distance_gain_s_inv", 1.5)
    policy_path = args.evaluation/"policy.onnx"
    if receipt["policy_sha256"] != digest(policy_path):
        raise ValueError("policy digest mismatch")
    args.output.mkdir(parents=True, exist_ok=False)
    import genesis as gs
    import torch
    import numpy as np
    import onnxruntime as ort
    from microduck.laser_env import MicroduckLaserEnv
    gs.init(backend=gs.cpu, logging_level="warning", seed=74105)
    env = MicroduckLaserEnv(1, demo=True)
    session = ort.InferenceSession(str(policy_path), providers=["CPUExecutionProvider"])
    suite = json.loads(SUITE.read_text())
    reports = []
    with (args.output/"trajectory.jsonl").open("w") as stream:
        for case in suite["cases"]:
            env.reset()
            env.laser_xy[0] = torch.tensor(case["target_xy_m"], device=env.device)
            env.laser_visible[:] = True
            obs = env.place([0, 0, .125], yaw=0)
            rows = []
            for step in range(round(case["seconds"]*50)):
                target, visible = target_at(case, step/50)
                position = env.base_pos[0].cpu().numpy()
                quaternion = env.base_quat[0].cpu().numpy()
                command = approach_command(world_to_body_xy(target, position[:2], quaternion), visible, gain)
                env.laser_xy[0] = torch.from_numpy(target).to(env.device)
                env.laser_visible[:] = visible
                env.twist_cmd[0] = torch.from_numpy(command).to(env.device)
                vector = obs["policy"].cpu().numpy().copy()
                # Update only the canonical command slots, not sensor buffers:
                # computing observations twice would consume delay state twice.
                vector[:, 48:51] = command
                action = session.run(None, {"obs": vector})[0]
                obs, _, done, _ = env.step(torch.from_numpy(action).to(env.device))
                if bool(done.any()):
                    raise RuntimeError("Genesis nonfinite reset: episode is invalid, not a hidden success")
                position = env.base_pos[0].cpu().numpy()
                speed = float(env.robot.get_vel()[0, :2].norm().item())
                gravity = env.projected_gravity[0].cpu().numpy()
                tilt = float(np.degrees(np.arccos(np.clip(-gravity[2], -1, 1))))
                fell = position[2] < suite["thresholds"]["minimum_height_m"] or tilt > suite["thresholds"]["maximum_tilt_deg"]
                row = {"case_id": case["id"], "time_s": (step+1)/50,
                       "robot_xyz_m": position.tolist(), "target_xy_m": target.tolist(),
                       "distance_m": float(np.linalg.norm(target-position[:2])),
                       "speed_m_s": speed, "visible": bool(visible), "command": command.tolist(),
                       "action_rad": action[0].tolist(), "fell": bool(fell), "tilt_deg": tilt,
                       "latency_ms": None}
                rows.append(row)
                stream.write(json.dumps(row)+"\n")
                if fell:
                    break
            report = summarize(case, rows, suite["thresholds"])
            report.pop("inference_deadline_misses")  # no latency claim in this diagnostic
            reports.append(report)
            print(json.dumps(report), flush=True)
    result = {"schema": "microduck.laser-genesis-diagnostic/v1", "backend": "Genesis CPU",
              "proof_class": "first_party_development", "held_out": False,
              "target_source": "simulated-ground-truth", "policy_sha256": digest(policy_path),
              "steering_gain_s_inv": gain,
              "suite_sha256": digest(SUITE), "source_sha256": digest(Path(__file__)),
              "passed_cases": sum(r["passed"] for r in reports), "case_reports": reports,
              "boundary": "Training-simulator diagnostic; not independent acceptance, camera, transfer, or physical proof."}
    (args.output/"evaluation.json").write_text(json.dumps(result, indent=2)+"\n")
    shutil.copy2(Path(__file__), args.output/"evaluator-source.py")
    shutil.copy2(ROOT/"microduck/laser_steering.py", args.output/"steering-source.py")
    (args.output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.name}\n" for f in sorted(args.output.iterdir()) if f.is_file() and f.name != "SHA256SUMS"))


if __name__ == "__main__":
    main()
