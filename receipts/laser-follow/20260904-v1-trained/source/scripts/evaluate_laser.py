"""Export and independently evaluate locally trained laser-goal policies.

Reuses the immutable C MuJoCo/BAM core; the target command adapter is separate
and explicit. Renders a red spot at the real simulated goal position. No robot
action offsets, IK, teleports, or post-policy action filters are added.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import imageio.v2 as imageio
import mujoco
import numpy as np

from evaluator.core import EvaluatorCore, projected_gravity
from microduck.laser_task import world_to_body_xy, target_command, detect_red_spot

SUITE = ROOT / "experiments/laser/suite-v1.json"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def export_own(run_id, output):
    import torch
    import onnx
    import onnxruntime as ort
    from tensordict import TensorDict
    from rsl_rl.models import MLPModel
    from export_onnx import ExportedPolicy
    if not run_id.replace("-", "").replace("_", "").isalnum():
        raise ValueError("invalid run id")
    run_dir = ROOT / "logs" / run_id
    record = json.loads((run_dir/"run.json").read_text())
    if record["status"] != "completed" or record["schema"] != "microduck.laser-training/v1":
        raise ValueError("only a completed local laser training receipt is admitted")
    name = record["checkpoint"]
    checkpoint = run_dir / name
    if Path(name).name != name or checkpoint.is_symlink() or run_dir.is_symlink():
        raise ValueError("invalid checkpoint path")
    if digest(checkpoint) != record["checkpoint_sha256"]:
        raise ValueError("checkpoint digest mismatch")
    for source, sha in record["source_sha256"].items():
        if digest(ROOT/source) != sha:
            raise ValueError(f"training source changed: {source}")
    cfg = copy.deepcopy(record["train_cfg"])
    actor_cfg = cfg["actor"]
    actor_cfg.pop("class_name")
    actor = MLPModel(TensorDict({"policy": torch.zeros(1, 61)}, [1]), cfg["obs_groups"], "actor", 14, **actor_cfg)
    actor.load_state_dict(torch.load(checkpoint, map_location="cpu", weights_only=True)["actor_state_dict"], strict=True)
    actor.eval()
    exported = ExportedPolicy(actor).eval()
    path = output/"policy.onnx"
    torch.onnx.export(exported, torch.zeros(1, 61), path,
                      input_names=["obs"], output_names=["action"],
                      opset_version=17, dynamic_axes=None, dynamo=False)
    onnx.checker.check_model(onnx.load(path))
    session = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
    if session.get_inputs()[0].shape != [1, 61] or session.get_outputs()[0].shape != [1, 14]:
        raise ValueError("export shape mismatch")
    torch.manual_seed(74104)
    probe = torch.cat((torch.zeros(1, 61), torch.randn(64, 61)), 0)
    with torch.no_grad():
        expected = exported(probe).numpy()
    actual = np.concatenate([session.run(None, {"obs": row.numpy()[None]})[0] for row in probe])
    error = float(np.abs(expected-actual).max())
    if error >= 1e-4 or not np.isfinite(actual).all():
        raise ValueError(f"ONNX parity failed: {error}")
    (output/"normalizer.json").write_text(json.dumps({"mean": exported.mean.tolist(), "std": exported.std.tolist(), "epsilon": exported.eps}, indent=2)+"\n")
    (output/"training.json").write_text(json.dumps(record, indent=2)+"\n")
    # Keep the actual weights and exact new source alongside the export;
    # ignored working logs are not the sole copy of the completed experiment.
    shutil.copy2(checkpoint, output/"source-checkpoint.pt")
    source_dir = output/"source"
    for source in record["source_sha256"]:
        dest = source_dir/source
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT/source, dest)
    return path, {"random_observations": 65, "max_abs_action_error_rad": error}, exported


def target_at(case, t):
    xy = np.array(case["target_xy_m"], dtype=float)
    if case["kind"] == "moving":
        xy += [case["velocity_x_m_s"]*t,
               case["sine_y_amplitude_m"]*np.sin(case["sine_frequency_rad_s"]*t)]
    visible = case["kind"] != "loss" or t < case["lost_at_s"]
    return xy, visible


def summarize(case, rows, thresholds):
    last = rows[-1]
    good = [r["distance_m"] <= thresholds["reach_radius_m"] and r["speed_m_s"] <= thresholds["settled_speed_m_s"] for r in rows]
    longest = streak = 0
    for hit in good:
        streak = streak + 1 if hit else 0
        longest = max(longest, streak)
    fell = any(r["fell"] for r in rows)
    loss_rows = [r for r in rows if not r["visible"] and r["time_s"] >= case.get("lost_at_s", float("inf")) + thresholds["lost_target_grace_s"]]
    moving_rows = [r for r in rows if r["time_s"] >= 4]
    tracking = float(np.mean([r["distance_m"] <= thresholds["moving_track_radius_m"] for r in moving_rows])) if moving_rows else 0.
    if case["kind"] == "loss":
        behavior_pass = bool(loss_rows) and max(r["speed_m_s"] for r in loss_rows) <= thresholds["lost_target_speed_m_s"] and all(r["command"] == [0., 0., 0.] for r in loss_rows)
    elif case["kind"] == "moving":
        behavior_pass = tracking >= thresholds["moving_min_fraction_after_4s"]
    else:
        behavior_pass = longest/50 >= thresholds["minimum_settled_s"] and last["distance_m"] <= thresholds["reach_radius_m"]
    return {"case_id": case["id"], "passed": bool(behavior_pass and not fell), "fell": fell,
            "duration_s": last["time_s"], "initial_distance_m": rows[0]["distance_m"],
            "final_distance_m": last["distance_m"], "minimum_distance_m": min(r["distance_m"] for r in rows),
            "max_settled_duration_s": longest/50,
            "moving_track_fraction_after_4s": tracking if case["kind"] == "moving" else None,
            "max_lost_target_speed_m_s": max((r["speed_m_s"] for r in loss_rows), default=None),
            "final_robot_xy_m": last["robot_xyz_m"][:2],
            "inference_deadline_misses": sum(r["latency_ms"] > 20 for r in rows if r.get("latency_ms") is not None)}


def main():
    p = argparse.ArgumentParser()
    choice = p.add_mutually_exclusive_group(required=True)
    choice.add_argument("--run-id")
    choice.add_argument("--baseline", action="store_true")
    p.add_argument("--bam-repo", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--video", action="store_true")
    args = p.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    exported = None
    if args.baseline:
        policy = ROOT/"receipts/first-party-development/20260904-walking-seed-26090401-v1/policy.normalized.fixed-batch.onnx"
        if digest(policy) != "843d5d9aa788334d43e95607fb917af560c61550080c92357825d360fb5b690f":
            raise ValueError("baseline digest mismatch")
        parity = None
    else:
        policy, parity, exported = export_own(args.run_id, output)
    suite = json.loads(SUITE.read_text())
    (output/"suite.json").write_text(json.dumps(suite, indent=2)+"\n")
    reports = []
    real_parity = 0.
    detections = renders = 0
    with (output/"trajectory.jsonl").open("w") as trajectory:
        for case in suite["cases"]:
            core = EvaluatorCore(policy, args.bam_repo, "microduck.walking.v1")
            core.model.vis.quality.offsamples = 1
            core.reset([0, 0, .125], [1, 0, 0, 0])
            last_action = np.zeros(14, dtype=np.float32)
            rows = []
            renderer = mujoco.Renderer(core.model, height=480, width=640) if args.video else None
            writer = imageio.get_writer(output/f"{case['id']}.mp4", fps=50, codec="libx264", quality=7) if renderer else None
            camera = mujoco.MjvCamera()
            camera.type = mujoco.mjtCamera.mjCAMERA_FREE
            camera.lookat[:] = [0.3, 0, .12]
            camera.distance, camera.azimuth, camera.elevation = 1.4, 120, -35
            try:
                for step in range(round(case["seconds"]*50)):
                    t = step/50
                    target, visible = target_at(case, t)
                    relative = world_to_body_xy(target, core.data.qpos[:2], core.data.qpos[3:7])
                    command = target_command(relative, visible)
                    observation = core.observation_vector(last_action, command, np.zeros(4), np.zeros(6))
                    action, latency = core.policy.infer(observation)
                    if exported is not None:
                        import torch
                        with torch.no_grad():
                            real_parity = max(real_parity, float(np.abs(exported(torch.from_numpy(observation)).numpy()-action).max()))
                    last_action = action[0].copy()
                    for j, name in enumerate(core.joint_names):
                        core.controller.set_q_target(name, float(core.home[j]+last_action[j]))
                    for _ in range(4):
                        core.controller.update()
                        mujoco.mj_step(core.model, core.data)
                    if not np.isfinite(np.r_[core.data.qpos, core.data.qvel, core.data.ctrl]).all():
                        raise ValueError("nonfinite simulator state")
                    gravity = projected_gravity(core.data.qpos[3:7])
                    tilt = float(np.degrees(np.arccos(np.clip(-gravity[2], -1, 1))))
                    threshold = suite["thresholds"]
                    fell = core.data.qpos[2] < threshold["minimum_height_m"] or tilt > threshold["maximum_tilt_deg"]
                    row = {"case_id": case["id"], "time_s": (step+1)/50,
                           "robot_xyz_m": core.data.qpos[:3].tolist(), "target_xy_m": target.tolist(),
                           "distance_m": float(np.linalg.norm(target-core.data.qpos[:2])),
                           "speed_m_s": float(np.linalg.norm(core.data.qvel[:2])),
                           "visible": bool(visible), "command": command.tolist(),
                           "action_rad": last_action.tolist(), "fell": bool(fell),
                           "tilt_deg": tilt, "latency_ms": latency}
                    rows.append(row)
                    trajectory.write(json.dumps(row)+"\n")
                    if renderer:
                        renderer.update_scene(core.data, camera=camera)
                        if visible:
                            geom = renderer.scene.geoms[renderer.scene.ngeom]
                            mujoco.mjv_initGeom(geom, mujoco.mjtGeom.mjGEOM_SPHERE,
                                               np.array([.012]*3), np.r_[target, .006],
                                               np.eye(3).reshape(-1), np.array([1., 0., 0., 1.]))
                            geom.emission = 1
                            renderer.scene.ngeom += 1
                        frame = renderer.render().copy()
                        if visible:
                            renders += 1
                            detections += detect_red_spot(frame, max_pixels=300) is not None
                        writer.append_data(frame)
                    if fell:
                        break  # Keep the fall visible; never reset to hide it.
            finally:
                if renderer:
                    renderer.close()
                if writer:
                    writer.close()
            report = summarize(case, rows, suite["thresholds"])
            reports.append(report)
            print(json.dumps(report), flush=True)
    if exported is not None and real_parity >= 1e-4:
        raise ValueError(f"real-observation export parity failed: {real_parity}")
    result = {"schema": "microduck.laser-evaluation/v1", "proof_class": "first_party_development",
              "held_out": False, "target_source": suite["target_source"],
              "policy_sha256": digest(policy), "suite_sha256": digest(SUITE),
              "evaluator_sha256": digest(Path(__file__)), "core_sha256": digest(ROOT/"evaluator/core.py"),
              "case_reports": reports, "passed_cases": sum(r["passed"] for r in reports),
              "total_cases": len(reports), "export_random_parity": parity,
              "export_real_observation_max_error_rad": real_parity if exported is not None else None,
              "rendered_spot_detector": {"visible_frames": renders, "detections": detections, "controls_robot": False},
              "boundary": suite["boundary"]}
    (output/"evaluation.json").write_text(json.dumps(result, indent=2)+"\n")
    (output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.relative_to(output)}\n" for f in sorted(output.rglob("*")) if f.is_file() and f.name != "SHA256SUMS"))
    print(json.dumps({"passed_cases": result["passed_cases"], "total_cases": len(reports)}))


if __name__ == "__main__":
    main()
