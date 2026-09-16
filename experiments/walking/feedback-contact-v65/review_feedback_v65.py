"""Read-only verification of source actions, force sampling, clocks and repeats."""
from pathlib import Path
import argparse
import gzip
import hashlib
import json
import sys
import numpy as np

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
sys.path.insert(0,str(ROOT/'experiments/walking/contact-isolation-v64'))
from review_v64 import verify_case, arrays_equal


def load(path): return json.loads(path.read_text())
def save(path,data): path.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')


def verify_feedback(case, bank):
    path=ROOT/bank['output_root']/case['id']
    with gzip.open(path/'solver-forces.jsonl.gz','rt') as f:
        forces=[json.loads(line) for line in f]
    with gzip.open(path/'bam-inputs.jsonl.gz','rt') as f:
        inputs=[json.loads(line) for line in f]
    with np.load(path/'dynamics.npz') as a, np.load(path/'initial-state.npz') as initial:
        steps=len(a['qpos']); n=round(.005/case['dt_s']); dt=case['dt_s']
        assert len(forces)==steps+1 and len(inputs)==(steps+n-1)//n
        config=load(path/'configuration.json')
        # Joint and DOF indices are frozen by the initial physical-model contract.
        joints=bank['joint_ids']; dofs=bank['dof_indices']
        for i, f in enumerate(forces):
            assert f['step']==i-1
            assert abs(f['solver_time_s']-max(0,i-1)*dt)<1e-8
            assert abs(f['captured_time_s']-i*dt)<1e-8
            assert len(f['efc_id'])==len(f['efc_type'])==len(f['efc_force'])
            for name in ('qfrc_bias','qfrc_constraint','qfrc_actuator','efc_force'):
                assert np.isfinite(f[name]).all()
        for tick, r in enumerate(inputs):
            expected=-1 if tick==0 else (tick*n-1 if case['feedback']=='native' else (tick-1)*n)
            f=forces[expected+1]
            assert r['bam_tick']==tick and r['snapshot_step']==expected
            assert abs(r['time_s']-tick*.005)<1e-8
            assert r['snapshot_solver_time_s']==f['solver_time_s']
            assert r['snapshot_captured_time_s']==f['captured_time_s']
            assert abs(r['force_input_age_s']-(0. if tick==0 else dt if case['feedback']=='native' else .005))<1e-8
            assert r['physical_solver_fields_unchanged'] is True
            assert set(r['fields_read'])=={'qpos','qvel','ctrl','time','qfrc_bias','qfrc_constraint','qfrc_actuator','efc_id','efc_type','efc_force'}
            for name in ('qpos','qvel'):
                np.testing.assert_array_equal(r[name], initial[name] if tick==0 else a[name][tick*n-1])
            for field,key in [('ctrl_nm','ctrl'),('frictionloss_nm','friction'),('damping','damping')]:
                np.testing.assert_array_equal(r[field],a[key][tick*n])
            for field,key in [('bias_nm','qfrc_bias'),('constraint_nm','qfrc_constraint'),('actuator_nm','qfrc_actuator')]:
                np.testing.assert_array_equal(r[field],np.array(f[key])[dofs])
            friction=np.array([sum(value for kind,joint,value in zip(f['efc_type'],f['efc_id'],f['efc_force']) if kind==1 and joint==j) for j in joints])
            np.testing.assert_array_equal(r['subtracted_dof_friction_nm'],friction)
            external=-np.array(f['qfrc_bias'])[dofs]+np.array(f['qfrc_constraint'])[dofs]-friction
            np.testing.assert_array_equal(r['external_nm'],external)
    return {'verified':True,'solver_snapshots':len(forces),'bam_updates':len(inputs),
            'post_bootstrap_age_s':dt if case['feedback']=='native' else .005,
            'physical_solver_fields_preserved':True}


def main():
    p=argparse.ArgumentParser(); p.add_argument('phase',choices=['controls','native','fixed','all']); args=p.parse_args()
    bank=load(BASE/'feedback-bank.json')
    for name,digest in bank['input_sha256'].items():
        with (ROOT/name).open('rb') as f: assert hashlib.file_digest(f,'sha256').hexdigest()==digest,name
    source=np.load(ROOT/bank['actions_file'])
    home=np.array(load(ROOT/'microduck_contract/interface/observation-v1.json')['home_joint_position_rad'])
    cases=[c for c in bank['cases'] if args.phase=='all' or c['phase']==args.phase]
    checks={};exact={};repeats={}
    for c in cases:
        check=verify_case(c,bank,source,home)
        check['feedback']=verify_feedback(c,bank)
        checks[c['id']]=check
        if c['phase'] in ('controls','native'):
            suffix='base' if c['dt_s']==.005 else f"dt{round(c['dt_s']*1e6)}us"
            old=ROOT/bank['v64_root']/'runs'/f"{c['model']}-replay-{suffix}-r{c['repeat']}"
            exact[c['id']]=arrays_equal(ROOT/bank['output_root']/c['id'],old)
        if c['repeat']==1:
            repeats[c['id'][:-1]]=arrays_equal(ROOT/bank['output_root']/c['id'],ROOT/bank['output_root']/(c['id'][:-1]+'2'))
            a=ROOT/bank['output_root']/c['id']; b=ROOT/bank['output_root']/(c['id'][:-1]+'2')
            for fn in ('solver-forces.jsonl.gz','bam-inputs.jsonl.gz'):
                with gzip.open(a/fn,'rb') as x,gzip.open(b/fn,'rb') as y: assert x.read()==y.read(),(c['id'],fn)
        print(json.dumps({'case':c['id'],'samples':check['samples'],'diagnostic_passed':check['diagnostic_passed'],'force_inputs_verified':True}),flush=True)
    report={'verification_passed':True,'cases_verified':len(cases),
        'physics_samples_verified':sum(c['samples'] for c in checks.values()),
        'bam_updates_verified':sum(c['feedback']['bam_updates'] for c in checks.values()),
        'checks':checks,'exact_v64_reproductions':exact,'exact_repeats':repeats,
        'walking_accepted':False,'physical_acceptance':False}
    save(BASE/(args.phase+'-feedback-review.json'),report)


if __name__=='__main__': main()
