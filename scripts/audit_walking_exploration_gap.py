"""Feedback ablation of trained Gaussian sampling versus exported mean.

Diagnostic only: stochastic actions must never be substituted for deployment
or accepted as a fix. Checkpoint, clock, model and commands stay fixed.
"""
import argparse
import copy
import inspect
import json
from pathlib import Path
import shutil
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.run_id.replace("-", "").isalnum():
        parser.error("simple run ID required")
    from scripts.evaluate_laser import digest
    folder = ROOT / "logs" / args.run_id
    record = json.loads((folder / "run.json").read_text())
    if record["status"] != "completed":
        raise ValueError("completed final checkpoint required")
    checkpoint = folder / record["checkpoint"]
    if digest(checkpoint) != record["checkpoint_sha256"]:
        raise ValueError("checkpoint digest mismatch")
    sources = dict(record["source_sha256"])
    for name in ("scripts/audit_walking_exploration_gap.py", "export_onnx.py",
                 "experiments/walking/sensor_world.py", "experiments/walking/world.py",
                 "experiments/walking/posture.py", "experiments/walking/metrics.py",
                 "experiments/walking/tracking-suite-v1.json", "experiments/laser/gait.py"):
        sources.setdefault(name, digest(ROOT / name))
    for name, sha in sources.items():
        if digest(ROOT / name) != sha:
            raise ValueError(f"source changed: {name}")
    args.output.mkdir(parents=True, exist_ok=False)

    import numpy as np
    import torch
    from tensordict import TensorDict
    from rsl_rl.models import MLPModel
    from export_onnx import ExportedPolicy
    from experiments.walking.sensor_world import ConsistentSensorWalkingWorld
    from experiments.walking.posture import evaluate_case
    from experiments.laser.gait import GaitProbe

    torch.set_num_threads(1)
    cfg = copy.deepcopy(record["train_cfg"])
    cfg["actor"].pop("class_name")
    actor = MLPModel(TensorDict({"policy": torch.zeros(1, 61)}, [1]),
                     cfg["obs_groups"], "actor", 14, **cfg["actor"])
    actor.load_state_dict(torch.load(checkpoint, map_location="cpu", weights_only=True)["actor_state_dict"])
    actor.eval()
    exported = ExportedPolicy(actor).eval()
    normalizer_before = {k: v.clone() for k, v in actor.obs_normalizer.state_dict().items()}
    suite = json.loads((ROOT / "experiments/walking/tracking-suite-v1.json").read_text())
    case = next(c for c in suite["cases"] if c["id"] == "turn-right")
    parity = []

    class DiagnosticPolicy:
        def __init__(self, stochastic):
            self.stochastic = stochastic

        def infer(self, obs):
            start = time.monotonic()
            tensor = torch.from_numpy(obs)
            td = TensorDict({"policy": tensor}, [1])
            with torch.no_grad():
                mean = actor(td, stochastic_output=False)
                error = float((mean - exported(tensor)).abs().max())
                parity.append(error)
                if error > 1e-5:
                    raise ValueError("mean/export path mismatch")
                action = actor(td, stochastic_output=True) if self.stochastic else mean
            return action.numpy(), (time.monotonic() - start) * 1000

    reports = []
    # Exact published failing case plus four predeclared RNG seeds. One mean
    # reference suffices: without sampling the seed has no effect on this world.
    for stochastic, seed in ((False, 76601), (True, 76601), (True, 76602),
                              (True, 76603), (True, 76604)):
        torch.manual_seed(seed)
        name = f'{"sampled" if stochastic else "mean"}-{seed}'
        world = ConsistentSensorWalkingWorld(
            ROOT / "receipts/laser-gait/20260905-v4-evaluation/policy.onnx",
            ROOT / ".workspace/bam", motor_ticks=0, sensor_ticks=0,
            yaw=case["yaw"], seed=suite["seed"], render=False)
        world.core.policy = DiagnosticPolicy(stochastic)
        probe = GaitProbe(world.core)
        rows = []
        try:
            for i in range(900):
                command = case["command"] if 1 <= i * .02 < 13 else [0, 0, 0]
                row = probe.sample(world.step_command(command))
                row["actor_observation"] = world.last_observation[0].tolist()
                rows.append(row)
                if world.fell:
                    break
            (args.output / f"{name}.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
            result = evaluate_case(rows, case, suite)
            result.update(diagnostic_case=name, stochastic=stochastic, torch_seed=seed)
            reports.append(result)
            print(json.dumps({k: v for k, v in result.items() if k != "gait"}), flush=True)
        finally:
            world.close()
    for key, value in normalizer_before.items():
        if not torch.equal(value, actor.obs_normalizer.state_dict()[key]):
            raise ValueError("diagnostic updated observation normalizer")
    if digest(checkpoint) != record["checkpoint_sha256"]:
        raise ValueError("checkpoint changed")
    for name, sha in sources.items():
        if digest(ROOT / name) != sha:
            raise ValueError(f"source changed during diagnostic: {name}")
        destination = args.output / "source" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, destination)
    library_sources = {}
    for cls in (type(actor), type(actor.distribution)):
        path = Path(inspect.getfile(cls))
        destination = args.output / "library-source" / path.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        library_sources[str(path)] = digest(path)
    report = {"schema": "microduck.walking-exploration-gap/v1", "cases": reports,
              "checkpoint_sha256": record["checkpoint_sha256"], "source_sha256": sources,
              "library_sha256": library_sources, "acceptance_eligible": False,
              "learned_std_rad": actor.output_std[0].detach().tolist(),
              "mean_export_max_abs_error_rad": max(parity),
              "normalizer_unchanged": True,
              "boundary": "Single failing fixed-clock feedback case; sampling changes actions using the trained distribution, not fixed-action simulator isolation. No noise deployment, candidate selection or physical acceptance."}
    (args.output / "diagnosis.json").write_text(json.dumps(report, indent=2) + "\n")
    shutil.copy2(checkpoint, args.output / "source-checkpoint.pt")
    shutil.copy2(folder / "run.json", args.output / "training.json")
    (args.output / "SHA256SUMS").write_text("".join(
        f"{digest(path)}  {path.relative_to(args.output)}\n"
        for path in sorted(args.output.rglob("*")) if path.is_file()))


if __name__ == "__main__":
    main()
