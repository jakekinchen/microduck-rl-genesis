"""Bind raw run/test logs and an interpretable learning curve to a receipt."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.evaluate_laser import digest


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--evaluation", required=True, type=Path)
    p.add_argument("--training-log", required=True, type=Path)
    p.add_argument("--test-log", required=True, type=Path)
    args = p.parse_args()
    evaluation = json.loads((args.evaluation/"evaluation.json").read_text())
    training = json.loads((args.evaluation/"training.json").read_text())
    if training["status"] != "completed" or evaluation["policy_sha256"] != digest(args.evaluation/"policy.onnx"):
        raise ValueError("receipt is not a completed verified laser experiment")
    for src, name in ((args.training_log, "training.stdout.log"), (args.test_log, "tests.stdout.log")):
        dest = args.evaluation/name
        if dest.exists():
            raise ValueError(f"refusing to replace {dest}")
        shutil.copy2(src, dest)
    raw = re.sub(r"\x1b\[[0-9;]*m", "", args.training_log.read_text())
    curves = []
    for block in raw.split("Learning iteration ")[1:]:
        iteration = int(block.split("/", 1)[0])
        def scalar(label):
            match = re.search(re.escape(label)+r":\s*([-+0-9.eE]+)", block)
            return float(match.group(1)) if match else None
        curves.append({"iteration": iteration, "mean_reward": scalar("Mean reward"),
                       "mean_episode_length_steps": scalar("Mean episode length"),
                       "laser_progress_rate": scalar("Mean episode rew_laser_progress")})
    if len(curves) != training["args"]["iterations"]:
        raise ValueError("training log does not contain the complete iteration budget")
    (args.evaluation/"learning-curve.json").write_text(json.dumps(curves, indent=2)+"\n")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.4), constrained_layout=True)
    x = [r["iteration"] for r in curves]
    axes[0].plot(x, [r["mean_reward"] for r in curves], color="#0d9488")
    axes[0].set_ylabel("Training reward (not task success)")
    axes[1].plot(x, [r["mean_episode_length_steps"]*.02 for r in curves], color="#7c3aed")
    axes[1].set_ylabel("Mean stochastic episode duration (s)")
    for ax in axes:
        ax.set_xlabel("Laser PPO iteration")
        ax.grid(alpha=.2)
    fig.suptitle("Microduck laser-goal training · privileged target coordinates")
    fig.savefig(args.evaluation/"learning-curve.png", dpi=160)
    plt.close(fig)
    # Record the receipt tooling too; these sources never alter policy actions.
    for name in ("scripts/evaluate_laser.py", "scripts/retain_laser_receipt.py", "tests/test_laser_task.py"):
        dest = args.evaluation/"source"/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            raise ValueError(f"source snapshot already exists: {dest}")
        shutil.copy2(ROOT/name, dest)
    manifest = args.evaluation/"SHA256SUMS"
    manifest.write_text("".join(f"{digest(f)}  {f.relative_to(args.evaluation)}\n" for f in sorted(args.evaluation.rglob("*")) if f.is_file() and f != manifest))
    print(f"Retained {len(curves)} training iterations and checksummed receipt payloads")


if __name__ == "__main__":
    main()
