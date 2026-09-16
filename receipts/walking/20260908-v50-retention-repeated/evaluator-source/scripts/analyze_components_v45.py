"""Verify retained controls and summarize the frozen four-pair intervention."""
import argparse
from collections import defaultdict
import gzip
import json
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.evaluate_laser import digest
from experiments.walking.component_pairs_v45 import PAIRS,FLAT_CASES


def verify_manifest(folder):
    count=0
    for line in (folder/'SHA256SUMS').read_text().splitlines():
        sha,name=line.split('  ',1);p=(folder/name).resolve()
        if not p.is_relative_to(folder.resolve()) or digest(p)!=sha:raise ValueError('receipt drift: '+str(p))
        count+=1
    return count


def poses(folder, selected):
    import numpy as np
    p=folder/'trajectory.jsonl.gz'
    if not p.exists():p=folder/'trajectory.jsonl'
    opener=gzip.open if p.suffix=='.gz' else open
    result=defaultdict(list)
    with opener(p,'rt') as f:
        for line in f:
            r=json.loads(line)
            if selected is None or r['case_id'] in selected:result[r['case_id']].append(r['qpos'])
    return {k:np.asarray(v,np.float64) for k,v in result.items()}


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    import numpy as np
    from microduck.constants import JOINT_NAMES
    a.output.mkdir(parents=True,exist_ok=False)
    comparisons={};manifests={};controls={}
    for pair in PAIRS:
        part={}
        for bank,filename in [('flat','evaluation.json'),('endurance','probe.json')]:
            folder=ROOT/f'receipts/walking/20260907-v45-{pair}-{bank}'
            manifests[str(folder.relative_to(ROOT))]=verify_manifest(folder)
            r=json.loads((folder/filename).read_text())
            if r['pair']!=pair:raise ValueError('pair label mismatch')
            if bank=='endurance' and not r['complete']:raise ValueError('incomplete evaluation')
            part[bank]={'passed':r.get('passed_cases',r.get('passed_sessions')),
                'total':r.get('total_cases',r.get('total_sessions')),'cases':r['case_reports']}
            if bank=='endurance':part[bank]['sessions']=r['session_reports']
            if pair in ('original','joint-v44'):
                name={'original':{'flat':'20260906-v30-flat-regression','endurance':'20260906-v30-heading-endurance'},
                      'joint-v44':{'flat':'20260907-v44-sequence-flat','endurance':'20260907-v44-sequence-endurance'}}[pair][bank]
                original=ROOT/'receipts/walking'/name;verify_manifest(original)
                action_rows=0
                for path in folder.glob('*-actions-float32.npy'):
                    x,y=np.load(path),np.load(original/path.name)
                    if x.shape!=y.shape or x.dtype!=y.dtype or x.tobytes()!=y.tobytes():raise ValueError('original action tensor bytes differ: '+path.name)
                    action_rows+=len(x)
                current=poses(folder,FLAT_CASES if bank=='flat' else None)
                expected=poses(original,FLAT_CASES if bank=='flat' else None)
                if current.keys()!=expected.keys():raise ValueError('control case set mismatch')
                for case in current:
                    if current[case].shape!=expected[case].shape or not np.array_equal(current[case],expected[case]):raise ValueError('control pose mismatch: '+case)
                controls[pair+'-'+bank]=dict(action_rows=action_rows,actual_action_tensor_bytes_identical=True,
                    numeric_qpos_exact=True,pose_rows=sum(len(v) for v in current.values()))
        comparisons[pair]=part
    # Role-resolved first case occupancy supplements, never replaces, original gates.
    phase={}
    for pair in PAIRS:
        folder=ROOT/f'receipts/walking/20260907-v45-{pair}-flat'
        counts=defaultdict(lambda:np.zeros(2,int))
        with gzip.open(folder/'trajectory.jsonl.gz','rt') as f:
            for line in f:
                r=json.loads(line)
                if r['case_id']=='nominal-20-20ms--forward-08' and r['time_s']>=1:
                    v=counts[r['actor_mode']];v[1]+=1;v[0]+=r['joint_limit_margin_fraction'][JOINT_NAMES.index('right_knee')]<.05
        phase[pair]={k:dict(controls=int(v[1]),near_limit_controls=int(v[0]),fraction=float(v[0]/v[1])) for k,v in counts.items()}
    source_freezes={}
    for path in (ROOT/'experiments/walking').glob('component-*-freeze-v45.json'):
        f=json.loads(path.read_text())
        for name,sha in f['source_sha256'].items():
            if digest(ROOT/name)!=sha:raise ValueError('source freeze drift: '+name)
        source_freezes[path.name]=len(f['source_sha256'])
    report=dict(complete=True,comparisons=comparisons,controls=controls,phase_knee_occupancy=phase,
        verified_manifest_files=manifests,verified_source_freezes=source_freezes,
        physical_transfer_validated=False,reserved_opened=False)
    (a.output/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
    shutil.copy2(__file__,a.output/'analyze_components_v45.py')
    (a.output/'SHA256SUMS').write_text(''.join(f'{digest(f)}  {f.name}\n' for f in sorted(a.output.iterdir()) if f.is_file() and f.name!='SHA256SUMS'))
    for pair,part in comparisons.items():
        print(pair,'flat',part['flat']['passed'],'/2','diagnostic',part['endurance']['passed'],'/4',
            [(r['session_id'],r['passed'],round(r['simulated_duration_s'],2)) for r in part['endurance']['sessions']])
    print('Exact reproduced controls:',sum(v['action_rows'] for v in controls.values()))
    print('First-case knee phases:',json.dumps(phase))

if __name__=='__main__':main()
