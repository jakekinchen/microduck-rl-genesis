"""Full-horizon heading and local tracking checks, using unchanged tolerances."""
import numpy as np
from experiments.walking.heading import THRESHOLDS
from experiments.walking.posture import posture_metrics, POSTURE_LIMITS


def evaluate_endurance(rows, window, thresholds):
    failures, buckets = [], []
    duration = window["duration_s"]
    selected = [r for r in rows if 2-1e-9 <= r["time_s"] <= window["stop_start_s"]+1e-9]
    heading = {}
    if len(rows) != round(duration*50) or len(selected) != round((window["stop_start_s"]-2)*50)+1:
        failures.append("incomplete_endurance_evidence")
    else:
        q=np.array([r["qpos"][3:7] for r in selected])
        w,x,y,z=q.T
        measured=np.unwrap(np.arctan2(2*(x*y+w*z),1-2*(y*y+z*z)))
        command=np.array([r["command"] for r in selected])
        if not np.isfinite(np.r_[q.ravel(),command.ravel()]).all() or not np.allclose(np.linalg.norm(q,axis=1),1.,atol=1e-5):
            raise ValueError("invalid endurance heading telemetry")
        target=np.r_[0.,np.cumsum(command[:-1,2]*.02)]
        error=np.degrees(measured-measured[0]-target)
        heading={"endpoint_heading_error_deg":float(abs(error[-1])),"maximum_heading_error_deg":float(abs(error).max())}
        failures += ["full_horizon_"+key for key,value in heading.items() if value>THRESHOLDS[key]]
        for start in np.arange(2,window["stop_start_s"],30):
            end=min(start+30,window["stop_start_s"])
            block=[r for r in selected if start <= r["time_s"] < end]
            if len(block) != round((end-start)*50):
                failures.append("missing_tracking_bucket")
                continue
            v=np.array([r["body_velocity_m_s"] for r in block])
            yaw=np.array([r["yaw_rate_rad_s"] for r in block])
            metrics={"mean_abs_forward_error_m_s":float(abs(v[:,0]-window["command"][0]).mean()),
                     "mean_abs_yaw_error_rad_s":float(abs(yaw-window["command"][2]).mean()),
                     "mean_abs_lateral_velocity_m_s":float(abs(v[:,1]).mean())}
            bad=[key for key,value in metrics.items() if not np.isfinite(value) or value>thresholds[key]]
            buckets.append({"start_s":float(start),"end_s":float(end),"metrics":metrics,"failures":bad,"passed":not bad})
            failures += [f"tracking_bucket_{start:g}:"+key for key in bad]
    stopping=[r for r in rows if r["time_s"]>=duration-2]
    posture={}
    if len(stopping)!=101:
        failures.append("missing_final_standing_posture")
    else:
        posture=posture_metrics(stopping)
        failures += ["final_standing_"+key for key,limit in POSTURE_LIMITS.items() if posture[key]>limit]
    return {"passed":not failures,"failures":failures,"full_horizon_heading":heading,
            "heading_thresholds":THRESHOLDS,"tracking_buckets":buckets,"final_standing_posture":posture}
