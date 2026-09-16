"""Offline closure of V44 source, stored training data and component lineage."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.evaluate_laser import digest


def manifest(folder):
    count=0
    for line in (folder/'SHA256SUMS').read_text().splitlines():
        sha,name=line.split('  ',1);path=(folder/name).resolve()
        if not path.is_relative_to(folder.resolve()) or digest(path)!=sha:raise ValueError('receipt drift: '+str(path))
        count+=1
    return count


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    import numpy as np
    import torch
    from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
    from scripts.train_native_sequence_v44 import binding,FREEZE,PARENTS
    from experiments.walking.native_candidate_v44 import candidate_sha,RUN
    assert binding()==json.loads(FREEZE.read_text())
    walk_sha,stand_sha=candidate_sha()
    frozen_counts={}
    for path in sorted((ROOT/'experiments/walking').glob('native-sequence*freeze-v44*.json')):
        frozen=json.loads(path.read_text())
        for name,sha in frozen['source_sha256'].items():
            if digest(ROOT/name)!=sha:raise ValueError('freeze drift: '+name)
        frozen_counts[path.name]=len(frozen['source_sha256'])
    folder=ROOT/'logs'/RUN;record=json.loads((folder/'run.json').read_text())
    joint=torch.load(folder/record['checkpoint'],map_location='cpu',weights_only=True)['actor_state_dict']
    actor_reports={}
    for role,parent_run in PARENTS.items():
        parent_folder=ROOT/'logs'/parent_run;parent=json.loads((parent_folder/'run.json').read_text())
        parent_state=torch.load(parent_folder/parent['checkpoint'],map_location='cpu',weights_only=True)['actor_state_dict']
        component_folder=ROOT/'logs'/(RUN+'-'+role)
        component=json.loads((component_folder/'run.json').read_text())
        state=torch.load(component_folder/component['checkpoint'],map_location='cpu',weights_only=True)['actor_state_dict']
        for key,value in state.items():
            if not torch.isfinite(value).all() or not torch.equal(value,joint[role+'.'+key]):raise ValueError('component split differs: '+key)
            if key.startswith('obs_normalizer.') and not torch.equal(value,parent_state[key]):raise ValueError('normalizer drift')
        changes={key:float((v-parent_state[key]).abs().max()) for key,v in state.items() if key.startswith('mlp.')}
        if not any(changes.values()):raise ValueError('actor did not learn')
        actor_reports[role]=dict(exact_joint_component=True,parent_normalizer_unchanged=True,finite=True,
            maximum_mlp_parameter_change=max(changes.values()),checkpoint_sha256=component['checkpoint_sha256'])
    data_reports={}
    for role,dim in [('observation',61),('action',14)]:
        h=hashlib.sha256();size=0
        with gzip.open(folder/('all-'+role+'s-float32.bin.gz'),'rb') as f:
            while data:=f.read(1024*1024):
                if len(data)%4 or not np.isfinite(np.frombuffer(data,dtype='<f4')).all():raise ValueError('nonfinite recorded '+role)
                h.update(data);size+=len(data)
        if size!=record['new_transitions']*dim*4 or h.hexdigest()!=record['final_coverage'][role+'_raw_sha256']:raise ValueError('recorded byte identity/shape mismatch')
        data_reports[role]=dict(bytes=size,rows=size//(dim*4),raw_sha256=h.hexdigest(),all_finite=True)
    switches=np.zeros((4,2),int);switch_rows=0
    with gzip.open(folder/'handoff-histories.jsonl.gz','rt') as f:
        for line in f:
            row=json.loads(line);b=row['bucket'];kind=0 if row['direction']=='walk-to-stand' else 1
            switches[b,kind]+=1;switch_rows+=1
            for name in ['observation','qpos','qvel','motor_fifo','previous_torque','q_target','sensors','last_action','damping','friction']:
                if not np.isfinite(np.asarray(row[name])).all():raise ValueError('nonfinite switch history')
            if bool(np.all(np.asarray(row['observation'])[48:51]==0))!=(kind==0):raise ValueError('switch role mismatch')
    if switches.tolist()!=record['final_coverage']['switches_walk_to_stand_and_reverse']:raise ValueError('switch coverage drift')
    events=EventAccumulator(str(folder),size_guidance={'scalars':0});events.Reload()
    scalar_count=0
    for tag in events.Tags()['scalars']:
        rows=events.Scalars(tag);scalar_count+=len(rows)
        if not all(np.isfinite(row.value) for row in rows):raise ValueError('nonfinite training scalar: '+tag)
    if scalar_count < 500: raise ValueError("missing learning scalar coverage")
    receipts={}
    for name in ['20260907-v44-sequence-conformance','20260907-v44-sequence-flat',
                 '20260907-v44-sequence-repeated','20260907-v44-sequence-endurance','20260907-v44-sequence-surfaces']:
        receipts[name]=manifest(ROOT/'receipts/walking'/name)
    for name,sha in record['source_sha256'].items():
        if digest(folder/'source'/name)!=sha:raise ValueError('training source retention drift')
    a.output.mkdir(parents=True,exist_ok=False)
    report=dict(complete=True,source_freezes=frozen_counts,receipt_manifests=receipts,
        actor_components=actor_reports,stored_training=data_reports,switch_history_rows=switch_rows,
        scalar_samples=scalar_count,all_training_scalars_finite=True,training_coverage=record['final_coverage'],
        claim_boundary='Evidence integrity and bounded learning completion, not behavior acceptance or calibrated physical transfer.')
    (a.output/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    shutil.copy2(Path(__file__),a.output/'verify_native_sequence_v44.py')
    for name in ['run.json',record['checkpoint'],'all-observations-float32.bin.gz','all-actions-float32.bin.gz','handoff-histories.jsonl.gz']:
        # Hard links retain exact evidence without duplicating hundreds of MB.
        (a.output/name).hardlink_to(folder/name)
    for file in folder.glob('events.out.tfevents.*'):(a.output/file.name).hardlink_to(file)
    (a.output/'SHA256SUMS').write_text(''.join(f'{digest(f)}  {f.relative_to(a.output)}\n' for f in sorted(a.output.rglob('*')) if f.is_file() and f.name!='SHA256SUMS'))
    print(json.dumps(dict(complete=True,transitions=record['new_transitions'],switch_rows=switch_rows,scalar_samples=scalar_count)))

if __name__=='__main__':main()
