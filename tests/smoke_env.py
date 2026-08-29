"""Smoke test : construit l'env, fait quelques pas, vérifie les formes."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import torch
import genesis as gs
from microduck.velocity_env import MicroduckVelocityEnv

rough = "--rough" in sys.argv
gs.init(backend=gs.gpu, logging_level="warning")
env = MicroduckVelocityEnv(num_envs=16, rough=rough)
obs = env.get_observations()
print("obs policy    :", tuple(obs["policy"].shape))
print("obs privileged:", tuple(obs["privileged"].shape))
t = time.time()
for i in range(30):
    a = torch.zeros(env.num_envs, env.num_actions, device=gs.device)
    obs, rew, done, extras = env.step(a)
    if i == 0 or i == 29:
        print(f"step {i}: rew={rew.mean().item():+.4f} done={done.sum().item()} "
              f"z={env.base_pos[:,2].mean().item():.4f} "
              f"foot_h={env.foot_height.mean().item():.4f} "
              f"contact={env.contact.float().mean().item():.2f}")
    assert torch.isfinite(obs["policy"]).all(), f"NaN dans l'obs au pas {i}"
    assert torch.isfinite(rew).all(), f"NaN dans la reward au pas {i}"
print(f"30 pas en {time.time()-t:.2f}s")
print("OK")
