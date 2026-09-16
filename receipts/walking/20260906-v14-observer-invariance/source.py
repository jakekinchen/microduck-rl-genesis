"""Retain full-bank invariance proof for an additive force observer (no physics)."""
import argparse
from itertools import zip_longest
import json
from pathlib import Path
import shutil
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.evaluate_laser import digest
from scripts.evaluate_walking_heading import verify_input_manifest


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--before", type=Path, required=True)
    p.add_argument("--observed", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    import numpy as np
    for folder in (a.before, a.observed):
        verify_input_manifest(folder)
    hashes = [digest(folder/"SHA256SUMS") for folder in (a.before, a.observed)]
    before, observed = [json.loads((folder/"evaluation.json").read_text()) for folder in (a.before,a.observed)]
    for key in ("policy_sha256", "model_scope", "suite_sha256", "total_cases"):
        if before[key] != observed[key]:
            raise ValueError(f"changed comparison input: {key}")
    identifiers = {c["case_id"] for c in before["case_reports"]}
    if identifiers != {c["case_id"] for c in observed["case_reports"]} or len(identifiers) != before["total_cases"]:
        raise ValueError("case population changed")
    frames, seen = 0, set()
    with (a.before/"trajectory.jsonl").open() as first, (a.observed/"trajectory.jsonl").open() as second:
        for left, right in zip_longest(first, second):
            if left is None or right is None:
                raise ValueError("trajectory length changed")
            x,y = json.loads(left),json.loads(right)
            for key in ("case_id", "time_s", "fell"):
                if x[key] != y[key]:
                    raise ValueError(f"changed control frame {frames}: {key}")
            for key, dtype in (("qpos", np.float64), ("qvel", np.float64), ("action_rad", np.float32),
                               ("actor_observation", np.float32), ("command", np.float32), ("policy_command", np.float32)):
                l,r = np.asarray(x[key],dtype),np.asarray(y[key],dtype)
                if l.shape != r.shape or not np.isfinite(l).all() or l.tobytes() != r.tobytes():
                    raise ValueError(f"changed frame {frames}: {key}")
            frames += 1
            seen.add(x["case_id"])
    if seen != identifiers:
        raise ValueError("missing complete case trace")
    for case in sorted(identifiers):
        name = case+"-actions-float32.npy"
        if digest(a.before/name) != digest(a.observed/name):
            raise ValueError("original action tensor file changed")
    if hashes != [digest(folder/"SHA256SUMS") for folder in (a.before,a.observed)]:
        raise ValueError("input manifest changed during audit")
    a.output.mkdir(parents=True, exist_ok=False)
    result = {"schema": "microduck.walking-observer-invariance/v1", "frames": frames, "cases": len(identifiers),
              "before": str(a.before), "observed": str(a.observed), "input_manifest_sha256": hashes,
              "physical_qpos_qvel_bytes_identical": True, "actor_observation_action_command_bytes_identical": True,
              "all_original_action_files_identical": True,
              "old_passed_cases": before["passed_cases"], "additive_passed_cases": observed["passed_cases"],
              "source_sha256": digest(Path(__file__)), "physical_transfer_validated": False,
              "boundary": "The full recorded baseline is unchanged by applied-load observation. New rejection is additional evidence, not altered dynamics or a physical force calibration."}
    (a.output/"audit.json").write_text(json.dumps(result,indent=2)+"\n")
    shutil.copy2(Path(__file__), a.output/"source.py")
    (a.output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.name}\n" for f in sorted(a.output.iterdir()) if f.is_file()))
    print(json.dumps(result),flush=True)


if __name__ == "__main__":
    main()
