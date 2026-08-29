"""Le couple externe lu dans Genesis doit égaler celui de MuJoCo.

`BamActuator._external_torque` lit `qf_bias` / `qf_constraint` du solveur Genesis
avec les conventions de signe de MuJoCo (-qfrc_bias + qfrc_constraint). C'est le
maillon le plus facile à se tromper de tout le portage, et une erreur de signe
y serait indolore au démarrage puis fausserait tout le frottement dépendant de
la charge. On compare donc directement à MuJoCo, moteur de référence, sur le
MÊME état : robot en l'air (pas de contact → qf_constraint nul), pose HOME,
vitesses nulles, donc qf_bias = pur couple de gravité.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, torch
import genesis as gs
from genesis.utils.misc import qd_to_torch
from microduck.constants import MICRODUCK_WALK_XML, JOINT_NAMES, DEFAULT_JOINT_POS

gs.init(backend=gs.cpu, logging_level="error")
sc = gs.Scene(show_viewer=False,
              sim_options=gs.options.SimOptions(dt=0.005, substeps=1),
              rigid_options=gs.options.RigidOptions(batch_dofs_info=True))
sc.add_entity(gs.morphs.Plane())
robot = sc.add_entity(gs.morphs.MJCF(file=MICRODUCK_WALK_XML))
sc.build(n_envs=2)

jb = {j.name: j for j in robot.joints}
dofs = [jb[n].dof_start for n in JOINT_NAMES]
q_home = torch.tensor(DEFAULT_JOINT_POS, dtype=gs.tc_float)

POS = (0.0, 0.0, 1.0)  # en l'air : aucun contact
robot.set_pos(torch.tensor([POS] * 2))
robot.set_quat(torch.tensor([[1.0, 0.0, 0.0, 0.0]] * 2))
robot.zero_all_dofs_velocity()
robot.set_dofs_position(q_home.unsqueeze(0).repeat(2, 1), dofs)
sc.step()

sv = sc.rigid_solver
qf_bias = qd_to_torch(sv.dofs_state.qf_bias, transpose=True)[0]
qf_con = qd_to_torch(sv.dofs_state.qf_constraint, transpose=True)[0]
g_ext = (-qf_bias + qf_con)[torch.tensor(dofs)].numpy()

import mujoco
m = mujoco.MjModel.from_xml_path(MICRODUCK_WALK_XML)
d = mujoco.MjData(m)
d.qpos[0:3] = POS
d.qpos[3:7] = [1, 0, 0, 0]
for k, n in enumerate(JOINT_NAMES):
    jid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, n)
    d.qpos[m.jnt_qposadr[jid]] = DEFAULT_JOINT_POS[k]
d.qvel[:] = 0.0
mujoco.mj_forward(m, d)
mj_ext = np.array([
    -d.qfrc_bias[m.jnt_dofadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, n)]]
    for n in JOINT_NAMES
])

print(f"{'articulation':16s} {'genesis':>10s} {'mujoco':>10s} {'écart':>10s}")
for k, n in enumerate(JOINT_NAMES):
    print(f"{n:16s} {g_ext[k]:10.5f} {mj_ext[k]:10.5f} {g_ext[k]-mj_ext[k]:10.2e}")
err = np.abs(g_ext - mj_ext).max()
scale = np.abs(mj_ext).max()
print(f"\nécart max = {err:.3e} N·m   (couple max = {scale:.4f} N·m, soit {100*err/scale:.3f} %)")
assert err < 2e-3 * max(scale, 1e-3) + 1e-5, "le couple externe diverge de MuJoCo"
print("OK — conventions de signe et indexation validées")
