"""Fixed supervised consolidation of V21/V15 into one shared MLP."""
import copy
import json
from pathlib import Path
import sys
import time
import numpy as np
import torch
from tensordict import TensorDict
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiments.walking.recipe_v54 import FREEZE,REPLAY,SEED,digest,new_output,write_manifest,storage_ready
from scripts.train_recipe_v54 import require_freeze,parent_state,INIT_RUN
from microduck.velocity_cfg import TRAIN_CFG
from microduck.recipe_actor_v54 import SharedActor,RoutedActor,mode_pools,balanced_indices


def main():
    frozen=require_freeze()
    out=new_output('logs/'+INIT_RUN)
    record=dict(status='starting',updates=0,new_rl_transitions=0,freeze_sha256=digest(FREEZE))
    started=time.monotonic()
    try:
        torch.set_num_threads(1);torch.manual_seed(SEED);np.random.seed(SEED)
        cfg=copy.deepcopy(TRAIN_CFG['actor']);cfg.pop('class_name')
        sample=TensorDict({'policy':torch.zeros(1,61)},[1])
        actor=SharedActor(sample,{'actor':['policy']},'actor',14,**copy.deepcopy(cfg))
        actor.load_state_dict(parent_state('walking'),strict=True)
        teacher=RoutedActor(sample,{'actor':['policy']},'actor',14,**copy.deepcopy(cfg))
        for role in ['walking','standing']: getattr(teacher,role).load_state_dict(parent_state(role),strict=True)
        data=np.load(REPLAY/'replay.npz')
        # Verify original stored labels against both actual parent tensor models.
        original_obs=torch.from_numpy(data['observations'])
        targets=torch.from_numpy(data['actions'])
        max_error=0.
        with torch.no_grad():
            for offset in range(0,len(original_obs),1024):
                prediction=teacher(TensorDict({'policy':original_obs[offset:offset+1024]},[len(original_obs[offset:offset+1024])]))
                max_error=max(max_error,float((prediction-targets[offset:offset+1024]).abs().max()))
        if not np.isfinite(max_error) or max_error>=1e-4: raise ValueError('replay teacher parity failed')
        actor=actor.to('mps');obs=original_obs.to('mps');target=targets.to('mps')
        pools=mode_pools(obs)
        optimizer=torch.optim.Adam(actor.mlp.parameters(),lr=1e-4)
        losses=[]
        record.update(status='running',replay_rows=len(obs),teacher_max_error_rad=max_error)
        (out/'initialization.json').write_text(json.dumps(record,indent=2)+'\n')
        for update in range(20000):
            indices=balanced_indices(pools)
            prediction=actor(TensorDict({'policy':obs[indices]},[len(indices)]))
            loss=(prediction-target[indices]).square().mean()
            if not torch.isfinite(loss): raise ValueError('nonfinite initialization loss')
            optimizer.zero_grad();loss.backward();optimizer.step()
            losses.append(float(loss.detach().cpu()))
            record['updates']=update+1
            if (update+1)%1000==0:
                storage_ready()
                print(json.dumps(dict(update=update+1,mse=losses[-1])),flush=True)
        actor=actor.cpu().eval();predictions=[]
        with torch.no_grad():
            for offset in range(0,len(original_obs),1024):
                part=original_obs[offset:offset+1024]
                predictions.append(actor(TensorDict({'policy':part},[len(part)])).numpy())
        predictions=np.concatenate(predictions);error=predictions-data['actions']
        provenance=json.loads((REPLAY/'provenance.json').read_text())
        groups=[]
        standing=(data['observations'][:,48:51]==0).all(-1)
        for index,name in enumerate(provenance['cases']):
            for role,mask in [('walking',~standing),('standing',standing)]:
                selected=(data['case_ids']==index)&mask
                if selected.any():
                    groups.append(dict(case=name,role=role,rows=int(selected.sum()),
                        rmse_rad=float(np.sqrt(np.mean(error[selected]**2))),max_abs_error_rad=float(abs(error[selected]).max())))
        torch.save({'actor_state_dict':actor.state_dict()},out/'shared.pt')
        np.save(out/'losses.npy',np.asarray(losses,np.float64))
        np.save(out/'predictions-float32.npy',predictions)
        if require_freeze()!=frozen: raise ValueError('source drift during initialization')
        record.update(status='completed',checkpoint_sha256=digest(out/'shared.pt'),
            sample_presentations=20000*512,groups=groups,
            boundary='Supervised recipe initialization; not behavior acceptance or new RL transitions.')
    except BaseException as exc:
        record.update(status='failed',failure=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        record['elapsed_s']=time.monotonic()-started
        (out/'initialization.json').write_text(json.dumps(record,indent=2)+'\n')
    write_manifest(out)
    print(json.dumps(dict(status=record['status'],updates=record['updates'],elapsed_s=record['elapsed_s'])),flush=True)


if __name__=='__main__': main()
