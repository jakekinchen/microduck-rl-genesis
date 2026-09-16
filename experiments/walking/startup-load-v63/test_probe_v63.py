import copy
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
import numpy as np
import mujoco

sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from metrics import strict_action, classify, dynamics_digest
from probe_startup_v63 import passive_update

THRESHOLDS={'maximum_internal_penetration_m':.001,'maximum_ground_penetration_m':.003,
    'maximum_joint_overshoot_rad':.02,'active_minimum_joint_margin_rad':.02,'maximum_nonsole_ground_load_n':.1,
    'motor_torque_limit_nm':.6405236195572268,'home_max_tilt_deg':15.,'home_max_drift_m':.05,
    'passive_final_speed_m_s':.02,'passive_final_angular_speed_rad_s':.2}


class ProbeTests(unittest.TestCase):
    def rows(self):
        return [{'time_s':(i+1)*.005,'root_z_m':.12,'tilt_deg':0.,'speed_m_s':0.,
                 'angular_speed_rad_s':0.,'internal_penetration_m':0.,'ground_penetration_m':0.,
                 'total_normal_n':0.,'largest_pair_normal_n':0.,'joint_margin_rad':.04,
                 'motor_torque_max_nm':0.,'actuator_force_max_nm':0.,'nonsole_ground_load_n':0.,
                 'warnings':[],'fell':False,'xy_displacement_m':0.} for i in range(1000)]

    def evaluate(self,rows,mode='home'):
        return classify(rows,{'mode':mode,'duration_s':5.},THRESHOLDS,
                        {'physics_ns':[100000]*len(rows),'control_ns':[1000000]*(len(rows)//4)})

    def test_actions_are_strict_and_bit_preserving(self):
        action=np.arange(14,dtype=np.float32);action[0]=-0.
        self.assertEqual(strict_action(action).tobytes(),action.tobytes())
        for bad in [action.astype(np.float64),action[:13],np.full(14,np.nan,dtype=np.float32)]:
            with self.assertRaises(ValueError):strict_action(bad)

    def test_missing_and_partial_evidence_cannot_pass(self):
        self.assertFalse(self.evaluate([])['passed'])
        result=self.evaluate(self.rows()[:-1]);self.assertFalse(result['passed'])
        self.assertIn('incomplete_duration',result['failures'])
        self.assertFalse(result['performance']['provisional_50hz_budget_passed'])

    def test_actual_body_loading_rejects_ordinary_upright_pose(self):
        rows=self.rows()
        self.assertTrue(self.evaluate(rows)['passed'])
        for row in rows[300:330]:row['total_normal_n']=2.;row['largest_pair_normal_n']=2.
        result=self.evaluate(rows)
        self.assertFalse(result['passed']);self.assertIn('continuous_body_bracing',result['failures'])

    def test_passive_settling_does_not_certify_upright_behavior(self):
        rows=self.rows()
        for row in rows:row.update(fell=True,root_z_m=.04,tilt_deg=90.,nonsole_ground_load_n=5.)
        result=self.evaluate(rows,'passive')
        self.assertTrue(result['passed']);self.assertFalse(result['upright_bracing_gate_applicable'])
        self.assertFalse(result['walking_accepted'])
        self.assertFalse(self.evaluate(rows)['passed'])
        rows[2]['actuator_force_max_nm']=.001
        self.assertIn('nonzero_passive_motor_torque',self.evaluate(rows,'passive')['failures'])

    def test_interference_and_warnings_reject(self):
        rows=self.rows();rows[0]['internal_penetration_m']=.00101;rows[0]['warnings']=[3]
        result=self.evaluate(rows)
        self.assertIn('internal_penetration',result['failures']);self.assertIn('mujoco_warning',result['failures'])

    def test_passive_friction_subtracts_existing_friction_constraint(self):
        seen=[]
        def friction(motor,external,velocity):
            seen.append((motor.copy(),external.copy(),velocity.copy()))
            return np.array([.12,.13]),np.array([.04,.05])
        controller=SimpleNamespace(dof_indexes=[0,1],joint_indexes=[7,4],actuator=['a','b'],
            model=SimpleNamespace(compute_frictions=friction),_prev_motor_torque=np.ones(2),last_ts=0.)
        data=SimpleNamespace(qfrc_bias=np.array([.1,.2]),qfrc_constraint=np.array([.8,.9]),
            efc_id=np.array([7,4,7]),efc_type=np.array([int(mujoco.mjtConstraint.mjCNSTR_FRICTION_DOF)]*2+[6]),
            efc_force=np.array([.2,.3,2.]),qvel=np.array([1.,2.]),ctrl=np.ones(2),time=.5)
        model=SimpleNamespace(dof_frictionloss=np.zeros(2),dof_damping=np.zeros(2))
        passive_update(SimpleNamespace(controller=controller,model=model,data=data))
        np.testing.assert_array_equal(seen[0][0],[0.,0.])
        np.testing.assert_allclose(seen[0][1],[.5,.4],atol=1e-15)
        np.testing.assert_array_equal(data.ctrl,[0.,0.]);np.testing.assert_array_equal(controller._prev_motor_torque,[0.,0.])
        np.testing.assert_array_equal(model.dof_frictionloss,[.12,.13])

    def test_mutated_reset_array_changes_fingerprint(self):
        a={'friction':np.array([.1,.2]),'qpos':np.zeros(3)}
        b=copy.deepcopy(a);self.assertEqual(dynamics_digest(a),dynamics_digest(b))
        b['friction'][0]=.2;self.assertNotEqual(dynamics_digest(a),dynamics_digest(b))


if __name__=='__main__':unittest.main()
