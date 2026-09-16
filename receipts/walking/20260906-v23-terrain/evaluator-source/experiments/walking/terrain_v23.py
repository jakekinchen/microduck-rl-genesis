"""Versioned static terrain and surface-relative diagnostics for the frozen pair."""
import hashlib
import math
from pathlib import Path
import xml.etree.ElementTree as ET
import mujoco
import numpy as np
from experiments.walking.collision_model import model_documents, verify_physical_arrays
from experiments.walking.physical_domain import nominal_arrays, apply_domain, FIELDS
from experiments.walking.filtered_heading_world import FilteredHeadingWalkingWorld
from experiments.laser.gait import GaitProbe
from experiments.laser.camera_alignment import align_head_camera


def materialize_terrain(destination, terrain):
    destination = Path(destination)
    docs = model_documents(destination)
    scene = ET.fromstring(docs["scene.xml"])
    body = scene.find("worldbody")
    floor = body.find("geom[@name='floor']")
    kind = terrain["kind"]
    if kind == "slope":
        angle = math.radians(terrain["degrees"])/2
        axis = terrain["axis"]
        if axis not in ("x", "y") or abs(terrain["degrees"]) != 3:
            raise ValueError("unregistered slope")
        floor.set("quat", f"{math.cos(angle)} {math.sin(angle) if axis == 'x' else 0} {math.sin(angle) if axis == 'y' else 0} 0")
    elif kind in ("seams", "tiles"):
        boxes = []
        if kind == "seams":
            boxes = [(x, 0., .03, 2., .003) for x in np.arange(.35, 4., .3)]
        else:
            rng = np.random.default_rng(terrain["layout_seed"])
            for x in np.arange(.32, 4., .16):
                for y in np.arange(-1.12, 1.13, .16):
                    height = float(rng.choice([.002, .004, .006]))
                    boxes.append((float(x), float(y), .16, .16, height))
        for i, (x, y, width, depth, height) in enumerate(boxes):
            ET.SubElement(body, "geom", name=f"terrain_{i}", type="box",
                          pos=f"{x} {y} {height/2}", size=f"{width/2} {depth/2} {height/2}",
                          contype="1", conaffinity="1", friction="1 .005 .0001",
                          rgba=".45 .49 .38 1")
    elif kind != "flat":
        raise ValueError("unregistered terrain")
    ET.indent(scene)
    docs["scene.xml"] = ET.tostring(scene, encoding="unicode") + "\n"
    destination.mkdir(parents=True, exist_ok=True)
    for name, content in docs.items():
        path = destination/name
        if path.exists():
            if path.read_text() != content:
                raise ValueError(f"terrain model drift: {path}")
        else:
            with path.open("x") as f:
                f.write(content)
    return destination/"scene.xml"


class Ground:
    """Query the compiled primitive collision geometry, not the requested recipe."""
    def __init__(self, model):
        self.ids = [i for i in range(model.ngeom) if model.geom_bodyid[i] == 0
                    and (model.geom_contype[i] or model.geom_conaffinity[i])]
        self.planes, self.boxes = [], []
        for i in self.ids:
            if not model.geom_contype[i] & 1 or not model.geom_conaffinity[i] & 1:
                raise ValueError("ground collision masks disabled")
            rotation = np.zeros(9)
            mujoco.mju_quat2Mat(rotation, model.geom_quat[i])
            if model.geom_type[i] == mujoco.mjtGeom.mjGEOM_PLANE:
                self.planes.append((model.geom_pos[i].copy(), rotation.reshape(3,3)[:,2]))
            elif model.geom_type[i] == mujoco.mjtGeom.mjGEOM_BOX:
                np.testing.assert_allclose(rotation.reshape(3,3), np.eye(3), atol=1e-12)
                self.boxes.append((model.geom_pos[i].copy(), model.geom_size[i].copy()))
            else:
                raise ValueError("ground query does not support this collision geometry")
        if len(self.planes) != 1:
            raise ValueError("one supporting plane required")
        self.box_pos = np.array([p for p,s in self.boxes]).reshape(-1,3)
        self.box_size = np.array([s for p,s in self.boxes]).reshape(-1,3)

    def height(self, xy):
        xy = np.asarray(xy, float).reshape(-1,2)
        p, n = self.planes[0]
        height = p[2] - ((xy-p[:2]) @ n[:2])/n[2]
        if len(self.boxes):
            within = (np.abs(xy[:,None,:]-self.box_pos[None,:,:2]) <= self.box_size[None,:,:2]+1e-12).all(2)
            height = np.maximum(height, np.where(within, self.box_pos[:,2]+self.box_size[:,2], -np.inf).max(1))
        return height

    def clearance(self, vertices):
        value = float((vertices[:,2]-self.height(vertices[:,:2])).min())
        if len(self.boxes):
            low, high = vertices[:,:2].min(0), vertices[:,:2].max(0)
            overlap = ((self.box_pos[:,:2]+self.box_size[:,:2] >= low) &
                       (self.box_pos[:,:2]-self.box_size[:,:2] <= high)).all(1)
            if overlap.any():
                # Conservative footprint bound also catches a narrow seam under
                # the middle of the sole, between mesh vertices. May undercount
                # swings; cannot inflate clearance by ignoring that seam.
                value = min(value, float(vertices[:,2].min() -
                    (self.box_pos[overlap,2]+self.box_size[overlap,2]).max()))
        return value


class TerrainWorld(FilteredHeadingWalkingWorld):
    def __init__(self, *args, terrain_scene, domain, **kwargs):
        render = kwargs.pop("render", False)
        super().__init__(*args, render=False, **kwargs)
        c = self.core
        initial = c.data.qpos.copy()
        expected = {key: getattr(c.model,key).copy() for key in ("dof_armature", "dof_damping")}
        candidate = mujoco.MjModel.from_xml_path(str(terrain_scene))
        nominal = mujoco.MjModel.from_xml_path(str(Path(kwargs["model_directory"])/"scene.xml"))
        verify_physical_arrays(nominal, candidate)
        c.model, c.data = candidate, mujoco.MjData(candidate)
        c._validate_model()
        c._configure_torque_actuators()
        c.controller = c._build_bam_controller(args[1])
        for key, value in expected.items():
            np.testing.assert_array_equal(getattr(c.model,key), value)
        align_head_camera(c.model)
        self.materialized_domain = apply_domain(c.model, nominal_arrays(c.model), domain)
        self.expected_physics = {key: getattr(c.model,key).copy() for key in FIELDS}
        mujoco.mj_setConst(c.model,c.data)
        c.reset(initial[:3],initial[3:7])
        np.testing.assert_array_equal(c.data.qpos, initial)
        self.sensor_data = mujoco.MjData(c.model)
        self.ground = Ground(c.model)
        c.model.vis.quality.offsamples = 1
        c.model.vis.global_.offwidth, c.model.vis.global_.offheight = 720, 480
        self.renderer = mujoco.Renderer(c.model, height=480, width=720) if render else None
        self.materialized_terrain = {"geometry_ids": self.ground.ids,
            "geometry_names": [c.model.geom(i).name for i in self.ground.ids],
            "arrays": {key: getattr(c.model,key)[self.ground.ids].tolist() for key in
                       ("geom_type", "geom_pos", "geom_quat", "geom_size", "geom_contype", "geom_conaffinity")},
            "scene_sha256": hashlib.sha256(Path(terrain_scene).read_bytes()).hexdigest()}

    def step_command(self, command, action_override=None):
        row = super().step_command(command, action_override)
        c = self.core
        for key, value in self.expected_physics.items():
            np.testing.assert_array_equal(getattr(c.model,key),value)
        ground = float(self.ground.height([c.data.qpos[:2]])[0])
        clearance = float(c.data.qpos[2]-ground)
        # Same fall limits, expressed relative to the actual supporting surface.
        self.fell = bool(clearance < .07 or row["tilt_deg"] > 70)
        row.update(fell=self.fell, ground_height_at_base_m=ground, base_clearance_m=clearance)
        row["observed_contact_sliding_friction"] = [float(cn.friction[0]) for cn in c.data.contact]
        np.testing.assert_allclose(row["observed_contact_sliding_friction"],
                                   self.materialized_domain["factors"]["sliding_friction_scale"], atol=1e-12, rtol=0)
        return row


class TerrainGaitProbe(GaitProbe):
    def __init__(self, core):
        super().__init__(core)
        self.ground = Ground(core.model)

    def sample(self, row):
        row = super().sample(row)
        m, d = self.core.model, self.data
        load, speed_load = np.zeros(2), np.zeros(2)
        nonfoot, contacts = [], []
        for i, contact in enumerate(d.contact):
            a,b = int(contact.geom1),int(contact.geom2)
            if a not in self.ground.ids and b not in self.ground.ids:
                continue
            ground, geom = (a,b) if a in self.ground.ids else (b,a)
            force = np.zeros(6)
            mujoco.mj_contactForce(m,d,i,force)
            normal = max(0.,float(force[0]))
            contacts.append({"ground":m.geom(ground).name,"normal_n":normal})
            if geom not in self.feet:
                if normal > .1:
                    nonfoot.append({"body":m.body(m.geom_bodyid[geom]).name,"normal_n":normal})
                continue
            foot = self.feet.index(geom)
            jac = np.zeros((3,m.nv))
            mujoco.mj_jac(m,d,jac,None,contact.pos,int(m.geom_bodyid[geom]))
            tangent = contact.frame.reshape(3,3)[1:] @ (jac@d.qvel)
            load[foot] += normal
            speed_load[foot] += normal*np.linalg.norm(tangent)
        clearance=[]
        for geom, vertices in zip(self.feet,self.vertices):
            world=vertices@d.geom_xmat[geom].reshape(3,3).T+d.geom_xpos[geom]
            clearance.append(self.ground.clearance(world))
        row.update(foot_normal_n=load.tolist(), nonfoot_ground_contacts=nonfoot,
                   loaded_contact_slip_m_s=np.divide(speed_load,load,out=np.zeros(2),where=load>0).tolist(),
                   sole_clearance_m=clearance, terrain_contacts=contacts,
                   clearance_frame="vertical distance to compiled terrain surface")
        return row
