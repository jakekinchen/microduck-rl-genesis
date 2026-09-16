"""Action-frozen robot-level comparison of exposed public-surface failures."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.evaluate_laser import digest

FREEZE=ROOT/'experiments/walking/public-surface-action-replay-freeze-v1.json'
BASE='receipts/walking/20260906-v25-surface-baseline'
STANDING='receipts/walking/20260906-v26-surface-standing'
CASES=[(BASE,p+'-start-1') for p in ['rigid-control','soft-low-traction','soft-middle','soft-high-traction']]+[(STANDING,'soft-high-traction-start-1')]


def binding():
    sources=json.loads((ROOT/'logs/standing-20260906-v25/run.json').read_text())['source_sha256'].copy()
    for name in ['scripts/probe_public_surface_action_replay_v1.py','experiments/walking/PUBLIC-SURFACE-ACTION-REPLAY-v1.md']:
        sources[name]=digest(ROOT/name)
    for name,sha in sources.items():
        if digest(ROOT/name)!=sha:raise ValueError('source drift: '+name)
    manifests={}
    for directory in sorted({c[0] for c in CASES}):
        root=ROOT/directory;seen=set()
        for line in (root/'SHA256SUMS').read_text().splitlines():
            expected,name=line.split('  ',1);path=(root/name).resolve()
            if name in seen or not path.is_relative_to(root.resolve()) or digest(path)!=expected:
                raise ValueError('input manifest mismatch')
            seen.add(name)
        if not {'trajectory.jsonl','probe.json','suite.json'}<=seen:raise ValueError('missing native input')
        manifests[directory]=digest(root/'SHA256SUMS')
    return {'source_sha256':sources,'input_manifest_sha256':manifests,'cases':CASES,
        'maximum_prefix_steps':50,'base_limit_m':.002,'joint_limit_deg':5.,'backend':'cpu','support_representation':'Native plane versus Genesis fixed panels; equal local top height, different manifold representations.'}


def run(output,result):
    import genesis as gs
    import numpy as np
    import torch
    from microduck.bam_actuator import DelayBuffer
    from microduck.public_surface_env_v25 import PublicSurfaceWalkingEnv
    from experiments.walking.public_surface_v25 import PROFILES
    torch.set_num_threads(1)
    gs.init(backend=gs.cpu,logging_level='warning',seed=26090625)
    env=PublicSurfaceWalkingEnv(1,demo=True,model_directory=ROOT/'experiments/walking/models/contact-v11',surface_xml=output/'panels.xml')
    ids=torch.arange(1,device=env.device)
    for index,(directory,session_id) in enumerate(CASES):
        native=ROOT/directory;suite=json.loads((native/'suite.json').read_text())
        session=next(s for s in suite['sessions'] if s['id']==session_id)
        profile=next(i for i,p in enumerate(PROFILES) if p['id']==session['profile']['id'])
        case_id=session_id+'--window-1'
        rows=[]
        with (native/'trajectory.jsonl').open() as f:
            for line in f:
                r=json.loads(line)
                if r['case_id']==case_id:rows.append(r)
                if len(rows)==50:break
        actions=np.load(native/(case_id+'-actions-float32.npy'),allow_pickle=False)[:len(rows)]
        if actions.dtype!=np.float32 or actions.shape!=(len(rows),14) or not rows:raise ValueError('invalid recorded actions')
        np.testing.assert_array_equal(actions,np.asarray([r['action_rad'] for r in rows],np.float32))
        motor,sensor=suite['motor_ticks'],suite['sensor_ticks']
        env.bam._delay=DelayBuffer((1,14),motor,motor,0,env.device)
        for key,dim in [('base_ang_vel',3),('projected_gravity',3),('joint_vel',14)]:
            env.obs_delays[key]=DelayBuffer((1,dim),sensor,sensor,0,env.device)
        env.reset();env.env_origins[0]=torch.tensor([0.,16.*profile,0.],device=env.device)
        env.bam.vin_nominal.fill_(7.35);env.bam.vin_drop_resistance.zero_()
        for delay in env.obs_delays.values():delay.reset(ids)
        env.set_twist(0.,0.,0.)
        env.place([0.,16.*profile,.125],yaw=session['yaw'])
        env.bam._delay._buf[:]=env.default_dof_pos;env.bam._delay._needs_fill[:]=False
        for tensor in [env.dof_vel,env.actions,env.last_actions,env.bam.prev_torque,env.base_lin_vel,env.base_ang_vel,env.encoder_bias,env.head_cmd,env.body_cmd]:
            if torch.count_nonzero(tensor):raise ValueError('nonzero initial state')
        np.testing.assert_allclose(env.base_pos[0].cpu(),[0,16.*profile,.125],rtol=0,atol=1e-7)
        delay=env.bam._delay;targets=[]
        def record_delay(target):
            actual=delay(target);targets.append(actual[0].detach().cpu().numpy().copy());return actual
        env.bam._delay=record_delay
        comparisons=[]
        try:
            with (output/f'case-{index}.jsonl').open('w') as stream:
                for i,(row,action) in enumerate(zip(rows,actions)):
                    targets.clear();env.set_twist(*row['policy_command'])
                    _,_,done,_=env.step(torch.from_numpy(action[None,:].copy()).to(env.device))
                    if bool(done[0]) or action.tobytes()!=env.actions[0].cpu().numpy().tobytes():raise ValueError('reset or altered action')
                    if len(targets)!=4:raise ValueError('missing physics targets')
                    np.testing.assert_allclose(targets[-1],row['applied_servo_target_rad'],rtol=0,atol=2e-7)
                    qpos=np.r_[env.base_pos[0].cpu(),env.base_quat[0].cpu(),env.dof_pos[0].cpu()].astype(float)
                    qpos[1]-=16.*profile;reference=np.asarray(row['qpos'])
                    if not np.isfinite(qpos).all():raise ValueError('nonfinite state')
                    error=float(np.linalg.norm(qpos[:3]-reference[:3]));joint=float(np.rad2deg(np.abs(qpos[7:]-reference[7:]).max()))
                    item={'time_s':row['session_time_s'],'qpos':qpos.tolist(),'native_qpos':reference.tolist(),
                        'base_error_m':error,'joint_error_deg':joint,'action_rad':action.tolist(),
                        'motor_targets_rad_physics':np.asarray(targets).tolist(),'native_fell':row['fell'],
                        'genesis_base_below_fall_height':bool(qpos[2]<.07)}
                    comparisons.append(item);stream.write(json.dumps(item)+'\n')
        finally:env.bam._delay=delay
        snapshot=env.surface_snapshot()
        max_base=max(r['base_error_m'] for r in comparisons);max_joint=max(r['joint_error_deg'] for r in comparisons)
        first=next((r['time_s'] for r in comparisons if r['base_error_m']>.002 or r['joint_error_deg']>5.),None)
        r={'native_receipt':directory,'session_id':session_id,'steps':len(rows),'physics_steps':4*len(rows),
            'action_bytes_sha256':hashlib.sha256(actions.tobytes()).hexdigest(),
            'action_bytes_identical':True,'all_final_substep_targets_match':True,'surface_snapshot':snapshot,
            'max_base_error_m':max_base,'max_joint_error_deg':max_joint,'first_threshold_divergence_s':first,
            'passed_numerical_comparison':first is None,'native_final_z_m':rows[-1]['qpos'][2],
            'genesis_final_z_m':comparisons[-1]['qpos'][2]}
        result['cases'].append(r);np.save(output/f'case-{index}-actions-float32.npy',actions)
        print(json.dumps({k:v for k,v in r.items() if k!='surface_snapshot'}),flush=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--freeze',action='store_true');p.add_argument('--output',type=Path);a=p.parse_args()
    frozen=binding()
    if a.freeze:
        with FREEZE.open('x') as f:json.dump(frozen,f,indent=2);f.write('\n')
        return
    if a.output is None:p.error('new output required')
    if json.loads(FREEZE.read_text())!=json.loads(json.dumps(frozen)):raise ValueError('freeze mismatch')
    a.output.mkdir(parents=True,exist_ok=False)
    result={'schema':'microduck.public-surface-action-replay/v1','status':'starting','cases':[],
        'physical_calibration':False,'candidate_selection_eligible':False,
        'boundary':'Recorded action replay with native initialization; numerical dynamics diagnostic, not closed-loop gait or physical acceptance.'}
    started=time.monotonic()
    try:
        run(a.output,result)
        if binding()!=frozen:raise ValueError('source or input drift during replay')
        result['status']='completed'
    except BaseException as exc:
        result.update(status='failed',failure=f'{type(exc).__name__}: {exc}');raise
    finally:
        result['elapsed_s']=time.monotonic()-started
        (a.output/'probe.json').write_text(json.dumps(result,indent=2)+'\n')
        shutil.copy2(FREEZE,a.output/'freeze.json')
        for name in frozen['source_sha256']:
            target=a.output/'source'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
        (a.output/'SHA256SUMS').write_text(''.join(f'{digest(f)}  {f.relative_to(a.output)}\n' for f in sorted(a.output.rglob('*')) if f.is_file() and f.name!='SHA256SUMS'))

if __name__=='__main__':main()
