#!/usr/bin/env python3
"""Frozen sparse copied-pose collision diagnostic. No dynamics or policy calls."""
from pathlib import Path
from collections import Counter
import gzip
import hashlib
import importlib.util
import json
import math
import os
import xml.etree.ElementTree as ET

import mujoco
import numpy as np
from scipy.spatial import ConvexHull, cKDTree
import scipy

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
V56 = HERE.parent / "upstream-audit-v56"
UP = V56 / "sources/src/mjlab_microduck/robot/microduck"
spec = importlib.util.spec_from_file_location("v56_static_audit", V56 / "audit.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def materialize(name, preserve_exclude):
    tree = ET.parse(UP / "robot_allcollisions.xml")
    root = tree.getroot()
    root.find("compiler").set("meshdir", os.path.relpath(UP / "assets", HERE / name))
    defaults = root.find("./default/default[@class='self_collision_only']/geom")
    assert defaults.attrib["contype"] == defaults.attrib["conaffinity"] == "2"
    defaults.set("contype", "1")
    defaults.set("conaffinity", "1")
    for bi, body in enumerate(root.findall(".//body")):
        for gi, geom in enumerate(body.findall("geom")):
            original_class = geom.get("class")
            geom.set("name", f"{body.get('name')}_{gi}_{geom.get('mesh','primitive')}_{original_class}")
            if original_class in ("collision", "self_collision_only"):
                geom.set("contype", "1")
                geom.set("conaffinity", "1")
                geom.set("condim", "3")
    exclusions = root.findall("./contact/exclude")
    assert [e.attrib for e in exclusions] == [{"body1": "neck_pitch", "body2": "jaw_soft"}]
    if not preserve_exclude:
        for element in exclusions:
            root.find("contact").remove(element)
    ET.indent(root)
    output = HERE / name / "robot.xml"
    output.parent.mkdir(exist_ok=True)
    value = ET.tostring(root, encoding="unicode") + "\n"
    if output.exists() and output.read_text() != value:
        raise ValueError(f"materialized diagnostic model drift: {output}")
    output.write_text(value)
    return mujoco.MjModel.from_xml_path(str(output))


def mesh_diagnostics(files):
    def points(path):
        raw = path.read_bytes()
        n = int.from_bytes(raw[80:84], "little")
        assert len(raw) == 84 + n * 50
        dtype = np.dtype([("normal", "<f4", (3,)), ("vertices", "<f4", (3, 3)), ("attr", "<u2")])
        return np.unique(np.frombuffer(raw, dtype=dtype, offset=84)["vertices"].reshape(-1, 3), axis=0).astype(float)
    k = np.arange(256)
    z = 1 - 2 * (k + .5) / 256
    phi = k * math.pi * (3 - math.sqrt(5))
    directions = np.vstack([np.column_stack([np.sqrt(1-z*z)*np.cos(phi), np.sqrt(1-z*z)*np.sin(phi), z]), np.eye(3), -np.eye(3)])
    results = []
    for name in files:
        a = points(ROOT / "microduck/assets/microduck/assets" / name)
        b = points(UP / "assets" / name)
        ha, hb = ConvexHull(a), ConvexHull(b)
        pa, pb = a[ha.vertices], b[hb.vertices]
        hausdorff = lambda x,y: float(max(cKDTree(x).query(y)[0].max(), cKDTree(y).query(x)[0].max()))
        supports = np.abs(np.max(pa @ directions.T, axis=0) - np.max(pb @ directions.T, axis=0))
        results.append({"mesh": name, "local_vertices": len(a), "upstream_vertices": len(b),
                        "local_hull_vertices": len(pa), "upstream_hull_vertices": len(pb),
                        "vertex_set_hausdorff_m": hausdorff(a,b),
                        "hull_vertex_set_hausdorff_m": hausdorff(pa,pb),
                        "max_sampled_hull_support_difference_m": float(supports.max()),
                        "support_directions": len(directions),
                        "local_hull_volume_m3": ha.volume, "upstream_hull_volume_m3": hb.volume,
                        "max_bounds_difference_m": float(np.max(np.abs(np.r_[a.min(0)-b.min(0),a.max(0)-b.max(0)]))),
                        "boundary": "Nearest-vertex Hausdorff is not triangle-surface Hausdorff; finite-direction support is not a global bound."})
    return results


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    upstream_lock = json.loads((V56 / "sources.lock.json").read_text())
    for path, record in upstream_lock["files"].items():
        if digest(ROOT / path) != record["sha256"]:
            raise ValueError(f"upstream/local input drift: {path}")
    for row in protocol["sources"]:
        if digest(ROOT / row["path"]) != row["sha256"]:
            raise ValueError(f"recording drift: {row['path']}")
    local = mujoco.MjModel.from_xml_path(str(ROOT / "experiments/walking/models/contact-v11/scene.xml"))
    models = {"retained_v11": local,
              "full_cad_original_jaw_exclusion": materialize("original-jaw-exclusion", True),
              "full_cad_jaw_contact_enabled": materialize("jaw-contact-enabled", False)}
    for model in models.values():
        assert model.nq == 21 and [model.joint(i).name for i in range(model.njnt)] == [local.joint(i).name for i in range(local.njnt)]
    geoms = {key:audit.geoms(model) for key,model in models.items()}
    old_coverage = {(g["body"],g["mesh"]) for g in geoms["retained_v11"] if g["active"] and g["body_id"]}
    matrices = {}
    for key,model in models.items():
        active = [g for g in geoms[key] if g["active"] and g["body_id"]]
        matrices[key] = {"geoms": geoms[key], "all_internal_pairs": [
            {"geom_ids":[a["id"],b["id"]], "eligible":audit.eligible_pair(model,a["id"],b["id"])}
            for a in active for b in active if a["id"] < b["id"]]}
    (HERE / "pair-matrices.json").write_text(json.dumps(matrices,indent=2)+'\n')
    poses = []
    for source in protocol["sources"]:
        selected = set(source["zero_based_indices"])
        with gzip.open(ROOT / source["path"],"rt") as stream:
            count = 0
            for i,line in enumerate(stream):
                count += 1
                if i in selected:
                    row = json.loads(line)
                    poses.append({"source":source["path"],"row_index":i,"time_s":row["time_s"],"qpos":row["qpos"]})
        assert count == source["record_count"]
    home = json.loads((ROOT / "microduck_contract/interface/observation-v1.json").read_text())["home_joint_position_rad"]
    for case in protocol["home_cases"]:
        yaw=case["yaw_rad"]
        poses.append({"source": "explicit_HOME", "case":case, "qpos":[0,0,case["root_z_m"],math.cos(yaw/2),0,0,math.sin(yaw/2),*home]})
    data = {key:mujoco.MjData(model) for key,model in models.items()}
    results = []
    for pose in poses:
        item = {k:v for k,v in pose.items() if k != "qpos"}
        item["qpos_sha256"] = hashlib.sha256(np.asarray(pose["qpos"],dtype='<f8').tobytes()).hexdigest()
        item["variants"] = {}
        for key,model in models.items():
            d = data[key]
            d.qpos[:] = pose["qpos"]
            mujoco.mj_kinematics(model,d)
            mujoco.mj_collision(model,d)
            contacts = []
            for c in d.contact:
                a,b = geoms[key][int(c.geom1)],geoms[key][int(c.geom2)]
                if not a["body_id"] or not b["body_id"]:
                    continue
                depth = -float(c.dist)
                assert math.isfinite(depth)
                contacts.append({"geom_ids":[a['id'],b['id']],"bodies":[a['body'],b['body']],
                                 "meshes":[a['mesh'],b['mesh']],"penetration_m":depth,
                                 "outside_v11_collider_coverage":any((g['body'],g['mesh']) not in old_coverage for g in [a,b])})
            item['variants'][key] = {"maximum_penetration_m":max([0.]+[c['penetration_m'] for c in contacts]),
                                    "contacts":contacts, "over_1mm":any(c['penetration_m']>protocol['threshold_penetration_m'] for c in contacts)}
        results.append(item)
    (HERE/'pose-results.json').write_text(json.dumps(results,indent=2)+'\n')
    meshes = mesh_diagnostics(protocol['mesh_diagnostics']['meshes'])
    summary = {"protocol_sha256":digest(HERE/'protocol.json'), "physics_steps":0,
               "mujoco_version":mujoco.__version__,"scipy_version":scipy.__version__,
               "sampled_poses":len(poses),"recorded_controls":sum(s['record_count'] for s in protocol['sources']),
               "stored_pose_samples":sum(len(s['zero_based_indices']) for s in protocol['sources']),
               "upstream_sources_verified":len(upstream_lock['files']),"models":{},"mesh_diagnostics":meshes,
               "physical_acceptance":False,"dynamic_loads_measured":False,
               "original_behavior_scores_modified":False}
    for key in models:
        rows=[r['variants'][key] for r in results]
        pairmax={}
        for r in rows:
            for c in r['contacts']:
                pair=' / '.join(f'{b}:{m}' for b,m in zip(c['bodies'],c['meshes']))
                pairmax[pair]=max(pairmax.get(pair,0.),c['penetration_m'])
        summary['models'][key]={"active_colliders":sum(g['active'] and bool(g['body_id']) for g in geoms[key]),
                                "sampled_poses_over_1mm":sum(r['over_1mm'] for r in rows),
                                "maximum_penetration_m":max(r['maximum_penetration_m'] for r in rows),
                                "poses_with_uncovered_part_over_1mm":sum(any(c['outside_v11_collider_coverage'] and c['penetration_m']>.001 for c in r['contacts']) for r in rows),
                                "worst_pairs":sorted(pairmax.items(),key=lambda p:-p[1])[:12]}
    (HERE/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    inputs=[HERE/'protocol.json',HERE/'diagnose.py',V56/'audit.py',V56/'sources.lock.json',ROOT/'microduck_contract/interface/observation-v1.json']
    generated=list(HERE.glob('*/robot.xml'))+[HERE/'pair-matrices.json',HERE/'pose-results.json',HERE/'summary.json']
    receipt={'inputs':{str(p.relative_to(ROOT)):digest(p) for p in inputs},'outputs':{str(p.relative_to(ROOT)):digest(p) for p in generated},'physics_steps':0}
    (HERE/'manifest.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='mesh_diagnostics'},indent=2))


if __name__=='__main__':
    main()
