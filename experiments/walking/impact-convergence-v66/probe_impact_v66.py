"""V66 version of the frozen V65 guided drop, with explicit free-fall phase."""
from pathlib import Path
import argparse
import gzip
import json
import signal
import time
import sys
import mujoco
import numpy as np
sys.path.insert(1,str(Path(__file__).resolve().parents[1]/'feedback-contact-v65'))
from impact_v66 import start_state, impact_audit
from bench_v65 import ROOT, load, save, sha, mesh_arrays, bench_metrics


def run(bank,case,out):
    assert mujoco.__version__==bank['mujoco_version']
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
    static=bank['models'][case['model']]['static']
    assert mass==static['mass_kg']
    for key in ('body_inertia','body_ipos','body_iquat','body_pos'):
        np.testing.assert_array_equal(getattr(model,key)[1],static[key])
    for key,value in static['options'].items():assert getattr(model.opt,key)==value,key
    for key,value in static['contact_parameters'].items():
        np.testing.assert_array_equal(getattr(model,'geom_'+key),value)
    np.testing.assert_array_equal(model.geom_contype,[1,1])
    np.testing.assert_array_equal(model.geom_conaffinity,[1,1])
    assert not model.dof_damping.any() and not model.dof_frictionloss.any() and not model.dof_armature.any()
    q0,v0=start_state(case['start_advance_s'])
    if case['start_advance_s']:
        data.qpos[0]=q0;data.qvel[0]=v0;mujoco.mj_forward(model,data)
    np.savez_compressed(out/'initial-state.npz',qpos=data.qpos.copy(),qvel=data.qvel.copy(),
        qfrc_constraint=data.qfrc_constraint.copy(),qfrc_bias=data.qfrc_bias.copy(),
        qacc_warmstart=data.qacc_warmstart.copy())
    save(out/'configuration.json',{'case':case,'mass_kg':mass,'clearance_m':clearance,
        'nq':model.nq,'nv':model.nv,'nu':model.nu,'xml':str(source),'xml_sha256':sha(source),
        'gravity':model.opt.gravity.tolist(),'dt_s':dt,'initial_qpos':data.qpos.tolist(),
        'initial_qvel':data.qvel.tolist(),'model_static_check':bank['models'][case['model']]['static'],
        'start_advance_s':case['start_advance_s'],'model_static_arrays_verified':True,
        'applied_initial_clearance_m':clearance+q0,
        'boundary':'Guided CAD ankle load with analytic phase advance; no robot gait or physical calibration.'})
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
    result['bench_diagnostic_passed']=result['passed']
    result['analytic_audit']=impact_audit(rows,clearance,case['start_advance_s'],dt)
    result['passed']=result['passed'] and result['analytic_audit']['passed']
    result['failures']+=['analytic:'+reason for reason in result['analytic_audit']['failures']]
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
