"""Look for raw CAD triangle witnesses at recorded battery/leg hull contacts."""
import argparse
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def intersection_witness(vertices_a, faces_a, vertices_b, faces_b):
    import numpy as np
    import igl
    a, b = vertices_a[faces_a], vertices_b[faces_b]
    blo, bhi = b.min(1), b.max(1)
    broad_lo, broad_hi = blo.min(0), bhi.max(0)
    for i, triangle in enumerate(a):
        lo, hi = triangle.min(0), triangle.max(0)
        if (lo > broad_hi).any() or (hi < broad_lo).any():
            continue
        for j in np.flatnonzero(((blo <= hi).all(1) & (bhi >= lo).all(1))):
            points = [np.ascontiguousarray(v[None], dtype=np.float64) for v in (*triangle, *b[j])]
            hit, coplanar, source, target = igl.tri_tri_intersection_test_3d(*points)
            if hit and not coplanar:
                return {"triangle_a": int(i), "triangle_b": int(j),
                        "intersection_segment_m": [source.tolist(), target.tolist()]}
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--receipt", type=Path, required=True)
    p.add_argument("--contacts", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    import numpy as np
    import mujoco
    import trimesh
    from scripts.evaluate_walking_heading import verify_input_manifest
    from scripts.evaluate_laser import digest
    from scripts.audit_walking_self_contact import geom_label
    verify_input_manifest(a.receipt)
    report = json.loads((a.contacts/"audit.json").read_text())
    if report["input_manifest_sha256"] != digest(a.receipt/"SHA256SUMS"):
        raise ValueError("different input receipt")
    for line in (a.contacts/"SHA256SUMS").read_text().splitlines():
        sha, name = line.split("  ", 1)
        path = (a.contacts/name).resolve()
        if not path.is_relative_to(a.contacts.resolve()) or digest(path) != sha:
            raise ValueError("contact manifest mismatch")
    a.output.mkdir(parents=True, exist_ok=False)
    trace = {(r["case_id"], r["time_s"]): r for r in
             map(json.loads, (a.receipt/"trajectory.jsonl").read_text().splitlines())}
    candidates = {}
    for line in (a.contacts/"contacts.jsonl").read_text().splitlines():
        r = json.loads(line)
        for c in r["contacts"]["full"]:
            key = (r["case_id"], c["a"]["id"], c["b"]["id"])
            old = candidates.get(key)
            if old is None or c["penetration_m"] > old[1]["penetration_m"]:
                candidates[key] = (r["time_s"], c)
    model = mujoco.MjModel.from_xml_path(str(ROOT/"microduck/assets/microduck/scene.xml"))
    data = mujoco.MjData(model)
    results = []
    for (case, ga, gb), (time_s, contact) in sorted(candidates.items()):
        data.qpos[:] = trace[case, time_s]["qpos"]
        mujoco.mj_kinematics(model, data)
        meshes = []
        metadata = []
        for g in (ga, gb):
            mesh = int(model.geom_dataid[g])
            v = model.mesh_vert[model.mesh_vertadr[mesh]:model.mesh_vertadr[mesh]+model.mesh_vertnum[mesh]].astype(float)
            f = model.mesh_face[model.mesh_faceadr[mesh]:model.mesh_faceadr[mesh]+model.mesh_facenum[mesh]].astype(np.int64)
            v = v@data.geom_xmat[g].reshape(3, 3).T + data.geom_xpos[g]
            tm = trimesh.Trimesh(v, f, process=False)
            meshes.append((v, f))
            metadata.append({**geom_label(model, g), "watertight": bool(tm.is_watertight),
                             "winding_consistent": bool(tm.is_winding_consistent), "raw_triangles": len(f)})
        witness = intersection_witness(*meshes[0], *meshes[1])
        result = {"case_id": case, "time_s": time_s, "hull_penetration_m": contact["penetration_m"],
                  "raw_meshes": metadata, "noncoplanar_triangle_intersection": witness is not None,
                  "witness": witness, "qpos": data.qpos.tolist()}
        results.append(result)
        print(json.dumps(result), flush=True)
    output = {"schema": "microduck.raw-cad-intersection-witness/v1", "cases": results,
              "input_manifest_sha256": digest(a.receipt/"SHA256SUMS"),
              "contact_manifest_sha256": digest(a.contacts/"SHA256SUMS"),
              "acceptance_eligible": False,
              "boundary": "Raw compiled CAD triangle intersection witnesses at maximum recorded convex-hull penetration per case/pair, not all-frame geometry acceptance, contact forces, or calibrated hardware truth. A positive noncoplanar witness is not merely convex-hull filling a cavity."}
    (a.output/"audit.json").write_text(json.dumps(output, indent=2)+"\n")
    for name in ("scripts/audit_walking_cad_intersections.py", "scripts/audit_walking_self_contact.py",
                 "microduck/assets/microduck/scene.xml", "microduck/assets/microduck/robot_allcollisions.xml"):
        dest = a.output/"source"/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT/name, dest)
    assets = ROOT/"microduck/assets/microduck/assets"
    (a.output/"mesh-input-sha256.json").write_text(json.dumps({str(f.relative_to(ROOT)): digest(f) for f in sorted(assets.iterdir()) if f.is_file()}, indent=2)+"\n")
    (a.output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.relative_to(a.output)}\n" for f in sorted(a.output.rglob("*")) if f.is_file()))


if __name__ == "__main__":
    main()
