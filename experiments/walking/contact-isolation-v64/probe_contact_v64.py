"""V64 version of the frozen V63 probe: isolated contact/export/subdivision changes."""
from pathlib import Path
import argparse
import gzip
import hashlib
import json
import signal
import sys
import time
import xml.etree.ElementTree as ET
import numpy as np
import mujoco

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from evaluator.core import EvaluatorCore, projected_gravity
from experiments.walking.world import TargetDelay
from metrics_v64 import classify, strict_action, dynamics_digest
from contact_v64 import PHYSICAL, SHELLS, clock_subdivisions, match_export, mask_shell_floor, mask_changes


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def passive_update(core):
    """Zero electrical motor torque; retain BAM rotor inertia and mechanical friction.

    No firmware control, voltage-drop history or electrical braking is simulated.
    External-load/friction separation matches the pinned BAM controller.
    """
    c, m, d = core.controller, core.model, core.data
    external = -d.qfrc_bias[c.dof_indexes]+d.qfrc_constraint[c.dof_indexes]
    selector = (np.asarray(c.joint_indexes)[:,None] == d.efc_id[None,:]) & (
        d.efc_type[None,:] == int(mujoco.mjtConstraint.mjCNSTR_FRICTION_DOF))
    external -= np.sum(d.efc_force[None,:]*selector, axis=1)
    friction, damping = c.model.compute_frictions(np.zeros(len(c.actuator)), external, d.qvel[c.dof_indexes])
    m.dof_frictionloss[c.dof_indexes] = friction
    m.dof_damping[c.dof_indexes] = damping
    d.ctrl[:] = 0.
    c._prev_motor_torque[:] = 0.
    c.last_ts = d.time


def physical_snapshot(core):
    m,d,c = core.model,core.data,core.controller
    return {name:getattr(m,name).copy() for name in ['body_mass','body_inertia','body_ipos','body_iquat',
        'body_pos','body_quat','jnt_range','dof_armature','dof_damping','dof_frictionloss',
        'geom_contype','geom_conaffinity','geom_friction','actuator_gainprm','actuator_biasprm',
        'actuator_forcerange']} | {'qpos':d.qpos.copy(),'qvel':d.qvel.copy(),'ctrl':d.ctrl.copy(),
        'target':c.q_target.copy(),'previous_motor_torque':c._prev_motor_torque.copy()}


def sample_contacts(core, sole_ids):
    m,d = core.model,core.data
    records, pairs = [], {}
    internal_depth=ground_depth=nonsole=0.
    sole_load = np.zeros(2)
    sole_speed_load = np.zeros(2)
    for index,contact in enumerate(d.contact):
        a,b = int(contact.geom1),int(contact.geom2)
        force = np.zeros(6)
        mujoco.mj_contactForce(m,d,index,force)
        if not np.isfinite(force).all():
            raise RuntimeError('nonfinite applied contact force')
        normal=max(0.,float(force[0]));depth=max(0.,-float(contact.dist))
        internal = bool(m.geom_bodyid[a] and m.geom_bodyid[b])
        if internal:
            key=tuple(sorted((a,b)));pairs[key]=pairs.get(key,0.)+normal
            internal_depth=max(internal_depth,depth)
        else:
            ground_depth=max(ground_depth,depth)
            robot = a if m.geom_bodyid[a] else b
            if robot in sole_ids:
                j=sole_ids.index(robot);sole_load[j]+=normal
                jac=np.zeros((3,m.nv))
                mujoco.mj_jac(m,d,jac,None,contact.pos,int(m.geom_bodyid[robot]))
                slip=np.linalg.norm(contact.frame.reshape(3,3)[1:] @ (jac@d.qvel))
                sole_speed_load[j]+=normal*slip
            else:
                nonsole+=normal
        records.append({'geom_ids':[a,b],'internal':internal,'position_m':contact.pos.tolist(),
            'distance_m':float(contact.dist),'force_contact_frame':force.tolist(),
            'efc_address':int(contact.efc_address), 'solref':contact.solref.tolist(),
            'solimp':contact.solimp.tolist(), 'friction':contact.friction.tolist(),
            'dim':int(contact.dim), 'includemargin':float(contact.includemargin)})
    return {'contacts':records,'total_normal_n':sum(pairs.values()),
            'largest_pair_normal_n':max(pairs.values(),default=0.),
            'internal_penetration_m':internal_depth,'ground_penetration_m':ground_depth,
            'nonsole_ground_load_n':nonsole,'sole_load_n':sole_load.tolist(),
            'loaded_sole_slip_m_s':np.divide(sole_speed_load,sole_load,out=np.zeros(2),where=sole_load>0).tolist()}


def run(bank, case, output):
    started=time.monotonic()
    variant=bank['models'][case['model']]
    source_robot=ROOT/variant['robot_xml']
    robot=ET.parse(source_robot).getroot()
    compiler=robot.find('compiler')
    compiler.set('meshdir',str((source_robot.parent/compiler.get('meshdir')).resolve()))
    scene=ET.parse(ROOT/bank['scene_template']).getroot()
    intervention=case['intervention']; changes=[]
    if intervention=='match_v11_export':
        changes=match_export(robot,ET.parse(ROOT/bank['models']['v11']['robot_xml']).getroot())
    elif intervention=='mask_shell_floor':
        mask_shell_floor(robot,scene)
    elif intervention!='none':raise ValueError('unknown intervention')
    robot_path=output/'robot.xml';robot_path.write_text(ET.tostring(robot,encoding='unicode')+'\n')
    scene.find('include').set('file',str(robot_path.resolve()))
    scene_path=output/'scene.xml';scene_path.write_text(ET.tostring(scene,encoding='unicode')+'\n')
    core=EvaluatorCore(ROOT/bank['policy'],ROOT/bank['bam_repo'],'microduck.walking.v1')
    model=mujoco.MjModel.from_xml_path(str(scene_path))
    core.model,core.data=model,mujoco.MjData(model)
    before={name:getattr(model,name).copy() for name in ['body_mass','body_inertia','jnt_range',
        'dof_armature','dof_damping','dof_frictionloss','actuator_gainprm','actuator_biasprm','actuator_forcerange']}
    core._validate_model();core._configure_torque_actuators()
    core.controller=core._build_bam_controller(ROOT/bank['bam_repo'])
    dt=case['dt_s']; microsteps=clock_subdivisions(dt); model.opt.timestep=dt
    # BAM and FIFO still update once per .005 s, independent of integration subdivision.
    with np.load(ROOT/bank['v63_root']/f"runs/{case['model']}-{case['mode']}-r1/initial-state.npz") as old:
        pairs=mask_changes(old['geom_contype'],old['geom_conaffinity'],model.geom_contype,model.geom_conaffinity)
    wanted=sorted([[min(model.geom('floor').id,model.geom(n).id),max(model.geom('floor').id,model.geom(n).id),True,False] for n in SHELLS]) if intervention=='mask_shell_floor' else []
    if sorted(pairs)!=wanted:raise RuntimeError('unexpected contact compatibility change')
    if model.npair or model.nexclude:raise RuntimeError('unexpected explicit pair/exclusion')
    save(output/'intervention.json',{'kind':intervention,'xml_changes':changes,'changed_compatibility_pairs':pairs,
        'all_other_compatibility_pairs_preserved':True,'compiled_explicit_pairs':model.npair,'compiled_exclusions':model.nexclude,
        'undirected_pairs_checked':model.ngeom*(model.ngeom-1)//2,'admissible_model':False})
    np.savez_compressed(output/'physical-parameters.npz',**{n:getattr(model,n).copy() for n in PHYSICAL})
    if intervention=='match_v11_export':
        with np.load(ROOT/bank['output_root']/'v11-replay-base-r1/physical-parameters.npz') as ref:
            for name in PHYSICAL:
                np.testing.assert_array_equal(getattr(model,name),ref[name],err_msg=name)
    yaw=case['yaw_rad']
    core.reset([0.,0.,.125],[np.cos(yaw/2),0.,0.,np.sin(yaw/2)])
    initial=physical_snapshot(core)
    assert not core.controller._prev_motor_torque.any() and not core.data.qvel.any() and not core.data.ctrl.any()
    np.testing.assert_array_equal(core.data.qpos[core.qpos_indices],core.home)
    np.savez_compressed(output/'initial-state.npz',**initial)
    save(output/'configuration.json',{'model_variant':case['model'],
        'active_colliders':int(np.count_nonzero((model.geom_bodyid!=0)&((model.geom_contype!=0)|(model.geom_conaffinity!=0)))),
        'total_mass_kg':float(model.body_mass.sum()),'timestep_s':model.opt.timestep,
        'gravity_m_s2':model.opt.gravity.tolist(),
        'bam_update_period_s':.005,'command_period_s':.02,'target_delay_s':bank['motor_ticks']*.005,
        'integration_subdivisions_per_bam_tick':microsteps,
        'solver_options':{n:getattr(model.opt,n) for n in ['integrator','solver','cone','iterations','tolerance','ls_iterations','ls_tolerance','disableflags','enableflags','ccd_iterations','ccd_tolerance']},
        'contact_geom_parameters':{model.geom(i).name:{n:getattr(model,n)[i].tolist() for n in ['geom_solref','geom_solimp','geom_friction','geom_priority','geom_solmix','geom_condim','geom_margin','geom_gap']} for i in range(model.ngeom) if model.geom(i).name=='floor' or model.geom(i).name in (*variant['sole_geoms'],*SHELLS)},'initial_state_sha256':dynamics_digest(initial),
        'runtime_mutated_arrays':[n for n,a in before.items() if not np.array_equal(a,getattr(model,n))],
        'geom_names':[model.geom(i).name for i in range(model.ngeom)],
        'joint_order':core.joint_names,'scope':'runtime BAM adaptation explicitly changes actuator and rotor arrays; frozen geometry remains unchanged'})
    expected=int(variant['active_colliders'])
    actual=np.count_nonzero((model.geom_bodyid!=0)&((model.geom_contype!=0)|(model.geom_conaffinity!=0)))
    if actual!=expected:raise RuntimeError('active collider count mismatch')
    sole_ids=[model.geom(name).id for name in variant['sole_geoms']]
    delay=TargetDelay(core.home,bank['motor_ticks'])
    intervals=round(case['duration_s']/.02)
    if case['mode']=='replay':
        all_actions=np.load(ROOT/bank['actions_file'],allow_pickle=False)
        actions=all_actions[:intervals].copy()
        if actions.dtype!=np.float32 or actions.shape!=(intervals,14):raise RuntimeError('invalid retained action file')
    else:
        actions=np.zeros((intervals,14),dtype=np.float32)
    np.save(output/'requested-actions-float32.npy',actions,allow_pickle=False)
    rows=[];state_arrays={key:[] for key in ['qpos','qvel','ctrl','target','actuator_force','friction','damping','loads']}
    timing={'physics_ns':[],'control_ns':[],'observer_ns':[],'controller_ns':[]}
    stop=None
    trace=gzip.open(output/'physics.jsonl.gz','wt')
    written=0
    try:
        for index,raw_action in enumerate(actions):
            cycle_start=time.perf_counter_ns()
            action=strict_action(raw_action)
            if action.tobytes()!=raw_action.tobytes():raise RuntimeError('action bytes changed')
            reference=core.home+action.astype(np.float64)
            for substep in range(4):
                applied=delay.step(reference)
                control_start=time.perf_counter_ns()
                if case['mode']=='passive':
                    passive_update(core)
                else:
                    for j,name in enumerate(core.joint_names):core.controller.set_q_target(name,float(applied[j]))
                    core.controller.update()
                timing['controller_ns'].append(time.perf_counter_ns()-control_start)
                for integration_substep in range(microsteps):
                    qpos_before=core.data.qpos.copy();t_before=float(core.data.time)
                    step_start=time.perf_counter_ns();mujoco.mj_step(model,core.data)
                    timing['physics_ns'].append(time.perf_counter_ns()-step_start)
                    observer_start=time.perf_counter_ns()
                    if not np.isfinite(np.r_[core.data.qpos,core.data.qvel,core.data.ctrl,core.data.qacc]).all():
                        raise RuntimeError('nonfinite simulation state')
                    contact=sample_contacts(core,sole_ids)
                    tilt=float(np.degrees(np.arccos(np.clip(-projected_gravity(core.data.qpos[3:7])[2],-1.,1.))))
                    margin=np.minimum(core.data.qpos[core.qpos_indices]-model.jnt_range[core.joint_ids,0],
                                      model.jnt_range[core.joint_ids,1]-core.data.qpos[core.qpos_indices])
                    row={'interval_start_s':t_before,'time_s':float(core.data.time),'action_index':index,'substep':substep,'integration_substep':integration_substep,'bam_tick':index*4+substep,
                        'qpos_before':qpos_before.tolist(),'qpos':core.data.qpos.tolist(),'qvel':core.data.qvel.tolist(),
                        'applied_target_rad':applied.tolist(),'motor_torque_nm':core.data.ctrl.tolist(),
                        'actuator_force_nm':core.data.actuator_force.tolist(),'frictionloss_nm':model.dof_frictionloss[core.dof_indices].tolist(),
                        'damping':model.dof_damping[core.dof_indices].tolist(),
                        'root_z_m':float(core.data.qpos[2]),'tilt_deg':tilt,
                        'speed_m_s':float(np.linalg.norm(core.data.qvel[:3])),
                        'angular_speed_rad_s':float(np.linalg.norm(core.data.qvel[3:6])),
                        'xy_displacement_m':float(np.linalg.norm(core.data.qpos[:2])),
                        'joint_margin_rad':float(margin.min()),'joint_margins_rad':margin.tolist(),
                        'motor_torque_max_nm':float(np.max(np.abs(core.data.ctrl))),
                        'actuator_force_max_nm':float(np.max(np.abs(core.data.actuator_force))),
                        'warnings':core.data.warning.number.tolist(),
                        'fell':bool(core.data.qpos[2]<.07 or tilt>70.),**contact}
                    row['warnings']=[i for i,n in enumerate(row['warnings']) if n]
                    rows.append(row)
                    for key,value in [('qpos',core.data.qpos),('qvel',core.data.qvel),('ctrl',core.data.ctrl),
                        ('target',applied),('actuator_force',core.data.actuator_force),
                        ('friction',model.dof_frictionloss[core.dof_indices]),('damping',model.dof_damping[core.dof_indices]),
                        ('loads',[row['total_normal_n'],row['largest_pair_normal_n'],*row['sole_load_n'],row['nonsole_ground_load_n']])]:
                        state_arrays[key].append(np.array(value,copy=True))
                    timing['observer_ns'].append(time.perf_counter_ns()-observer_start)
                    if row['warnings'] or row['internal_penetration_m']>.01 or row['ground_penetration_m']>.01 or row['speed_m_s']>5.:
                        stop='numerical_or_geometry_hard_stop'
                    if case['mode']!='passive' and row['fell']:stop='fall'
                    if stop:break
                if stop:break
            if substep==3 and integration_substep==microsteps-1:timing['control_ns'].append(time.perf_counter_ns()-cycle_start)
            if (index+1)%50==0 or stop:
                print(json.dumps({'case':case['id'],'time_s':core.data.time,'stop':stop}),flush=True)
            for pending in rows[written:]:
                trace.write(json.dumps(pending,allow_nan=False)+'\n')
            written=len(rows)
            if (index+1)%50==0 or stop:trace.flush()
            if stop:break
    finally:
        try:
            for pending in rows[written:]:trace.write(json.dumps(pending,allow_nan=False)+'\n')
        finally:
            trace.close()
    state_arrays={k:np.array(v) for k,v in state_arrays.items()}
    np.savez_compressed(output/'dynamics.npz',**state_arrays)
    np.savez_compressed(output/'timing.npz',**{k:np.array(v) for k,v in timing.items()})
    result=classify(rows,case,bank['thresholds'],timing)
    result.update(case=case,stop_reason=stop,initial_state_sha256=dynamics_digest(initial),
        dynamics_sha256=dynamics_digest(state_arrays),requested_action_bytes_sha256=hashlib.sha256(actions.tobytes()).hexdigest(),
        consumed_action_count=rows[-1]['action_index']+1 if rows else 0,
        physics_sample_count=len(rows),elapsed_seconds=time.monotonic()-started,
        contact_timing='applied solver loads for every integration interval; no extra mj_forward on physical data',
        integration_timestep_s=dt, bam_update_period_s=.005, command_period_s=.02, target_delay_s=bank['motor_ticks']*.005,
        passive_definition=bank['passive_definition'] if case['mode']=='passive' else None)
    if case['model']=='v11' and case['mode']=='replay' and dt==.005:
        golden=[]
        with (ROOT/bank['trajectory']).open() as stream:
            for line in stream:
                original=json.loads(line)
                if original['case_id']==bank['source_case']:
                    golden.append(original)
                    if len(golden)==intervals:break
        sampled=rows[3::4]
        errors={}
        for key,field in [('qpos','qpos'),('qvel','qvel'),('applied_target_rad','applied_servo_target_rad')]:
            errors[key]=float(np.max(np.abs(np.array([r[key] for r in sampled])-np.array([r[field] for r in golden[:len(sampled)]])))) if sampled else None
        errors['torque']=float(np.max(np.abs(state_arrays['ctrl']-np.array([r['motor_torque_physics_nm'] for r in golden]).reshape(-1,14)[:len(rows)]))) if rows else None
        result['golden_replay']={'passed':len(sampled)==intervals and all(v is not None and v<=1e-10 for v in errors.values()),'maximum_absolute_errors':errors,'control_intervals':len(sampled)}
    save(output/'result.json',result)
    return result


def main():
    signal.pthread_sigmask(signal.SIG_UNBLOCK,{signal.SIGINT,signal.SIGTERM})
    parser=argparse.ArgumentParser();parser.add_argument('bank',type=Path);parser.add_argument('case_id');args=parser.parse_args()
    bank=json.loads(args.bank.read_text())
    for path,digest in bank['input_sha256'].items():
        with (ROOT/path).open('rb') as stream:
            if hashlib.file_digest(stream,'sha256').hexdigest()!=digest:raise RuntimeError('changed input:'+path)
    case=next(c for c in bank['cases'] if c['id']==args.case_id)
    output=ROOT/bank['output_root']/case['id'];output.mkdir(exist_ok=False)
    try:
        result=run(bank,case,output)
    except Exception as error:
        save(output/'result.json',{'case':case,'passed':False,'error':repr(error),'physics_evidence_complete':False})
        raise
    print(json.dumps({k:v for k,v in result.items() if k not in ['passive_definition']}),flush=True)


if __name__=='__main__':main()
