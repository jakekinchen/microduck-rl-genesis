"""Geometric activation check of the discovered floor-mask mismatch."""
import argparse
import json
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    p=argparse.ArgumentParser();p.add_argument("--probe",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False)
    import mujoco
    import numpy as np
    from scripts.evaluate_laser import digest
    m=mujoco.MjModel.from_xml_path(str(ROOT/"microduck/assets/microduck/scene_walk.xml"));d=mujoco.MjData(m)
    geoms=[i for i in range(m.ngeom) if m.geom_contype[i]==2 and m.geom_conaffinity[i]==2]
    vertices={}
    for g in geoms:
        mesh=m.geom_dataid[g]
        if mesh<0:raise ValueError("mesh geometry required")
        vertices[g]=m.mesh_vert[m.mesh_vertadr[mesh]:m.mesh_vertadr[mesh]+m.mesh_vertnum[mesh]].copy()
    cases=[]
    for path in sorted(a.probe.glob("*.jsonl")):
        minima={g:float("inf") for g in geoms};penetrations=0;count=0
        for line in path.read_text().splitlines():
            row=json.loads(line);d.qpos[:]=row["qpos"];mujoco.mj_kinematics(m,d)
            low=[]
            for g in geoms:
                height=float((vertices[g]@d.geom_xmat[g].reshape(3,3).T+d.geom_xpos[g])[:,2].min())
                minima[g]=min(minima[g],height);low.append(height)
            penetrations+=min(low)<0;count+=1
        cases.append({"case":path.stem,"source_sha256":digest(path),"rows":count,
            "extra_floor_geometry_penetration_rows":penetrations,
            "minimum_geometry_height_m":{m.body(m.geom_bodyid[g]).name:value for g,value in minima.items()}})
    report={"schema":"microduck.floor-mask-activation-diagnostic/v1","cases":cases,
        "genesis_floor_masks":[65535,65535],"native_floor_masks":[1,1],
        "extra_genesis_floor_colliders":[m.body(m.geom_bodyid[g]).name for g in geoms],
        "boundary":"Copied-state geometry activation check. Does not execute a policy or assert identical-action dynamics, causal attribution, or physical calibration."}
    (a.output/"audit.json").write_text(json.dumps(report,indent=2)+"\n")
    shutil.copy2(Path(__file__),a.output/"source.py")
    (a.output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.relative_to(a.output)}\n" for f in sorted(a.output.rglob("*")) if f.is_file()))
    print(json.dumps(report),flush=True)


if __name__=="__main__":main()
