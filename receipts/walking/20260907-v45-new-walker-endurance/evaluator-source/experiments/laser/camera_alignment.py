"""Versioned render-camera correction; no kinematic/dynamic or sensor changes.

MuJoCo cameras look along local -Z and have image-up local +Y. The CAD
head-camera site declares physical forward +X, left +Y, up +Z. Bind that
mapping explicitly instead of assuming the camera XML was already correct.
"""
import mujoco
import numpy as np

CAMERA_REVISION="microduck.head-camera-site-aligned.v2"


def align_head_camera(model):
    camera=model.camera("head_camera").id
    site=model.site("head_camera").id
    if model.cam_bodyid[camera]!=model.site_bodyid[site]:
        raise ValueError("camera and physical site must share a body")
    site_rotation=np.zeros(9)
    mujoco.mju_quat2Mat(site_rotation,model.site_quat[site])
    # Columns: image-right=-siteY, image-up=siteZ, optical-back=-siteX.
    camera_in_site=np.array([[0,0,-1],[-1,0,0],[0,1,0]],dtype=float)
    rotation=site_rotation.reshape(3,3)@camera_in_site
    quat=np.zeros(4)
    mujoco.mju_mat2Quat(quat,rotation.reshape(-1))
    before=model.cam_quat[camera].copy()
    model.cam_quat[camera]=quat
    return {"revision":CAMERA_REVISION,"old_local_quaternion_wxyz":before.tolist(),
            "new_local_quaternion_wxyz":quat.tolist(),
            "physics_changed":False,"physical_calibration":False}
