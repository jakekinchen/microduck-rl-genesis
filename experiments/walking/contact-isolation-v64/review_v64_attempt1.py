"""Independent read-only checks of frozen actions, clocks, contacts and controls."""
from pathlib import Path
import argparse
import gzip
import json
import numpy as np

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]


def load(path):return json.loads(path.read_text())
def save(path,data):path.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')


def verify_case(case,bank,source,home):
    path=ROOT/bank['output_root']/case['id'];result=load(path/'result.json')
    assert 'error' not in result,(case['id'],result)
    config=load(path/'configuration.json');names=config['geom_names']
    soles=set(bank['models'][case['model']]['sole_geoms'])
    actions=np.load(path/'requested-actions-float32.npy')
    expected=source if case['mode']=='replay' else np.zeros((250,14),np.float32)
    assert actions.dtype==np.float32 and actions.shape==expected.shape and actions.tobytes()==expected.tobytes()
    dt=case['dt_s'];subdiv=round(.005/dt)
    assert config['timestep_s']==dt and config['bam_update_period_s']==.005
    assert config['command_period_s']==.02 and config['target_delay_s']==.02
    params={};first_shell=None;first_shell_loaded=None;sample_count=0
    max_depth=max_internal=nonsole_max=internal_max=0.
    run=longest=loaded=0;first_fall=None;last_qpos=None;held=None;warnings=[]
    with np.load(path/'dynamics.npz') as a,gzip.open(path/'physics.jsonl.gz','rt') as stream:
        for i,line in enumerate(stream):
            row=json.loads(line);tick=i//subdiv;sample_count+=1
            assert abs(row['time_s']-(i+1)*dt)<1e-8
            assert abs(row['interval_start_s']-i*dt)<1e-8
            assert (row['action_index'],row['substep'],row['integration_substep'],row['bam_tick'])==(tick//4,tick%4,i%subdiv,tick)
            target=home if tick<4 else home+actions[(tick-4)//4].astype(np.float64)
            np.testing.assert_array_equal(row['applied_target_rad'],target)
            for name,field in [('qpos','qpos'),('qvel','qvel'),('ctrl','motor_torque_nm'),('target','applied_target_rad'),('actuator_force','actuator_force_nm'),('friction','frictionloss_nm'),('damping','damping')]:
                np.testing.assert_array_equal(a[name][i],row[field])
            if last_qpos is not None:np.testing.assert_array_equal(last_qpos,row['qpos_before'])
            last_qpos=row['qpos']
            current=[a[n][i].tobytes() for n in ('target','ctrl','friction','damping','actuator_force')]
            if i%subdiv:assert current==held,'BAM output changed inside held update interval'
            held=current
            pairs={};depth=inside=nonsole=0.;sole_load=np.zeros(2)
            for contact in row['contacts']:
                ids=tuple(contact['geom_ids']);labels=tuple(names[g] for g in ids)
                force=np.array(contact['force_contact_frame']);assert np.isfinite(force).all()
                normal=max(0.,float(force[0]));penetration=max(0.,-contact['distance_m'])
                if normal>0:assert contact['efc_address']>=0
                internal='floor' not in labels;assert internal==contact['internal']
                if internal:
                    pair=tuple(sorted(ids));pairs[pair]=pairs.get(pair,0.)+normal;inside=max(inside,penetration)
                else:
                    depth=max(depth,penetration)
                    robot=labels[1] if labels[0]=='floor' else labels[0]
                    if robot not in soles:nonsole+=normal
                    else:sole_load[bank['models'][case['model']]['sole_geoms'].index(robot)]+=normal
                    if robot in ('ankle_left_3_foot_left_collision','ankle_right_7_foot_right_collision'):
                        first_shell=row['time_s'] if first_shell is None else first_shell
                        if normal>.1:first_shell_loaded=row['time_s'] if first_shell_loaded is None else first_shell_loaded
                parameter=(tuple(contact['solref']),tuple(contact['solimp']),tuple(contact['friction']),contact['dim'],contact['includemargin'])
                key=json.dumps(parameter);params[key]=params.get(key,0)+1
            total=sum(pairs.values());largest=max(pairs.values(),default=0.)
            assert row['total_normal_n']==total and row['largest_pair_normal_n']==largest
            assert row['internal_penetration_m']==inside and row['ground_penetration_m']==depth
            assert row['nonsole_ground_load_n']==nonsole
            np.testing.assert_array_equal(row['sole_load_n'],sole_load)
            np.testing.assert_array_equal(a['loads'][i],[total,largest,*sole_load,nonsole])
            flag=total>1.;loaded+=flag;run=run+1 if flag else 0;longest=max(longest,run)
            max_depth=max(max_depth,depth);max_internal=max(max_internal,inside)
            nonsole_max=max(nonsole_max,nonsole);internal_max=max(internal_max,total)
            fell=row['qpos'][2]<.07 or row['tilt_deg']>70.;assert fell==row['fell']
            if fell and first_fall is None:first_fall=row['time_s']
            if case['mode']=='passive':assert not a['ctrl'][i].any() and not a['actuator_force'][i].any()
            warnings.extend(row['warnings'])
        assert sample_count==len(a['qpos'])==result['observed_physics_steps']
    assert result['maximum_ground_penetration_m']==max_depth and result['maximum_internal_penetration_m']==max_internal
    assert result['maximum_nonsole_ground_load_n']==nonsole_max and result['maximum_internal_load_n']==internal_max
    assert result['first_fall_s']==first_fall
    assert result['load_gate']['total_over_1n_fraction']==loaded/sample_count
    assert abs(result['load_gate']['longest_over_1n_s']-longest*dt)<1e-12
    assert result['completed']==(sample_count==round(case['duration_s']/dt))
    if not result['completed']:assert not result['passed']
    if case['intervention']=='mask_shell_floor':assert first_shell is None
    return {'verified':True,'samples':sample_count,'source_actions_and_fifo_exact':True,
            'all_subdivision_holds_verified':True,'first_shell_contact_s':first_shell,
            'first_shell_loaded_s':first_shell_loaded,'contact_parameter_sets':[{'values':json.loads(k),'count':v} for k,v in params.items()],
            'warnings':sorted(set(warnings)),'diagnostic_passed':result['passed'],'failures':result['failures']}


def arrays_equal(one,two):
    counts={}
    for filename in ('initial-state.npz','dynamics.npz'):
        with np.load(one/filename) as a,np.load(two/filename) as b:
            assert a.files==b.files
            for name in a.files:
                assert a[name].shape==b[name].shape and a[name].dtype==b[name].dtype
                assert a[name].tobytes()==b[name].tobytes(),(str(one),str(two),filename,name)
            counts[filename]=len(a.files)
    return counts


def main():
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['controls','all']);args=parser.parse_args()
    bank=load(BASE/'bank.json');source=np.load(ROOT/bank['actions_file'])
    home=np.array(load(ROOT/'microduck_contract/interface/observation-v1.json')['home_joint_position_rad'])
    cases=[c for c in bank['cases'] if args.phase=='all' or c['phase']=='controls']
    checks={};golden={}
    for case in cases:
        checks[case['id']]=verify_case(case,bank,source,home)
        if case['phase']=='controls':
            now=ROOT/bank['output_root']/case['id']
            old=ROOT/bank['v63_root']/'runs'/f"{case['model']}-{case['mode']}-r{case['repeat']}"
            golden[case['id']]=arrays_equal(now,old)
            if case['model']=='v11' and case['mode']=='replay':assert load(now/'result.json')['golden_replay']['passed']
        print(json.dumps({'case':case['id'],**{k:v for k,v in checks[case['id']].items() if k not in ('contact_parameter_sets',)}}),flush=True)
    repeats={}
    for case in cases:
        if case['repeat']==1:
            name=case['id'][:-1]
            repeats[name]=arrays_equal(ROOT/bank['output_root']/(name+'1'),ROOT/bank['output_root']/(name+'2'))
    report={'verification_passed':True,'cases_verified':len(cases),'samples_verified':sum(r['samples'] for r in checks.values()),
            'checks':checks,'original_v63_controls_exact':golden,'repeats':repeats,
            'model_admitted':False,'walking_accepted':False,'physical_acceptance':False}
    save(BASE/(args.phase+'-review.json'),report)


if __name__=='__main__':main()
