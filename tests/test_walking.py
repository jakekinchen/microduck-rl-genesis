"""The new training signal must measure the sole and reject non-stepping rewards."""
from pathlib import Path
import sys
import unittest
import copy
import json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import mujoco
import numpy as np
import torch
from microduck.constants import MICRODUCK_WALK_XML,DEFAULT_JOINT_POS,JOINT_NAMES
from microduck.walking_env import sole_vertices,lift_score
from experiments.walking.world import TargetDelay,WalkingWorld
from experiments.walking.metrics import evaluate_case


def walking_fixture(command=(.12,0.,0.)):
    rows=[]
    for i in range(900):
        t=(i+1)*.02;active=1<=i*.02<13
        foot=(i//10)%2;air=active and i%10<6
        load=[4.,4.];clear=[0.,0.]
        if air:load[foot]=0.;clear[foot]=.012
        distance=max(0.,min(t-1,12))*command[0]
        rows.append(dict(time_s=t,command=list(command) if active else [0.,0.,0.],
            robot_xyz_m=[distance,0.,.12],speed_m_s=abs(command[0]) if active else 0.,
            body_velocity_m_s=[command[0] if active else 0.,0.,0.],yaw_rate_rad_s=command[2] if active else 0.,
            foot_normal_n=load,sole_clearance_m=clear,loaded_contact_slip_m_s=[.001,.001],
            face_velocity_cosine=1.,servo_target_limit_violation_rad=[0.]*14,joint_limit_violation_rad=[0.]*14,
            joint_limit_margin_fraction=[.4]*14,servo_velocity_rad_s=[1.]*14,actuator_torque_nm=[.1]*14,
            motor_torque_physics_nm=[[.1]*14 for _ in range(4)],minimum_actual_joint_margin_rad=.3,
            nonfoot_ground_contacts=[],tilt_deg=2.,fell=False))
    return rows


class WalkingTests(unittest.TestCase):
    def setUp(self):
        self.suite=json.loads((ROOT/"experiments/walking/suite-v1.json").read_text())

    def test_sole_hull_matches_collision_mesh_under_rotated_poses(self):
        m=mujoco.MjModel.from_xml_path(MICRODUCK_WALK_XML);d=mujoco.MjData(m)
        local=sole_vertices(MICRODUCK_WALK_XML)
        rng=np.random.default_rng(76501)
        indices=[m.jnt_qposadr[m.joint(n).id] for n in JOINT_NAMES]
        for _ in range(20):
            d.qpos[:3]=[0,0,.125]
            q=rng.normal(size=4);d.qpos[3:7]=q/np.linalg.norm(q)
            d.qpos[indices]=np.array(DEFAULT_JOINT_POS)+rng.uniform(-.2,.2,14)
            mujoco.mj_forward(m,d)
            for i,side in enumerate(("left","right")):
                g=m.geom(f"{side}_foot_collision").id;b=m.geom_bodyid[g]
                mesh=m.geom_dataid[g];start,count=m.mesh_vertadr[mesh],m.mesh_vertnum[mesh]
                actual=(m.mesh_vert[start:start+count]@d.geom_xmat[g].reshape(3,3).T+d.geom_xpos[g])[:,2].min()
                computed=(local[i]@d.xmat[b].reshape(3,3).T+d.xpos[b])[:,2].min()
                self.assertAlmostEqual(actual,computed,places=7)

    def test_lift_signal_excludes_dragging_hopping_and_one_leg_parking(self):
        height=torch.tensor([[.018,0.],[0.,0.],[.018,.018],[.018,0.]])
        air=torch.tensor([[.1,0.],[0.,0.],[.1,.1],[1.,0.]])
        contact=torch.tensor([[False,True],[True,True],[False,False],[False,True]])
        score=lift_score(height,air,contact)
        self.assertEqual(score.tolist(),[1.,0.,0.,0.])

    def test_motor_fifo_preserves_values_and_exact_physics_tick_delay(self):
        delay=TargetDelay(np.zeros(14),3)
        targets=[np.full(14,i+1,dtype=np.float32) for i in range(8)]
        output=[delay.step(v) for v in targets]
        for i in range(3):np.testing.assert_array_equal(output[i],np.zeros(14))
        for i in range(3,8):self.assertEqual(output[i].tobytes(),targets[i-3].tobytes())
        zero=TargetDelay(np.zeros(14),0)
        self.assertEqual(zero.step(targets[0]).tobytes(),targets[0].tobytes())

    def test_forward_fixture_and_turn_without_translation(self):
        for command in ([.12,0,0],[0,0,.5]):
            result=evaluate_case(walking_fixture(command),{"id":"fixture","command":command},self.suite)
            self.assertTrue(result["passed"],result["failures"])

    def test_stationary_turn_dragging_hopping_and_failed_stop_are_rejected(self):
        case={"id":"fixture","command":[.12,0,0]}
        for mode in ("drag","hop","no_stop"):
            rows=walking_fixture()
            for row in rows:
                if mode=="drag":row.update(foot_normal_n=[4.,4.],sole_clearance_m=[0.,0.])
                if mode=="hop" and min(row["foot_normal_n"])==0:row.update(foot_normal_n=[0.,0.],sole_clearance_m=[.012,.012])
                if mode=="no_stop" and row["time_s"]>=13:row.update(speed_m_s=.1,body_velocity_m_s=[.1,0,0])
            result=evaluate_case(rows,case,self.suite)
            self.assertFalse(result["passed"],mode)
        rows=walking_fixture([0,0,.5])
        for row in rows:row["yaw_rate_rad_s"]=0
        self.assertIn("no_useful_turning",evaluate_case(rows,{"id":"turn","command":[0,0,.5]},self.suite)["failures"])

    def test_nan_in_stop_telemetry_is_unknown_not_pass(self):
        rows=walking_fixture();rows[-1]["yaw_rate_rad_s"]=float("nan")
        with self.assertRaises(ValueError):evaluate_case(rows,{"id":"fixture","command":[.12,0,0]},self.suite)

    def test_torque_saturation_and_missing_substeps_cannot_pass(self):
        rows=walking_fixture();case={"id":"fixture","command":[.12,0,0]}
        for row in rows:row["motor_torque_physics_nm"]=[[.64]*14 for _ in range(4)]
        self.assertIn("persistent_torque_saturation",evaluate_case(rows,case,self.suite)["failures"])
        rows[-1]["motor_torque_physics_nm"]=[[.1]*14]
        with self.assertRaises(ValueError):evaluate_case(rows,case,self.suite)

    def test_zero_lag_world_preserves_old_action_and_state_bytes(self):
        from experiments.laser.face_world import FaceFirstLaserWorld
        from microduck.laser_dynamics import domain_draw
        policy=ROOT/"receipts/laser-gait/20260905-v4-evaluation/policy.onnx"
        a=WalkingWorld(policy,ROOT/".workspace/bam",motor_ticks=0,sensor_ticks=0)
        b=FaceFirstLaserWorld(policy,ROOT/".workspace/bam",domain_draw(76521,False))
        b.command_for=lambda target,visible:np.array([.12,0,0],np.float32)
        try:
            for _ in range(20):
                a.step_command([.12,0,0]);b.step([0,0])
                self.assertEqual(a.last_action.tobytes(),b.last_action.tobytes())
                self.assertEqual(a.core.data.qpos.tobytes(),b.core.data.qpos.tobytes())
                self.assertEqual(a.core.data.qvel.tobytes(),b.core.data.qvel.tobytes())
        finally:a.close();b.close()


if __name__=="__main__":unittest.main(verbosity=2)
