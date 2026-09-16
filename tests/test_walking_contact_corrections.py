"""Standalone process entry for pure geometry/controller correction tests."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


if __name__ == '__main__':
    names = ['test_walking_collision_model', 'test_walking_self_contact',
             'test_walking_cad_intersections', 'test_heading_servo',
             'test_walking_persistent_timing', 'test_walking_persistent_contact']
    suite = unittest.defaultTestLoader.loadTestsFromNames(names)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(not result.wasSuccessful())
