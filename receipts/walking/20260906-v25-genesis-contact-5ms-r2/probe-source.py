"""Independent primitive contact response check against retained MuJoCo trials."""
import argparse
import json
from pathlib import Path
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiments.walking.public_surface_v25 import PROFILES,SOLIMP,training_panels


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    p.add_argument('--dt',type=float,choices=(.005,.0025),required=True);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False)
    import numpy as np
    import torch
    import genesis as gs
    from scripts.evaluate_laser import digest
    gs.init(backend=gs.cpu,logging_level='warning',seed=26092588)
    scene=gs.Scene(sim_options=gs.options.SimOptions(dt=a.dt,substeps=1),
        rigid_options=gs.options.RigidOptions(constraint_timeconst=.02),show_viewer=False)
    ground=scene.add_entity(gs.morphs.MJCF(file=str(training_panels(a.output/'panels.xml'))))
    feet=[scene.add_entity(gs.morphs.Box(size=(.04,.02,.01),pos=(0,16*i,.025)),
        material=gs.materials.Rigid(rho=.4/(.04*.02*.01))) for i in range(4)]
    scene.build()
    solver=scene.rigid_solver
    for foot in feet:
        solver.set_geoms_friction(.1,geoms_idx=[g.idx for g in foot.geoms])
        solver.set_sol_params([.02,1.]+SOLIMP,geoms_idx=[g.idx for g in foot.geoms])
    samples=[]
    for i in range(round(2/a.dt)):
        scene.step()
        if i*a.dt>1.5:samples.append([.005-float(foot.get_pos()[2]) for foot in feet])
    measured=np.array(samples).mean(0)
    native=json.loads((ROOT/'receipts/walking/20260906-v25-public-surface-physics-r2/passive.json').read_text())
    rows=[]
    for i,profile in enumerate(PROFILES):
        ref=next(r for r in native['trials'] if r['profile']==profile['id'] and r['mass_kg']==.4 and r['timestep_s']==a.dt)
        gap=abs(measured[i]-ref['mean_indentation_m'])
        limit=max(.0001,.2*ref['mean_indentation_m'])
        rows.append({'profile':profile['id'],'genesis_indentation_m':float(measured[i]),
            'mujoco_indentation_m':ref['mean_indentation_m'],'gap_m':float(gap),
            'preregistered_limit_m':limit,'passed':bool(gap<=limit),
            'genesis_settled_std_m':float(np.std(samples,axis=0)[i])})
    result={'schema':'microduck.public-surface-engine-response/v1','timestep_s':a.dt,
        'rows':rows,'passed':all(r['passed'] for r in rows),'source_sha256':digest(__file__),
        'physical_calibration':False,'boundary':'0.4-kg rigid cuboid passive response only; no real carpet force curve, dynamic hysteresis or policy equivalence.'}
    (a.output/'probe.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)

if __name__=='__main__':main()
