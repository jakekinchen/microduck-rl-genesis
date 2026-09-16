"""Persistent timing primitives; no simulator initialization or policy execution."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import torch
import genesis as gs
from microduck.bam_actuator import DelayBuffer
from microduck.walking_viability_env import MicroduckViableWalkingEnv
from microduck.walking_persistent_timing_env import EpisodeDelayBuffer, MicroduckPersistentTimingWalkingEnv


class PersistentTimingTests(unittest.TestCase):
    def setUp(self):
        # The FIFO needs only Genesis's initialized dtype, not a scene/runtime.
        # Keep this a pure CPU tensor test and restore the module after each case.
        dtype = patch.object(gs, "tc_float", torch.float32, create=True)
        dtype.start()
        self.addCleanup(dtype.stop)

    def test_call_is_exact_parent_fifo(self):
        self.assertIs(EpisodeDelayBuffer.__call__, DelayBuffer.__call__)

    def test_lags_do_not_change_over_four_thousand_physics_ticks(self):
        torch.manual_seed(76740)
        buf = EpisodeDelayBuffer((32, 2), 0, 6, "cpu")
        lags = buf._lag.clone()
        for i in range(4000):
            value = torch.full((32, 2), float(i))
            out = buf(value)
            expected = (i - lags).clamp_min(0).float()[:, None].expand(-1, 2)
            torch.testing.assert_close(out, expected, rtol=0, atol=0)
        self.assertTrue(torch.equal(lags, buf._lag))

    def test_selected_reset_resamples_only_that_device_and_primes_current_value(self):
        buf = EpisodeDelayBuffer((3, 2), 0, 6, "cpu")
        buf._lag[:] = torch.tensor([1, 3, 5])
        for i in range(12):
            buf(torch.full((3, 2), float(i)))
        before = buf._buf.clone()
        with patch("microduck.walking_persistent_timing_env.torch.randint", return_value=torch.tensor([6])) as draw:
            buf.reset(torch.tensor([1]))
        draw.assert_called_once()
        self.assertEqual(buf._lag.tolist(), [1, 6, 5])
        self.assertTrue(torch.equal(buf._buf, before))
        output = buf(torch.tensor([[12., 12.], [99., 99.], [12., 12.]]))
        self.assertEqual(output.tolist(), [[11., 11.], [99., 99.], [7., 7.]])

    def test_zero_delay_is_byte_identical_current_tensor(self):
        buf = EpisodeDelayBuffer((2, 14), 0, 0, "cpu")
        value = torch.randn(2, 14)
        self.assertIs(buf(value), value)
        buf.reset(torch.tensor([0, 1]))
        self.assertIs(buf(value), value)

    def test_ranges_cover_endpoints_and_reset_draws_are_reproducible(self):
        outputs = []
        for _ in range(2):
            torch.manual_seed(76741)
            buf = EpisodeDelayBuffer((4096, 1), 0, 6, "cpu")
            draws = [buf._lag.clone()]
            buf.reset(torch.arange(4096))
            draws.append(buf._lag.clone())
            outputs.append(torch.stack(draws))
            self.assertEqual(set(draws[0].tolist()), set(range(7)))
            self.assertEqual(set(draws[1].tolist()), set(range(7)))
            self.assertFalse(torch.equal(draws[0], draws[1]))
        self.assertTrue(torch.equal(outputs[0], outputs[1]))

    def test_rewards_physics_observations_actions_reset_commands_unchanged(self):
        for name in ("step", "_build_scene", "_compute_rewards", "_refresh_state", "_update_contacts",
                     "_compute_observations", "reset_idx", "_check_termination", "_resample_twist",
                     "_apply_curricula", "_startup_randomization"):
            self.assertIs(getattr(MicroduckPersistentTimingWalkingEnv, name),
                          getattr(MicroduckViableWalkingEnv, name))

    def test_empty_reset_and_invalid_ranges(self):
        buf = EpisodeDelayBuffer((2, 1), 0, 1, "cpu")
        old = buf._lag.clone()
        buf.reset(torch.tensor([], dtype=torch.long))
        self.assertTrue(torch.equal(old, buf._lag))
        for low, high in ((-1, 1), (0, 7), (2, 1), (False, 1), (0, 1.5)):
            with self.assertRaises(ValueError):
                EpisodeDelayBuffer((2, 1), low, high, "cpu")


if __name__ == "__main__":
    unittest.main(verbosity=2)
