"""Offline RGB/timestamp and ONNX-byte replay of retained visual-follow cases.

The replay consumes no target/root coordinates, simulator or depth data.
Its trace reader whitelists commands, actor fields and load sample counts.
"""
import argparse
from dataclasses import asdict
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import onnxruntime as ort

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/"receipts/walking/20260906-v30-flat-regression"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_detector(path, index):
    name = f"visual_follow_frozen_perception_{index}"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def read_control_evidence(path):
    # Do not forward the general trajectory dictionary to the RGB replayer.
    # Position, target, route and all other fields are deliberately excluded.
    allowed = ("control_time_s", "pixel_command", "actor_mode", "actor_observation", "action_rad", "physics_samples")
    with gzip.open(path, "rt") as stream:
        return [{key: record[key] for key in allowed} for record in map(json.loads, stream)]


def verify_case(path, index):
    manifest_paths = []
    for line in (path/"SHA256SUMS").read_text().splitlines():
        expected, relative = line.split(maxsplit=1)
        candidate = (path/relative).resolve()
        if not candidate.is_relative_to(path.resolve()) or sha(candidate) != expected:
            raise ValueError("manifest mismatch: "+str(candidate))
        manifest_paths.append(relative)
    result = json.loads((path/"evaluation.json").read_text())
    freeze = json.loads((path/"freeze.json").read_text())
    if sha(path/"freeze.json") != result["source_freeze_sha256"]:
        raise ValueError("evaluation freeze binding mismatch")
    for relative, expected in freeze["source_sha256"].items():
        if sha(path/"source"/relative) != expected:
            raise ValueError("frozen source mismatch: "+relative)
    for relative, expected in freeze["asset_sha256"].items():
        if sha(ROOT/relative) != expected:
            raise ValueError("asset changed: "+relative)
    for name, expected in freeze["materialized_model_sha256"].items():
        if sha(path/"model"/name) != expected:
            raise ValueError("materialized model changed")
    module_path = path/"source/experiments/visual-follow-v1/perception.py"
    module = load_detector(module_path, index)
    protocol = json.loads((path/"source/experiments/visual-follow-v1/protocol.json").read_text())
    camera, follower = module.Camera(**protocol["camera"]), module.Follower()
    control = read_control_evidence(path/"trajectory.jsonl.gz")
    metadata = json.loads((path/"camera-frames.json").read_text())
    rgb = np.load(path/"camera-frames.npz")["rgb"]
    if len(rgb) != len(metadata):
        raise ValueError("RGB/timestamp length mismatch")
    case = result["case"]
    frame_index = 0
    reconstructed = []
    for index, row in enumerate(control):
        t = index*.02
        if row["control_time_s"] != t:
            raise ValueError("irregular control timestamps")
        receiving = index % 5 == 0 and not (case["fault"] == "camera-drop" and 10 <= t < 13)
        if receiving:
            frame = metadata[frame_index]
            expected_capture = 9.9 if case["fault"] == "camera-stale" and 10 <= t < 13 else t
            expected_sequence = 99 if case["fault"] == "camera-stale" and 10 <= t < 13 else index//5
            if frame["received_s"] != t or frame["captured_s"] != expected_capture or frame["sequence"] != expected_sequence:
                raise ValueError("capture/drop/stale scheduling mismatch")
            pixels = rgb[frame_index]
            if hashlib.sha256(pixels.tobytes()).hexdigest() != frame["rgb_sha256"]:
                raise ValueError("RGB byte binding mismatch")
            detection = module.detect(pixels, camera)
            if json.loads(json.dumps(asdict(detection))) != frame["detection"]:
                raise ValueError("RGB-derived detection differs from recorded result")
            follower.ingest(detection, frame["captured_s"], frame["sequence"], frame["received_s"])
            frame_index += 1
        command = follower.command(t)
        if case["fault"] == "negative-control":
            command[:] = 0
        expected = np.asarray(row["pixel_command"], np.float32)
        if expected.tobytes() != command.tobytes():
            raise ValueError(f"RGB-only command byte mismatch at control {index}")
        reconstructed.append(command)
    if frame_index != len(metadata):
        raise ValueError("unused or unexpected camera frames")
    motion = np.load(path/"motion.npz")
    actions, observations = motion["actions"], motion["observations"]
    if actions.shape != (len(control), 14) or observations.shape != (len(control), 61):
        raise ValueError("actor array dimensions mismatch")
    if actions.dtype != np.float32 or observations.dtype != np.float32:
        raise ValueError("actor arrays must retain float32 bytes")
    options = ort.SessionOptions()
    options.intra_op_num_threads = 1
    options.inter_op_num_threads = 1
    options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    sessions = {}
    for role, relative in (("walking", "policy.onnx"), ("standing", "standing/policy.onnx")):
        if sha(SOURCE/relative) != freeze["actors"][relative]:
            raise ValueError("actor digest mismatch")
        sessions[role] = ort.InferenceSession(str(SOURCE/relative), sess_options=options, providers=["CPUExecutionProvider"])
    for index, row in enumerate(control):
        if observations[index].tobytes() != np.asarray(row["actor_observation"], np.float32).tobytes():
            raise ValueError("stored actor observation mismatch")
        if actions[index].tobytes() != np.asarray(row["action_rad"], np.float32).tobytes():
            raise ValueError("stored actor action mismatch")
        session = sessions[row["actor_mode"]]
        action = session.run(None, {session.get_inputs()[0].name: observations[index:index+1]})[0]
        if action[0].tobytes() != actions[index].tobytes():
            raise ValueError("independent ONNX action byte mismatch")
        samples = row["physics_samples"]
        if len(samples) != 4:
            raise ValueError("incomplete physics-rate load evidence")
        for substep, sample in enumerate(samples):
            if abs(sample["interval_start_s"]-(index*4+substep)*.005) > 1e-9:
                raise ValueError("irregular physics-rate load axis")
    return {"case": case["id"], "repeat": case["repeat"], "evaluation_passed": result["passed"],
            "evaluation_failures": result["failures"], "complete": result["complete"],
            "manifest_files_verified": len(manifest_paths), "rgb_frames_replayed": len(rgb),
            "float32_pixel_commands_exact": len(control), "float32_onnx_rows_exact": len(control),
            "physics_load_samples": 4*len(control), "source_freeze_sha256": sha(path/"freeze.json"),
            "perception_source_sha256": sha(module_path), "evaluation_sha256": sha(path/"evaluation.json"),
            "replayed_command_sha256": hashlib.sha256(np.asarray(reconstructed, np.float32).tobytes()).hexdigest(),
            "replay_inputs": ["RGB", "capture_time", "receive_time", "frame_sequence", "fixed_camera_intrinsics_and_marker_size", "negative_control_flag"]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("fresh verification output required")
    bank_path = args.receipt/"bank.json"
    cases = sorted(p.parent for p in args.receipt.glob("*/evaluation.json")) if bank_path.exists() else [args.receipt]
    records = []
    for index, path in enumerate(cases):
        record = verify_case(path, index)
        records.append(record)
        print(json.dumps({key: record[key] for key in ("case", "repeat", "float32_pixel_commands_exact", "float32_onnx_rows_exact", "evaluation_passed")}), flush=True)
    if bank_path.exists():
        bank = json.loads(bank_path.read_text())
        for relative, expected in bank["result_sha256"].items():
            if sha(args.receipt/relative) != expected:
                raise ValueError("bank result changed")
        if len(records) != len(bank["result_sha256"]):
            raise ValueError("bank case count mismatch")
    output = {"schema": "microduck.visual-follow-offline-verification/v1", "complete": True,
              "source_receipt": str(args.receipt.resolve()), "verification_source_sha256": sha(Path(__file__)),
              "cases": records, "totals": {key: sum(r[key] for r in records) for key in
                 ("manifest_files_verified", "rgb_frames_replayed", "float32_pixel_commands_exact", "float32_onnx_rows_exact", "physics_load_samples")},
              "boundary": "Independent offline pixels/timestamps and actor inference replay. Does not simulate or establish behavior acceptance, sensor calibration or physical transfer."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2)+"\n")
    args.output.with_suffix(".py").write_bytes(Path(__file__).read_bytes())
    print(json.dumps(output["totals"]), flush=True)


if __name__ == "__main__":
    main()
