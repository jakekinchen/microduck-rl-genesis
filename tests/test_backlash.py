"""La variante à jeu d'engrenage doit se comporter comme le vrai servo.

Le jeu (±1° en série avec chaque servo) est un vrai élément sim2real : sans lui,
la simulation est plus optimiste que le robot sur la précision de position.

Ce qu'on vérifie :
  1. le modèle porte bien 14 articulations de jeu, alignées sur les 14 servos ;
  2. l'observation `joint_pos` est la vue ENCODEUR (servo + jeu), pas la vue
     moteur — sinon la politique ne verrait jamais le jeu ;
  3. le jeu est borné à ±1° ;
  4. les dimensions d'obs et d'action sont INCHANGÉES (61 / 14), donc l'export
     ONNX et le runtime embarqué n'ont rien à changer.
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import torch
import genesis as gs
from microduck.velocity_env import MicroduckVelocityEnv
from microduck.constants import JOINT_NAMES, NUM_OBS, NUM_ACTIONS

gs.init(backend=gs.cpu, logging_level="warning")
env = MicroduckVelocityEnv(num_envs=2, backlash=True, demo=True)
d = gs.device

# 1. alignement servo ↔ jeu
assert env.backlash_dof_idx is not None and len(env.backlash_dof_idx) == NUM_ACTIONS
names = [j.name for j in env.robot.joints]
print(f"modèle : {len(names)} articulations dont {sum('backlash' in n for n in names)} de jeu")

# 2/3. le jeu est borné et l'obs le voit
env.robot.set_pos(torch.tensor([[0.0, 0.0, 0.125]] * 2, device=d))
env.robot.set_quat(torch.tensor([[1.0, 0.0, 0.0, 0.0]] * 2, device=d))
env.robot.zero_all_dofs_velocity()
env.robot.set_dofs_position(env.default_dof_pos.unsqueeze(0).repeat(2, 1), env.motors_dof_idx)
env.robot.set_dofs_position(torch.zeros(2, NUM_ACTIONS, device=d), env.backlash_dof_idx)
env._refresh_state()
assert torch.allclose(env.dof_pos_enc, env.dof_pos, atol=1e-6), "jeu non nul au départ"

# On impose un jeu de +0,5° sur une articulation : la vue encodeur doit bouger,
# la vue moteur non.
probe = 3  # left_knee
bl = torch.zeros(2, NUM_ACTIONS, device=d)
bl[:, probe] = math.radians(0.5)
env.robot.set_dofs_position(bl, env.backlash_dof_idx)
env._refresh_state()
diff_enc = float(env.dof_pos_enc[0, probe] - env.dof_pos[0, probe])
print(f"jeu imposé +0,500° sur {JOINT_NAMES[probe]} → vue encodeur {math.degrees(diff_enc):+.3f}°")
assert abs(math.degrees(diff_enc) - 0.5) < 1e-3, "l'obs ne lit pas à travers le jeu"

for _ in range(4):
    obs = env._compute_observations()
jp = obs["policy"][0][6:20]
assert abs(float(jp[probe]) - diff_enc) < 1e-4, "joint_pos n'est pas la vue encodeur"
print("joint_pos de l'observation = vue encodeur ✓")

# Butée : on pousse loin, la physique doit ramener dans ±1°.
bl[:, probe] = math.radians(10.0)
env.robot.set_dofs_position(bl, env.backlash_dof_idx)
for _ in range(40):
    env.scene.step()
env._refresh_state()
play = env.dof_pos_enc[0] - env.dof_pos[0]
print(f"jeu après relâchement : max {math.degrees(float(play.abs().max())):.3f}° (butée ±1°)")
assert math.degrees(float(play.abs().max())) < 1.6, "le jeu dépasse largement sa butée"

# 4. contrat inchangé
assert obs["policy"].shape[-1] == NUM_OBS == 61
assert env.num_actions == NUM_ACTIONS == 14
print(f"contrat inchangé : obs {NUM_OBS}, action {NUM_ACTIONS}")
print("OK — variante à jeu d'engrenage conforme")
