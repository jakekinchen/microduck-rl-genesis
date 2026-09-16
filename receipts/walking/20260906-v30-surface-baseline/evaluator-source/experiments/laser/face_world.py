"""Explicit command intervention, not an action or simulator modification."""
from .world import LaserWorld
from microduck.laser_face_command import face_first_command
from microduck.laser_task import world_to_body_xy
from .camera_alignment import align_head_camera
import mujoco


class FaceFirstLaserWorld(LaserWorld):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.camera_revision=align_head_camera(self.core.model)
        mujoco.mj_forward(self.core.model,self.core.data)

    def command_for(self, target, visible):
        c = self.core
        return face_first_command(world_to_body_xy(target, c.data.qpos[:2], c.data.qpos[3:7]), visible)
