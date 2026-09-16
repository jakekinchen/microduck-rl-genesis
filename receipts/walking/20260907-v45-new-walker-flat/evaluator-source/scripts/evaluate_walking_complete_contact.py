"""Frozen v11 complete-contact development battery, all earlier gates retained."""
import argparse
import json
from pathlib import Path
import shutil
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.evaluate_laser import digest
from scripts.evaluate_walking_sensor import SOURCES as OLD_SOURCES

SOURCES = list(dict.fromkeys(OLD_SOURCES + [
    "scripts/evaluate_walking_complete_contact.py", "experiments/walking/collision_world.py",
    "experiments/walking/collision_model.py", "experiments/walking/self_contact.py",
    "experiments/walking/heading.py", "experiments/walking/HEADING-v1.md",
    "experiments/walking/COLLISION-v11.md", "tests/test_walking_collision_model.py",
    "tests/test_walking_self_contact.py", "experiments/walking/models/contact-v11/robot.xml",
    "experiments/walking/models/contact-v11/scene.xml"]))
FREEZE = ROOT/"experiments/walking/evaluator-freeze-collision-v11.json"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--freeze", action="store_true")
    p.add_argument("--run-id")
    p.add_argument("--baseline", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--video", action="store_true")
    a = p.parse_args()
    if a.freeze:
        with FREEZE.open("x") as f:
            json.dump({"schema": "microduck.walking-evaluator-freeze/v1", "held_out": False,
                       "candidate": "v11 final, training not yet started",
                       "source_sha256": {name: digest(ROOT/name) for name in SOURCES}}, f, indent=2)
            f.write("\n")
        return
    if a.output is None or bool(a.run_id) == bool(a.baseline):
        p.error("one run ID or immutable baseline receipt and a new output required")
    for name, sha in json.loads(FREEZE.read_text())["source_sha256"].items():
        if digest(ROOT/name) != sha:
            raise ValueError(f"evaluator source changed: {name}")
    import numpy as np
    import torch
    import imageio.v2 as imageio
    from PIL import Image, ImageDraw
    from scripts.export_walking import export_walking
    from scripts.evaluate_walking_heading import verify_input_manifest
    from experiments.walking.collision_world import CompleteContactWalkingWorld
    from experiments.walking.self_contact import SelfContactProbe, evaluate_self_contact
    from experiments.walking.heading import evaluate_heading
    from experiments.walking.posture import evaluate_case
    from experiments.laser.gait import GaitProbe
    torch.set_num_threads(1)
    a.output.mkdir(parents=True, exist_ok=False)
    exported, parity = None, None
    if a.run_id:
        policy, parity, exported = export_walking(a.run_id, a.output)
    else:
        verify_input_manifest(a.baseline)
        policy = a.output/"policy.onnx"
        shutil.copy2(a.baseline/"policy.onnx", policy)
        shutil.copy2(a.baseline/"training.json", a.output/"training.json")
    model_directory = ROOT/"experiments/walking/models/contact-v11"
    geometry = SelfContactProbe(model_directory/"scene.xml")
    suite = json.loads((ROOT/"experiments/walking/tracking-suite-v1.json").read_text())
    reports, real_error = [], 0.
    with (a.output/"trajectory.jsonl").open("w") as stream:
        for timing in suite["timing_profiles"]:
            for case in suite["cases"]:
                case_id = f'{timing["id"]}--{case["id"]}'
                world = CompleteContactWalkingWorld(policy, ROOT/".workspace/bam", model_directory=model_directory,
                    motor_ticks=timing["motor_ticks"], sensor_ticks=timing["sensor_ticks"],
                    yaw=case["yaw"], seed=suite["seed"], render=a.video)
                probe, rows, actions = GaitProbe(world.core), [], []
                writer = imageio.get_writer(a.output/f"{case_id}.mp4", fps=25, codec="libx264", quality=7) if a.video else None
                try:
                    for i in range(round(suite["duration_s"]*50)):
                        command = case["command"] if suite["move_start_s"] <= i*.02 < suite["stop_start_s"] else [0, 0, 0]
                        row = probe.sample(world.step_command(command))
                        row.update(case_id=case_id, actor_observation=world.last_observation[0].tolist())
                        if exported is not None:
                            with torch.no_grad():
                                expected = exported(torch.from_numpy(world.last_observation)).numpy()[0]
                            error = float(np.abs(expected-world.last_action).max())
                            if not np.isfinite(error) or error >= 1e-4:
                                raise ValueError("real-observation export parity failed")
                            real_error = max(real_error, error)
                        rows.append(row)
                        actions.append(world.last_action.copy())
                        stream.write(json.dumps(row)+"\n")
                        if writer and i % 2 == 0:
                            frame = Image.fromarray(world.walking_frame())
                            draw = ImageDraw.Draw(frame)
                            draw.rectangle((0, 0, 720, 38), fill=(15, 20, 30))
                            draw.text((10, 8), f"COMPLETE BODY CONTACTS | {case_id} | {row['time_s']:.2f}s", fill="white")
                            writer.append_data(np.asarray(frame))
                        if world.fell:
                            break
                    np.save(a.output/f"{case_id}-actions-float32.npy", np.asarray(actions, np.float32))
                    report = evaluate_case(rows, case, suite)
                    report.update(case_id=case_id, timing_profile=timing["id"],
                                  original_motor_posture_passed=report["passed"],
                                  heading=evaluate_heading(rows), self_contact=evaluate_self_contact(rows, geometry))
                    report["passed"] = report["passed"] and report["heading"]["passed"] and report["self_contact"]["passed"]
                    report["failures"] = list(report["failures"]) + [
                        prefix+reason for prefix, gate in (("heading:", report["heading"]), ("self_contact:", report["self_contact"]))
                        for reason in gate["failures"]]
                    report["gait"]["boundary"] = "Visible-development gait rejection measured in the explicitly versioned complete-contact-v11 model; no calibrated physical acceptance."
                    reports.append(report)
                    print(json.dumps({k: v for k, v in report.items() if k != "gait"}), flush=True)
                finally:
                    if writer:
                        writer.close()
                    world.close()
    result = {"schema": "microduck.walking-evaluation/v1", "acceptance_variant": "complete-contact-heading-self-v11",
              "proof_class": "visible_development", "held_out": False,
              "policy_sha256": digest(policy), "suite_sha256": digest(ROOT/"experiments/walking/tracking-suite-v1.json"),
              "evaluator_freeze_sha256": digest(FREEZE), "passed_cases": sum(c["passed"] for c in reports),
              "total_cases": len(reports), "case_reports": reports, "export_parity": parity,
              "max_real_observation_action_error_rad": real_error if exported is not None else None,
              "physical_transfer_validated": False, "reserved_opened": False,
              "model_scope": {"variant": "complete-contact-v11", "scene_sha256": digest(model_directory/"scene.xml"),
                              "robot_sha256": digest(model_directory/"robot.xml"), "old_reduced_model_acceptance": False},
              "boundary": "Complete-contact-v11 native BAM development battery. All earlier motor/head gates plus unchanged cumulative heading and additive 1-mm self-penetration rejection. Original reduced-model receipts remain separate. No held-out or physical authority."}
    (a.output/"evaluation.json").write_text(json.dumps(result, indent=2)+"\n")
    shutil.copy2(FREEZE, a.output/"evaluator-freeze.json")
    for name in SOURCES:
        dest = a.output/"evaluator-source"/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT/name, dest)
    (a.output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.relative_to(a.output)}\n" for f in sorted(a.output.rglob("*")) if f.is_file()))
    print(f'{result["passed_cases"]}/{len(reports)} complete-contact cases passed', flush=True)


if __name__ == "__main__":
    main()
