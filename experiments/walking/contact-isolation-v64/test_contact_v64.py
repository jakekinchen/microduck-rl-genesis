"""Isolation and clock contracts; no simulated robot rollout."""
import json
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from contact_v64 import clock_subdivisions, mask_changes, mask_shell_floor, match_export, load_gate


class ContactTests(unittest.TestCase):
    def test_only_two_floor_pairs_change_and_shell_body_pairs_remain(self):
        original = np.ones(5, dtype=np.int32)
        types = np.array([2,1,1,1,0]); affinity = np.array([2,1,1,3,0])
        old = original.copy(); old[-1] = 0
        self.assertEqual(mask_changes(old, old, types, affinity), [[0,1,True,False],[0,2,True,False]])

    def test_xml_mask_preserves_internal_bits_and_visuals(self):
        robot=ET.fromstring('<mujoco><worldbody><body><geom name="ankle_left_3_foot_left_collision" contype="1" conaffinity="1"/><geom name="ankle_right_7_foot_right_collision" contype="1" conaffinity="1"/><geom name="sole" contype="1" conaffinity="1"/><geom name="visual" contype="0" conaffinity="0"/></body></worldbody></mujoco>')
        scene=ET.fromstring('<mujoco><worldbody><geom name="floor"/></worldbody></mujoco>')
        mask_shell_floor(robot,scene)
        geoms=robot.findall('.//geom')
        self.assertEqual([g.get('conaffinity') for g in geoms],['1','1','3','0'])
        self.assertEqual([g.get('contype') for g in geoms],['1','1','1','0'])

    def test_export_matching_does_not_replace_geometry(self):
        robot=ET.fromstring('<mujoco><worldbody><body name="a" pos="1 0 0"><inertial mass="1"/><joint name="j" range="-1 1"/><geom name="shell" mesh="candidate" contype="1"/></body></worldbody></mujoco>')
        reference=ET.fromstring('<mujoco><worldbody><body name="a" pos="1.0000001 0 0"><inertial mass="1.1"/><joint name="j" range="-1.1 1"/><geom name="simplified"/></body></worldbody></mujoco>')
        before=ET.tostring(robot.find('.//geom'))
        self.assertEqual(len(match_export(robot,reference)),3)
        self.assertEqual(before,ET.tostring(robot.find('.//geom')))
        self.assertEqual(robot.find('.//inertial').get('mass'),'1.1')

    def test_nonintegral_clock_is_rejected(self):
        self.assertEqual([clock_subdivisions(x) for x in (.005,.0025,.00125)],[1,2,4])
        with self.assertRaises(ValueError): clock_subdivisions(.003)

    def test_high_rate_missing_tail_cannot_pass(self):
        rows=[{'time_s':(i+1)*.00125,'total_normal_n':0.,'largest_pair_normal_n':0.} for i in range(79)]
        self.assertIn('incomplete_duration',load_gate(rows,.1,.00125)['failures'])

    def test_continuous_loading_uses_physical_seconds(self):
        for dt in (.005,.0025,.00125):
            n=round(.06/dt)
            rows=[{'time_s':(i+1)*dt,'total_normal_n':2.,'largest_pair_normal_n':2.} for i in range(n)]
            result=load_gate(rows,.06,dt)
            self.assertAlmostEqual(result['longest_over_1n_s'],.06)
            self.assertIn('continuous_body_bracing',result['failures'])

    def test_per_step_force_order_and_finite_required(self):
        for invalid in (float('nan'),-1.):
            rows=[{'time_s':.00125,'total_normal_n':invalid,'largest_pair_normal_n':0.}]
            self.assertIn('invalid_or_unordered_load_evidence',load_gate(rows,.00125,.00125)['failures'])


if __name__=='__main__':unittest.main()
