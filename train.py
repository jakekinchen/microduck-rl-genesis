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
from importlib import metadata

try:
    if int(metadata.version("rsl-rl-lib").split(".")[0]) < 5:
        raise ImportError
except (metadata.PackageNotFoundError, ImportError) as e:
    raise ImportError("Installer 'rsl-rl-lib>=5.0.0'.") from e

import genesis as gs
from rsl_rl.runners import OnPolicyRunner

from microduck import velocity_cfg as C
from microduck.velocity_env import MicroduckVelocityEnv


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-e", "--exp-name", default="microduck-velocity")
    p.add_argument("-B", "--num-envs", type=int, default=4096)
    p.add_argument("--max-iterations", type=int, default=50_000)
    p.add_argument("--rough", action="store_true", help="terrain accidenté")
    p.add_argument("--backlash", action="store_true",
                   help="variante à jeu d'engrenage (±1° par servo, encodeur lu à travers)")
    p.add_argument("--resume", default=None, help="chemin d'un checkpoint .pt")
    p.add_argument("--cpu", action="store_true")
    p.add_argument("--seed", type=int, default=1)
    args = p.parse_args()

    gs.init(backend=gs.cpu if args.cpu else gs.gpu, logging_level="warning")

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
                     "backlash": args.backlash}, f)

    runner = OnPolicyRunner(env, train_cfg, log_dir, device=str(gs.device))
    if args.resume:
        runner.load(args.resume)
    runner.learn(num_learning_iterations=args.max_iterations, init_at_random_ep_len=True)


if __name__ == "__main__":
    main()
