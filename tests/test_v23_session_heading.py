import math
import unittest
from scripts.audit_v23_session_heading import audit


class SessionHeadingTests(unittest.TestCase):
    def setUp(self):
        self.rows=[{"session_time_s":(i+1)*.02,"qpos":[0,0,.12,1,0,0,0],"command":[0,0,0]} for i in range(9000)]

    def test_complete_zero_drift(self):
        self.assertTrue(audit(self.rows,180)["passed"])

    def test_small_errors_across_transitions_accumulate(self):
        for i,row in enumerate(self.rows):
            angle=math.radians(3*(i//900))
            row["qpos"][3:7]=[math.cos(angle/2),0,0,math.sin(angle/2)]
        self.assertFalse(audit(self.rows,180)["passed"])

    def test_missing_sample_rejected(self):
        with self.assertRaises(ValueError): audit(self.rows[:-1],180)


if __name__=="__main__": unittest.main()
