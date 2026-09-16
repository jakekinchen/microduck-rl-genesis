"""Retain completed training evidence without treating it as behavior acceptance."""
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
    p.add_argument("--run-id", required=True)
    p.add_argument("--stdout", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--test-log", type=Path, action="append", default=[])
    a = p.parse_args()
    if not a.run_id.replace("-", "").isalnum():
        raise ValueError("invalid run id")
    run = ROOT/"logs"/a.run_id
    record = json.loads((run/"run.json").read_text())
    completed = record["args"]["num_envs"]*record["args"]["iterations"]*24
    counts = [int(n) for n in re.findall(r"Total steps:\s*(\d+)", a.stdout.read_text())]
    if record["status"] != "completed" or record["new_transitions"] != completed or max(counts, default=0) != completed:
        raise ValueError("completion and logged transition counts must agree")
    checkpoint = run/record["checkpoint"]
    if checkpoint.parent != run or digest(checkpoint) != record["checkpoint_sha256"]:
        raise ValueError("final checkpoint identity mismatch")
    for name, sha in record["source_sha256"].items():
        if digest(run/"source"/name) != sha or digest(ROOT/name) != sha:
            raise ValueError(f"training source drift: {name}")
    a.output.mkdir(parents=True, exist_ok=False)
    shutil.copy2(run/"run.json", a.output/"training.json")
    shutil.copy2(a.stdout, a.output/"training.stdout.log")
    shutil.copytree(run/"source", a.output/"source")
    for f in sorted(run.glob("model_*.pt")):
        shutil.copy2(f, a.output/f.name)
    for f in sorted(run.glob("events.out.tfevents.*")):
        shutil.copy2(f, a.output/f.name)
    for i, log in enumerate(a.test_log):
        shutil.copy2(log, a.output/f"validation-{i}-{log.name}")
    receipt = {"schema": "microduck.completed-walking-training-receipt/v1", "new_transitions": completed,
        "checkpoint_sha256": record["checkpoint_sha256"], "policy_accepted": False,
        "boundary": "Completed bounded local training and retained intermediate diagnostic checkpoints. Only the declared final checkpoint is a candidate; task acceptance requires its separate frozen evaluation."}
    (a.output/"receipt.json").write_text(json.dumps(receipt, indent=2)+"\n")
    shutil.copy2(Path(__file__), a.output/"retention-source.py")
    (a.output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.relative_to(a.output)}\n" for f in sorted(a.output.rglob("*")) if f.is_file()))
    print(json.dumps(receipt), flush=True)


if __name__ == "__main__":
    main()
