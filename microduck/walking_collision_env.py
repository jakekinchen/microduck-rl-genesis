"""V11: V9 behavior with complete, contact-filter-consistent body geometry."""
from pathlib import Path
from .walking_viability_env import MicroduckViableWalkingEnv
from experiments.walking.collision_model import materialize


def assert_battery_contacts_enabled(robot, collider):
    def indices(body, mesh):
        return [g.idx for g in robot.geoms if g.link.name == body
                and Path(g.metadata.get("mesh_path", "")).stem == mesh]
    battery = indices("trunk_base", "np_f970")
    left = indices("leg", "leg")
    right = indices("leg_2", "leg")
    if any(len(v) != 1 for v in (battery, left, right)):
        raise ValueError("required battery/leg collider identity missing or ambiguous")
    pairs = {tuple(sorted(map(int, pair))) for pair in collider._valid_collision_pairs}
    for leg in (left, right):
        if tuple(sorted((battery[0], leg[0]))) not in pairs:
            raise ValueError("Genesis filtered a required battery/leg collision pair")


class MicroduckCompleteContactWalkingEnv(MicroduckViableWalkingEnv):
    def __init__(self, num_envs, *, model_directory, **kwargs):
        if any(key in kwargs for key in ("robot_xml", "max_collision_pairs")) or kwargs.get("backlash"):
            raise ValueError("v11 owns its non-backlash model and collision capacity")
        robot, _ = materialize(model_directory)
        super().__init__(num_envs, robot_xml=str(robot), max_collision_pairs=120, **kwargs)
        assert_battery_contacts_enabled(self.robot, self.scene.rigid_solver.collider)
        self.cfg.update(task="Walking-Complete-Body-Contacts-v11", walking_version="v11",
                        collision_model="full CAD plus restored support/leg contact mask",
                        genesis_mesh_processing="unchanged defaults",
                        inherited_behavior="v9 reward, action, observations, reset, command and timing unchanged")
