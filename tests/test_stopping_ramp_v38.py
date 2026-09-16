import numpy as np
import unittest
from experiments.walking.command_ramp import CommandRamp
from microduck.stopping_ramp_v38 import StoppingRamp


def test_existing_moving_commands_keep_exact_arithmetic():
    original,candidate=CommandRamp(),StoppingRamp()
    for command in np.random.default_rng(38).uniform(-.2,.2,(1000,3)):
        assert original.step(command).tobytes()==candidate.step(command).tobytes()


def test_stop_rate_exact_zero_and_no_overshoot():
    ramp=StoppingRamp()
    for _ in range(30):ramp.step([.2,-.1,.5])
    previous=ramp.value.copy()
    rows=[]
    for _ in range(50):
        value=ramp.step([0,0,0]);rows.append(value.copy())
        assert np.all(np.abs(value)<=np.abs(previous)+1e-7)
        assert np.all(np.abs(value[:2]-previous[:2])<=.005+1e-7)
        previous=value.copy()
    np.testing.assert_array_equal(rows[-1],[0.,0.,0.])
    assert next(i for i,r in enumerate(rows) if np.all(r==0))==40


def test_invalid_command_rejected_without_state_change():
    ramp=StoppingRamp();ramp.step([.1,0,0]);before=ramp.value.copy()
    for value in ([np.nan,0,0],[0,0]):
        with unittest.TestCase().assertRaises(ValueError):ramp.step(value)
        np.testing.assert_array_equal(ramp.value,before)


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(unittest.FunctionTestCase(f) for f in
        (test_existing_moving_commands_keep_exact_arithmetic,
         test_stop_rate_exact_zero_and_no_overshoot,
         test_invalid_command_rejected_without_state_change))
