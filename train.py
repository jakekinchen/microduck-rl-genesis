"""Entraînement de la marche du Microduck sous Genesis (PPO / rsl_rl).

    python train.py --num-envs 4096                # tâche principale, sol plat
    python train.py --num-envs 64 --max-iterations 5   # SMOKE TEST — toujours en premier
    python train.py --rough --num-envs 4096        # terrain accidenté

Un smoke test de 5 itérations à 64 envs attrape ~95 % des erreurs de config
pour quelques centimes. Ne jamais lancer un run long sans.
"""

import argparse
import os
import pickle
import shutil
import sys
from importlib import metadata

try:
    if int(metadata.version("rsl-rl-lib").split(".")[0]) < 5:
        raise ImportError
except (metadata.PackageNotFoundError, ImportError) as e:
    raise ImportError("Installer 'rsl-rl-lib>=5.0.0'.") from e

import genesis as gs
import torch
from rsl_rl.runners import OnPolicyRunner

from microduck import velocity_cfg as C
from microduck.velocity_env import MicroduckVelocityEnv


def _physics_backend(name: str):
    return {"metal": gs.metal, "cpu": gs.cpu, "gpu": gs.gpu}[name]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-e", "--exp-name", default="microduck-velocity")
    p.add_argument("-B", "--num-envs", type=int, default=4096)
    p.add_argument("--max-iterations", type=int, default=50_000)
    p.add_argument("--rough", action="store_true", help="terrain accidenté")
    p.add_argument("--backlash", action="store_true",
                   help="variante à jeu d'engrenage (±1° par servo, encodeur lu à travers)")
    p.add_argument("--resume", default=None, help="chemin d'un checkpoint .pt")
    p.add_argument(
        "--physics-backend",
        choices=("metal", "cpu", "gpu"),
        default="metal" if sys.platform == "darwin" else "gpu",
        help="moteur physique (macOS: metal requis, cpu = repli immédiat)",
    )
    p.add_argument(
        "--learner-device",
        choices=("mps", "cpu", "auto"),
        default="mps" if sys.platform == "darwin" else "auto",
        help="device PPO, indépendant du moteur physique",
    )
    p.add_argument(
        "--cpu",
        action="store_true",
        help="alias historique de --physics-backend cpu; PPO reste sur --learner-device",
    )
    p.add_argument("--seed", type=int, default=1)
    args = p.parse_args()

    physics_name = "cpu" if args.cpu else args.physics_backend
    if args.learner_device == "mps" and not torch.backends.mps.is_available():
        raise RuntimeError("PPO sur MPS requis, mais torch.backends.mps.is_available() est faux")

    gs.init(backend=_physics_backend(physics_name), logging_level="warning")
    if physics_name == "metal" and gs.backend != gs.metal:
        raise RuntimeError(f"physique Metal requise, backend obtenu: {gs.backend}")
    if physics_name == "cpu" and gs.backend != gs.cpu:
        raise RuntimeError(f"physique CPU demandée, backend obtenu: {gs.backend}")

    learner_device = (
        str(gs.device) if args.learner_device == "auto" else args.learner_device
    )
    print(
        f"devices: physics={physics_name}/{gs.backend} ({gs.device}), "
        f"ppo={learner_device}, envs={args.num_envs}, iterations={args.max_iterations}"
    )

    log_dir = os.path.join("logs", args.exp_name)
    if os.path.exists(log_dir) and args.resume is None:
        shutil.rmtree(log_dir)
    os.makedirs(log_dir, exist_ok=True)

    env = MicroduckVelocityEnv(num_envs=args.num_envs, rough=args.rough,
                               backlash=args.backlash)

    train_cfg = dict(C.TRAIN_CFG)
    train_cfg["run_name"] = args.exp_name
    train_cfg["seed"] = args.seed
    with open(os.path.join(log_dir, "cfgs.pkl"), "wb") as f:
        pickle.dump({"train_cfg": train_cfg, "rough": args.rough,
                     "backlash": args.backlash, "physics_backend": physics_name,
                     "learner_device": learner_device}, f)

    runner = OnPolicyRunner(env, train_cfg, log_dir, device=learner_device)
    if args.resume:
        runner.load(args.resume)
    runner.learn(num_learning_iterations=args.max_iterations, init_at_random_ep_len=True)


if __name__ == "__main__":
    main()
