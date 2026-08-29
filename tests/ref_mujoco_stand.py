"""Référence : le MÊME robot tenu à HAUTEUR HOME par le MÊME BAM, sous MuJoCo.

Sert de mètre-étalon au maintien sous Genesis (`tests/smoke_env.py` affiche
les mêmes grandeurs : hauteur du tronc, contact, hauteur de pied) : si les deux moteurs
s'affaissent pareil, l'affaissement est une propriété de l'actionneur (P seul,
raideur firmware faible, bande morte de striction), pas un défaut du portage.
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

import numpy as np, mujoco
from bam.model import load_model
from bam.mujoco import MujocoController
from microduck.constants import (JOINT_NAMES, DEFAULT_JOINT_POS, ROBOT_DIR,
                                 BAM_XL330_M6_JSON, BAM_KP_FW)

m = mujoco.MjModel.from_xml_path(os.path.join(ROBOT_DIR, "scene_walk.xml"))
d = mujoco.MjData(m)
m.opt.timestep = 0.005

# BAM produit le couple : les actionneurs <position> deviennent des moteurs purs.
for name in JOINT_NAMES:
    a = m.actuator(name)
    m.actuator_gaintype[a.id] = mujoco.mjtGain.mjGAIN_FIXED
    m.actuator_biastype[a.id] = mujoco.mjtBias.mjBIAS_NONE
    m.actuator_gainprm[a.id, :] = 0.0
    m.actuator_gainprm[a.id, 0] = 1.0
    m.actuator_biasprm[a.id, :] = 0.0
    m.actuator_ctrlrange[a.id] = [-10.0, 10.0]
    m.actuator_forcerange[a.id] = [-10.0, 10.0]

model = load_model(BAM_XL330_M6_JSON)
model.actuator.kp = BAM_KP_FW
model.actuator.vin = 7.35  # milieu de BAM_VIN_RANGE
ctrl = MujocoController(model, list(JOINT_NAMES), m, d)

mujoco.mj_resetData(m, d)
d.qpos[0:3] = [0.0, 0.0, 0.125]
d.qpos[3:7] = [1, 0, 0, 0]
for k, n in enumerate(JOINT_NAMES):
    d.qpos[m.jnt_qposadr[m.joint(n).id]] = DEFAULT_JOINT_POS[k]
    ctrl.set_q_target(n, DEFAULT_JOINT_POS[k])
# BAM calcule lui-même frottement et amortissement.
d.qvel[:] = 0.0
mujoco.mj_forward(m, d)

for i in range(1600):  # 8 s à 200 Hz
    ctrl.update()
    mujoco.mj_step(m, d)
    if i in (0, 20, 100, 400, 800, 1599):
        qq = np.array([d.qpos[m.jnt_qposadr[m.joint(n).id]] for n in JOINT_NAMES])
        e = np.abs(qq - np.array(DEFAULT_JOINT_POS))
        print(f"  step {i:4d} z={d.qpos[2]:+.4f} ncon={d.ncon} "
              f"|tau|max={np.abs(d.ctrl).max():.4f} err_max={e.max()*57.3:.2f}deg "
              f"({JOINT_NAMES[int(e.argmax())]})")

q = np.array([d.qpos[m.jnt_qposadr[m.joint(n).id]] for n in JOINT_NAMES])
err = np.abs(q - np.array(DEFAULT_JOINT_POS))
quat = d.qpos[3:7]
R = np.zeros(9); mujoco.mju_quat2Mat(R, quat); R = R.reshape(3, 3)
g_b = R.T @ np.array([0.0, 0.0, -1.0])

print(f"hauteur du tronc      : {d.qpos[2]:.4f} m")
print(f"inclinaison (|g_xy|)  : {np.linalg.norm(g_b[:2]):.4f}")
print(f"erreur articulaire max: {err.max()*57.3:.2f}°  moyenne {err.mean()*57.3:.2f}°")
print(f"pire articulation     : {JOINT_NAMES[int(err.argmax())]} ({err.max()*57.3:.2f}°)")
print(f"couple |τ|            : moy {np.abs(d.ctrl).mean():.4f}  max {np.abs(d.ctrl).max():.4f} N·m")
fl = m.dof_frictionloss[[m.jnt_dofadr[m.joint(n).id] for n in JOINT_NAMES]]
print(f"frictionloss          : moy {fl.mean():.5f}  max {fl.max():.5f} N·m")
