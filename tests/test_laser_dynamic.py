"""Dynamic targets, declared DR, live control validation, and fail-closed physics."""
import copy
import json
import math
import os
from pathlib import Path
import sys
import unittest
import urllib.request
import urllib.error
import threading
import queue
from types import SimpleNamespace
from http.server import ThreadingHTTPServer
from unittest.mock import patch
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from microduck.laser_dynamics import program_target, domain_draw
from scripts.laser_playground import validate_control, handler_for, playground_target
from scripts.evaluate_laser_dynamic import metrics
from experiments.laser.world import LaserWorld


class DynamicTests(unittest.TestCase):
    def test_playground_waypoints_keep_looping(self):
        np.testing.assert_array_equal(playground_target("retarget", 49)[0], playground_target("retarget", 1)[0])
        self.assertFalse(playground_target("retarget", 86)[1])
        self.assertTrue(playground_target("retarget", 88)[1])

    def test_nominal_routes_reject_a_stationary_noop(self):
        suite = json.loads((ROOT/"experiments/laser/dynamic-suite-v1.json").read_text())
        for program in suite["programs"]:
            rows = []
            for step in range(2400):
                target, visible, _, epoch = program_target(program, step*.02)
                rows.append({"time_s": (step+1)*.02, "visible": visible,
                             "distance_m": float(np.linalg.norm(target)), "target_epoch": epoch,
                             "fell": False, "speed_m_s": 0., "latency_ms": 0.})
            self.assertFalse(metrics(rows, program, suite["thresholds"])["passed"], program)

    def test_turn_reward_does_not_pay_full_linear_credit_for_ignoring_yaw(self):
        import torch
        from microduck.laser_turn_env import MicroduckLaserTurnEnv
        from microduck.laser_robust_env import MicroduckLaserRobustEnv
        env = object.__new__(MicroduckLaserTurnEnv)
        env.twist_cmd = torch.tensor([[0., 0., 1.], [0., 0., 1.], [0., 0., 0.]])
        env.base_ang_vel = torch.tensor([[0., 0., 0.], [0., 0., 1.], [0., 0., 0.]])
        with patch.object(MicroduckLaserRobustEnv, "_rew_track_lin", return_value=torch.ones(3)):
            values = env._rew_track_lin()
        self.assertLess(float(values[0]), .17)
        np.testing.assert_array_equal(values[1:].numpy(), [1, 1])

    def test_http_controls_are_bounded_and_loopback_only(self):
        sim = SimpleNamespace(lock=threading.Lock(), state={"ready": False}, jpeg=None, commands=queue.Queue(2))
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler_for(sim))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f"http://127.0.0.1:{server.server_port}"
        try:
            with urllib.request.urlopen(url+"/state") as response:
                self.assertEqual(json.load(response), {"ready": False})
            for data, origin in (({"target": [0, 0]}, "https://foreign.invalid"), ({"target": [2, 0]}, url)):
                req = urllib.request.Request(url+"/control", json.dumps(data).encode(), {"Content-Type": "application/json", "Origin": origin})
                with self.assertRaises(urllib.error.HTTPError):
                    urllib.request.urlopen(req)
            self.assertTrue(sim.commands.empty())
            req = urllib.request.Request(url+"/control", b'{"target":[0.1,0.2]}', {"Content-Type": "application/json", "Origin": url})
            with urllib.request.urlopen(req) as response:
                self.assertEqual(response.status, 202)
            self.assertEqual(sim.commands.get_nowait(), {"target": [.1, .2]})
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_routes_jumps_loss_and_reacquisition(self):
        self.assertFalse(np.array_equal(program_target("retarget", 6.98)[0], program_target("retarget", 7)[0]))
        self.assertFalse(program_target("retarget", 38)[1])
        self.assertFalse(program_target("retarget", 39.98)[1])
        self.assertTrue(program_target("retarget", 40)[1])
        self.assertEqual(program_target("retarget", 40)[3], 5)
        for name in ("circle", "figure-eight"):
            samples = [program_target(name, t)[0] for t in np.arange(0, 48, .02)]
            self.assertGreater(np.ptp(samples, axis=0).min(), .5)
            self.assertLess(np.linalg.norm(np.diff(samples, axis=0), axis=1).max()/.02, .14)
        np.testing.assert_allclose(program_target("retarget", 0, rotation=math.pi/2)[0], [0, .6], atol=1e-8)

    def test_domains_reproducible_and_splits_disjoint(self):
        suite = json.loads((ROOT/"experiments/laser/dynamic-suite-v1.json").read_text())
        self.assertFalse(set(suite["development_seeds"]) & set(suite["reserved_seeds"]))
        for seed in range(100):
            d = domain_draw(seed)
            self.assertEqual(d, domain_draw(seed))
            self.assertTrue(.6 <= d["friction_ratio"] <= 1.4)
            self.assertTrue(.9 <= d["trunk_mass_ratio"] <= 1.1)
            self.assertIn(d["sensor_delay_steps"], (0, 1, 2))
            self.assertLessEqual(max(np.abs(d["push_delta_v_m_s"])), .1)
        self.assertEqual(domain_draw(1, False)["push_delta_v_m_s"], [0, 0])

    def test_controls_reject_bad_input(self):
        for value in ({"target": [float("nan"), 0]}, {"target": [True, 0]}, {"target": [2, 0]},
                      {"target": [0]}, {"paused": "false"}, {"mode": "teleport"}, {"domain": "hills"},
                      {"action": [0]*14}, {}, [], {"reset": 1}):
            with self.assertRaises(ValueError):
                validate_control(value)
        self.assertEqual(validate_control({"target": [-1, 1], "paused": True}), {"target": [-1, 1], "paused": True})

    def test_metrics_cannot_hide_falls_or_incomplete_runs(self):
        suite = json.loads((ROOT/"experiments/laser/dynamic-suite-v1.json").read_text())
        row = {"time_s": 48., "visible": True, "distance_m": .2, "target_epoch": 0,
               "fell": False, "speed_m_s": 0., "latency_ms": .1}
        self.assertTrue(metrics([row], "circle", suite["thresholds"])["passed"])
        for update in ({"fell": True}, {"time_s": 47.9}, {"distance_m": .31}):
            self.assertFalse(metrics([dict(row, **update)], "circle", suite["thresholds"])["passed"])


@unittest.skipUnless(os.environ.get("BAM_REPO"), "exact BAM_REPO required for real world tests")
class WorldTests(unittest.TestCase):
    def setUp(self):
        self.domain = domain_draw(75001, False)
        self.world = LaserWorld(ROOT/"receipts/laser-follow/20260904-v2-steering/policy.onnx", os.environ["BAM_REPO"], self.domain)

    def tearDown(self):
        self.world.close()

    def test_actions_and_targets_fail_before_advancing(self):
        for target in ([np.nan, 0], [4, 0], [0, 0, 0]):
            with self.assertRaises(ValueError):
                self.world.step(target)
        with patch.object(self.world.core.policy, "infer", return_value=(np.full((1, 14), np.nan), 0)):
            with self.assertRaises(ValueError):
                self.world.step([.6, 0])
        self.assertEqual(self.world.steps, 0)

    def test_loss_commands_are_not_sensor_delayed(self):
        self.domain["sensor_delay_steps"] = 2
        self.world.step([.6, 0])
        self.world.step([.6, 0])
        row = self.world.step([.6, 0], False)
        np.testing.assert_array_equal(row["command"], [0, 0, 0])
        np.testing.assert_array_equal(self.world.last_observation[0, 48:51], [0, 0, 0])

    def test_domain_changes_real_parameters_without_mutating_next_reset(self):
        d = copy.deepcopy(self.domain)
        d.update(friction_ratio=.6, trunk_mass_ratio=1.1, motor_kp_ratio=.9)
        altered = LaserWorld(ROOT/"receipts/laser-follow/20260904-v2-steering/policy.onnx", os.environ["BAM_REPO"], d)
        try:
            np.testing.assert_allclose(altered.core.model.geom_friction[:, 0], self.world.core.model.geom_friction[:, 0]*.6)
            from microduck.constants import TRUNK_BODY
            idx = altered.core.model.body(TRUNK_BODY).id
            self.assertAlmostEqual(altered.core.model.body_mass[idx], self.world.core.model.body_mass[idx]*1.1)
            np.testing.assert_allclose(altered.core.controller.model.actuator.kp, self.world.core.controller.model.actuator.kp*.9)
        finally:
            altered.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
