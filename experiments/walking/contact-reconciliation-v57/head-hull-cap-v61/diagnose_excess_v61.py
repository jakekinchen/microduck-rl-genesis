"""Posthoc localization of immutable V61 excess samples; no mesh/model changes."""
from pathlib import Path
import hashlib
import importlib.util
import io
import json
import signal
import sys
import time

import numpy as np
import trimesh


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def interrupt(signum, _frame):
    raise InterruptedError(f"localization interrupted by signal {signum}")


def bounds(points):
    return None if not len(points) else [points.min(0).tolist(), points.max(0).tolist()]


def make_plot(report, backgrounds):
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.colors import Normalize
    from matplotlib.cm import ScalarMappable

    figure = Figure(figsize=(12, 12), layout="constrained")
    FigureCanvasAgg(figure)
    axes = figure.subplots(3, 2)
    maximum_mm = max(item["max_sampled_excess_material_m"] for item in report["meshes"].values()) * 1000
    norm = Normalize(0.25, maximum_mm)
    for row, (name, item) in enumerate(report["meshes"].items()):
        witnesses = item["largest_excess_samples"]
        points = np.asarray([w["source_local_point_m"] for w in witnesses]) * 1000
        nearest = np.asarray([w["nearest_original_surface_point_m"] for w in witnesses]) * 1000
        distances = np.asarray([w["distance_m"] for w in witnesses]) * 1000
        background = backgrounds[name] * 1000
        for column, (a, b) in enumerate(((0, 1), (0, 2))):
            axis = axes[row, column]
            axis.scatter(background[:, a], background[:, b], s=1, c="#c1c8cc", rasterized=True)
            for index, (point, close) in enumerate(zip(points, nearest)):
                axis.plot([point[a], close[a]], [point[b], close[b]], color="#2f3943", lw=0.6)
                if index < 3:
                    axis.annotate(str(index + 1), (point[a], point[b]), xytext=(4, 3), textcoords="offset points", fontsize=8)
            axis.scatter(points[:, a], points[:, b], s=30, c=distances, cmap="inferno", norm=norm, edgecolors="black", linewidths=0.35)
            axis.set(title=f"{name} | max {item['max_sampled_excess_material_m'] * 1000:.6f} mm",
                     xlabel=f"source-local {'XYZ'[a]} (mm)", ylabel=f"source-local {'XYZ'[b]} (mm)")
            axis.set_aspect("equal", adjustable="datalim")
            axis.grid(alpha=0.15)
    figure.colorbar(ScalarMappable(norm=norm, cmap="inferno"), ax=axes.ravel().tolist(), label="Distance outside original surface (mm)", shrink=0.55)
    figure.suptitle("V61 posthoc excess-material witnesses\nGrey: deterministic source vertices; markers: largest 20 excess samples; lines: nearest surface", fontsize=13)
    output = HERE / "excess-witnesses.png"
    figure.savefig(output, dpi=170)
    return {"path": str(output.relative_to(ROOT)), "sha256": digest(output),
            "scope": "orthographic source-local point projections; not semantic CAD annotation or rendered contact proof"}


def main():
    signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGINT, signal.SIGTERM})
    signal.signal(signal.SIGINT, interrupt)
    signal.signal(signal.SIGTERM, interrupt)
    plan_path = HERE / "localization-plan.json"
    plan = json.loads(plan_path.read_text())
    report = {
        "scope": "posthoc localization of unchanged V61 sampled excess-material failures; no tuning, global error bound or admission",
        "status": "running", "meshes": {}, "physics_steps": 0, "model_compiled": False,
        "model_admitted": False, "physical_acceptance": False, "decomposition_runs": 0,
        "plan_sha256": digest(plan_path), "script_sha256": digest(__file__),
        "input_sha256": plan["input_sha256"], "sample_order": "all part vertices, then V59's deterministic sampled face centroids",
        "rank_order": "descending excess distance, tie broken by ascending original sample index",
        "mesh_coordinates": "unmodified original STL local frame, metres",
        "sampled_tolerance_m": 0.00025,
    }
    started = time.monotonic()
    output = HERE / "excess-witnesses.json"
    if output.exists():
        raise FileExistsError("refusing to overwrite an existing localization receipt")

    def persist():
        output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")

    def verify_inputs():
        for name, expected in plan["input_sha256"].items():
            if digest(ROOT / name) != expected:
                raise ValueError("frozen localization input changed: " + name)

    try:
        verify_inputs()
        material = json.loads((HERE / "material-result.json").read_text())
        spec = importlib.util.spec_from_file_location("frozen_v59_material", ROOT / plan["material_validator"])
        validator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(validator)
        if validator.TOLERANCE_M != report["sampled_tolerance_m"]:
            raise ValueError("material threshold changed")
        if material["validator_sha256"] != digest(ROOT / plan["material_validator"]):
            raise ValueError("retained material result used another validator")
        backgrounds = {}
        persist()
        for name in plan["meshes"]:
            old = material["meshes"][name]
            if old["failures"] != ["sampled_excess_material"] or old["errors"]:
                raise ValueError("unexpected original failure classification: " + name)
            source_path = Path(old["inputs"]["source_stl"]["path"])
            archive_path = Path(old["inputs"]["parts_npz"]["path"])
            metadata_path = Path(old["inputs"]["complete_json"]["path"])
            for key, path in (("source_stl", source_path), ("parts_npz", archive_path), ("complete_json", metadata_path)):
                if digest(path) != old["inputs"][key]["sha256"]:
                    raise ValueError("retained material input mismatch: " + name + " " + key)
            source = validator._source_mesh(source_path.read_bytes())
            metadata = json.loads(metadata_path.read_text())
            with np.load(io.BytesIO(archive_path.read_bytes()), allow_pickle=False) as arrays:
                parts = [validator._checked_mesh(arrays[f"v{i:03}"], arrays[f"f{i:03}"]) for i in range(metadata["parts"])]
            vertices = np.vstack([part.vertices for part in parts])
            centers = np.vstack([part.triangles_center for part in parts])
            face_indices = validator._sample(np.arange(len(centers)))
            points = np.vstack([vertices, centers[face_indices]])
            vertex_counts = np.asarray([len(part.vertices) for part in parts])
            face_counts = np.asarray([len(part.faces) for part in parts])
            vertex_offsets = np.r_[0, np.cumsum(vertex_counts)]
            face_offsets = np.r_[0, np.cumsum(face_counts)]
            source_inside = source.contains(points)
            distances = np.zeros(len(points))
            nearest = np.full(points.shape, np.nan)
            triangles = np.full(len(points), -1, dtype=int)
            for start in range(0, len(points), 512):
                ids = np.flatnonzero(~source_inside[start:start + 512]) + start
                if len(ids):
                    nearest[ids], distances[ids], triangles[ids] = trimesh.proximity.closest_point(source, points[ids])
            maximum = float(distances.max())
            if maximum != old["max_sampled_excess_material_m"] or len(points) != old["proxy_samples"]:
                raise ValueError("exact retained sample count/maximum mismatch: " + name)
            excess_ids = np.flatnonzero(distances > validator.TOLERANCE_M)
            positive_ids = np.flatnonzero(distances > 0)
            ranked = positive_ids[np.lexsort((positive_ids, -distances[positive_ids]))][:20]
            origin_part = np.empty(len(points), dtype=int)
            origin_part[:len(vertices)] = np.repeat(np.arange(len(parts)), vertex_counts)
            origin_part[len(vertices):] = np.searchsorted(face_offsets[1:], face_indices, side="right")
            witnesses = []
            for rank, index in enumerate(ranked, 1):
                part_index = int(origin_part[index])
                part = parts[part_index]
                is_vertex = index < len(vertices)
                local_index = int(index - vertex_offsets[part_index]) if is_vertex else int(face_indices[index - len(vertices)] - face_offsets[part_index])
                triangle_index = int(triangles[index])
                witnesses.append({
                    "rank": rank, "sample_index": int(index), "sample_kind": "vertex" if is_vertex else "face_centroid",
                    "part_index": part_index, "part_element_index": local_index,
                    "source_local_point_m": points[index].tolist(), "distance_m": float(distances[index]),
                    "over_frozen_tolerance": bool(distances[index] > validator.TOLERANCE_M),
                    "nearest_original_surface_point_m": nearest[index].tolist(),
                    "nearest_original_triangle_index": triangle_index,
                    "nearest_original_triangle_vertices_m": source.triangles[triangle_index].tolist(),
                    "part_signed_volume_m3": float(part.volume), "part_bounds_m": part.bounds.tolist(),
                    "part_extents_m": part.extents.tolist(),
                })
            affected = [{
                "part_index": int(index), "over_tolerance_samples": int(np.sum(origin_part[excess_ids] == index)),
                "max_sampled_excess_material_m": float(distances[origin_part == index].max()),
                "part_signed_volume_m3": float(parts[index].volume), "part_bounds_m": parts[index].bounds.tolist(),
                "part_extents_m": parts[index].extents.tolist(),
            } for index in np.unique(origin_part[excess_ids])]
            record = {
                "parts": len(parts), "proxy_samples": len(points), "outside_source_samples": int(np.sum(~source_inside)),
                "positive_excess_samples": len(positive_ids), "over_tolerance_samples": len(excess_ids),
                "over_tolerance_vertex_samples": int(np.sum(excess_ids < len(vertices))),
                "over_tolerance_face_centroid_samples": int(np.sum(excess_ids >= len(vertices))),
                "max_sampled_excess_material_m": maximum,
                "retained_max_sampled_excess_material_m": old["max_sampled_excess_material_m"],
                "maximum_exactly_reproduced": True, "retained_material_passed": old["passed"],
                "source_bounds_m": source.bounds.tolist(), "all_excess_sample_bounds_m": bounds(points[excess_ids]),
                "top_witness_bounds_m": bounds(points[ranked]), "affected_parts": affected,
                "largest_excess_samples": witnesses,
            }
            report["meshes"][name] = record
            backgrounds[name] = validator._sample(source.vertices)
            persist()
            print(json.dumps({k: record[k] for k in ("parts", "proxy_samples", "over_tolerance_samples", "max_sampled_excess_material_m")}|{"mesh": name}), flush=True)
        verify_inputs()
        report["all_three_maxima_exactly_reproduced"] = len(report["meshes"]) == 3
        report["figure"] = make_plot(report, backgrounds)
        report["status"] = "completed"
    except BaseException as exc:
        report["status"] = "failed"
        report["failure"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        report["elapsed_seconds"] = time.monotonic() - started
        persist()


if __name__ == "__main__":
    main()
