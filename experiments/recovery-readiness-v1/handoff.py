"""Offline recovery handoff preview. This module cannot issue motor commands.

Fresh IMU/encoder observations can qualify a transition predicate; they cannot
prove support, walking success, physical calibration or a recovery capability.
Contact observations are consulted only for a declared deployable source.
"""
from dataclasses import dataclass
from enum import Enum
import json
import math
from numbers import Real
from pathlib import Path

_CONTRACT = Path(__file__).resolve().parents[2] / "microduck_contract/interface/observation-v1.json"
HOME = tuple(json.loads(_CONTRACT.read_text())["home_joint_position_rad"])

FEET = frozenset(("left_foot", "right_foot"))
# Candidate envelope only; an actor must earn these allowances in its evaluator.
RECOVERY_SURFACES = FEET | {"trunk_shell", "head_shell"}


class Phase(str, Enum):
    WALKING = "walking"
    STOPPING = "stopping"
    RECOVERY_ENTRY = "recovery_entry"
    RECOVERING = "recovering"
    STABILIZING = "stabilizing"
    READY_WALK = "ready_walk"
    BLOCKED = "blocked"
    FAULT = "fault"


@dataclass(frozen=True)
class Sample:
    timestamp_s: float
    gyro_rad_s: tuple[float, float, float]
    gravity: tuple[float, float, float]
    joint_position_rad: tuple[float, ...]
    joint_velocity_rad_s: tuple[float, ...]
    contact_regions: frozenset[str] | None = None
    contact_source: str | None = None


@dataclass(frozen=True)
class RecoveryReadiness:
    """Already verified evaluator inputs, not a public manifest or authorization.

    The default is blocked. No loader upgrades upstream metadata to these
    receipts. Positive values are used only by synthetic contract tests here;
    a future integration must obtain them from the evaluator's hash verifier.
    """
    actor_sha256: str | None = None
    training_source_freeze_sha256: str | None = None
    reconciled_full_cad_sha256: str | None = None
    actual_surface_audit_sha256: str | None = None
    internal_load_audit_sha256: str | None = None
    task_safety_transition_endurance_receipt_sha256: str | None = None

    def failures(self):
        failures = []
        for name, value in vars(self).items():
            if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
                failures.append("missing_verified_" + name.removesuffix("_sha256"))
        return tuple(failures)


@dataclass(frozen=True)
class Decision:
    phase: Phase
    preview_actor: str | None
    request_zero_twist: bool
    reasons: tuple[str, ...]
    contact_evidence: str
    # Deliberately invariant. This is not an actuator-capable controller.
    actuator_actions: None = None
    physical_authority: bool = False


class HandoffPreview:
    """One continuous transition; faults/blockers latch until a new instance.

    Start only as a shadow observer of an already-running retained controller.
    Times are aligned monotonic seconds, supplied by the caller for replay.
    """
    def __init__(self, readiness=None, deployable_contact_sources=frozenset()):
        self.readiness = readiness or RecoveryReadiness()
        self.deployable_contact_sources = frozenset(deployable_contact_sources)
        self.phase = Phase.WALKING
        self.entered_s = None
        self.last_sample_s = None
        self.last_now_s = None
        self.quiet_since_s = None
        self.reasons = ()

    def transition(self, phase, now):
        self.phase = phase
        self.entered_s = now
        self.quiet_since_s = None

    def fail(self, reason, now):
        self.transition(Phase.FAULT, now)
        self.reasons = (reason,)

    def result(self, contacts):
        selected = {
            Phase.WALKING: "retained_walking",
            Phase.STOPPING: "retained_command_ramp_to_zero",
            Phase.RECOVERING: "recovery_candidate",
            Phase.STABILIZING: "retained_standing",
            Phase.READY_WALK: "retained_standing",
        }.get(self.phase)
        return Decision(self.phase, selected, self.phase not in (Phase.WALKING, Phase.RECOVERING),
                        self.reasons, contacts)

    def update(self, sample, now_s, request=None):
        if self.phase in (Phase.FAULT, Phase.BLOCKED):
            return self.result("unavailable")
        if request not in (None, "recover", "walk", "stop", "cancel"):
            self.fail("unknown_request", now_s)
            return self.result("unavailable")
        if not isinstance(sample, Sample):
            self.fail("invalid_sensor_sample", now_s)
            return self.result("unavailable")
        vectors = (sample.gyro_rad_s, sample.gravity, sample.joint_position_rad, sample.joint_velocity_rad_s)
        try:
            valid_vectors = tuple(map(len, vectors)) == (3, 3, 14, 14) and all(
                isinstance(x, Real) and not isinstance(x, bool) and math.isfinite(x) for v in vectors for x in v)
        except (TypeError, ValueError):
            valid_vectors = False
        if not valid_vectors:
            self.fail("invalid_sensor_shape_or_values", now_s)
            return self.result("unavailable")
        if not all(isinstance(t, Real) and not isinstance(t, bool) and math.isfinite(t)
                   for t in (now_s, sample.timestamp_s)):
            self.fail("invalid_timestamp", now_s)
            return self.result("unavailable")
        if self.last_now_s is not None and now_s < self.last_now_s:
            self.fail("clock_reversed", now_s)
            return self.result("unavailable")
        self.last_now_s = now_s
        age = now_s - sample.timestamp_s
        if age < 0 or age > .060:
            self.fail("future_or_stale_sample", now_s)
            return self.result("unavailable")
        if self.last_sample_s is not None and sample.timestamp_s <= self.last_sample_s:
            self.fail("duplicate_or_reordered_sample", now_s)
            return self.result("unavailable")
        if self.last_sample_s is not None and sample.timestamp_s-self.last_sample_s > .060:
            # Missing frames cannot silently contribute to an uninterrupted dwell.
            self.fail("sensor_gap", now_s)
            return self.result("unavailable")
        self.last_sample_s = sample.timestamp_s
        norm = math.sqrt(sum(x*x for x in sample.gravity))
        if abs(norm-1) > .02:
            self.fail("invalid_projected_gravity", now_s)
            return self.result("unavailable")
        contacts = "unavailable"
        if sample.contact_regions is not None:
            if not isinstance(sample.contact_regions, frozenset) or not all(isinstance(c, str) for c in sample.contact_regions):
                self.fail("invalid_contact_observation", now_s)
                return self.result("unavailable")
            if not isinstance(sample.contact_source, str) or not sample.contact_source or sample.contact_source not in self.deployable_contact_sources:
                self.fail("undeclared_or_privileged_contact_source", now_s)
                return self.result("unavailable")
            contacts = "declared_deployable_source"
            allowed = RECOVERY_SURFACES if self.phase in (Phase.RECOVERY_ENTRY, Phase.RECOVERING) else FEET
            if not sample.contact_regions.issubset(allowed):
                self.fail("forbidden_contact_region", now_s)
                return self.result(contacts)
        elif sample.contact_source is not None:
            self.fail("contact_source_without_observation", now_s)
            return self.result("unavailable")
        if request == "cancel" or (request == "stop" and
            (self.phase in (Phase.RECOVERY_ENTRY, Phase.RECOVERING, Phase.STABILIZING, Phase.READY_WALK) or
             (self.phase == Phase.STOPPING and self.want_recovery))):
            # Do not select standing on a body whose recovery was interrupted.
            # Actual emergency handling belongs to an independently validated
            # actuator supervisor; this preview only inhibits further requests.
            self.fail("operator_cancel_or_stop_during_transition", now_s)
            return self.result(contacts)
        quiet = max(map(abs, sample.gyro_rad_s)) <= .20 and max(map(abs, sample.joint_velocity_rad_s)) <= .25
        tilt = math.degrees(math.acos(max(-1., min(1., -sample.gravity[2]))))
        home = max(abs(q-ref) for q, ref in zip(sample.joint_position_rad, HOME)) <= .12
        upright = tilt <= 10 and home and quiet
        # A measured shell support may be allowed during a rise, but cannot
        # satisfy the locomotion exit condition on that same sample.
        if sample.contact_regions is not None:
            upright = upright and sample.contact_regions.issubset(FEET)
        elapsed = 0 if self.entered_s is None else now_s-self.entered_s
        timeout = {Phase.STOPPING: 4., Phase.RECOVERY_ENTRY: 1., Phase.RECOVERING: 8., Phase.STABILIZING: 3.}.get(self.phase)
        if timeout is not None and elapsed >= timeout:
            self.fail("phase_timeout", now_s)
            return self.result(contacts)
        if self.phase == Phase.WALKING and request in ("recover", "stop"):
            self.want_recovery = request == "recover"
            self.transition(Phase.STOPPING, now_s)
        elif self.phase == Phase.STOPPING:
            self.quiet_since_s = (self.quiet_since_s if self.quiet_since_s is not None else sample.timestamp_s) if quiet else None
            if self.quiet_since_s is not None and sample.timestamp_s-self.quiet_since_s >= .5:
                self.transition(Phase.RECOVERY_ENTRY if self.want_recovery else Phase.STABILIZING, now_s)
        elif self.phase == Phase.RECOVERY_ENTRY:
            missing = self.readiness.failures()
            if missing:
                self.transition(Phase.BLOCKED, now_s)
                self.reasons = missing
            elif quiet:
                self.transition(Phase.RECOVERING, now_s)
        elif self.phase == Phase.RECOVERING:
            self.quiet_since_s = (self.quiet_since_s if self.quiet_since_s is not None else sample.timestamp_s) if upright else None
            if self.quiet_since_s is not None and sample.timestamp_s-self.quiet_since_s >= .75:
                self.transition(Phase.STABILIZING, now_s)
        elif self.phase == Phase.STABILIZING:
            self.quiet_since_s = (self.quiet_since_s if self.quiet_since_s is not None else sample.timestamp_s) if upright else None
            if self.quiet_since_s is not None and sample.timestamp_s-self.quiet_since_s >= .75:
                self.transition(Phase.READY_WALK, now_s)
        elif self.phase == Phase.READY_WALK:
            if not upright:
                self.fail("standing_exit_no_longer_satisfied", now_s)
            elif request == "walk":
                self.transition(Phase.WALKING, now_s)
        return self.result(contacts)
