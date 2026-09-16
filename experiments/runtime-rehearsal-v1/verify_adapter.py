"""Recorded-state verification of the command adapter; never steps physics."""
import gzip
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from command_adapter import RetainedCommandAdapter


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    base = ROOT / "receipts/laser-course/20260913-v2-development-r2"
    source_paths = ["experiments/walking/command_ramp.py", "microduck/constants.py",
                    "microduck/heading_headroom_v30.py", "microduck/motion_heading_servo_v28.py",
                    "microduck/persistent_heading_servo_v24.py", "microduck/filtered_heading_servo.py",
                    "microduck/heading_servo.py"]
    source_hashes = {name: sha(ROOT / name) for name in source_paths}
    cases = []
    for path in sorted(base.glob("*/trajectory.jsonl.gz")):
        entries = dict(line.split(maxsplit=1)[::-1] for line in (path.parent / "SHA256SUMS").read_text().splitlines())
        assert sha(path) == entries[path.name]
        with gzip.open(path, "rt") as stream:
            rows = [json.loads(line) for line in stream]
        freeze = json.loads((path.parent / "freeze.json").read_text())
        assert sha(path.parent / "freeze.json") == entries["freeze.json"]
        assert all(freeze["source_sha256"][name] == digest for name, digest in source_hashes.items())
        yaw = freeze["case"]["yaw"]
        q = np.array([np.cos(yaw/2), 0., 0., np.sin(yaw/2)], dtype=np.float64)
        adapter = RetainedCommandAdapter(sensor_ticks=1)
        exact = {"routing_command": 0, "policy_command": 0, "actor_mode": 0, "motor_reference": 0}
        max_command_error = 0.
        legacy_threshold_disagreements = 0
        for row in rows:
            result = adapter.step(row["command"], q)
            for field in ("routing_command", "policy_command"):
                wanted = np.asarray(row[field], np.float32)
                exact[field] += int(result[field].tobytes() == wanted.tobytes())
                max_command_error = max(max_command_error, float(np.max(np.abs(result[field] - wanted))))
            exact["actor_mode"] += int(result["actor_mode"] == row["actor_mode"])
            action = np.asarray(row["action_rad"], np.float32)
            original = action.tobytes()
            target = adapter.motor_reference(action)
            assert action.tobytes() == original
            exact["motor_reference"] += int(np.array_equal(target, np.asarray(row["servo_target_rad"])))
            legacy_mode = "standing" if np.linalg.norm(result["routing_command"].astype(float)) <= .05 else "walking"
            legacy_threshold_disagreements += int(legacy_mode != row["actor_mode"])
            q = np.asarray(row["qpos"][3:7], dtype=np.float64)
        cases.append({"case": path.parent.name, "rows": len(rows), "exact_rows": exact,
                      "max_command_error": max_command_error,
                      "upstream_threshold_disagreements": legacy_threshold_disagreements,
                      "source_sha256": sha(path), "passed": all(v == len(rows) for v in exact.values())})
    # A malformed action cannot be silently narrowed or filtered by the bridge.
    rejected = 0
    for action in (np.zeros(14, np.float64), np.zeros(15, np.float32), np.full(14, np.nan, np.float32)):
        try:
            RetainedCommandAdapter.motor_reference(action)
        except ValueError:
            rejected += 1
    result = {"schema": "microduck.runtime-command-adapter-verification.v1",
              "scope": "recorded-state command and raw-target reconstruction; no physics",
              "cases": cases, "invalid_action_inputs_rejected": rejected,
              "source_sha256": source_hashes,
              "adapter_sha256": sha(Path(__file__).with_name("command_adapter.py")),
              "verification_script_sha256": sha(__file__),
              "passed": len(cases) == 6 and all(c["passed"] for c in cases) and rejected == 3,
              "body_transport_implemented": False, "robotd_startup_modified": False,
              "physical_authority": False}
    output = ROOT / ".workspace/runtime-rehearsal-v1/adapter-verification.json"
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
