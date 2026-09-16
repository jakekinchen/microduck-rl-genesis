"""Bounded V51 recovery eligibility with the V50 walker and V15 steady standing."""
import argparse,gzip,hashlib,json,shutil,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiments.walking.recovery_v51 import *
OLD=ROOT/'receipts/walking/20260908-v49-recovery-search'
EXTRA=['experiments/walking/recovery_v51.py','scripts/probe_recovery_v51.py','experiments/walking/BRAKING-FEASIBILITY-v51.md']

def binding():
    sources={}
    for name in ['recovery-freeze-v49.json','native-retention-freeze-v50.json']:
        f=json.loads((ROOT/'experiments/walking'/name).read_text())
        for path,sha in f['source_sha256'].items():
            assert digest(ROOT/path)==sha,path
            sources[path]=sha
    for name in EXTRA:sources[name]=digest(ROOT/name)
    inputs={}
    for folder in [ROOT/'receipts/walking'/INPUTS['v50'],OLD,ROOT/'receipts/walking/20260908-v48-standing-retention-endurance']:
        manifest(folder);inputs[str(folder.relative_to(ROOT))]=digest(folder/'SHA256SUMS')
    return dict(schema='microduck.braking-freeze/v51',source_sha256=sources,inputs=inputs,
        seed=26090851,generations=8,population=24,elites=6,maximum_trials=1152)

def witness(entry):
    import numpy as np
    folder=OLD/f"matched--{entry['session']}-{entry['step']}"
    r=json.loads((folder/'evaluation.json').read_text())
    assert r['anchor']=='v48'
    assert eligible(r)
    return np.load(folder/'chosen-knots-float32.npy')

def eligible(report):
    c=report['case_reports'][0]
    allowed={'mean_abs_yaw_error_rad_s','endurance:tracking_bucket_2:mean_abs_yaw_error_rad_s'}
    return c['observed_controls']==900 and not (set(c['failures'])-allowed)

def retain_sources(out,frozen):
    for name in frozen['source_sha256']:
        dst=out/'source'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dst)
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
                        search_target=True))
                print(json.dumps(dict(captured=tag,reproduced_controls=len(source['rows']))),flush=True)
            finally:w.close()
    assert len(entries)==3
    return dict(complete=True,states=entries,reproduced_controls=total,exact_reset_controls=continuations,
                action_and_observation_bytes_exact=True,poses_and_velocities_exact=True)


def evaluate_branch(out,entry,source,state,world,anchor,knots,label):
    a=rollout(world,state,source,entry['step'],anchor,knots=knots)
    b=rollout(world,state,source,entry['step'],anchor,knots=knots);exact(a,b)
    if label=='unmodified':
        assert a['actions'].tobytes()==source['actions'][entry['step']:].tobytes()
        assert len(a['rows'])==len(source['rows'])-entry['step']
        for now,old in zip(a['rows'],source['rows'][entry['step']:]):
            np.testing.assert_array_equal(now['qpos'],old['qpos']);np.testing.assert_array_equal(now['qvel'],old['qvel'])
            assert np.asarray(now['actor_observation'],np.float32).tobytes()==np.asarray(old['actor_observation'],np.float32).tobytes()
    folder=out/(entry['id']+'--'+label);store_rollout(folder,a)
    if knots is not None:np.save(folder/'knots-float32.npy',knots)
    report=score(source['rows'][:entry['step']],a['rows'],source)
    report.update(schema='microduck.braking-branch/v51',state_id=entry['id'],anchor=anchor,label=label,
        repeat_exact=True,demonstration_eligible=eligible(report) and anchor!='v48',
        stop_checks_passed=eligible(report),steady_v15=anchor!='v48',state_sha256=entry['state_sha256'])
    (folder/'branch-result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['state_id','label','demonstration_eligible','observed_duration_s','passed']}),flush=True)
    return report

def compare(out):
    from experiments.walking.snapshots_v43 import load_state
    manifest(CAPTURE);manifest(OLD)
    entries=json.loads((CAPTURE/'result.json').read_text())['states'];sources={s['session']['id']:s for s in source_data('v50')};reports=[]
    for entry in entries:
        source=sources[entry['session']];state=load_state(CAPTURE/entry['state'],CAPTURE/'snapshot-blobs');w=world_for(source)
        try:
            knots=witness(entry)
            for anchor,k,label in [('original',None,'unmodified'),('original',knots,'witness-v15'),('v48',knots,'witness-v48'),('transient',knots,'witness-transient')]:
                reports.append(evaluate_branch(out,entry,source,state,w,anchor,k,label))
        finally:w.close()
    return dict(complete=True,branches=reports,eligible_states=sorted({r['state_id'] for r in reports if r['demonstration_eligible']}))

def search(out):
    from experiments.walking.snapshots_v43 import load_state
    manifest(CAPTURE);manifest(COMPARE)
    entries=json.loads((CAPTURE/'result.json').read_text())['states'];comparisons=json.loads((COMPARE/'result.json').read_text())['branches']
    sources={s['session']['id']:s for s in source_data('v50')};reports=[];trials=offset=0
    with gzip.open(out/'all-actions-float32.bin.gz','wb',compresslevel=1) as af,gzip.open(out/'all-observations-float32.bin.gz','wb',compresslevel=1) as of,(out/'trials.jsonl').open('w') as tf:
        for n,entry in enumerate(entries):
            solved=[r for label in ['witness-v15','witness-transient'] for r in comparisons if r['state_id']==entry['id'] and r['label']==label and r['demonstration_eligible']]
            if solved:
                reports.append(dict(state_id=entry['id'],search_skipped=True,selected_comparison=solved[0]['label'],demonstration_eligible=True));continue
            source=sources[entry['session']];state=load_state(CAPTURE/entry['state'],CAPTURE/'snapshot-blobs');w=world_for(source)
            rng=np.random.default_rng(26090851+n);mean=np.repeat(witness(entry)[None],2,axis=0);std=np.full((2,5,14),.18);best=[None,None]
            try:
                for gen in range(8):
                    for ai,anchor in enumerate(['original','transient']):
                        population=np.clip(rng.normal(mean[ai],std[ai],size=(24,5,14)),-1.5,1.5).astype(np.float32)
                        population[0]=mean[ai];population[1]=best[ai]['knots'] if best[ai] else witness(entry);population[2]=0
                        candidates=[]
                        for knots in population:
                            result=rollout(w,state,source,entry['step'],anchor,knots=knots,end=900,record=False)
                            a=result['actions'].tobytes();o=result['observations'].tobytes();af.write(a);of.write(o)
                            record=dict(state_id=entry['id'],generation=gen,anchor=anchor,trial=trials,knots=knots.tolist(),cost=result['cost'],fell=result['fell'],controls=result['controls'],raw_row_offset=offset,action_sha256=hashlib.sha256(a).hexdigest(),observation_sha256=hashlib.sha256(o).hexdigest())
                            tf.write(json.dumps(record)+'\n');offset+=result['controls'];trials+=1
                            candidate=dict(cost=result['cost'],anchor=anchor,knots=knots.copy(),trial=record['trial']);candidates.append(candidate)
                            if best[ai] is None or candidate['cost']<best[ai]['cost']:best[ai]=candidate
                        elite=np.array([r['knots'] for r in sorted(candidates,key=lambda x:x['cost'])[:6]])
                        mean[ai]=.5*mean[ai]+.5*elite.mean(0);std[ai]=np.maximum(.02,.5*std[ai]+.5*elite.std(0))
                    tf.flush();print(json.dumps(dict(state_id=entry['id'],generation=gen,trials=trials,best_cost=[b['cost'] for b in best])),flush=True)
                chosen=min(best,key=lambda x:x['cost'])
                report=evaluate_branch(out,entry,source,state,w,chosen['anchor'],chosen['knots'],'retargeted')
                report.update(selected_trial=chosen['trial'],proxy_cost=chosen['cost']);reports.append(report)
            finally:w.close()
    return dict(complete=True,states=reports,search_trials=trials,search_controls=offset,maximum_trials=1152,
        learning_eligible=all(r['demonstration_eligible'] for r in reports),policy_trained=False,policy_activated=False)

def main():
    p=argparse.ArgumentParser();p.add_argument('--phase',choices=['freeze','capture','compare','search'],required=True);a=p.parse_args();frozen=binding()
    if a.phase=='freeze':
        with FREEZE.open('x') as f:json.dump(frozen,f,indent=2);f.write('\n')
        return
    assert frozen==json.loads(FREEZE.read_text())
    assert shutil.disk_usage(ROOT).free>3_000_000_000
    out={'capture':CAPTURE,'compare':COMPARE,'search':SEARCH}[a.phase];out.mkdir(parents=True,exist_ok=False);retain_sources(out,frozen)
    started=time.monotonic();result={'complete':False}
    try:
        result={'capture':capture,'compare':compare,'search':search}[a.phase](out);assert binding()==frozen
    except BaseException as exc:
        result.update(complete=False,exception=f'{type(exc).__name__}: {exc}');raise
    finally:
        result.update(phase=a.phase,elapsed_s=time.monotonic()-started,freeze_sha256=digest(FREEZE));(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');seal(out)
    print(json.dumps({k:v for k,v in result.items() if k not in ['states','branches']}),flush=True)
if __name__=='__main__':main()
