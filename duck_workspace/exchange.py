"""Source-bound workspace metadata; never imports a simulator or executes a packet."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat

from duck_workspace.core import ROOT, git, safe_path

SCHEMA_PATH = ROOT / "docs/workspace/exchange/workspace_adapter.v1.schema.json"
PACKET_LIMIT = 2 * 1024 * 1024
SOURCE_LIMIT = 8 * 1024 * 1024
PERMISSIONS = dict(inspect=True, execute=False, mutate_sources=False, train=False,
                   hardware=False, promote=False, paid_compute=False)
SOURCES = (
    ("agents", "AGENTS.md", "current operating instructions"),
    ("queue", "TRAINING_ACTUALIZATION.md", "ordered work and acceptance gates"),
    ("goal", "GOAL.md", "concise current status; subordinate to the ordered queue"),
    ("action", "microduck_contract/interface/action-v1.json", "candidate local action interface"),
    ("observation", "microduck_contract/interface/observation-v1.json", "candidate local observation interface"),
    ("control", "microduck_contract/interface/control-v1.json", "candidate local timing interface"),
    ("environment", "microduck/velocity_env.py", "native frame and observation implementation"),
    ("runtime", "environments/apple/requirements.lock", "pinned Apple runtime dependencies"),
    ("skill", ".agents/skills/microduck-experiments/SKILL.md", "project workflow guidance"),
    ("lessons", "docs/workspace/RETROSPECTIVE.md", "historical findings; no execution authority"),
    ("inspector", "duck_workspace/core.py", "native evidence inspection semantics"),
    ("active_work", "duck_workspace/active.py", "read-only active evidence and training-source checks"),
    ("active_focus", "docs/workspace/active-experiment.json", "working inspection focus; subordinate to the ordered queue"),
    ("exporter", "duck_workspace/exchange.py", "metadata projection and validation semantics"),
)


def _json(raw: bytes):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def reject(value):
        raise ValueError(f"non-finite JSON number: {value}")

    def finite_float(value):
        result = float(value)
        if not math.isfinite(result):
            raise ValueError("non-finite JSON number")
        return result

    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=reject, parse_float=finite_float)
    except (UnicodeError, RecursionError) as error:
        raise ValueError("invalid JSON encoding or excessive nesting") from error


def _read_regular(path: Path, limit: int) -> bytes:
    """Bound reads even if a path is replaced with a FIFO between stat/open."""
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode):
        raise ValueError("exchange inputs must be regular files, not symlinks or special files")
    if before.st_size > limit:
        raise ValueError(f"input exceeds {limit} byte inspection limit")
    descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(descriptor, "rb") as stream:
        opened = os.fstat(stream.fileno())
        if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
            raise ValueError("input was replaced while opening")
        raw = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
    if len(raw) > limit:
        raise ValueError(f"input exceeds {limit} byte inspection limit")
    if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
        raise ValueError("input changed while reading; retain a stable copy")
    return raw


def sha256(path: Path) -> str:
    return hashlib.sha256(_read_regular(path, SOURCE_LIMIT)).hexdigest()


def load_packet(path: Path):
    return _json(_read_regular(path, PACKET_LIMIT))


def _schema_errors(value, schema, path="$"):
    """Validate the exact vocabulary used by the checked-in v1 contract.

    This is deliberately not a general JSON Schema implementation. A future
    contract using another keyword is refused until this reader is updated.
    """
    supported = {"$schema", "$id", "title", "type", "additionalProperties", "required",
                 "properties", "const", "enum", "items", "minItems", "maxItems",
                 "minLength", "pattern", "format", "minimum", "maximum", "exclusiveMinimum"}
    if set(schema) - supported:
        return [f"{path}: unsupported schema keywords"]
    errors = []
    kinds = schema.get("type", [])
    kinds = [kinds] if isinstance(kinds, str) else kinds
    checks = {"object": type(value) is dict, "array": type(value) is list,
              "string": type(value) is str, "integer": type(value) is int,
              "number": type(value) in (int, float), "boolean": type(value) is bool,
              "null": value is None}
    if kinds and not any(checks.get(kind, False) for kind in kinds):
        return [f"{path}: expected {' or '.join(kinds)}"]
    if "const" in schema and (type(value) is not type(schema["const"]) or value != schema["const"]):
        errors.append(f"{path}: expected constant {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: unknown enum value")
    if type(value) is dict:
        properties = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}.{key}: required")
        if schema.get("additionalProperties") is False and set(value) - set(properties):
            errors.append(f"{path}: unexpected properties {sorted(set(value) - set(properties))}")
        for key in value.keys() & properties.keys():
            errors.extend(_schema_errors(value[key], properties[key], f"{path}.{key}"))
    elif type(value) is list:
        if not schema.get("minItems", 0) <= len(value) <= schema.get("maxItems", math.inf):
            return [f"{path}: invalid array length"]
        for index, item in enumerate(value):
            if "items" in schema:
                errors.extend(_schema_errors(item, schema["items"], f"{path}[{index}]"))
    elif type(value) is str:
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{path}: string too short")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{path}: pattern mismatch")
        if schema.get("format") == "date-time":
            try:
                if not re.fullmatch(r"\d{4}-\d\d-\d\d[Tt]\d\d:\d\d:\d\d(?:\.\d+)?(?:[Zz]|[+-]\d\d:\d\d)", value):
                    raise ValueError()
                datetime.fromisoformat(value.upper().replace("Z", "+00:00"))
            except ValueError:
                errors.append(f"{path}: invalid date-time")
    elif type(value) in (int, float):
        if type(value) is float and not math.isfinite(value):
            errors.append(f"{path}: non-finite number")
        elif (value < schema.get("minimum", -math.inf) or value > schema.get("maximum", math.inf)
              or value <= schema.get("exclusiveMinimum", -math.inf)):
            errors.append(f"{path}: number out of range")
    return errors


def _relative(path: str) -> bool:
    parts = PurePosixPath(path).parts
    return (bool(parts) and not path.startswith("/") and "\\" not in path and ":" not in path
            and all(part not in ("", ".", "..") for part in path.split("/"))
            and not any(ord(char) < 32 for char in path))


def validate(packet, source_root: Path | None = None) -> dict:
    schema_bytes = _read_regular(SCHEMA_PATH, PACKET_LIMIT)
    errors = _schema_errors(packet, _json(schema_bytes))
    source_state = "not_requested"
    if not errors:
        if packet["contract_sha256"] != hashlib.sha256(schema_bytes).hexdigest():
            errors.append("contract_sha256: does not match the local contract bytes")
        for group in ("sources", "profiles", "capabilities"):
            ids = [item["id"] for item in packet[group]]
            if len(ids) != len(set(ids)):
                errors.append(f"{group}: duplicate id")
        sources = {item["id"] for item in packet["sources"]}
        for label, ids in [("source_priority", packet["workspace"]["mandate"]["source_priority"])] + [
            (f"profile {profile['id']} source_ids", profile["source_ids"]) for profile in packet["profiles"]
        ]:
            if len(ids) != len(set(ids)) or not set(ids) <= sources:
                errors.append(f"{label}: duplicate or unresolved source reference")
        paths = [source["path"] for source in packet["sources"]]
        if len(paths) != len(set(paths)) or not all(_relative(path) for path in paths):
            errors.append("sources: paths must be unique canonical relative POSIX paths")
        for profile in packet["profiles"]:
            action = profile["action"]
            if len(action["ordered_names"]) != action["dimension"] or len(action["units"]) != action["dimension"]:
                errors.append(f"profile {profile['id']}: action name/unit counts differ from dimension")
            if len(set(action["ordered_names"])) != action["dimension"]:
                errors.append(f"profile {profile['id']}: duplicate action name")
    if source_root is not None:
        source_state = "not_attempted_invalid_packet"
        if not errors:
            source_state = "verified"
            for source in packet["sources"]:
                try:
                    path = safe_path(source_root, source["path"])
                    if not path.is_file() or path.stat().st_size > SOURCE_LIMIT or sha256(path) != source["sha256"]:
                        raise ValueError("missing, oversized or mismatched file")
                except (OSError, ValueError) as error:
                    errors.append(f"source {source['id']}: {error}")
            repository = packet["workspace"]["repository"]
            if git(source_root, "rev-parse", "HEAD") != repository["head"]:
                errors.append("repository: HEAD differs from the supplied source root")
            if git(source_root, "rev-parse", "--abbrev-ref", "HEAD") != repository["branch"]:
                errors.append("repository: branch differs from the supplied source root")
            if errors:
                source_state = "mismatch"
    return {"schema": "microduck.workspace-exchange-inspection/v1", "valid": not errors,
            "errors": sorted(errors), "source_verification": source_state,
            "native_gate_checked": False, "execution_authorized": False,
            "policy_portable": False,
            "policy_portability": "not_established",
            "note": "Structure and optional source-byte identity only. Native gate and dirty flag are producer observations; evaluator acceptance is not checked."}


def export_workspace(owner_task: str, root: Path = ROOT) -> dict:
    if not owner_task.strip():
        raise ValueError("owner_task must identify the exporting workspace task")
    raw_sources = {}
    sources = []
    for identifier, relative, role in SOURCES:
        path = safe_path(root, relative)
        raw = _read_regular(path, SOURCE_LIMIT)
        raw_sources[identifier] = raw
        sources.append(dict(id=identifier, path=relative, role=role,
                            sha256=hashlib.sha256(raw).hexdigest()))
    action = _json(raw_sources["action"])
    observation = _json(raw_sources["observation"])
    control = _json(raw_sources["control"])
    try:
        interface_valid = not (action.get("interface_id") != "microduck.action.v1"
        or observation.get("interface_id") != "microduck.obs.v1"
        or control.get("control_id") != "microduck.control.50hz.v1"
        or action.get("shape") != [1, 14] or observation.get("shape") != [1, 61]
        or action.get("joint_order") != observation.get("joint_order")
        or sum(item["size"] for item in observation["layout"]) != 61
        or action.get("dtype") != "float32" or observation.get("dtype") != "float32"
        or action.get("semantics") != "unfiltered_delta_from_home_rad" or action.get("scale") != 1.0
        or control.get("control_hz") != 50 or control.get("physics_dt_s") != .005
        or control.get("decimation") != 4 or control.get("action_filter") != "none")
    except (AttributeError, KeyError, TypeError):
        interface_valid = False
    if not interface_valid:
        raise ValueError("native interface changed; version/review the adapter before exporting")
    def capability(identifier, kind, native, description, *entrypoint):
        return dict(id=identifier, kind=kind, native_schema=native, availability="implemented",
                    description=description, read_only=True, entrypoint=list(entrypoint))
    packet = {
        "schema_version": "robotics.workspace_exchange.v1",
        "contract_sha256": sha256(SCHEMA_PATH),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "workspace": {
            "id": "microduck-rl-genesis", "domain": "simulated biped behavior training on macOS",
            "repository": {"head": git(root, "rev-parse", "HEAD"),
                           "branch": git(root, "rev-parse", "--abbrev-ref", "HEAD"),
                           "dirty": bool(git(root, "status", "--porcelain"))},
            "mandate": {"summary": "Work in one task. Follow the ordered training queue; retain native interface, evaluator and authority boundaries. Historical lessons do not grant actions.",
                        "source_priority": ["agents", "queue", "goal", "action", "observation", "control"]},
            "owner_task": owner_task,
        },
        "sources": sources,
        "profiles": [{
            "id": "microduck-local-v1", "robot_family": "MicroDuck",
            "native_schema": "microduck.interface/v1",
            "scope": "Candidate repository-local locomotion interface; no checkpoint, backend conformance, held-out acceptance or physical transfer is asserted.",
            "action": {"dimension": 14, "ordered_names": action["joint_order"], "units": ["rad"] * 14,
                       "encoding": "float32 tensor [1,14]; metadata contains no action payload",
                       "representation": action["semantics"],
                       "transform_policy": "Native target is home joint position plus action, scale 1.0, no post-policy filter. No shared conversion, clipping or assistance is supplied."},
            "observation": {"dimension": 61,
                            "description": "; ".join(f"{item['name']}:{item['size']}" for item in observation["layout"]),
                            "privileged_state_policy": "This layout is the actor interface. Reward/evaluation simulator state and command-source privilege require task-specific declarations; current laser target input is simulator ground truth, not camera control."},
            "timing": {"control_hz": 50, "physics_step_s": .005,
                       "clock": "simulation seconds; four physics steps per control tick; no wall-clock deadline guarantee",
                       "frame_policy": "Native velocity_env.py body-frame angular velocity and projected gravity; home-relative ordered joint positions. No coordinate conversion or camera extrinsic is exported."},
            "source_ids": ["action", "observation", "control", "environment", "goal"],
        }],
        "capabilities": [
            capability("status", "workspace", "microduck.workspace/v1", "Queue and development-receipt projection; recorded process liveness remains unchecked.", "./scripts/duck", "status", "--json"),
            capability("prepare", "diagnostic", "microduck.active-preflight/v1", "Source-bound working-case and active-training-record inspection; never launches a job.", "./scripts/duck", "prepare"),
            capability("doctor", "diagnostic", "microduck.workspace-doctor/v1", "Native read-only dependency and frozen-contract readiness checks; not run by this exporter.", "./scripts/duck", "doctor"),
            capability("studio", "evidence", "microduck.workspace/v1", "Local recorded video, trajectory and metric inspection; its URLs are not portable artifact addresses.", "./scripts/duck", "studio"),
            capability("behavior-spec", "behavior_spec", "microduck.behavior-draft/v1", "Inspect completeness of an existing task draft; does not validate experiment design or authorize training.", "./scripts/duck", "check-spec", "<existing-spec.json>"),
            capability("lessons", "lesson", "markdown", "Source-linked retrospective covering successful and negative experiment evidence.", "docs/workspace/RETROSPECTIVE.md"),
        ],
        "evidence": {"native_classes": ["first_party_development", "visible_development", "unspecified"],
                     "native_record_schemas": ["microduck.laser-evaluation/v1", "microduck.dynamic-laser-evaluation/v1", "microduck.laser-gait-evaluation/v3", "microduck.first-party-evaluation/v1"],
                     "integrity_meaning": "Native containing-manifest verification establishes covered file bytes. Missing, unknown or corrupt evidence is not promoted; semantic validity is separate.",
                     "acceptance_meaning": "Native task evaluator and current authority govern acceptance. Historical, visible-development, held-out and physical claims remain distinct. This packet evaluates none of them.",
                     "records_exported": False},
        "permissions": dict(PERMISSIONS),
        "native_gate": {"status": "source_only", "detail": "Read-only source projection. No evaluator, physics runtime, paid-compute inventory or hardware gateway was invoked."},
        "limitations": [
            "Only metadata is shared. Entrypoints are descriptions, never commands to execute from a received packet.",
            "Owner task identifies this workspace-tool export; it does not claim exclusive ownership of concurrent behavior experiments.",
            "Source hashes bind current file bytes, including uncommitted changes. HEAD alone does not bind a dirty worktree; this is not an atomic snapshot of every repository file.",
            "Queue and concise status can disagree during ongoing work. Preserve their recorded priority and hashes; do not infer a merged completion or permission.",
            "No policy, trace, media, checkpoint, training result or hardware authority is exported. Shape and units alone do not establish policy portability.",
            "The native interface remains candidate-repo-local. Metadata conformance does not establish cross-backend physics equivalence.",
        ],
    }
    result = validate(packet, root)
    if not result["valid"]:
        raise ValueError("exchange refused: " + "; ".join(result["errors"]))
    return packet


def check_conformance() -> dict:
    """Run shared data fixtures; all entrypoint strings remain inert."""
    fixture_path = SCHEMA_PATH.with_name("workspace_adapter.v1.fixtures.json")
    pack = load_packet(fixture_path)
    if (pack.get("schema_version") != "robotics.workspace_conformance_fixtures.v1"
        or pack.get("contract_sha256") != sha256(SCHEMA_PATH) or not pack.get("cases")):
        raise ValueError("fixture version, contract bytes or cases are invalid")
    cases = []
    for case in pack["cases"]:
        result = validate(case["payload"])
        cases.append({"id": case["id"], "expected_valid": case["expected_valid"],
                      "actual_valid": result["valid"], "passed": result["valid"] is case["expected_valid"]
                      and result["execution_authorized"] is False and result["policy_portable"] is False,
                      "execution_authorized": result["execution_authorized"],
                      "policy_portable": result["policy_portable"]})
    return {"schema": "microduck.workspace-exchange-conformance/v1",
            "contract_sha256": sha256(SCHEMA_PATH), "fixtures_sha256": sha256(fixture_path),
            "passed": bool(cases) and all(case["passed"] for case in cases),
            "cases": cases, "source_verification": "not_requested_synthetic_fixtures",
            "execution_authorized": False, "policy_portable": False}
