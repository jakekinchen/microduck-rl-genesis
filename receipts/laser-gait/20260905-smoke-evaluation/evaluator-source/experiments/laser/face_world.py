"""Explicit command intervention, not an action or simulator modification."""
from .world import LaserWorld
from microduck.laser_face_command import face_first_command
from microduck.laser_task import world_to_body_xy


class FaceFirstLaserWorld(LaserWorld):
    def command_for(self, target, visible):
        c = self.core
        return face_first_command(world_to_body_xy(target, c.data.qpos[:2], c.data.qpos[3:7]), visible)
