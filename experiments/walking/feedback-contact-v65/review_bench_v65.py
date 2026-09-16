"""Independent impulse, Euler state, contact and repeat checks for the drop bench."""
from pathlib import Path
import gzip
import hashlib
import json
import math
import numpy as np

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]


def load(p):return json.loads(p.read_text())


def main():
    b=load(BASE/'bench-bank.json'); checks={};repeats={}
    for name,digest in b['input_sha256'].items():
        with (ROOT/name).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest,name
    for c in b['cases']:
        path=ROOT/b['output_root']/c['id'];cfg=load(path/'configuration.json');result=load(path/'result.json')
        assert 'error' not in result and cfg['nu']==0 and cfg['nq']==cfg['nv']==1
        dt=c['dt_s'];mass=cfg['mass_kg'];previous_position=previous_velocity=0.;impulses=[];peaks=[];first=None;tail=[];warnings=[]
        params={}
        with np.load(path/'dynamics.npz') as a,gzip.open(path/'physics.jsonl.gz','rt') as f:
            count=0
            for i,line in enumerate(f):
                r=json.loads(line);count+=1
                assert r['step']==i and abs(r['time_s']-(i+1)*dt)<1e-10 and abs(r['interval_start_s']-i*dt)<1e-10
                assert r['position_before_m']==previous_position and r['velocity_before_m_s']==previous_velocity
                for key in a.files:
                    assert np.isfinite(a[key][i]) and a[key][i]==r[key]
                assert r['qfrc_actuator_n']==0. and r['qfrc_passive_n']==0.
                assert abs(r['qfrc_bias_n']-mass*9.81)<1e-12
                fz=normal=depth=0.
                for contact in r['contacts']:
                    force=np.array(contact['force_contact_frame']);frame=np.array(contact['frame']).reshape(3,3)
                    assert np.isfinite(force).all() and set(contact['geom_ids'])=={0,1}
                    sign=1 if contact['geom_ids'][1]==1 else -1
                    expected=float((frame.T@force[:3])[2])*sign
                    assert expected==contact['force_z_on_sole_n']
                    if force[0]>0:assert contact['efc_address']>=0
                    fz+=expected;normal+=max(0.,float(force[0]));depth=max(depth,max(0.,-contact['distance_m']))
                    param=json.dumps([contact[k] for k in ('solref','solimp','friction','dim','includemargin')])
                    params[param]=params.get(param,0)+1
                assert fz==r['contact_force_z_n'] and depth==r['penetration_m'] and normal==r['normal_load_n']
                assert abs(fz-r['qfrc_constraint_n'])<1e-9
                expected_velocity=previous_velocity+(fz/mass-9.81)*dt
                assert abs(expected_velocity-r['velocity_m_s'])<1e-10
                assert abs(previous_position+r['velocity_m_s']*dt-r['position_m'])<1e-12
                previous_position=r['position_m'];previous_velocity=r['velocity_m_s']
                impulses.append(fz*dt);peaks.append(depth);warnings+=r['warnings']
                if normal>1e-8 and first is None:first=r['interval_start_s']
                if r['time_s']>c['duration_s']-.2+1e-9:tail.append(abs(previous_velocity))
            assert count==result['physics_samples']==len(a['position_m'])
        residual=abs(math.fsum(impulses)-(mass*previous_velocity+mass*9.81*count*dt))
        assert abs(math.fsum(impulses)-result['normal_impulse_ns'])<1e-12
        assert max(peaks)==result['peak_penetration_m'] and first==result['first_loaded_impact_s']
        assert count==round(c['duration_s']/dt) and not warnings and first is not None
        assert len(tail)==round(.2/dt) and max(tail)==result['final_tail_max_speed_m_s']
        assert residual<=1e-8
        assert result['passed']==(max(peaks)<=.003 and max(tail)<=.02)
        checks[c['id']]={'verified':True,'physics_samples':count,'momentum_residual_ns':residual,
                         'diagnostic_passed':result['passed'],'contact_parameter_sets':[{ 'values':json.loads(k),'count':n} for k,n in params.items()]}
        if c['repeat']==1:
            twin=path.parent/(c['id'][:-1]+'2')
            with np.load(path/'dynamics.npz') as x,np.load(twin/'dynamics.npz') as y:
                assert x.files==y.files
                for key in x.files:assert x[key].dtype==y[key].dtype and x[key].shape==y[key].shape and x[key].tobytes()==y[key].tobytes()
            with gzip.open(path/'physics.jsonl.gz','rb') as x,gzip.open(twin/'physics.jsonl.gz','rb') as y:assert x.read()==y.read()
            repeats[c['id'][:-1]]=True
        print(json.dumps({'case':c['id'],'verified':True,'samples':count,'diagnostic_passed':result['passed']}),flush=True)
    report={'verification_passed':True,'cases_verified':len(checks),'checks':checks,'exact_repeats':repeats,
        'physics_samples_verified':sum(c['physics_samples'] for c in checks.values()),
        'walking_accepted':False,'physical_acceptance':False}
    (BASE/'bench-review.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
