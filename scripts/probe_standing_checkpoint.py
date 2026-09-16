"""Three deterministic V15 standing-component diagnostics, never selection."""
import argparse
import copy
import json
from pathlib import Path
import shutil
import sys
import time
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.evaluate_laser import digest


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run-id", required=True)
    p.add_argument("--iteration", type=int, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if not a.run_id.replace("-", "").isalnum() or a.iteration < 0:
        p.error("simple run ID and nonnegative iteration required")
    run = ROOT/"logs"/a.run_id
    record = json.loads((run/"run.json").read_text())
    checkpoint = run/f"model_{a.iteration}.pt"
    sha = digest(checkpoint)
    from scripts.evaluate_walking_standing_trained import FREEZE
    from scripts.evaluate_walking_heading import verify_input_manifest
    sources = {**record["source_sha256"], **json.loads(FREEZE.read_text())["source_sha256"],
               "scripts/probe_standing_checkpoint.py": digest(Path(__file__))}
    if record["variant"] != "standing-v15":
        raise ValueError("standing-only V15 diagnostic required")
    for name, expected in sources.items():
        if digest(ROOT/name) != expected:
            raise ValueError("source drift")
    baseline = ROOT/"receipts/walking/20260906-v14-standing-pair"
    verify_input_manifest(baseline)
    import numpy as np
    import torch
    from tensordict import TensorDict
    from rsl_rl.models import MLPModel
    from export_onnx import ExportedPolicy
    from experiments.walking.standing_world import StandingSwitchWalkingWorld
    from experiments.walking.posture import evaluate_case
    from experiments.walking.heading import evaluate_heading
    from experiments.walking.self_contact import SelfContactProbe, evaluate_self_contact
    from experiments.walking.self_load import record_self_loads, evaluate_self_load
    from experiments.laser.gait import GaitProbe
    torch.set_num_threads(1)
    cfg = copy.deepcopy(record["train_cfg"])
    cfg["actor"].pop("class_name")
    actor = MLPModel(TensorDict({"policy": torch.zeros(1,61)},[1]), cfg["obs_groups"], "actor",14,**cfg["actor"])
    actor.load_state_dict(torch.load(checkpoint,map_location="cpu",weights_only=True)["actor_state_dict"])
    policy = ExportedPolicy(actor.eval()).eval()
    class TorchPolicy:
        def infer(self, obs):
            started = time.monotonic()
            with torch.no_grad():
                actions = policy(torch.from_numpy(obs)).numpy()
            return actions, (time.monotonic()-started)*1000
    a.output.mkdir(parents=True,exist_ok=False)
    suite = json.loads((baseline/"suite.json").read_text())
    model = ROOT/"experiments/walking/models/contact-v11"
    geometry = SelfContactProbe(model/"scene.xml")
    reports = []
    with (a.output/"trajectory.jsonl").open("w") as stream:
        for name in ("nominal-20-20ms--forward-08", "long-30-20ms--forward-20", "long-30-20ms--arc-right"):
            timing_id, case_id = name.split("--")
            timing = next(t for t in suite["timing_profiles"] if t["id"] == timing_id)
            case = next(c for c in suite["cases"] if c["id"] == case_id)
            world = StandingSwitchWalkingWorld(baseline/"policy.onnx", ROOT/".workspace/bam",
                standing_policy=baseline/"standing/policy.onnx", model_directory=model,
                motor_ticks=timing["motor_ticks"], sensor_ticks=timing["sensor_ticks"], yaw=case["yaw"],seed=suite["seed"])
            world.standing_policy = TorchPolicy()
            probe, rows, actions = GaitProbe(world.core),[],[]
            try:
                with record_self_loads(world) as loads:
                    for i in range(900):
                        requested = case["command"] if 1 <= i*.02 < 13 else [0,0,0]
                        row = probe.sample(world.step_command(requested))
                        row.update(case_id=name,actor_observation=world.last_observation[0].tolist(),self_load_physics=loads[-4:])
                        rows.append(row)
                        actions.append(world.last_action.copy())
                        stream.write(json.dumps(row)+"\n")
                        if world.fell:
                            break
                report = evaluate_case(rows,case,suite)
                report.update(case_id=name, heading=evaluate_heading(rows), self_contact=evaluate_self_contact(rows,geometry),
                              self_load=evaluate_self_load(loads))
                report["combined_passed"] = report["passed"] and all(report[k]["passed"] for k in ("heading","self_contact","self_load"))
                reports.append(report)
                np.save(a.output/f"{name}-actions-float32.npy",np.asarray(actions,np.float32))
                print(json.dumps({k:v for k,v in report.items() if k != "gait"}),flush=True)
            finally:
                world.close()
    if digest(checkpoint) != sha:
        raise ValueError("checkpoint changed")
    for name, expected in sources.items():
        if digest(ROOT/name) != expected:
            raise ValueError("source changed")
        dest = a.output/"source"/name
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(ROOT/name,dest)
    result = {"schema": "microduck.standing-intermediate-diagnostic/v1", "iteration":a.iteration,
              "checkpoint_sha256":sha,"case_reports":reports,"combined_passed_cases":sum(c["combined_passed"] for c in reports),
              "total_cases":3,"candidate_selection_eligible":False,"source_sha256":sources,
              "baseline_manifest_sha256":digest(baseline/"SHA256SUMS"),"evaluator_freeze_sha256":digest(FREEZE),
              "physical_transfer_validated":False,"held_out":False,
              "boundary":"Fixed V13 ONNX walking plus intermediate V15 normalized Torch standing; three diagnostic cases only, not final ONNX acceptance or checkpoint selection."}
    (a.output/"probe.json").write_text(json.dumps(result,indent=2)+"\n")
    (a.output/"training-at-probe.json").write_text(json.dumps(record,indent=2)+"\n")
    shutil.copy2(checkpoint,a.output/"source-checkpoint.pt")
    (a.output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.relative_to(a.output)}\n" for f in sorted(a.output.rglob("*")) if f.is_file()))


if __name__ == "__main__":
    main()
