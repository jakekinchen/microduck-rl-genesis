"""Read and retain the completed V31–V42 sequence; never simulate or promote."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PROBES = ["v31-matched-contact", "v32-contact-patch", "v34-exact-hull",
          "v35-exact-patch", "v36-unpruned-patch", "v37-compatible-patch",
          "v39-euler-hull", "v40-legacy-collider"]
EVALUATIONS = ["v38-stopping-endurance", "v41-native-standing-endurance",
               "v42-native-standing-endurance", "v42-native-standing-flat",
               "v42-native-standing-repeated", "v42-native-standing-surfaces"]


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_text())


def check(condition, message):
    if not condition:
        raise ValueError(message)


def verify_manifest(directory):
    entries = {}
    for line in (directory / "SHA256SUMS").read_text().splitlines():
        expected, name = line.split("  ", 1)
        path = (directory / name).resolve()
        check(path.is_relative_to(directory.resolve()) and name not in entries,
              "unsafe or duplicate manifest entry")
        check(sha(path) == expected, f"manifest mismatch: {path}")
        entries[name] = expected
    check(bool(entries), "empty manifest")
    return {"files": len(entries), "manifest_sha256": sha(directory / "SHA256SUMS")}


def physics(path):
    import numpy as np
    with gzip.open(path, "rt") as stream:
        rows = [json.loads(line) for line in stream]
    return {key: np.asarray([row[key] for row in rows]) for key in ("qpos", "target")}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    check(not args.output.exists(), "new output directory required")
    import numpy as np
    import torch
    from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
    from duck_workspace.core import Inspector
    torch.set_num_threads(1)

    result = {"schema": "microduck.sequence-verification/v42", "freezes": {},
              "receipts": {}, "probes": {}, "training": {}, "evaluations": {},
              "physical_calibration": False, "fresh_terrain_opened": False,
              "promotion": "rejected; retain V30", "verification_completed": False}
    source_cache = {}
    freezes = []
    for path in sorted((ROOT / "experiments/walking").glob("*freeze-v*.json")):
        version = path.stem.rsplit("-v", 1)[-1]
        if version.isdigit() and 31 <= int(version) <= 42:
            freeze = read(path)
            for name, expected in freeze["source_sha256"].items():
                if name not in source_cache:
                    source_cache[name] = sha(ROOT / name)
                check(source_cache[name] == expected, f"source drift: {name}")
            result["freezes"][path.name] = {"sha256": sha(path), "sources": len(freeze["source_sha256"])}
            freezes.append(path)
    check(len(freezes) == 19, "incomplete sequence freeze inventory")
    for name in PROBES + ["v33-geometry-audit"] + EVALUATIONS:
        directory = ROOT / "receipts/walking" / ("20260906-" + name)
        result["receipts"][name] = verify_manifest(directory)
        if name not in PROBES:
            continue
        report = read(directory / "probe.json")
        check(report["status"] == "completed", "incomplete contact probe")
        check(len(report["cases"]) == 5, "missing contact probe case")
        for index, case in enumerate(report["cases"]):
            actions = np.load(directory / f"case-{index}-actions-float32.npy", allow_pickle=False)
            check(actions.dtype == np.float32 and actions.shape == (case["steps"], 14), "action contract")
            check(hashlib.sha256(actions.tobytes()).hexdigest() == case["action_bytes_sha256"], "action hash")
            check(case["action_bytes_identical"] and case["native_plane_reproduced"], "failed control reproduction")
            lanes = [physics(directory / f"native-{index}-{kind}/physics.jsonl.gz") for kind in ("plane", "boxes")]
            lanes.append(physics(directory / f"genesis-{index}-physics.jsonl.gz"))
            check(all(len(lane["qpos"]) == case["physics_steps"] for lane in lanes), "physics telemetry missing")
            np.testing.assert_array_equal(lanes[0]["target"], lanes[1]["target"])
            np.testing.assert_allclose(lanes[0]["target"], lanes[2]["target"], rtol=0, atol=2e-7)
        result["probes"][name] = {
            "passed_cases": sum(c["comparisons"]["boxes_genesis"]["passed"] for c in report["cases"]),
            "total_cases": 5, "controls": sum(c["steps"] for c in report["cases"]),
            "physics_steps_per_lane": sum(c["physics_steps"] for c in report["cases"]),
            "comparisons": [c["comparisons"]["boxes_genesis"] for c in report["cases"]]}
    for left, right in [("v35-exact-patch", "v36-unpruned-patch"), ("v34-exact-hull", "v40-legacy-collider")]:
        for index in range(5):
            paths = [ROOT / "receipts/walking" / ("20260906-" + v) / f"genesis-{index}-physics.jsonl.gz" for v in (left, right)]
            np.testing.assert_array_equal(physics(paths[0])["qpos"], physics(paths[1])["qpos"])

    run_paths = []
    for version in (41, 42):
        for smoke in (True, False):
            name = f"standing-native-20260906-v{version}" + ("-smoke" if smoke else "")
            directory = ROOT / "logs" / name
            run = read(directory / "run.json")
            expected_steps = 960 if smoke else 384000
            check(run["status"] == "completed" and run["new_transitions"] == expected_steps, "incomplete training")
            check(run["checkpoint"] == ("model_4.pt" if smoke else "model_249.pt"), "wrong candidate")
            check(sha(directory / run["checkpoint"]) == run["checkpoint_sha256"], "checkpoint identity")
            for path, expected in run["source_sha256"].items():
                check(sha(directory / "source" / path) == expected == source_cache[path], "captured training source drift")
            actor = torch.load(directory / run["checkpoint"], map_location="cpu", weights_only=True)["actor_state_dict"]
            check(all(torch.isfinite(value).all() for value in actor.values()), "nonfinite actor")
            events = EventAccumulator(str(directory), size_guidance={"scalars": 0})
            events.Reload()
            scalar_count = 0
            for tag in events.Tags()["scalars"]:
                values = events.Scalars(tag)
                check(all(math.isfinite(event.value) for event in values), "nonfinite training scalar")
                scalar_count += len(values)
            check(scalar_count > 0, "missing learning telemetry")
            coverage = run["final_coverage"]
            visited = coverage["reset_counts_home_handoff"]
            # The 120-step smoke is shorter than a 150-step episode; its final
            # assignment need not visit both initial-state types. Full training must.
            check(all(sum(pair) > 0 for pair in visited), "unvisited template")
            if not smoke:
                check(all(all(count > 0 for count in pair) for pair in visited), "unvisited reset bucket")
            check(len(coverage["templates"]) == 8 and all(t["exact_reset_continuation"] for t in coverage["templates"]), "reset continuation missing")
            check(coverage["control_steps"] * run["args"]["num_envs"] == expected_steps, "transition accounting")
            result["training"][name] = {"checkpoint_sha256": run["checkpoint_sha256"],
                "transitions": expected_steps, "elapsed_s": run["elapsed_s"], "finite_scalar_samples": scalar_count,
                "coverage": coverage}
            run_paths.append((directory, run))
    template_sets = [read(directory / "templates.json") for directory, _ in run_paths]
    check(all(templates == template_sets[0] for templates in template_sets), "V41/V42 template mismatch")

    for name in EVALUATIONS:
        directory = ROOT / "receipts/walking" / ("20260906-" + name)
        if (directory / "probe.json").exists():
            report = read(directory / "probe.json")
            check(report["complete"] and report["exception"] is None, "evaluation incomplete")
            check(sum(c["passed"] for c in report["case_reports"]) == report["passed_windows"], "window denominator")
            check(sum(c["passed"] for c in report["session_reports"]) == report["passed_sessions"], "session denominator")
            result["evaluations"][name] = {key: report[key] for key in ("passed_sessions", "total_sessions", "passed_windows", "total_windows")}
        else:
            detail = Inspector(ROOT).detail(str(directory.relative_to(ROOT)))
            check(detail["heading_evidence"]["status"] == "verified", "composite identity failure")
            result["evaluations"][name] = {"passed_cases": detail["passed"], "total_cases": detail["total"],
                "trace_cases": len(detail["trajectories"]), "component_gates": {
                    k: v for k, v in detail["heading_evidence"].items() if k.endswith("passed_cases")}}

    args.output.mkdir(parents=True)
    for path in freezes:
        dest = args.output / "freezes" / path.name
        dest.parent.mkdir(exist_ok=True)
        shutil.copy2(path, dest)
    for directory, run in run_paths:
        dest = args.output / "training" / directory.name
        dest.mkdir(parents=True)
        # Retain source, final and full-state templates. Intermediate policies stay in logs.
        for path in directory.iterdir():
            if path.name == "git" or (path.suffix == ".pt" and path.name != run["checkpoint"]):
                continue
            if path.is_dir():
                shutil.copytree(path, dest / path.name)
            else:
                shutil.copy2(path, dest / path.name)
    shutil.copy2(__file__, args.output / "verifier.py")
    result["verification_completed"] = True
    (args.output / "verification.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"verification_completed": True, "freezes": len(freezes), "receipts": len(result["receipts"]),
                      "training_transitions": sum(r["transitions"] for r in result["training"].values()),
                      "evaluations": result["evaluations"], "promotion": result["promotion"]}), flush=True)


if __name__ == "__main__":
    main()
