"""Standalone entry for frozen V14 routing/load tests."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromName("test_walking_standing"))
    sys.exit(not result.wasSuccessful())
