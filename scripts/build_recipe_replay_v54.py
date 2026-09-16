"""Both modes from verified, wholly passing original V30 trajectories."""
import gzip
import json
from collections import defaultdict
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiments.walking.recipe_v54 import new_output, write_manifest, digest
from scripts.analyze_components_v45 import verify_manifest


def main():
    out=new_output('experiments/walking/recipe-replay-v54')
    inputs, targets, case_ids, sources, cases = [], [], [], [], []
    for name in ['20260906-v30-flat-regression','20260906-v30-repeated-regression-r2',
            '20260906-v30-heading-endurance','20260906-v30-surface-baseline']:
        folder=ROOT/'receipts/walking'/name
        verify_manifest(folder)
        session_bank=name.endswith(('heading-endurance','surface-baseline'))
        report=json.loads((folder/('probe.json' if session_bank else 'evaluation.json')).read_text())
        allowed={r['case_id'] for r in report['case_reports'] if r['passed']}
        if session_bank:
            assert report['complete']
            sessions={r['session_id'] for r in report['session_reports'] if r['passed']}
            allowed={c for c in allowed if c.split('--window-')[0] in sessions}
            assert len(sessions)==(2 if name.endswith('heading-endurance') else 5)
        else:
            assert report['passed_cases']==report['total_cases']
        path=folder/'trajectory.jsonl.gz'
        if not path.exists(): path=folder/'trajectory.jsonl'
        opener=gzip.open if path.suffix=='.gz' else open
        counters=defaultdict(int)
        actions={p.name.removesuffix('-actions-float32.npy'):np.load(p) for p in folder.glob('*-actions-float32.npy')}
        identifiers={case:len(cases)+i for i,case in enumerate(sorted(allowed))}
        cases += [name+'/'+c for c in sorted(allowed)]
        modes=defaultdict(int)
        with opener(path,'rt') as stream:
            for line in stream:
                row=json.loads(line);case=row['case_id'];index=counters[case];counters[case]+=1
                if case not in allowed: continue
                obs=np.asarray(row['actor_observation'],np.float32)
                is_stand=bool(np.all(obs[48:51]==0))
                assert is_stand==(row['actor_mode']=='standing') and np.isfinite(obs).all()
                inputs.append(obs);targets.append(actions[case][index]);case_ids.append(identifiers[case])
                modes[row['actor_mode']] += 1
        assert all(n==len(actions[case]) for case,n in counters.items())
        sources.append(dict(receipt=name,allowed_cases=sorted(allowed),modes=dict(modes),
            manifest_sha256=digest(folder/'SHA256SUMS'),trace_sha256=digest(path)))
    np.savez_compressed(out/'replay.npz',observations=np.asarray(inputs,np.float32),
        actions=np.asarray(targets,np.float32),case_ids=np.asarray(case_ids,np.int32))
    (out/'provenance.json').write_text(json.dumps(dict(rows=len(inputs),cases=cases,sources=sources,
        split='exposed retained V30 rehearsal, both actual modes; not held out',
        labels='original stored float32 action tensors; whole passing sessions only'),indent=2)+'\n')
    write_manifest(out)
    print(json.dumps(dict(rows=len(inputs),cases=len(cases),sources=sources)),flush=True)


if __name__=='__main__': main()
