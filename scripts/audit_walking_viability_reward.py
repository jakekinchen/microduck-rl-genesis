"""Pretraining numerical decomposition of v9 on actual Genesis state.

No PPO, candidate selection, action intervention or acceptance evaluation.
Compare independent per-term episode deltas against the gating expression.
"""
import argparse
import copy
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    from scripts.train_walking_viability import verified_initializer
    from scripts.evaluate_laser import digest
    checkpoint, record, evidence = verified_initializer(ROOT)
    args.output.mkdir(parents=True, exist_ok=False)
    import genesis as gs
    import torch
    from tensordict import TensorDict
    from rsl_rl.models import MLPModel
    from export_onnx import ExportedPolicy
    from microduck.walking_viability_env import MicroduckViableWalkingEnv, positive_walking_return, posture_viability
    from microduck.velocity_cfg import REWARD_WEIGHTS
    torch.set_num_threads(1)
    gs.init(backend=gs.cpu, logging_level="warning", seed=76719)
    env = MicroduckViableWalkingEnv(4)
    cfg = copy.deepcopy(record["train_cfg"])
    cfg["actor"].pop("class_name")
    actor = MLPModel(TensorDict({"policy": torch.zeros(1, 61)}, [1]), cfg["obs_groups"], "actor", 14, **cfg["actor"])
    actor.load_state_dict(torch.load(checkpoint, map_location="cpu", weights_only=True)["actor_state_dict"])
    policy = ExportedPolicy(actor.eval()).eval()
    terms = list(REWARD_WEIGHTS) + ["sole_lift", "valid_landing", "flight_cost", "fall_event",
                                   "motor_effort", "stop_motion", "head_command_cost",
                                   "command_error_cost", "trunk_lean_cost"]
    original = env._compute_rewards
    positive_error = reward_error = 0.
    samples = landing_events = 0
    viability_min, viability_max = 1., 0.

    def audited_rewards():
        nonlocal positive_error, reward_error, samples, landing_events, viability_min, viability_max
        before = {name: env.episode_sums[name].clone() for name in terms}
        original()
        delta = torch.stack([env.episode_sums[name] - before[name] for name in terms])
        measured_positive = delta.clamp_min(0).sum(0)
        positive = positive_walking_return(env)
        viability = posture_viability(env.walking_head_absolute_ema, env.projected_gravity)
        # Direct formula for the new DC cost, independent of logged episode sums.
        dc = -2 * (env.walking_yaw_bias_ema.abs() - .005).clamp_min(0) / .05 * env.dt
        expected = delta.sum(0) - (1 - viability) * positive + dc
        positive_error = max(positive_error, float((measured_positive - positive).abs().max()))
        reward_error = max(reward_error, float((expected - env.rew_buf).abs().max()))
        if not torch.isfinite(env.rew_buf).all() or positive_error > 1e-4 or reward_error > 1e-4:
            raise ValueError("actual-state reward decomposition failed")
        samples += env.num_envs
        landing_events += int(env.valid_landing.sum())
        viability_min = min(viability_min, float(viability.min()))
        viability_max = max(viability_max, float(viability.max()))

    env._compute_rewards = audited_rewards
    obs = env.get_observations()
    for _ in range(500):
        with torch.no_grad():
            action = policy(obs["policy"].cpu())
        obs, _, _, _ = env.step(action.to(env.device))
    if landing_events < 2 or viability_min > .5 or viability_max < .99:
        raise ValueError("audit did not cover landings and both healthy and unhealthy posture")
    result = {"schema": "microduck.walking-viability-reward-audit/v1",
              "checkpoint_sha256": digest(checkpoint), "samples": samples,
              "landing_events": landing_events, "maximum_positive_decomposition_error": positive_error,
              "maximum_reward_decomposition_error": reward_error,
              "posture_viability_range": [viability_min, viability_max],
              "inference": "unchanged normalized Torch CPU v8 FINAL mean",
              "physics": "Genesis CPU, four training environments, inherited reset/commands/timing",
              "training_performed": False, "passed": True,
              "boundary": "Numerical reward-accounting test across actual stepping states, not controller or physical acceptance."}
    (args.output / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
    for name in ("scripts/audit_walking_viability_reward.py", "microduck/walking_viability_env.py",
                 "microduck/walking_yaw_bias_env.py", "experiments/walking/VIABILITY-v9.md"):
        target = args.output / "source" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
    (args.output / "SHA256SUMS").write_text("".join(
        f"{digest(p)}  {p.relative_to(args.output)}\n"
        for p in sorted(args.output.rglob("*")) if p.is_file()))
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
