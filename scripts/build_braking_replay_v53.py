"""Retain successful stops and verified recovery states; all examples exposed."""
import gzip,json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.walking.recovery_v49 import digest,manifest,seal

def main():
    out=ROOT/'experiments/walking/braking-replay-v53';old=ROOT/'experiments/walking/braking-replay-v52';collection=ROOT/'receipts/walking/20260908-v53-retention-collection';downhill=ROOT/'receipts/walking/20260908-v52-braking-endurance'
    for p in [old,collection,downhill]:manifest(p)
    sources=[];obs=[];target=[];positive=[]
    # Keep the exact legacy retention bank, replacing mixed V51 knot labels.
    with np.load(old/'replay.npz') as data:
        keep=~data['positive'];x=data['observations'][keep];y=data['residuals'][keep]
    assert len(x)==11625 and not y.any();obs.extend(x);target.extend(y);positive.extend([False]*len(x));sources.append(dict(source=str(old.relative_to(ROOT)),kind='original_zero_labels',rows=len(x),manifest_sha256=digest(old/'SHA256SUMS')))
    import onnxruntime as ort
    options=ort.SessionOptions();options.intra_op_num_threads=1;options.inter_op_num_threads=1
    policies=[ort.InferenceSession(str(p),sess_options=options,providers=['CPUExecutionProvider']) for p in [downhill/'policy.onnx',downhill/'standing/policy.onnx']]
    reports=json.loads((downhill/'probe.json').read_text());allowed={'mean_abs_yaw_error_rad_s','endurance:tracking_bucket_2:mean_abs_yaw_error_rad_s'}
    accepted={c['case_id'] for c in reports['case_reports'] if c['case_id'].startswith('downhill') and c['observed_duration_s']==18 and not (set(c['failures'])-allowed)};assert len(accepted)==4
    n=0
    with gzip.open(downhill/'trajectory.jsonl.gz','rt') as f:
        for line in f:
            row=json.loads(line)
            if row['case_id'] in accepted and row['braking_active']:
                x=np.asarray(row['actor_observation'],np.float32);actor=policies[int(row['actor_mode']=='standing')];base=actor.run(None,{actor.get_inputs()[0].name:x[None]})[0][0];delta=np.asarray(row['action_rad'],np.float32)-base
                obs.append(x);target.append(delta);positive.append(True);n+=1
    assert n==500;sources.append(dict(source=str(downhill.relative_to(ROOT)),kind='actual_successful_downhill_brakes_yaw_still_failed',rows=n,manifest_sha256=digest(downhill/'SHA256SUMS')))
    collected=json.loads((collection/'result.json').read_text());assert collected['complete'] and collected['eligible_branches']>0
    for branch in collected['branches']:
        if not branch['demonstration_eligible']:continue
        assert branch['mode']=='base' and branch['passed'] and not branch['failures'] and branch['observed_controls']==900 and branch['repeat_exact']
        folder=ROOT/branch['branch'];count=775-branch['start_control'];x=np.load(folder/'observations-float32.npy')[:count];actions=np.load(folder/'actions-float32.npy')[:count]
        for row,action in zip(x,actions):
            actor=policies[int((row[48:51]==0).all())];base=actor.run(None,{actor.get_inputs()[0].name:row[None]})[0][0];assert action.tobytes()==base.tobytes()
        obs.extend(x);target.extend(np.zeros((count,14),np.float32));positive.extend([False]*count);sources.append(dict(source=branch['branch'],kind='verified_learner_state_recovery_zero',rows=count,branch_result_sha256=digest(folder/'branch-result.json'),observations_sha256=digest(folder/'observations-float32.npy'),actions_sha256=digest(folder/'actions-float32.npy')))
    out.mkdir(exist_ok=False);np.savez_compressed(out/'replay.npz',observations=np.asarray(obs,np.float32),residuals=np.asarray(target,np.float32),positive=np.asarray(positive,bool))
    r=dict(sources=sources,positive_rows=sum(positive),negative_rows=len(positive)-sum(positive),collection_manifest_sha256=digest(collection/'SHA256SUMS'),boundary='All exposed; complete branch acceptance required for new zero labels. Downhill yaw failure retained.')
    (out/'provenance.json').write_text(json.dumps(r,indent=2)+'\n');seal(out);print({k:v for k,v in r.items() if k!='sources'})
if __name__=='__main__':main()
