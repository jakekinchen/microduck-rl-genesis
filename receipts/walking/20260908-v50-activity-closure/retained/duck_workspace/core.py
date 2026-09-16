"""Read existing development evidence without changing its classification."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import quote
from .quality_plan import check_quality_plan, new_quality_plan

ROOT = Path(__file__).resolve().parents[1]
DEVELOPMENT_ROOTS = ("receipts/laser-follow", "receipts/first-party-development", "receipts/laser-dynamic", "receipts/laser-gait", "receipts/walking")
GAIT_SCHEMAS = {"microduck.laser-gait-evaluation/v3", "microduck.laser-gait-evaluation/v4"}
WALKING_SCHEMA = "microduck.walking-evaluation/v1"
PAIRED_WALKING_VARIANTS = {
    "command-stand-switch-v14", "command-stand-switch-v15", "unbraced-walking-ramped-v18",
    "yaw-refinement-filtered-heading-v21", "heading-persistence-v24-flat-regression",
    "motion-heading-v28-flat-regression", "heading-headroom-v29-flat-regression",
    "heading-headroom-v30-flat-regression",
    "stopping-ramp-v38-flat-regression", "native-standing-v41-flat-regression",
    "native-standing-v42-flat-regression", "native-sequence-v44-flat-regression", "component-isolation-v45-flat", "native-retention-v46-flat-regression",
    "native-standing-retention-v48-flat-regression", "native-retention-v50-flat-regression",
}
SELF_LOAD_WALKING_VARIANTS = PAIRED_WALKING_VARIANTS | {"self-load-v14-v13-baseline"}
COMPLETE_WALKING_VARIANTS = {"complete-contact-heading-self-v11", "imu-heading-command-servo-v12", "imu-heading-command-servo-v13-actor"} | SELF_LOAD_WALKING_VARIANTS
LASER_SCHEMAS = {"microduck.laser-evaluation/v1", "microduck.dynamic-laser-evaluation/v1", WALKING_SCHEMA, *GAIT_SCHEMAS}
JSON_LIMIT = 32 * 1024 * 1024
TRAJECTORY_LIMIT = 512 * 1024 * 1024  # Up to 42 repeated-start windows with 200-Hz motor/load telemetry; 50,000-row bound remains.


def case_failure_summary(case: dict) -> str:
    """Explain recorded failures without recomputing or upgrading a score."""
    if case.get("passed") is True:
        return "Passed the reported gates; not physical or full walking acceptance."
    if case.get("passed") is not False:
        return "Outcome not recorded."
    labels = {
        "posture_maximum_mean_joint_error_rad": "Head posture",
        "posture_p95_worst_joint_error_rad": "Head posture",
        "posture_mean_absolute_face_pitch_deg": "Face orientation",
        "mean_abs_yaw_error_rad_s": "Turning accuracy",
        "mean_abs_forward_error_m_s": "Forward speed accuracy",
        "mean_abs_lateral_velocity_m_s": "Sideways drift",
        "stop_max_tilt_deg": "Leaning when stopped",
        "stop_max_speed_m_s": "Not settled after stop",
        "stop_max_yaw_rate_rad_s": "Still turning after stop",
        "minimum_actual_joint_margin_rad": "Actual joint-limit margin",
        "torque_saturation_fraction": "Motor saturation",
    }
    failures = case.get("failures")
    if not isinstance(failures, list) or not failures:
        return "Failed; a reason was not recorded."
    return "; ".join(dict.fromkeys(labels.get(str(f), str(f).replace("_", " ")) for f in failures))


def safe_path(root: Path, relative: str) -> Path:
    """Reject traversal and symlinks, including symlinked parent directories."""
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts or not rel.parts:
        raise ValueError("expected a path inside this workspace")
    root = root.resolve()
    current = root
    for part in rel.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("symlinked evidence is not served")
    if not current.resolve().is_relative_to(root):
        raise ValueError("path escapes workspace")
    return current


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_json(path: Path):
    if path.stat().st_size > JSON_LIMIT:
        raise ValueError("JSON is larger than the inspection limit")
    def reject(value):
        raise ValueError(f"non-finite JSON number: {value}")
    return json.loads(path.read_text(), parse_constant=reject)


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                            text=True, timeout=15, check=False)
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def sections(text: str) -> dict[str, str]:
    result = {}
    for chunk in re.split(r"(?m)^## ", text)[1:]:
        heading, _, content = chunk.partition("\n")
        result[heading.strip()] = content.strip()
    return result


def training_counts(data: dict) -> dict:
    """Do not relabel legacy or unfinalized counters as a training budget."""
    def count(name):
        value = data.get(name)
        if value is not None and (type(value) is not int or value < 0):
            raise ValueError(f"invalid {name}")
        return value
    planned = count("planned_new_transitions")
    recorded = count("new_transitions")
    modern = planned is not None
    terminal = data.get("status") in {"completed", "interrupted", "failed"}
    return {"planned_transitions": planned,
            "finalized_completed_transitions": recorded if modern and terminal else None,
            "legacy_recorded_transitions": recorded if not modern else None,
            "partial_iteration_unknown": data.get("partial_iteration_transitions") == "unknown"}


def manifest_entries(root: Path, directory: Path) -> dict[str, str]:
    manifest = directory / "SHA256SUMS"
    if not manifest.exists():
        return {}
    safe_path(root, str(manifest.relative_to(root)))
    entries = {}
    for line in manifest.read_text().splitlines():
        match = re.fullmatch(r"([0-9a-f]{64}) [ *](.+)", line)
        if not match:
            raise ValueError("malformed SHA256SUMS")
        digest, relative = match.groups()
        path = safe_path(directory, relative)
        name = str(path.relative_to(directory))
        if name in entries:
            raise ValueError("duplicate manifest entry")
        entries[name] = digest
    if not entries:
        raise ValueError("empty SHA256SUMS")
    return entries


class Inspector:
    """Cache hashes only while a file's size and nanosecond timestamps agree."""

    def __init__(self, root: Path = ROOT):
        self.root = root.resolve()
        self._hashes = {}

    def digest(self, path: Path) -> str:
        safe_path(self.root, str(path.relative_to(self.root)))
        stat = path.stat()
        stamp = (stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
        previous = self._hashes.get(path)
        if previous and previous[0] == stamp:
            return previous[1]
        digest = sha256(path)
        self._hashes[path] = (stamp, digest)
        return digest

    def integrity(self, directory: Path) -> dict:
        try:
            manifest_root = directory
            while not (manifest_root / "SHA256SUMS").exists() and manifest_root != self.root / "receipts":
                manifest_root = manifest_root.parent
                if manifest_root == self.root:
                    break
            entries = manifest_entries(self.root, manifest_root)
            if not entries:
                return {"status": "unmanifested", "files": 0}
            report_name = str((directory / "evaluation.json").relative_to(manifest_root))
            if report_name not in entries:
                return {"status": "unmanifested", "files": len(entries), "error": "evaluation.json is not covered by the manifest"}
            # manifest_entries validates names; digest rechecks workspace paths
            # and symlinks before consulting its timestamp-bound hash cache.
            bad = [name for name, digest in entries.items()
                   if self.digest(manifest_root / name) != digest]
            return {"status": "invalid" if bad else "manifest_verified",
                    "files": len(entries), "mismatches": bad}
        except (OSError, ValueError) as error:
            return {"status": "invalid", "error": str(error)}

    def artifacts(self, directory: Path) -> dict[str, str]:
        result = {}
        for path in sorted(directory.iterdir()):
            if path.suffix not in {".json", ".jsonl", ".mp4", ".png", ".parquet"} and not path.name.endswith(".jsonl.gz"):
                continue
            try:
                path = safe_path(self.root, str(path.relative_to(self.root)))
                if path.is_file():
                    result[path.name] = "/artifact?path=" + quote(str(path.relative_to(self.root)), safe="")
            except ValueError:
                continue
        return result

    def evaluations(self, run_id: str | None = None) -> tuple[list[dict], list[dict]]:
        runs, errors = [], []
        for base in DEVELOPMENT_ROOTS:
            for path in sorted((self.root / base).glob("**/evaluation.json")):
                # Keep discovery and admission identical for individual routes,
                # but do not verify unrelated runs for every video byte range.
                if run_id is not None and str(path.parent.relative_to(self.root)) != run_id:
                    continue
                if any(word in path.parent.name.lower() for word in ("reserved", "heldout", "held-out", "acceptance")):
                    continue
                relative = str(path.relative_to(self.root))
                try:
                    safe_path(self.root, relative)
                    report = read_json(path)
                    if not isinstance(report, dict):
                        raise ValueError("evaluation report must be an object")
                    schema = report.get("schema", report.get("schema_version", ""))
                    if not schema and "state_id" in report and "anchor" in report:
                        # V49's frozen nested records inherit their explicitly
                        # exposed diagnostic envelope. They are not policy runs.
                        report = self.recovery_branch(path, report)
                        schema = report["schema"]
                    dynamic = schema == "microduck.dynamic-laser-evaluation/v1"
                    gait = schema in GAIT_SCHEMAS
                    walking = schema == WALKING_SCHEMA
                    visible = (report.get("reserved_opened") is False and report.get("physical_transfer_validated") is False and report.get("proof_class") == "visible_development") if gait or walking else (report.get("canonical_held_out") is False and report.get("split") in {"nominal", "development"}) if dynamic else report.get("held_out") is False
                    if not visible:
                        raise ValueError("only explicitly visible development reports are supported")
                    if walking and report.get("held_out") is not False:
                        raise ValueError("walking reports must explicitly exclude held-out data")
                    laser = schema in LASER_SCHEMAS
                    if not laser and schema != "microduck.first-party-evaluation/v1":
                        # Keep new formats discoverable without inventing metric semantics.
                        supported = False
                    else:
                        supported = True
                    cases = report.get("case_reports", []) if laser else []
                    if not isinstance(cases, list):
                        raise ValueError("case_reports must be a list")
                    if gait:
                        normalized = []
                        for case in cases:
                            target, movement = case["target"], case["gait"]
                            passed = case["development_passed"]
                            if type(passed) is not bool or passed != (target["passed"] is True and movement["rejection_gate_passed"] is True and case["failures"] == []):
                                raise ValueError("inconsistent composite gait/target gates")
                            normalized.append({**case, "passed": passed, "fell": target.get("fell"),
                                               "mean_visible_distance_m": target.get("mean_visible_distance_m"),
                                               "deadline_misses": target.get("deadline_misses")})
                        cases = normalized
                        if report.get("passed_cases") != sum(case["passed"] for case in cases):
                            raise ValueError("composite pass count disagrees with case gates")
                    if walking:
                        for case in cases:
                            if type(case["passed"]) is not bool or case["passed"] != (case["failures"] == []):
                                raise ValueError("inconsistent command/timing result")
                            if report.get("acceptance_variant") == "motor-plus-neutral-head-v1":
                                posture = case["posture"]["passed"]
                                motor = case["motor_battery_passed"]
                                if type(posture) is not bool or type(motor) is not bool or case["passed"] != (posture and motor):
                                    raise ValueError("inconsistent additive motor/posture gates")
                            if report.get("acceptance_variant") in COMPLETE_WALKING_VARIANTS:
                                additional = ("heading", "self_contact", "self_load") if report.get("acceptance_variant") in SELF_LOAD_WALKING_VARIANTS else ("heading", "self_contact")
                                gates = [case["posture"]["passed"], case["motor_battery_passed"],
                                         case["original_motor_posture_passed"]] + [case[key]["passed"] for key in additional]
                                if (any(type(value) is not bool for value in gates)
                                        or gates[2] != (gates[0] and gates[1])
                                        or case["passed"] != all(gates[2:])):
                                    raise ValueError("inconsistent motor/head/heading/body-contact gates")
                                for key in additional:
                                    if not isinstance(case[key].get("failures"), list) or case[key]["passed"] != (case[key]["failures"] == []):
                                        raise ValueError("inconsistent embedded rejection evidence")
                            case["fell"] = case["gait"]["fell"]
                        if report.get("passed_cases") != sum(c["passed"] for c in cases) or report.get("total_cases") != len(cases):
                            raise ValueError("walking pass count disagrees with cases")
                    directory = path.parent
                    cases = [{**case, "failure_summary": case_failure_summary(case)} for case in cases]
                    runs.append({"id": str(directory.relative_to(self.root)),
                                 "name": directory.name, "schema": schema,
                                 "acceptance_variant": report.get("acceptance_variant"),
                                 "supported_metrics": supported,
                                 "engine": "Genesis diagnostic" if "genesis" in schema else "C MuJoCo / BAM" if supported else "See report",
                                 "proof_class": report.get("proof_class", "visible_development" if dynamic else "unspecified"),
                                 "split": report.get("split", "visible-development"),
                                 "target_source": report.get("target_source", "See report"),
                                 "held_out": False, "policy_sha256": report.get("policy_sha256"),
                                 "suite_sha256": report.get("suite_sha256", report.get("spec_sha256")),
                                 "steering": report.get("steering"),
                                 "model_scope": report.get("model_scope"), "controller": report.get("controller"),
                                 "standing_policy_sha256": report.get("standing_policy_sha256"),
                                 "standing_policy_used": report.get("standing_policy_used"),
                                 "cases": cases, "passed": report.get("passed_cases") if laser else None,
                                 "total": len(cases) if gait else report.get("total_cases") if laser else None,
                                 "boundary": report.get("boundary", report.get("evidence_boundary", "Development evidence; see report.")),
                                 "integrity": self.integrity(directory),
                                 "artifacts": self.artifacts(directory)})
                except (OSError, ValueError, TypeError, AttributeError, KeyError) as error:
                    errors.append({"path": relative, "error": str(error)})
        return runs, errors

    def recovery_branch(self, path: Path, report: dict) -> dict:
        parent = path.parent.parent
        frozen_path = safe_path(self.root, str((parent / "freeze.json").relative_to(self.root)))
        result_path = safe_path(self.root, str((parent / "result.json").relative_to(self.root)))
        frozen, result = read_json(frozen_path), read_json(result_path)
        phase = result.get("phase")
        if (frozen.get("schema") != "microduck.recovery-freeze/v49"
                or frozen.get("parameters", {}).get("schema") != "microduck.recovery-diagnostic/v49"
                or phase not in {"compare", "search"} or result.get("complete") is not True
                or result.get("freeze_sha256") != self.digest(frozen_path)
                or report.get("anchor") not in {"original", "v48"}
                or report.get("repeat_exact") is not True
                or report not in result.get("branches" if phase == "compare" else "states", [])):
            raise ValueError("nested recovery report lacks its complete frozen diagnostic envelope")
        covered = manifest_entries(self.root, parent)
        # Entries are relative to the containing manifest, so require the
        # envelope as well as the branch's own evaluation and raw evidence.
        prefix = path.parent.name + "/"
        required = {"freeze.json", "result.json"} | {
            prefix + name for name in ("evaluation.json", "trajectory.jsonl.gz",
                                       "actions-float32.npy", "observations-float32.npy")}
        if (not required <= covered.keys()
                or any(self.digest(parent / name) != sha for name, sha in covered.items())):
            raise ValueError("recovery diagnostic manifest is incomplete or invalid")
        return {**report, "schema": "microduck.recovery-branch/v49", "held_out": False,
                "proof_class": "privileged_diagnostic" if phase == "search" else "counterfactual_diagnostic",
                "boundary": "Exposed full-state branch, not a standalone policy evaluation, held-out generalization or physical acceptance. See the original case and session gates."}

    def snapshot(self) -> dict:
        goal_path = self.root / "GOAL.md"
        queue_path = self.root / "TRAINING_ACTUALIZATION.md"
        goal = sections(goal_path.read_text()) if goal_path.exists() else {}
        queue = queue_path.read_text() if queue_path.exists() else ""
        tasks = []
        for chunk in re.split(r"(?m)^### ", queue)[1:]:
            title, _, body = chunk.partition("\n")
            checks = re.findall(r"(?m)^- \[([ x])\] (.+)", body)
            tasks.append({"title": title, "checked": sum(x == "x" for x, _ in checks),
                          "total": len(checks), "next": next((s for x, s in checks if x == " "), None)})
        runs, errors = self.evaluations()
        from duck_workspace.active import focus
        active_focus = focus(self.root, runs)
        training = []
        for path in sorted((self.root / "logs").glob("*/run.json")):
            try:
                safe_path(self.root, str(path.relative_to(self.root)))
                data = read_json(path)
                training.append({"id": path.parent.name, "recorded_status": data.get("status", "unspecified"),
                                 "process_liveness": "not_checked", "elapsed_s": data.get("elapsed_s"),
                                 "transitions": data.get("new_transitions"), "args": data.get("args"),
                                 **training_counts(data),
                                 "checkpoint": data.get("checkpoint"), "source_commit": data.get("source_commit"),
                                 "telemetry": self.training_telemetry(path.parent)})
            except (OSError, ValueError, AttributeError) as error:
                errors.append({"path": str(path.relative_to(self.root)), "error": str(error)})
        # Prioritize recorded work without asserting process liveness.
        training.sort(key=lambda r: ({"running": 2, "starting": 1}.get(r["recorded_status"], 0), r["id"]), reverse=True)
        return {"schema": "microduck.workspace/v1", "generated_at": datetime.now(timezone.utc).isoformat(),
                "read_only": True, "root": str(self.root), "head": git(self.root, "rev-parse", "HEAD"),
                "branch": git(self.root, "branch", "--show-current"), "dirty": git(self.root, "status", "--short"),
                "goal": goal, "queue": tasks, "evaluations": runs, "training": training, "errors": errors,
                "active_focus": active_focus,
                "source_documents": ["GOAL.md", "TRAINING_ACTUALIZATION.md"],
                "notice": "Receipt display only. Checkboxes, reward and checksums do not confer task acceptance or hardware authority."}

    def training_telemetry(self, directory: Path) -> dict:
        files = sorted(directory.glob("events.out.tfevents.*"))
        if not files:
            return {"status": "no_events"}
        try:
            for path in files:
                safe_path(self.root, str(path.relative_to(self.root)))
            # Optional reader from the already-installed training environment.
            # The workspace CLI still works with Python's standard library alone.
            from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
            accumulator = EventAccumulator(str(directory), size_guidance={"scalars": 256})
            accumulator.Reload()
            if "Train/mean_reward" not in accumulator.Tags()["scalars"]:
                return {"status": "no_reward_samples"}
            samples = accumulator.Scalars("Train/mean_reward")
            return {"status": "recorded", "last_iteration": samples[-1].step,
                    "last_wall_time": samples[-1].wall_time, "latest_reward": samples[-1].value,
                    "reward_curve": [[p.step, p.value] for p in samples]}
        except ImportError:
            return {"status": "optional_tensorboard_unavailable"}
        except (OSError, ValueError, KeyError, IndexError) as error:
            return {"status": "unreadable", "error": str(error)}

    def detail(self, run_id: str) -> dict:
        runs, _ = self.evaluations(run_id)
        run = next((run for run in runs if run["id"] == run_id), None)
        if run is None:
            raise ValueError("unknown development run")
        directory = safe_path(self.root, run_id)
        if run["schema"] == WALKING_SCHEMA:
            run["heading_evidence"] = self.heading_evidence(directory, run)
        trajectories = {}
        trace_file = "trajectory.jsonl" if "trajectory.jsonl" in run["artifacts"] else "trajectory.jsonl.gz"
        path = directory / trace_file
        if run["schema"] in LASER_SCHEMAS and trace_file in run["artifacts"]:
            if path.stat().st_size > TRAJECTORY_LIMIT:
                raise ValueError("trajectory exceeds inspection limit")
            from experiment_ops.compare import bounded_trace_lines, strict_json
            for row_index, line in enumerate(bounded_trace_lines(path, TRAJECTORY_LIMIT)):
                if row_index >= 50000:
                    raise ValueError("trajectory exceeds 50000-row inspection bound")
                row = strict_json(line)
                point = {key: row.get(key) for key in ("time_s", "robot_xyz_m", "target_xy_m", "distance_m",
                                                      "speed_m_s", "visible", "command", "tilt_deg", "fell", "latency_ms", "target_label", "target_epoch",
                                                      "body_velocity_m_s", "yaw_rate_rad_s", "foot_normal_n", "sole_clearance_m", "loaded_contact_slip_m_s", "face_world",
                                                      "actor_mode", "self_load_physics", "session_time_s")}
                trajectories.setdefault(row["case_id"], []).append(point)
        curve = read_json(directory / "learning-curve.json") if "learning-curve.json" in run["artifacts"] else []
        # Known evaluators render after the first control step (legacy/gait) or
        # after each second step (dynamic). UI time remains simulation time.
        frame_index = 1 if run["schema"] == "microduck.dynamic-laser-evaluation/v1" else 0
        video_origins = {case: rows[frame_index]["time_s"] for case, rows in trajectories.items()
                         if len(rows) > frame_index and f"{case}.mp4" in run["artifacts"]}
        return {**run, "trajectories": trajectories, "learning_curve": curve,
                "video_time_origins_s": video_origins}

    def heading_evidence(self, directory: Path, run: dict) -> dict:
        """Join a separately retained heading report, never replace old scores.

        Only the conventional sibling is considered. No scan of hidden banks,
        no latest/best-result selection and no simulator imports or evaluation.
        Missing or stale evidence leaves combined walking status unknown.
        """
        if run.get("acceptance_variant") in COMPLETE_WALKING_VARIANTS:
            return self.embedded_walking_evidence(directory, run)
        sibling = directory.with_name(directory.name + "-heading")
        try:
            safe_path(self.root, str(sibling.relative_to(self.root)))
            if not (sibling / "evaluation.json").exists():
                return {"status": "missing", "combined_passed_cases": None}
            if run["integrity"]["status"] != "manifest_verified" or self.integrity(sibling)["status"] != "manifest_verified":
                raise ValueError("both original and heading manifests must verify")
            required = {"training.json", "evaluation.json", "trajectory.jsonl", "policy.onnx"}
            if not required <= manifest_entries(self.root, directory).keys():
                raise ValueError("original manifest must cover all final evidence")
            data = read_json(sibling / "evaluation.json")
            training = read_json(safe_path(self.root, str((directory / "training.json").relative_to(self.root))))
            if (data.get("schema") != "microduck.walking-heading-evaluation/v1"
                    or data.get("held_out") is not False or data.get("physical_transfer_validated") is not False
                    or training.get("status") != "completed"):
                raise ValueError("only completed, visible, nonphysical heading evidence is supported")
            if (not re.fullmatch(r"[0-9a-f]{64}", str(data.get("checkpoint_sha256")))
                    or data["checkpoint_sha256"] != training.get("checkpoint_sha256")
                    or data.get("policy_sha256") != run["policy_sha256"]
                    or data["policy_sha256"] != self.digest(directory / "policy.onnx")):
                raise ValueError("heading policy/checkpoint identity mismatch")
            for name in ("SHA256SUMS", "evaluation.json", "trajectory.jsonl", "training.json"):
                if data.get("input_sha256", {}).get(name) != self.digest(directory / name):
                    raise ValueError(f"heading input identity mismatch: {name}")
            original = {case["case_id"]: case for case in run["cases"]}
            cases = data.get("case_reports")
            if (not isinstance(cases, list) or len(cases) != len(original)
                    or len(original) != len(run["cases"])
                    or {c["case_id"] for c in cases} != set(original)):
                raise ValueError("heading cases must exactly cover the original bank")
            for case in cases:
                heading = case["heading"]
                if (type(heading.get("passed")) is not bool or not isinstance(heading.get("failures"), list)
                        or heading["passed"] != (heading["failures"] == [])
                        or type(case.get("original_passed")) is not bool
                        or case["original_passed"] != original[case["case_id"]]["passed"]
                        or type(case.get("combined_passed")) is not bool
                        or case["combined_passed"] != (case["original_passed"] and heading["passed"])):
                    raise ValueError("inconsistent original/heading/combined case result")
            counts = {"total_cases": len(cases), "original_passed_cases": run["passed"],
                      "heading_passed_cases": sum(c["heading"]["passed"] for c in cases),
                      "combined_passed_cases": sum(c["combined_passed"] for c in cases)}
            if any(type(data.get(k)) is not int or data[k] != value for k, value in counts.items()):
                raise ValueError("heading totals disagree with case results")
            return {"status": "verified", **counts, "case_reports": cases,
                    "receipt": str(sibling.relative_to(self.root)),
                    "boundary": "Visible motor/posture plus heading only; not full generalization or physical acceptance."}
        except (OSError, ValueError, TypeError, AttributeError, KeyError) as error:
            return {"status": "invalid", "combined_passed_cases": None, "error": str(error)}

    def embedded_walking_evidence(self, directory: Path, run: dict) -> dict:
        """Project explicitly versioned evaluated gates; do not simulate or rescore."""
        try:
            if run["integrity"]["status"] != "manifest_verified":
                raise ValueError("complete receipt manifest must verify")
            covered = manifest_entries(self.root, directory)
            trace_file = "trajectory.jsonl" if (directory / "trajectory.jsonl").exists() else "trajectory.jsonl.gz"
            required = {"training.json", "evaluation.json", trace_file, "policy.onnx"}
            if not required <= covered.keys():
                raise ValueError("manifest omits required complete-controller evidence")
            training = read_json(safe_path(self.root, str((directory/"training.json").relative_to(self.root))))
            if training.get("status") != "completed" or not re.fullmatch(r"[0-9a-f]{64}", str(training.get("checkpoint_sha256"))):
                raise ValueError("completed checkpoint identity required")
            if run["policy_sha256"] != self.digest(directory/"policy.onnx"):
                raise ValueError("complete-controller policy identity mismatch")
            has_load = run.get("acceptance_variant") in SELF_LOAD_WALKING_VARIANTS
            if has_load:
                required_components = {"source-checkpoint.pt", "standing/training.json", "standing/policy.onnx", "standing/source-checkpoint.pt"}
                if not required_components <= covered.keys():
                    raise ValueError("manifest omits standing/walking component evidence")
                standing = read_json(safe_path(self.root, str((directory/"standing/training.json").relative_to(self.root))))
                if (standing.get("status") != "completed"
                        or standing.get("checkpoint_sha256") != self.digest(directory/"standing/source-checkpoint.pt")
                        or training["checkpoint_sha256"] != self.digest(directory/"source-checkpoint.pt")
                        or run.get("standing_policy_sha256") != self.digest(directory/"standing/policy.onnx")
                        or type(run.get("standing_policy_used")) is not bool
                        or run["standing_policy_used"] != (run["acceptance_variant"] in PAIRED_WALKING_VARIANTS)):
                    raise ValueError("standing/walking component identity or routing mismatch")
            scope = run.get("model_scope") or {}
            if scope.get("variant") != "complete-contact-v11" or scope.get("old_reduced_model_acceptance") is not False:
                raise ValueError("explicit complete-contact model scope required")
            for name in ("scene", "robot"):
                relative = f"evaluator-source/experiments/walking/models/contact-v11/{name}.xml"
                if relative not in covered or scope.get(name+"_sha256") != self.digest(directory/relative):
                    raise ValueError("complete contact model identity mismatch")
            cases = run["cases"]
            if len({c["case_id"] for c in cases}) != len(cases):
                raise ValueError("duplicate complete-controller case")
            projected = [{"case_id": c["case_id"], "original_passed": c["original_motor_posture_passed"],
                          "heading": c["heading"], "self_contact": c["self_contact"],
                          **({"self_load": c["self_load"]} if has_load else {}), "combined_passed": c["passed"]} for c in cases]
            return {"status": "verified", "embedded": True, "total_cases": len(cases),
                    "original_passed_cases": sum(c["original_passed"] for c in projected),
                    "heading_passed_cases": sum(c["heading"]["passed"] for c in projected),
                    "self_contact_passed_cases": sum(c["self_contact"]["passed"] for c in projected),
                    "self_load_passed_cases": sum(c["self_load"]["passed"] for c in projected) if has_load else None,
                    "combined_passed_cases": sum(c["combined_passed"] for c in projected),
                    "case_reports": projected, "receipt": str(directory.relative_to(self.root)),
                    "controller": run.get("controller"),
                    "boundary": "Explicit model/controller-scoped visible gates; not raw-policy improvement or physical acceptance."}
        except (OSError, ValueError, TypeError, AttributeError, KeyError) as error:
            return {"status": "invalid", "combined_passed_cases": None, "error": str(error)}

    def artifact(self, relative: str) -> Path:
        # Exact files indexed from development receipts only; never expose the repo root.
        runs, _ = self.evaluations(relative.rpartition("/")[0])
        allowed = {run["id"] + "/" + name for run in runs for name in run["artifacts"]}
        if relative not in allowed:
            raise ValueError("artifact is not indexed development evidence")
        return safe_path(self.root, relative)


def doctor(root: Path = ROOT) -> dict:
    checks = []
    def add(name, passed, observed, next_step=""):
        checks.append({"name": name, "passed": passed, "observed": observed, "next_step": next_step})
    python = root / ".venv-apple/bin/python"
    add("Apple runtime", python.exists(), str(python), "./scripts/setup_apple.sh")
    if python.exists():
        probe = 'import importlib.metadata as m,json,platform,torch; print(json.dumps({"python":platform.python_version(),"machine":platform.machine(),"mps":torch.backends.mps.is_available(),"packages":{n:m.version(n) for n in ("genesis-world","torch","rsl-rl-lib","mujoco","onnxruntime")}}))'
        try:
            result = subprocess.run([str(python), "-c", probe], capture_output=True, text=True, timeout=30)
            data = json.loads(result.stdout) if result.returncode == 0 else {"error": result.stderr[-1200:]}
            lock = (root / "environments/apple/requirements.lock").read_text()
            expected = {}
            for package in ("genesis-world", "torch", "rsl-rl-lib", "mujoco", "onnxruntime"):
                match = re.search(r"(?m)^" + re.escape(package) + r"==([^\s\\]+)", lock)
                if not match:
                    raise ValueError(f"missing pinned package in Apple lock: {package}")
                expected[package] = match[1]
            good = data.get("mps") is True and data.get("python", "").startswith("3.12.") and all(data.get("packages", {}).get(k) == v for k, v in expected.items())
            add("Pinned packages and MPS availability", good, data, "./scripts/setup_apple.sh; inspect environment drift")
        except (OSError, ValueError, subprocess.TimeoutExpired) as error:
            add("Pinned packages and MPS availability", False, str(error))
    result = subprocess.run([str(python) if python.exists() else "python3", "scripts/freeze_contract.py", "--check"],
                            cwd=root, capture_output=True, text=True, timeout=30)
    add("Frozen contract", result.returncode == 0, (result.stdout + result.stderr)[-1500:], "Resolve drift in the affected versioned lane before training")
    bam = os.environ.get("BAM_REPO") or (str(root / ".workspace/bam") if (root / ".workspace/bam").is_dir() else None)
    if bam:
        actual = git(Path(bam), "rev-parse", "HEAD")
        dirty = git(Path(bam), "status", "--porcelain")
        lock = read_json(root / "microduck_contract/actuator/bam-m6-xl330-v1.lock.json")
        add("BAM authority checkout", actual == lock["golden_vectors"]["authority_commit"] and not dirty,
            {"head": actual, "dirty": dirty, "path": bam},
            "Use scripts/materialize_bam_authority.py and export BAM_REPO")
    else:
        add("BAM authority checkout", False, "BAM_REPO is unset; independent evaluation needs the pinned checkout",
            "python scripts/materialize_bam_authority.py /path/to/bam; export BAM_REPO=/path/to/bam")
    return {"schema": "microduck.workspace-doctor/v1", "checks": checks,
            "ready_for_evaluator_setup": all(x["passed"] for x in checks),
            "physics_executed": False, "training_executed": False,
            "boundary": "Availability and contract checks only; no simulator smoke, task acceptance or compute authorization."}


def new_behavior(root: Path, slug: str, request: str) -> Path:
    if not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", slug):
        raise ValueError("use a lowercase hyphenated behavior name")
    directory = safe_path(root, f"experiments/behaviors/{slug}")
    directory.mkdir(parents=True, exist_ok=False)
    spec = {"schema": "microduck.behavior-draft/v2", "id": slug, "request": request,
            "status": "draft", "hypothesis": None, "model_variant": None,
            "actor_inputs": [], "privileged_training_inputs": [], "target_source": None,
            "physics_changes": [], "reward_terms": [], "failure_conditions": [],
            "success_metrics": [], "visible_suite": None, "baseline": None,
            "budget": {"num_envs": 64, "smoke_iterations": 5, "training_iterations": None, "seed": None},
            "implementation": {"train_entrypoint": None, "evaluate_entrypoint": None},
            "claim_scope": "visible_development", "next_decision": None,
            "quality_plan": new_quality_plan()}
    (directory / "spec.json").write_text(json.dumps(spec, indent=2) + "\n")
    (directory / "NOTES.md").write_text(f"# {slug}\n\n{request}\n\nThis is a draft, not a runnable or authorized experiment.\nComplete spec.json using docs/workspace/BEHAVIOR_WORKFLOW.md.\nKeep the ordered queue in TRAINING_ACTUALIZATION.md.\n\n## Experiment notes\n\nRecord the intervention, fixed inputs, run/receipt paths, outcome and next decision here.\n")
    return directory


def check_spec(path: Path) -> list[str]:
    data = read_json(path)
    if isinstance(data, dict) and data.get("schema") == "microduck.behavior-draft/v1":
        return ["legacy v1 draft lacks the required quality contract; create a separate v2 draft with quality_plan; do not rewrite frozen artifacts"]
    if not isinstance(data, dict) or data.get("schema") != "microduck.behavior-draft/v2":
        return ["unsupported behavior draft schema"]
    required = ("request", "hypothesis", "model_variant", "actor_inputs", "target_source",
                "reward_terms", "failure_conditions", "success_metrics", "visible_suite", "baseline", "next_decision")
    missing = [key for key in required if not data.get(key)]
    for key in ("actor_inputs", "privileged_training_inputs", "physics_changes", "reward_terms", "failure_conditions", "success_metrics"):
        if not isinstance(data.get(key), list):
            missing.append(key + " must be a list")
    budget = data.get("budget") if isinstance(data.get("budget"), dict) else {}
    implementation = data.get("implementation") if isinstance(data.get("implementation"), dict) else {}
    for key in ("num_envs", "smoke_iterations", "training_iterations", "seed"):
        value = budget.get(key)
        if type(value) is not int or value < (0 if key == "seed" else 1):
            missing.append("budget." + key)
    for key in ("train_entrypoint", "evaluate_entrypoint"):
        if not implementation.get(key):
            missing.append("implementation." + key)
    if data.get("claim_scope") != "visible_development":
        missing.append("claim_scope must remain visible_development in this draft tool")
    if data.get("status") != "draft":
        missing.append("status must remain draft; planning completeness is not acceptance")
    missing.extend(check_quality_plan(data.get("quality_plan")))
    return missing
