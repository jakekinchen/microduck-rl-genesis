"""Verify all retained V56 feasibility actions and the exact zero-offset control."""
import gzip
import json
from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.walking.posture_v56 import digest
from scripts.analyze_components_v45 import verify_manifest
from evaluator.core import OnnxPolicy

def main():
    base=ROOT/'receipts/walking/20260916-v56-posture-feasibility'
    assisted=ROOT/'receipts/walking/20260916-v56-head-diagnostic'
    reports=[];rows_by_case={}
    inference=json.loads((ROOT/'evaluator/config-v1.json').read_text())['inference']
    for folder,count in [(base,12),(assisted,18)]:
        verify_manifest(folder)
        cfg=json.loads((folder/'protocol.json').read_text())
        result=json.loads((folder/'feasibility.json').read_text())
        assert result['complete'] and len(result['reports'])==count
        assert digest(folder/'protocol.json')==result['protocol_sha256']
        for path,sha in cfg['sources'].items():assert digest(ROOT/path)==sha,path
        total=loads=0
        for case in result['reports']:
            name=case['case'];role=name.split('-motor')[0]
            actor_cfg=cfg['policies'][role]
            actor_path=ROOT/actor_cfg['folder']/actor_cfg['actor']
            assert digest(actor_path)==actor_cfg['sha256']
            actor=OnnxPolicy(actor_path,inference)
            with gzip.open(folder/(name+'.jsonl.gz'),'rt') as f:rows=[json.loads(line) for line in f]
            actions=np.load(folder/(name+'-actions-float32.npy'))
            assert len(rows)==500 and actions.shape==(500,14) and actions.dtype==np.float32
            for tick,(row,action) in enumerate(zip(rows,actions)):
                raw,_=actor.infer(np.asarray(row['actor_observation'],np.float32)[None])
                if folder==assisted:
                    assert raw[0].tobytes()==np.asarray(row['raw_actor_action'],np.float32).tobytes()
                    expected=np.float32(actor_cfg['head_pitch_offset_rad']*min(1.,tick/50.))
                    assert expected==row['head_pitch_offset_rad']
                    raw[0,6]+=expected
                assert raw[0].tobytes()==action.tobytes()
                assert len(row['self_load_physics'])==4
                assert abs(row['time_s']-(tick+1)*.02)<1e-9
            pitch=np.degrees(np.arcsin(np.clip(np.abs(np.asarray([r['face_world'] for r in rows[-100:]])[:,2]),0,1))).mean()
            assert abs(pitch-case['metrics']['mean_final_face_pitch_deg'])<1e-10
            assert not any(r['fell'] for r in rows)
            assert case['passed']==(not case['failures'])
            rows_by_case[(folder.name,name)]=(rows,actions)
            total+=len(rows);loads+=sum(len(r['self_load_physics']) for r in rows)
        reports.append(dict(receipt=str(folder.relative_to(ROOT)),cases=count,verified_actions=total,
            physics_load_samples=loads,manifest_sha256=digest(folder/'SHA256SUMS')))
    for motor in [0,4,6]:
        for yaw in [0.0,.12]:
            left,la=rows_by_case[(base.name,f'shared-motor{motor}-yaw{yaw}')]
            right,ra=rows_by_case[(assisted.name,f'zero-motor{motor}-yaw{yaw}')]
            assert la.tobytes()==ra.tobytes()
            for a,b in zip(left,right):
                for key in ['qpos','qvel','actor_observation','self_load_physics']:assert a[key]==b[key]
    out=ROOT/'experiments/walking/posture-feasibility-review-v56/verification.json'
    record=dict(complete=True,integrity_passed=True,reports=reports,zero_offset_exact_controls=3000,
        script_sha256=digest(Path(__file__)),training_allowed=False,
        decision='No unchanged or fixed-offset recipe passed every declared25-degree case. Paired training remains unlaunched; this bounded negative does not prove physical or learning infeasibility.')
    with out.open('x') as f:json.dump(record,f,indent=2);f.write('\n')
    print(json.dumps(record))

if __name__=='__main__':main()
