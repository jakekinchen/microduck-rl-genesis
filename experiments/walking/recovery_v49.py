"""V49 full-state branches and fixed recovery scoring in the native V30 world."""
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
FREEZE = ROOT/'experiments/walking/recovery-freeze-v49.json'
CAPTURE = ROOT/'receipts/walking/20260908-v49-recovery-capture'
COMPARE = ROOT/'receipts/walking/20260908-v49-recovery-comparisons'
SEARCH = ROOT/'receipts/walking/20260908-v49-recovery-search'
INPUTS = {'matched':'20260908-v47-original-handoff',
          'original':'20260906-v30-heading-endurance',
          'v48':'20260908-v48-standing-retention-endurance'}
KNOT_TIMES = np.array([0., .2, .5, 1., 1.75, 2.5])


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        while block:=f.read(1024*1024):h.update(block)
    return h.hexdigest()


def manifest(folder):
    folder=Path(folder).resolve();count=0
    for line in (folder/'SHA256SUMS').read_text().splitlines():
        expected,name=line.split('  ',1);path=(folder/name).resolve()
        if not path.is_relative_to(folder) or digest(path)!=expected:raise ValueError('receipt drift: '+str(path))
        count+=1
    return count


def seal(folder):
    (folder/'SHA256SUMS').write_text(''.join(f'{digest(p)}  {p.relative_to(folder)}\n'
        for p in sorted(folder.rglob('*')) if p.is_file() and p.name!='SHA256SUMS'))


def source_data(key):
    folder=ROOT/'receipts/walking'/INPUTS[key]
    suite=json.loads((folder/'suite.json').read_text())
    sessions=suite['sessions'] if key=='matched' else [s for s in suite['sessions'] if s['id']=='continuous-composition-start-1']
    rows={s['id']:[] for s in sessions}
    path=folder/'trajectory.jsonl.gz'
    if not path.exists():path=folder/'trajectory.jsonl'
    opener=gzip.open if path.suffix=='.gz' else open
    with opener(path,'rt') as f:
        for line in f:
            row=json.loads(line)
            if row['session_id'] in rows:rows[row['session_id']].append(row)
    data=[]
    for session in sessions:
        actions=np.concatenate([np.load(folder/f'{session["id"]}--window-{i+1}-actions-float32.npy')
                                for i in range(len(session['windows']))])
        assert actions.dtype==np.float32 and len(actions)==len(rows[session['id']])
        data.append(dict(key=key,folder=folder,suite=suite,session=session,rows=rows[session['id']],actions=actions,
                         capture_steps=[650,657] if key=='matched' else [4250,4256]))
    return data


def command_at(step, session):
    offset=0
    for index,window in enumerate(session['windows']):
        end=offset+round(window['duration_s']*50)
        if step<end:
            local=step-offset
            moving=round(window['move_start_s']*50)<=local<round(window['stop_start_s']*50)
            return window['command'] if moving else [0,0,0],index,local
        offset=end
    raise ValueError('command requested beyond full session')


def world_for(source):
    from experiments.walking.terrain_v23 import TerrainWorld
    from microduck.heading_headroom_v30 import Float32HeadingHeadroomServo
    s=source['session'];f=source['folder'];suite=source['suite']
    w=TerrainWorld(f/'policy.onnx',ROOT/'.workspace/bam',standing_policy=f/'standing/policy.onnx',
        model_directory=ROOT/'experiments/walking/models/contact-v11',terrain_scene=f/'terrain-models'/s['id']/'scene.xml',
        domain=s['domain'],motor_ticks=suite['motor_ticks'],sensor_ticks=suite['sensor_ticks'],yaw=s['yaw'],seed=s['seed'])
    w.heading_servo=Float32HeadingHeadroomServo()
    return w


def anchors(world):
    from evaluator.core import OnnxPolicy
    def actor(key):
        return OnnxPolicy(ROOT/'receipts/walking'/INPUTS[key]/'standing/policy.onnx',world.core.config['inference'])
    return {'original':actor('original'),'v48':actor('v48')}


class KnotPolicy:
    """Explicit diagnostic policy: base actor plus a fixed timed residual."""
    def __init__(self,base,knots):
        self.base=base;self.knots=np.asarray(knots,np.float32)
        if self.knots.shape!=(5,14) or not np.isfinite(self.knots).all() or abs(self.knots).max()>1.500001:
            raise ValueError('invalid V49 knot parameters')
        self.step=0;self.last=None

    def infer(self,obs):
        base,latency=self.base.infer(obs)
        t=self.step*.02
        if t>=KNOT_TIMES[-1] or not self.knots.any():
            action=base
        else:
            k=min(np.searchsorted(KNOT_TIMES,t,side='right')-1,4)
            a=self.knots[k];b=self.knots[k+1] if k<4 else np.zeros(14,np.float32)
            weight=(t-KNOT_TIMES[k])/(KNOT_TIMES[k+1]-KNOT_TIMES[k])
            action=(base+(a+(b-a)*weight).astype(np.float32)).astype(np.float32)
        self.last=action[0].copy()
        return action,latency


def rollout(world,state,source,start,anchor,knots=None,end=None,record=True):
    from experiments.walking.handoff_inspection_v47 import restore_state
    from experiments.walking.terrain_v23 import TerrainGaitProbe
    from experiments.walking.self_load import record_self_loads
    restore_state(world,state)
    if not hasattr(world,'v49_base_policies'):
        from evaluator.core import OnnxPolicy
        world.v49_base_policies=anchors(world)
        world.v49_base_policies['walking']=OnnxPolicy(source['folder']/'policy.onnx',world.core.config['inference'])
    policies=world.v49_base_policies
    walking=policies['walking']
    stand=policies[anchor]
    wrappers=None
    if knots is not None:
        wrappers=[KnotPolicy(walking,knots),KnotPolicy(stand,knots)]
        walking,stand=wrappers
    world.walking_policy=walking;world.standing_policy=stand
    end=end or sum(round(w['duration_s']*50) for w in source['session']['windows'])
    probe=TerrainGaitProbe(world.core) if record else None
    rows=[];actions=[];observations=[];cost=0.
    with record_self_loads(world) as loads:
        for i in range(start,end):
            if world.fell:break
            command,index,local=command_at(i,source['session'])
            if wrappers:
                for wrapper in wrappers:wrapper.step=i-start
            row=world.step_command(command)
            if probe:row=probe.sample(row)
            action=world.last_action.copy();obs=world.last_observation[0].copy()
            if wrappers:
                wrapper=wrappers[int(row['actor_mode']=='standing')]
                if action.tobytes()!=wrapper.last.tobytes():raise ValueError('diagnostic action altered')
            if len(loads)!=(i-start+1)*4:raise ValueError('missing 200Hz internal loads')
            if not np.isfinite(np.r_[action,obs,world.core.data.qpos,world.core.data.qvel]).all():raise ValueError('nonfinite rollout')
            actions.append(action);observations.append(obs)
            load=max(s['total_normal_n'] for s in loads[-4:])
            torque=np.asarray(row['motor_torque_physics_nm'])
            margin=row['minimum_actual_joint_margin_rad']
            cost+=.02*((row['speed_m_s']/.04)**2+(row['yaw_rate_rad_s']/.15)**2+(row['tilt_deg']/15)**2
                +100*(max(0,.02-margin)/.02)**2+100*max(0,load-1)**2
                +10*float((abs(torque)>=.98*.6405236195572268).mean()))
            if record:
                row.update(case_id=f'{source["session"]["id"]}--window-{index+1}',session_id=source['session']['id'],
                    session_time_s=(i+1)*.02,time_s=(local+1)*.02,actor_observation=obs.tolist(),
                    self_load_physics=[{**s,'interval_start_s':local*.02+j*.005} for j,s in enumerate(loads[-4:])])
                rows.append(row)
    elapsed=len(actions)
    if world.fell:cost+=100000+10000*(end-start-elapsed)*.02
    return dict(rows=rows,actions=np.asarray(actions,np.float32).reshape(-1,14),
                observations=np.asarray(observations,np.float32).reshape(-1,61),cost=float(cost),fell=bool(world.fell),controls=elapsed)


def score(prefix,suffix,source):
    from experiments.walking.posture import evaluate_case
    from experiments.walking.self_contact import SelfContactProbe,evaluate_self_contact
    from experiments.walking.self_load import evaluate_self_load
    from experiments.walking.endurance_v23 import evaluate_endurance
    from scripts.audit_v23_session_heading import audit
    rows=prefix+suffix;reports=[]
    geometry=SelfContactProbe(ROOT/'experiments/walking/models/contact-v11/scene.xml')
    for index,window in enumerate(source['session']['windows']):
        case=f'{source["session"]["id"]}--window-{index+1}';part=[r for r in rows if r['case_id']==case]
        if not part:report=dict(passed=False,failures=['not_run_after_terminal_fall'])
        else:
            try:report=evaluate_case(part,{'id':case,'command':window['command']},{**source['suite'],**window})
            except (ValueError,IndexError) as exc:report=dict(passed=False,failures=['missing_or_invalid_case_evidence:'+str(exc)])
            report.update(self_contact=evaluate_self_contact(part,geometry,round(window['duration_s']*50)),
                self_load=evaluate_self_load([s for r in part for s in r['self_load_physics']],window['duration_s']),
                endurance=evaluate_endurance(part,window,source['suite']['thresholds']))
            for key in ['self_contact','self_load','endurance']:report['failures'] += [key+':'+f for f in report[key]['failures']]
            report['passed']=not report['failures']
        report.update(case_id=case,observed_controls=len(part));reports.append(report)
    duration=sum(w['duration_s'] for w in source['session']['windows'])
    loads=[{**s,'interval_start_s':i*.02+j*.005} for i,r in enumerate(rows) for j,s in enumerate(r['self_load_physics'])]
    loading=evaluate_self_load(loads,duration)
    try:heading=audit(rows,duration)
    except (ValueError,AssertionError) as exc:heading={'passed':False,'failure':str(exc)}
    first_window=command_at(len(prefix),source['session'])[1]
    return dict(passed=all(r['passed'] for r in reports) and loading['passed'] and heading['passed'],
        current_window_passed=reports[first_window]['passed'],
        restart_window_passed=reports[first_window+1]['passed'] if first_window+1<len(reports) else None,
        observed_duration_s=len(rows)*.02,required_duration_s=duration,case_reports=reports,
        full_session_internal_load=loading,whole_session_heading=heading,
        prefix_controls=len(prefix),suffix_controls=len(suffix),resets_within_continuation=0)


def store_rollout(folder,result):
    folder.mkdir(parents=True,exist_ok=False)
    with gzip.open(folder/'trajectory.jsonl.gz','wt') as stream:
        for row in result['rows']:stream.write(json.dumps(row)+'\n')
    np.save(folder/'actions-float32.npy',result['actions'])
    np.save(folder/'observations-float32.npy',result['observations'])


def exact(a,b):
    assert a['actions'].shape==b['actions'].shape and a['actions'].tobytes()==b['actions'].tobytes()
    assert a['observations'].tobytes()==b['observations'].tobytes()
    assert len(a['rows'])==len(b['rows'])
    for x,y in zip(a['rows'],b['rows']):
        assert np.array_equal(x['qpos'],y['qpos']) and np.array_equal(x['qvel'],y['qvel'])
