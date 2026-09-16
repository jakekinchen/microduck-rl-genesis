"""Retain the visual-camera misalignment and isolated, physics-neutral fix."""
import argparse
import json
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import imageio.v2 as imageio
import mujoco
import numpy as np
from evaluator.core import EvaluatorCore
from experiments.laser.camera_alignment import align_head_camera
from scripts.evaluate_laser import digest
from microduck.laser_task import detect_red_spot


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--bam-repo",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    core=EvaluatorCore(ROOT/"tests/fixtures/evaluator/zero-policy.onnx",a.bam_repo,"microduck.walking.v1")
    core.reset([0,0,.125],[1,0,0,0])
    m,d=core.model,core.data
    m.vis.quality.offsamples=1
    renderer=mujoco.Renderer(m,height=480,width=640)
    # A level HOME camera has a close-ground blind zone. Keep this 85 cm probe
    # inside the unchanged FOV; the retained 65 cm probe is clipped at the edge.
    target=np.array([.85,0,.006])
    records=[]
    try:
        for label in ("legacy","site-aligned-v2"):
            if label!="legacy":
                correction=align_head_camera(m)
                mujoco.mj_forward(m,d)
            camera=m.camera("head_camera").id
            rotation=d.cam_xmat[camera].reshape(3,3)
            renderer.update_scene(d,camera="head_camera")
            geom=renderer.scene.geoms[renderer.scene.ngeom]
            mujoco.mjv_initGeom(geom,mujoco.mjtGeom.mjGEOM_SPHERE,np.array([.012]*3),target,np.eye(3).reshape(-1),np.array([1.,0.,0.,1.]))
            geom.emission=1;renderer.scene.ngeom+=1
            frame=renderer.render()
            imageio.imwrite(a.output/f"{label}.png",frame)
            records.append({"variant":label,"optical_forward_world":(-rotation[:,2]).tolist(),
                            "image_up_world":rotation[:,1].tolist(),
                            "target_camera_m":(rotation.T@(target-d.cam_xpos[camera])).tolist(),
                            "red_pixel":detect_red_spot(frame,max_pixels=300)})
        result={"schema":"microduck.camera-alignment-audit/v2", "records":records,"correction":correction,
                "target_world_m":target.tolist(), "field_of_view_deg":float(m.cam_fovy[0]),
                "physical_site_forward_world":d.site("head_camera").xmat.reshape(3,3)[:,0].tolist(),
                "mouth_world_m":d.site("mouth_tip").xpos.tolist(),
                "head_com_world_m":d.xipos[m.body("jaw_soft").id].tolist(),
                "model_root_sha256":core.model_root_digest,"policy_executed":False,
                "boundary":"Render camera convention corrected only; no physical calibration or camera-driven policy."}
        if records[0]["red_pixel"] is not None or records[1]["red_pixel"] is None:
            raise ValueError("camera visibility regression")
        (a.output/"camera-audit.json").write_text(json.dumps(result,indent=2)+"\n")
        for source in ("scripts/audit_camera_alignment.py","experiments/laser/camera_alignment.py"):
            dest=a.output/"source"/source;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/source,dest)
    finally:renderer.close()
    (a.output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.relative_to(a.output)}\n" for f in sorted(a.output.rglob("*")) if f.is_file() and f.name!="SHA256SUMS"))
    print(json.dumps(result))


if __name__=="__main__":main()
