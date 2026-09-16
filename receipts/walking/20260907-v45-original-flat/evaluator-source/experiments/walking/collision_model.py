"""Versioned complete-contact model; frozen original models remain untouched.

The bundled allcollisions robot already contains battery/hip/head/sole CAD.
Its power-support mask is self-only bit 2 while leg masks are bit 1, silently
removing the reduced model's support/leg contacts. V11 makes that support use
the same bit 1 as every other collider. No mass, frame, joint or visual edits.
"""
from pathlib import Path
import os
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "microduck/assets/microduck"


def model_documents(destination):
    destination = Path(destination).resolve()
    robot = ET.parse(ASSETS / "robot_allcollisions.xml").getroot()
    support = robot.find("./default/default[@class='self_collision_only']/geom")
    if support is None or support.get("contype") != "2" or support.get("conaffinity") != "2":
        raise ValueError("unexpected source self-collision mask")
    support.set("contype", "1")
    support.set("conaffinity", "1")
    robot.find("compiler").set("meshdir", os.path.relpath(ASSETS / "assets", destination))
    scene = ET.parse(ASSETS / "scene.xml").getroot()
    include = scene.find("include")
    if include is None or include.get("file") != "robot_allcollisions.xml":
        raise ValueError("unexpected source scene include")
    include.set("file", "robot.xml")
    result = {}
    for name, root in (("robot.xml", robot), ("scene.xml", scene)):
        ET.indent(root)
        result[name] = ET.tostring(root, encoding="unicode") + "\n"
    return result


def materialize(destination):
    destination = Path(destination).resolve()
    documents = model_documents(destination)
    # Check every preexisting file before writing any output; never rewrite a
    # previously materialized model after source drift.
    for name, content in documents.items():
        target = destination / name
        if target.is_symlink() or (target.exists() and target.read_text() != content):
            raise ValueError(f"existing model differs: {target}")
    destination.mkdir(parents=True, exist_ok=True)
    for name, content in documents.items():
        target = destination / name
        if not target.exists():
            with target.open("x") as output:
                output.write(content)
    return destination / "robot.xml", destination / "scene.xml"


def verify_physical_arrays(reference, candidate):
    import numpy as np
    fields = ("jnt_qposadr", "jnt_range", "jnt_axis", "jnt_pos", "body_mass",
              "body_inertia", "body_ipos", "body_iquat", "body_pos", "body_quat",
              "dof_damping", "dof_armature", "dof_frictionloss")
    for field in fields:
        if not np.array_equal(getattr(reference, field), getattr(candidate, field)):
            raise ValueError(f"collision-only model changes {field}")
    if [reference.joint(i).name for i in range(reference.njnt)] != [candidate.joint(i).name for i in range(candidate.njnt)]:
        raise ValueError("collision model changes joint order")
    return fields
