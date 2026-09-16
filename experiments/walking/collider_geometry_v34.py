"""Audit actual imported hulls and runtime mass at a copied comparison pose."""
from pathlib import Path
import mujoco
import numpy as np


def audit_geometry(env):
    model=mujoco.MjModel.from_xml_path(str(env.robot_xml))
    data=mujoco.MjData(model)
    data.qpos[:7]=np.r_[env.robot.get_pos()[0].cpu(),env.robot.get_quat()[0].cpu()]
    for i,name in enumerate(env.joint_names if hasattr(env,'joint_names') else __import__('microduck.constants',fromlist=['JOINT_NAMES']).JOINT_NAMES):
        data.qpos[model.jnt_qposadr[model.joint(name).id]]=float(env.dof_pos[0,i])
    mujoco.mj_forward(model,data)  # Separate copied-pose audit data only.
    actual_mass=env.robot.get_links_inertial_mass().cpu().numpy().reshape(-1)
    for i,link in enumerate(env.robot.links):
        np.testing.assert_allclose(actual_mass[i],model.body_mass[model.body(link.name).id],rtol=1e-5,atol=1e-8)
    directions=np.r_[np.eye(3),-np.eye(3),np.random.default_rng(26090633).normal(size=(2048,3))]
    directions/=np.linalg.norm(directions,axis=1,keepdims=True)
    rows=[]
    for g in env.robot.geoms:
        if not g.contype:continue
        stem=Path(g.metadata.get('mesh_path','')).stem
        matches=[i for i in range(model.ngeom) if model.geom_contype[i] and model.geom_bodyid[i]>0
                 and model.mesh(model.geom_dataid[i]).name==stem and model.body(model.geom_bodyid[i]).name==g.link.name]
        if len(matches)!=1:raise ValueError((g.link.name,stem,matches))
        geom=matches[0];mesh=model.geom_dataid[geom]
        vertices=model.mesh_vert[model.mesh_vertadr[mesh]:model.mesh_vertadr[mesh]+model.mesh_vertnum[mesh]]
        native=vertices@data.geom_xmat[geom].reshape(3,3).T+data.geom_xpos[geom]
        actual=g.get_verts()[0].cpu().numpy()
        error=np.abs((native@directions.T).max(0)-(actual@directions.T).max(0))
        rows.append(dict(body=g.link.name,mesh=stem,native_vertices=len(native),genesis_vertices=len(actual),
            max_support_difference_m=float(error.max()),axis_difference_m=error[:6].tolist(),runtime_mass_matches=True))
    return rows
