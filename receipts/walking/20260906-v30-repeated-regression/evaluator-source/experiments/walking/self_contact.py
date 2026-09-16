"""Reward-independent, copied-state body-interference rejection (visible dev)."""
import numpy as np
import mujoco

MAXIMUM_SELF_PENETRATION_M = .001


class SelfContactProbe:
    def __init__(self, scene_path):
        self.model = mujoco.MjModel.from_xml_path(str(scene_path))
        self.data = mujoco.MjData(self.model)
        meshes = {self.model.mesh(int(self.model.geom_dataid[i])).name
                  for i in range(self.model.ngeom) if self.model.geom_bodyid[i]
                  and (self.model.geom_contype[i] or self.model.geom_conaffinity[i])}
        if not {"np_f970", "power_support", "leg", "sole_left", "sole_right"} <= meshes:
            raise ValueError("required complete body collision coverage missing")

    def sample(self, qpos):
        q = np.asarray(qpos, float)
        if q.shape != (21,) or not np.isfinite(q).all() or abs(np.linalg.norm(q[3:7])-1.) > 1e-5:
            raise ValueError("invalid copied robot pose")
        self.data.qpos[:] = q
        mujoco.mj_kinematics(self.model, self.data)
        mujoco.mj_collision(self.model, self.data)
        contacts = []
        for c in self.data.contact:
            if not all(self.model.geom_bodyid[g] for g in (c.geom1, c.geom2)):
                continue
            depth = -float(c.dist)
            if not np.isfinite(depth):
                raise ValueError("nonfinite contact geometry")
            geoms = [{"body": self.model.body(int(self.model.geom_bodyid[g])).name,
                      "mesh": self.model.mesh(int(self.model.geom_dataid[g])).name,
                      "geom_id": int(g)} for g in (c.geom1, c.geom2)]
            contacts.append({"geometries": geoms, "penetration_m": depth})
        return contacts


def evaluate_self_contact(rows, probe, expected_frames=900):
    reasons = []
    maximum, first, bad_frames = 0., None, 0
    if len(rows) != expected_frames:
        reasons.append("incomplete_duration")
    for i, row in enumerate(rows):
        time = row.get("time_s")
        if not isinstance(time, (float, int)) or not np.isfinite(time) or abs(time-(i+1)*.02) > 1e-6:
            reasons.append("invalid_time_axis")
            break
        try:
            contacts = probe.sample(row.get("qpos"))
        except (ValueError, TypeError):
            reasons.append("invalid_pose_or_geometry")
            break
        depth = max((c["penetration_m"] for c in contacts), default=0.)
        maximum = max(maximum, depth)
        if depth > MAXIMUM_SELF_PENETRATION_M:
            bad_frames += 1
            if first is None:
                first = {"time_s": time, "contacts": contacts}
    if bad_frames:
        reasons.append("self_penetration_over_1mm")
    return {"passed": not reasons, "failures": sorted(set(reasons)), "frames": len(rows),
            "maximum_self_penetration_m": maximum, "violating_frames": bad_frames,
            "first_violation": first, "threshold_m": MAXIMUM_SELF_PENETRATION_M,
            "boundary": "Visible-development geometric rejection on a versioned complete CAD model. Not contact-force measurement, calibrated hardware clearance or standalone walking acceptance."}
