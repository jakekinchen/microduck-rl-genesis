"""Compare every semantic dynamic rollout row, excluding measured wall latency."""
import argparse
import hashlib
import json
from pathlib import Path


def canonical(path):
    h = hashlib.sha256()
    count = 0
    with path.open() as stream:
        for line in stream:
            row = json.loads(line)
            row.pop("latency_ms")
            h.update(json.dumps(row, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()+b"\n")
            count += 1
    return count, h.hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("first", type=Path)
    p.add_argument("second", type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    a, b = canonical(args.first/"trajectory.jsonl"), canonical(args.second/"trajectory.jsonl")
    ra = json.loads((args.first/"evaluation.json").read_text())
    rb = json.loads((args.second/"evaluation.json").read_text())
    equal = a == b and ra["policy_sha256"] == rb["policy_sha256"] and ra["suite_sha256"] == rb["suite_sha256"]
    with args.output.open("x") as stream:
        json.dump({"equal": equal, "rows": a[0], "semantic_sha256": a[1],
                   "repeat_rows": b[0], "repeat_sha256": b[1], "excluded": ["latency_ms"],
                   "policy_sha256": ra["policy_sha256"]}, stream, indent=2)
        stream.write("\n")
    print(f"{a[0]} rows; semantic replay equal: {equal}")
    if not equal:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
