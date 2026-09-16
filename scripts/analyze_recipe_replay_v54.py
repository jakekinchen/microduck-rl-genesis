"""Post-hoc action-fit diagnostics; does not evaluate or change a behavior gate."""
import argparse
from collections import Counter, defaultdict
import copy
import gzip
import json
from pathlib import Path
import shutil
import sys

import numpy as np
import torch
from tensordict import TensorDict

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.walking.recipe_v54 import REPLAY, candidate, digest, run_name, storage_ready
from microduck.recipe_actor_v54 import RoutedActor, SharedActor
from scripts.train_recipe_v54 import INIT_RUN


def groups(observations, case_ids):
    moving = (observations[:, 48:51] != 0).any(1)
    boundary = np.r_[True, case_ids[1:] != case_ids[:-1]]
    previous = np.r_[False, moving[:-1]]
    start = moving & (~previous | boundary)
    stop = ~moving & previous & ~boundary
    return {
        "all": np.ones(len(moving), bool),
        "moving": moving,
        "zero_command": ~moving,
        "first_nonzero_control": start,
        "first_zero_after_nonzero": stop,
        "continued_nonzero": moving & ~start,
    }


def summarize(predictions, labels, masks):
    error = np.abs(predictions.astype(np.float64) - labels)
    if not np.isfinite(error).all():
        raise ValueError("nonfinite fit diagnostic")
    maximum = error.max(1)
    return {
        name: {
            "rows": int(mask.sum()),
            "rmse_rad": float(np.sqrt(np.mean(error[mask] ** 2))),
            "max_error_rad": float(error[mask].max()),
            "rows_max_error_over_0_1_rad": int((maximum[mask] > .1).sum()),
        }
        for name, mask in masks.items()
    }


def training_falls(folder, record):
    last_switch = {}
    with gzip.open(folder / "handoff-histories.jsonl.gz", "rt") as stream:
        for line in stream:
            row = json.loads(line)
            last_switch[row["env"], row["episode"]] = (row["global_step"], row["direction"])
    counts, falls = defaultdict(Counter), []
    with gzip.open(folder / "episodes.jsonl.gz", "rt") as stream:
        for line in stream:
            row = json.loads(line)
            if not row["fell"]:
                continue
            latest = last_switch.get((row["env"], row["episode"]))
            mode = "walking" if latest and latest[1] == "stand-to-walk" else "standing"
            elapsed = row["global_control"] - latest[0] if latest else row["controls"]
            assert elapsed >= 0
            name = record["final_coverage"]["buckets"][row["bucket"]]
            terrain = "downhill" if name.startswith("downhill") else "uphill" if name.startswith("uphill") else "flat"
            counts[terrain][mode] += 1
            counts[terrain]["within_0_5s_of_switch"] += int(latest is not None and elapsed <= 25)
            falls.append({**row, "bucket_name": name, "last_actor_mode": mode,
                          "seconds_after_last_switch": elapsed * .02})
    assert len(falls) == sum(record["final_coverage"]["falls"])
    return {"total": len(falls), "counts_by_terrain": dict(counts), "falls": falls,
            "boundary": "Stochastic training falls grouped by the last recorded actor-mode switch. Temporal association does not establish which actor or physical mechanism caused a fall."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    storage_ready()
    if args.output.exists():
        raise FileExistsError(args.output)
    torch.set_num_threads(1)
    data = np.load(REPLAY / "replay.npz")
    observations, labels = data["observations"], data["actions"]
    masks = groups(observations, data["case_ids"])
    initializer = ROOT / "logs" / INIT_RUN
    predictions = np.load(initializer / "predictions-float32.npy")
    reports = {"shared_initializer": summarize(predictions, labels, masks)}
    fall_reports = {}
    bindings = {"replay_sha256": digest(REPLAY / "replay.npz"),
                "initializer_predictions_sha256": digest(initializer / "predictions-float32.npy")}
    for recipe, cls in [("routed", RoutedActor), ("shared", SharedActor)]:
        candidate(recipe)
        folder = ROOT / "logs" / run_name(recipe)
        record = json.loads((folder / "run.json").read_text())
        checkpoint = folder / record["checkpoint"]
        state = torch.load(checkpoint, map_location="cpu", weights_only=True)["actor_state_dict"]
        config = copy.deepcopy(record["train_cfg"]["actor"])
        config.pop("class_name")
        sample = TensorDict({"policy": torch.zeros(1, 61)}, [1])
        actor = cls(sample, {"actor": ["policy"]}, "actor", 14, **config).eval()
        actor.load_state_dict(state, strict=True)
        predictions = []
        with torch.no_grad():
            for offset in range(0, len(observations), 1024):
                batch = torch.from_numpy(observations[offset:offset + 1024])
                predictions.append(actor(TensorDict({"policy": batch}, [len(batch)])).numpy())
        reports[recipe + "_final"] = summarize(np.concatenate(predictions), labels, masks)
        fall_reports[recipe] = training_falls(folder, record)
        bindings[recipe + "_checkpoint_sha256"] = digest(checkpoint)
    args.output.mkdir(parents=True)
    shutil.copy2(__file__, args.output / Path(__file__).name)
    result = {
        "complete": True, "bindings": bindings, "groups": reports,
        "training_fall_diagnostics": fall_reports,
        "boundary": "Post-hoc fit on the original exposed rehearsal observations. The 0.1-radian count is a descriptive diagnostic, not an acceptance threshold. First-control masks restart at case boundaries. No physics, new training, counterfactual rollout, candidate selection or gate changes.",
    }
    (args.output / "analysis.json").write_text(json.dumps(result, indent=2) + "\n")
    from experiments.walking.recipe_v54 import write_manifest
    write_manifest(args.output)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
