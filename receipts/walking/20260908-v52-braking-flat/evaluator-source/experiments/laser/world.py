"""Shared live/demo/test MuJoCo world. No joint-action assistance or auto reset."""
from collections import deque
from pathlib import Path

import mujoco
import numpy as np

from evaluator.core import EvaluatorCore, projected_gravity
from microduck.laser_task import world_to_body_xy
from microduck.laser_steering import approach_command
from microduck.constants import TRUNK_BODY


class LaserWorld:
    def __init__(self, policy, bam_repo, domain, render=False):
        self.core = core = EvaluatorCore(Path(policy), Path(bam_repo), "microduck.walking.v1")
        self.domain = domain
        self.rng = np.random.default_rng(domain["seed"])
        model, data = core.model, core.data
        model.geom_friction[:, 0] *= domain["friction_ratio"]
        trunk = model.body(TRUNK_BODY).id
        model.body_mass[trunk] *= domain["trunk_mass_ratio"]
        model.body_inertia[trunk] *= domain["trunk_mass_ratio"]
        model.body_ipos[trunk] += domain["trunk_com_shift_m"]
        core.controller.model.actuator.kp *= domain["motor_kp_ratio"]
        palettes = [([.13, .23, .32], [.24, .39, .49]),
                    ([.42, .39, .33], [.59, .56, .48]),
                    ([.20, .29, .26], [.37, .46, .40])]
        # Visual variation is recorded but not called perceptual robustness.
        for i in range(model.ntex):
            if model.tex_type[i] == mujoco.mjtTexture.mjTEXTURE_2D:
                start, end = model.tex_adr[i], model.tex_adr[i]+model.tex_height[i]*model.tex_width[i]*model.tex_nchannel[i]
                tex = model.tex_data[start:end].reshape(-1, model.tex_nchannel[i])
                choose = tex[:, :3].mean(1) > tex[:, :3].mean()
                a, b = palettes[domain["visual_palette"]]
                tex[:, :3] = np.where(choose[:, None], np.array(a)*255, np.array(b)*255).astype(np.uint8)
        mujoco.mj_setConst(model, data)
        core.reset([0., 0., .125], [1., 0., 0., 0.])
        self.last_action = np.zeros(14, np.float32)
        self.sensor_history = deque(maxlen=3)
        self.steps, self.fell, self.pushed = 0, False, False
        self.robot_trail, self.target_trail = deque(maxlen=400), deque(maxlen=400)
        model.vis.quality.offsamples = 1
        model.vis.global_.offwidth = 720
        model.vis.global_.offheight = 480
        self.renderer = mujoco.Renderer(model, height=480, width=720) if render else None
        self.camera = mujoco.MjvCamera()
        self.camera.lookat[:] = [0.15, .05, .10]
        self.camera.distance, self.camera.azimuth, self.camera.elevation = 1.8, 130., -43.
        self.latest = None

    def step(self, target, visible=True):
        if self.fell:
            raise RuntimeError("world fell; explicit reset required")
        core, domain = self.core, self.domain
        target = np.asarray(target, float)
        if target.shape != (2,) or not np.isfinite(target).all() or np.max(np.abs(target)) > 3:
            raise ValueError("target must be finite XY within 3 metres")
        t = self.steps*.02
        if not self.pushed and t >= domain["push_at_s"]:
            core.data.qvel[:2] += domain["push_delta_v_m_s"]
            self.pushed = True
        command = self.command_for(target, visible)
        observation = core.observation_vector(self.last_action, command, np.zeros(4), np.zeros(6))
        self.sensor_history.append(observation.copy())
        lag = min(domain["sensor_delay_steps"], len(self.sensor_history)-1)
        delayed = self.sensor_history[-1-lag]
        observation[:, :6], observation[:, 20:34] = delayed[:, :6], delayed[:, 20:34]
        observation[:, 6:20] += np.array(domain["encoder_bias_rad"])
        if domain["sensor_noise"]:
            observation[:, :3] += self.rng.uniform(-.03, .03, (1, 3))
            observation[:, 3:6] += self.rng.uniform(-.006, .006, (1, 3))
            observation[:, 20:34] += self.rng.uniform(-.25, .25, (1, 14))
        self.last_observation = observation.copy()
        action, latency = core.policy.infer(observation)
        if action.shape != (1, 14) or not np.isfinite(action).all():
            raise ValueError("invalid policy action; physics not advanced")
        self.last_action = action[0].copy()
        for i, name in enumerate(core.joint_names):
            core.controller.set_q_target(name, float(core.home[i]+self.last_action[i]))
        for _ in range(4):
            core.controller.update()
            mujoco.mj_step(core.model, core.data)
        if not np.isfinite(np.r_[core.data.qpos, core.data.qvel, core.data.ctrl]).all():
            raise ValueError("nonfinite physics state")
        tilt = float(np.degrees(np.arccos(np.clip(-projected_gravity(core.data.qpos[3:7])[2], -1, 1))))
        self.fell = bool(core.data.qpos[2] < .07 or tilt > 70)
        self.steps += 1
        self.robot_trail.append(core.data.qpos[:3].copy())
        self.target_trail.append(np.r_[target, .009])
        self.latest = {"time_s": self.steps*.02, "robot_xyz_m": core.data.qpos[:3].tolist(),
                       "robot_yaw_rad": float(np.arctan2(2*(core.data.qpos[3]*core.data.qpos[6]+core.data.qpos[4]*core.data.qpos[5]), 1-2*(core.data.qpos[5]**2+core.data.qpos[6]**2))),
                       "target_xy_m": target.tolist(), "visible": bool(visible), "command": command.tolist(),
                       "action_rad": self.last_action.tolist(), "distance_m": float(np.linalg.norm(target-core.data.qpos[:2])),
                       "speed_m_s": float(np.linalg.norm(core.data.qvel[:2])), "tilt_deg": tilt,
                       "fell": self.fell, "latency_ms": latency}
        return self.latest

    def command_for(self, target, visible):
        core = self.core
        return approach_command(world_to_body_xy(target, core.data.qpos[:2], core.data.qpos[3:7]), visible, 3.)

    def frame(self, target, visible=True, view="activity"):
        # Camera framing follows the activity; robot and target physics are untouched.
        robot_xy = self.core.data.qpos[:2]
        if view == "inspection":
            self.camera.lookat[:] = [robot_xy[0], robot_xy[1], .12]
            self.camera.distance, self.camera.azimuth, self.camera.elevation = .65, 90., -15.
        elif view == "fixed":
            self.camera.lookat[:] = [0., 0., .1]
            self.camera.distance, self.camera.azimuth, self.camera.elevation = 2.4, 130., -43.
        elif view == "activity":
            self.camera.lookat[:] = [*((robot_xy+np.asarray(target))/2), .10]
            self.camera.distance = max(1.25, .8+1.5*np.linalg.norm(robot_xy-target))
            self.camera.azimuth, self.camera.elevation = 130., -43.
        else:
            raise ValueError("unknown camera view")
        self.renderer.update_scene(self.core.data, camera=self.camera)
        scene = self.renderer.scene
        def dot(position, radius, color):
            if scene.ngeom >= scene.maxgeom:
                return
            geom = scene.geoms[scene.ngeom]
            mujoco.mjv_initGeom(geom, mujoco.mjtGeom.mjGEOM_SPHERE, np.array([radius]*3),
                               np.asarray(position), np.eye(3).reshape(-1), np.array(color))
            geom.emission = .7
            scene.ngeom += 1
        for p in list(self.robot_trail)[::8]:
            dot([p[0], p[1], .008], .005, [.9, .75, .12, .7])
        for p in list(self.target_trail)[::12]:
            dot(p, .003, [.8, .2, .18, .3])
        if visible:
            dot(np.r_[target, .012], .014, [1., .02, .02, 1.])
        return self.renderer.render().copy()

    def close(self):
        if self.renderer:
            self.renderer.close()
