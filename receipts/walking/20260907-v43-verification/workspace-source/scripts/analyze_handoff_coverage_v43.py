"""Validate source-actor branches and compare complete reset histories offline."""
import argparse
from collections import defaultdict
import gzip
import itertools
import json
from pathlib import Path
import pickle
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.evaluate_laser import digest
from scripts.probe_handoff_coverage_v43_r3 import INPUTS, seal
from scripts.verify_walking_sequence_v42 import verify_manifest
from experiments.walking.snapshots_v43 import load_state


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    verify_manifest(args.receipt)
    report = json.loads((args.receipt / "probe.json").read_text())
    if not report["complete"]:
        raise ValueError("completed diagnosis required")
    import numpy as np
    snapshots = {}
    for state in report["states"]:
        path = args.receipt / state["state_file"]
        if digest(path) != state["state_sha256"]:
            raise ValueError("snapshot identity mismatch")
        snapshots[state["id"]] = load_state(path, args.receipt / "snapshot-blobs")
    resets = [s for s in report["states"] if s["source"] == "training-reset"]
    histories = {}
    for state in report["states"]:
        current = snapshots[state["id"]]
        candidates = [s for s in resets if s["terrain"] == state["terrain"] and s["kind"] == state["kind"]]
        distances = {}
        for field in ("motor_history", "sensors", "previous_torque", "q_target", "damping", "friction"):
            value = np.asarray(current[field])
            alternatives = [(s["id"], np.asarray(snapshots[s["id"]][field])) for s in candidates]
            alternatives = [(name, a) for name, a in alternatives if a.shape == value.shape]
            distances[field] = {"shape": list(value.shape), "matched_reference_count": len(alternatives),
                "nearest_max_abs_difference": min((float(np.max(np.abs(a-value))) if value.size else 0. for _,a in alternatives), default=None)}
        histories[state["id"]] = distances
    reference = {}
    for name, relative in INPUTS.items():
        directory = ROOT / relative
        verify_manifest(directory)
        path = directory / "trajectory.jsonl"
        if not path.exists():
            path = directory / "trajectory.jsonl.gz"
        opener = gzip.open if path.suffix == ".gz" else open
        with opener(path, "rt") as stream:
            for session, group in itertools.groupby((json.loads(line) for line in stream), lambda r:r["session_id"]):
                reference[name, session] = [{k:r[k] for k in ("qpos", "actor_mode", "action_rad", "actor_observation", "fell")} for r in group]
    state_by_branch = {v["case_id"]:(s, actor) for s in report["states"] for actor,v in s["branches"].items()}
    branches = {}; reproduction = []
    with gzip.open(args.receipt / "branches.jsonl.gz", "rt") as stream:
        for name, group in itertools.groupby((json.loads(line) for line in stream), lambda r:r["case_id"]):
            state, actor = state_by_branch[name]
            rows = list(group)
            old = state["branches"][actor]
            torques = np.asarray([r["motor_torque_physics_nm"] for r in rows])
            # The original walking contract uses 98%, not the diagnostic's 99%.
            # Apply that stricter inherited gate without rewriting the old score.
            saturation = float((np.abs(torques) >= .98 * .6405236195572268).mean())
            additional = []
            if saturation > .02:
                additional.append("original_contract_torque_saturation")
            if np.max(np.abs(torques)) > .6405236195572268 + 1e-6:
                additional.append("original_contract_torque_limit")
            branches[name] = {**old, "original_diagnostic_passed": old["passed"],
                "passed": old["passed"] and not additional, "additional_failures": additional,
                "torque_saturation_at_original_98_percent": saturation}
            if state["source"] == actor:
                originals = reference[actor, state["session"]][state["before_step"]:]
                compared = 0; maximum = 0.
                for row, original in zip(rows, originals):
                    if original["actor_mode"] != "standing":
                        break
                    error = float(np.max(np.abs(np.asarray(row["qpos"]) - original["qpos"])))
                    maximum = max(maximum, error)
                    np.testing.assert_allclose(row["qpos"], original["qpos"], rtol=0, atol=1e-10)
                    np.testing.assert_array_equal(np.asarray(row["action_rad"], np.float32), np.asarray(original["action_rad"], np.float32))
                    np.testing.assert_array_equal(np.asarray(row["actor_observation"], np.float32), np.asarray(original["actor_observation"], np.float32))
                    if row["fell"] != original["fell"]:
                        raise ValueError("branch terminal mismatch")
                    compared += 1
                if not compared:
                    raise ValueError("empty original branch comparison")
                reproduction.append({"state":state["id"], "matched_controls":compared, "max_qpos_error":maximum})
    summary = defaultdict(lambda: {"passed":0,"total":0,"falls":0,"survived_3s_failed_5s":0})
    for state in report["states"]:
        for actor, original in state["branches"].items():
            b = branches[original["case_id"]]
            key = state["source"] + "/" + state["kind"] + "/actor-" + actor
            summary[key]["total"] += 1
            summary[key]["passed"] += int(b["passed"])
            summary[key]["falls"] += int("fall" in b["failures"])
            summary[key]["survived_3s_failed_5s"] += int(b["alive_at_3s"] and b["duration_s"] < 5.)
    result = {"schema":"microduck.handoff-coverage-analysis/v43", "complete":True,
        "source_receipt_manifest_sha256":digest(args.receipt / "SHA256SUMS"),
        "source_branch_reproduction":reproduction, "history_distances":histories,
        "branches":branches, "summary":dict(summary),
        "boundary":"Reset-bank and full-state paired diagnostics; original PPO trajectory coverage is unavailable. Stricter original torque gate is additive; original scores remain retained. No behavior promotion."}
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "analysis.json").write_text(json.dumps(result, indent=2) + "\n")
    (args.output / "source.py").write_text(Path(__file__).read_text())
    seal(args.output)
    print(json.dumps({"summary":dict(summary),"exact_source_branches":len(reproduction)}), flush=True)


if __name__ == "__main__":
    main()
