"""Read-only verification of retained V63 actions, states and contact evidence."""
from pathlib import Path
import gzip
import hashlib
import json
import numpy as np

P=Path(__file__).resolve().parent
ROOT=P.parents[2]


def rotation(q):
    w,x,y,z=np.asarray(q)/np.linalg.norm(q)
    return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                     [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                     [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])


def main():
    bank=json.loads((P/'bank.json').read_text())
    source=np.load(ROOT/bank['actions_file'],allow_pickle=False)
    home=np.array(json.loads((ROOT/'microduck_contract/interface/observation-v1.json').read_text())['home_joint_position_rad'])
    reports={};traces={};checks={};first_contacts={};total=0
    for case in bank['cases']:
        name=case['id'];directory=P/'runs'/name
        result=json.loads((directory/'result.json').read_text());reports[name]=result
        if 'error' in result:raise RuntimeError(name+': '+result['error'])
        actions=np.load(directory/'requested-actions-float32.npy',allow_pickle=False)
        expected=source if case['mode']=='replay' else np.zeros((250,14),np.float32)
        assert actions.dtype==np.float32 and actions.tobytes()==expected.tobytes(),name
        with gzip.open(directory/'physics.jsonl.gz','rt') as stream:rows=[json.loads(line) for line in stream]
        traces[name]=rows;total+=len(rows)
        names=json.loads((directory/'configuration.json').read_text())['geom_names']
        sole_names=set(bank['models'][case['model']]['sole_geoms'])
        active_pairs={}
        with np.load(directory/'dynamics.npz',allow_pickle=False) as arrays:
            assert len(rows)==result['observed_physics_steps']==len(arrays['qpos'])
            for tick,row in enumerate(rows):
                assert abs(row['time_s']-(tick+1)*.005)<1e-8
                assert row['action_index']==tick//4 and row['substep']==tick%4
                np.testing.assert_array_equal(row['qpos'],arrays['qpos'][tick])
                np.testing.assert_array_equal(row['qvel'],arrays['qvel'][tick])
                np.testing.assert_array_equal(row['motor_torque_nm'],arrays['ctrl'][tick])
                np.testing.assert_array_equal(row['actuator_force_nm'],arrays['actuator_force'][tick])
                np.testing.assert_array_equal(row['frictionloss_nm'],arrays['friction'][tick])
                np.testing.assert_array_equal(row['damping'],arrays['damping'][tick])
                target=home if tick<bank['motor_ticks'] else home+actions[(tick-bank['motor_ticks'])//4].astype(np.float64)
                np.testing.assert_array_equal(row['applied_target_rad'],target)
                if tick:np.testing.assert_array_equal(row['qpos_before'],rows[tick-1]['qpos'])
                pairs={};internal_depth=ground_depth=nonsole=0.
                for contact in row['contacts']:
                    ids=tuple(contact['geom_ids']);pair_names=tuple(names[i] for i in ids)
                    force=np.array(contact['force_contact_frame']);assert np.isfinite(force).all()
                    internal='floor' not in pair_names;assert internal==contact['internal']
                    normal=max(0.,float(force[0]));depth=max(0.,-contact['distance_m'])
                    if normal>0:assert contact['efc_address']>=0
                    if internal:
                        pair=tuple(sorted(ids));pairs[pair]=pairs.get(pair,0.)+normal
                        internal_depth=max(internal_depth,depth)
                    else:
                        ground_depth=max(ground_depth,depth)
                        robot=pair_names[1] if pair_names[0]=='floor' else pair_names[0]
                        if robot not in sole_names:nonsole+=normal
                    if normal>.1 and ids not in active_pairs:
                        active_pairs[ids]={'time_s':row['time_s'],'geom_ids':list(ids),'names':list(pair_names),
                                          'normal_n':normal,'penetration_m':depth,'internal':internal}
                assert row['total_normal_n']==sum(pairs.values())
                assert row['largest_pair_normal_n']==max(pairs.values(),default=0.)
                assert row['internal_penetration_m']==internal_depth and row['ground_penetration_m']==ground_depth
                assert row['nonsole_ground_load_n']==nonsole
                if case['mode']=='passive':
                    assert not arrays['ctrl'][tick].any() and not arrays['actuator_force'][tick].any()
        checks[name]={'passed':True,'physics_samples':len(rows),'action_values_byte_identical':True,
                      'manual_fifo_targets_exact':True,'contact_loads_independently_reaggregated':True,
                      'state_arrays_equal_trace':True,'original_case_passed':result['passed'],
                      'first_fall_s':result['first_fall_s'],'failures':result['failures']}
        first_contacts[name]=list(active_pairs.values())
    repeats={}
    for model in bank['models']:
        for mode in ['home','passive','replay']:
            one,two=[P/'runs'/f'{model}-{mode}-r{r}' for r in [1,2]]
            counts={}
            for filename in ['initial-state.npz','dynamics.npz']:
                with np.load(one/filename) as a,np.load(two/filename) as b:
                    assert a.files==b.files
                    for key in a.files:
                        assert a[key].shape==b[key].shape and a[key].dtype==b[key].dtype
                        assert a[key].tobytes()==b[key].tobytes(),(model,mode,filename,key)
                    counts[filename]=len(a.files)
            repeats[model+'-'+mode]={'passed':True,'array_counts':counts}
    a=traces['v11-replay-r1'];b=traces['v62-replay-r1'];n=len(b)
    qa=np.array([r['qpos'] for r in a[:n]]);qb=np.array([r['qpos'] for r in b])
    root=np.linalg.norm(qb[:,:3]-qa[:,:3],axis=1);joint=np.max(np.abs(qb[:,7:]-qa[:,7:]),axis=1)
    first=lambda values,limit:float((np.flatnonzero(values>limit)[0]+1)*.005) if (values>limit).any() else None
    divergence={'first_root_over_0_1mm_s':first(root,.0001),'first_root_over_1mm_s':first(root,.001),
                'first_joint_over_0_1deg_s':first(joint,np.deg2rad(.1)),
                'first_joint_over_1deg_s':first(joint,np.deg2rad(1.)),
                'boundary':'posthoc localization, not a causal isolation or acceptance threshold'}
    physical={}
    with np.load(P/'runs/v11-replay-r1/initial-state.npz') as aa,np.load(P/'runs/v62-replay-r1/initial-state.npz') as bb:
        for key in ['body_mass','body_inertia','body_ipos','body_iquat','body_pos','body_quat','jnt_range','dof_armature','dof_damping','dof_frictionloss']:
            physical[key]={'byte_equal':aa[key].tobytes()==bb[key].tobytes(),
                           'maximum_raw_absolute_difference':float(np.max(np.abs(aa[key]-bb[key])))}
        physical['body_rotation_matrix_maximum_difference']=float(max(
            np.abs(rotation(a)-rotation(b)).max() for a,b in zip(aa['body_quat'],bb['body_quat'])))
        ta=np.array([rotation(q)@np.diag(i)@rotation(q).T for q,i in zip(aa['body_iquat'],aa['body_inertia'])])
        tb=np.array([rotation(q)@np.diag(i)@rotation(q).T for q,i in zip(bb['body_iquat'],bb['body_inertia'])])
        physical['body_frame_inertia_tensor_maximum_difference_kg_m2']=float(np.max(np.abs(ta-tb)))
    summary={'verification_passed':True,'cases_verified':len(checks),'physics_samples_verified':total,
             'checks':checks,'repeats':repeats,'replay_divergence':divergence,
             'first_loaded_contacts':first_contacts,'initial_physical_comparison':physical,
             'diagnostic_cases_passed':sum(r['passed'] for r in reports.values()),
             'candidate_replay_completed':reports['v62-replay-r1']['completed'],
             'model_admitted':False,'walking_accepted':False,'physical_acceptance':False}
    with (P/'review.json').open('x') as stream:json.dump(summary,stream,indent=2);stream.write('\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ['checks','first_loaded_contacts','repeats']},indent=2))


if __name__=='__main__':main()
