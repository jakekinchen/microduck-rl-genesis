"""Bounded first-party V15 standing-only refinement from exact V5 FINAL."""
import argparse
import copy
import importlib.metadata
import json
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.evaluate_laser import digest
from scripts.evaluate_walking_heading import verify_input_manifest
PARENT_SHA = "19fef3b5d443001f817169cecc660a2bef51b34791b5d84dfa59cc4e619a43c1"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run-id", required=True)
    p.add_argument("--num-envs", type=int, default=1024)
    p.add_argument("--iterations", type=int, default=250)
    p.add_argument("--seed", type=int, default=26090615)
    a = p.parse_args()
    if (not a.run_id.replace("-", "").isalnum() or (a.num_envs, a.iterations) not in ((64,5),(1024,250)) or a.seed != 26090615):
        p.error("new simple ID, frozen 64x5 smoke or 1024x250 full run, seed26090615")
    parent = ROOT/"receipts/walking/20260905-v5-training-complete"
    prior = json.loads((parent/"training.json").read_text())
    checkpoint = parent/"model_749.pt"
    if prior["status"] != "completed" or prior["checkpoint_sha256"] != PARENT_SHA or digest(checkpoint) != PARENT_SHA:
        raise ValueError("exact V5 FINAL required")
    for name, sha in prior["source_sha256"].items():
        if digest(ROOT/name) != sha or digest(parent/"source"/name) != sha:
            raise ValueError("parent source drift")
    baseline = ROOT/"receipts/walking/20260906-v14-standing-pair"
    verify_input_manifest(baseline)
    evaluation = json.loads((baseline/"evaluation.json").read_text())
    if (evaluation["acceptance_variant"] != "command-stand-switch-v14" or evaluation["passed_cases"] != 13
            or evaluation["total_cases"] != 21
            or any(c["failures"] not in ([], ["stop_max_tilt_deg"]) or not c["self_load"]["passed"] for c in evaluation["case_reports"])):
        raise ValueError("complete unbraced V14 posture-only negative required")
    from scripts.evaluate_walking_standing_trained import FREEZE, SOURCES
    for name, sha in json.loads(FREEZE.read_text())["source_sha256"].items():
        if digest(ROOT/name) != sha:
            raise ValueError(f"frozen source drift: {name}")
    out = ROOT/"logs"/a.run_id
    out.mkdir(parents=True, exist_ok=False)
    record = {"schema": "microduck.walking-training/v1", "variant": "standing-v15",
              "proof_class": "first_party_development", "held_out": False, "target_source": "zero-command-standing",
              "args": vars(a), "status": "starting", "planned_new_transitions": a.num_envs*a.iterations*24,
              "new_transitions": 0, "pid": __import__("os").getpid(),
              "standing_pair_baseline_manifest_sha256": digest(baseline/"SHA256SUMS")}
    started, runner = time.monotonic(), None
    try:
        (out/"run.json").write_text(json.dumps(record, indent=2)+"\n")
        import torch
        import genesis as gs
        from rsl_rl.runners import OnPolicyRunner
        from microduck.velocity_cfg import TRAIN_CFG
        from microduck.standing_env import MicroduckStandingEnv
        cfg = copy.deepcopy(TRAIN_CFG)
        cfg.update(seed=a.seed, run_name=a.run_id)
        cfg["algorithm"]["learning_rate"] = 2e-4
        sources = list(dict.fromkeys(list(prior["source_sha256"])+SOURCES+[
            "scripts/train_standing.py", "experiments/walking/evaluator-freeze-standing-trained-v15.json"]))
        sources += ["microduck/assets/microduck/robot_allcollisions.xml", "microduck/assets/microduck/scene.xml"]
        sources += [str(path.relative_to(ROOT)) for path in sorted((ROOT/"microduck/assets/microduck/assets").iterdir()) if path.is_file()]
        record.update(train_cfg=cfg,
            source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            source_sha256={name: digest(ROOT/name) for name in sources},
            packages={name: importlib.metadata.version(name) for name in ("genesis-world", "torch", "rsl-rl-lib", "mujoco")},
            warm_start={"path": str(checkpoint.relative_to(ROOT)), "sha256": PARENT_SHA,
                        "optimizer_loaded": False, "initialization_only": True})
        for name, sha in record["source_sha256"].items():
            dest = out/"source"/name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT/name, dest)
            if digest(dest) != sha:
                raise ValueError("source capture changed")
        gs.init(backend=gs.metal, logging_level="warning", seed=a.seed)
        env = MicroduckStandingEnv(a.num_envs, model_directory=ROOT/"experiments/walking/models/contact-v11")
        if env.num_obs != 61 or env.num_actions != 14 or torch.count_nonzero(env.twist_cmd).item():
            raise ValueError("standing actor contract or command drift")
        record["env_cfg"] = env.cfg
        runner = OnPolicyRunner(env, copy.deepcopy(cfg), str(out), device="mps")
        runner.load(str(checkpoint), load_cfg={"actor": True, "critic": True, "optimizer": False, "iteration": False})
        def stop(signum, frame):
            raise KeyboardInterrupt(f"owned standing run interrupted: {signum}")
        signal.signal(signal.SIGINT, stop)
        signal.signal(signal.SIGTERM, stop)
        record["status"] = "running"
        (out/"run.json").write_text(json.dumps(record, indent=2)+"\n")
        runner.learn(num_learning_iterations=a.iterations, init_at_random_ep_len=False)
        if (torch.count_nonzero(env.twist_cmd).item() or torch.count_nonzero(env.head_cmd).item()
                or torch.count_nonzero(env.body_cmd).item() or not torch.isfinite(env.rew_buf).all().item()
                or not torch.isfinite(env.standing_internal_n).all().item()):
            raise ValueError("nonzero standing command or nonfinite final training telemetry")
        final = out/f"model_{runner.current_learning_iteration}.pt"
        record.update(status="completed", checkpoint=final.name, checkpoint_sha256=digest(final),
                      final_zero_commands_verified=True, final_finite_reward_and_internal_load_verified=True)
    except BaseException as exc:
        record.update(status="interrupted" if isinstance(exc, KeyboardInterrupt) else "failed", failure=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        if runner is not None:
            record["new_transitions"] = runner.logger.tot_timesteps
        record["partial_iteration_transitions"] = "unknown" if record["status"] != "completed" else 0
        record["elapsed_s"] = time.monotonic()-started
        (out/"run.json").write_text(json.dumps(record, indent=2)+"\n")
    print(json.dumps({key: record[key] for key in ("status", "elapsed_s", "new_transitions", "checkpoint")}), flush=True)


if __name__ == "__main__":
    main()
