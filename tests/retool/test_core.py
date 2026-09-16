import contextlib
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace as NS
import unittest

import numpy as np
from retool.metrics import Gate, score_case, paired_summary
from retool.learning import transition_labels, balanced_replay_indices, standing_face_cost
from retool.runtime import LockstepBody, Token
from retool.checkpoint import WorldCheckpoint
from retool.impact import ImpactSchedule, run_window, compare_common_grid
from retool.vision import edge_limited_twist, ReacquisitionYaw, make_follower
from retool.__main__ import main, program


class MetricsTests(unittest.TestCase):
    def test_tiny_miss_is_failure(self):
        result = Gate('yaw', .20, 'rad/s').score(.2002463513)
        self.assertEqual(result['status'], 'fail')
        self.assertLess(result['margin'], 0)

    def test_missing_nan_and_boolean_are_not_passes(self):
        for value in (None, float('nan'), float('inf'), True):
            self.assertEqual(Gate('yaw', .2, 'rad/s').score(value)['status'], 'missing')

    def test_minimum_and_zero_gates(self):
        self.assertEqual(Gate('steps', 3, 'count', 'min').score(3)['status'], 'pass')
        self.assertIsNone(Gate('falls', 0, 'count').score(1)['relative_margin'])

    def test_complete_case_requires_every_gate(self):
        gates = [Gate('yaw', .2, 'rad/s'), Gate('falls', 0, 'count', hard_failure=True)]
        self.assertFalse(score_case(gates, {'yaw': .1})['passed'])
        self.assertEqual(score_case(gates, {'yaw': .1, 'falls': 1})['hard_failures'], ['falls'])

    def test_empty_and_duplicate_gates_rejected(self):
        for gates in ([], [Gate('a', 1, 'm')]*2):
            with self.assertRaises(ValueError): score_case(gates, {})

    @staticmethod
    def runs():
        return [dict(training_seed=s, arm=a, status='completed', split='exposed_development',
                     comparison_sha256='a'*64, bank_sha256='b'*64, model_sha256='c'*64,
                     gates_sha256='d'*64, required_case_ids=['one','two'], cases={'one':True,'two':a=='control'})
                for s in (1,2,3) for a in ('control','candidate')]

    def test_paired_denominator_and_no_promotion(self):
        result = paired_summary(self.runs(), [1,2,3], ('control','candidate'))
        self.assertEqual(result['required_cases_per_run'], 2)
        self.assertEqual(result['all_cases_pass'], {'control':True, 'candidate':False})
        self.assertFalse(result['automatic_promotion'])

    def test_duplicates_are_not_replication(self):
        rows = self.runs(); rows[-1] = rows[0]
        with self.assertRaises(ValueError): paired_summary(rows, [1,2,3], ('control','candidate'))

    def test_changed_bank_or_missing_cases_rejected(self):
        for mutation in ('bank','cases','status'):
            rows = self.runs()
            if mutation == 'bank': rows[0]['bank_sha256'] = 'e'*64
            if mutation == 'cases': rows[0]['cases'].pop('two')
            if mutation == 'status': rows[0]['status'] = 'failed'
            with self.assertRaises(ValueError): paired_summary(rows, [1,2,3], ('control','candidate'))

    def test_missing_or_malformed_comparison_identity_rejected(self):
        for field in ('comparison_sha256','bank_sha256','model_sha256','gates_sha256'):
            for value in (None, '', 'unfrozen', 'z'*64):
                with self.subTest(field=field, value=value):
                    rows = self.runs()
                    for row in rows: row[field] = value
                    with self.assertRaises(ValueError):
                        paired_summary(rows, [1,2,3], ('control','candidate'))

    def test_exact_two_arms_and_integer_run_seeds_required(self):
        with self.assertRaises(ValueError):
            paired_summary(self.runs(), [1,2,3], ('control','candidate','control'))
        for value in (True, 1.):
            rows = self.runs(); rows[0]['training_seed'] = value
            with self.assertRaises(ValueError):
                paired_summary(rows, [1,2,3], ('control','candidate'))


class ReplayTests(unittest.TestCase):
    def test_transition_phases(self):
        obs = np.zeros((125,61), np.float32)
        obs[5:25,48] = .1; obs[90:,48] = .1
        labels = transition_labels(obs, np.zeros(125,int), np.zeros(125,int), np.arange(125))
        self.assertEqual(labels[[0,5,15,25,35,75,90,100]].tolist(),
                         ['initial_stand','start','walk','brake','settle','stand','restart','walk'])
        chosen = balanced_replay_indices(labels, np.random.default_rng(1), total_count=512)
        self.assertEqual(len(chosen), 512)
        self.assertEqual(set(labels[chosen]), set(labels))
        self.assertLessEqual(np.ptp(np.unique(labels[chosen], return_counts=True)[1]), 1)

    def test_reset_is_not_restart(self):
        obs = np.zeros((4,61),np.float32); obs[:,48] = .1
        labels = transition_labels(obs, [0,0,0,0], [0,0,1,1], [0,1,0,1])
        self.assertEqual(labels.tolist(), ['start']*4)

    def test_interleaved_environments_are_independent(self):
        obs = np.zeros((4,61),np.float32); obs[[1,3],48] = .1
        labels = transition_labels(obs, [0,1,0,1], [0,0,0,0], [0,0,1,1])
        self.assertEqual(labels.tolist(), ['initial_stand','start','initial_stand','start'])

    def test_missing_or_duplicate_rows_rejected(self):
        for steps in ([0,2], [0,0], [1,2]):
            with self.assertRaises(ValueError):
                transition_labels(np.zeros((2,61)), [0,0], [0,0], steps)

    def test_empty_phase_is_not_silently_ignored(self):
        with self.assertRaises(ValueError):
            balanced_replay_indices(['walk'], np.random.default_rng(1))

    def test_sampler_rng_is_explicit(self):
        labels = ['walk','stand','walk','stand']
        a = balanced_replay_indices(labels,np.random.default_rng(5),phases=('walk','stand'))
        b = balanced_replay_indices(labels,np.random.default_rng(5),phases=('walk','stand'))
        np.testing.assert_array_equal(a,b)

    def test_face_cost_standing_only(self):
        face = [np.cos(np.pi/6),0,np.sin(np.pi/6)]
        self.assertAlmostEqual(standing_face_cost(face,True,2),2)
        self.assertEqual(standing_face_cost(face,False,2),0)
        with self.assertRaises(ValueError): standing_face_cost([0,0,2],True,2)


class RuntimeTests(unittest.TestCase):
    @staticmethod
    def world():
        w = NS(core=NS(model=NS(opt=NS(timestep=.005)),data=NS(time=0.)),
               steps=0,fell=False,walking_policy=object(),standing_policy=object(),loads_count=4,
               bad_torque=False,reset_time=False)
        def advance(command):
            obs=np.zeros((1,61),np.float32);obs[0,48:51]=command
            actor=w.standing_policy if not np.any(command) else w.walking_policy
            action,_=actor.infer(obs)
            w.last_action=action[0].copy();w.steps+=1
            w.core.data.time = 0 if w.reset_time else w.core.data.time+.02
            return {'motor_torque_physics_nm':np.full((4,14),np.nan) if w.bad_torque else np.zeros((4,14))}
        w.step_command=advance
        return w

    @staticmethod
    def preview(w, command):
        obs=np.zeros((1,61),np.float32);obs[0,48:51]=command;return obs

    @staticmethod
    @contextlib.contextmanager
    def observer(w):
        yield [{'total_normal_n':0.} for _ in range(w.loads_count)]

    def bridge(self,w):
        return LockstepBody(w,'test',preview=self.preview,load_observer=self.observer)

    def test_no_physics_before_action_and_exact_raw_action(self):
        w=self.world();b=self.bridge(w);t=Token('test',0);command=np.array([.1,0,0],np.float32)
        obs=b.prepare(t,command);np.testing.assert_array_equal(obs,b.prepare(t,command))
        self.assertEqual(w.steps,0)
        action=np.linspace(-1,1,14,dtype=np.float32)
        result=b.advance(t,action)
        self.assertEqual(result['action'].tobytes(),action.tobytes())
        self.assertEqual(w.steps,1)
        self.assertFalse(result['physical_acceptance'])

    def test_duplicate_or_wrong_epoch_never_steps(self):
        w=self.world();b=self.bridge(w);t=Token('test',0)
        b.prepare(t,np.zeros(3,np.float32));b.advance(t,np.zeros(14,np.float32))
        for token in (t,Token('wrong',1)):
            with self.assertRaises(ValueError): b.prepare(token,np.zeros(3,np.float32))
        self.assertEqual(w.steps,1)

    def test_missing_loads_poison_bridge(self):
        w=self.world();w.loads_count=3;b=self.bridge(w);t=Token('test',0)
        b.prepare(t,np.zeros(3,np.float32))
        with self.assertRaises(ValueError): b.advance(t,np.zeros(14,np.float32))
        self.assertTrue(b.poisoned)
        with self.assertRaises(ValueError): b.advance(t,np.zeros(14,np.float32))
        self.assertEqual(w.steps,1)

    def test_bad_action_rejected_before_physics(self):
        w=self.world();b=self.bridge(w);t=Token('test',0);b.prepare(t,np.zeros(3,np.float32))
        for action in (np.zeros(14),np.zeros(13,np.float32),np.full(14,np.nan,np.float32)):
            with self.assertRaises(ValueError): b.advance(t,action)
        self.assertEqual(w.steps,0)

    def test_pending_command_cannot_change(self):
        w=self.world();b=self.bridge(w);t=Token('test',0);b.prepare(t,np.zeros(3,np.float32))
        with self.assertRaises(ValueError): b.prepare(t,np.ones(3,np.float32))

    def test_hidden_reset_or_nonfinite_torque_rejected(self):
        for flag in ('reset_time','bad_torque'):
            w=self.world();setattr(w,flag,True);b=self.bridge(w);t=Token('test',0)
            b.prepare(t,np.zeros(3,np.float32))
            with self.assertRaises(ValueError): b.advance(t,np.zeros(14,np.float32))
            self.assertTrue(b.poisoned)

    def test_prepare_advance_order(self):
        b=self.bridge(self.world())
        with self.assertRaises(ValueError): b.advance(Token('test',0),np.zeros(14,np.float32))


class Data(NS):
    def __copy__(self): return copy.deepcopy(self)


class CheckpointTests(unittest.TestCase):
    @staticmethod
    def world():
        from collections import deque
        m=NS(nq=21,nv=20,nu=14,names=b'robot',body_mass=np.array([.7]),
             dof_damping=np.ones(20),dof_frictionloss=np.ones(20),opt=NS(timestep=.005))
        d=Data(time=.035,qpos=np.zeros(21),qvel=np.zeros(20),ctrl=np.zeros(14),
               qacc_warmstart=np.arange(20.),qfrc_constraint=np.arange(20.),
               warning=NS(number=np.zeros(8,int)),contact=[])
        c=NS(model=m,data=d,joint_names=[str(i) for i in range(14)])
        c.controller=NS(model=m,data=d,q_target=np.zeros(14),_prev_motor_torque=np.ones(14),last_ts=.03)
        return NS(core=c,sensor_data=copy.copy(d),motor_delay=NS(history=deque([np.zeros(14)])),
                  sensor_rows=deque([np.zeros((1,61),np.float32)]),last_action=np.zeros(14,np.float32),
                  applied_target=np.zeros(14),steps=1,fell=False,command_ramp={'v':1},
                  heading_servo={'i':2},heading_sensor_history=deque([np.array([1.,0,0,0])]))

    @staticmethod
    def copy_data(dst,model,src):
        dst.__dict__.clear();dst.__dict__.update(copy.deepcopy(vars(src)))

    def test_solver_controller_and_histories_restored_without_alias(self):
        w=self.world();s=WorldCheckpoint.capture(w)
        w.core.data.qfrc_constraint[:]=0;w.core.controller._prev_motor_torque[:]=9
        w.heading_servo['i']=99;w.motor_delay.history[0][:]=8;w.core.model.dof_damping[:]=7
        s.restore(w,copy_data=self.copy_data)
        np.testing.assert_array_equal(w.core.data.qfrc_constraint,np.arange(20.))
        np.testing.assert_array_equal(w.core.controller._prev_motor_torque,np.ones(14))
        self.assertEqual(w.heading_servo['i'],2)
        self.assertIs(w.core.controller.data,w.core.data)
        w.core.controller._prev_motor_torque[:]=5
        s.restore(w,copy_data=self.copy_data)
        np.testing.assert_array_equal(w.core.controller._prev_motor_torque,np.ones(14))

    def test_model_or_timestep_drift_rejected(self):
        for field in ('mass','step'):
            w=self.world();s=WorldCheckpoint.capture(w)
            if field=='mass':w.core.model.body_mass[:]=.8
            else:w.core.model.opt.timestep=.0025
            with self.assertRaises(ValueError):s.restore(w,copy_data=self.copy_data)

    def test_missing_full_world_history_rejected(self):
        w=self.world();del w.heading_sensor_history
        with self.assertRaises(ValueError):WorldCheckpoint.capture(w)

    def test_cross_instance_controller_references_rebound(self):
        a,b=self.world(),self.world();s=WorldCheckpoint.capture(a)
        s.restore(b,copy_data=self.copy_data)
        self.assertIs(b.core.controller.model,b.core.model)
        self.assertIs(b.core.controller.data,b.core.data)


class ImpactTests(unittest.TestCase):
    @staticmethod
    def trace(dt=.005):
        return dict(timestep_s=dt, start_s=.035, end_s=.135,
                    samples=[dict(time_s=.035+i*dt, qpos=np.zeros(7))
                             for i in range(1, round(.1/dt)+1)])

    def test_fixed_clock_and_restore_between_rates(self):
        w=CheckpointTests.world();s=WorldCheckpoint.capture(w)
        schedule=ImpactSchedule(.035,np.ones((20,14)),np.ones((20,20)),np.ones((20,20)),np.zeros((20,14)))
        def step(m,d):d.time+=m.opt.timestep;d.qpos[0]+=m.opt.timestep
        physics=NS(mj_copyData=CheckpointTests.copy_data,mj_step=step)
        a=run_window(w,s,schedule,.005,physics=physics)
        b=run_window(w,s,schedule,.00125,physics=physics)
        self.assertEqual(len(a['samples']),20);self.assertEqual(len(b['samples']),80)
        self.assertAlmostEqual(b['samples'][-1]['time_s'],.135)
        self.assertLess(compare_common_grid(a,b)['max_root_axis_difference_m'],1e-12)
        self.assertEqual(w.core.model.opt.timestep,.005)
        self.assertFalse(a['closed_loop_score'])

    def test_unbounded_rate_or_schedule_rejected(self):
        w=CheckpointTests.world();s=WorldCheckpoint.capture(w)
        schedule=ImpactSchedule(.035,np.zeros((21,14)),np.zeros((21,20)),np.zeros((21,20)),np.zeros((21,14)))
        with self.assertRaises(ValueError):schedule.validate(w)
        with self.assertRaises(ValueError):run_window(w,s,schedule,.000001,physics=NS())

    def test_partial_traces_not_compared(self):
        for dt in (.005, .0025):
            for index in (0, 1, -1):
                with self.subTest(dt=dt, missing_index=index):
                    a,b = self.trace(),self.trace(dt)
                    del b['samples'][index]
                    with self.assertRaises(ValueError):compare_common_grid(a,b)

    def test_full_rate_faults_off_common_grid_rejected(self):
        for fault in ('nan_time','nan_position','short_position','duplicate','reordered'):
            with self.subTest(fault=fault):
                a,b = self.trace(),self.trace(.0025)
                if fault == 'nan_time': b['samples'][0]['time_s'] = float('nan')
                if fault == 'nan_position': b['samples'][0]['qpos'][0] = float('nan')
                if fault == 'short_position': b['samples'][0]['qpos'] = np.zeros(2)
                if fault == 'duplicate': b['samples'][0] = copy.deepcopy(b['samples'][1])
                if fault == 'reordered': b['samples'][0],b['samples'][1] = b['samples'][1],b['samples'][0]
                with self.assertRaises(ValueError):compare_common_grid(a,b)

    def test_invalid_clock_metadata_rejected(self):
        for field,value in (('start_s',.04),('end_s',float('nan')),('end_s',.14),
                            ('timestep_s',0.),('timestep_s',float('nan'))):
            with self.subTest(field=field, value=value):
                a,b = self.trace(),self.trace(.0025); b[field] = value
                with self.assertRaises(ValueError):compare_common_grid(a,b)
        for tolerance in (float('nan'), float('inf'), 0., .005):
            with self.assertRaises(ValueError):
                compare_common_grid(self.trace(),self.trace(),time_tolerance_s=tolerance)


class VisionTests(unittest.TestCase):
    def test_center_unchanged_and_edge_slows_forward_only(self):
        camera=NS(width=320,height=240)
        command=np.array([.12,0,.3],np.float32)
        center=NS(valid=True,centroid_uv=(160,120),area_px=314)
        edge=NS(valid=True,centroid_uv=(160,12),area_px=314)
        np.testing.assert_array_equal(edge_limited_twist(command,center,camera),command)
        result=edge_limited_twist(command,edge,camera)
        self.assertLess(result[0],command[0]);self.assertEqual(result[2],command[2])

    def test_invalid_detection_cannot_move(self):
        d=NS(valid=False,centroid_uv=None,area_px=0)
        np.testing.assert_array_equal(edge_limited_twist(np.ones(3,np.float32),d,NS()),np.zeros(3))

    def test_fault_stop_is_not_slewed(self):
        s=ReacquisitionYaw();cmd=np.array([.1,0,.6],np.float32)
        s.apply(cmd,0);a=s.apply(cmd,.02)
        self.assertAlmostEqual(a[2],.03,places=6)
        np.testing.assert_array_equal(s.apply(np.zeros(3,np.float32),.04),np.zeros(3))
        b=s.apply(cmd,.06);self.assertAlmostEqual(b[2],.03,places=6)

    def test_bad_clock_and_long_gap_stop(self):
        s=ReacquisitionYaw();cmd=np.ones(3,np.float32);s.apply(cmd,1)
        for timestamp in (.5,float('nan'),float('inf')):
            np.testing.assert_array_equal(s.apply(cmd,timestamp),np.zeros(3))
        s.apply(cmd,2)
        np.testing.assert_array_equal(s.apply(cmd,3),np.zeros(3))

    @unittest.skipUnless((Path(__file__).resolve().parents[2]/'experiments/visual-follow-v1/perception.py').exists(),
                         'retained source is absent from this partial local checkout')
    def test_retained_detector_follower_integration(self):
        from retool.vision import retained_perception
        legacy=retained_perception()
        for arm in ('control','edge_speed','reacquisition_yaw'):
            f=make_follower(arm);d=legacy.Detection(True,'detected',.1,1.,100,(160.,120.),1)
            f.ingest(d,0.,0,0.);np.testing.assert_array_equal(f.command(0.),np.zeros(3))
            f.ingest(d,.04,1,.04);self.assertGreater(f.command(.04)[0],0)
            f.ingest(legacy.Detection(False,'ambiguous_targets'),.08,2,.08)
            np.testing.assert_array_equal(f.command(.08),np.zeros(3))


class CliTests(unittest.TestCase):
    def test_program_is_bounded_and_does_not_promote(self):
        root=Path(__file__).resolve().parents[2]
        data=program(root/'experiments/retool-v1/program.json')
        self.assertFalse(data['automatic_promotion']);self.assertEqual(len(data['workstreams']),7)

    def test_replay_file_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'input.npz';out=Path(tmp)/'out.npz'
            np.savez(source,observations=np.zeros((2,61),np.float32),actions=np.zeros((2,14),np.float32),
                     env_ids=np.zeros(2,int),episode_ids=np.zeros(2,int),control_steps=np.arange(2))
            with contextlib.redirect_stdout(None),contextlib.redirect_stderr(None):
                self.assertEqual(main(['label-replay','--input',str(source),'--output',str(out)]),0)
                old=out.read_bytes()
                self.assertEqual(main(['label-replay','--input',str(source),'--output',str(out)]),2)
            self.assertEqual(out.read_bytes(),old)
            with np.load(out,allow_pickle=False) as data:self.assertEqual(len(data['phases']),2)


if __name__=='__main__':unittest.main()
