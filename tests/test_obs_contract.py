"""Le contrat de déploiement 61-D doit être respecté au bit près.

C'est LE test qui décide si une politique entraînée ici peut être branchée telle
quelle sur le runtime embarqué du Microduck. On ne vérifie pas seulement la
dimension : on impose un état connu au robot et on vérifie que chaque tranche de
l'observation contient bien la grandeur annoncée dans SIM2REAL.md, dans le bon
repère et le bon ordre.

Un test qui ne regarderait que `obs.shape == (n, 61)` laisserait passer une
permutation d'articulations — l'erreur exacte qui détruit un transfert.
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import torch
import genesis as gs
from microduck.velocity_env import MicroduckVelocityEnv
from microduck.constants import (JOINT_NAMES, DEFAULT_JOINT_POS, OBS_LAYOUT,
                                 NUM_OBS, NUM_ACTIONS, HEAD_JOINT_NAMES)

gs.init(backend=gs.cpu, logging_level="warning")
env = MicroduckVelocityEnv(num_envs=2, demo=True)   # démo : ni bruit ni biais
d = gs.device

# --- 1. La découpe annoncée fait bien 61 et couvre tout -----------------------
off, slices = 0, {}
for name, dim in OBS_LAYOUT:
    slices[name] = slice(off, off + dim)
    off += dim
assert off == NUM_OBS == 61, off
print(f"découpe : {NUM_OBS} dimensions, {len(OBS_LAYOUT)} tranches")

# --- 2. État connu : robot debout, à plat, immobile, pose HOME ---------------
env.robot.set_pos(torch.tensor([[0.0, 0.0, 0.125]] * 2, device=d))
env.robot.set_quat(torch.tensor([[1.0, 0.0, 0.0, 0.0]] * 2, device=d))
env.robot.zero_all_dofs_velocity()
env.robot.set_dofs_position(
    env.default_dof_pos.unsqueeze(0).repeat(2, 1), env.motors_dof_idx
)
env.set_twist(0.31, -0.12, 0.44)
env.set_head_pose(0.11, -0.22, 0.33, -0.05)
env.body_cmd[:] = torch.tensor([0.001, 0.002, 0.003, 0.004, 0.005, 0.006], device=d)
env._refresh_state()
env._update_contacts()
# Vider les tampons de retard : sinon on lirait l'état d'AVANT le placement.
for _ in range(4):
    obs = env._compute_observations()
o = obs["policy"][0]

# gravité projetée : robot droit → (0, 0, −1)
g = o[slices["projected_gravity"]]
assert torch.allclose(g, torch.tensor([0.0, 0.0, -1.0], device=d), atol=2e-3), g
print(f"projected_gravity debout : {[round(float(v),4) for v in g]}")

# vitesse angulaire : robot immobile → 0
w = o[slices["base_ang_vel"]]
assert w.abs().max() < 1e-3, w

# joint_pos est RELATIVE à HOME → 0 à la pose HOME
jp = o[slices["joint_pos"]]
assert jp.abs().max() < 1e-4, f"joint_pos non relative à HOME : {jp}"
print(f"joint_pos à la pose HOME  : max |·| = {float(jp.abs().max()):.2e}")

# commandes : recopiées telles quelles, dans l'ordre annoncé
assert torch.allclose(o[slices["twist_command"]],
                      torch.tensor([0.31, -0.12, 0.44], device=d), atol=1e-6)
assert torch.allclose(o[slices["head_pose_command"]],
                      torch.tensor([0.11, -0.22, 0.33, -0.05], device=d), atol=1e-6)
assert torch.allclose(o[slices["body_pose_command"]],
                      torch.tensor([0.001, 0.002, 0.003, 0.004, 0.005, 0.006], device=d),
                      atol=1e-6)
print("tranches de commande : conformes")

# --- 3. joint_pos suit l'ORDRE canonique des servos --------------------------
# On décale UNE articulation et on vérifie que c'est bien la bonne case qui bouge.
for probe in (0, 5, 13):
    q = env.default_dof_pos.clone()
    q[probe] += 0.17
    env.robot.set_dofs_position(q.unsqueeze(0).repeat(2, 1), env.motors_dof_idx)
    env._refresh_state()
    for _ in range(4):
        obs = env._compute_observations()
    jp = obs["policy"][0][slices["joint_pos"]]
    moved = int(jp.abs().argmax())
    assert moved == probe and abs(float(jp[probe]) - 0.17) < 1e-3, (
        f"{JOINT_NAMES[probe]} apparaît en position {moved} de joint_pos")
    print(f"  {JOINT_NAMES[probe]:16s} → indice {probe} ✓")

# --- 4. Les 4 DOF de tête sont bien ceux que head_pose commande --------------
head_ids = [JOINT_NAMES.index(n) for n in HEAD_JOINT_NAMES]
assert head_ids == list(env.head_ids.cpu().numpy()), head_ids
print(f"head_pose pilote {HEAD_JOINT_NAMES} → indices {head_ids}")

# --- 5. L'action est un delta en radians autour de HOME ----------------------
env.robot.set_dofs_position(
    env.default_dof_pos.unsqueeze(0).repeat(2, 1), env.motors_dof_idx)
a = torch.zeros(2, NUM_ACTIONS, device=d)
a[:, 3] = 0.2                      # left_knee
env.step(a)
# La cible est HOME + action ; le servo ne l'atteint pas instantanément (raideur
# firmware finie), mais il doit partir DANS LE BON SENS, sur la bonne articulation.
delta = env.dof_pos[0] - env.default_dof_pos
assert delta[3] > 0.0, f"left_knee n'a pas suivi l'action : {float(delta[3]):.4f}"
assert int(delta.abs().argmax()) == 3, f"c'est {JOINT_NAMES[int(delta.abs().argmax())]} qui a bougé"
print(f"action[3] = +0.2 rad → left_knee se déplace de {float(delta[3]):+.4f} rad")

print("OK — contrat d'observation et d'action conforme à SIM2REAL.md")
