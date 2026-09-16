#!/usr/bin/env python3
"""Compile and inspect pinned source models; never run physics or a policy.

Executes only selected, inspected definitions from the saved mjlab 1.3.0 and
MicroDuck sources. This avoids installing/initializing the GPU training stack.
The result is a source-editor/CPU model audit, not a full mjlab runtime test.
"""
from __future__ import annotations

import ast
import argparse
from collections import Counter
from dataclasses import dataclass
from abc import ABC, abstractmethod
import hashlib
import json
from pathlib import Path
import sys
import types
from typing import Literal

import mujoco
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SRC = HERE / "sources"
UPSTREAM = SRC / "src/mjlab_microduck"


def selected(path, names, namespace):
    tree = ast.parse(path.read_text())
    body = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names:
            body.append(node)
        elif isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id in names for target in node.targets
        ):
            body.append(node)
    exec(compile(ast.Module(body=body, type_ignores=[]), str(path), "exec"), namespace)


def upstream_spec():
    # Direct source definitions, not a handwritten approximation of matching.
    module = types.ModuleType("audit_upstream_configuration")
    module.__dict__.update(mujoco=mujoco, dataclass=dataclass, ABC=ABC,
                           abstractmethod=abstractmethod, Literal=Literal)
    sys.modules[module.__name__] = module
    helpers = types.ModuleType("mjlab.utils.string")
    exec(compile((SRC / "mjlab/utils/string.py").read_text(), "mjlab/utils/string.py", "exec"), helpers.__dict__)
    sys.modules[helpers.__name__] = helpers
    spec_helpers = types.ModuleType("mjlab.utils.spec")
    spec_helpers.__dict__["mujoco"] = mujoco
    selected(SRC / "mjlab/utils/spec.py", {"disable_collision"}, spec_helpers.__dict__)
    sys.modules[spec_helpers.__name__] = spec_helpers
    selected(SRC / "mjlab/utils/spec_config.py",
             {"_GEOM_ATTR_DEFAULTS", "SpecCfg", "CollisionCfg"}, module.__dict__)
    selected(UPSTREAM / "robot/microduck_constants.py",
             {"SERVO_MESH_NAME", "SERVO_GEOM_SUFFIX", "name_servo_collision_geoms", "FULL_COLLISION"},
             module.__dict__)
    xml = str(UPSTREAM / "robot/microduck/robot_allcollisions.xml")
    raw = mujoco.MjSpec.from_file(xml).compile()
    spec = mujoco.MjSpec.from_file(xml)
    module.name_servo_collision_geoms(spec)
    names_before = [geom.name for geom in spec.geoms]
    masks_before = [(geom.contype, geom.conaffinity) for geom in spec.geoms]
    module.FULL_COLLISION.edit_spec(spec)
    mutations = []
    for index, geom in enumerate(spec.geoms):
        if masks_before[index] != (geom.contype, geom.conaffinity):
            mutations.append({"geom": index, "name": names_before[index],
                              "before": masks_before[index], "after": [geom.contype, geom.conaffinity]})
    return raw, spec.compile(), {"unnamed_geoms": names_before.count(""), "mask_mutations": mutations,
                                 "disable_other_geoms": module.FULL_COLLISION.disable_other_geoms}


def geoms(model):
    rows = []
    for i in range(model.ngeom):
        mesh = int(model.geom_dataid[i])
        if model.geom_type[i] != mujoco.mjtGeom.mjGEOM_MESH:
            mesh = -1
        body = int(model.geom_bodyid[i])
        rows.append({"id": i, "name": model.geom(i).name,
                     "body_id": body, "body": model.body(body).name,
                     "mesh": model.mesh(mesh).name if mesh >= 0 else None,
                     "contype": int(model.geom_contype[i]), "conaffinity": int(model.geom_conaffinity[i]),
                     "condim": int(model.geom_condim[i]), "priority": int(model.geom_priority[i]),
                     "friction": model.geom_friction[i].tolist(),
                     "active": bool(model.geom_contype[i] or model.geom_conaffinity[i])})
    return rows


def eligible_pair(model, a, b):
    """Static broad-phase eligibility, not observed collision or force.

    Applies masks, same-weld, parent-weld filters and explicit body exclusions.
    These pinned models have zero explicit contact pairs; fail if that changes.
    Spatial separation and mesh convexity are deliberately outside this test.
    """
    assert model.npair == 0
    if not ((model.geom_contype[a] & model.geom_conaffinity[b]) or
            (model.geom_contype[b] & model.geom_conaffinity[a])):
        return False
    ba, bb = int(model.geom_bodyid[a]), int(model.geom_bodyid[b])
    wa, wb = int(model.body_weldid[ba]), int(model.body_weldid[bb])
    if wa == wb:
        return False
    if not (model.opt.disableflags & int(mujoco.mjtDisableBit.mjDSBL_FILTERPARENT)):
        pa = int(model.body_weldid[model.body_parentid[wa]])
        pb = int(model.body_weldid[model.body_parentid[wb]])
        if wa and wb and (pa == wb or pb == wa):
            return False
    lo, hi = sorted((ba, bb))
    if (lo << 16) + hi in model.exclude_signature:
        return False
    return True


def inventory(model):
    rows = geoms(model)
    active = [r for r in rows if r["active"] and r["body_id"]]
    pairs = []
    for a in active:
        for b in active:
            if b["id"] > a["id"] and eligible_pair(model, a["id"], b["id"]):
                pairs.append([a["id"], b["id"]])
    support = [r["id"] for r in active if r["mesh"] == "power_support"]
    legs = [r["id"] for r in active if r["mesh"] == "leg"]
    floor = {r["mesh"] for r in active if (r["contype"] & 1) or (r["conaffinity"] & 1)}
    return {"nq": model.nq, "nv": model.nv, "nu": model.nu,
            "actuator_names": [model.actuator(i).name for i in range(model.nu)],
            "joint_names": [model.joint(i).name for i in range(model.njnt)],
            "body_mass_total_kg": float(model.body_mass.sum()),
            "active_robot_geom_count": len(active),
            "active_mesh_count": len({r["mesh"] for r in active}),
            "active_condim_counts": dict(Counter(r["condim"] for r in active)),
            "floor_mask_eligible_meshes": sorted(floor),
            "eligible_internal_geom_pairs": pairs,
            "support_leg_pairs": [{"support": a, "leg": b, "eligible": eligible_pair(model, a, b)}
                                  for a in support for b in legs],
            "exclude_signatures": [int(x) for x in model.exclude_signature],
            "filter_parent_enabled": not bool(model.opt.disableflags & int(mujoco.mjtDisableBit.mjDSBL_FILTERPARENT)),
            "geoms": rows}


def mesh_comparison():
    root = UPSTREAM / "robot/microduck/assets"
    out = []
    for path in sorted(root.glob("*.stl")):
        local = ROOT / "microduck/assets/microduck/assets" / path.name
        raw, old = path.read_bytes(), local.read_bytes()
        # Binary STL: byte equality and vertex equality are different claims.
        def vertices(data):
            count = int.from_bytes(data[80:84], "little")
            assert len(data) == 84 + count * 50
            dtype = np.dtype([("normal", "<f4", (3,)), ("vertices", "<f4", (3, 3)), ("attr", "<u2")])
            return np.frombuffer(data, dtype=dtype, offset=84)["vertices"]
        v1, v2 = vertices(raw), vertices(old)
        points1 = np.unique(v1.reshape(-1, 3), axis=0)
        points2 = np.unique(v2.reshape(-1, 3), axis=0)
        out.append({"file": path.name, "upstream_sha256": hashlib.sha256(raw).hexdigest(),
                    "local_sha256": hashlib.sha256(old).hexdigest(), "bytes_equal": raw == old,
                    "triangle_vertices_equal": bool(v1.shape == v2.shape and np.array_equal(v1, v2)),
                    "unique_vertices_equal": bool(points1.shape == points2.shape and np.array_equal(points1, points2)),
                    "upstream_unique_vertices": len(points1), "local_unique_vertices": len(points2),
                    "upstream_triangles": len(v1), "local_triangles": len(v2),
                    "upstream_bounds_m": [v1.min(axis=(0,1)).tolist(), v1.max(axis=(0,1)).tolist()],
                    "local_bounds_m": [v2.min(axis=(0,1)).tolist(), v2.max(axis=(0,1)).tolist()]})
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE / "audit.json")
    args = parser.parse_args()
    manifest = json.loads((HERE / "sources.lock.json").read_text())
    for rel, record in manifest["files"].items():
        actual = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        if actual != record["sha256"]:
            raise ValueError(f"source drift: {rel}")
    raw, edited, editor = upstream_spec()
    local = mujoco.MjModel.from_xml_path(str(ROOT / "experiments/walking/models/contact-v11/scene.xml"))
    fields = ["body_mass", "body_inertia", "body_ipos", "body_iquat", "body_pos", "body_quat",
              "jnt_range", "jnt_axis", "jnt_pos", "dof_damping", "dof_armature", "dof_frictionloss"]
    arrays = {name: {"equal": bool(getattr(local,name).shape == getattr(edited,name).shape and
                                    np.array_equal(getattr(local,name),getattr(edited,name))),
                     "local_shape": list(getattr(local,name).shape),
                     "upstream_shape": list(getattr(edited,name).shape),
                     "max_abs_difference": float(np.max(np.abs(getattr(local,name)-getattr(edited,name))))}
              for name in fields}
    # q and -q are the same orientation. Raw component deltas can mislead.
    for field in ("body_quat", "body_iquat"):
        old, new = getattr(local, field), getattr(edited, field)
        signs = np.where(np.sum(old * new, axis=1) < 0, -1, 1)
        arrays[field]["max_abs_difference_after_quaternion_sign_alignment"] = float(
            np.max(np.abs(old - new * signs[:, None])))
    report = {"schema": "microduck-upstream-static-audit-v56", "physics_steps": 0,
              "upstream_revision": manifest["upstream_revision"], "mujoco_version": mujoco.__version__,
              "source_hashes_verified": len(manifest["files"]), "full_upstream_runtime_executed": False,
              "policy_compatibility_proven": False, "physical_calibration_proven": False,
              "decision": "retain_local_v11_do_not_replace_with_upstream_without_versioned_dynamic_conformance",
              "editor": editor, "local_v11": inventory(local), "upstream_raw": inventory(raw),
              "upstream_after_pinned_collision_editor": inventory(edited),
              "physical_arrays": arrays, "meshes": mesh_comparison()}
    report["same_actuator_order"] = report["local_v11"]["actuator_names"] == report["upstream_after_pinned_collision_editor"]["actuator_names"]
    report["same_joint_order"] = report["local_v11"]["joint_names"] == report["upstream_after_pinned_collision_editor"]["joint_names"]
    report["bam_parameters_byte_equal"] = (SRC / "bam/params/xl330/m6.json").read_bytes() == (ROOT / "microduck/assets/xl330_m6.json").read_bytes()
    report["local_compiled_xml_solver_defaults"] = {
        name: int(getattr(local.opt, name)) for name in ("integrator", "solver", "iterations", "ls_iterations")}
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"decision": report["decision"], "physics_steps": 0,
                      "source_hashes_verified": len(manifest["files"]),
                      "local_active_geoms": report["local_v11"]["active_robot_geom_count"],
                      "upstream_active_geoms": report["upstream_after_pinned_collision_editor"]["active_robot_geom_count"],
                      "upstream_condim_counts": report["upstream_after_pinned_collision_editor"]["active_condim_counts"],
                      "physical_arrays_equal": {k:v["equal"] for k,v in arrays.items()},
                      "equal_mesh_vertices": sum(r["triangle_vertices_equal"] for r in report["meshes"])}, indent=2))


if __name__ == "__main__":
    main()
