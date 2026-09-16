"""Neutral head is an additive condition, not an excuse to relax motor gates."""
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"tests"))
import json
import numpy as np
import torch
from test_walking import walking_fixture
from microduck.constants import DEFAULT_JOINT_POS
from microduck.walking_posture_env import head_command_cost
from experiments.walking.posture import evaluate_case,posture_metrics


def fixture():
    rows=walking_fixture()
    for r in rows:r.update(qpos=[0,0,.125,1,0,0,0]+list(DEFAULT_JOINT_POS),face_world=[1,0,0])
    return rows


class PostureWalkingTests(unittest.TestCase):
    def test_cost_does_not_saturate_or_average_away_bad_neck(self):
        errors=torch.tensor([[.1,.1,.1,.1],[.8,0,0,0],[1.5,0,0,0]])
        cost=head_command_cost(errors)
        self.assertEqual(float(cost[0]),0.)
        self.assertGreater(float(cost[2]),float(cost[1]))
        self.assertAlmostEqual(float(cost[2]),1.3,places=6)

    def test_neutral_steps_pass_but_folded_neck_is_rejected(self):
        suite=json.loads((ROOT/"experiments/walking/suite-v1.json").read_text())
        case={"id":"fixture","command":[.12,0,0]}
        rows=fixture()
        self.assertTrue(evaluate_case(rows,case,suite)["passed"])
        for r in rows:
            r["qpos"][12]-=1.5
            r["face_world"]=[float(np.cos(1.5)),0,-float(np.sin(1.5))]
        result=evaluate_case(rows,case,suite)
        self.assertTrue(result["motor_battery_passed"])
        self.assertFalse(result["passed"])
        self.assertEqual(len(result["failures"]),3)

    def test_good_head_does_not_override_failed_stop(self):
        rows=fixture()
        for r in rows:
            if r["time_s"]>=13:r.update(speed_m_s=.1,body_velocity_m_s=[.1,0,0])
        suite=json.loads((ROOT/"experiments/walking/suite-v1.json").read_text())
        result=evaluate_case(rows,{"id":"fixture","command":[.12,0,0]},suite)
        self.assertTrue(result["posture"]["passed"])
        self.assertFalse(result["passed"])

    def test_missing_or_nonfinite_head_evidence_is_not_a_pass(self):
        rows=fixture();rows[-1]["qpos"][12]=float("nan")
        with self.assertRaises(ValueError):posture_metrics(rows)


if __name__=="__main__":unittest.main(verbosity=2)
