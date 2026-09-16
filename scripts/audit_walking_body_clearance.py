"""Audit non-foot floor clearance using the existing full-collision CAD variant.

This is copied-state kinematics, not a dynamics replay or measured load. It can
reject impossible penetration omitted by the reduced walking model, but cannot
prove contact-free physical operation.
"""
import argparse
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class BodyClearance:
    def __init__(self):
        import mujoco
        import numpy as np
        from scipy.spatial import ConvexHull
        self.mj, self.np = mujoco, np
        self.model = mujoco.MjModel.from_xml_path(str(ROOT/"microduck/assets/microduck/scene.xml"))
        self.data = mujoco.MjData(self.model)
        reduced = mujoco.MjModel.from_xml_path(str(ROOT/"microduck/assets/microduck/scene_walk.xml"))
        for field in ("jnt_qposadr", "jnt_range", "body_mass", "body_inertia", "body_ipos", "body_iquat"):
            if not np.array_equal(getattr(reduced, field), getattr(self.model, field)):
                raise ValueError(f"full-collision model changes {field}")
        if [reduced.joint(j).name for j in range(reduced.njnt)] != [self.model.joint(j).name for j in range(self.model.njnt)]:
            raise ValueError("joint order differs")
        self.geoms = []
        self.vertices = []
        for g in range(self.model.ngeom):
            name = self.model.geom(g).name
            if name == "floor" or name in ("left_foot_collision", "right_foot_collision"):
                continue
            if not ((int(self.model.geom_contype[g]) | int(self.model.geom_conaffinity[g])) & 1):
                continue
            if self.model.geom_type[g] != mujoco.mjtGeom.mjGEOM_MESH:
                raise ValueError("unsupported non-foot collision geometry")
            mesh = self.model.geom_dataid[g]
            start, count = self.model.mesh_vertadr[mesh], self.model.mesh_vertnum[mesh]
            v = self.model.mesh_vert[start:start+count].copy()
            self.geoms.append(g)
            self.vertices.append(v[ConvexHull(v).vertices])
        if not self.geoms:
            raise ValueError("missing full-body floor geometry")

    def sample(self, qpos):
        q = self.np.asarray(qpos, float)
        if q.shape != (21,) or not self.np.isfinite(q).all():
            raise ValueError("invalid copied qpos")
        self.data.qpos[:] = q
        self.mj.mj_kinematics(self.model, self.data)
        return [float((v @ self.data.geom_xmat[g].reshape(3, 3)[2, :]) .min()+self.data.geom_xpos[g, 2]) for g, v in zip(self.geoms, self.vertices)]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--trace", type=Path, nargs="+", required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    from scripts.evaluate_laser import digest
    import numpy as np
    a.output.mkdir(parents=True, exist_ok=False)
    probe = BodyClearance()
    report = {"schema": "microduck.full-body-clearance-diagnostic/v1", "cases": [],
        "boundary": "Static full-collision CAD clearance on copied states, not full-collision dynamics or contact force. Reduced native walk model has only two floor-capable robot geoms, so its non-foot-floor-force rejection alone is vacuous.",
        "physical_transfer_validated": False}
    for path in a.trace:
        rows = [json.loads(s) for s in path.read_text().splitlines()]
        values = np.asarray([probe.sample(r["qpos"]) for r in rows])
        minimum = values.min(0)
        case = {"trace": str(path), "sha256": digest(path), "frames": len(rows),
            "minimum_nonfoot_floor_clearance_m": float(minimum.min()),
            "frames_below_floor_by_1mm": int((values.min(1) < -.001).sum()),
            "geometries": [{"name": probe.model.geom(g).name, "body": probe.model.body(int(probe.model.geom_bodyid[g])).name,
                "minimum_clearance_m": float(minimum[i]), "penetrating_frames": int((values[:, i] < -.001).sum())} for i, g in enumerate(probe.geoms)]}
        report["cases"].append(case)
        print(json.dumps(case), flush=True)
    (a.output/"audit.json").write_text(json.dumps(report, indent=2)+"\n")
    for name in ("scripts/audit_walking_body_clearance.py", "microduck/assets/microduck/scene.xml", "microduck/assets/microduck/scene_walk.xml", "microduck/assets/microduck/robot_walk.xml", "microduck/assets/microduck/robot_allcollisions.xml"):
        dest = a.output/"source"/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT/name, dest)
    # Mesh inputs are pinned by the repository contract; capture their hashes.
    assets = ROOT/"microduck/assets/microduck/assets"
    (a.output/"mesh-input-sha256.json").write_text(json.dumps({str(f.relative_to(ROOT)): digest(f) for f in sorted(assets.iterdir()) if f.is_file()}, indent=2)+"\n")
    (a.output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.relative_to(a.output)}\n" for f in sorted(a.output.rglob("*")) if f.is_file()))


if __name__ == "__main__":
    main()
