"""Read-only compiled HOME geometry/inertial audit, no learned-policy execution."""
import argparse
import json
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False)
    import genesis as gs
    import mujoco
    import numpy as np
    import torch
    from microduck.walking_ground_env import MicroduckGroundAlignedWalkingEnv as MicroduckVelocityEnv
    from microduck.constants import MICRODUCK_WALK_XML,JOINT_NAMES,DEFAULT_JOINT_POS
    from microduck.walking_env import sole_vertices
    from scripts.evaluate_laser import digest
    torch.set_num_threads(1);gs.init(backend=gs.cpu,logging_level="warning",seed=76530)
    env=MicroduckVelocityEnv(1,demo=True)
    env.reset();env.place([0,0,.125],yaw=0.)
    m=mujoco.MjModel.from_xml_path(str(ROOT/"microduck/assets/microduck/scene_walk.xml"));d=mujoco.MjData(m)
    d.qpos[:7]=[0,0,.125,1,0,0,0]
    for name,value in zip(JOINT_NAMES,DEFAULT_JOINT_POS):d.qpos[m.jnt_qposadr[m.joint(name).id]]=value
    mujoco.mj_forward(m,d)
    positions=env.robot.get_links_pos()[0].cpu().numpy()
    quats=env.robot.get_links_quat()[0].cpu().numpy()
    rows=[]
    for i,link in enumerate(env.robot.links):
        try:b=m.body(link.name).id
        except KeyError:continue
        rot=np.zeros(9);mujoco.mju_quat2Mat(rot,quats[i].astype(float));rot=rot.reshape(3,3)
        ip=np.asarray(link.inertial_pos);iq=np.asarray(link.inertial_quat)
        ir=np.zeros(9);mujoco.mju_quat2Mat(ir,iq.astype(float));ir=ir.reshape(3,3)
        local_inertia=ir@np.asarray(link.inertial_i)@ir.T
        mr=np.zeros(9);mujoco.mju_quat2Mat(mr,m.body_iquat[b]);mr=mr.reshape(3,3)
        reference=mr@np.diag(m.body_inertia[b])@mr.T
        rows.append({"body":link.name,"link_position_error_m":float(np.max(np.abs(positions[i]-d.xpos[b]))),
            "link_rotation_matrix_error":float(np.max(np.abs(rot-d.xmat[b].reshape(3,3)))),
            "local_com_error_m":float(np.max(np.abs(ip-m.body_ipos[b]))),
            "mass_error_kg":float(abs(link.inertial_mass-m.body_mass[b])),
            "local_inertia_tensor_error_kg_m2":float(np.max(np.abs(local_inertia-reference)))})
    geoms=[{"link":g.link.name,"contype":g.contype,"conaffinity":g.conaffinity,
            "friction":float(g.friction)} for g in env.robot.geoms if g.contype or g.conaffinity]
    floor=[{"contype":g.contype,"conaffinity":g.conaffinity,"friction":float(g.friction)} for g in env.ground.geoms]
    vertices=sole_vertices(MICRODUCK_WALK_XML);soles=[]
    for i,side in enumerate(("left","right")):
        link=env.foot_link_idx[i];rot=np.zeros(9);mujoco.mju_quat2Mat(rot,quats[link].astype(float))
        actual=float((vertices[i]@rot.reshape(3,3).T+positions[link])[:,2].min())
        g=m.geom(f"{side}_foot_collision").id;mesh=m.geom_dataid[g]
        vs=m.mesh_vert[m.mesh_vertadr[mesh]:m.mesh_vertadr[mesh]+m.mesh_vertnum[mesh]]
        reference=float((vs@d.geom_xmat[g].reshape(3,3).T+d.geom_xpos[g])[:,2].min())
        soles.append({"foot":side,"genesis_home_sole_min_m":actual,"mujoco_home_sole_min_m":reference,"error_m":abs(actual-reference)})
    report={"schema":"microduck.compiled-home-frame-audit/v1","links":rows,"collision_geometries":geoms,
            "genesis_floor":floor,"mujoco_floor":{"contype":int(m.geom("floor").contype[0]),
                "conaffinity":int(m.geom("floor").conaffinity[0]),"friction":m.geom("floor").friction.tolist()},
            "soles":soles,"physical_transfer_validated":False,
            "boundary":"Compiled HOME static frame/COM/inertia/mask inspection. No dynamic contact equivalence or hardware calibration is asserted."}
    (a.output/"audit.json").write_text(json.dumps(report,indent=2)+"\n")
    for source in ("scripts/audit_walking_aligned_frames.py","microduck/velocity_env.py","microduck/walking_env.py","microduck/walking_controlled_env.py","microduck/walking_posture_env.py","microduck/walking_ground_env.py","microduck/constants.py"):
        dest=a.output/"source"/source;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/source,dest)
    (a.output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.relative_to(a.output)}\n" for f in sorted(a.output.rglob("*")) if f.is_file()))
    print(json.dumps(report),flush=True)


if __name__=="__main__":main()
