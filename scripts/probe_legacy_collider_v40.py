"""Three-lane fixed-action replay; immutable V1 receipts remain the controls."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.probe_public_surface_action_replay_v1 import binding as prior_binding, CASES
from scripts.evaluate_laser import digest

FREEZE = ROOT/'experiments/walking/legacy-collider-freeze-v40.json'
PRIOR = ROOT/'receipts/walking/20260906-v25-action-replay'


def binding():
    value = prior_binding()
    from scripts.probe_matched_contact_v31 import binding as v31_binding
    value['source_sha256'].update(v31_binding()['source_sha256'])
    value.update(schema='microduck.legacy-collider-freeze/v40',
                 prior_replay_manifest_sha256=digest(PRIOR/'SHA256SUMS'),
                 support_representation='original native plane; matched native boxes; unchanged Genesis boxes')
    for name in ['scripts/probe_legacy_collider_v40.py', 'experiments/walking/LEGACY-COLLIDER-v40.md', 'microduck/exact_hull_env_v34.py', 'experiments/walking/collider_geometry_v34.py']:
        value['source_sha256'][name] = digest(ROOT/name)
    for line in (PRIOR/'SHA256SUMS').read_text().splitlines():
        sha, name = line.split('  ', 1)
        path = (PRIOR/name).resolve()
        if not path.is_relative_to(PRIOR.resolve()) or digest(path) != sha:
            raise ValueError('prior replay changed')
    return value


def native_replay(output, index, session, actions, rows, boxes):
    import mujoco
    import numpy as np
    from evaluator.core import EvaluatorCore
    from experiments.walking.collision_model import model_documents, verify_physical_arrays
    from experiments.walking.public_surface_v25 import training_panels, configure_native, PROFILES
    from experiments.walking.world import TargetDelay
    directory = output/f'native-{index}-{"boxes" if boxes else "plane"}'
    directory.mkdir()
    docs = model_documents(directory)
    scene = ET.fromstring(docs['scene.xml'])
    if boxes:
        world = scene.find('worldbody')
        world.remove(world.find("geom[@name='floor']"))
        panels = ET.parse(training_panels(output/'panels.xml')).getroot()
        for geom in panels.find('worldbody'):
            world.append(geom)
        docs['scene.xml'] = ET.tostring(scene, encoding='unicode')
    for name, content in docs.items():
        (directory/name).write_text(content)
    c = EvaluatorCore(ROOT/CASES[index][0]/'policy.onnx', ROOT/'.workspace/bam', 'microduck.walking.v1')
    model = mujoco.MjModel.from_xml_path(str(directory/'scene.xml'))
    original = mujoco.MjModel.from_xml_path(str(ROOT/'experiments/walking/models/contact-v11/scene.xml'))
    verify_physical_arrays(original, model)
    c.model, c.data = model, mujoco.MjData(model)
    c._validate_model()
    if boxes: model.opt.disableflags |= int(mujoco.mjtDisableBit.mjDSBL_NATIVECCD)
    c._configure_torque_actuators()
    c.controller = c._build_bam_controller(ROOT/'.workspace/bam')
    profile = next(i for i,p in enumerate(PROFILES) if p['id'] == session['profile']['id'])
    if boxes:
        for name in ('left_foot_collision', 'right_foot_collision'):
            model.geom_friction[model.geom(name).id,0] = .1
    else:
        configure_native(model, session['profile'])
    offset = 16.*profile if boxes else 0.
    yaw = session['yaw']
    c.reset([0., offset, .125], [np.cos(yaw/2),0.,0.,np.sin(yaw/2)])
    delay = TargetDelay(c.home, 6)
    history = []
    for action in actions:
        target = c.home + action.astype(np.float64)
        for substep in range(4):
            applied = delay.step(target)
            for j,name in enumerate(c.joint_names):
                c.controller.set_q_target(name, float(applied[j]))
            c.controller.update()
            torque = c.data.ctrl.copy()
            mujoco.mj_step(model, c.data)
            qpos = c.data.qpos.copy(); qpos[1] -= offset
            contacts = []
            for k,contact in enumerate(c.data.contact):
                force = np.zeros(6); mujoco.mj_contactForce(model, c.data, k, force)
                contacts.append(dict(geoms=[model.geom(int(g)).name for g in (contact.geom1,contact.geom2)],
                    position=contact.pos.tolist(), penetration_m=max(0.,float(-contact.dist)),
                    force_contact_frame=force.tolist(), solref=contact.solref.tolist()))
            history.append(dict(time_s=float(c.data.time), qpos=qpos.tolist(), target=applied.tolist(),
                torque=torque.tolist(), contacts=contacts))
    if not boxes:
        np.testing.assert_allclose([r['qpos'] for r in history[3::4]], [r['qpos'] for r in rows], rtol=0, atol=1e-10)
    with gzip.open(directory/'physics.jsonl.gz', 'wt') as stream:
        for row in history: stream.write(json.dumps(row)+'\n')
    return history


def run(output, result):
    import genesis as gs
    import numpy as np
    import torch
    from microduck.bam_actuator import DelayBuffer
    from microduck.exact_hull_env_v34 import ExactHullWalkingEnv as PublicSurfaceWalkingEnv
    from experiments.walking.public_surface_v25 import PROFILES
    torch.set_num_threads(1)
    gs.init(backend=gs.cpu, logging_level='warning', seed=26090625)
    env = PublicSurfaceWalkingEnv(1, demo=True, model_directory=ROOT/'experiments/walking/models/contact-v11', surface_xml=output/'panels.xml')
    from experiments.walking.collider_geometry_v34 import audit_geometry
    env.reset(); env.place([0.,0.,.125])
    result['geometry_audit'] = audit_geometry(env)
    if max(r['max_support_difference_m'] for r in result['geometry_audit']) > 1e-6: raise ValueError('authored collision hull mismatch')
    ids = torch.arange(1, device=env.device)
    for index,(directory,session_id) in enumerate(CASES):
        native = ROOT/directory; suite = json.loads((native/'suite.json').read_text())
        assert (suite['motor_ticks'],suite['sensor_ticks']) == (6,1)
        session = next(s for s in suite['sessions'] if s['id'] == session_id)
        profile = next(i for i,p in enumerate(PROFILES) if p['id'] == session['profile']['id'])
        case_id = session_id+'--window-1'; rows = []
        with (native/'trajectory.jsonl').open() as stream:
            for line in stream:
                r = json.loads(line)
                if r['case_id'] == case_id: rows.append(r)
                if len(rows) == 50: break
        actions = np.load(native/(case_id+'-actions-float32.npy'), allow_pickle=False)[:len(rows)]
        assert actions.dtype == np.float32 and actions.shape == (len(rows),14) and len(rows)
        np.testing.assert_array_equal(actions, np.asarray([r['action_rad'] for r in rows], np.float32))
        plane = native_replay(output,index,session,actions,rows,False)
        boxes = native_replay(output,index,session,actions,rows,True)
        env.bam._delay = DelayBuffer((1,14),6,6,0,env.device)
        for key,dim in [('base_ang_vel',3),('projected_gravity',3),('joint_vel',14)]:
            env.obs_delays[key] = DelayBuffer((1,dim),1,1,0,env.device)
        env.reset(); env.env_origins[0] = torch.tensor([0.,16.*profile,0.],device=env.device)
        env.bam.vin_nominal.fill_(7.35); env.bam.vin_drop_resistance.zero_()
        for delay in env.obs_delays.values(): delay.reset(ids)
        env.set_twist(0.,0.,0.); env.place([0.,16.*profile,.125],yaw=session['yaw'])
        env.bam._delay._buf[:] = env.default_dof_pos; env.bam._delay._needs_fill[:] = False
        delay, compute, step = env.bam._delay, env.bam.compute, env.scene.step
        actual_target, actual_torque, history = [], [], []
        def observed_delay(target):
            actual = delay(target); actual_target[:] = actual[0].cpu().tolist(); return actual
        def observed_compute(target):
            torque = compute(target); actual_torque[:] = torque[0].cpu().tolist(); return torque
        def observed_step():
            step()
            qpos = np.r_[env.robot.get_pos()[0].cpu(),env.robot.get_quat()[0].cpu(),env.robot.get_dofs_position(env.motors_dof_idx)[0].cpu()].astype(float)
            qpos[1] -= 16.*profile
            data = env.robot.get_contacts()
            contacts = {key:value[0][data['valid_mask'][0]].cpu().tolist() for key,value in data.items() if key != 'valid_mask'}
            history.append(dict(time_s=(len(history)+1)*.005,qpos=qpos.tolist(),target=list(actual_target),
                torque=list(actual_torque),contacts=contacts))
        env.bam._delay, env.bam.compute, env.scene.step = observed_delay, observed_compute, observed_step
        try:
            for row,action in zip(rows,actions):
                env.set_twist(*row['policy_command'])
                _,_,done,_ = env.step(torch.from_numpy(action[None,:].copy()).to(env.device))
                if bool(done[0]) or action.tobytes() != env.actions[0].cpu().numpy().tobytes():
                    raise ValueError('reset or altered action')
                np.testing.assert_allclose(actual_target,row['applied_servo_target_rad'],rtol=0,atol=2e-7)
        finally:
            env.bam._delay, env.bam.compute, env.scene.step = delay, compute, step
        old = [json.loads(line) for line in (PRIOR/f'case-{index}.jsonl').read_text().splitlines()]
        observer_delta = float(np.abs(np.asarray([r['qpos'] for r in history[3::4]])-np.asarray([r['qpos'] for r in old])).max())
        with gzip.open(output/f'genesis-{index}-physics.jsonl.gz','wt') as stream:
            for row in history: stream.write(json.dumps(row)+'\n')
        np.save(output/f'case-{index}-actions-float32.npy',actions)
        item = dict(session_id=session_id,input_receipt=directory,steps=len(rows),physics_steps=len(history),
            action_bytes_sha256=hashlib.sha256(actions.tobytes()).hexdigest(),action_bytes_identical=True,
            native_plane_reproduced=True,genesis_variant='original-mpr-no-mesh-decimation',native_box_variant='legacy-mpr',genesis_original_max_qpos_delta=observer_delta,comparisons={})
        for name, first, second in [('plane_genesis',plane,history),('boxes_genesis',boxes,history),('plane_boxes',plane,boxes)]:
            q1,q2 = np.asarray([r['qpos'] for r in first]),np.asarray([r['qpos'] for r in second])
            if not np.isfinite(q1).all() or not np.isfinite(q2).all(): raise ValueError('nonfinite state')
            base = np.linalg.norm(q1[:,:3]-q2[:,:3],axis=1)
            joints = np.rad2deg(np.abs(q1[:,7:]-q2[:,7:]).max(1))
            bad = np.flatnonzero((base[3::4]>.002)|(joints[3::4]>5.))
            item['comparisons'][name] = dict(max_base_error_m=float(base[3::4].max()),max_joint_error_deg=float(joints[3::4].max()),
                max_physics_base_error_m=float(base.max()),max_physics_joint_error_deg=float(joints.max()),
                first_threshold_divergence_s=float((bad[0]+1)*.02) if len(bad) else None,passed=not len(bad))
        result['cases'].append(item); print(json.dumps(item),flush=True)


def main():
    p = argparse.ArgumentParser(); p.add_argument('--freeze',action='store_true'); p.add_argument('--output',type=Path); a=p.parse_args()
    frozen = binding()
    if a.freeze:
        with FREEZE.open('x') as stream: json.dump(frozen,stream,indent=2); stream.write('\n')
        return
    if a.output is None: p.error('fresh output required')
    if json.loads(FREEZE.read_text()) != json.loads(json.dumps(frozen)): raise ValueError('freeze changed')
    a.output.mkdir(parents=True,exist_ok=False)
    result = dict(schema='microduck.legacy-collider/v40',status='starting',cases=[],physical_calibration=False)
    started = time.monotonic()
    try:
        run(a.output,result)
        if binding() != frozen: raise ValueError('inputs changed during replay')
        result['status'] = 'completed'
    except BaseException as exc:
        result.update(status='failed',failure=f'{type(exc).__name__}: {exc}'); raise
    finally:
        result['elapsed_s'] = time.monotonic()-started
        (a.output/'probe.json').write_text(json.dumps(result,indent=2)+'\n')
        shutil.copy2(FREEZE,a.output/'freeze.json')
        for name in frozen['source_sha256']:
            target = a.output/'source'/name; target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(ROOT/name,target)
        (a.output/'SHA256SUMS').write_text(''.join(f'{digest(f)}  {f.relative_to(a.output)}\n' for f in sorted(a.output.rglob('*')) if f.is_file() and f.name!='SHA256SUMS'))


if __name__ == '__main__': main()
