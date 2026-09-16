"""Intermediate diagnosis on complete contacts; never checkpoint selection.

The fixed v12 command controller is explicit. Every exposed command/timing
bucket is included; unchanged motor, head, heading and body-contact gates are
reported separately. Torch CPU inference is diagnostic, not ONNX acceptance.
"""
import argparse
import copy
import json
from pathlib import Path
import shutil
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.evaluate_laser import digest


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run-id", required=True)
    p.add_argument("--iteration", required=True, type=int)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--raw-actor", action="store_true")
    p.add_argument("--video", action="store_true", help="retain slow forward, long fast forward and left turn")
    a = p.parse_args()
    if not a.run_id.replace("-", "").isalnum() or a.iteration < 0:
        p.error("simple run ID and nonnegative iteration required")
    folder = ROOT / "logs" / a.run_id
    checkpoint = folder / f"model_{a.iteration}.pt"
    checkpoint_sha = digest(checkpoint)
    record = json.loads((folder / "run.json").read_text())
    freeze = ROOT / "experiments/walking/evaluator-freeze-persistent-controller-v13.json"
    sources = dict(record["source_sha256"])
    sources.update(json.loads(freeze.read_text())["source_sha256"])
    sources["scripts/probe_walking_complete_checkpoint.py"] = digest(Path(__file__))
    for name, sha in sources.items():
        if digest(ROOT / name) != sha:
            raise ValueError(f"source drift: {name}")
    a.output.mkdir(parents=True, exist_ok=False)

    import numpy as np
    import torch
    from tensordict import TensorDict
    from rsl_rl.models import MLPModel
    from export_onnx import ExportedPolicy
    from experiments.walking.collision_world import CompleteContactWalkingWorld
    from experiments.walking.heading_servo_world import HeadingServoWalkingWorld
    from experiments.walking.posture import evaluate_case
    from experiments.walking.heading import evaluate_heading
    from experiments.walking.self_contact import SelfContactProbe, evaluate_self_contact
    from experiments.laser.gait import GaitProbe
    torch.set_num_threads(1)
    cfg = copy.deepcopy(record["train_cfg"])
    cfg["actor"].pop("class_name")
    actor = MLPModel(TensorDict({"policy": torch.zeros(1, 61)}, [1]),
                     cfg["obs_groups"], "actor", 14, **cfg["actor"])
    actor.load_state_dict(torch.load(checkpoint, map_location="cpu", weights_only=True)["actor_state_dict"])
    actor.eval()
    policy = ExportedPolicy(actor).eval()

    class TorchPolicy:
        def infer(self, obs):
            start = time.monotonic()
            with torch.no_grad():
                action = policy(torch.from_numpy(obs)).numpy()
            return action, (time.monotonic() - start) * 1000

    suite = json.loads((ROOT / "experiments/walking/tracking-suite-v1.json").read_text())
    model_directory = ROOT / "experiments/walking/models/contact-v11"
    geometry = SelfContactProbe(model_directory / "scene.xml")
    world_type = CompleteContactWalkingWorld if a.raw_actor else HeadingServoWalkingWorld
    reports = []
    with (a.output / "trajectory.jsonl").open("w") as stream:
        for timing in suite["timing_profiles"]:
            for case in suite["cases"]:
                name = timing["id"] + "--" + case["id"]
                video = a.video and name in {
                    "nominal-20-20ms--forward-08", "long-30-20ms--forward-20",
                    "nominal-20-20ms--turn-left"}
                world = world_type(
                    ROOT / "receipts/laser-gait/20260905-v4-evaluation/policy.onnx",
                    ROOT / ".workspace/bam", model_directory=model_directory,
                    motor_ticks=timing["motor_ticks"], sensor_ticks=timing["sensor_ticks"],
                    yaw=case["yaw"], seed=suite["seed"], render=video)
                world.core.policy = TorchPolicy()
                probe, rows = GaitProbe(world.core), []
                writer = None
                if video:
                    import imageio.v2 as imageio
                    writer = imageio.get_writer(a.output / f"{name}.mp4", fps=25, codec="libx264", quality=7)
                try:
                    for i in range(round(suite["duration_s"] * 50)):
                        command = case["command"] if suite["move_start_s"] <= i * .02 < suite["stop_start_s"] else [0, 0, 0]
                        row = probe.sample(world.step_command(command))
                        row.update(case_id=name, actor_observation=world.last_observation[0].tolist())
                        np.testing.assert_array_equal(np.asarray(row["command"], np.float32), np.asarray(command, np.float32))
                        rows.append(row)
                        stream.write(json.dumps(row) + "\n")
                        if writer and i % 2 == 0:
                            writer.append_data(world.walking_frame())
                        if world.fell:
                            break
                    report = evaluate_case(rows, case, suite)
                    report.update(case_id=name, heading=evaluate_heading(rows),
                                  self_contact=evaluate_self_contact(rows, geometry))
                    report["combined_passed"] = report["passed"] and report["heading"]["passed"] and report["self_contact"]["passed"]
                    reports.append(report)
                    print(json.dumps({key: value for key, value in report.items() if key != "gait"}), flush=True)
                finally:
                    if writer:
                        writer.close()
                    world.close()
    if digest(checkpoint) != checkpoint_sha:
        raise ValueError("checkpoint changed during diagnostic")
    for name, sha in sources.items():
        if digest(ROOT / name) != sha:
            raise ValueError(f"source changed during diagnostic: {name}")
        destination = a.output / "source" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, destination)
    result = {"schema": "microduck.walking-intermediate-complete-bank/v1",
              "iteration": a.iteration, "checkpoint_sha256": checkpoint_sha,
              "candidate_selection_eligible": False, "held_out": False,
              "case_reports": reports, "total_cases": len(reports),
              "motor_posture_passed_cases": sum(case["passed"] for case in reports),
              "heading_passed_cases": sum(case["heading"]["passed"] for case in reports),
              "self_contact_passed_cases": sum(case["self_contact"]["passed"] for case in reports),
              "combined_passed_cases": sum(case["combined_passed"] for case in reports),
              "source_sha256": sources, "evaluator_freeze_sha256": digest(freeze),
              "controller": "raw actor" if a.raw_actor else "fixed v12 upstream IMU heading command servo",
              "model_scope": {"variant": "complete-contact-v11", "scene_sha256": digest(model_directory / "scene.xml"),
                              "robot_sha256": digest(model_directory / "robot.xml"), "old_reduced_model_acceptance": False},
              "inference": "Torch CPU normalized deterministic mean; not ONNX acceptance",
              "boundary": "All 21 exposed current-sensor command/timing cases, intermediate diagnosis only. No checkpoint promotion, hidden test or physical acceptance. Motor actions unfiltered; command controller explicitly declared."}
    (a.output / "probe.json").write_text(json.dumps(result, indent=2) + "\n")
    shutil.copy2(checkpoint, a.output / "source-checkpoint.pt")
    (a.output / "training-at-probe.json").write_text(json.dumps(record, indent=2) + "\n")
    (a.output / "SHA256SUMS").write_text("".join(
        f"{digest(path)}  {path.relative_to(a.output)}\n"
        for path in sorted(a.output.rglob("*")) if path.is_file()))
    print(json.dumps({key: value for key, value in result.items() if key.endswith("cases")}), flush=True)


if __name__ == "__main__":
    main()
