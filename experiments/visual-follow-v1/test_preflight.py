import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE))
from preflight import check_cases


class DomainPreflightTests(unittest.TestCase):
    def test_all_declared_development_factors_use_supported_frozen_lane(self):
        protocol = json.loads((HERE/"protocol.json").read_text())
        self.assertTrue(check_cases(protocol["cases"])["all_supported"])

    def test_fresh_unsupported_configuration_is_explicitly_blocked(self):
        protocol = json.loads((HERE/"protocol.json").read_text())
        result = check_cases(protocol["fresh_layout_development_cases"])
        self.assertFalse(result["all_supported"])
        self.assertEqual([r["case"] for r in result["cases"] if not r["supported"]], ["offset-bay"])
        self.assertEqual(result["cases"][1]["error"], "outside frozen exploratory domain")


if __name__ == "__main__":
    unittest.main()
