"""One frozen guided-drop case, recording actual solver forces each step."""
from pathlib import Path
import argparse
import gzip
import json
import signal
import time
import mujoco
import numpy as np
from bench_v65 import ROOT, load, save, sha, mesh_arrays, bench_metrics


def run(bank,case,out):
    dt=case['dt_s'];source=ROOT/bank['models'][case['model']]['xml']
    model=mujoco.MjModel.from_xml_path(str(source));model.opt.timestep=dt
    data=mujoco.MjData(model);mujoco.mj_forward(model,data)
    assert (model.nq,model.nv,model.nu,model.ngeom)==(1,1,0,2)
    assert not data.qpos.any() and not data.qvel.any() and data.time==0
    floor=model.geom('floor').id;sole=model.geom('sole').id
    verts,_=mesh_arrays(model,sole)
    clearance=float((verts@data.geom_xmat[sole].reshape(3,3).T+data.geom_xpos[sole])[:,2].min())
    assert abs(clearance-.005)<1e-7
    mass=float(model.body_mass[1]);assert np.array_equal(model.opt.gravity,[0,0,-9.81])
    save(out/'configuration.json',{'case':case,'mass_kg':mass,'clearance_m':clearance,
        'nq':model.nq,'nv':model.nv,'nu':model.nu,'xml':str(source),'xml_sha256':sha(source),
        'gravity':model.opt.gravity.tolist(),'dt_s':dt,'initial_qpos':data.qpos.tolist(),
        'initial_qvel':data.qvel.tolist(),'model_static_check':bank['models'][case['model']]['static'],
        'boundary':'Vertical guided CAD ankle-load numerical diagnostic; not robot gait or physical calibration.'})
    rows=[];stop=None;started=time.monotonic()
    with gzip.open(out/'physics.jsonl.gz','wt') as stream:
        for i in range(round(case['duration_s']/dt)):
            before=float(data.qpos[0]);vb=float(data.qvel[0]);tb=float(data.time)
            mujoco.mj_step(model,data)
            assert np.isfinite(np.r_[data.qpos,data.qvel,data.qacc,data.qfrc_constraint]).all()
            contacts=[];force_z=normal=penetration=0.
            for j,c in enumerate(data.contact):
                assert set((c.geom1,c.geom2))=={floor,sole}
                force=np.zeros(6);mujoco.mj_contactForce(model,data,j,force)
                assert np.isfinite(force).all()
                world=c.frame.reshape(3,3).T@force[:3]
                fz=float(world[2])*(1 if c.geom2==sole else -1)
                force_z+=fz;normal+=max(0.,float(force[0]));penetration=max(penetration,max(0.,-float(c.dist)))
                contacts.append({'geom_ids':[int(c.geom1),int(c.geom2)],'distance_m':float(c.dist),
                    'force_contact_frame':force.tolist(),'frame':c.frame.tolist(),'force_z_on_sole_n':fz,
                    'efc_address':int(c.efc_address),'solref':c.solref.tolist(),'solimp':c.solimp.tolist(),
                    'friction':c.friction.tolist(),'dim':int(c.dim),'includemargin':float(c.includemargin)})
            assert abs(force_z-data.qfrc_constraint[0])<1e-9
            row={'step':i,'interval_start_s':tb,'time_s':float(data.time),'position_before_m':before,
                'velocity_before_m_s':vb,'position_m':float(data.qpos[0]),'velocity_m_s':float(data.qvel[0]),
                'contact_force_z_n':force_z,'normal_load_n':normal,'penetration_m':penetration,
                'qfrc_constraint_n':float(data.qfrc_constraint[0]),'qfrc_bias_n':float(data.qfrc_bias[0]),
                'qfrc_passive_n':float(data.qfrc_passive[0]),'qfrc_actuator_n':float(data.qfrc_actuator[0]),
                'warnings':[j for j,n in enumerate(data.warning.number) if n],'contacts':contacts}
            rows.append(row);stream.write(json.dumps(row,allow_nan=False)+'\n')
            if row['warnings'] or penetration>.01 or abs(row['velocity_m_s'])>5.:
                stop='numerical_or_geometry_hard_stop';break
    np.savez_compressed(out/'dynamics.npz',**{k:np.array([r[k] for r in rows]) for k in (
        'position_m','velocity_m_s','contact_force_z_n','normal_load_n','penetration_m')})
    result=bench_metrics(rows,mass,case['duration_s'],dt)
    result.update(case=case,stop_reason=stop,elapsed_seconds=time.monotonic()-started)
    save(out/'result.json',result)
    print(json.dumps(result),flush=True)


def main():
    signal.pthread_sigmask(signal.SIG_UNBLOCK,{signal.SIGINT,signal.SIGTERM})
    p=argparse.ArgumentParser();p.add_argument('bank',type=Path);p.add_argument('case');a=p.parse_args()
    b=load(a.bank)
    for name,digest in b['input_sha256'].items():assert sha(ROOT/name)==digest,name
    case=next(c for c in b['cases'] if c['id']==a.case)
    out=ROOT/b['output_root']/case['id'];out.mkdir(exist_ok=False)
    try:run(b,case,out)
    except Exception as error:
        save(out/'result.json',{'case':case,'passed':False,'error':repr(error),'physics_evidence_complete':False})
        raise


if __name__=='__main__':main()
