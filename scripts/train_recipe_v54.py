"""Two separately invoked, bounded V54 PPO arms; no automatic run extension."""
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
from experiments.walking.recipe_v54 import (
    FREEZE, REPLAY, SEED, PARENTS, RECIPES, digest, new_output,
    run_name, storage_ready, verify_sources, write_manifest)

EXTRA=['microduck/recipe_actor_v54.py','microduck/native_sequence_env_v54.py',
    'experiments/walking/recipe_v54.py','experiments/walking/RECIPE-COMPARISON-v54.md',
    'experiments/walking/UPSTREAM-RECIPE-AUDIT-v54.md',
    'scripts/build_recipe_replay_v54.py','scripts/train_recipe_v54.py',
    'scripts/train_recipe_initializer_v54.py','scripts/probe_recipe_v54.py',
    'scripts/verify_recipe_v54.py','scripts/evaluate_recipe_flat_v54.py',
    'scripts/evaluate_recipe_endurance_v54.py','scripts/evaluate_recipe_surfaces_v54.py',
    'tests/test_recipe_v54.py','experiments/walking/recipe-replay-v54/replay.npz',
    'experiments/walking/recipe-replay-v54/provenance.json']
INIT_RUN='recipe-init-20260909-v54-shared'


def parent_state(role):
    import torch
    folder=ROOT/'logs'/PARENTS[role]
    record=json.loads((folder/'run.json').read_text())
    if digest(folder/record['checkpoint'])!=record['checkpoint_sha256']:
        raise ValueError('parent drift')
    return torch.load(folder/record['checkpoint'],map_location='cpu',weights_only=True)['actor_state_dict']


def binding():
    base=json.loads((ROOT/'experiments/walking/native-retention-freeze-v50.json').read_text())
    verify_sources(base)
    sources=base['source_sha256'].copy()
    sources.update({name:digest(ROOT/name) for name in EXTRA})
    return dict(schema='microduck.recipe-freeze/v54',source_sha256=sources,
        warm_start=base['warm_start'],seed=SEED,recipes=list(RECIPES),
        full_transitions_per_arm=1_728_000,smoke_transitions_per_arm=2880,
        initialization_updates=20_000,initialization_samples_per_update=512)


def require_freeze():
    frozen=json.loads(FREEZE.read_text())
    if binding()!=frozen: raise ValueError('V54 freeze drift')
    return frozen


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--freeze',action='store_true')
    p.add_argument('--recipe',choices=RECIPES)
    p.add_argument('--smoke',action='store_true')
    args=p.parse_args()
    if args.freeze:
        with FREEZE.open('x') as stream: json.dump(binding(),stream,indent=2);stream.write('\n')
        return
    if not args.recipe: p.error('recipe required')
    frozen=require_freeze()
    probe=ROOT/'receipts/walking/20260909-v54-conformance'
    from scripts.analyze_components_v45 import verify_manifest
    verify_manifest(probe)
    proof=json.loads((probe/'probe.json').read_text())
    if not proof['complete'] or not proof['passed'] or proof['freeze_sha256']!=digest(FREEZE):
        raise ValueError('complete V54 conformance required')
    init=ROOT/'logs'/INIT_RUN
    init_record=json.loads((init/'initialization.json').read_text())
    if (init_record['status']!='completed' or init_record['updates']!=20000
            or init_record['freeze_sha256']!=digest(FREEZE)
            or digest(init/'shared.pt')!=init_record['checkpoint_sha256']):
        raise ValueError('fixed shared initialization required')
    if not args.smoke:
        smoke=json.loads((ROOT/'logs'/run_name(args.recipe,True)/'run.json').read_text())
        if smoke['status']!='completed' or smoke['new_transitions']!=2880:
            raise ValueError('completed matching smoke required')
    storage_ready()
    num_envs,iterations=(24,5) if args.smoke else (48,1500)
    name=run_name(args.recipe,args.smoke)
    out=new_output('logs/'+name)
    record=dict(schema='microduck.walking-training/v1',variant='native-recipe-v54',
        recipe=args.recipe,proof_class='first_party_development',held_out=False,
        target_source='continuous-native-commands',args=dict(num_envs=num_envs,iterations=iterations),
        status='starting',pid=os.getpid(),source_sha256=frozen['source_sha256'],
        warm_start=frozen['warm_start'],new_transitions=0,
        planned_new_transitions=num_envs*iterations*24,freeze_sha256=digest(FREEZE),
        initialization_sha256=init_record['checkpoint_sha256'] if args.recipe=='shared' else None,
        critic_loaded=False,optimizer_loaded=False,
        packages={name:importlib.metadata.version(name) for name in ['mujoco','torch','rsl-rl-lib']})
    for rel in record['source_sha256']:
        dest=out/'source'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/rel,dest)
    started=time.monotonic();runner=env=None
    try:
        (out/'run.json').write_text(json.dumps(record,indent=2)+'\n')
        import numpy as np
        import torch
        from tensordict import TensorDict
        from rsl_rl.models import MLPModel
        from rsl_rl.runners import OnPolicyRunner
        from microduck.velocity_cfg import TRAIN_CFG
        from microduck.recipe_actor_v54 import RoutedActor, mode_pools
        from microduck.native_sequence_env_v54 import NativeSequenceEnv
        torch.set_num_threads(1);torch.manual_seed(SEED);np.random.seed(SEED)
        cfg=copy.deepcopy(TRAIN_CFG)
        cfg.update(seed=SEED,run_name=name,save_interval=iterations)
        cfg['algorithm'].update(class_name='microduck.recipe_actor_v54:RecipePPO',
            learning_rate=3e-5,schedule='fixed',entropy_coef=0.,gamma=.999)
        cfg['obs_groups']['critic']=['policy']
        cls='RoutedActor' if args.recipe=='routed' else 'SharedActor'
        cfg['actor']['class_name']='microduck.recipe_actor_v54:'+cls
        cfg['actor']['distribution_cfg']['std_range']=[.005,.15]
        record['train_cfg']=copy.deepcopy(cfg)
        env=NativeSequenceEnv(num_envs,SEED,out);record['env_cfg']=env.cfg
        runner=OnPolicyRunner(env,copy.deepcopy(cfg),str(out),device='mps')
        if args.recipe=='routed':
            for role in PARENTS:
                getattr(runner.alg.actor,role).load_state_dict(parent_state(role),strict=True)
        else:
            state=torch.load(init/'shared.pt',map_location='cpu',weights_only=True)['actor_state_dict']
            runner.alg.actor.load_state_dict(state,strict=True)
        actors=[getattr(runner.alg.actor,r) for r in PARENTS] if args.recipe=='routed' else [runner.alg.actor]
        with torch.no_grad():
            for actor in actors: actor.distribution.std_param.mul_(.25)
        obs=TensorDict({'policy':torch.zeros(1,61)},[1])
        actor_cfg=copy.deepcopy(cfg['actor']);actor_cfg.pop('class_name')
        teacher=RoutedActor(obs,cfg['obs_groups'],'actor',14,**actor_cfg)
        for role in PARENTS: getattr(teacher,role).load_state_dict(parent_state(role),strict=True)
        runner.alg.teacher=teacher.to('mps').requires_grad_(False).eval()
        # A separate seed gives both arms exactly the same cold critic tensors.
        torch.manual_seed(SEED+1)
        critic_cfg=copy.deepcopy(cfg['critic']);critic_cfg.pop('class_name')
        cold_critic=MLPModel(obs,cfg['obs_groups'],'critic',1,**critic_cfg)
        runner.alg.critic.load_state_dict(cold_critic.state_dict(),strict=True)
        data=np.load(REPLAY/'replay.npz')
        runner.alg.replay_obs=torch.from_numpy(data['observations']).to('mps')
        runner.alg.replay_actions=torch.from_numpy(data['actions']).to('mps')
        runner.alg.replay_pools=mode_pools(runner.alg.replay_obs)
        immutable={k:v.detach().cpu().numpy().tobytes() for k,v in runner.alg.actor.state_dict().items() if 'obs_normalizer.' in k}
        teacher_before={k:v.detach().cpu().numpy().tobytes() for k,v in teacher.state_dict().items()}
        torch.save({'actor_state_dict':runner.alg.actor.state_dict(),
            'critic_state_dict':runner.alg.critic.state_dict()},out/'initial.pt')
        record['initial_checkpoint_sha256']=digest(out/'initial.pt')
        def stop(signum,frame): raise KeyboardInterrupt(f'owned V54 job interrupted: {signum}')
        signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
        torch.manual_seed(SEED);np.random.seed(SEED)
        record['status']='running';(out/'run.json').write_text(json.dumps(record,indent=2)+'\n')
        runner.learn(num_learning_iterations=iterations,init_at_random_ep_len=False)
        final=out/f'model_{runner.current_learning_iteration}.pt'
        state=torch.load(final,map_location='cpu',weights_only=True)['actor_state_dict']
        if not all(torch.isfinite(v).all() for v in state.values()): raise ValueError('nonfinite actor')
        if require_freeze()!=frozen: raise ValueError('source drift during training')
        for key,value in immutable.items():
            if state[key].numpy().tobytes()!=value: raise ValueError('parent normalizer drift')
        for key,value in teacher_before.items():
            if teacher.state_dict()[key].detach().cpu().numpy().tobytes()!=value: raise ValueError('teacher changed')
        record.update(status='completed',checkpoint=final.name,checkpoint_sha256=digest(final),
            frozen_normalizers_verified=True,frozen_teachers_verified=True)
    except BaseException as exc:
        record.update(status='interrupted' if isinstance(exc,KeyboardInterrupt) else 'failed',
            failure=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        if runner is not None: record['new_transitions']=runner.logger.tot_timesteps
        if env is not None: record['final_coverage']=env.coverage();env.close()
        record['elapsed_s']=time.monotonic()-started
        (out/'run.json').write_text(json.dumps(record,indent=2)+'\n')
    for role in PARENTS:
        folder=new_output('logs/'+name+'-'+role)
        component=copy.deepcopy(record)
        component.update(variant='native-recipe-'+role+'-v54',joint_checkpoint_sha256=record['checkpoint_sha256'])
        component['train_cfg']['actor']['class_name']='MLPModel'
        actor=getattr(runner.alg.actor,role) if args.recipe=='routed' else runner.alg.actor
        torch.save({'actor_state_dict':actor.state_dict()},folder/final.name)
        component['checkpoint_sha256']=digest(folder/final.name)
        (folder/'run.json').write_text(json.dumps(component,indent=2)+'\n')
    write_manifest(out)
    print(json.dumps({k:record[k] for k in ['status','recipe','checkpoint','elapsed_s','new_transitions']}),flush=True)


if __name__=='__main__': main()
