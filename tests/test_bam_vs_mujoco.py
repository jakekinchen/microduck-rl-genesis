"""Genesis+BAM contre MuJoCo+BAM : mêmes conditions, mêmes trajectoires ?

Tenir la pose HOME en boucle ouverte est un équilibre INSTABLE — les deux
moteurs finissent par basculer, et le moment exact du basculement est chaotique.
Ce test ne compare donc que la phase où le robot est encore debout : c'est là
que la boucle actionneur (loi firmware → couple → budget de frottement → écrêtage
par le solveur) est réellement mise à l'épreuve, avec les deux pieds chargés.

Tout l'aléatoire est neutralisé : tension fixe, pas de chute de tension, pas de
retard de bus, pas de DR, pas de bruit.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def _bam_repo():
    """Chemin du dépôt BAM de référence, ou None s'il n'est pas disponible.

    Le dépôt BAM n'est pas une dépendance du projet : il ne sert qu'à VÉRIFIER
    le portage. On le prend en argument ou dans BAM_REPO ; sans lui, le test se
    saute proprement au lieu d'échouer.

        git clone -b mjlab_frictionloss https://github.com/Rhoban/bam.git
        BAM_REPO=$PWD/bam python tests/<ce test>.py
    """
    import os, sys
    p = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("BAM_REPO", "")
    return p if p and os.path.isdir(p) else None

_BAM = _bam_repo()
if _BAM is None:
    print("SKIP — dépôt BAM absent (voir _bam_repo ci-dessus)")
    raise SystemExit(0)
sys.path.insert(0, _BAM)

import numpy as np, torch, mujoco
import genesis as gs
from bam.model import load_model
from bam.mujoco import MujocoController
from microduck.bam_actuator import BamActuator
from microduck.constants import (JOINT_NAMES, DEFAULT_JOINT_POS, ROBOT_DIR,
                                 MICRODUCK_WALK_XML, BAM_XL330_M6_JSON, BAM_KP_FW)

N_STEPS = 120           # 0,6 s à 200 Hz
VIN = 7.35
Z0 = 0.125
HOME = np.array(DEFAULT_JOINT_POS)

# ---------------------------------------------------------------- MuJoCo -----
m = mujoco.MjModel.from_xml_path(os.path.join(ROBOT_DIR, "scene_walk.xml"))
m.opt.timestep = 0.005
d = mujoco.MjData(m)
for name in JOINT_NAMES:  # <position> → moteur pur, BAM fournit le couple
    a = m.actuator(name)
    m.actuator_gaintype[a.id] = mujoco.mjtGain.mjGAIN_FIXED
    m.actuator_biastype[a.id] = mujoco.mjtBias.mjBIAS_NONE
    m.actuator_gainprm[a.id, :] = 0.0
    m.actuator_gainprm[a.id, 0] = 1.0
    m.actuator_biasprm[a.id, :] = 0.0
    m.actuator_forcerange[a.id] = [-10.0, 10.0]
ref = load_model(BAM_XL330_M6_JSON)
ref.actuator.kp = BAM_KP_FW
ref.actuator.vin = VIN
ctrl = MujocoController(ref, list(JOINT_NAMES), m, d)
d.qpos[0:3] = [0.0, 0.0, Z0]; d.qpos[3:7] = [1, 0, 0, 0]
for k, n in enumerate(JOINT_NAMES):
    d.qpos[m.jnt_qposadr[m.joint(n).id]] = HOME[k]
    ctrl.set_q_target(n, HOME[k])
d.qvel[:] = 0.0
mujoco.mj_forward(m, d)
mj_q, mj_z = [], []
for _ in range(N_STEPS):
    ctrl.update()
    mujoco.mj_step(m, d)
    mj_q.append([d.qpos[m.jnt_qposadr[m.joint(n).id]] for n in JOINT_NAMES])
    mj_z.append(d.qpos[2])
mj_q = np.array(mj_q); mj_z = np.array(mj_z)

# --------------------------------------------------------------- Genesis -----
gs.init(backend=gs.cpu, logging_level="error")
sc = gs.Scene(show_viewer=False,
              sim_options=gs.options.SimOptions(dt=0.005, substeps=1),
              rigid_options=gs.options.RigidOptions(batch_dofs_info=True,
                                                    iterations=100, ls_iterations=50))
sc.add_entity(gs.morphs.Plane())
robot = sc.add_entity(gs.morphs.MJCF(file=MICRODUCK_WALK_XML))
sc.build(n_envs=1)
jb = {j.name: j for j in robot.joints}
dofs = [jb[n].dof_start for n in JOINT_NAMES]
bam = BamActuator(robot, dofs, 1, torch.device("cpu"), 0.005)
bam.vin_nominal[:] = VIN
bam.vin_drop_resistance = None          # pas de chute de tension
robot.set_pos(torch.tensor([[0.0, 0.0, Z0]]))
robot.set_quat(torch.tensor([[1.0, 0.0, 0.0, 0.0]]))
robot.zero_all_dofs_velocity()
target = torch.tensor(HOME, dtype=gs.tc_float).unsqueeze(0)
robot.set_dofs_position(target, dofs)
gs_q, gs_z = [], []
for _ in range(N_STEPS):
    robot.control_dofs_force(bam.compute(target), dofs)
    sc.step()
    gs_q.append(robot.get_dofs_position(dofs)[0].numpy().copy())
    gs_z.append(float(robot.get_pos()[0, 2]))
gs_q = np.array(gs_q); gs_z = np.array(gs_z)

# --------------------------------------------------------------- Rapport -----
print(f"{'t (s)':>7s} {'z mujoco':>10s} {'z genesis':>10s} {'|Δq| max':>12s} {'|Δq| moy':>10s}")
for i in (9, 29, 59, 99, N_STEPS - 1):
    dq = np.abs(gs_q[i] - mj_q[i]) * 57.3
    print(f"{(i+1)*0.005:7.3f} {mj_z[i]:10.4f} {gs_z[i]:10.4f} "
          f"{dq.max():10.2f}°  {dq.mean():8.2f}°")

worst = np.abs(gs_q - mj_q).max(axis=0) * 57.3
print("\nécart max sur l'horizon, par articulation :")
for k, n in enumerate(JOINT_NAMES):
    print(f"  {n:16s} {worst[k]:6.2f}°   (amplitude mujoco {np.ptp(mj_q[:,k])*57.3:6.2f}°)")

half = N_STEPS // 2
d_half = np.abs(gs_q[half] - mj_q[half]).max() * 57.3
print(f"\nécart max à {half*0.005:.2f} s : {d_half:.2f}°")
print(f"écart de hauteur à {half*0.005:.2f} s : {abs(gs_z[half]-mj_z[half])*1000:.1f} mm")
assert d_half < 3.0, "les deux moteurs divergent trop tôt — portage BAM suspect"
print("OK — l'actionneur porté suit la référence MuJoCo+BAM")
