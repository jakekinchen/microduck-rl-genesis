"""Task-specific command tracking and stopping, composed with frozen gait checks."""
import numpy as np
from experiments.laser.gait import summarize_gait


def evaluate_case(rows,case,suite):
    gait=summarize_gait(rows)
    velocity=np.asarray([r["body_velocity_m_s"] for r in rows],float)
    yaw=np.asarray([r["yaw_rate_rad_s"] for r in rows],float)
    if velocity.shape!=(len(rows),3) or not np.isfinite(velocity).all() or not np.isfinite(yaw).all():
        raise ValueError("missing or nonfinite command-response telemetry")
    failures=list(gait["rejection_reasons"])
    if rows[-1]["time_s"]<suite["duration_s"]-1e-8:failures.append("incomplete_duration")
    moving=[r for r in rows if 2<=r["time_s"]<=suite["stop_start_s"]]
    stopping=[r for r in rows if r["time_s"]>=suite["duration_s"]-2]
    metrics={}
    torques=np.asarray([r["motor_torque_physics_nm"] for r in rows],float)
    if torques.shape!=(len(rows),4,14) or not np.isfinite(torques).all():raise ValueError("missing 200Hz torque evidence")
    torque_limit=suite["thresholds"]["motor_torque_limit_nm"]
    saturation=float(np.mean(np.abs(torques)>=.98*torque_limit))
    if np.max(np.abs(torques))>torque_limit+1e-6:failures.append("motor_torque_limit_exceeded")
    if saturation>suite["thresholds"]["torque_saturation_fraction_max"]:failures.append("persistent_torque_saturation")
    margins=np.asarray([r["minimum_actual_joint_margin_rad"] for r in rows],float)
    if not np.isfinite(margins).all():raise ValueError("missing actual joint margin")
    if margins.min()<suite["thresholds"]["actual_joint_margin_rad_min"]:failures.append("actual_joint_margin_below_minimum")
    if not moving or not stopping:
        failures.append("missing_tracking_or_stop_evidence")
    else:
        v=np.array([r["body_velocity_m_s"] for r in moving]);w=np.array([r["yaw_rate_rad_s"] for r in moving])
        if not np.isfinite(np.r_[v.ravel(),w]).all():raise ValueError("invalid body velocity")
        cmd=np.array(case["command"])
        metrics={"mean_abs_forward_error_m_s":float(np.abs(v[:,0]-cmd[0]).mean()),
                 "mean_abs_lateral_velocity_m_s":float(np.abs(v[:,1]).mean()),
                 "mean_abs_yaw_error_rad_s":float(np.abs(w-cmd[2]).mean()),
                 "stop_max_speed_m_s":max(r["speed_m_s"] for r in stopping),
                 "stop_max_yaw_rate_rad_s":max(abs(r["yaw_rate_rad_s"]) for r in stopping),
                 "stop_max_tilt_deg":max(r["tilt_deg"] for r in stopping)}
        metrics["torque_saturation_fraction"]=saturation
        metrics["minimum_actual_joint_margin_rad"]=float(margins.min())
        metrics["simultaneous_flight_fraction"]=float(np.mean([max(r["foot_normal_n"])<=1 for r in moving]))
        if abs(cmd[0])<.01:
            # Turning need not translate, but it must ACTUALLY turn with steps.
            # Backward *translation* is not the direction test for an in-place
            # turn: signed yaw tracking and bounded XY excursion are.
            failures=[f for f in failures if f not in ("no_useful_translation","unsustained_bilateral_stepping","backward_pursuit")]
            turning=[r for r in moving if abs(r["yaw_rate_rad_s"])>.15]
            coverage=[]
            for r in turning:
                coverage.append(all(any(e["foot"]==foot and r["time_s"]-1.5<=e["land_s"]<=r["time_s"] for e in gait["swing_events"]) for foot in (0,1)))
            metrics["turn_bilateral_step_coverage"]=float(np.mean(coverage)) if coverage else 0.
            if len(turning)*.02<1:failures.append("no_useful_turning")
            if metrics["turn_bilateral_step_coverage"]<suite["thresholds"]["minimum_bilateral_step_coverage"]:failures.append("unsustained_bilateral_turn_steps")
            xy=np.array([r["robot_xyz_m"][:2] for r in moving])
            metrics["turn_max_xy_excursion_m"]=float(np.linalg.norm(xy-np.array(rows[0]["robot_xyz_m"][:2]),axis=1).max())
        for key,value in metrics.items():
            if key in suite["thresholds"] and value>suite["thresholds"][key]:failures.append(key)
    return {"case_id":case["id"],"passed":not failures,"failures":sorted(set(failures)),"metrics":metrics,"gait":gait}
