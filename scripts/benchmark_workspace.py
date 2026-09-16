#!/usr/bin/env python3
"""Compare read-only receipt inspection against a saved core.py baseline.

Cold means a fresh Inspector hash cache, not an empty operating-system cache.
Only retained evaluation/detail/artifact data is compared; live training curves
and snapshot timestamps are deliberately outside this benchmark.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def load_core(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str,
                                     separators=(",", ":")).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--baseline-core", type=Path, help="core.py saved before the change")
    parser.add_argument("--run-id", help="development run with a retained video and trajectory")
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats must be positive")
    root = args.root.resolve()
    paths = {"candidate": ROOT / "duck_workspace/core.py"}
    if args.baseline_core:
        paths = {"baseline": args.baseline_core.resolve(), **paths}
    modules = {name: load_core(path, f"workspace_benchmark_{name}") for name, path in paths.items()}
    runs, errors = next(iter(modules.values())).Inspector(root).evaluations()
    expected_results = {"evaluations": fingerprint((runs, errors))}
    selected = next((run for run in runs
                     if (run["id"] == args.run_id if args.run_id else
                         "trajectory.jsonl" in run["artifacts"] and
                         any(name.endswith(".mp4") for name in run["artifacts"]))), None)
    if selected is None:
        parser.error("no matching development run with retained artifacts")
    video = next((name for name in selected["artifacts"] if name.endswith(".mp4")), None)
    if video is None:
        parser.error("selected run has no retained video")
    artifact = selected["id"] + "/" + video
    operations = {"evaluations": lambda inspector: inspector.evaluations(),
                  "detail": lambda inspector: inspector.detail(selected["id"]),
                  "artifact": lambda inspector: inspector.artifact(artifact)}
    warm = {name: module.Inspector(root) for name, module in modules.items()}
    for inspector in warm.values():
        if fingerprint(inspector.evaluations()) != expected_results["evaluations"]:
            raise RuntimeError("warmup: retained inventory changed or implementations disagree")
    measurements = {}
    measured_inventory = {}
    for operation, request in operations.items():
        for cache in ("cold", "warm"):
            key = f"{operation}_{cache}"
            values = {name: [] for name in modules}
            for trial in range(args.repeats):
                # Alternate order to reduce systematic effects of machine load.
                order = list(modules) if trial % 2 == 0 else list(reversed(modules))
                for name in order:
                    inspector = modules[name].Inspector(root) if cache == "cold" else warm[name]
                    start = time.perf_counter()
                    result = request(inspector)
                    values[name].append(time.perf_counter() - start)
                    digest = fingerprint(result)
                    expected = expected_results.get(operation)
                    if expected is not None and digest != expected:
                        raise RuntimeError(f"{key}: retained result changed or implementations disagree")
                    expected_results[operation] = digest
                    if operation == "evaluations":
                        measured_inventory = {"evaluation_count": len(result[0]),
                                              "evaluation_error_count": len(result[1])}
            measurements[key] = {
                "result_sha256": expected_results[operation],
                **{name: {"seconds": samples, "median_seconds": statistics.median(samples)}
                   for name, samples in values.items()}}
            if "baseline" in values:
                measurements[key]["speedup"] = statistics.median(values["baseline"]) / statistics.median(values["candidate"])
    # Individual routes need not read unrelated runs, so check the full inventory
    # again after timing them. Never publish results against a changed inventory.
    for inspector in warm.values():
        if fingerprint(inspector.evaluations()) != expected_results["evaluations"]:
            raise RuntimeError("final check: retained inventory changed or implementations disagree")
    report = {"schema": "microduck.workspace-benchmark/v1", "root": str(root),
              "python": sys.version, "platform": platform.platform(), "repeats": args.repeats,
              "core_sha256": {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in paths.items()},
              "run_id": selected["id"], "artifact": artifact,
              **measured_inventory, "inventory_sha256": expected_results["evaluations"],
              "boundary": "Receipt reader performance only. Cold is a fresh Inspector hash cache; OS caches are not cleared.",
              "result_equality_verified": True, "measurements": measurements}
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered)
    print(rendered, end="")


if __name__ == "__main__":
    main()
