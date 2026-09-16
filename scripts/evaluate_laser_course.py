"""Frozen, bounded moving-laser course evaluation. No training or hardware."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import numpy as np
import mujoco
from experiments.laser.course_v2 import (CourseWorld,materialize_course,laser_target,navigation_command,
                                        obstacle_contacts,DURATION,MOVE_START,MOVE_END,STATIONS,path_y)
from experiments.laser.gait import GaitProbe,summarize_gait
from experiments.walking.self_load import read_self_load,evaluate_self_load
from experiments.walking.self_contact import SelfContactProbe,evaluate_self_contact
from experiments.walking.posture import posture_metrics,POSTURE_LIMITS
from evaluator.core import OnnxPolicy

SOURCE=ROOT/'receipts/walking/20260906-v30-flat-regression'
CASES=[{'id':'nominal','yaw':0.,'motor_ticks':4,'mass':1.,'friction':1.,'mirror':1},
       {'id':'heading-offset','yaw':.04,'motor_ticks':4,'mass':1.,'friction':1.,'mirror':1},
       {'id':'motor-30ms','yaw':0.,'motor_ticks':6,'mass':1.,'friction':1.,'mirror':1},
       {'id':'low-friction','yaw':0.,'motor_ticks':4,'mass':1.,'friction':.6,'mirror':1},
       {'id':'higher-inertia','yaw':0.,'motor_ticks':4,'mass':1.1,'friction':1.,'mirror':1},
       {'id':'mirrored','yaw':-.04,'motor_ticks':4,'mass':1.,'friction':1.,'mirror':-1}]

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

@contextmanager
def physics_observer(world):
    original=mujoco.mj_step
    samples=[]
    def step(m,d,*args,**kwargs):
        if m is not world.core.model or d is not world.core.data:raise ValueError('foreign physics')
        original(m,d,*args,**kwargs)
        samples.append({'interval_start_s':len(samples)*.005,**read_self_load(m,d),
                        'course_contact':obstacle_contacts(m,d,world.obstacles)})
    mujoco.mj_step=step
    try:yield samples
    finally:mujoco.mj_step=original

def verify_actor_sources():
    expected={line.split()[-1].lstrip('*'):line.split()[0] for line in (SOURCE/'SHA256SUMS').read_text().splitlines()}
    for name in ['policy.onnx','standing/policy.onnx','training.json','standing/training.json']:
        if sha(SOURCE/name)!=expected[name]:raise ValueError('actor receipt drift: '+name)
    return {n:sha(SOURCE/n) for n in ['policy.onnx','standing/policy.onnx']}

def source_freeze(output,case,duration):
    # Freeze the transitive local Python sources actually imported by this task.
    paths={Path(__file__).resolve(),ROOT/'experiments/laser/COURSE-v1.md'}
    for module in list(sys.modules.values()):
        name=getattr(module,'__file__',None)
        if name:
            p=Path(name).resolve()
            if p.is_file() and p.is_relative_to(ROOT) and p.suffix=='.py' and not p.is_relative_to(ROOT/'.venv-apple') and not p.is_relative_to(ROOT/'.workspace'):
                paths.add(p)
    record={'schema':'microduck.laser-course-freeze/v1','created_at':datetime.now(timezone.utc).isoformat(),
            'case':case,'duration_s':duration,'actors':verify_actor_sources(),
            'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)},
            'proof_class':'visible_development','protected_bank_opened':False}
    for p in paths:
        dest=output/'source'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    (output/'freeze.json').write_text(json.dumps(record,indent=2)+'\n')
    return record

def collision_audit(world):
    m=world.core.model
    robot=[i for i in range(m.ngeom) if m.geom_bodyid[i] and (m.geom_contype[i] or m.geom_conaffinity[i])]
    coverage=[]
    for g in sorted(world.obstacles):
        pairs=[r for r in robot if (m.geom_contype[g]&m.geom_conaffinity[r]) or (m.geom_contype[r]&m.geom_conaffinity[g])]
        if len(pairs)!=len(robot):raise ValueError('incomplete obstacle collision masks')
        coverage.append({'name':m.geom(g).name,'robot_collider_pairs':len(pairs),'position':m.geom_pos[g].tolist(),'size':m.geom_size[g].tolist()})
    # Deliberately collide a COPY with a barrier to prove engine filtering.
    copied=mujoco.MjData(m);mujoco.mj_copyData(copied,m,world.core.data)
    g=m.geom('course_barrier_0').id
    copied.qpos[:2]=m.geom_pos[g,:2]
    mujoco.mj_forward(m,copied)
    witness=obstacle_contacts(m,copied,world.obstacles)
    if 'course_barrier_0' not in witness['obstacles'] or witness['maximum_penetration_m']<=0:raise ValueError('missing active collision witness')
    return {'obstacles':coverage,'copied_pose_collision_witness':witness,'physical_state_modified':False}

def score(rows,samples,world,duration,case,scene):
    gait=summarize_gait(rows)
    # GaitProbe's historical text describes its original reduced model. This
    # receipt separately binds complete-contact-v11 and its collision audit.
    geometry=evaluate_self_contact(rows,SelfContactProbe(scene),round(duration*50))
    internal=evaluate_self_load(samples,duration)
    posture=posture_metrics(rows)
    failures=list(gait['rejection_reasons'])+geometry['failures']+internal['failures']
    if len(rows)!=round(duration*50):failures.append('incomplete_duration')
    if duration!=DURATION:failures.append('diagnostic_duration_only')
    post=[r for r in rows if 3<=r['time_s']<MOVE_END and r['target_visible']]
    tracking=float(np.mean([r['target_distance_m']<=.45 for r in post])) if post else 0.
    if tracking<.90:failures.append('moving_target_tracking')
    reached=[]
    start_index=0
    for x in STATIONS:
        p=np.array([x,path_y(x,case['mirror'])])
        for i in range(start_index,len(rows)):
            if np.linalg.norm(np.array(rows[i]['robot_xyz_m'][:2])-p)<=.25:
                reached.append({'x':x,'time_s':rows[i]['time_s']});start_index=i+1;break
        else:break
    if len(reached)!=len(STATIONS):failures.append('missing_ordered_course_stations')
    if rows[-1]['robot_xyz_m'][0]<4.95:failures.append('finish_not_reached')
    # Proximity before a gate is not traversal. Require crossing and clearance.
    gate_crossings=[]
    for name in ['course_gate_0_beam','course_gate_1_beam']:
        beam=world.core.model.geom(name).id
        x,y=world.core.model.geom_pos[beam,:2]
        crossings=[r for previous,r in zip(rows,rows[1:]) if previous['robot_xyz_m'][0]<x<=r['robot_xyz_m'][0]
                   and abs(r['robot_xyz_m'][1]-y)<.30]
        cleared=bool(rows[-1]['robot_xyz_m'][0]>x+.20)
        gate_crossings.append({'gate':name,'x_m':float(x),'crossing_time_s':crossings[0]['time_s'] if crossings else None,'cleared':cleared})
        if not crossings or not cleared:failures.append('gate_not_traversed:'+name)
    impacts=[s['course_contact'] for s in samples]
    max_load=max((s['maximum_load_n'] for s in impacts),default=0.)
    max_depth=max((s['maximum_penetration_m'] for s in impacts),default=0.)
    if max_load>.1 or max_depth>.0001:failures.append('robot_obstacle_contact')
    for key,limit in POSTURE_LIMITS.items():
        if posture[key]>limit:failures.append('posture_'+key)
    stop=[r for r in rows if r['time_s']>=DURATION-2]
    stops={}
    if len(stop)!=101:failures.append('missing_final_stop')
    else:
        stops={'speed_m_s':max(r['speed_m_s'] for r in stop),'yaw_rad_s':max(abs(r['yaw_rate_rad_s']) for r in stop),'tilt_deg':max(r['tilt_deg'] for r in stop)}
        for key,limit in [('speed_m_s',.04),('yaw_rad_s',.15),('tilt_deg',15)]:
            if stops[key]>limit:failures.append('stop_'+key)
        final_posture=posture_metrics(stop)
        for key,limit in POSTURE_LIMITS.items():
            if final_posture[key]>limit:failures.append('final_posture_'+key)
    torque=np.array([r['motor_torque_physics_nm'] for r in rows])
    limit=.6405236195572268
    sat=float(np.mean(np.abs(torque)>=.98*limit))
    if abs(torque).max()>limit+1e-6 or sat>.02:failures.append('torque_limit_or_saturation')
    margin=min(r['minimum_actual_joint_margin_rad'] for r in rows)
    if margin<.02:failures.append('actual_joint_margin')
    response={}
    if post:
        v=np.array([r['body_velocity_m_s'] for r in post]);w=np.array([r['yaw_rate_rad_s'] for r in post]);cmd=np.array([r['command'] for r in post])
        response={'forward_error_m_s':float(abs(v[:,0]-cmd[:,0]).mean()),'lateral_velocity_m_s':float(abs(v[:,1]).mean()),'yaw_error_rad_s':float(abs(w-cmd[:,2]).mean())}
        for key,limit in [('forward_error_m_s',.05),('lateral_velocity_m_s',.05),('yaw_error_rad_s',.20)]:
            if response[key]>limit:failures.append(key)
    return {'passed':not failures,'failures':sorted(set(failures)),'gait':gait,'posture':posture,'self_contact':geometry,'self_load':internal,
            'course':{'ordered_stations':reached,'tracking_fraction_within_45cm':tracking,'final_position_m':rows[-1]['robot_xyz_m'],
                      'maximum_obstacle_load_n':max_load,'maximum_obstacle_penetration_m':max_depth,'gate_crossings':gate_crossings},
            'stop':stops,'motor':{'saturation_fraction':sat,'minimum_actual_margin_rad':margin},'command_response':response}

def run(output,case,duration,negative=False):
    output.mkdir(parents=True,exist_ok=False)
    freeze=source_freeze(output,case,duration)
    scene=materialize_course(output/'model',case['mirror'])
    world=CourseWorld(SOURCE/'policy.onnx',ROOT/'.workspace/bam',standing_policy=SOURCE/'standing/policy.onnx',
                      model_directory=ROOT/'experiments/walking/models/contact-v11',terrain_scene=scene,
                      domain={'mass_inertia_scale':case['mass'],'sliding_friction_scale':case['friction']},
                      motor_ticks=case['motor_ticks'],sensor_ticks=1,yaw=case['yaw'],seed=26091301,render=False)
    probe=GaitProbe(world.core)
    actors={role:OnnxPolicy(SOURCE/name,world.core.config['inference']) for role,name in [('walking','policy.onnx'),('standing','standing/policy.onnx')]}
    rows=[];actions=[];observations=[];exception=None
    try:
        audit=collision_audit(world)
        with gzip.open(output/'trajectory.jsonl.gz','wt') as stream,physics_observer(world) as samples:
            for i in range(round(duration*50)):
                target,visible=laser_target(i*.02,case['mirror'])
                command=navigation_command(target,world.core.data.qpos[:2],world.core.data.qpos[3:7],visible)
                if negative:command[:]=0
                row=probe.sample(world.step_command(command))
                expected,_=actors[row['actor_mode']].infer(world.last_observation)
                if expected[0].tobytes()!=world.last_action.tobytes():raise ValueError('motor action is not exact ONNX output')
                row.update(target_xy_m=target.tolist(),target_visible=visible,
                           target_distance_m=float(np.linalg.norm(target-world.core.data.qpos[:2])),
                           actor_observation=world.last_observation[0].tolist(),physics_samples=samples[-4:])
                assert abs(world.core.data.time-row['time_s'])<1e-7
                rows.append(row);actions.append(world.last_action.copy());observations.append(world.last_observation[0].copy())
                stream.write(json.dumps(row,separators=(',',':'))+'\n')
                if i%500==499:print(json.dumps({'case':case['id'],'time_s':row['time_s'],'position':row['robot_xyz_m'],'distance':row['target_distance_m'],'fell':row['fell']}),flush=True)
                if world.fell:break
        result=score(rows,samples,world,duration,case,scene)
        result.update(schema='microduck.laser-course-evaluation/v1',case=case,complete=len(rows)==round(duration*50),duration_s=len(rows)*.02,
                      source_freeze_sha256=sha(output/'freeze.json'),collision_audit=audit,
                      materialized_domain=world.materialized_domain,physics_samples=len(samples),
                      exact_onnx_rows=len(rows),no_root_pose_writes=True,resets_within_session=0,
                      model_variant='complete-contact-v11 with solid course geometry',
                      controller='V21 walker / V15 stander / V30 heading / moving-dot command v1 / extended route v2',
                      boundary='Exposed coordinate-target simulation development. No camera control, calibrated physical accuracy, protected-bank acceptance or transfer claim.')
        np.savez_compressed(output/'motion.npz',qpos=np.array([r['qpos'] for r in rows]),qvel=np.array([r['qvel'] for r in rows]),target=np.array([r['target_xy_m'] for r in rows]),visible=np.array([r['target_visible'] for r in rows]),actions=np.array(actions,np.float32),observations=np.array(observations,np.float32))
        (output/'evaluation.json').write_text(json.dumps(result,indent=2)+'\n')
        for name,digest in freeze['source_sha256'].items():
            if sha(ROOT/name)!=digest:raise ValueError('source changed during evaluation: '+name)
        (output/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(output)}\n' for p in sorted(output.rglob('*')) if p.is_file()))
        print(json.dumps({'case':case['id'],'passed':result['passed'],'failures':result['failures'],'course':result['course'],
                          'steps':result['gait']['qualified_swings_left_right'],'slip':result['gait']['loaded_slip_over_3cm_s_fraction']}),flush=True)
    except BaseException as exc:
        (output/'terminal-error.json').write_text(json.dumps({'error':repr(exc),'rows':len(rows)}));raise
    finally:world.close()

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--case',choices=[c['id'] for c in CASES]+['all'],default='nominal');p.add_argument('--duration',type=float,default=DURATION);p.add_argument('--negative',action='store_true');a=p.parse_args()
    if not 2<=a.duration<=DURATION:raise ValueError('bounded duration required')
    for case in CASES if a.case=='all' else [next(c for c in CASES if c['id']==a.case)]:
        run(a.output/case['id'] if a.case=='all' else a.output,case,a.duration,a.negative)

if __name__=='__main__':main()
