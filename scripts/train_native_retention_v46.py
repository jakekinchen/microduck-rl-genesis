"""One bounded native PPO run learning both actors across complete sequences."""
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
FREEZE=ROOT/'experiments/walking/native-retention-freeze-v46.json'
PARENTS={'walking':'walking-20260906-v21','standing':'standing-20260906-v15'}
EXTRA=['microduck/retained_walker_v46.py','microduck/native_sequence_env_v46.py',
       'scripts/train_native_retention_v46.py','scripts/probe_native_sequence_v46.py',
       'scripts/build_retention_replay_v46.py','scripts/analyze_components_v45.py',
       'experiments/walking/component_pairs_v45.py',
       'experiments/walking/RETENTION-CORRECTION-v46.md','experiments/walking/native_candidate_v46.py',
       'experiments/walking/retention-replay-v46/replay.npz','experiments/walking/retention-replay-v46/provenance.json',
       'scripts/evaluate_native_retention_flat_v46.py','scripts/evaluate_native_retention_endurance_v46.py',
       'scripts/evaluate_native_retention_surfaces_v46.py','tests/test_retained_walker_v46.py']



def binding():
    frozen=json.loads((ROOT/'experiments/walking/native-sequence-freeze-v44.json').read_text())
    sources=frozen['source_sha256'].copy()
    for name in EXTRA:sources[name]=digest(ROOT/name)
    for name,sha in sources.items():
        if digest(ROOT/name)!=sha:raise ValueError('source drift: '+name)
    warm={}
    for role,run in PARENTS.items():
        folder=ROOT/'logs'/run;record=json.loads((folder/'run.json').read_text())
        if digest(folder/record['checkpoint'])!=record['checkpoint_sha256']:raise ValueError('parent drift')
        warm[role]=record['checkpoint_sha256']
    if warm!={'walking':'7b5e166c13a8086fdd21b5ad237a0e69aa75828ad6f8fb5536f3ea057535a322',
              'standing':'acab8402e262dbb6af5a3fab9b67fa4ce5e34a4d23cadb127fe6dfa475a70e46'}:raise ValueError('parent identity')
    return dict(schema='microduck.native-retention-freeze/v46',source_sha256=sources,
        warm_start=warm,seed=26090746,full_transitions=360000,smoke_transitions=1440)


def main():
    p=argparse.ArgumentParser();p.add_argument('--freeze',action='store_true');p.add_argument('--run-id')
    p.add_argument('--num-envs',type=int,default=60);p.add_argument('--iterations',type=int,default=250);a=p.parse_args()
    frozen=binding()
    if a.freeze:
        with FREEZE.open('x') as f:json.dump(frozen,f,indent=2);f.write('\n')
        return
    if not a.run_id or not a.run_id.replace('-','').isalnum() or (a.num_envs,a.iterations) not in [(12,5),(60,250)]:p.error('12x5 smoke or 60x250 full')
    if frozen!=json.loads(FREEZE.read_text()):raise ValueError('freeze drift')
    preflight=ROOT/'receipts/walking/20260907-v46-retention-conformance'
    for line in (preflight/'SHA256SUMS').read_text().splitlines():
        sha,name=line.split('  ',1)
        if digest(preflight/name)!=sha:raise ValueError('preflight drift')
    if not json.loads((preflight/'probe.json').read_text())['passed']:raise ValueError('conformance required')
    if shutil.disk_usage(ROOT).free<1_200_000_000:raise ValueError('less than 1.2 GB free before bounded run')
    out=ROOT/'logs'/a.run_id;out.mkdir(parents=True,exist_ok=False)
    record=dict(schema='microduck.walking-training/v1',variant='native-retention-v46',proof_class='first_party_development',
        held_out=False,target_source='continuous-native-commands',args=vars(a),status='starting',pid=os.getpid(),
        source_sha256=frozen['source_sha256'],new_transitions=0,planned_new_transitions=a.num_envs*a.iterations*24,
        evaluator_freeze_sha256=digest(FREEZE),warm_start=frozen['warm_start'],critic_loaded=False,optimizer_loaded=False,
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
        from microduck.native_sequence_env_v46 import NativeSequenceEnv
        torch.set_num_threads(1);torch.manual_seed(26090746);np.random.seed(26090746)
        cfg=copy.deepcopy(TRAIN_CFG);cfg.update(seed=26090746,run_name=a.run_id,save_interval=250)
        cfg['algorithm'].update(learning_rate=1e-5,schedule='fixed',entropy_coef=0.,gamma=.999)
        cfg['obs_groups']['critic']=['policy']
        cfg['actor']['class_name']='microduck.retained_walker_v46:RetainedWalkerActor'
        cfg['algorithm']['class_name']='microduck.retained_walker_v46:RetentionPPO'
        cfg['actor']['distribution_cfg']['std_range']=[.005,.15]
        record['train_cfg']=copy.deepcopy(cfg)
        env=NativeSequenceEnv(a.num_envs,26090746,out);record['env_cfg']=env.cfg
        runner=OnPolicyRunner(env,copy.deepcopy(cfg),str(out),device='mps')
        for role,run in PARENTS.items():
            folder=ROOT/'logs'/run;parent=json.loads((folder/'run.json').read_text())
            state=torch.load(folder/parent['checkpoint'],map_location='cpu',weights_only=True)['actor_state_dict']
            actor=getattr(runner.alg.actor,role);actor.load_state_dict(state,strict=True)
            if role=='walking':
                runner.alg.actor.teacher.load_state_dict(state,strict=True)
                with torch.no_grad():actor.distribution.std_param.mul_(.25)
        data=np.load(ROOT/'experiments/walking/retention-replay-v46/replay.npz')
        runner.alg.replay_obs=torch.from_numpy(data['observations']).to('mps')
        runner.alg.replay_actions=torch.from_numpy(data['actions']).to('mps')
        immutable={role:{k:v.detach().cpu().numpy().tobytes() for k,v in getattr(runner.alg.actor,role).state_dict().items()} for role in ['standing','teacher']}
        def stop(signum,frame):raise KeyboardInterrupt(f'owned native sequence training interrupted: {signum}')
        signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
        record['status']='running';(out/'run.json').write_text(json.dumps(record,indent=2)+'\n')
        runner.learn(num_learning_iterations=a.iterations,init_at_random_ep_len=False)
        final=out/f'model_{runner.current_learning_iteration}.pt'
        state=torch.load(final,map_location='cpu',weights_only=True)['actor_state_dict']
        if not all(torch.isfinite(v).all() for v in state.values()):raise ValueError('nonfinite actor')
        if not torch.isfinite(env.get_observations()['policy']).all():raise ValueError('nonfinite telemetry')
        if binding()!=frozen:raise ValueError('source changed during training')
        for role,values in immutable.items():
            for key,value in getattr(runner.alg.actor,role).state_dict().items():
                if value.detach().cpu().numpy().tobytes()!=values[key]:raise ValueError('frozen component changed: '+role+'/'+key)
        record.update(status='completed',checkpoint=final.name,checkpoint_sha256=digest(final),final_finite_actor=True)
    except BaseException as exc:
        record.update(status='interrupted' if isinstance(exc,KeyboardInterrupt) else 'failed',failure=f'{type(exc).__name__}: {exc}');raise
    finally:
        if runner is not None:record['new_transitions']=runner.logger.tot_timesteps
        if env is not None:record['final_coverage']=env.coverage();env.close()
        record['elapsed_s']=time.monotonic()-started
        (out/'run.json').write_text(json.dumps(record,indent=2)+'\n')
    # Split deterministic actors without another optimization or checkpoint choice.
    for role in PARENTS:
        folder=ROOT/'logs'/(a.run_id+'-'+role);folder.mkdir(exist_ok=False)
        component={**record,'variant':'native-retention-'+role+'-v46','joint_checkpoint_sha256':record['checkpoint_sha256']}
        cfg=copy.deepcopy(record['train_cfg']);cfg['actor']['class_name']='MLPModel';component['train_cfg']=cfg
        torch.save({'actor_state_dict':getattr(runner.alg.actor,role).state_dict()},folder/final.name)
        component['checkpoint_sha256']=digest(folder/final.name)
        (folder/'run.json').write_text(json.dumps(component,indent=2)+'\n')
    print(json.dumps({key:record[key] for key in ['status','checkpoint','elapsed_s','new_transitions']}),flush=True)

if __name__=='__main__':main()
