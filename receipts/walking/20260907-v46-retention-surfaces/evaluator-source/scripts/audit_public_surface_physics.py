"""Passive soft-contact checks; no policy or material-calibration fit."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import mujoco
import numpy as np
from experiments.walking.public_surface_v25 import PROFILES, ground_solref


def trial(profile,mass,dt):
    ref=' '.join(map(str,ground_solref(profile)))
    xml=f'''<mujoco><option timestep="{dt}"/><worldbody>
    <geom name="floor" type="plane" size="2 2 .1" solref="{ref}" friction="{profile['friction']} .005 .0001"/>
    <body pos="0 0 .025"><freejoint/><geom name="foot" type="box" size=".02 .01 .005" mass="{mass}" solref=".02 1" friction=".1 .005 .0001"/></body>
    </worldbody></mujoco>'''
    m=mujoco.MjModel.from_xml_string(xml);d=mujoco.MjData(m)
    samples=[]
    for i in range(round(2/dt)):
        mujoco.mj_step(m,d)
        if not np.isfinite(d.qpos).all(): raise ValueError('nonfinite passive dynamics')
        for c in d.contact:
            np.testing.assert_allclose(c.solref,[profile['timeconst_s'],1.],atol=1e-12)
            np.testing.assert_allclose(c.friction[0],profile['friction'],atol=1e-12)
        if i*dt>1.5: samples.append(.005-d.qpos[2])
    sink=float(np.mean(samples))
    return {'profile':profile['id'],'mass_kg':mass,'timestep_s':dt,'mean_indentation_m':sink,
            'settled_speed_m_s':float(np.linalg.norm(d.qvel[:3])),
            'passed':bool(0<sink<.007 and np.std(samples)<1e-5 and np.linalg.norm(d.qvel[:3])<1e-4)}


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    rows=[trial(pr,m,dt) for pr in PROFILES for m in [.2,.4,.737243] for dt in [.005,.0025]]
    gaps=[abs(rows[i]['mean_indentation_m']-rows[i+1]['mean_indentation_m']) for i in range(0,len(rows),2)]
    result={'schema':'microduck.public-contact-passive-audit/v1','trials':rows,
            'max_timestep_indentation_difference_m':max(gaps),'passed':all(r['passed'] for r in rows) and max(gaps)<.0001,
            'measurement_calibrated':False,'boundary':'Numerical settling, actual contact parameters and timestep sensitivity only. Primitive rigid probe, not measured carpet or actual-foot calibration; no hysteresis identification.'}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    serialized=json.dumps(result,indent=2)+'\n'
    with a.output.open('x') as f:f.write(serialized)
    print(json.dumps(result),flush=True)

if __name__=='__main__':main()
