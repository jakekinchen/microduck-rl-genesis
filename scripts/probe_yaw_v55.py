"""V55 actual-step conformance under the two frozen reward coefficients."""
import json,hashlib,gzip,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
import torch
from experiments.walking.yaw_v55 import new_output,write_manifest,digest,FREEZE
from scripts.train_yaw_v55 import require_freeze
from scripts.analyze_components_v45 import verify_manifest
from microduck.native_sequence_env_v54 import NativeSequenceEnv as Original,BUCKETS
from microduck.native_yaw_env_v55 import NativeSequenceEnv as Candidate
from evaluator.core import OnnxPolicy

def main():
    require_freeze();torch.set_num_threads(1)
    old=ROOT/'receipts/walking/20260909-v54-conformance';verify_manifest(old)
    prior=json.loads((old/'probe.json').read_text())
    assert prior['complete'] and prior['passed'] and len(prior['reports'])==72
    out=new_output('receipts/walking/20260912-v55-conformance')
    config=json.loads((ROOT/'evaluator/config-v1.json').read_text())['inference']
    policy=OnnxPolicy(ROOT/'receipts/walking/20260909-v54-shared-flat/policy.onnx',config)
    reports=[]
    for weight in (3.,6.):
        aout=out/f'weight{int(weight)}-original';bout=out/f'weight{int(weight)}-candidate'
        aout.mkdir();bout.mkdir()
        a=Original(24,26091255,aout);b=Candidate(24,26091255,bout,yaw_weight=weight)
        h=hashlib.sha256()
        try:
            for tick in range(1200):
                obs=a.get_observations()['policy'].numpy()
                assert obs.tobytes()==b.get_observations()['policy'].numpy().tobytes()
                action=np.concatenate([policy.infer(row[None])[0] for row in obs])
                ao,ar,ad,_=a.step(torch.from_numpy(action));bo,br,bd,_=b.step(torch.from_numpy(action))
                assert ao['policy'].numpy().tobytes()==bo['policy'].numpy().tobytes()
                assert ad.numpy().tobytes()==bd.numpy().tobytes()
                if weight==3.: assert ar.numpy().tobytes()==br.numpy().tobytes()
                for wa,wb in zip(a.worlds,b.worlds):
                    for field in ('qpos','qvel','ctrl','qfrc_constraint','qfrc_actuator','efc_force'):
                        left,right=getattr(wa.core.data,field),getattr(wb.core.data,field)
                        assert left.tobytes()==right.tobytes(),field
                        h.update(left.tobytes())
                if (tick+1)%300==0: print(json.dumps(dict(weight=weight,controls=tick+1)),flush=True)
            ac,bc=a.coverage(),b.coverage();assert ac==bc
            assert all(n>=2 for n in ac['reset_counts'])
        finally: a.close();b.close()
        with gzip.open(bout/'all-reward-components-float32.bin.gz','rb') as f:
            r=np.frombuffer(f.read(),dtype='<f4').reshape(1200,24,6)
        active=np.array([cell[1]>0 for cell in BUCKETS])[None,:] & (r[:,:,5]==0)
        expected=np.where(active,weight*np.abs(r[:,:,0]-r[:,:,1])/.20,0)
        np.testing.assert_allclose(r[:,:,2],expected,rtol=2e-6,atol=2e-6)
        np.testing.assert_allclose(r[:,:,4],r[:,:,3]-.02*r[:,:,2],rtol=2e-6,atol=2e-6)
        reports.append(dict(weight=weight,paired_controls=1200*24,physical_sha256=h.hexdigest(),
            identical_observations_actions_physics_and_resets=True,reward_verified=True,coverage=bc))
    require_freeze()
    (out/'probe.json').write_text(json.dumps(dict(complete=True,passed=True,
        freeze_sha256=digest(FREEZE),prior_conformance_manifest_sha256=digest(old/'SHA256SUMS'),
        reports=reports,boundary='Actual native step/reward/reset conformance, not behavior acceptance.'),indent=2)+'\n')
    write_manifest(out)
if __name__=='__main__': main()
