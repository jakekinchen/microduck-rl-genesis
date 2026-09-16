"""Public-informed contact hypotheses. These are not calibrated carpets."""
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np

PROFILES = (
    {"id":"rigid-control", "friction":1., "timeconst_s":.02},
    {"id":"soft-low-traction", "friction":.51, "timeconst_s":.035},
    {"id":"soft-middle", "friction":1., "timeconst_s":.05},
    {"id":"soft-high-traction", "friction":1.8, "timeconst_s":.07},
)
FOOT_FRICTION = .1
SOLIMP = [.9, .95, .001, .5, 2.]


def ground_solref(profile):
    # Equal solmix averaging with the unchanged .02 s foot; both engines.
    return [2*profile["timeconst_s"]-.02, 1.]


def training_panels(path):
    root = ET.Element("mujoco", model="public-contact-panels-v25")
    world = ET.SubElement(root, "worldbody")
    for i,p in enumerate(PROFILES):
        ET.SubElement(world, "geom", name=f"surface_{i}", type="box",
                      pos=f"0 {16*i} -.05", size="8 8 .05",
                      contype="1", conaffinity="1", friction=f'{p["friction"]} .005 .0001',
                      solref=" ".join(map(str,ground_solref(p))),
                      solimp=" ".join(map(str,SOLIMP)))
    ET.indent(root)
    content=ET.tostring(root,encoding="unicode")+"\n"
    path=Path(path)
    if path.exists():
        if path.read_text()!=content: raise ValueError("surface panel model drift")
    else:
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(content)
    return path


def configure_native(model, profile):
    ground=[i for i in range(model.ngeom) if model.geom_bodyid[i]==0 and
            (model.geom_contype[i] or model.geom_conaffinity[i])]
    for i in ground:
        model.geom_friction[i]=[profile["friction"],.005,.0001]
        model.geom_solref[i]=ground_solref(profile)
    for name in ("left_foot_collision","right_foot_collision"):
        model.geom_friction[model.geom(name).id,0]=FOOT_FRICTION
    return {"profile":dict(profile),"ground_ids":ground,
            "geom_solref":model.geom_solref.tolist(),"geom_friction":model.geom_friction.tolist(),
            "measurement_calibrated":False}


def verify_contacts(model,data):
    for c in data.contact:
        a,b=int(c.geom1),int(c.geom2)
        expected=max(model.geom_friction[a,0],model.geom_friction[b,0])
        np.testing.assert_allclose(c.friction[0],expected,rtol=0,atol=1e-8)
        np.testing.assert_allclose(c.solref,(model.geom_solref[a]+model.geom_solref[b])/2,rtol=0,atol=1e-8)


from experiments.walking.terrain_v23 import TerrainWorld
from experiments.walking.filtered_heading_world import FilteredHeadingWalkingWorld
from microduck.persistent_heading_servo_v24 import PersistentHeadingServo


class PublicSurfaceWorld(TerrainWorld):
    def __init__(self,*args,profile,**kwargs):
        super().__init__(*args,**kwargs)
        self.materialized_surface=configure_native(self.core.model,profile)
        self.expected_surface_arrays={key:getattr(self.core.model,key).copy() for key in
            ('geom_friction','geom_solref','body_mass','body_inertia')}
        self.heading_servo=PersistentHeadingServo()

    def step_command(self,command,action_override=None):
        # V23 assumes uniform unit/scaled friction, so retain its ground-relative
        # fall rule while auditing the actual per-pair surface law here.
        row=FilteredHeadingWalkingWorld.step_command(self,command,action_override)
        c=self.core
        for key,value in self.expected_surface_arrays.items():
            np.testing.assert_array_equal(getattr(c.model,key),value)
        verify_contacts(c.model,c.data)
        height=float(self.ground.height([c.data.qpos[:2]])[0])
        clearance=float(c.data.qpos[2]-height)
        self.fell=bool(clearance<.07 or row['tilt_deg']>70)
        row.update(fell=self.fell,ground_height_at_base_m=height,base_clearance_m=clearance,
                   surface_profile=self.materialized_surface['profile'],
                   observed_contacts=[{'geom1':int(cn.geom1),'geom2':int(cn.geom2),
                       'solref':cn.solref.tolist(),'friction':cn.friction.tolist(),
                       'penetration_m':max(0.,float(-cn.dist))} for cn in c.data.contact])
        return row
