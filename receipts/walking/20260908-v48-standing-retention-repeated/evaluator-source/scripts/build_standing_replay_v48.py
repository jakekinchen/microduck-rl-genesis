"""Retain original passing actor inputs/actions; never synthesize action labels."""
import gzip
import json
from pathlib import Path
import sys
from collections import defaultdict
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.evaluate_laser import digest
from scripts.analyze_components_v45 import verify_manifest

out=ROOT/'experiments/walking/standing-replay-v48'
if __name__=='__main__':
    out.mkdir(exist_ok=False)
    inputs=[];targets=[];reports=[]
    for name in ['20260906-v30-flat-regression','20260906-v30-repeated-regression-r2','20260906-v30-heading-endurance']:
        folder=ROOT/'receipts/walking'/name;verify_manifest(folder)
        report_path=folder/('probe.json' if name.endswith('heading-endurance') else 'evaluation.json')
        report=json.loads(report_path.read_text())
        allowed={r['case_id'] for r in report['case_reports'] if r['passed']}
        if name.endswith('heading-endurance'):
            assert report['complete'] and len(allowed)==20
        elif report['passed_cases']!=report['total_cases']:raise ValueError('passing original bank required')
        path=folder/'trajectory.jsonl.gz'
        if not path.exists():path=folder/'trajectory.jsonl'
        opener=gzip.open if path.suffix=='.gz' else open
        indices=defaultdict(int);actions={p.name.removesuffix('-actions-float32.npy'):np.load(p) for p in folder.glob('*-actions-float32.npy')}
        count=0
        with opener(path,'rt') as f:
            for line in f:
                row=json.loads(line);case=row['case_id'];i=indices[case];indices[case]+=1
                if row['actor_mode']!='standing' or case not in allowed:continue
                obs=np.asarray(row['actor_observation'],np.float32)
                if np.any(obs[48:51]) or not np.isfinite(obs).all():raise ValueError('invalid teacher input')
                inputs.append(obs);targets.append(actions[case][i]);count+=1
        for case,n in indices.items():
            if n!=len(actions[case]):raise ValueError('action/observation alignment')
        reports.append(dict(receipt=name,rows=count,manifest_sha256=digest(folder/'SHA256SUMS'),trace_sha256=digest(path)))
    np.savez_compressed(out/'replay.npz',observations=np.asarray(inputs,np.float32),actions=np.asarray(targets,np.float32))
    (out/'provenance.json').write_text(json.dumps(dict(rows=len(inputs),sources=reports,split='exposed baseline rehearsal; not held out',action_labels='original stored float32 policy outputs'),indent=2)+'\n')
    (out/'SHA256SUMS').write_text(''.join(f'{digest(p)}  {p.name}\n' for p in sorted(out.iterdir()) if p.is_file() and p.name!='SHA256SUMS'))
    print(json.dumps(dict(rows=len(inputs),stored_bytes=(out/'replay.npz').stat().st_size)))
