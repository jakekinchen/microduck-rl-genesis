"""One bounded V49 full-state recovery diagnostic; no learning or activation."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiments.walking.recovery_v49 import (FREEZE,CAPTURE,COMPARE,SEARCH,INPUTS,digest,manifest,seal,
    source_data,world_for,rollout,score,store_rollout,exact,command_at)

EXTRA=['experiments/walking/recovery_v49.py','scripts/probe_recovery_v49.py',
       'experiments/walking/RECOVERY-FEASIBILITY-v49.md','experiments/walking/recovery-v49.json',
       'experiments/walking/snapshots_v43.py','experiments/walking/handoff_inspection_v47.py',
       'microduck/native_standing_env_v42.py','tests/test_recovery_v49.py']


def binding():
    source=json.loads((ROOT/'experiments/walking/native-standing-retention-freeze-v48.json').read_text())['source_sha256'].copy()
    for name,sha in source.items():
        if digest(ROOT/name)!=sha:raise ValueError('parent source drift: '+name)
    for name in EXTRA:source[name]=digest(ROOT/name)
    inputs={}
    for key,name in INPUTS.items():
        folder=ROOT/'receipts/walking'/name;manifest(folder)
        inputs[key]={'receipt':name,'manifest_sha256':digest(folder/'SHA256SUMS')}
    return dict(schema='microduck.recovery-freeze/v49',source_sha256=source,inputs=inputs,
        parameters=json.loads((ROOT/'experiments/walking/recovery-v49.json').read_text()))


def retain_sources(out,frozen):
    for name in frozen['source_sha256']:
        dest=out/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dest)
    shutil.copy2(FREEZE,out/'freeze.json')


def capture(out):
    import numpy as np
    from experiments.walking.handoff_inspection_v47 import retain_state,restore_state
    from experiments.walking.snapshots_v43 import load_state
    from microduck.native_standing_env_v42 import clone_world
    entries=[];total=0;continuations=0
    for key in INPUTS:
        for source in source_data(key):
            w=world_for(source);s=source['session'];tag=key+'--'+s['id']
            try:
                for i,old in enumerate(source['rows']):
                    row=w.step_command(command_at(i,s)[0])
                    assert w.last_action.tobytes()==source['actions'][i].tobytes()
                    assert w.last_observation[0].tobytes()==np.asarray(old['actor_observation'],np.float32).tobytes()
                    assert np.array_equal(w.core.data.qpos,old['qpos']) and np.array_equal(w.core.data.qvel,old['qvel'])
                    total+=1
                    if i+1 in source['capture_steps']:retain_state(w,out,tag,i+1)
                for step in source['capture_steps']:
                    path=out/'states'/f'{tag}-step-{step}.json'
                    # Locally created index, loaded after checking its exact serialized hash.
                    index_sha=digest(path);state=load_state(path,out/'snapshot-blobs');assert digest(path)==index_sha
                    target=clone_world(w)
                    try:
                        for repeat in range(2):
                            restore_state(target,state)
                            for i in range(step,min(step+25,len(source['rows']))):
                                target.step_command(command_at(i,s)[0]);old=source['rows'][i]
                                assert target.last_action.tobytes()==source['actions'][i].tobytes()
                                assert target.last_observation[0].tobytes()==np.asarray(old['actor_observation'],np.float32).tobytes()
                                assert np.array_equal(target.core.data.qpos,old['qpos']) and np.array_equal(target.core.data.qvel,old['qvel'])
                                continuations+=1
                    finally:target.close()
                    entries.append(dict(id=tag+'-'+str(step),key=key,session=s['id'],step=step,
                        state=str(path.relative_to(out)),state_sha256=index_sha,
                        search_target=key=='v48' or key=='matched' and s['id'].startswith('downhill')))
                print(json.dumps(dict(captured=tag,reproduced_controls=len(source['rows']))),flush=True)
            finally:w.close()
    assert len(entries)==12
    return dict(complete=True,states=entries,reproduced_controls=total,exact_reset_controls=continuations,
                action_and_observation_bytes_exact=True,poses_and_velocities_exact=True)


def paired_controls(out):
    import numpy as np
    from experiments.walking.snapshots_v43 import load_state
    manifest(CAPTURE)
    captured=json.loads((CAPTURE/'result.json').read_text())
    sources={(d['key'],d['session']['id']):d for k in INPUTS for d in source_data(k)}
    reports=[];exact_controls=0;source_controls=0
    for entry in captured['states']:
        source=sources[entry['key'],entry['session']];start=entry['step']
        state=load_state(CAPTURE/entry['state'],CAPTURE/'snapshot-blobs');world=world_for(source)
        try:
            for anchor in ['original','v48']:
                a=rollout(world,state,source,start,anchor)
                b=rollout(world,state,source,start,anchor);exact(a,b);exact_controls+=a['controls']
                is_source=anchor==('v48' if entry['key']=='v48' else 'original')
                if is_source:
                    old=source['rows'][start:]
                    assert a['actions'].tobytes()==source['actions'][start:].tobytes()
                    for now,before in zip(a['rows'],old):
                        assert np.array_equal(now['qpos'],before['qpos']) and np.array_equal(now['qvel'],before['qvel'])
                        assert np.asarray(now['actor_observation'],np.float32).tobytes()==np.asarray(before['actor_observation'],np.float32).tobytes()
                    assert len(a['rows'])==len(old);source_controls+=len(old)
                folder=out/(entry['id']+'--'+anchor);store_rollout(folder,a)
                report=score(source['rows'][:start],a['rows'],source)
                report.update(state_id=entry['id'],anchor=anchor,source_arm_exact=is_source,repeat_exact=True,
                    search_target=entry['search_target'],prefix_source=INPUTS[entry['key']],state_sha256=entry['state_sha256'])
                (folder/'evaluation.json').write_text(json.dumps(report,indent=2)+'\n');reports.append(report)
                print(json.dumps({k:report[k] for k in ['state_id','anchor','passed','current_window_passed','restart_window_passed','observed_duration_s']}),flush=True)
        finally:world.close()
    return dict(complete=True,branches=reports,exact_repeated_controls=exact_controls,exact_source_controls=source_controls)


def search(out):
    import numpy as np
    from experiments.walking.snapshots_v43 import load_state
    manifest(CAPTURE);manifest(COMPARE)
    entries=json.loads((CAPTURE/'result.json').read_text())['states']
    controls=json.loads((COMPARE/'result.json').read_text())['branches']
    sources={(d['key'],d['session']['id']):d for k in INPUTS for d in source_data(k)}
    cfg=json.loads((ROOT/'experiments/walking/recovery-v49.json').read_text())['search']
    reports=[];total_trials=0;total_steps=0;offset=0
    with gzip.open(out/'all-actions-float32.bin.gz','wb',compresslevel=1) as action_stream, gzip.open(out/'all-observations-float32.bin.gz','wb',compresslevel=1) as obs_stream, (out/'trials.jsonl').open('w') as trial_stream:
        for n,entry in enumerate(e for e in entries if e['search_target']):
            solved=[r['anchor'] for r in controls if r['state_id']==entry['id'] and r['passed']]
            if solved:
                reports.append(dict(state_id=entry['id'],search_skipped='unmodified counterfactual already passes full session',passing_controls=solved));continue
            source=sources[entry['key'],entry['session']];start=entry['step']
            state=load_state(CAPTURE/entry['state'],CAPTURE/'snapshot-blobs');world=world_for(source)
            _,window,_=command_at(start,source['session']);end=sum(round(w['duration_s']*50) for w in source['session']['windows'][:window+1])
            rng=np.random.default_rng(cfg['seed']+n)
            mean=np.zeros((2,5,14));std=np.full_like(mean,cfg['initial_std_rad']);best=[None,None]
            generation_log=[]
            # Incoming-action bridge seeds are explicit search candidates, not
            # a deployed filter. First-standing source observations precede any
            # intervention and are used only for this privileged initialization.
            from experiments.walking.recovery_v49 import anchors,KNOT_TIMES
            first_stand=next(i for i in range(start,len(source['rows'])) if source['rows'][i]['actor_mode']=='standing')
            prior=source['actions'][first_stand-1]
            observation=np.asarray(source['rows'][first_stand]['actor_observation'],np.float32)[None]
            seeds={}
            for anchor,actor in anchors(world).items():
                delta=prior-actor.infer(observation)[0][0]
                delay=(first_stand-start)*.02
                seeds[anchor]=[np.clip(np.array([delta*max(0.,1-max(0,t-delay)/release) if t>=delay or delay==0 else np.zeros(14)
                    for t in KNOT_TIMES[:-1]]),-cfg['maximum_residual_rad'],cfg['maximum_residual_rad']).astype(np.float32)
                    for release in [.5,1.,1.75]]
            try:
                for gen in range(cfg['generations']):
                    candidates=[[],[]]
                    for ai,anchor in enumerate(['original','v48']):
                        population=np.clip(rng.normal(mean[ai],std[ai],size=(cfg['population_per_anchor'],5,14)),-cfg['maximum_residual_rad'],cfg['maximum_residual_rad']).astype(np.float32)
                        population[0]=mean[ai]
                        population[1]=best[ai]['knots'] if best[ai] else np.zeros((5,14),np.float32)
                        population[2:5]=seeds[anchor]
                        for knots in population:
                            result=rollout(world,state,source,start,anchor,knots=knots,end=end,record=False)
                            a=result['actions'].tobytes();o=result['observations'].tobytes()
                            action_stream.write(a);obs_stream.write(o)
                            record=dict(state_id=entry['id'],generation=gen,anchor=anchor,trial=total_trials,
                                knots=knots.tolist(),cost=result['cost'],fell=result['fell'],controls=result['controls'],
                                raw_row_offset=offset,action_sha256=hashlib.sha256(a).hexdigest(),observation_sha256=hashlib.sha256(o).hexdigest())
                            trial_stream.write(json.dumps(record)+'\n');trial_stream.flush()
                            offset+=result['controls'];total_trials+=1;total_steps+=result['controls']
                            candidate=dict(cost=result['cost'],knots=knots.copy(),anchor=anchor,trial=record['trial'])
                            candidates[ai].append(candidate)
                            if best[ai] is None or candidate['cost']<best[ai]['cost']:best[ai]=candidate
                        elite=sorted(candidates[ai],key=lambda x:x['cost'])[:cfg['elites_per_anchor']]
                        values=np.array([r['knots'] for r in elite]);mean[ai]=.5*mean[ai]+.5*values.mean(0)
                        std[ai]=np.maximum(cfg['minimum_std_rad'],.5*std[ai]+.5*values.std(0))
                    progress=dict(state_id=entry['id'],generation=gen,best_costs=[b['cost'] for b in best],trials=total_trials,simulated_search_controls=total_steps)
                    generation_log.append(progress);print(json.dumps(progress),flush=True)
                    (out/'progress.json').write_text(json.dumps(progress,indent=2)+'\n')
                chosen=min(best,key=lambda x:x['cost'])
                # Exactly one proxy-selected candidate, then full original-gate validation.
                a=rollout(world,state,source,start,chosen['anchor'],knots=chosen['knots'])
                b=rollout(world,state,source,start,chosen['anchor'],knots=chosen['knots']);exact(a,b)
                folder=out/entry['id'];store_rollout(folder,a)
                np.save(folder/'chosen-knots-float32.npy',chosen['knots'])
                report=score(source['rows'][:start],a['rows'],source)
                report.update(state_id=entry['id'],anchor=chosen['anchor'],selected_trial=chosen['trial'],
                    search_cost=chosen['cost'],repeat_exact=True,privileged_diagnostic=True,
                    prefix_source=INPUTS[entry['key']],state_sha256=entry['state_sha256'],generation_log=generation_log)
                (folder/'evaluation.json').write_text(json.dumps(report,indent=2)+'\n');reports.append(report)
                print(json.dumps({k:report[k] for k in ['state_id','anchor','passed','current_window_passed','restart_window_passed','observed_duration_s']}),flush=True)
            finally:world.close()
    return dict(complete=True,states=reports,search_trials=total_trials,simulated_search_controls=total_steps,
                maximum_trials=6*cfg['generations']*2*cfg['population_per_anchor'],seed=cfg['seed'],
                policy_trained=False,policy_activated=False,physical_calibration=False,
                boundary='Bounded privileged recovery search. A failed finite search is unresolved, not impossibility; same-state replay is not generalization.')


def main():
    p=argparse.ArgumentParser();p.add_argument('--phase',choices=['freeze','capture','compare','search'],required=True);a=p.parse_args()
    frozen=binding()
    if a.phase=='freeze':
        with FREEZE.open('x') as f:json.dump(frozen,f,indent=2);f.write('\n')
        return
    if frozen!=json.loads(FREEZE.read_text()):raise ValueError('source or input drift')
    if shutil.disk_usage(ROOT).free<3_000_000_000:raise ValueError('less than 3GB free before diagnostic')
    out={'capture':CAPTURE,'compare':COMPARE,'search':SEARCH}[a.phase];out.mkdir(parents=True,exist_ok=False)
    started=time.monotonic();result={'complete':False}
    retain_sources(out,frozen)
    try:
        result={'capture':capture,'compare':paired_controls,'search':search}[a.phase](out)
        assert binding()==frozen
    except BaseException as exc:
        result.update(complete=False,exception=f'{type(exc).__name__}: {exc}');raise
    finally:
        result.update(phase=a.phase,elapsed_s=time.monotonic()-started,freeze_sha256=digest(FREEZE))
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');seal(out)
    print(json.dumps({k:v for k,v in result.items() if k not in ['states','branches']}),flush=True)


if __name__=='__main__':main()
