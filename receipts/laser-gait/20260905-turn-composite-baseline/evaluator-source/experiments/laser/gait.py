"""Reward-independent gait diagnostics; all probes operate on copied MuJoCo data.

These are visible-development rejection gates, not a hardware calibration.
Loaded contact-point speed distinguishes foot sliding from harmless ankle/site
motion during rolling contact. Sole clearance uses the collision mesh, not a
site whose origin may be above the sole.
"""
import mujoco
import numpy as np


class GaitProbe:
    def __init__(self, core):
        self.core = core
        self.data = mujoco.MjData(core.model)
        self.feet = [core.model.geom(f"{side}_foot_collision").id for side in ("left", "right")]
        self.floor = core.model.geom("floor").id
        self.vertices = []
        for geom in self.feet:
            mesh = core.model.geom_dataid[geom]
            start, count = core.model.mesh_vertadr[mesh], core.model.mesh_vertnum[mesh]
            self.vertices.append(core.model.mesh_vert[start:start+count].copy())

    def sample(self, row):
        c, m, d = self.core, self.core.model, self.data
        # Recompute forces/kinematics at the current state without advancing or
        # changing the simulated world, policy inputs, RNG or controller state.
        mujoco.mj_copyData(d, m, c.data)
        mujoco.mj_forward(m, d)
        load = np.zeros(2)
        speed_load = np.zeros(2)
        nonfoot = []
        for i in range(d.ncon):
            contact = d.contact[i]
            a, b = int(contact.geom1), int(contact.geom2)
            if self.floor not in (a, b):
                continue
            geom = b if a == self.floor else a
            force = np.zeros(6)
            mujoco.mj_contactForce(m, d, i, force)
            normal = max(0., float(force[0]))
            if geom not in self.feet:
                if normal > .1:
                    nonfoot.append({"body": m.body(m.geom_bodyid[geom]).name, "normal_n": normal})
                continue
            foot = self.feet.index(geom)
            jac = np.zeros((3, m.nv))
            mujoco.mj_jac(m, d, jac, None, contact.pos, int(m.geom_bodyid[geom]))
            velocity = jac @ d.qvel
            # First contact-frame axis is the normal. Remaining axes tangent.
            tangent = contact.frame.reshape(3, 3)[1:] @ velocity
            load[foot] += normal
            speed_load[foot] += normal * np.linalg.norm(tangent)
        clearance = []
        for geom, vertices in zip(self.feet, self.vertices):
            world = vertices @ d.geom_xmat[geom].reshape(3, 3).T + d.geom_xpos[geom]
            clearance.append(float(world[:, 2].min()))
        q, limits = d.qpos[c.qpos_indices], m.jnt_range[c.joint_ids]
        target = c.home + np.asarray(row["action_rad"])
        violation = np.maximum(limits[:, 0]-target, 0) + np.maximum(target-limits[:, 1], 0)
        actual_violation = np.maximum(limits[:, 0]-q, 0) + np.maximum(q-limits[:, 1], 0)
        limit_margin = np.minimum(q-limits[:, 0], limits[:, 1]-q)/(limits[:, 1]-limits[:, 0])
        # CAD site +X agrees with mouth-tip direction. The legacy CAMERA -Z
        # points inside the head, so it must not define physical facing.
        face = d.site("head_camera").xmat.reshape(3, 3)[:, 0]
        optical = -d.cam_xmat[m.camera("head_camera").id].reshape(3, 3)[:, 2]
        speed = np.linalg.norm(d.qvel[:2])
        face_cos = float(np.dot(face[:2], d.qvel[:2]) / max(1e-9, np.linalg.norm(face[:2])*speed))
        return dict(row, qpos=d.qpos.tolist(), qvel=d.qvel.tolist(),
                    foot_normal_n=load.tolist(),
                    loaded_contact_slip_m_s=np.divide(speed_load, load, out=np.zeros(2), where=load>0).tolist(),
                    sole_clearance_m=clearance, nonfoot_ground_contacts=nonfoot,
                    face_velocity_cosine=face_cos, face_world=face.tolist(),
                    camera_optical_forward_world=optical.tolist(),
                    camera_face_alignment_cosine=float(np.dot(face,optical)),
                    servo_target_rad=target.tolist(), servo_target_limit_violation_rad=violation.tolist(),
                    joint_limit_violation_rad=actual_violation.tolist(),
                    joint_limit_margin_fraction=limit_margin.tolist(),
                    actuator_torque_nm=c.data.actuator_force.tolist(),
                    servo_velocity_rad_s=d.qvel[c.dof_indices].tolist())


def segments(mask):
    """Half-open runs of True values."""
    indices = np.flatnonzero(np.diff(np.r_[False, mask, False]))
    return list(zip(indices[::2], indices[1::2]))


def summarize_gait(rows, dt=.02):
    if not rows:
        raise ValueError("gait evidence missing")
    for index, row in enumerate(rows):
        if abs(row["time_s"]-(index+1)*dt)>1e-8:
            raise ValueError("missing or irregular gait samples")
        for field, size in (("foot_normal_n",2), ("loaded_contact_slip_m_s",2),
                            ("sole_clearance_m",2), ("joint_limit_margin_fraction",14),
                            ("servo_target_limit_violation_rad",14), ("joint_limit_violation_rad",14),
                            ("servo_velocity_rad_s",14), ("actuator_torque_nm",14),
                            ("command",3), ("robot_xyz_m",3)):
            value = np.asarray(row[field], float)
            if value.shape!=(size,) or not np.isfinite(value).all():
                raise ValueError(f"invalid gait field: {field}")
        if not np.isfinite([row["face_velocity_cosine"],row["speed_m_s"],row["tilt_deg"]]).all():
            raise ValueError("invalid gait scalar")
    active = np.array([r["time_s"] >= 1 and (abs(r["command"][0])>.03 or abs(r["command"][2])>.15) for r in rows])
    translating = active & np.array([r["speed_m_s"]>.03 for r in rows])
    loads = np.array([r["foot_normal_n"] for r in rows])
    slip = np.array([r["loaded_contact_slip_m_s"] for r in rows])
    clear = np.array([r["sole_clearance_m"] for r in rows])
    loaded = loads > 1.
    events = []
    for foot in range(2):
        for start, end in segments(~loaded[:, foot]):
            # Exclude startup/truncated flights and contact chatter. Require
            # a real sole lift and both a loaded takeoff and loaded landing.
            if start == 0 or end == len(rows) or start*dt < 1:
                continue
            if (end-start)*dt >= .06 and clear[start:end, foot].max() >= .005:
                events.append({"foot": foot, "land_s": rows[end]["time_s"],
                               "air_s": (end-start)*dt, "clearance_m": float(clear[start:end, foot].max())})
    events.sort(key=lambda e: e["land_s"])
    event_times=[np.array([e["land_s"] for e in events if e["foot"]==foot]) for foot in range(2)]
    coverage=[]
    for row in rows:
        t=row["time_s"]
        coverage.append(all(np.any((times<=t)&(times>=t-1.5)) for times in event_times))
    coverage=np.array(coverage)
    target_bad = np.array([max(r["servo_target_limit_violation_rad"])>.01 for r in rows])
    margins = np.array([r["joint_limit_margin_fraction"] for r in rows])
    settled = np.array([r["time_s"] >= 1 for r in rows])
    face = np.array([r["face_velocity_cosine"] for r in rows])
    loaded_active = loaded & active[:, None]
    def fraction(mask, denominator):
        return float(np.sum(mask & denominator)/np.sum(denominator)) if np.any(denominator) else None
    summary = {
        "duration_s": rows[-1]["time_s"], "active_s": float(active.sum()*dt),
        "translation_s": float(translating.sum()*dt),
        "path_length_m": float(np.linalg.norm(np.diff(np.array([r["robot_xyz_m"][:2] for r in rows]), axis=0), axis=1).sum()),
        "qualified_swings_left_right": [sum(e["foot"]==i for e in events) for i in range(2)],
        "swing_events": events,
        "alternating_landing_fraction": float(np.mean([a["foot"] != b["foot"] for a,b in zip(events, events[1:])])) if len(events)>1 else None,
        "both_feet_loaded_active_fraction": fraction(loaded.all(axis=1), active),
        "loaded_slip_over_3cm_s_fraction": fraction(slip>.03, loaded_active),
        "loaded_slip_p95_m_s": float(np.quantile(slip[loaded_active], .95)) if loaded_active.any() else None,
        "backward_translation_fraction": fraction(face<-.25, translating),
        "bilateral_step_coverage_during_translation": fraction(coverage,translating),
        "target_outside_joint_limits_fraction": float(target_bad.mean()),
        "joint_hard_stop_fraction": (margins[settled]<.05).mean(axis=0).tolist() if settled.any() else None,
        "max_target_limit_violation_rad": max(max(r["servo_target_limit_violation_rad"]) for r in rows),
        "max_actual_limit_violation_rad": max(max(r["joint_limit_violation_rad"]) for r in rows),
        "max_abs_servo_velocity_rad_s": float(np.max(np.abs([r["servo_velocity_rad_s"] for r in rows]))),
        "max_abs_actuator_torque_nm": float(np.max(np.abs([r["actuator_torque_nm"] for r in rows]))),
        "nonfoot_contact_frames": sum(bool(r["nonfoot_ground_contacts"]) for r in rows),
        "max_tilt_deg": max(r["tilt_deg"] for r in rows), "fell": any(r["fell"] for r in rows),
    }
    # Conservative *rejection* checks, fixed independently of pursuit score.
    reasons = []
    if summary["fell"]: reasons.append("fall")
    if summary["active_s"] < 2: reasons.append("insufficient_active_evidence")
    if summary["translation_s"] < 1: reasons.append("no_useful_translation")
    if min(summary["qualified_swings_left_right"]) < 2: reasons.append("missing_bilateral_steps")
    if (summary["bilateral_step_coverage_during_translation"] or 0)<.60: reasons.append("unsustained_bilateral_stepping")
    if (summary["loaded_slip_over_3cm_s_fraction"] or 0) > .20: reasons.append("persistent_loaded_foot_slip")
    if (summary["backward_translation_fraction"] or 0) > .10: reasons.append("backward_pursuit")
    # A BAM position reference may legitimately exceed a mechanical angle to
    # produce torque with low firmware gain. Reject actual hard-stop parking,
    # not command overshoot alone; never silently clip the policy's output.
    if summary["joint_hard_stop_fraction"] is None: reasons.append("missing_joint_limit_evidence")
    elif max(summary["joint_hard_stop_fraction"]) > .20: reasons.append("persistent_joint_hard_stop")
    if summary["max_actual_limit_violation_rad"] > .05: reasons.append("joint_limit_excursion")
    if summary["nonfoot_contact_frames"]: reasons.append("nonfoot_support")
    summary.update(rejection_reasons=reasons, rejection_gate_passed=not reasons,
                   physical_transfer_validated=False,
                   boundary="Visible-development rejection only. Passing is not hardware or calibrated gait acceptance; walk model omits body/floor collisions.")
    return summary
