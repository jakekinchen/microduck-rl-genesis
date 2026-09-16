"""One preregistered hard-retention fit; no new RL transitions."""
import json,sys,time,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.walking.recovery_v49 import digest,manifest,seal
FREEZE=ROOT/'experiments/walking/braking-freeze-v53.json'
EXTRA=['microduck/braking_v53.py','scripts/train_braking_v53.py','scripts/build_braking_replay_v53.py','tests/test_braking_v53.py','experiments/walking/BRAKING-RETENTION-v53.md','experiments/walking/braking-replay-v53/replay.npz','experiments/walking/braking-replay-v53/provenance.json']+[f'scripts/evaluate_braking_{b}_v53.py' for b in ['flat','endurance','surfaces']]
PARENT=ROOT/'logs/braking-distill-20260908-v52'
def binding():
    f=json.loads((ROOT/'experiments/walking/native-retention-freeze-v50.json').read_text())['source_sha256'].copy()
    for p in EXTRA:f[p]=digest(ROOT/p)
    for p,h in f.items():assert digest(ROOT/p)==h,p
    manifest(PARENT)
    return dict(schema='microduck.braking-freeze/v53',source_sha256=f,parent_manifest_sha256=digest(PARENT/'SHA256SUMS'),parent_checkpoint_sha256=digest(PARENT/'model.pt'),seed=26090853,steps=8000,batch_size=384,positive_per_batch=128,random_zero_per_batch=128,hard_zero_per_batch=128,hard_pool_refresh_updates=50)
def main():
    frozen=binding()
    if '--freeze' in sys.argv:
        with FREEZE.open('x') as f:json.dump(frozen,f,indent=2);f.write('\n')
        return
    assert frozen==json.loads(FREEZE.read_text()) and shutil.disk_usage(ROOT).free>3_000_000_000
    import numpy as np,torch
    import onnxruntime as ort
    from microduck.braking_v53 import BrakeNet,RUN,retention_loss
    torch.set_num_threads(1);torch.manual_seed(26090853);np.random.seed(26090853)
    RUN.mkdir(exist_ok=False);started=time.monotonic();record=dict(status='running',steps=0,source_sha256=frozen['source_sha256'],freeze_sha256=digest(FREEZE),method='supervised hard-retention residual distillation',policy_activated=False)
    (RUN/'run.json').write_text(json.dumps(record,indent=2)+'\n')
    try:
        with np.load(ROOT/'experiments/walking/braking-replay-v53/replay.npz') as d:x=torch.from_numpy(d['observations']);y=torch.from_numpy(d['residuals']);positive=torch.from_numpy(d['positive'])
        state=torch.load(PARENT/'model.pt',map_location='cpu',weights_only=True);model=BrakeNet(state['mean'],state['scale']);model.load_state_dict(state);optimizer=torch.optim.Adam(model.parameters(),lr=1e-4)
        yes,no=torch.where(positive)[0],torch.where(~positive)[0]
        with (RUN/'learning.jsonl').open('w') as trace,(RUN/'hard-pools.jsonl').open('w') as pools:
            for step in range(8000):
                if step%50==0:
                    with torch.no_grad():errors=model(x[no]).abs().max(1).values;hard=no[torch.argsort(errors,descending=True,stable=True)[:128]]
                    pools.write(json.dumps(dict(step=step,row_indices=hard.tolist(),maximum_error_rad=float(errors.max())))+'\n')
                selected=torch.cat([yes[torch.randint(len(yes),(128,))],no[torch.randint(len(no),(128,))],hard]);prediction=model(x[selected]);loss,components=retention_loss(prediction,y[selected]);assert torch.isfinite(loss)
                optimizer.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.);optimizer.step();record['steps']=step+1
                trace.write(json.dumps(dict(step=step,loss=float(loss.detach()),components=[float(c.detach()) for c in components]))+'\n')
        model.eval();torch.save(model.state_dict(),RUN/'model.pt')
        assert torch.equal(model.mean,state['mean']) and torch.equal(model.scale,state['scale'])
        torch.onnx.export(model,torch.zeros(1,61),str(RUN/'policy.onnx'),input_names=['obs'],output_names=['residual'],opset_version=17,dynamo=False)
        options=ort.SessionOptions();options.intra_op_num_threads=1;options.inter_op_num_threads=1;sess=ort.InferenceSession(str(RUN/'policy.onnx'),sess_options=options,providers=['CPUExecutionProvider'])
        with torch.no_grad():fitted=model(x).numpy();random=torch.randn(1000,61);reference=model(random).numpy()
        error=0.
        for inputs,target in [(x.numpy(),fitted),(random.numpy(),reference)]:
            for obs,expected in zip(inputs,target):error=max(error,float(abs(sess.run(None,{'obs':obs[None]})[0][0]-expected).max()))
        assert error<1e-4 and np.isfinite(fitted).all() and binding()==frozen
        record.update(status='completed',policy_sha256=digest(RUN/'policy.onnx'),checkpoint_sha256=digest(RUN/'model.pt'),maximum_export_error=error,positive_rows=len(yes),negative_rows=len(no),sample_draws=3072000,new_rl_transitions=0,rmse_positive=float(np.sqrt(np.mean((fitted[positive]-y.numpy()[positive])**2))),rmse_retention=float(np.sqrt(np.mean(fitted[~positive]**2))),maximum_retention_error=float(abs(fitted[~positive]).max()),p95_retention_row_max_error=float(np.percentile(abs(fitted[~positive]).max(1),95)),normalizer_unchanged=True,parent_checkpoint_sha256=frozen['parent_checkpoint_sha256'])
    except BaseException as exc:record.update(status='failed',error=f'{type(exc).__name__}: {exc}');raise
    finally:
        record['elapsed_s']=time.monotonic()-started;(RUN/'run.json').write_text(json.dumps(record,indent=2)+'\n')
        for p in frozen['source_sha256']:
            dst=RUN/'source'/p;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,dst)
        seal(RUN)
    print(json.dumps({k:v for k,v in record.items() if k!='source_sha256'}),flush=True)
if __name__=='__main__':main()
