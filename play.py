"""Visualisation d'une politique entraînée dans le viewer Genesis.

    python play.py -e microduck-velocity --ckpt 1000
"""

import argparse
import os
import pickle

import torch

import genesis as gs
from rsl_rl.runners import OnPolicyRunner

from microduck import velocity_cfg as C
from microduck.velocity_env import MicroduckVelocityEnv


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-e", "--exp-name", default="microduck-velocity")
    p.add_argument("--ckpt", type=int, default=-1, help="-1 = dernier")
    p.add_argument("-B", "--num-envs", type=int, default=1)
    p.add_argument("--seconds", type=float, default=30.0)
    args = p.parse_args()

    gs.init(backend=gs.gpu, logging_level="warning")
    log_dir = os.path.join("logs", args.exp_name)
    with open(os.path.join(log_dir, "cfgs.pkl"), "rb") as f:
        saved = pickle.load(f)

    env = MicroduckVelocityEnv(
        num_envs=args.num_envs, rough=saved["rough"], backlash=saved.get("backlash", False), show_viewer=True, play=True
    )
    runner = OnPolicyRunner(env, saved["train_cfg"], log_dir, device=str(gs.device))

    if args.ckpt < 0:
        ckpts = [f for f in os.listdir(log_dir) if f.startswith("model_")]
        ckpt = max(ckpts, key=lambda f: int(f.split("_")[1].split(".")[0]))
    else:
        ckpt = f"model_{args.ckpt}.pt"
    runner.load(os.path.join(log_dir, ckpt))
    print(f"checkpoint : {ckpt}")

    policy = runner.get_inference_policy(device=str(gs.device))
    obs = env.get_observations()
    with torch.no_grad():
        for _ in range(int(args.seconds / env.dt)):
            obs, _, _, _ = env.step(policy(obs))


if __name__ == "__main__":
    main()
