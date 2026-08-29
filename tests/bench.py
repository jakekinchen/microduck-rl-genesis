"""Débit de simulation à l'échelle d'entraînement."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import torch, genesis as gs
from microduck.velocity_env import MicroduckVelocityEnv

n = int(sys.argv[1]) if len(sys.argv) > 1 else 4096
gs.init(backend=gs.gpu, logging_level="warning")
t0 = time.time()
env = MicroduckVelocityEnv(num_envs=n)
print(f"construction ({n} envs) : {time.time()-t0:.1f}s")
a = torch.zeros(n, env.num_actions, device=gs.device)
for _ in range(20):
    env.step(a)   # préchauffage / compilation des kernels
torch.cuda.synchronize() if torch.cuda.is_available() else None
t = time.time()
K = 100
for _ in range(K):
    env.step(a)
torch.cuda.synchronize() if torch.cuda.is_available() else None
dt = time.time() - t
sps = K * n / dt
print(f"{K} pas de contrôle en {dt:.2f}s → {sps:,.0f} pas-env/s")
print(f"itération PPO (24 pas × {n} envs) ≈ {24*n/sps:.2f}s de collecte")
print(f"→ 1000 itérations ≈ {1000*24*n/sps/3600:.2f} h de simulation pure")
