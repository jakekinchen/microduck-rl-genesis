"""Bounded fixed-output versus live-BAM impact diagnostics; no policy scoring."""
from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np

TIMESTEPS_S = (.005, .0025, .00125, .000625, .0003125, .00015625)


@dataclass(frozen=True)
class ImpactSchedule:
    start_s: float
    torque: np.ndarray
    damping: np.ndarray
    friction: np.ndarray
    references: np.ndarray
    bam_period_s: float = .005

    def validate(self, world):
        n = len(self.torque)
        if not 1 <= n <= 20 or not math.isclose(self.bam_period_s, .005, rel_tol=0, abs_tol=1e-12):
            raise ValueError("one to twenty fixed 5-ms BAM intervals required")
        if not math.isclose(self.start_s, .035, rel_tol=0, abs_tol=1e-12):
            raise ValueError("review window must start at the 0.035-second checkpoint")
        m = world.core.model
        for a, shape in ((self.torque, (n, m.nu)), (self.damping, (n, m.nv)),
                         (self.friction, (n, m.nv)), (self.references, (n, 14))):
            if not isinstance(a, np.ndarray) or a.shape != shape or not np.isfinite(a).all():
                raise ValueError("finite row-aligned actuator schedule required")
        if (self.damping < 0).any() or (self.friction < 0).any():
            raise ValueError("nonnegative damping/friction required")


def run_window(world, checkpoint, schedule: ImpactSchedule, timestep_s: float,
               *, mode="fixed_output", physics=None):
    """Restore first; vary integration only afterward, retaining the 200-Hz clock.

    Caller must supply a source-bound schedule and first demonstrate exact 5-ms
    clone parity against V65. This function does not assert that prerequisite.
    `references` are PRE-delay motor references at each BAM tick. Fixed-output
    holds recorded applied motor/friction/damping values. Live-BAM advances the
    restored delay FIFO and controller; it never substitutes an ideal PD.
    """
    if physics is None:
        import mujoco as physics
    if mode not in ("fixed_output", "live_bam"):
        raise ValueError("unknown diagnostic mode")
    if timestep_s not in TIMESTEPS_S:
        raise ValueError("unregistered timestep; no automatic refinement")
    schedule.validate(world)
    checkpoint.restore(world, copy_data=physics.mj_copyData)
    c = world.core
    if not math.isclose(c.data.time, schedule.start_s, rel_tol=0, abs_tol=1e-9):
        raise ValueError("checkpoint time does not match schedule")
    original_dt = c.model.opt.timestep
    substeps = round(schedule.bam_period_s / timestep_s)
    records = []
    before_warnings = np.asarray(c.data.warning.number).copy()
    try:
        c.model.opt.timestep = timestep_s
        for tick in range(len(schedule.torque)):
            if mode == "fixed_output":
                c.data.ctrl[:] = schedule.torque[tick]
                c.model.dof_damping[:] = schedule.damping[tick]
                c.model.dof_frictionloss[:] = schedule.friction[tick]
            else:
                world.applied_target = world.motor_delay.step(schedule.references[tick])
                for index, name in enumerate(c.joint_names):
                    c.controller.set_q_target(name, float(world.applied_target[index]))
                c.controller.update()
            for _ in range(substeps):
                physics.mj_step(c.model, c.data)
                expected_time = schedule.start_s + (len(records) + 1) * timestep_s
                if (not math.isclose(c.data.time, expected_time, rel_tol=0, abs_tol=1e-9)
                        or not np.isfinite(np.r_[c.data.qpos, c.data.qvel, c.data.ctrl]).all()
                        or np.any(np.asarray(c.data.warning.number) != before_warnings)):
                    raise RuntimeError("nonfinite state, simulator reset or new warning")
                contacts = []
                for index, contact in enumerate(c.data.contact):
                    force = np.zeros(6)
                    physics.mj_contactForce(c.model, c.data, index, force)
                    if not np.isfinite(force).all():
                        raise RuntimeError("nonfinite contact force")
                    contacts.append(dict(geom1=int(contact.geom1), geom2=int(contact.geom2),
                                         distance_m=float(contact.dist), force=force.tolist()))
                records.append(dict(time_s=float(c.data.time), qpos=c.data.qpos.copy(),
                                    qvel=c.data.qvel.copy(), contacts=contacts,
                                    torque=c.data.ctrl.copy(), bam_tick=tick))
    finally:
        # All other state remains the diagnostic endpoint; a new arm must restore.
        c.model.opt.timestep = original_dt
    return dict(mode=mode, timestep_s=timestep_s, start_s=schedule.start_s,
                end_s=schedule.start_s + len(schedule.torque) * schedule.bam_period_s,
                samples=records,
                evidence="open_loop_diagnostic", closed_loop_score=False,
                physical_acceptance=False)


def _validate_trace(trace, tolerance):
    """Check every integration sample, including rows off the common grid."""
    dt, start, end = trace["timestep_s"], trace["start_s"], trace["end_s"]
    if (dt not in TIMESTEPS_S or not all(math.isfinite(v) for v in (start, end))
            or not math.isclose(start, .035, rel_tol=0, abs_tol=tolerance)):
        raise ValueError("registered rate and finite 0.035-second window required")
    ticks = round((end - start) / .005)
    if not 1 <= ticks <= 20 or abs(end - start - ticks * .005) > tolerance:
        raise ValueError("one to twenty complete BAM intervals required")
    rows = trace["samples"]
    if len(rows) != ticks * round(.005 / dt):
        raise ValueError("complete full-rate trace required")
    shape = None
    for index, row in enumerate(rows, 1):
        time = row["time_s"]
        qpos = np.asarray(row["qpos"])
        if (not math.isfinite(time) or abs(time - (start + index * dt)) > tolerance
                or qpos.ndim != 1 or len(qpos) < 3 or not np.isfinite(qpos).all()
                or (shape is not None and qpos.shape != shape)):
            raise ValueError("missing, reordered or invalid full-rate state sample")
        shape = qpos.shape


def compare_common_grid(left, right, *, time_tolerance_s=1e-9):
    """Compare coarser sample times without interpolation or time shifting.

    Peak contact values must additionally be evaluated on each full-rate trace;
    this state comparison is not a substitute for contact/load acceptance.
    """
    if not math.isfinite(time_tolerance_s) or not 0 < time_tolerance_s < min(TIMESTEPS_S) / 2:
        raise ValueError("finite sub-sample time tolerance required")
    for trace in (left, right):
        _validate_trace(trace, time_tolerance_s)
    if (abs(left["start_s"] - right["start_s"]) > time_tolerance_s
            or abs(left["end_s"] - right["end_s"]) > time_tolerance_s):
        raise ValueError("complete equal-duration traces required")
    if left["timestep_s"] < right["timestep_s"]:
        left, right = right, left
    a, b = left["samples"], right["samples"]
    if not a or not b or abs(a[-1]["time_s"] - b[-1]["time_s"]) > time_tolerance_s:
        raise ValueError("complete equal-duration traces required")
    diffs, index = [], 0
    for row in a:
        while index < len(b) and b[index]["time_s"] < row["time_s"] - time_tolerance_s:
            index += 1
        if index == len(b) or abs(b[index]["time_s"] - row["time_s"]) > time_tolerance_s:
            raise ValueError("missing common-grid sample")
        x, y = np.asarray(row["qpos"]), np.asarray(b[index]["qpos"])
        if x.shape != y.shape or not np.isfinite(x).all() or not np.isfinite(y).all():
            raise ValueError("incompatible/nonfinite state")
        diffs.append(float(np.max(np.abs(x[:3] - y[:3]))))
    return {"common_samples": len(diffs), "max_root_axis_difference_m": max(diffs),
            "automatic_model_admission": False}
