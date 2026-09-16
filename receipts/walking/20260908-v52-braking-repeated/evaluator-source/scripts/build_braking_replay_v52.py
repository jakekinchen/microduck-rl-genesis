"""Build exposed state-conditioned braking labels from admitted V51 recoveries."""
import gzip,json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.walking.recovery_v51 import digest,manifest,seal,CAPTURE,COMPARE,SEARCH
from evaluator.core import OnnxPolicy

def main():
    import onnxruntime as ort
    for f in [CAPTURE,COMPARE,SEARCH]:manifest(f)
    decisions=json.loads((SEARCH/'result.json').read_text());assert decisions['learning_eligible']
    obs=[];actions=[];positive=[];provenance=[]
    base=ROOT/'receipts/walking/20260908-v50-retention-flat'
    options=ort.SessionOptions();options.intra_op_num_threads=1;options.inter_op_num_threads=1
    sessions=[ort.InferenceSession(str(p),sess_options=options,providers=['CPUExecutionProvider']) for p in [base/'policy.onnx',base/'standing/policy.onnx']]
    for state in decisions['states']:
        folder=(COMPARE/(state['state_id']+'--'+state['selected_comparison']) if state.get('search_skipped') else SEARCH/(state['state_id']+'--retargeted'))
        x=np.load(folder/'observations-float32.npy')[:125];y=np.load(folder/'actions-float32.npy')[:125];assert len(x)==125
        residual=[]
        for row,act in zip(x,y):
            actor=sessions[int((row[48:51]==0).all())];baseline=actor.run(None,{actor.get_inputs()[0].name:row[None]})[0][0]
            residual.append(act-baseline)
        obs.extend(x);actions.extend(residual);positive.extend([True]*len(x));provenance.append(dict(source=str(folder.relative_to(ROOT)),rows=len(x),kind='eligible_recovery',observations_sha256=digest(folder/'observations-float32.npy'),actions_sha256=digest(folder/'actions-float32.npy')))
    for suffix in ['flat','repeated','endurance','surfaces']:
        folder=ROOT/f'receipts/walking/20260908-v50-retention-{suffix}';manifest(folder)
        report=json.loads((folder/('evaluation.json' if suffix in ['flat','repeated'] else 'probe.json')).read_text())
        allowed={c['case_id'] for c in report['case_reports'] if c['passed']}
        if suffix in ['endurance','surfaces']:
            passed={s['session_id'] for s in report['session_reports'] if s['passed']};allowed={c for c in allowed if c.split('--window-')[0] in passed}
        n=0
        with gzip.open(folder/'trajectory.jsonl.gz','rt') as f:
            for line in f:
                row=json.loads(line)
                if row['case_id'] in allowed and 13.<row['time_s']<=15.5:
                    obs.append(row['actor_observation']);actions.append(np.zeros(14,np.float32));positive.append(False);n+=1
        provenance.append(dict(source=str(folder.relative_to(ROOT)),rows=n,kind='passing_brake_retention',manifest_sha256=digest(folder/'SHA256SUMS')))
    out=ROOT/'experiments/walking/braking-replay-v52';out.mkdir(exist_ok=False)
    np.savez_compressed(out/'replay.npz',observations=np.asarray(obs,np.float32),residuals=np.asarray(actions,np.float32),positive=np.asarray(positive,bool))
    (out/'provenance.json').write_text(json.dumps(dict(positive_rows=sum(positive),negative_rows=len(positive)-sum(positive),sources=provenance,boundary='Exposed demonstrations and successful-brake retention, not held out.'),indent=2)+'\n');seal(out)
    print(dict(positive=sum(positive),negative=len(positive)-sum(positive)))
if __name__=='__main__':main()
