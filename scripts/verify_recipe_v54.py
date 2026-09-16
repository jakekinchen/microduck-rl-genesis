"""Read complete V54 evidence and decide prerequisites without rerunning physics."""
import gzip
import hashlib
import json
from collections import defaultdict,deque
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiments.walking.recipe_v54 import (FREEZE,RECIPES,REPLAY,candidate,digest,
    new_output,run_name,verify_sources,write_manifest)
from scripts.train_recipe_v54 import require_freeze,INIT_RUN,parent_state
from scripts.analyze_components_v45 import verify_manifest
from microduck.native_sequence_env_v54 import LAYOUTS,next_level,BUCKETS


def stored_rows(folder,record,role,dim):
    h=hashlib.sha256();size=0
    with gzip.open(folder/('all-'+role+'s-float32.bin.gz'),'rb') as stream:
        while block:=stream.read(1024*1024):
            if len(block)%4 or not np.isfinite(np.frombuffer(block,dtype='<f4')).all():
                raise ValueError('invalid stored '+role)
            h.update(block);size+=len(block)
    assert size==record['new_transitions']*dim*4
    assert h.hexdigest()==record['final_coverage'][role+'_raw_sha256']
    return dict(rows=size//(dim*4),bytes=size,raw_sha256=h.hexdigest(),finite=True)


def verify_curriculum(folder,record):
    n=record['args']['num_envs'];total=record['new_transitions']//n
    levels=np.zeros(n,int);starts=np.zeros(n,int)
    recent=[deque(maxlen=8) for _ in range(n)]
    completions=np.zeros((24,3),int);falls=np.zeros((24,3),int);controls=np.zeros((24,3),int)
    rows=0
    with gzip.open(folder/'episodes.jsonl.gz','rt') as stream:
        for line in stream:
            row=json.loads(line);i=row['env'];b=i%24;level=int(levels[i])
            assert row['bucket']==b and row['level']==level
            assert row['controls']==row['global_control']-starts[i]+1
            assert row['controls']>0 and row['controls']<=LAYOUTS[level][0]*LAYOUTS[level][2]
            if row['completed']:
                assert not row['fell'] and row['controls']==LAYOUTS[level][0]*LAYOUTS[level][2]
            else: assert row['fell']
            completions[b,level]+=int(row['completed']);falls[b,level]+=int(row['fell'])
            controls[b,level]+=row['controls'];recent[i].append(row['completed'])
            levels[i]=next_level(level,recent[i],row['global_control'])
            if levels[i]!=level: recent[i].clear()
            starts[i]=row['global_control']+1;rows+=1
    for i in range(n): controls[i%24,levels[i]]+=total-starts[i]
    cover=record['final_coverage']
    for actual,key in [(levels,'final_levels'),(completions,'curriculum_completions'),
            (falls,'curriculum_falls'),(controls,'curriculum_control_counts')]:
        np.testing.assert_array_equal(actual,np.asarray(cover[key]))
    assert controls.sum()==record['new_transitions']
    switches=np.zeros((24,2),int);switch_rows=0
    with gzip.open(folder/'handoff-histories.jsonl.gz','rt') as stream:
        for line in stream:
            row=json.loads(line);direction=0 if row['direction']=='walk-to-stand' else 1
            assert bool(np.all(np.asarray(row['observation'])[48:51]==0))==(direction==0)
            for key in ['observation','qpos','qvel','motor_fifo','previous_torque','q_target','sensors','last_action']:
                assert np.isfinite(np.asarray(row[key])).all()
            switches[row['bucket'],direction]+=1;switch_rows+=1
    np.testing.assert_array_equal(switches,np.asarray(cover['switches_walk_to_stand_and_reverse']))
    return dict(episode_rows=rows,switch_rows=switch_rows,completions=completions.tolist(),
        falls=falls.tolist(),control_counts=controls.tolist(),final_levels=levels.tolist(),
        all_cells_complete_level2=bool((completions[:,2]>0).all()),
        all_cells_both_switch_directions=bool((switches>0).all()))


def verify_evaluation(folder,recipe,expected_count,session_bank):
    import torch
    from evaluator.core import OnnxPolicy
    verify_manifest(folder)
    result=json.loads((folder/('probe.json' if session_bank else 'evaluation.json')).read_text())
    assert result['recipe']==recipe and not result['held_out']
    if session_bank:
        assert result['complete'] and result['total_sessions']==expected_count and result['exception'] is None
    else: assert result['total_cases']==expected_count
    config=json.loads((ROOT/'evaluator/config-v1.json').read_text())['inference']
    policies={role:OnnxPolicy(folder/('standing/policy.onnx' if role=='standing' else 'policy.onnx'),config)
        for role in ['walking','standing']}
    if recipe=='shared':
        assert digest(folder/'policy.onnx')==digest(folder/'standing/policy.onnx')
    arrays={p.name.removesuffix('-actions-float32.npy'):np.load(p) for p in folder.glob('*-actions-float32.npy')}
    counters=defaultdict(int);rows=loads=0
    with gzip.open(folder/'trajectory.jsonl.gz','rt') as stream:
        for line in stream:
            row=json.loads(line);case=row['case_id'];index=counters[case];counters[case]+=1
            obs=np.asarray(row['actor_observation'],np.float32)[None]
            action,_=policies[row['actor_mode']].infer(obs)
            assert action[0].tobytes()==arrays[case][index].tobytes(), 'ONNX/action byte mismatch'
            assert len(row['self_load_physics'])==4
            rows+=1;loads+=4
    assert all(count==len(arrays[case]) for case,count in counters.items())
    assert sum(len(a) for a in arrays.values())==rows
    return result,dict(exact_onnx_action_rows=rows,physics_load_samples=loads)


def main():
    import torch
    from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
    torch.set_num_threads(1)
    frozen=require_freeze()
    out=new_output('receipts/walking/20260909-v54-verification')
    init=ROOT/'logs'/INIT_RUN;verify_manifest(init)
    init_record=json.loads((init/'initialization.json').read_text())
    assert init_record['status']=='completed' and init_record['updates']==20000
    losses=np.load(init/'losses.npy');assert losses.shape==(20000,) and np.isfinite(losses).all()
    reports={};cold_critics=[]
    for recipe in RECIPES:
        walking,standing,_=candidate(recipe)
        folder=ROOT/'logs'/run_name(recipe);verify_manifest(folder)
        record=json.loads((folder/'run.json').read_text())
        joint=torch.load(folder/record['checkpoint'],map_location='cpu',weights_only=True)['actor_state_dict']
        initial=torch.load(folder/'initial.pt',map_location='cpu',weights_only=True)
        assert digest(folder/'initial.pt')==record['initial_checkpoint_sha256']
        cold_critics.append(initial['critic_state_dict'])
        for key,value in joint.items():
            assert torch.isfinite(value).all()
            if 'obs_normalizer.' in key:
                assert value.numpy().tobytes()==initial['actor_state_dict'][key].numpy().tobytes()
        for role,run in [('walking',walking),('standing',standing)]:
            part=ROOT/'logs'/run;meta=json.loads((part/'run.json').read_text())
            state=torch.load(part/meta['checkpoint'],map_location='cpu',weights_only=True)['actor_state_dict']
            for key,value in state.items():
                joint_key=role+'.'+key if recipe=='routed' else key
                assert value.numpy().tobytes()==joint[joint_key].numpy().tobytes()
        raw={role:stored_rows(folder,record,role,dim) for role,dim in [('observation',61),('action',14)]}
        with gzip.open(folder/'all-reward-components-float32.bin.gz','rb') as stream:
            rewards=np.frombuffer(stream.read(),dtype='<f4').reshape(-1,record['args']['num_envs'],6)
        assert np.isfinite(rewards).all() and rewards.shape[0]*rewards.shape[1]==record['new_transitions']
        downhill=np.asarray([BUCKETS[i%24][1]>0 for i in range(record['args']['num_envs'])])
        active=downhill[None,:] & (rewards[:,:,5]==0)
        expected=np.where(active,3*np.abs(rewards[:,:,0]-rewards[:,:,1])/.20,0)
        np.testing.assert_allclose(rewards[:,:,2],expected,rtol=2e-6,atol=2e-6)
        np.testing.assert_allclose(rewards[:,:,4],rewards[:,:,3]-.02*rewards[:,:,2],rtol=2e-6,atol=2e-6)
        curriculum=verify_curriculum(folder,record)
        events=EventAccumulator(str(folder),size_guidance={'scalars':0});events.Reload()
        scalar_count=0
        for tag in events.Tags()['scalars']:
            values=events.Scalars(tag);assert all(np.isfinite(r.value) for r in values);scalar_count+=len(values)
        assert scalar_count>=1500
        banks={};parity={}
        for bank,count,is_session in [('flat',21,False),('repeated',42,False),('endurance',4,True),('surfaces',14,True)]:
            path=ROOT/'receipts/walking'/f'20260909-v54-{recipe}-{bank}'
            banks[bank],parity[bank]=verify_evaluation(path,recipe,count,is_session)
        old=json.loads((ROOT/'receipts/walking/20260906-v30-surface-baseline/probe.json').read_text())
        old_passes={s['session_id'] for s in old['session_reports'] if s['passed']}
        new_passes={s['session_id'] for s in banks['surfaces']['session_reports'] if s['passed']}
        behavior=(banks['flat']['passed_cases']==21 and banks['repeated']['passed_cases']==42
            and banks['endurance']['passed_sessions']==4 and old_passes<=new_passes)
        coverage=curriculum['all_cells_complete_level2'] and curriculum['all_cells_both_switch_directions']
        reports[recipe]=dict(record=record,stored_rows=raw,curriculum=curriculum,finite_scalars=scalar_count,
            evaluation_parity=parity,behavior_prerequisites_passed=behavior,coverage_prerequisites_passed=coverage,
            advances=behavior and coverage,surface_passes=sorted(new_passes),surface_regressions=sorted(old_passes-new_passes),
            results={bank:{k:r[k] for k in ('passed_cases','total_cases','passed_sessions','total_sessions') if k in r} for bank,r in banks.items()})
        for name,sha in record['source_sha256'].items(): assert digest(folder/'source'/name)==sha
        print(json.dumps(dict(recipe=recipe,advances=reports[recipe]['advances'],results=reports[recipe]['results'])),flush=True)
    for key,value in cold_critics[0].items(): assert value.numpy().tobytes()==cold_critics[1][key].numpy().tobytes()
    for bank in ['flat','endurance','surfaces']:
        verify_sources(json.loads((ROOT/f'experiments/walking/recipe-{bank}-freeze-v54.json').read_text()))
    require_freeze()
    result=dict(complete=True,evidence_verified=True,freeze_sha256=digest(FREEZE),
        initializer=init_record,arms=reports,identical_cold_critics=True,
        next_stage_allowed=any(r['advances'] for r in reports.values()),
        boundary='Exposed local recipe comparison; no physical, protected-terrain or calibrated-carpet acceptance.')
    (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    write_manifest(out)


if __name__=='__main__': main()
