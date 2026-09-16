"""Import-safe sampled material validation, independent of model compilation.

``validate_meshes`` accepts a mapping from mesh names to ``source_stl``,
``parts_npz`` and ``complete_json`` paths. ``expected_source_sha256`` may also
bind each original STL to a caller's frozen protocol. Archives retain V58's
v000/f000 convention and completion metadata must bind both source and archive.

Cavity witnesses are supplied in the original STL's local frame. Each witness
has an ``id`` and exactly two ``sides``; each side contains ``mesh``,
``local_point_m``, ``source_inside_three_rays`` (three booleans) and
``source_distance_m``. Transform/provenance verification belongs to the caller.
Every side outside the original CAD by more than 0.25 mm must remain outside
its corresponding proxy, even when the other side is already empty.

This module imports no simulator, generates no meshes, writes no files, and
never admits a model. The fixed sampling is a diagnostic, not a global bound.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np
import trimesh
from scipy.spatial import ConvexHull


TOLERANCE_M = 0.00025
SAMPLE_COUNT = 4096
INSIDE_EPSILON_M = 1e-9


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_digest(value: Any) -> str:
    return _digest(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())


def _sample(values: np.ndarray) -> np.ndarray:
    """Preserve V58's evenly spaced, unique indices including endpoints."""
    return values[np.unique(np.linspace(0, len(values) - 1, min(SAMPLE_COUNT, len(values)), dtype=int))]


def union_inside(points: np.ndarray, hulls: Sequence[ConvexHull]) -> np.ndarray:
    """Use V58's convex half-space union and 1 nm numerical boundary epsilon."""
    inside = np.zeros(len(points), dtype=bool)
    for hull in hulls:
        for start in range(0, len(points), 512):
            chunk = points[start : start + 512]
            inside[start : start + len(chunk)] |= np.all(
                chunk @ hull.equations[:, :3].T + hull.equations[:, 3] <= INSIDE_EPSILON_M,
                axis=1,
            )
    return inside


def _source_mesh(raw: bytes) -> trimesh.Trimesh:
    """Read binary STL with V58's exact canonical vertex ordering."""
    if len(raw) < 84:
        raise ValueError("source STL has no complete binary header")
    count = int.from_bytes(raw[80:84], "little")
    if not count or len(raw) != 84 + 50 * count:
        raise ValueError("source must be a nonempty, exact-length binary STL")
    dtype = np.dtype([("normal", "<f4", (3,)), ("vertices", "<f4", (3, 3)), ("attr", "<u2")])
    vertices, inverse = np.unique(
        np.frombuffer(raw, dtype=dtype, offset=84)["vertices"].reshape(-1, 3).astype(float),
        axis=0,
        return_inverse=True,
    )
    return _checked_mesh(vertices, inverse.reshape(-1, 3))


def _checked_mesh(vertices: np.ndarray, faces: np.ndarray) -> trimesh.Trimesh:
    if vertices.ndim != 2 or vertices.shape[1:] != (3,) or len(vertices) < 4:
        raise ValueError("mesh vertices must have shape (N>=4, 3)")
    if vertices.dtype.kind not in "fiu" or not np.isfinite(vertices).all():
        raise ValueError("mesh vertices must be finite real numbers")
    if faces.ndim != 2 or faces.shape[1:] != (3,) or len(faces) < 4:
        raise ValueError("mesh faces must have shape (N>=4, 3)")
    if faces.dtype.kind not in "iu" or faces.min() < 0 or faces.max() >= len(vertices):
        raise ValueError("mesh faces must be in-range integer vertex indices")
    mesh = trimesh.Trimesh(vertices, faces, process=False)
    if np.any(mesh.area_faces <= 0):
        raise ValueError("mesh contains a zero-area triangle")
    return mesh


def _read_inputs(spec: Mapping[str, Any], record: dict[str, Any]) -> dict[str, bytes]:
    raw = {}
    for key in ("source_stl", "parts_npz", "complete_json"):
        try:
            path = Path(spec[key])
            record["inputs"][key] = {"path": str(path.resolve()), "sha256": None}
            raw[key] = path.read_bytes()
            record["inputs"][key]["sha256"] = _digest(raw[key])
        except (KeyError, TypeError, ValueError, OSError) as exc:
            record["errors"].append({"stage": key, "type": type(exc).__name__, "message": str(exc)})
    return raw


def _validate_one(
    name: str, spec: Mapping[str, Any], max_parts: int,
) -> tuple[dict[str, Any], list[ConvexHull] | None]:
    record: dict[str, Any] = {"status": "input_error", "passed": False, "inputs": {}, "failures": [], "errors": []}
    stage = "input"
    hulls = None
    try:
        raw = _read_inputs(spec, record)
        if record["errors"]:
            return record, None
        stage = "metadata"
        metadata = json.loads(raw["complete_json"])
        if metadata.get("mesh") != name:
            raise ValueError("completion mesh name does not match supplied name")
        if metadata.get("source_sha256") != record["inputs"]["source_stl"]["sha256"]:
            raise ValueError("completion source hash does not match original STL")
        expected = spec.get("expected_source_sha256")
        if expected is not None and expected != record["inputs"]["source_stl"]["sha256"]:
            raise ValueError("original STL hash does not match caller's frozen hash")
        if metadata.get("parts_sha256") != record["inputs"]["parts_npz"]["sha256"]:
            raise ValueError("completion archive hash does not match parts.npz")
        count = metadata.get("parts")
        if type(count) is not int or not 1 <= count <= max_parts:
            raise ValueError("part count is missing, invalid or over the fixed budget")
        record["parts"] = count
        stage = "source_geometry"
        source = _source_mesh(raw["source_stl"])
        record["source_watertight"] = bool(source.is_watertight)
        record["source_winding_consistent"] = bool(source.is_winding_consistent)
        if not source.is_watertight or not source.is_winding_consistent:
            raise ValueError("source must be watertight with consistent winding for occupancy checks")
        stage = "proxy_geometry"
        # Read exactly the bytes whose digest was checked, avoiding a path reread.
        import io

        parts = []
        with np.load(io.BytesIO(raw["parts_npz"]), allow_pickle=False) as arrays:
            expected_keys = {f"{prefix}{i:03}" for i in range(count) for prefix in ("v", "f")}
            if set(arrays.files) != expected_keys:
                raise ValueError("archive keys do not exactly match the declared part count")
            for i in range(count):
                parts.append(_checked_mesh(arrays[f"v{i:03}"], arrays[f"f{i:03}"]))
        hulls = [ConvexHull(part.vertices) for part in parts]
        record.update({
            "all_parts_watertight": all(bool(part.is_watertight) for part in parts),
            "all_parts_convex": all(bool(part.is_convex) for part in parts),
            "vertices": sum(len(part.vertices) for part in parts),
            "faces": sum(len(part.faces) for part in parts),
            "part_geometry": [{
                "part": i, "watertight": bool(part.is_watertight), "convex": bool(part.is_convex),
                "triangle_signed_volume_m3": float(part.volume),
                "convex_hull_volume_m3": float(hull.volume),
                "minimum_centered_singular_value_m": float(np.linalg.svd(
                    part.vertices - part.vertices.mean(0), compute_uv=False)[-1]),
            } for i, (part, hull) in enumerate(zip(parts, hulls))],
        })
        stage = "material_sampling"
        source_points = np.vstack([_sample(source.vertices), _sample(source.triangles_center)])
        missing = ~union_inside(source_points, hulls)
        missing_distance = np.zeros(len(source_points))
        if missing.any():
            distances = np.full(int(missing.sum()), np.inf)
            for part in parts:
                distances = np.minimum(distances, trimesh.proximity.closest_point(part, source_points[missing])[1])
            missing_distance[missing] = distances
        proxy_points = np.vstack([
            np.vstack([part.vertices for part in parts]),
            _sample(np.vstack([part.triangles_center for part in parts])),
        ])
        inside = source.contains(proxy_points)
        excess_distance = np.zeros(len(proxy_points))
        for start in range(0, len(proxy_points), 512):
            ids = np.flatnonzero(~inside[start : start + 512]) + start
            if len(ids):
                excess_distance[ids] = trimesh.proximity.closest_point(source, proxy_points[ids])[1]
        if not np.isfinite(missing_distance).all() or not np.isfinite(excess_distance).all():
            raise ValueError("material distance calculation produced nonfinite values")
        record.update({
            "status": "verified_sampled_geometry",
            "source_samples": len(source_points), "proxy_samples": len(proxy_points),
            "source_samples_outside_union": int(missing.sum()),
            "max_sampled_missing_material_m": float(missing_distance.max()),
            "max_sampled_excess_material_m": float(excess_distance.max()),
            "sampled_tolerance_m": TOLERANCE_M,
        })
        for key, condition in (
            ("non_watertight_proxy", record["all_parts_watertight"]),
            ("non_convex_proxy", record["all_parts_convex"]),
            ("sampled_missing_material", missing_distance.max() <= TOLERANCE_M),
            ("sampled_excess_material", excess_distance.max() <= TOLERANCE_M),
        ):
            if not condition:
                record["failures"].append(key)
        record["passed"] = not record["failures"]
    except Exception as exc:
        # Isolate malformed geometry or dependency failures to this named mesh.
        # KeyboardInterrupt/SystemExit remain visible to the owning coordinator.
        record["status"] = "validation_error"
        record["errors"].append({"stage": stage, "type": type(exc).__name__, "message": str(exc)})
    return record, hulls


def _cavity_checks(
    witnesses: Sequence[Mapping[str, Any]], hulls_by_name: Mapping[str, Sequence[ConvexHull]],
) -> list[dict[str, Any]]:
    results = []
    for index, witness in enumerate(witnesses):
        result: dict[str, Any] = {"id": witness.get("id", str(index)), "sides": [], "passed": False, "errors": []}
        try:
            if len(witness["sides"]) != 2:
                raise ValueError("a cavity witness must contain exactly two sides")
            for side in witness["sides"]:
                mesh_name = side["mesh"]
                point = np.asarray(side["local_point_m"], dtype=float)
                rays = side["source_inside_three_rays"]
                distance = side["source_distance_m"]
                if point.shape != (3,) or not np.isfinite(point).all():
                    raise ValueError("cavity point must contain three finite local coordinates")
                if len(rays) != 3 or any(type(value) is not bool for value in rays):
                    raise ValueError("cavity source occupancy must contain exactly three booleans")
                if type(distance) not in (float, int) or not np.isfinite(distance) or distance < 0:
                    raise ValueError("cavity source distance must be finite and nonnegative")
                must_empty = not any(rays) and distance > TOLERANCE_M
                inside = None if mesh_name not in hulls_by_name else bool(
                    union_inside(point.reshape(1, 3), hulls_by_name[mesh_name])[0])
                result["sides"].append({
                    "mesh": mesh_name, "local_point_m": point.tolist(),
                    "source_inside_three_rays": list(rays), "source_distance_m": float(distance),
                    "must_remain_empty": must_empty, "inside_convex_part_union": inside,
                    "cavity_preserved": inside is not None and (not must_empty or not inside),
                })
            available = all(side["inside_convex_part_union"] is not None for side in result["sides"])
            result["source_cavities_preserved"] = available and all(side["cavity_preserved"] for side in result["sides"])
            result["no_false_pair_contact_at_witness"] = available and not all(
                side["inside_convex_part_union"] for side in result["sides"])
            result["passed"] = result["source_cavities_preserved"] and result["no_false_pair_contact_at_witness"]
        except Exception as exc:
            result["errors"].append({"type": type(exc).__name__, "message": str(exc)})
        results.append(result)
    return results


def validate_meshes(
    mesh_inputs: Mapping[str, Mapping[str, Any]], *, max_parts: int = 64,
    cavity_witnesses: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Validate requested materials independently; missing/failed meshes reject.

    ``max_parts`` must come from the caller's frozen experiment budget. All
    tolerance, sampling and occupancy rules remain fixed at their V58 values.
    An omitted/empty cavity bank is explicitly not evaluated. Even all sampled
    checks passing cannot establish model, global clearance or physical validity.
    """
    if type(max_parts) is not int or max_parts < 1:
        raise ValueError("max_parts must be a positive frozen integer budget")
    report: dict[str, Any] = {
        "scope": "sampled source/proxy material diagnostic; not a global error bound or model admission",
        "physics_steps": 0, "model_compiled": False, "model_admitted": False, "physical_acceptance": False,
        "settings": {
            "sampled_tolerance_m": TOLERANCE_M, "source_vertex_samples": SAMPLE_COUNT,
            "source_face_centroid_samples": SAMPLE_COUNT, "proxy_vertices": "all",
            "proxy_face_centroid_samples": SAMPLE_COUNT, "maximum_parts_per_mesh": max_parts,
            "selection": "evenly spaced unique deterministic indices including endpoints",
            "convex_half_space_epsilon_m": INSIDE_EPSILON_M,
        },
        "validator_sha256": _digest(Path(__file__).read_bytes()),
        "versions": {package: importlib.metadata.version(package) for package in ("numpy", "scipy", "trimesh")},
        "meshes": {},
    }
    hulls_by_name = {}
    for name in sorted(mesh_inputs):
        record, hulls = _validate_one(name, mesh_inputs[name], max_parts)
        report["meshes"][name] = record
        if hulls is not None:
            hulls_by_name[name] = hulls
    report["sampled_material_gates_passed"] = bool(mesh_inputs) and all(record["passed"] for record in report["meshes"].values())
    witnesses = list(cavity_witnesses or [])
    report["cavity_witness_input_sha256"] = _json_digest(witnesses)
    report["cavity_checks"] = _cavity_checks(witnesses, hulls_by_name)
    report["cavity_bank_evaluated"] = bool(witnesses)
    report["cavity_gates_passed"] = bool(witnesses) and all(check["passed"] for check in report["cavity_checks"])
    report["all_requested_checks_passed"] = report["sampled_material_gates_passed"] and (
        report["cavity_gates_passed"] if cavity_witnesses is not None else True)
    report["result_sha256"] = _json_digest(report)
    return report
