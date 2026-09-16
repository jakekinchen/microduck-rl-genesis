from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import unittest
import numpy as np
from experiments.walking.command_ramp import CommandRamp


class CommandRampTests(unittest.TestCase):
    def test_zero_stays_exact_zero(self):
        r=CommandRamp()
        np.testing.assert_array_equal(r.step([0,0,0]), np.zeros(3,np.float32))

    def test_slope_and_exact_stop(self):
        r=CommandRamp()
        np.testing.assert_allclose(r.step([.22,-.22,.75]), [.015,-.015,.05])
        for _ in range(14):
            result=r.step([.22,-.22,.75])
        np.testing.assert_array_equal(result,np.asarray([.22,-.22,.75],np.float32))
        for _ in range(15):
            result=r.step([0,0,0])
        np.testing.assert_array_equal(result,np.zeros(3,np.float32))

    def test_arbitrary_reversal_has_same_bound(self):
        r=CommandRamp()
        prior=r.value.copy()
        for command in [[.12,0,.4]]*10+[[-.12,0,-.4]]*20+[[.08,0,0]]*10:
            result=r.step(command)
            self.assertTrue(np.all(np.abs(result-prior)<=r.rate_per_s*.02+1e-7))
            prior=result.copy()

    def test_invalid_input_does_not_change_state(self):
        r=CommandRamp()
        with self.assertRaises(ValueError):
            r.step([float('nan'),0,0])
        np.testing.assert_array_equal(r.value,np.zeros(3))


if __name__=='__main__':
    unittest.main()
