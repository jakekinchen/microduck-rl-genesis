"""Synthetic protocol tests; no model/physics/actor or hardware execution."""
from dataclasses import fields, replace
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from handoff import HandoffPreview, HOME, Phase, RecoveryReadiness, Sample


def complete_fixture():
    # These are synthetic verifier inputs, not receipts and not actuator authority.
    return RecoveryReadiness(**{f.name: "a"*64 for f in fields(RecoveryReadiness)})


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.now = -0.02

    def tick(self, machine, request=None, **changes):
        self.now = round(self.now+.02, 8)
        sample = Sample(self.now, (0., 0., 0.), (0., 0., -1.), HOME, (0.,)*14)
        decision = machine.update(replace(sample, **changes), self.now, request)
        self.assertIsNone(decision.actuator_actions)
        self.assertFalse(decision.physical_authority)
        return decision

    def until(self, machine, phase, limit=600, **changes):
        for _ in range(limit):
            decision = self.tick(machine, **changes)
            if decision.phase == phase:
                return decision
        self.fail(f"Never reached {phase}; actual={machine.phase}")

    def enter_recovery(self, machine):
        self.tick(machine, "recover")
        self.until(machine, Phase.RECOVERY_ENTRY)
        return self.tick(machine)

    def test_missing_actor_prevents_recovery_request(self):
        machine = HandoffPreview()
        result = self.enter_recovery(machine)
        self.assertEqual(result.phase, Phase.BLOCKED)
        self.assertIsNone(result.preview_actor)
        self.assertIn("missing_verified_actor", result.reasons)
        self.assertEqual(len(result.reasons), 6)
        self.assertEqual(self.tick(machine, "walk").phase, Phase.BLOCKED)

    def test_full_continuous_sequence_with_synthetic_verified_inputs(self):
        machine = HandoffPreview(complete_fixture())
        self.assertEqual(self.enter_recovery(machine).phase, Phase.RECOVERING)
        for _ in range(20):
            result = self.tick(machine, gravity=(1., 0., 0.))
            self.assertEqual(result.phase, Phase.RECOVERING)
        self.until(machine, Phase.STABILIZING)
        self.until(machine, Phase.READY_WALK)
        self.assertEqual(self.tick(machine).phase, Phase.READY_WALK)
        self.assertEqual(self.tick(machine, "walk").phase, Phase.WALKING)

    def test_disturbance_resets_sensor_quiet_dwell(self):
        machine = HandoffPreview()
        self.tick(machine, "recover")
        for _ in range(20): self.tick(machine)
        self.tick(machine, gyro_rad_s=(.21, 0., 0.))
        for _ in range(20):
            self.assertEqual(self.tick(machine).phase, Phase.STOPPING)
        self.until(machine, Phase.RECOVERY_ENTRY)

    def test_stale_and_future_samples_fault(self):
        for stamp, now in [(0., .061), (.01, 0.)]:
            machine = HandoffPreview()
            sample = Sample(stamp, (0.,)*3, (0., 0., -1.), HOME, (0.,)*14)
            self.assertEqual(machine.update(sample, now).phase, Phase.FAULT)

    def test_duplicate_reordered_and_missing_frames_fault(self):
        for second in [0., -.02, .08]:
            machine = HandoffPreview()
            sample = Sample(0., (0.,)*3, (0., 0., -1.), HOME, (0.,)*14)
            machine.update(sample, 0.)
            self.assertEqual(machine.update(replace(sample, timestamp_s=second), max(0., second)).phase, Phase.FAULT)

    def test_privileged_contact_is_not_deployable_input(self):
        machine = HandoffPreview()
        result = self.tick(machine, contact_regions=frozenset(("left_foot",)), contact_source="mujoco_ground_truth")
        self.assertEqual(result.phase, Phase.FAULT)
        self.assertIn("undeclared_or_privileged_contact_source", result.reasons)

    def test_contact_allowances_differ_and_cannot_complete_with_shell_support(self):
        machine = HandoffPreview(complete_fixture(), {"synthetic_verified_contact_source"})
        self.enter_recovery(machine)
        for _ in range(60):
            result = self.tick(machine, contact_regions=frozenset(("head_shell",)),
                               contact_source="synthetic_verified_contact_source")
            self.assertEqual(result.phase, Phase.RECOVERING)
        self.until(machine, Phase.STABILIZING, contact_regions=frozenset(("left_foot", "right_foot")),
                   contact_source="synthetic_verified_contact_source")
        result = self.tick(machine, contact_regions=frozenset(("head_shell",)),
                           contact_source="synthetic_verified_contact_source")
        self.assertEqual(result.phase, Phase.FAULT)

    def test_servo_loading_contact_never_allowed_by_preview(self):
        machine = HandoffPreview(complete_fixture(), {"synthetic_verified_contact_source"})
        self.enter_recovery(machine)
        result = self.tick(machine, contact_regions=frozenset(("servo_housing",)),
                           contact_source="synthetic_verified_contact_source")
        self.assertEqual(result.phase, Phase.FAULT)

    def test_stop_timeout(self):
        machine = HandoffPreview()
        self.tick(machine, "recover")
        result = self.until(machine, Phase.FAULT, gyro_rad_s=(.3, 0., 0.))
        self.assertIn("phase_timeout", result.reasons)

    def test_recovery_timeout(self):
        machine = HandoffPreview(complete_fixture())
        self.enter_recovery(machine)
        result = self.until(machine, Phase.FAULT, gravity=(1., 0., 0.))
        self.assertIn("phase_timeout", result.reasons)

    def test_missing_full_cad_or_training_provenance_blocks(self):
        for name in ("reconciled_full_cad_sha256", "training_source_freeze_sha256"):
            self.now = -.02
            machine = HandoffPreview(replace(complete_fixture(), **{name: None}))
            result = self.enter_recovery(machine)
            self.assertEqual(result.phase, Phase.BLOCKED)
            self.assertIsNone(result.preview_actor)

    def test_standing_must_remain_qualified_before_walk(self):
        machine = HandoffPreview(complete_fixture())
        self.tick(machine, "stop")
        self.until(machine, Phase.READY_WALK)
        result = self.tick(machine, "walk", gyro_rad_s=(.3, 0., 0.))
        self.assertEqual(result.phase, Phase.FAULT)
        self.assertEqual(self.tick(machine, "walk").phase, Phase.FAULT)

    def test_missing_contacts_remain_unknown_not_a_contact_pass(self):
        result = self.tick(HandoffPreview())
        self.assertEqual(result.contact_evidence, "unavailable")

    def test_stop_in_every_recovery_phase_inhibits_further_actor_requests(self):
        for phase in (Phase.STOPPING, Phase.RECOVERY_ENTRY, Phase.RECOVERING, Phase.STABILIZING, Phase.READY_WALK):
            self.now = -.02
            machine = HandoffPreview(complete_fixture())
            self.tick(machine, "recover")
            if phase != Phase.STOPPING: self.until(machine, phase)
            result = self.tick(machine, "stop")
            self.assertEqual(result.phase, Phase.FAULT)
            self.assertIsNone(result.preview_actor)
            self.assertEqual(self.tick(machine, "walk").phase, Phase.FAULT)

    def test_cancel_in_walking_is_latched_inhibition(self):
        machine = HandoffPreview(complete_fixture())
        result = self.tick(machine, "cancel")
        self.assertEqual(result.phase, Phase.FAULT)
        self.assertIsNone(result.preview_actor)

    def test_malformed_samples_fault_instead_of_throwing(self):
        sample = Sample(0., (0.,)*3, (0., 0., -1.), HOME, (0.,)*14)
        bad_samples = [None, {}, replace(sample, gyro_rad_s=None),
                       replace(sample, gravity=("bad", 0., -1.)),
                       replace(sample, timestamp_s="bad"),
                       replace(sample, contact_regions="left_foot"),
                       replace(sample, contact_regions=frozenset(("left_foot",)), contact_source=[]),
                       replace(sample, joint_velocity_rad_s=(False,)*14)]
        for bad in bad_samples:
            self.assertEqual(HandoffPreview().update(bad, 0.).phase, Phase.FAULT)
        for now in (None, "bad", float("nan"), True):
            self.assertEqual(HandoffPreview().update(sample, now).phase, Phase.FAULT)


if __name__ == "__main__":
    unittest.main(verbosity=2)
