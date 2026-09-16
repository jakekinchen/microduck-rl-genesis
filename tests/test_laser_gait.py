import copy
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
import torch
from experiments.laser.gait import summarize_gait, GaitProbe
from microduck.laser_face_command import face_first_command
from microduck.laser_gait_env import face_commands_torch, joint_boundary_cost, MicroduckLaserGaitEnv


def stepping_fixture():
    rows=[]
    for i in range(300):
        phase=i%40
        foot=0 if phase<20 else 1
        airborne=(phase%20)<8
        load=[4.,4.]; clearance=[0.,0.]
        if airborne: load[foot]=0.; clearance[foot]=.012
        rows.append(dict(time_s=(i+1)*.02, command=[.1,0,0], robot_xyz_m=[.002*i,0,.12],
                         speed_m_s=.1, foot_normal_n=load, sole_clearance_m=clearance,
                         loaded_contact_slip_m_s=[.001,.001], face_velocity_cosine=1.,
                         servo_target_limit_violation_rad=[0.]*14, joint_limit_violation_rad=[0.]*14,
                         joint_limit_margin_fraction=[.4]*14, servo_velocity_rad_s=[1.]*14,
                         actuator_torque_nm=[.1]*14, nonfoot_ground_contacts=[], tilt_deg=2., fell=False))
    return rows


class GaitTests(unittest.TestCase):
    def test_face_command_is_canonical_positive_x(self):
        self.assertGreater(face_first_command([.6,0])[0],0)
        self.assertEqual(face_first_command([-.6,0])[0],0)
        self.assertGreater(face_first_command([.6,.1])[2],0)
        self.assertLess(face_first_command([.6,-.1])[2],0)
        for xy in ([0,0],[np.nan,0]):
            np.testing.assert_array_equal(face_first_command(xy),np.zeros(3))
        np.testing.assert_array_equal(face_first_command([-.6,0],False),np.zeros(3))

    def test_train_deploy_command_parity(self):
        relative=np.random.default_rng(76200).uniform(-1,1,(100,2)).astype(np.float32)
        visible=np.random.default_rng(76201).random(100)>.2
        expected=np.stack([face_first_command(x,v) for x,v in zip(relative,visible)])
        actual=face_commands_torch(torch.tensor(relative),torch.tensor(visible)).numpy()
        np.testing.assert_allclose(actual,expected,atol=2e-7)

    def test_boundary_cost_prices_actual_stop_not_reference(self):
        lower,upper=torch.tensor([-1.,-1.]),torch.tensor([1.,1.])
        score=joint_boundary_cost(torch.tensor([[0.,0.],[.7,.7],[1.,1.]]),lower,upper)
        self.assertEqual(score[0],0); self.assertEqual(score[1],0); self.assertGreater(score[2],1)

    def test_tracking_accepts_inherited_float_active_mask(self):
        from types import SimpleNamespace
        env=SimpleNamespace(twist_cmd=torch.zeros(2,3),base_lin_vel=torch.zeros(2,3),
                            _command_active=lambda:torch.tensor([0.,1.]),
                            _gait_credit=lambda:torch.tensor([.15,.15]))
        np.testing.assert_allclose(MicroduckLaserGaitEnv._rew_track_lin(env).numpy(),[1.,.15])

    def test_nonzero_command_no_longer_rewards_standing_like_walking(self):
        from types import SimpleNamespace
        env=SimpleNamespace(twist_cmd=torch.tensor([[.2,0.,0.],[.2,0.,0.]]),
                            base_lin_vel=torch.tensor([[0.,0.,0.],[.2,0.,0.]]),
                            _command_active=lambda:torch.ones(2),
                            _gait_credit=lambda:torch.tensor([.15,1.]))
        score=MicroduckLaserGaitEnv._rew_track_lin(env)
        self.assertLess(score[0],.001)
        self.assertEqual(score[1],1.)

    def test_gait_credit_requires_recent_steps_from_both_feet(self):
        from types import SimpleNamespace
        env=SimpleNamespace(episode_length_buf=torch.tensor([100,100,100]),dt=.02,
                            last_step_tick=torch.tensor([[90,90],[90,-10000],[0,0]]))
        np.testing.assert_allclose(MicroduckLaserGaitEnv._gait_credit(env).numpy(),[1.,.15,.15])

    def test_synthetic_steps_pass_rejection_only(self):
        result=summarize_gait(stepping_fixture())
        self.assertTrue(result["rejection_gate_passed"],result)
        self.assertFalse(result["physical_transfer_validated"])

    def test_wrong_motions_cannot_pass(self):
        for failure in ("backward_pursuit","persistent_loaded_foot_slip","persistent_joint_hard_stop","missing_bilateral_steps","no_useful_translation","fall"):
            rows=stepping_fixture()
            for r in rows:
                if failure=="backward_pursuit": r["face_velocity_cosine"]=-1
                if failure=="persistent_loaded_foot_slip": r["loaded_contact_slip_m_s"]=[.2,.2]
                if failure=="persistent_joint_hard_stop": r["joint_limit_margin_fraction"][0]=0
                if failure=="missing_bilateral_steps": r["sole_clearance_m"][1]=0
                if failure=="no_useful_translation": r["speed_m_s"]=0
                if failure=="fall": r["fell"]=True
            result=summarize_gait(rows)
            self.assertIn(failure,result["rejection_reasons"])
            self.assertFalse(result["rejection_gate_passed"])

    def test_bam_reference_overshoot_is_not_a_stop(self):
        rows=stepping_fixture()
        for r in rows: r["servo_target_limit_violation_rad"]=[.5]*14
        self.assertTrue(summarize_gait(rows)["rejection_gate_passed"])

    def test_token_steps_do_not_hide_later_skating(self):
        rows=stepping_fixture()
        for row in rows:
            if row["time_s"]>2.5:
                row["foot_normal_n"]=[4.,4.]
                row["sole_clearance_m"]=[0.,0.]
        result=summarize_gait(rows)
        self.assertIn("unsustained_bilateral_stepping",result["rejection_reasons"])

    def test_target_pass_cannot_override_gait_failure(self):
        from scripts.evaluate_laser_gait import combine_gates
        gait={"rejection_gate_passed":False,"rejection_reasons":["persistent_joint_hard_stop"]}
        result=combine_gates({"passed":True},gait,duration_s=48,required_s=48)
        self.assertFalse(result["development_passed"])
        self.assertIn("persistent_joint_hard_stop",result["failures"])

    def test_missing_nan_irregular_fail_closed(self):
        for field in ("sole_clearance_m","joint_limit_margin_fraction","loaded_contact_slip_m_s"):
            rows=stepping_fixture(); rows[10][field][0]=float("nan")
            with self.assertRaises(ValueError): summarize_gait(rows)
        rows=stepping_fixture(); rows.pop(10)
        with self.assertRaises(ValueError): summarize_gait(rows)
        with self.assertRaises(ValueError): summarize_gait([])

    @unittest.skipUnless(os.environ.get("BAM_REPO"),"requires pinned BAM checkout")
    def test_camera_mapping_matches_physical_mouth_without_changing_actions(self):
        import mujoco
        from experiments.laser.world import LaserWorld
        from experiments.laser.face_world import FaceFirstLaserWorld
        from microduck.laser_dynamics import domain_draw
        policy=ROOT/"receipts/laser-dynamic/20260905-turn-dev/policy.onnx"
        first=LaserWorld(policy,Path(os.environ["BAM_REPO"]),domain_draw(76202,False))
        second=FaceFirstLaserWorld(policy,Path(os.environ["BAM_REPO"]),domain_draw(76202,False))
        d,m=second.core.data,second.core.model
        face=d.site("head_camera").xmat.reshape(3,3)[:,0]
        mouth=d.site("mouth_tip").xpos-d.xipos[m.body("jaw_soft").id]
        self.assertGreater(np.dot(mouth,face),.04)
        old_optical=-first.core.data.cam_xmat[0].reshape(3,3)[:,2]
        new_optical=-d.cam_xmat[0].reshape(3,3)[:,2]
        self.assertLess(np.dot(old_optical,face),-.999)
        self.assertGreater(np.dot(new_optical,face),.999)
        np.testing.assert_allclose(d.cam_xmat[0].reshape(3,3)[:,1],[0,0,1],atol=1e-7)
        for _ in range(30):
            first.step([.6,0]);second.step([.6,0])
            self.assertEqual(first.last_action.tobytes(),second.last_action.tobytes())
            self.assertEqual(first.core.data.qpos.tobytes(),second.core.data.qpos.tobytes())
            self.assertEqual(first.core.data.qvel.tobytes(),second.core.data.qvel.tobytes())
        first.close();second.close()

    @unittest.skipUnless(os.environ.get("BAM_REPO"),"requires pinned BAM checkout")
    def test_probe_preserves_original_action_and_state_bytes(self):
        from experiments.laser.world import LaserWorld
        from microduck.laser_dynamics import domain_draw
        policy=ROOT/"receipts/laser-dynamic/20260905-turn-dev/policy.onnx"
        first=LaserWorld(policy,Path(os.environ["BAM_REPO"]),domain_draw(76202,False))
        second=LaserWorld(policy,Path(os.environ["BAM_REPO"]),domain_draw(76202,False))
        probe=GaitProbe(second.core)
        for _ in range(30):
            first.step([.6,0]); row=second.step([.6,0]); probe.sample(row)
            self.assertEqual(first.last_action.tobytes(),second.last_action.tobytes())
            self.assertEqual(first.core.data.qpos.tobytes(),second.core.data.qpos.tobytes())
            self.assertEqual(first.core.data.qvel.tobytes(),second.core.data.qvel.tobytes())
        first.close(); second.close()


if __name__=="__main__": unittest.main()
