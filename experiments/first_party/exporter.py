"""Fixed-batch exporter for one admitted first-party training receipt."""

from __future__ import annotations

import argparse
import json
import os
import pickle
from pathlib import Path

import genesis as gs
import numpy as np
import onnx
import onnxruntime as ort
import torch
from rsl_rl.runners import OnPolicyRunner

from experiments.first_party.development import validate_export_admission
from export_onnx import ExportedPolicy
from microduck.constants import NUM_ACTIONS, NUM_OBS, OBS_LAYOUT
from microduck.velocity_env import MicroduckVelocityEnv


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log-dir", required=True, type=Path)
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--normalizer-output", required=True, type=Path)
    parser.add_argument("--parity-output", required=True, type=Path)
    parser.add_argument("--admission", required=True, type=Path)
    args = parser.parse_args()
    validate_export_admission(
        args.admission, args.log_dir, args.checkpoint, args.output,
        args.normalizer_output, args.parity_output,
    )
    # The admission authenticates cfgs.pkl before this intentionally trusted
    # first-party pickle or its checkpoint is parsed by Torch.
    with (args.log_dir / "cfgs.pkl").open("rb") as stream:
        saved = pickle.load(stream)
    if saved.get("task") != "walking" or saved.get("rough") or saved.get("backlash"):
        raise RuntimeError("first-party exporter received the wrong training configuration")
    seed = int(saved["train_cfg"]["seed"])
    gs.init(backend=gs.cpu, logging_level="warning", seed=seed)
    env = MicroduckVelocityEnv(num_envs=1, rough=False, backlash=False)
    runner = OnPolicyRunner(env, saved["train_cfg"], os.fspath(args.log_dir), device="cpu")
    runner.load(os.fspath(args.checkpoint), map_location="cpu")
    actor = getattr(runner.alg, "_raw_actor", None) or runner.alg.actor
    exported = ExportedPolicy(actor).to("cpu").eval()
    offset = 0
    layout = []
    for name, size in OBS_LAYOUT:
        layout.append({"name": name, "offset": offset, "size": size})
        offset += size
    args.normalizer_output.write_text(json.dumps({
        "schema_version": "microduck.first-party-normalizer/v1",
        "shape": [1, NUM_OBS], "observation_layout": layout,
        "mean": exported.mean.detach().cpu().reshape(-1).tolist(),
        "std": exported.std.detach().cpu().reshape(-1).tolist(),
        "epsilon": exported.eps,
    }, indent=2, sort_keys=True) + "\n")
    dummy = torch.zeros(1, NUM_OBS)
    torch.onnx.export(
        exported, dummy, args.output, input_names=["obs"], output_names=["action"],
        dynamic_axes=None, opset_version=17,
    )
    model = onnx.load(args.output)
    onnx.save_model(model, args.output, save_as_external_data=False)
    external = Path(os.fspath(args.output) + ".data")
    if external.exists():
        external.unlink()
    session = ort.InferenceSession(os.fspath(args.output), providers=["CPUExecutionProvider"])
    if session.get_inputs()[0].shape != [1, NUM_OBS] or session.get_outputs()[0].shape != [1, NUM_ACTIONS]:
        raise RuntimeError("first-party export is not fixed [1,61] to [1,14]")
    torch.manual_seed(0)
    probe = torch.cat([dummy, torch.randn(32, NUM_OBS)], dim=0)
    with torch.no_grad():
        expected = exported(probe).numpy()
    actual = np.concatenate([
        session.run(None, {"obs": row.numpy()})[0] for row in probe.split(1)
    ], axis=0)
    random_error = float(np.abs(actual - expected).max())
    policy = runner.get_inference_policy(device="cpu")
    obs = env.reset()
    if isinstance(obs, tuple):
        obs = obs[0]
    real_error = 0.0
    seen = []
    with torch.no_grad():
        for _ in range(60):
            vector = obs["policy"]
            torch_action = policy(obs)
            onnx_action = session.run(None, {"obs": vector.cpu().numpy()})[0]
            real_error = max(real_error, float(np.abs(onnx_action - torch_action.cpu().numpy()).max()))
            seen.append(vector.cpu().numpy().copy())
            obs = env.step(torch_action)[0]
    seen_array = np.concatenate(seen, axis=0)
    result = {
        "schema_version": "microduck.first-party-export-parity/v1",
        "fixed_batch": True,
        "random_probe": {
            "seed": 0, "observation_count": 33,
            "max_abs_action_error_rad": random_error,
            "max_action_std_rad": float(actual.std(axis=0).max()),
            "threshold_rad": 1.0e-4, "passed": random_error < 1.0e-4,
        },
        "real_observation_episode": {
            "step_count": 60, "max_abs_action_error_rad": real_error,
            "observation_min": float(seen_array.min()),
            "observation_max": float(seen_array.max()),
            "max_observation_std": float(seen_array.std(axis=0).max()),
            "threshold_rad": 1.0e-4, "passed": real_error < 1.0e-4,
        },
    }
    args.parity_output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    if not result["random_probe"]["passed"] or not result["real_observation_episode"]["passed"]:
        raise RuntimeError("first-party Torch/ONNX parity failed")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
