"""Full exposed-bank intermediate diagnosis; never candidate selection.

Uses the normalized Torch mean, not an accepted ONNX export. Includes every
timing/command bucket so a small spot check cannot hide a long-delay failure.
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--iteration", required=True, type=int)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if not args.run_id.replace("-", "").isalnum() or args.iteration < 0:
        parser.error("simple run ID and nonnegative diagnostic iteration required")
    folder = ROOT / "logs" / args.run_id
    checkpoint = folder / f"model_{args.iteration}.pt"
    checkpoint_sha = digest(checkpoint)
    record = json.loads((folder / "run.json").read_text())
    freeze = ROOT / "experiments/walking/evaluator-freeze-sensor-v1.json"
    sources = dict(record["source_sha256"])
    sources.update(json.loads(freeze.read_text())["source_sha256"])
    for name in ("scripts/probe_walking_full_checkpoint.py", "experiments/walking/heading.py",
                 "experiments/walking/HEADING-v1.md", "tests/test_walking_heading.py"):
        sources[name] = digest(ROOT / name)
    for name, sha in sources.items():
        if digest(ROOT / name) != sha:
            raise ValueError(f"source drift: {name}")
    args.output.mkdir(parents=True, exist_ok=False)

    import numpy as np
    import torch
    from tensordict import TensorDict
    from rsl_rl.models import MLPModel
    from export_onnx import ExportedPolicy
    from experiments.walking.sensor_world import ConsistentSensorWalkingWorld
    from experiments.walking.posture import evaluate_case
    from experiments.walking.heading import evaluate_heading
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
    reports = []
    with (args.output / "trajectory.jsonl").open("w") as stream:
        for timing in suite["timing_profiles"]:
            for case in suite["cases"]:
                name = timing["id"] + "--" + case["id"]
                world = ConsistentSensorWalkingWorld(
                    ROOT / "receipts/laser-gait/20260905-v4-evaluation/policy.onnx",
                    ROOT / ".workspace/bam", motor_ticks=timing["motor_ticks"],
                    sensor_ticks=timing["sensor_ticks"], yaw=case["yaw"], seed=suite["seed"])
                world.core.policy = TorchPolicy()
                probe = GaitProbe(world.core)
                rows = []
                try:
                    for i in range(900):
                        command = case["command"] if 1 <= i * .02 < 13 else [0, 0, 0]
                        row = probe.sample(world.step_command(command))
                        row["case_id"] = name
                        row["actor_observation"] = world.last_observation[0].tolist()
                        rows.append(row)
                        stream.write(json.dumps(row) + "\n")
                        if world.fell:
                            break
                    report = evaluate_case(rows, case, suite)
                    report.update(case_id=name, heading=evaluate_heading(rows))
                    report["combined_passed"] = report["passed"] and report["heading"]["passed"]
                    reports.append(report)
                    print(json.dumps({key: value for key, value in report.items() if key != "gait"}), flush=True)
                finally:
                    world.close()
    if digest(checkpoint) != checkpoint_sha:
        raise ValueError("checkpoint changed during diagnostic")
    for name, sha in sources.items():
        if digest(ROOT / name) != sha:
            raise ValueError(f"source changed during diagnostic: {name}")
        destination = args.output / "source" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, destination)
    result = {"schema": "microduck.walking-intermediate-full-bank/v1",
              "iteration": args.iteration, "checkpoint_sha256": checkpoint_sha,
              "candidate_selection_eligible": False, "held_out": False,
              "case_reports": reports, "total_cases": 21,
              "motor_posture_passed_cases": sum(case["passed"] for case in reports),
              "heading_passed_cases": sum(case["heading"]["passed"] for case in reports),
              "combined_passed_cases": sum(case["combined_passed"] for case in reports),
              "source_sha256": sources, "evaluator_freeze_sha256": digest(freeze),
              "inference": "Torch CPU normalized deterministic mean; not ONNX acceptance",
              "boundary": "All 21 exposed current-sensor command/timing cases, intermediate diagnosis only. No source/threshold mutation, missing-bucket averaging, checkpoint promotion or physical acceptance."}
    (args.output / "probe.json").write_text(json.dumps(result, indent=2) + "\n")
    shutil.copy2(checkpoint, args.output / "source-checkpoint.pt")
    shutil.copy2(folder / "run.json", args.output / "training-at-probe.json")
    (args.output / "SHA256SUMS").write_text("".join(
        f"{digest(path)}  {path.relative_to(args.output)}\n"
        for path in sorted(args.output.rglob("*")) if path.is_file()))
    print(json.dumps({key: result[key] for key in
                     ("total_cases", "motor_posture_passed_cases", "heading_passed_cases", "combined_passed_cases")}))


if __name__ == "__main__":
    main()
