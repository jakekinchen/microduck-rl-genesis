"""Apply the workspace lessons to one existing, visible development experiment."""
from pathlib import Path

from duck_workspace.core import ROOT, Inspector, read_json, safe_path, sha256

CONFIG = "docs/workspace/active-experiment.json"


def focus(root: Path, runs: list[dict]) -> dict:
    try:
        path = safe_path(root, CONFIG)
        if not path.exists():
            return {"status": "not_configured"}
        data = read_json(path)
        if not isinstance(data, dict) or data.get("schema") != "microduck.active-workspace/v1":
            raise ValueError("unsupported active-workspace schema")
        selected = {}
        for key in ("primary", "comparison"):
            if key == "comparison" and data.get(key) is None:
                continue  # a single retained baseline is not a fake comparison
            run = next((run for run in runs if run["id"] == data.get(key)), None)
            if run is None or run["integrity"]["status"] != "manifest_verified":
                raise ValueError(f"{key} is missing or its development manifest is not verified")
            if run["policy_sha256"] != data.get(key + "_policy_sha256") or run["suite_sha256"] != data.get("suite_sha256"):
                raise ValueError(f"{key} policy/suite identity differs from the working focus")
            if data.get("case_id") not in [case["case_id"] for case in run["cases"]]:
                raise ValueError(f"{key} lacks the focused case")
            selected[key] = run["id"]
        return {"status": "verified", **selected, "case_id": data["case_id"],
                "id": data["id"], "question": data["question"], "phase": data["phase"],
                "config_sha256": sha256(path), "boundary": data["boundary"]}
    except (OSError, ValueError, KeyError, TypeError) as error:
        return {"status": "unavailable", "error": str(error)}


def prepare(root: Path = ROOT) -> dict:
    from experiment_ops.activity import inspect
    from experiment_ops.compare import load_trace

    root = root.resolve()
    inspector = Inspector(root)
    runs, discovery_errors = inspector.evaluations()
    active = focus(root, runs)
    result = {"schema": "microduck.active-preflight/v1", "read_only": True,
              "focus": active, "ready_for_diagnosis": False, "execution_authorized_by_report": False,
              "training_started": False, "physics_causality": "not_established",
              "activity": inspect(root), "discovery_errors": discovery_errors, "errors": []}
    result["active_training_records"] = []
    result["active_training_record_errors"] = []
    for path in sorted((root / "logs").glob("*/run.json")):
        relative = str(path.relative_to(root))
        try:
            safe_path(root, relative)
            record = read_json(path)
            if not isinstance(record, dict):
                raise ValueError("training record must be an object")
        except (OSError, ValueError) as error:
            # External archives remain outside the viewer's serving boundary.
            # Report incomplete inspection instead of crashing or hiding it.
            result["active_training_record_errors"].append({"path": relative, "error": str(error)})
            result["errors"].append(f"training record unavailable: {relative}: {error}")
            continue
        if record.get("status") not in {"starting", "running"}:
            continue
        checks = []
        for relative, expected in record.get("source_sha256", {}).items():
            try:
                checks.append({"path": relative, "matches": sha256(safe_path(root, relative)) == expected})
            except (OSError, ValueError):
                checks.append({"path": relative, "matches": False})
        result["active_training_records"].append({"id": path.parent.name, "variant": record.get("variant"),
            "recorded_status": record["status"], "source_commit": record.get("source_commit"),
            "planned_transitions": record.get("planned_new_transitions", record.get("new_transitions")), "source_checks": checks,
            "current_sources_match_record": bool(checks) and all(check["matches"] for check in checks),
            "exact_process_to_run_binding": "not_checked"})
    if active["status"] != "verified":
        result["errors"].append(active.get("error", "no active experiment configured"))
        return result
    data = read_json(safe_path(root, CONFIG))
    if sha256(safe_path(root, CONFIG)) != active["config_sha256"]:
        raise ValueError("active experiment changed during preparation; refresh the working focus")
    result["before_training"] = data["before_training"]
    cases = {}
    primary_manifest = None
    for key in ("primary", "comparison"):
        if key not in active:
            continue
        run = next(run for run in runs if run["id"] == active[key])
        case = next(case for case in run["cases"] if case["case_id"] == active["case_id"])
        directory = safe_path(root, run["id"])
        # A containing manifest must cover the trace; arbitrary siblings are not evidence.
        from duck_workspace.core import manifest_entries
        manifest_root = directory
        while not (manifest_root / "SHA256SUMS").exists() and manifest_root != root:
            manifest_root = manifest_root.parent
        entries = manifest_entries(root, manifest_root)
        policy_path = safe_path(root, str((directory / "policy.onnx").relative_to(root)))
        policy_name = str(policy_path.relative_to(manifest_root))
        if entries.get(policy_name) != run["policy_sha256"] or sha256(policy_path) != run["policy_sha256"]:
            raise ValueError("focused policy bytes are not bound by report and manifest")
        if key == "primary":
            primary_manifest = (manifest_root, entries)
        trace_file = "trajectory.jsonl" if (directory / "trajectory.jsonl").exists() else "trajectory.jsonl.gz"
        trace_path = safe_path(root, str((directory / trace_file).relative_to(root)))
        trace_name = str(trace_path.relative_to(manifest_root))
        walking = run["schema"] == "microduck.walking-evaluation/v1"
        traces, identity = load_trace(trace_path,
                                     max_bytes=(512 if walking else 16) * 1024 * 1024,
                                     max_rows=50000 if walking else 20000)
        if entries.get(trace_name) != identity["sha256"]:
            raise ValueError("focused trajectory is not bound by the verified manifest")
        rows = traces.get(active["case_id"], [])
        if not rows:
            raise ValueError("focused trajectory has no case rows")
        fall = next((row for row in rows if row.get("fell") is True), None)
        cases[key] = {"receipt": run["id"], "policy_sha256": run["policy_sha256"],
                      "case": case, "trajectory": identity,
                      "first_fall": {field: fall.get(field) for field in
                                     ("time_s", "_line", "robot_xyz_m", "tilt_deg", "command", "action_rad")} if fall else None}
    result["cases"] = cases
    domain = cases["primary"]["case"].get("domain", {})
    if "comparison" in cases and domain != cases["comparison"]["case"].get("domain"):
        result["errors"].append("comparison case has a different domain draw")
    bindings = []
    for relative in data["source_paths"]:
        current = safe_path(root, relative)
        source_folder = data.get("source_folder", "source")
        if source_folder not in {"source", "evaluator-source"}:
            raise ValueError("unsupported retained source folder")
        retained = safe_path(root, active["primary"] + "/" + source_folder + "/" + relative)
        current_sha, retained_sha = sha256(current), sha256(retained)
        manifest_root, entries = primary_manifest
        if entries.get(str(retained.relative_to(manifest_root))) != retained_sha:
            raise ValueError(f"retained source is not bound by the manifest: {relative}")
        bindings.append({"path": relative, "current_sha256": current_sha,
                         "retained_sha256": retained_sha, "matches": current_sha == retained_sha})
        if current_sha != retained_sha:
            result["errors"].append(f"current implementation differs from retained case: {relative}")
    result["source_bindings"] = bindings
    fall = cases["primary"]["first_fall"]
    result["observations"] = []
    if fall and isinstance(domain.get("push_at_s"), (int, float)) and fall["time_s"] < domain["push_at_s"]:
        result["observations"].append(f"Fall at {fall['time_s']} s precedes the scheduled push at {domain['push_at_s']} s; that scheduled push cannot explain this recorded startup fall.")
    if domain.get("sensor_delay_steps") == 0:
        result["observations"].append("This case has zero sensor-delay steps; added delay is not active in its recorded domain.")
    result["observations"].append("Feedback rollout comparison cannot isolate a physics cause." if "comparison" in cases
                                  else "Retained baseline only; no candidate comparison or improvement is asserted.")
    result["ready_for_diagnosis"] = not result["errors"]
    if sha256(safe_path(root, CONFIG)) != active["config_sha256"]:
        raise ValueError("active experiment changed during preparation; refresh the working focus")
    return result
