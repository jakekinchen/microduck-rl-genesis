"""Additive posture rejection; never modifies or relaxes the frozen motor gates."""
import numpy as np
from microduck.constants import DEFAULT_JOINT_POS,HEAD_JOINT_IDS
from experiments.walking.metrics import evaluate_case as evaluate_motor_case

POSTURE_LIMITS={"maximum_mean_joint_error_rad":.35,
                "p95_worst_joint_error_rad":float(np.pi/4),
                "mean_absolute_face_pitch_deg":30.}


def posture_metrics(rows):
    # Every case commands neutral head pose. Allow transient start, but score
    # both locomotion and stop. Do not average away one failed head joint.
    selected=[r for r in rows if r["time_s"]>=1.]
    if not selected:raise ValueError("no posture evidence")
    q=np.asarray([r["qpos"] for r in selected],float)
    face=np.asarray([r["face_world"] for r in selected],float)
    if q.shape!=(len(selected),21) or face.shape!=(len(selected),3) or not np.isfinite(np.r_[q.ravel(),face.ravel()]).all():
        raise ValueError("missing or nonfinite rigid-model head posture")
    if not np.allclose(np.linalg.norm(face,axis=1),1.,atol=1e-5):raise ValueError("invalid face vector")
    error=np.abs(q[:,7:][:,HEAD_JOINT_IDS]-np.asarray(DEFAULT_JOINT_POS)[list(HEAD_JOINT_IDS)])
    return {"maximum_mean_joint_error_rad":float(error.mean(0).max()),
            "p95_worst_joint_error_rad":float(np.percentile(error.max(1),95)),
            "mean_absolute_face_pitch_deg":float(np.degrees(np.arcsin(np.clip(np.abs(face[:,2]),0,1))).mean()),
            "per_head_joint_mean_abs_error_rad":error.mean(0).tolist()}


def evaluate_case(rows,case,suite):
    result=evaluate_motor_case(rows,case,suite)
    result["motor_battery_passed"]=result["passed"]
    metrics=posture_metrics(rows)
    failures=["posture_"+key for key,value in POSTURE_LIMITS.items() if metrics[key]>value]
    result["posture"]={"metrics":metrics,"thresholds":POSTURE_LIMITS,"passed":not failures,
                       "boundary":"Neutral-head visible-development requirement, not calibrated hardware limits."}
    result["failures"]=sorted(set(result["failures"]+failures))
    result["passed"]=not result["failures"]
    return result
