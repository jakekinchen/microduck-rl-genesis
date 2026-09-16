import copy
import math
import unittest
from microduck.constants import DEFAULT_JOINT_POS
from experiments.walking.endurance_v23 import evaluate_endurance


class EnduranceTests(unittest.TestCase):
    def setUp(self):
        self.window={"duration_s":180,"stop_start_s":175,"command":[.12,0,0]}
        self.limits={"mean_abs_forward_error_m_s":.05,"mean_abs_lateral_velocity_m_s":.05,"mean_abs_yaw_error_rad_s":.2}
        self.rows=[{"time_s":(i+1)*.02,"qpos":[0,0,.125,1,0,0,0]+list(DEFAULT_JOINT_POS),
                    "face_world":[1,0,0],"command":[.12,0,0],"body_velocity_m_s":[.12,0,0],"yaw_rate_rad_s":0.} for i in range(9000)]

    def test_complete_control_and_missing_tail(self):
        self.assertTrue(evaluate_endurance(self.rows,self.window,self.limits)["passed"])
        report=evaluate_endurance(self.rows[:-1],self.window,self.limits)
        self.assertFalse(report["passed"])
        self.assertIn("incomplete_endurance_evidence",report["failures"])

    def test_late_heading_drift_cannot_hide_in_first_window(self):
        for r in self.rows:
            if r["time_s"]>100:
                r["qpos"][3:7]=[math.cos(.4/2),0,0,math.sin(.4/2)]
        report=evaluate_endurance(self.rows,self.window,self.limits)
        self.assertIn("full_horizon_maximum_heading_error_deg",report["failures"])

    def test_local_tracking_failure_cannot_average_away(self):
        for r in self.rows:
            if 62<=r["time_s"]<92: r["body_velocity_m_s"]=[.2,0,0]
        report=evaluate_endurance(self.rows,self.window,self.limits)
        self.assertFalse(report["passed"])
        self.assertEqual(sum(not b["passed"] for b in report["tracking_buckets"]),1)

    def test_nonfinite_telemetry_rejected(self):
        self.rows[4000]["body_velocity_m_s"]=[float("nan"),0,0]
        self.assertFalse(evaluate_endurance(self.rows,self.window,self.limits)["passed"])


if __name__=="__main__": unittest.main()
