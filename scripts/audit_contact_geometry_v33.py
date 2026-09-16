"""Read actual imported collision hull support functions at the same HOME pose."""
import json
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    import genesis as gs
    import torch
    import mujoco
    from microduck.public_surface_env_v25 import PublicSurfaceWalkingEnv
    from experiments.walking.collision_world import CompleteContactWalkingWorld
    out=ROOT/'receipts/walking/20260906-v33-geometry-audit'
    out.mkdir(exist_ok=False)
    gs.init(backend=gs.cpu,logging_level='warning',seed=26090633)
    env=PublicSurfaceWalkingEnv(1,demo=True,model_directory=ROOT/'experiments/walking/models/contact-v11',surface_xml=out/'panels.xml')
    env.reset();env.place([0.,0.,.125])
    world=CompleteContactWalkingWorld(ROOT/'receipts/walking/20260906-v30-flat-regression/policy.onnx',ROOT/'.workspace/bam',model_directory=ROOT/'experiments/walking/models/contact-v11')
    model,data=world.core.model,world.core.data
    directions=np.r_[np.eye(3),-np.eye(3),np.random.default_rng(26090633).normal(size=(2048,3))]
    directions/=np.linalg.norm(directions,axis=1,keepdims=True)
    results=[]
    for g in env.robot.geoms:
        if not g.contype:continue
        stem=Path(g.metadata.get('mesh_path','')).stem
        matches=[i for i in range(model.ngeom) if model.geom_contype[i] and model.geom_bodyid[i]>0
                 and model.mesh(model.geom_dataid[i]).name==stem and model.body(model.geom_bodyid[i]).name==g.link.name]
        if len(matches)!=1:raise ValueError((g.link.name,stem,matches))
        geom=matches[0];mesh=model.geom_dataid[geom]
        vertices=model.mesh_vert[model.mesh_vertadr[mesh]:model.mesh_vertadr[mesh]+model.mesh_vertnum[mesh]]
        native=vertices@data.geom_xmat[geom].reshape(3,3).T+data.geom_xpos[geom]
        actual=g.get_verts()[0].cpu().numpy()
        errors=np.abs((native@directions.T).max(0)-(actual@directions.T).max(0))
        item=dict(body=g.link.name,mesh=stem,native_vertices=len(native),genesis_vertices=len(actual),
                  max_support_difference_m=float(errors.max()),axis_difference_m=errors[:6].tolist())
        results.append(item)
        np.savez_compressed(out/f'geom-{geom}.npz',native=native,genesis=actual,directions=directions)
    (out/'audit.json').write_text(json.dumps(dict(schema='microduck.contact-geometry/v33',results=results,
        boundary='Finite directional support audit of actual colliders at HOME; not physical calibration.'),indent=2)+'\n')
    print(json.dumps(results),flush=True)
    world.close()


if __name__=='__main__':main()
