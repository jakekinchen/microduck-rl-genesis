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

ROOT = Path(__file__).resolve().parents[1]
DEVELOPMENT_ROOTS = ("receipts/laser-follow", "receipts/first-party-development", "receipts/laser-dynamic", "receipts/laser-gait")
GAIT_SCHEMA = "microduck.laser-gait-evaluation/v3"
LASER_SCHEMAS = {"microduck.laser-evaluation/v1", "microduck.dynamic-laser-evaluation/v1", GAIT_SCHEMA}
JSON_LIMIT = 32 * 1024 * 1024


def safe_path(root: Path, relative: str) -> Path:
    """Reject traversal and symlinks, including symlinked parent directories."""
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts or not rel.parts:
        raise ValueError("expected a path inside this workspace")
    current = root.resolve()
    for part in rel.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("symlinked evidence is not served")
    if not current.resolve().is_relative_to(root.resolve()):
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
            bad = [name for name, digest in entries.items()
                   if self.digest(safe_path(manifest_root, name)) != digest]
            return {"status": "invalid" if bad else "manifest_verified",
                    "files": len(entries), "mismatches": bad}
        except (OSError, ValueError) as error:
            return {"status": "invalid", "error": str(error)}

    def artifacts(self, directory: Path) -> dict[str, str]:
        result = {}
        for path in sorted(directory.iterdir()):
            if path.suffix not in {".json", ".jsonl", ".mp4", ".png", ".parquet"}:
                continue
            try:
                path = safe_path(self.root, str(path.relative_to(self.root)))
                if path.is_file():
                    result[path.name] = "/artifact?path=" + quote(str(path.relative_to(self.root)), safe="")
            except ValueError:
                continue
        return result

    def evaluations(self) -> tuple[list[dict], list[dict]]:
        runs, errors = [], []
        for base in DEVELOPMENT_ROOTS:
            for path in sorted((self.root / base).glob("**/evaluation.json")):
                if any(word in path.parent.name.lower() for word in ("reserved", "heldout", "held-out", "acceptance")):
                    continue
                relative = str(path.relative_to(self.root))
                try:
                    safe_path(self.root, relative)
                    report = read_json(path)
                    if not isinstance(report, dict):
                        raise ValueError("evaluation report must be an object")
                    schema = report.get("schema", report.get("schema_version", ""))
                    dynamic = schema == "microduck.dynamic-laser-evaluation/v1"
                    gait = schema == GAIT_SCHEMA
                    visible = (report.get("reserved_opened") is False and report.get("physical_transfer_validated") is False and report.get("proof_class") == "visible_development") if gait else (report.get("canonical_held_out") is False and report.get("split") in {"nominal", "development"}) if dynamic else report.get("held_out") is False
                    if not visible:
                        raise ValueError("only explicitly visible development reports are supported")
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
                    directory = path.parent
                    runs.append({"id": str(directory.relative_to(self.root)),
                                 "name": directory.name, "schema": schema,
                                 "supported_metrics": supported,
                                 "engine": "Genesis diagnostic" if "genesis" in schema else "C MuJoCo / BAM" if supported else "See report",
                                 "proof_class": report.get("proof_class", "visible_development" if dynamic else "unspecified"),
                                 "split": report.get("split", "visible-development"),
                                 "target_source": report.get("target_source", "See report"),
                                 "held_out": False, "policy_sha256": report.get("policy_sha256"),
                                 "suite_sha256": report.get("suite_sha256", report.get("spec_sha256")),
                                 "steering": report.get("steering"),
                                 "cases": cases, "passed": report.get("passed_cases") if laser else None,
                                 "total": len(cases) if gait else report.get("total_cases") if laser else None,
                                 "boundary": report.get("boundary", report.get("evidence_boundary", "Development evidence; see report.")),
                                 "integrity": self.integrity(directory),
                                 "artifacts": self.artifacts(directory)})
                except (OSError, ValueError, TypeError, AttributeError, KeyError) as error:
                    errors.append({"path": relative, "error": str(error)})
        return runs, errors

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
                                 "checkpoint": data.get("checkpoint"), "source_commit": data.get("source_commit"),
                                 "telemetry": self.training_telemetry(path.parent)})
            except (OSError, ValueError, AttributeError) as error:
                errors.append({"path": str(path.relative_to(self.root)), "error": str(error)})
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
        runs, _ = self.evaluations()
        run = next((run for run in runs if run["id"] == run_id), None)
        if run is None:
            raise ValueError("unknown development run")
        directory = safe_path(self.root, run_id)
        trajectories = {}
        path = directory / "trajectory.jsonl"
        if run["schema"] in LASER_SCHEMAS and "trajectory.jsonl" in run["artifacts"]:
            if path.stat().st_size > JSON_LIMIT:
                raise ValueError("trajectory exceeds inspection limit")
            with path.open() as stream:
                for line in stream:
                    row = json.loads(line)
                    point = {key: row.get(key) for key in ("time_s", "robot_xyz_m", "target_xy_m", "distance_m",
                                                          "speed_m_s", "visible", "command", "tilt_deg", "fell", "latency_ms", "target_label", "target_epoch")}
                    trajectories.setdefault(row["case_id"], []).append(point)
        curve = read_json(directory / "learning-curve.json") if "learning-curve.json" in run["artifacts"] else []
        # Known evaluators render after the first control step (legacy/gait) or
        # after each second step (dynamic). UI time remains simulation time.
        frame_index = 1 if run["schema"] == "microduck.dynamic-laser-evaluation/v1" else 0
        video_origins = {case: rows[frame_index]["time_s"] for case, rows in trajectories.items()
                         if len(rows) > frame_index and f"{case}.mp4" in run["artifacts"]}
        return {**run, "trajectories": trajectories, "learning_curve": curve,
                "video_time_origins_s": video_origins}

    def artifact(self, relative: str) -> Path:
        # Exact files indexed from development receipts only; never expose the repo root.
        runs, _ = self.evaluations()
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
    spec = {"schema": "microduck.behavior-draft/v1", "id": slug, "request": request,
            "status": "draft", "hypothesis": None, "model_variant": None,
            "actor_inputs": [], "privileged_training_inputs": [], "target_source": None,
            "physics_changes": [], "reward_terms": [], "failure_conditions": [],
            "success_metrics": [], "visible_suite": None, "baseline": None,
            "budget": {"num_envs": 64, "smoke_iterations": 5, "training_iterations": None, "seed": None},
            "implementation": {"train_entrypoint": None, "evaluate_entrypoint": None},
            "claim_scope": "visible_development", "next_decision": None}
    (directory / "spec.json").write_text(json.dumps(spec, indent=2) + "\n")
    (directory / "NOTES.md").write_text(f"# {slug}\n\n{request}\n\nThis is a draft, not a runnable or authorized experiment.\nComplete spec.json using docs/workspace/BEHAVIOR_WORKFLOW.md.\nKeep the ordered queue in TRAINING_ACTUALIZATION.md.\n\n## Experiment notes\n\nRecord the intervention, fixed inputs, run/receipt paths, outcome and next decision here.\n")
    return directory


def check_spec(path: Path) -> list[str]:
    data = read_json(path)
    if not isinstance(data, dict) or data.get("schema") != "microduck.behavior-draft/v1":
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
    return missing
