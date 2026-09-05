"""Laser steering/perception tests, including fail-closed negative cases."""
import math
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from microduck.laser_task import target_command, world_to_body_xy, detect_red_spot
from microduck.laser_steering import approach_command
from microduck.laser_env import MicroduckLaserEnv
from microduck.velocity_env import MicroduckVelocityEnv
from scripts.evaluate_laser import summarize, target_at, SUITE
import json


class LaserTests(unittest.TestCase):
    def test_v2_approach_is_bounded_and_preserves_turn_loss_and_stop(self):
        for xy in ([1, 0], [.25, 0], [.1, 0], [-1, 0], [.25, -.1], [float("nan"), 0]):
            original = target_command(xy)
            np.testing.assert_array_equal(approach_command(xy, gain=1.5), original)
            updated = approach_command(xy, gain=3.)
            self.assertTrue(np.isfinite(updated).all())
            self.assertLessEqual(updated[0], .25)
            np.testing.assert_array_equal(updated[1:], original[1:])
            np.testing.assert_array_equal(approach_command(xy, False, gain=3.), [0, 0, 0])
        self.assertGreater(approach_command([.25, 0], gain=3.)[0], target_command([.25, 0])[0])
        np.testing.assert_array_equal(approach_command([.1, 0], gain=3.), [0, 0, 0])

    def test_forward_turn_and_stop(self):
        np.testing.assert_allclose(target_command([1, 0]), [0.25, 0, 0])
        self.assertGreater(target_command([0.5, 0.4])[2], 0)
        self.assertLess(target_command([0.5, -0.4])[2], 0)
        self.assertEqual(target_command([-1, 0])[0], 0)
        for xy, visible in [([0.1, 0], True), ([1, 0], False), ([np.nan, 0], True)]:
            np.testing.assert_array_equal(target_command(xy, visible), [0, 0, 0])

    def test_frame_rotation(self):
        q = [math.sqrt(0.5), 0, 0, math.sqrt(0.5)]
        np.testing.assert_allclose(world_to_body_xy([2, 4], [2, 3], q), [1, 0], atol=1e-7)

    def test_vectorized_training_matches_deployment_commands(self):
        rng = np.random.default_rng(74103)
        n = 100
        env = object.__new__(MicroduckLaserEnv)
        env.base_pos = torch.tensor(rng.normal(size=(n, 3)), dtype=torch.float32)
        yaw = torch.tensor(rng.uniform(-math.pi, math.pi, n), dtype=torch.float32)
        env.base_quat = torch.stack((torch.cos(yaw/2), yaw*0, yaw*0, torch.sin(yaw/2)), dim=-1)
        env.laser_xy = torch.tensor(rng.normal(size=(n, 2)), dtype=torch.float32)
        env.laser_visible = torch.tensor(rng.random(n) > .2)
        env.twist_cmd = torch.zeros(n, 3)
        env.head_cmd, env.body_cmd = torch.zeros(n, 4), torch.zeros(n, 6)
        env._update_laser_commands()
        for i in range(n):
            xy = world_to_body_xy(env.laser_xy[i].numpy(), env.base_pos[i, :2].numpy(), env.base_quat[i].numpy())
            np.testing.assert_allclose(env.twist_cmd[i].numpy(), target_command(xy, bool(env.laser_visible[i])), atol=2e-6)

    def test_detection_and_loss(self):
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        self.assertIsNone(detect_red_spot(frame))
        frame[28:33, 38:43] = [255, 20, 10]
        self.assertEqual(detect_red_spot(frame), (40., 30.))
        frame[68:73, 68:73] = [255, 20, 10]
        self.assertIsNone(detect_red_spot(frame))

    def test_reject_white_hot_pixel_large_red_object_and_line(self):
        for color, region in [([255, 255, 255], (slice(30, 35), slice(30, 35))),
                              ([255, 0, 0], (slice(30, 31), slice(30, 31))),
                              ([255, 0, 0], (slice(20, 70), slice(20, 70))),
                              ([255, 0, 0], (slice(20, 21), slice(20, 70)))]:
            frame = np.zeros((100, 100, 3), dtype=np.uint8)
            frame[region] = color
            self.assertIsNone(detect_red_spot(frame))

    def reward_probe(self, velocity, *, visible=True, distance=.6, height=.125):
        env = object.__new__(MicroduckLaserEnv)
        env.dt = .02
        env.laser_relative = torch.tensor([[distance, 0.]])
        env.laser_distance = torch.tensor([distance])
        env.laser_visible = torch.tensor([visible])
        env.base_quat = torch.tensor([[1., 0., 0., 0.]])
        env.base_pos = torch.tensor([[0., 0., height]])
        env.projected_gravity = torch.tensor([[0., 0., -1.]])
        env.robot = SimpleNamespace(get_vel=lambda: torch.tensor([velocity]))
        env.rew_buf = torch.zeros(1)
        env.episode_sums = {name: torch.zeros(1) for name in ("laser_progress", "laser_stop", "laser_fall")}
        with patch.object(MicroduckVelocityEnv, "_compute_rewards", lambda self: None):
            env._compute_rewards()
        return {key: float(value[0]) for key, value in env.episode_sums.items()}

    def test_progress_rewards_robot_motion_not_target_distance(self):
        self.assertGreater(self.reward_probe([.2, 0., 0.])["laser_progress"], 0)
        self.assertLess(self.reward_probe([-.2, 0., 0.])["laser_progress"], 0)
        self.assertEqual(self.reward_probe([0., .2, 0.])["laser_progress"], 0)
        for distance in (.9, .5, .3):
            # A stationary robot earns no progress as the target approaches.
            self.assertEqual(self.reward_probe([0., 0., 0.], distance=distance)["laser_progress"], 0)

    def test_missing_target_stops_rewarding_pursuit(self):
        result = self.reward_probe([.2, 0., 0.], visible=False)
        self.assertEqual(result["laser_progress"], 0)
        stopped = self.reward_probe([0., 0., 0.], visible=False)
        self.assertGreater(stopped["laser_stop"], result["laser_stop"])

    def test_reached_target_has_finite_stop_reward(self):
        result = self.reward_probe([0., 0., 0.], distance=0.)
        self.assertTrue(all(np.isfinite(value) for value in result.values()))
        self.assertEqual(result["laser_progress"], 0)
        self.assertAlmostEqual(result["laser_stop"], .02)

    def test_fall_is_an_event_penalty_not_dt_scaled(self):
        self.assertEqual(self.reward_probe([0., 0., 0.], height=.06)["laser_fall"], -5.)

    def test_pursuit_classifier_does_not_promote_standing_or_falling(self):
        suite = json.loads(SUITE.read_text())
        case = suite["cases"][0]
        rows = [{"time_s": (i+1)/50, "distance_m": .6, "speed_m_s": 0.,
                 "fell": False, "visible": True, "robot_xyz_m": [0., 0., .125],
                 "command": [.25, 0., 0.], "latency_ms": .1} for i in range(600)]
        self.assertFalse(summarize(case, rows, suite["thresholds"])["passed"])
        for row in rows:
            row["distance_m"] = .2
        self.assertTrue(summarize(case, rows, suite["thresholds"])["passed"])
        rows[-1]["fell"] = True
        self.assertFalse(summarize(case, rows, suite["thresholds"])["passed"])

    def test_loss_case_requires_actual_stop_not_only_zero_command(self):
        suite = json.loads(SUITE.read_text())
        case = next(c for c in suite["cases"] if c["kind"] == "loss")
        rows = [{"time_s": (i+1)/50, "distance_m": .6, "speed_m_s": .2,
                 "fell": False, "visible": i < 150, "robot_xyz_m": [0., 0., .125],
                 "command": [0., 0., 0.], "latency_ms": .1} for i in range(400)]
        self.assertFalse(summarize(case, rows, suite["thresholds"])["passed"])
        for row in rows:
            row["speed_m_s"] = 0.
        self.assertTrue(summarize(case, rows, suite["thresholds"])["passed"])
        self.assertTrue(target_at(case, 2.98)[1])
        self.assertFalse(target_at(case, 3.)[1])


if __name__ == "__main__":
    unittest.main()
