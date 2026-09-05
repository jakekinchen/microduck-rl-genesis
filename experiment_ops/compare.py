"""Compare recorded development traces without executing either producer."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import struct

MAX_BYTES = 16 * 1024 * 1024
MAX_ROWS = 20000
MAX_CASES = 256
VECTOR_FIELDS = {"action_rad": 14, "command": 3, "robot_xyz_m": 3, "target_xy_m": 2}
EVENT_FIELDS = ("fell", "visible", "contacts")


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def reject(value):
        raise ValueError(f"nonfinite JSON: {value}")

    result = json.loads(text, object_pairs_hook=pairs, parse_constant=reject)
    def finite(value):
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("nonfinite numeric value")
        if isinstance(value, dict):
            for child in value.values():
                finite(child)
        if isinstance(value, list):
            for child in value:
                finite(child)
    finite(result)
    return result


def exact_vector(values):
    # JSON does not retain source tensor dtype/bytes. Compare the parsed values
    # as binary64, with no rounding, tolerance, clipping or signed-zero erasure.
    return b"".join(struct.pack("!d", value) for value in values)


def load_trace(path: Path, action_width=14):
    path = path.resolve(strict=True)
    if not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise ValueError(f"trace must be a regular file <= {MAX_BYTES} bytes: {path}")
    before = path.stat()
    identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
    cases, digest, rows, consumed = {}, hashlib.sha256(), 0, 0
    with path.open("rb") as stream:
        for line, raw in enumerate(stream, 1):
            consumed += len(raw)
            if consumed > MAX_BYTES or len(raw) > 128 * 1024:
                raise ValueError("trace exceeds bounded read limit")
            digest.update(raw)
            if not raw.strip():
                raise ValueError(f"blank trace row at line {line}")
            row = strict_json(raw)
            if not isinstance(row, dict):
                raise ValueError(f"row {line} is not an object")
            case = row.get("case_id")
            time = row.get("time_s")
            if not isinstance(case, str) or not case or len(case) > 160:
                raise ValueError(f"invalid case_id at line {line}")
            if not number(time) or time < 0:
                raise ValueError(f"invalid time_s at line {line}")
            for field, width in VECTOR_FIELDS.items():
                if field == "action_rad":
                    width = action_width
                value = row.get(field)
                if field not in row:
                    continue  # Missing telemetry is reported, never invented.
                if value is None and field == "target_xy_m":
                    continue
                if not isinstance(value, list) or len(value) != width or not all(number(x) for x in value):
                    raise ValueError(f"invalid {field} at line {line}; expected {width} finite numbers")
            for field in ("fell", "visible"):
                if field in row and type(row[field]) is not bool:
                    raise ValueError(f"{field} must be boolean at line {line}")
            for field in ("distance_m", "speed_m_s", "tilt_deg"):
                if field in row and not number(row[field]):
                    raise ValueError(f"{field} must be finite at line {line}")
            if "contacts" in row and (not isinstance(row["contacts"], list) or
                                      not all(isinstance(x, str) for x in row["contacts"])):
                raise ValueError(f"contacts must be canonical pair-name strings at line {line}")
            group = cases.setdefault(case, [])
            if group and time <= group[-1]["time_s"]:
                raise ValueError(f"non-increasing/duplicate case time at line {line}")
            row["_line"] = line
            group.append(row)
            rows += 1
            if rows > MAX_ROWS or len(cases) > MAX_CASES:
                raise ValueError("trace exceeds row/case limit")
    after = path.stat()
    if identity != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
        raise ValueError("trace changed while reading; compare a retained terminal artifact")
    if not rows:
        raise ValueError("empty trace")
    return cases, {"path": str(path), "sha256": digest.hexdigest(), "bytes": consumed, "rows": rows}


def compare(left: Path, right: Path, *, position_tolerance_m=1e-6, action_width=14):
    if not number(position_tolerance_m) or position_tolerance_m < 0:
        raise ValueError("position tolerance must be finite and nonnegative")
    if type(action_width) is not int or not 1 <= action_width <= 128:
        raise ValueError("action width must be an integer from 1 to 128")
    a_cases, a_source = load_trace(left, action_width)
    b_cases, b_source = load_trace(right, action_width)
    reports = []
    for case in sorted(a_cases.keys() | b_cases.keys()):
        aa, bb = a_cases.get(case, []), b_cases.get(case, [])
        a_by_time, b_by_time = {r["time_s"]: r for r in aa}, {r["time_s"]: r for r in bb}
        shared = sorted(a_by_time.keys() & b_by_time.keys())
        mismatched_times = sorted(a_by_time.keys() ^ b_by_time.keys())
        fields = list(VECTOR_FIELDS) + list(EVENT_FIELDS)
        coverage = {f: {"left": sum(f in r and r[f] is not None for r in aa),
                        "right": sum(f in r and r[f] is not None for r in bb)} for f in fields}
        first, counts, maxima, points = {}, {f: 0 for f in fields}, {}, []
        action_a, action_b = hashlib.sha256(), hashlib.sha256()
        for t in shared:
            a, b = a_by_time[t], b_by_time[t]
            delta = {}
            for field in fields:
                va, vb = a.get(field), b.get(field)
                if va is None or vb is None:
                    continue
                if field in VECTOR_FIELDS:
                    magnitude = max(abs(x - y) for x, y in zip(va, vb))
                    if not math.isfinite(magnitude):
                        raise ValueError(f"unrepresentable delta for {field} in {case}")
                    maxima[field] = max(maxima.get(field, 0), magnitude)
                    unequal = (magnitude > position_tolerance_m if field == "robot_xyz_m"
                               else exact_vector(va) != exact_vector(vb))
                    delta[field] = magnitude
                    if field == "action_rad":
                        action_a.update(struct.pack("!d", t) + exact_vector(va))
                        action_b.update(struct.pack("!d", t) + exact_vector(vb))
                else:
                    unequal = sorted(va) != sorted(vb) if field == "contacts" else va != vb
                if unequal:
                    counts[field] += 1
                    first.setdefault(field, {"time_s": t, "left_line": a["_line"], "right_line": b["_line"],
                                             "left": va, "right": vb})
            points.append({"time_s": t, "position_error_m": delta.get("robot_xyz_m"),
                           "action_error_rad": delta.get("action_rad"),
                           "left_xyz_m": a.get("robot_xyz_m"), "right_xyz_m": b.get("robot_xyz_m"),
                           "left_distance_m": a.get("distance_m"), "right_distance_m": b.get("distance_m")})
        aligned = bool(aa and bb) and not mismatched_times
        actions_complete = aligned and coverage["action_rad"]["left"] == len(aa) and coverage["action_rad"]["right"] == len(bb)
        commands_complete = aligned and coverage["command"]["left"] == len(aa) and coverage["command"]["right"] == len(bb)
        fixed_actions = actions_complete and counts["action_rad"] == 0
        kind = ("incomplete_or_misaligned" if not aligned else "action_telemetry_missing" if not actions_complete
                else "fixed_recorded_actions" if fixed_actions else "different_recorded_actions")
        reports.append({"case_id": case, "comparison_kind": kind, "left_rows": len(aa), "right_rows": len(bb),
                        "aligned_rows": len(shared), "unmatched_time_count": len(mismatched_times),
                        "first_unmatched_time_s": mismatched_times[0] if mismatched_times else None,
                        "coverage": coverage, "first_differences": first, "different_rows": counts,
                        "max_abs_component_error": maxima,
                        "recorded_action_values_equal": fixed_actions if actions_complete else None,
                        "recorded_command_values_equal": counts["command"] == 0 if commands_complete else None,
                        "aligned_action_value_sha256": {"left": action_a.hexdigest(), "right": action_b.hexdigest()} if actions_complete else None,
                        "physics_causality": "not_established", "points": points})
    return {"schema_version": "microduck.ops.trace-comparison.v1", "proof_class": "offline_trace_diagnostic",
            "sources": [a_source, b_source], "action_width": action_width,
            "position_tolerance_m": position_tolerance_m, "cases": reports,
            "behavior_acceptance": "not_evaluated", "hardware_authority": False,
            "boundary": "Recorded JSON values only; original tensor bytes/dtype are unavailable. Exact action values are a prerequisite, not proof of physics isolation. Reset, model, observation, actuator and applied-force provenance require separate inspection. Missing contact telemetry stays unknown. Position tolerance is diagnostic, never a behavior acceptance threshold."}
