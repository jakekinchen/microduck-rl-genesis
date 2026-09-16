"""Verify actual produced float32 bytes, not only numerical array equality."""
import argparse
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.probe_handoff_coverage_v43_r3 import INPUTS, make_world, seal
from scripts.verify_walking_sequence_v42 import verify_manifest
from scripts.evaluate_laser import digest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("new verification output required")
    import numpy as np
    import torch
    torch.set_num_threads(1)
    result = {"sessions": [], "source_branches": [], "complete": False}
    references = {}
    for source, relative in INPUTS.items():
        directory = ROOT / relative
        verify_manifest(directory)
        suite = json.loads((directory / "suite.json").read_text())
        sessions = {s["id"]: s for s in suite["sessions"] if s["bank"] == "diagnostic"}
        path = directory / "trajectory.jsonl"
        if not path.exists():
            path = directory / "trajectory.jsonl.gz"
        opener = gzip.open if path.suffix == ".gz" else open
        with opener(path, "rt") as stream:
            for session, group in itertools.groupby((json.loads(line) for line in stream), lambda r:r["session_id"]):
                world = make_world(directory / "terrain-models" / session / "scene.xml",
                                   directory / "standing/policy.onnx", sessions[session])
                produced, recorded = hashlib.sha256(), hashlib.sha256()
                expected_rows = []
                try:
                    for saved in group:
                        row = world.step_command(saved["command"])
                        action = np.asarray(saved["action_rad"], np.float32).tobytes()
                        obs = np.asarray(saved["actor_observation"], np.float32).tobytes()
                        if world.last_action.tobytes() != action or world.last_observation[0].tobytes() != obs:
                            raise ValueError("actual action/observation byte mismatch")
                        np.testing.assert_array_equal(world.core.data.qpos, np.asarray(saved["qpos"]))
                        if row["fell"] != saved["fell"]:
                            raise ValueError("terminal mismatch")
                        produced.update(world.last_action.tobytes()); recorded.update(action)
                        expected_rows.append({"action":action, "observation":obs, "actor_mode":saved["actor_mode"]})
                    item = {"source":source, "session":session, "controls":len(expected_rows),
                            "produced_action_sha256":produced.hexdigest(), "recorded_action_sha256":recorded.hexdigest(),
                            "actual_observation_bytes_identical":True, "qpos_exactly_equal":True}
                    result["sessions"].append(item)
                    references[source, session] = expected_rows
                    print(json.dumps(item), flush=True)
                finally:
                    world.close()
    directory = ROOT / "receipts/walking/20260907-v43-handoff-coverage-r3"
    verify_manifest(directory)
    report = json.loads((directory / "probe.json").read_text())
    branches = {b["case_id"]:(s, actor) for s in report["states"] for actor,b in s["branches"].items()}
    with gzip.open(directory / "branches.jsonl.gz", "rt") as stream:
        for name, group in itertools.groupby((json.loads(line) for line in stream), lambda r:r["case_id"]):
            state, actor = branches[name]
            if state["source"] != actor:
                continue
            count = 0
            for row, expected in zip(group, references[actor,state["session"]][state["before_step"]:]):
                if expected["actor_mode"] != "standing":
                    break
                if (np.asarray(row["action_rad"],np.float32).tobytes() != expected["action"]
                        or np.asarray(row["actor_observation"],np.float32).tobytes() != expected["observation"]):
                    raise ValueError("source-branch action/observation byte mismatch")
                count += 1
            if not count:
                raise ValueError("empty source branch")
            result["source_branches"].append({"state":state["id"],"matched_controls":count})
    result.update(complete=True, script_sha256=digest(Path(__file__)),
                  boundary="Full closed-loop reproduction with checked byte identity; no action overrides, new policy or acceptance claim.")
    args.output.mkdir(parents=True)
    (args.output / "verification.json").write_text(json.dumps(result,indent=2)+'\n')
    (args.output / "source.py").write_text(Path(__file__).read_text())
    seal(args.output)


if __name__ == "__main__":
    main()
