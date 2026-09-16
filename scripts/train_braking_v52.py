"""One frozen supervised distillation of braking demonstrations; not PPO."""
import json,sys,time,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.walking.recovery_v49 import digest,seal
FREEZE=ROOT/'experiments/walking/braking-freeze-v52.json'
EXTRA=['microduck/braking_v52.py','scripts/train_braking_v52.py','scripts/build_braking_replay_v52.py','tests/test_braking_v52.py','experiments/walking/BRAKING-DISTILLATION-v52.md','experiments/walking/braking-replay-v52/replay.npz','experiments/walking/braking-replay-v52/provenance.json']+[f'scripts/evaluate_braking_{b}_v52.py' for b in ['flat','endurance','surfaces']]
def binding():
    f=json.loads((ROOT/'experiments/walking/native-retention-freeze-v50.json').read_text())['source_sha256'].copy()
    for p in EXTRA:f[p]=digest(ROOT/p)
    for p,h in f.items():assert digest(ROOT/p)==h,p
    return dict(schema='microduck.braking-freeze/v52',source_sha256=f,seed=26090852,steps=2000,batch_size=256,positive_per_batch=128)
def main():
    frozen=binding()
    if '--freeze' in sys.argv:
        with FREEZE.open('x') as f:json.dump(frozen,f,indent=2);f.write('\n')
        return
    assert frozen==json.loads(FREEZE.read_text())
    assert shutil.disk_usage(ROOT).free>3_000_000_000
    import numpy as np,torch
    from microduck.braking_v52 import BrakeNet,RUN
    import onnxruntime as ort
    torch.set_num_threads(1);torch.manual_seed(26090852);np.random.seed(26090852)
    RUN.mkdir(exist_ok=False);started=time.monotonic();record=dict(status='running',steps=0,source_sha256=frozen['source_sha256'],freeze_sha256=digest(FREEZE),method='supervised residual distillation; no new RL transitions',policy_activated=False)
    (RUN/'run.json').write_text(json.dumps(record,indent=2)+'\n')
    try:
        with np.load(ROOT/'experiments/walking/braking-replay-v52/replay.npz') as data:
            x=torch.from_numpy(data['observations']);y=torch.from_numpy(data['residuals']);positive=torch.from_numpy(data['positive'])
        model=BrakeNet(x.mean(0),x.std(0));optimizer=torch.optim.Adam(model.parameters(),lr=3e-4)
        ids=[torch.where(positive)[0],torch.where(~positive)[0]];losses=[]
        with (RUN/'learning.jsonl').open('w') as trace:
            for step in range(2000):
                selected=torch.cat([group[torch.randint(len(group),(128,))] for group in ids]);prediction=model(x[selected])
                loss=((prediction-y[selected])/.03).square().mean();assert torch.isfinite(loss)
                optimizer.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.);optimizer.step()
                losses.append(float(loss.detach()));record['steps']=step+1
                trace.write(json.dumps(dict(step=step,loss=losses[-1]))+'\n')
        model.eval();torch.save(model.state_dict(),RUN/'model.pt')
        torch.onnx.export(model,torch.zeros(1,61),str(RUN/'policy.onnx'),input_names=['obs'],output_names=['residual'],opset_version=17,dynamo=False)
        options=ort.SessionOptions();options.intra_op_num_threads=1;options.inter_op_num_threads=1
        sess=ort.InferenceSession(str(RUN/'policy.onnx'),sess_options=options,providers=['CPUExecutionProvider'])
        with torch.no_grad():
            fitted=model(x).numpy();random=torch.randn(1000,61);reference=model(random).numpy()
        error=0.
        for inputs,target in [(x.numpy(),fitted),(random.numpy(),reference)]:
            for obs,expected in zip(inputs,target):error=max(error,float(abs(sess.run(None,{'obs':obs[None]})[0][0]-expected).max()))
        assert error<1e-4 and np.isfinite(fitted).all() and binding()==frozen
        record.update(status='completed',policy_sha256=digest(RUN/'policy.onnx'),checkpoint_sha256=digest(RUN/'model.pt'),maximum_export_error=error,positive_rows=len(ids[0]),negative_rows=len(ids[1]),sample_draws=512000,new_rl_transitions=0,rmse_positive=float(np.sqrt(np.mean((fitted[positive]-y.numpy()[positive])**2))),rmse_retention=float(np.sqrt(np.mean(fitted[~positive]**2))))
    except BaseException as exc:record.update(status='failed',error=f'{type(exc).__name__}: {exc}');raise
    finally:
        record['elapsed_s']=time.monotonic()-started;(RUN/'run.json').write_text(json.dumps(record,indent=2)+'\n')
        for p in frozen['source_sha256']:
            dst=RUN/'source'/p;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,dst)
        seal(RUN)
    print(json.dumps({k:v for k,v in record.items() if k!='source_sha256'}))
if __name__=='__main__':main()
