"""Planning-lint regression fixtures; no behavior or physics is validated."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from duck_workspace.core import check_spec, new_behavior
from duck_workspace.quality_plan import QUALITY_PLAN_FIELDS, check_quality_plan, new_quality_plan


class BehaviorQualityPlanTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.path = new_behavior(self.root, "fixture", "Synthetic planning fixture") / "spec.json"
        self.draft = json.loads(self.path.read_text())

    def complete_fixture(self):
        data = copy.deepcopy(self.draft)
        for field in ("hypothesis", "model_variant", "target_source", "visible_suite", "baseline", "next_decision"):
            data[field] = "Synthetic fixture; not execution evidence"
        for field in ("actor_inputs", "reward_terms", "failure_conditions", "success_metrics"):
            data[field] = ["Synthetic fixture"]
        data["budget"].update(training_iterations=1, seed=0)
        data["implementation"] = {"train_entrypoint": "fixture.py", "evaluate_entrypoint": "fixture.py"}
        for group, fields in QUALITY_PLAN_FIELDS.items():
            data["quality_plan"][group] = {field: "Synthetic plan section reference" for field in fields}
        return data

    def save_and_check(self, data):
        self.path.write_text(json.dumps(data))
        return check_spec(self.path)

    def test_new_draft_is_v2_and_every_quality_field_starts_incomplete(self):
        data = json.loads(self.path.read_text())
        self.assertEqual(data["schema"], "microduck.behavior-draft/v2")
        self.assertEqual(data["quality_plan"], new_quality_plan())
        self.assertEqual(len(check_quality_plan(data["quality_plan"])),
                         sum(map(len, QUALITY_PLAN_FIELDS.values())))

    def test_complete_plan_is_only_visible_development_and_read_only(self):
        data = self.complete_fixture()
        self.assertEqual(self.save_and_check(data), [])
        before = self.path.read_bytes()
        self.assertEqual(check_spec(self.path), [])
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(data["status"], "draft")
        self.assertEqual(data["claim_scope"], "visible_development")

    def test_omitting_any_quality_field_or_section_is_incomplete(self):
        baseline = self.complete_fixture()
        for group, fields in QUALITY_PLAN_FIELDS.items():
            with self.subTest(group=group):
                data = copy.deepcopy(baseline)
                del data["quality_plan"][group]
                self.assertTrue(self.save_and_check(data))
            for field in fields:
                with self.subTest(group=group, field=field):
                    data = copy.deepcopy(baseline)
                    del data["quality_plan"][group][field]
                    self.assertTrue(self.save_and_check(data))

    def test_malformed_groups_and_unexplained_exemptions_fail_closed(self):
        for value in (None, False, [], "physics is accurate"):
            with self.subTest(value=value):
                data = self.complete_fixture()
                data["quality_plan"] = value
                self.assertTrue(self.save_and_check(data))
        for value in (None, True, 1, [], {}, "", "   ", "TBD", "n/a", "not applicable"):
            with self.subTest(value=value):
                data = self.complete_fixture()
                data["quality_plan"]["physics_validation"]["measurement_calibration_uncertainty_and_known_gaps"] = value
                self.assertTrue(self.save_and_check(data))

    def test_legacy_draft_cannot_silently_satisfy_new_contract(self):
        data = self.complete_fixture()
        data["schema"] = "microduck.behavior-draft/v1"
        self.assertIn("legacy v1", self.save_and_check(data)[0])
        self.assertEqual(json.loads(self.path.read_text())["schema"], "microduck.behavior-draft/v1")

    def test_completed_plan_cannot_claim_acceptance_or_hardware_authority(self):
        for scope in ("accepted", "physical", "held_out"):
            with self.subTest(scope=scope):
                data = self.complete_fixture()
                data["claim_scope"] = scope
                self.assertTrue(self.save_and_check(data))
        for status in (None, "accepted", "completed"):
            with self.subTest(status=status):
                data = self.complete_fixture()
                data["status"] = status
                self.assertTrue(self.save_and_check(data))

    def test_new_templates_do_not_share_mutable_sections(self):
        first, second = new_quality_plan(), new_quality_plan()
        first["evidence"]["reproduction_and_regression_plan"] = "changed"
        self.assertIsNone(second["evidence"]["reproduction_and_regression_plan"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
