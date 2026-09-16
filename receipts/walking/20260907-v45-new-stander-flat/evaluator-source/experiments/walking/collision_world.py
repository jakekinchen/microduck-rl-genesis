"""Explicit alternate-model native development world, not the old model lock."""
import mujoco
import numpy as np
from experiments.walking.sensor_world import ConsistentSensorWalkingWorld
from experiments.walking.collision_model import materialize, verify_physical_arrays
from experiments.laser.camera_alignment import align_head_camera


class CompleteContactWalkingWorld(ConsistentSensorWalkingWorld):
    def __init__(self, policy, bam_repo, *, model_directory, render=False, **kwargs):
        super().__init__(policy, bam_repo, render=False, **kwargs)
        c = self.core
        initial = c.data.qpos.copy()
        configured = {field: getattr(c.model, field).copy() for field in ("dof_armature", "dof_damping")}
        _, scene = materialize(model_directory)
        alternate = mujoco.MjModel.from_xml_path(str(scene))
        # Compare unconfigured arrays; the core has already installed BAM.
        from experiments.walking.collision_model import ASSETS
        reference = mujoco.MjModel.from_xml_path(str(ASSETS/"scene_walk.xml"))
        verify_physical_arrays(reference, alternate)
        c.model = alternate
        c.data = mujoco.MjData(alternate)
        c._validate_model()
        c._configure_torque_actuators()
        c.controller = c._build_bam_controller(bam_repo)
        for field, expected in configured.items():
            if not np.array_equal(getattr(c.model, field), expected):
                raise ValueError(f"complete model changes BAM-configured {field}")
        align_head_camera(c.model)
        c.reset(initial[:3], initial[3:7])
        self.sensor_data = mujoco.MjData(c.model)
        c.model.vis.quality.offsamples = 1
        c.model.vis.global_.offwidth = 720
        c.model.vis.global_.offheight = 480
        self.renderer = mujoco.Renderer(c.model, height=480, width=720) if render else None
        self.model_scope = {"variant": "complete-contact-v11", "scene": str(scene),
                            "old_reduced_model_acceptance": False,
                            "physical_transfer_validated": False}
