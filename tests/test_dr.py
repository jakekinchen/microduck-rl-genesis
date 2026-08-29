"""La randomisation de domaine doit être PAR ENV et NON ACCUMULANTE.

Deux pièges que l'amont documente comme ayant coûté des mois :

  - une DR écrite dans un champ non « expansé » par monde s'applique à tous les
    envs à la fois : la randomisation est alors un no-op silencieux ;
  - une DR qui ajoute au lieu de repartir du défaut s'accumule reset après
    reset ; un randomiseur de CoM accumulant a dégradé tous les runs longs.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import torch
import genesis as gs
from genesis.utils.misc import qd_to_torch
from microduck.velocity_env import MicroduckVelocityEnv

gs.init(backend=gs.gpu, logging_level="warning")
env = MicroduckVelocityEnv(num_envs=8)
sv = env.scene.rigid_solver
dof_t = torch.tensor(env.motors_dof_idx, device=gs.device)


def frictionloss():
    return qd_to_torch(sv.dofs_info.frictionloss, transpose=True)[:, dof_t]


def armature():
    return qd_to_torch(sv.dofs_info.armature, transpose=True)[:, dof_t]


# -- 1. frictionloss strictement proportionnel à friction_scale, par env -------
# On met les 8 envs dans le MÊME état : tout écart restant vient du scale seul.
env.robot.set_pos(torch.tensor([[0.0, 0.0, 0.125]] * 8, device=gs.device))
env.robot.set_quat(torch.tensor([[1.0, 0.0, 0.0, 0.0]] * 8, device=gs.device))
env.robot.zero_all_dofs_velocity()
env.robot.set_dofs_position(
    env.default_dof_pos.unsqueeze(0).repeat(8, 1), env.motors_dof_idx
)
ids = torch.arange(8, device=gs.device)
scales = torch.tensor([[1.0], [2.0], [0.5], [1.0], [1.0], [1.0], [1.0], [1.0]],
                      device=gs.device)
env.bam.set_friction_scale(ids, scales)
env.bam.prev_torque.zero_()
env.bam.compute(env.default_dof_pos.unsqueeze(0).repeat(8, 1))
fl = frictionloss()
r2 = (fl[1] / fl[0]).mean().item()
r05 = (fl[2] / fl[0]).mean().item()
print(f"frictionloss ratio scale 2.0 : {r2:.4f} (attendu 2.0)")
print(f"frictionloss ratio scale 0.5 : {r05:.4f} (attendu 0.5)")
assert abs(r2 - 2.0) < 1e-3 and abs(r05 - 0.5) < 1e-3, "DR de frottement pas par-env"

# -- 2. l'armature ne doit pas dériver sur des resets répétés -----------------
base = float(env.bam.armature)
env.bam.set_armature_scale(ids, torch.full((8, 1), 1.1, device=gs.device))
a1 = armature()[:, 0].clone()
for _ in range(5):
    env.bam.set_armature_scale(ids, torch.full((8, 1), 1.1, device=gs.device))
a2 = armature()[:, 0]
print(f"armature : défaut {base:.6f}  après ×1.1 {a1.mean():.6f}  "
      f"après 6×(×1.1) {a2.mean():.6f}")
assert torch.allclose(a1, a2), "DR d'armature ACCUMULANTE"
assert abs(a1.mean().item() - base * 1.1) < 1e-6

# -- 3. le décalage de CoM ne doit pas s'accumuler non plus -------------------
env.com_range = 0.01
shifts = []
for _ in range(4):
    env.reset_idx(ids)
    sh = sv.get_links_COM_shift(links_idx=[env.robot.link_start + env.trunk_idx])
    shifts.append(sh.abs().max().item())
print(f"|COM shift| max sur 4 resets : {[round(s, 5) for s in shifts]}")
assert max(shifts) <= 0.01 + 1e-6, "DR de CoM ACCUMULANTE"

# -- 4. biais encodeur : constant par env, vu par l'ACTEUR seulement ----------
assert env.encoder_bias.std(dim=0).min() > 0, "biais encodeur identique sur tous les envs"
print(f"biais encodeur : [{env.encoder_bias.min():.4f}, {env.encoder_bias.max():.4f}] rad")
print("OK")
