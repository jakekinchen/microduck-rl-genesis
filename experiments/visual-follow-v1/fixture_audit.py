"""Static V3 scene/optics checks from retained V2 poses; never step physics."""
import argparse
import gzip
import json
from pathlib import Path
import math
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from run import PROTOCOL, ROOT, materialize_scene, sha
import mujoco
import numpy as np
from experiments.laser.camera_alignment import align_head_camera


def audit(output):
    output.mkdir(parents=True, exist_ok=False)
    scene = materialize_scene(output/"v3-model", PROTOCOL["cases"][0])
    prior = ROOT/"receipts/visual-follow/20260915-v2-smoke"
    before = mujoco.MjModel.from_xml_path(str(prior/"model/scene.xml"))
    after = mujoco.MjModel.from_xml_path(str(scene))
    compared, changed = [], []
    for name in dir(before):
        a, b = getattr(before, name), getattr(after, name)
        if isinstance(a, np.ndarray):
            if a.dtype != b.dtype or a.shape != b.shape or a.tobytes() != b.tobytes():
                changed.append(name)
            compared.append(name)
    if changed != ["mat_reflectance"]:
        raise ValueError("unexpected compiled-model change: "+str(changed))
    gid = after.geom("floor").id
    mid = int(after.geom_matid[gid])
    if before.mat_reflectance[mid] != .08 or after.mat_reflectance[mid] != 0.:
        raise ValueError("floor reflectance change not effective")
    align_head_camera(after)
    data = mujoco.MjData(after)
    rows = [json.loads(line) for line in gzip.open(prior/"trajectory.jsonl.gz", "rt")]
    focal = 240/(2*math.tan(math.radians(45)/2))
    visibility = {"v2_direct": 0, "v3_direct": 0}
    selected = []
    for row in rows[49:]:
        data.qpos[:] = row["qpos"]
        mujoco.mj_kinematics(after, data)
        mujoco.mj_camlight(after, data)
        cid = after.camera("head_camera").id
        eye, rotation = data.cam_xpos[cid], data.cam_xmat[cid].reshape(3, 3)
        record = {"time_s": row["time_s"], "projections": {}}
        for name, height in (("v2_direct", .20), ("v2_reflection", -.20), ("v3_direct", .04)):
            target = np.asarray(row["target_xyz_m"]).copy()
            target[2] = height
            local = rotation.T@(target-eye)
            depth = -local[2]
            u, v = 160+focal*local[0]/depth, 120-focal*local[1]/depth
            radius = focal*.035/depth
            inside = bool(radius < u < 320-radius and radius < v < 240-radius and depth > 0)
            if name in visibility:
                visibility[name] += int(inside)
            record["projections"][name] = {"uv": [float(u), float(v)], "whole_marker_inside": inside}
        if row["time_s"] in (1., 2., 3., 5.):
            selected.append(record)
    result = {"schema": "microduck.visual-follow-v3-fixture-audit/v1", "source_receipt": str(prior),
              "source_motion_sha256": sha(prior/"motion.npz"), "source_trajectory_sha256": sha(prior/"trajectory.jsonl.gz"),
              "protocol_sha256": sha(HERE/"protocol.json"), "audit_source_sha256": sha(Path(__file__)),
              "compiled_array_count": len(compared), "compared_arrays": compared, "changed_arrays": changed,
              "excluded_from_physical_identity": ["mat_reflectance"], "all_other_compiled_arrays_byte_equal": True,
              "old_floor_reflectance": float(before.mat_reflectance[mid]), "new_floor_reflectance": float(after.mat_reflectance[mid]),
              "camera_revision": "head-camera-site-aligned.v2", "retained_pose_samples": len(rows[49:]),
              "whole_marker_in_frame": visibility, "selected_projections": selected,
              "boundary": "Static optics at exposed prior candidate poses; not new closed-loop evidence. No integration or model/control changes except stated visual reflectance and marker height."}
    (output/"audit.json").write_text(json.dumps(result, indent=2)+"\n")
    (output/"SHA256SUMS").write_text("".join(f"{sha(p)}  {p.relative_to(output)}\n" for p in sorted(output.rglob("*")) if p.is_file()))
    print(json.dumps({key: result[key] for key in ("compiled_array_count", "changed_arrays", "retained_pose_samples", "whole_marker_in_frame")}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    audit(parser.parse_args().output)
