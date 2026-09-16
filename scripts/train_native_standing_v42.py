"""Bounded native stopping refinement; final checkpoint only, no paid compute."""
import argparse
import copy
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import signal
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.evaluate_laser import digest

FREEZE=ROOT/'experiments/walking/native-standing-freeze-v42.json'
PARENT=ROOT/'logs/standing-20260906-v15'
PARENT_SHA='acab8402e262dbb6af5a3fab9b67fa4ce5e34a4d23cadb127fe6dfa475a70e46'


def binding():
    from scripts.evaluate_heading_headroom_endurance_v30 import SOURCES
    extra=['scripts/train_native_standing_v42.py','microduck/native_standing_env_v42.py','experiments/walking/NATIVE-STANDING-v42.md',
        'experiments/walking/native_candidate_v42.py',
        'scripts/evaluate_native_standing_endurance_v42.py','scripts/evaluate_native_standing_flat_v42.py','scripts/evaluate_native_standing_surfaces_v42.py']
    parent=json.loads((PARENT/'run.json').read_text())
    sources=parent['source_sha256'].copy()
    for name in SOURCES+extra:sources[name]=digest(ROOT/name)
    for name,sha in sources.items():
        if digest(ROOT/name)!=sha:raise ValueError('parent source drift: '+name)
    if parent['checkpoint_sha256']!=PARENT_SHA or digest(PARENT/parent['checkpoint'])!=PARENT_SHA:raise ValueError('parent mismatch')
    for path in [ROOT/'receipts/walking/20260906-v30-flat-regression',ROOT/'receipts/walking/20260906-v30-heading-endurance']:
        for line in (path/'SHA256SUMS').read_text().splitlines():
            sha,name=line.split('  ',1);file=(path/name).resolve()
            if not file.is_relative_to(path.resolve()) or digest(file)!=sha:raise ValueError('baseline receipt mismatch')
    return dict(schema='microduck.native-standing-freeze/v42',parent_sha256=PARENT_SHA,
        source_sha256=sources,seed=26090641,full_transitions=64*250*24,smoke_transitions=8*5*24)


def main():
    p=argparse.ArgumentParser();p.add_argument('--freeze',action='store_true');p.add_argument('--run-id')
    p.add_argument('--num-envs',type=int,default=64);p.add_argument('--iterations',type=int,default=250);a=p.parse_args()
    frozen=binding()
    if a.freeze:
        with FREEZE.open('x') as f:json.dump(frozen,f,indent=2);f.write('\n')
        return
    if not a.run_id or not a.run_id.replace('-','').isalnum() or (a.num_envs,a.iterations) not in [(8,5),(64,250)]:p.error('new ID; 8x5 smoke or 64x250 full')
    if frozen!=json.loads(FREEZE.read_text()):raise ValueError('freeze drift')
    out=ROOT/'logs'/a.run_id;out.mkdir(parents=True,exist_ok=False)
    record=dict(schema='microduck.walking-training/v1',variant='native-standing-v42',proof_class='first_party_development',
        held_out=False,target_source='zero-command-native-handoff',args=vars(a),status='starting',pid=os.getpid(),
        source_sha256=frozen['source_sha256'],new_transitions=0,planned_new_transitions=a.num_envs*a.iterations*24,
        evaluator_freeze_sha256=digest(FREEZE),warm_start=dict(sha256=PARENT_SHA,actor_only=True,critic_loaded=False,optimizer_loaded=False),
        packages={name:importlib.metadata.version(name) for name in ['mujoco','torch','rsl-rl-lib']})
    for name in record['source_sha256']:
        target=out/'source'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
    started=time.monotonic();runner=env=None
    try:
        (out/'run.json').write_text(json.dumps(record,indent=2)+'\n')
        import numpy as np
        import torch
        from rsl_rl.runners import OnPolicyRunner
        from microduck.velocity_cfg import TRAIN_CFG
        from microduck.native_standing_env_v42 import NativeStandingEnv
        torch.set_num_threads(1);torch.manual_seed(26090641);np.random.seed(26090641)
        cfg=copy.deepcopy(TRAIN_CFG);cfg.update(seed=26090641,run_name=a.run_id)
        cfg['algorithm']['learning_rate']=1e-4;cfg['obs_groups']['critic']=['policy']
        record['train_cfg']=cfg
        env=NativeStandingEnv(a.num_envs,26090641,out)
        record['env_cfg']=env.cfg;record['initial_coverage']=env.coverage()
        runner=OnPolicyRunner(env,copy.deepcopy(cfg),str(out),device='mps')
        parent=json.loads((PARENT/'run.json').read_text())
        runner.load(str(PARENT/parent['checkpoint']),load_cfg={'actor':True,'critic':False,'optimizer':False,'iteration':False})
        def stop(signum,frame):raise KeyboardInterrupt(f'owned native training interrupted: {signum}')
        signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
        record['status']='running';(out/'run.json').write_text(json.dumps(record,indent=2)+'\n')
        runner.learn(num_learning_iterations=a.iterations,init_at_random_ep_len=False)
        final=out/f'model_{runner.current_learning_iteration}.pt'
        state=torch.load(final,map_location='cpu',weights_only=True)['actor_state_dict']
        if not all(torch.isfinite(v).all() for v in state.values()):raise ValueError('nonfinite actor')
        if not torch.isfinite(env.get_observations()['policy']).all():raise ValueError('nonfinite final telemetry')
        if binding()!=frozen:raise ValueError('source changed during training')
        record.update(status='completed',checkpoint=final.name,checkpoint_sha256=digest(final),final_finite_actor=True)
    except BaseException as exc:
        record.update(status='interrupted' if isinstance(exc,KeyboardInterrupt) else 'failed',failure=f'{type(exc).__name__}: {exc}');raise
    finally:
        if runner is not None:record['new_transitions']=runner.logger.tot_timesteps
        if env is not None:record['final_coverage']=env.coverage();env.close()
        record['elapsed_s']=time.monotonic()-started
        (out/'run.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({key:record[key] for key in ['status','checkpoint','elapsed_s','new_transitions']}),flush=True)


if __name__=='__main__':main()
