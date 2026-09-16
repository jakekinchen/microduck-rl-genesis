"""Prevent yaw refinement from silently changing frozen physics or curricula."""
import ast,unittest
from pathlib import Path
from microduck.native_yaw_env_v55 import downhill_yaw_cost
R=Path(__file__).resolve().parents[1]
class YawTests(unittest.TestCase):
    def test_absolute_error_cannot_cancel_alternating_yaw(self):
        for w in (3.,6.):
            self.assertAlmostEqual(downhill_yaw_cost(.2,0,w),w)
            self.assertAlmostEqual(downhill_yaw_cost(-.2,0,w),w)
            self.assertAlmostEqual(downhill_yaw_cost(.1,.1,w),0.)
    def test_only_yaw_plumbing_changes_in_native_environment(self):
        old=(R/'microduck/native_sequence_env_v54.py').read_text()
        new=(R/'microduck/native_yaw_env_v55.py').read_text()
        new=new.replace('"""V55: identical V54 dynamics/curriculum, parameterized downhill yaw weight."""','"""V54 shared native dynamics and outcome-gated transition curriculum."""')
        new=new.replace('def downhill_yaw_cost(actual, requested, weight=3.):','def downhill_yaw_cost(actual, requested):').replace('return weight*abs(actual-requested)/.20','return 3*abs(actual-requested)/.20')
        new=new.replace('def __init__(self, num_envs, seed, output, yaw_weight=3.):\n        if yaw_weight not in (3., 6.): raise ValueError("frozen yaw weights only")\n        self.yaw_weight = yaw_weight','def __init__(self, num_envs, seed, output):')
        new=new.replace('Native-Yaw-Refinement-v55','Native-Locomotion-Recipe-v54').replace('yaw_cost=f"{yaw_weight} * abs(actual yaw rate - requested yaw rate) / .20 on downhill walking"','yaw_cost="3 * abs(actual yaw rate - requested yaw rate) / .20 on downhill walking"')
        new=new.replace("downhill_yaw_cost(row['yaw_rate_rad_s'], requested[2], self.yaw_weight)","downhill_yaw_cost(row['yaw_rate_rad_s'], requested[2])")
        self.assertEqual(ast.dump(ast.parse(old)),ast.dump(ast.parse(new)))
if __name__=='__main__': unittest.main()
