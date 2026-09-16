"""Verify recovery labels on fixed V52 learner-visited flat states."""
import argparse
import copy
import gzip
import json
from pathlib import Path
import shutil
import sys
import time
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.walking.recovery_v49 import digest,manifest,seal,exact,store_rollout
from experiments.walking.handoff_inspection_v47 import retain_state,restore_state
from experiments.walking.snapshots_v43 import load_state
BASE=ROOT/'receipts/walking/20260908-v52-braking-flat'
OUT=ROOT/'receipts/walking/20260908-v53-retention-collection'
FREEZE=ROOT/'experiments/walking/retention-collection-freeze-v53.json'
CASES=['nominal-20-20ms--forward-08','nominal-20-20ms--forward-12','zero-lag--arc-left']
STEPS=[655,670,690]

def binding():
    f=json.loads((ROOT/'experiments/walking/braking-flat-freeze-v52.json').read_text())['source_sha256'].copy()
    for p in ['scripts/collect_braking_retention_v53.py','experiments/walking/BRAKING-RETENTION-v53.md','experiments/walking/recovery_v49.py','experiments/walking/handoff_inspection_v47.py','microduck/native_standing_env_v42.py','experiments/walking/snapshots_v43.py']:
        f[p]=digest(ROOT/p)
    for p,h in f.items():assert digest(ROOT/p)==h,p
    manifest(BASE)
    return dict(schema='microduck.retention-collection-freeze/v53',source_sha256=f,input_manifest_sha256=digest(BASE/'SHA256SUMS'),cases=CASES,capture_controls=STEPS)

def score(rows,case,suite):
    from experiments.walking.posture import evaluate_case
    from experiments.walking.heading import evaluate_heading
    from experiments.walking.self_contact import SelfContactProbe,evaluate_self_contact
    from experiments.walking.self_load import evaluate_self_load
    report=evaluate_case(rows,case,suite)
    report.update(heading=evaluate_heading(rows),self_contact=evaluate_self_contact(rows,SelfContactProbe(ROOT/'experiments/walking/models/contact-v11/scene.xml')),self_load=evaluate_self_load([s for r in rows for s in r['self_load_physics']],suite['duration_s']))
    for key in ['heading','self_contact','self_load']:report['failures'] += [key+':'+f for f in report[key]['failures']]
    report.update(passed=not report['failures'],observed_controls=len(rows),required_controls=900)
    return report

def requested(i,case):return case['command'] if 50<=i<650 else [0,0,0]

def continuation(w,state,brake_state,start,case,suite,mode,policies):
    from experiments.laser.gait import GaitProbe
    from experiments.walking.self_load import record_self_loads
    restore_state(w,state);w.brake_v52.age=brake_state['age'];w.brake_v52.previous_moving=brake_state['previous_moving']
    w.walking_policy,w.standing_policy=policies[mode]
    probe=GaitProbe(w.core);rows=[];actions=[];observations=[]
    with record_self_loads(w) as loads:
        for i in range(start,900):
            if w.fell:break
            row=probe.sample(w.step_command(requested(i,case)))
            row.update(time_s=(i+1)*.02,session_time_s=(i+1)*.02,case_id=case['full_id'],actor_observation=w.last_observation[0].tolist(),braking_active=w.brake_v52.active,braking_age=w.brake_v52.age,self_load_physics=[{**s,'interval_start_s':i*.02+j*.005} for j,s in enumerate(loads[-4:])])
            assert len(loads)==4*(i-start+1)
            rows.append(row);actions.append(w.last_action.copy());observations.append(w.last_observation[0].copy())
    return dict(rows=rows,actions=np.asarray(actions,np.float32),observations=np.asarray(observations,np.float32))

def main():
    a=argparse.ArgumentParser();a.add_argument('--freeze',action='store_true');args=a.parse_args();frozen=binding()
    if args.freeze:
        with FREEZE.open('x') as f:json.dump(frozen,f,indent=2);f.write('\n')
        return
    assert frozen==json.loads(FREEZE.read_text()) and shutil.disk_usage(ROOT).free>3_000_000_000
    from experiments.walking.filtered_heading_world import FilteredHeadingWalkingWorld
    from microduck.heading_headroom_v30 import Float32HeadingHeadroomServo
    from microduck.braking_v52 import install
    suite=json.loads((BASE/'suite.json').read_text());original={c:[] for c in CASES}
    with gzip.open(BASE/'trajectory.jsonl.gz','rt') as f:
        for line in f:
            row=json.loads(line)
            if row['case_id'] in original:original[row['case_id']].append(row)
    OUT.mkdir(exist_ok=False);started=time.monotonic();result=dict(complete=False,branches=[],source_controls=0,unchanged_repeated_controls=0,recovery_repeated_controls=0)
    try:
        for cid in CASES:
            tid,caseid=cid.split('--');timing=next(x for x in suite['timing_profiles'] if x['id']==tid);case={**next(x for x in suite['cases'] if x['id']==caseid),'full_id':cid}
            w=FilteredHeadingWalkingWorld(BASE/'policy.onnx',ROOT/'.workspace/bam',standing_policy=BASE/'standing/policy.onnx',model_directory=ROOT/'experiments/walking/models/contact-v11',motor_ticks=timing['motor_ticks'],sensor_ticks=timing['sensor_ticks'],yaw=case['yaw'],seed=suite['seed']);w.heading_servo=Float32HeadingHeadroomServo();install(w)
            policies={'v52':(w.walking_policy,w.standing_policy),'base':(w.walking_policy.base,w.standing_policy.base)};events={};saved=np.load(BASE/f'{cid}-actions-float32.npy')
            try:
                for i,old in enumerate(original[cid]):
                    row=w.step_command(requested(i,case))
                    assert w.last_action.tobytes()==saved[i].tobytes() and w.last_observation[0].tobytes()==np.asarray(old['actor_observation'],np.float32).tobytes()
                    assert np.array_equal(w.core.data.qpos,old['qpos']) and np.array_equal(w.core.data.qvel,old['qvel'])
                    assert w.brake_v52.age==old['braking_age'] and w.brake_v52.active==old['braking_active']
                    result['source_controls']+=1
                    if i+1 in STEPS:
                        retain_state(w,OUT,cid,i+1);events[i+1]=dict(age=w.brake_v52.age,previous_moving=w.brake_v52.previous_moving)
                for step in STEPS:
                    path=OUT/'states'/f'{cid}-step-{step}.json';state_sha=digest(path);state=load_state(path,OUT/'snapshot-blobs');assert digest(path)==state_sha
                    for mode in ['v52','base']:
                        one=continuation(w,state,events[step],step,case,suite,mode,policies);two=continuation(w,state,events[step],step,case,suite,mode,policies);exact(one,two)
                        for x,y in zip(one['rows'],two['rows']):assert x['self_load_physics']==y['self_load_physics']
                        if mode=='v52':
                            assert one['actions'].tobytes()==saved[step:].tobytes()
                            for now,old in zip(one['rows'],original[cid][step:]):assert np.array_equal(now['qpos'],old['qpos']) and np.array_equal(now['qvel'],old['qvel'])
                        folder=OUT/f'{cid}-{step}--{mode}';store_rollout(folder,one)
                        report=score(original[cid][:step]+one['rows'],case,suite)
                        report.update(case_id=cid,start_control=step,mode=mode,repeat_exact=True,braking_state=events[step],state_sha256=state_sha,demonstration_eligible=mode=='base' and report['passed'],branch=str(folder.relative_to(ROOT)))
                        (folder/'branch-result.json').write_text(json.dumps(report,indent=2)+'\n');result['branches'].append(report)
                        result['unchanged_repeated_controls' if mode=='v52' else 'recovery_repeated_controls']+=len(one['rows'])*2
                        print(json.dumps({k:report[k] for k in ['case_id','start_control','mode','passed','failures','demonstration_eligible']}),flush=True)
            finally:w.close()
        result.update(complete=True,eligible_branches=sum(b['demonstration_eligible'] for b in result['branches']));assert binding()==frozen
    except BaseException as exc:result.update(exception=f'{type(exc).__name__}: {exc}');raise
    finally:
        result.update(elapsed_s=time.monotonic()-started,freeze_sha256=digest(FREEZE));(OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n');shutil.copy2(FREEZE,OUT/'freeze.json')
        for p in frozen['source_sha256']:
            target=OUT/'source'/p;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,target)
        seal(OUT)
    print(json.dumps({k:v for k,v in result.items() if k!='branches'}),flush=True)
if __name__=='__main__':main()
