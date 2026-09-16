"""Read-only status/preflight and explicit offline analyses. No launch command."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def program(path):
    data = json.loads(Path(path).read_text())
    if data.get("schema") != "microduck.review-program/v1":
        raise ValueError("unsupported review program")
    streams = data["workstreams"]
    if not streams or len({s["id"] for s in streams}) != len(streams):
        raise ValueError("unique nonempty workstreams required")
    for stream in streams:
        if stream["scope"] not in ("exploratory_capability", "model_validation", "runtime_component", "tooling"):
            raise ValueError("unknown proof scope")
        if type(stream["max_attempts"]) is not int or stream["max_attempts"] < 1:
            raise ValueError("finite positive attempt bound required")
        if not stream["stop_rule"] or not stream["validation_status"]:
            raise ValueError("decision and validation status required")
    if data["automatic_promotion"] is not False:
        raise ValueError("review program cannot promote policies")
    return data


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    status = sub.add_parser("status")
    status.add_argument("--program", type=Path, default=ROOT/"experiments/retool-v1/program.json")
    sub.add_parser("doctor")
    replay = sub.add_parser("label-replay")
    replay.add_argument("--input", required=True, type=Path)
    replay.add_argument("--output", required=True, type=Path)
    comparison = sub.add_parser("compare")
    comparison.add_argument("--input", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "status":
            result = program(args.program)
        elif args.command == "doctor":
            packages = {name: importlib.util.find_spec(name) is not None
                        for name in ("numpy", "torch", "mujoco", "tensordict", "rsl_rl")}
            paths = {name: (ROOT/name).exists() for name in (
                ".workspace/bam/bam/mujoco.py", "receipts/walking/20260906-v30-flat-regression/policy.onnx",
                "experiments/walking/models/contact-v11/scene.xml")}
            ready = all(packages.values()) and all(paths.values())
            result = dict(packages=packages, required_paths=paths, native_inputs_present=ready,
                          runtime_validated=False, compute_started=False)
            print(json.dumps(result, indent=2)); return 0 if ready else 1
        elif args.command == "label-replay":
            import hashlib
            import numpy as np
            from .learning import transition_labels
            with np.load(args.input, allow_pickle=False) as archive:
                required = ("observations", "actions", "env_ids", "episode_ids", "control_steps")
                if not set(required).issubset(archive.files):
                    raise ValueError("replay requires observations/actions and explicit episode metadata")
                arrays = {name: archive[name] for name in required}
                obs, act = arrays["observations"], arrays["actions"]
                if act.shape != (len(obs), 14) or act.dtype != np.float32 or not np.isfinite(act).all():
                    raise ValueError("row-aligned finite float32 actions required")
                labels = transition_labels(obs, arrays["env_ids"], arrays["episode_ids"], arrays["control_steps"])
            # Exclusive creation: input and all retained evidence are never overwritten.
            with args.output.open("xb") as stream:
                np.savez_compressed(stream, **arrays, phases=labels,
                                    source_sha256=hashlib.sha256(args.input.read_bytes()).hexdigest())
            counts = dict(zip(*np.unique(labels, return_counts=True)))
            result = dict(rows=len(labels), phases={k: int(v) for k, v in counts.items()},
                          output=str(args.output), behavior_pass=False)
        else:
            from .metrics import paired_summary
            data = json.loads(args.input.read_text())
            result = paired_summary(data["runs"], data["seeds"], tuple(data["arms"]))
        print(json.dumps(result, indent=2, allow_nan=False))
        return 0
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(json.dumps({"error": str(exc), "behavior_pass": False}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
