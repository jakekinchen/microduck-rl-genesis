"""Offline V50 rehearsal label alignment and original ONNX parity."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.evaluate_laser import digest
from scripts.analyze_components_v45 import verify_manifest

def main():
    import numpy as np
    import onnxruntime as ort
    folder=ROOT/'experiments/walking/retention-replay-v50'
    verify_manifest(folder)
    data=np.load(folder/'replay.npz')
    obs,act=data['observations'],data['actions']
    assert obs.dtype==act.dtype==np.float32 and obs.shape==(len(act),61) and act.shape[1]==14
    assert np.isfinite(obs).all() and np.isfinite(act).all() and (obs[:,48:51]!=0).any(1).all()
    options=ort.SessionOptions();options.intra_op_num_threads=1;options.inter_op_num_threads=1
    policy=ROOT/'receipts/walking/20260906-v30-flat-regression/policy.onnx'
    session=ort.InferenceSession(str(policy),sess_options=options,providers=['CPUExecutionProvider'])
    errors=[]
    for i in range(len(obs)):
        inferred=session.run(None,{session.get_inputs()[0].name:obs[i:i+1]})[0][0]
        assert inferred.tobytes()==act[i].tobytes(),f'original tensor mismatch row {i}'
        errors.append(float(abs(inferred-act[i]).max()))
    out=ROOT/'receipts/walking/20260908-v50-replay-parity';out.mkdir(exist_ok=False)
    report=dict(passed=True,rows=len(obs),exact_original_policy_action_bytes=True,maximum_error=max(errors),
        policy_sha256=digest(policy),replay_sha256=digest(folder/'replay.npz'),provenance=json.loads((folder/'provenance.json').read_text()))
    (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'source.py').write_bytes(Path(__file__).read_bytes())
    (out/'SHA256SUMS').write_text(''.join(f'{digest(p)}  {p.name}\n' for p in sorted(out.iterdir()) if p.name!='SHA256SUMS'))
    print(json.dumps({k:report[k] for k in ['passed','rows','exact_original_policy_action_bytes']}))
if __name__=='__main__':main()
