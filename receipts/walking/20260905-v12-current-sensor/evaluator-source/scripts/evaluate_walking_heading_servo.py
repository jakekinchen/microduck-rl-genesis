"""Evaluate explicitly assisted COMMAND tracking; raw motor actions unfiltered."""
import argparse
import json
from pathlib import Path
import shutil
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.evaluate_laser import digest
from scripts.evaluate_walking_complete_contact import SOURCES as MODEL_SOURCES

SOURCES = list(dict.fromkeys(MODEL_SOURCES+[
    "scripts/evaluate_walking_heading_servo.py", "experiments/walking/heading_servo_world.py",
    "microduck/heading_servo.py", "tests/test_heading_servo.py", "experiments/walking/HEADING-SERVO-v12.md"]))
FREEZE = ROOT/"experiments/walking/evaluator-freeze-heading-servo-v12.json"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--freeze", action="store_true")
    p.add_argument("--output", type=Path)
    p.add_argument("--video", action="store_true")
    p.add_argument("--fresh", action="store_true", help="separately frozen fresh development bank, only after current bank passes")
    a = p.parse_args()
    if a.freeze:
        with FREEZE.open("x") as f:
            json.dump({"schema": "microduck.walking-evaluator-freeze/v1", "held_out": False,
                "candidate": "fixed v9 FINAL actor plus fixed v12 upstream heading servo, not yet evaluated",
                "source_sha256": {name: digest(ROOT/name) for name in SOURCES}}, f, indent=2)
            f.write("\n")
        return
    if a.output is None:
        p.error("new output required")
    frozen = json.loads(FREEZE.read_text())
    for name, sha in frozen["source_sha256"].items():
        if digest(ROOT/name) != sha:
            raise ValueError(f"controller/evaluator source drift: {name}")
    suite_path = ROOT/"experiments/walking/tracking-suite-v1.json"
    if a.fresh:
        current = ROOT/"receipts/walking/20260905-v12-current-sensor"
        from scripts.evaluate_walking_heading import verify_input_manifest
        verify_input_manifest(current)
        result = json.loads((current/"evaluation.json").read_text())
        if result["passed_cases"] != 21 or result["total_cases"] != 21 or result["evaluator_freeze_sha256"] != digest(FREEZE):
            raise ValueError("all current controller gates required before fresh bank")
        suite_path = ROOT/"experiments/walking/heading-servo-fresh-development-v1.json"
        fresh_freeze = ROOT/"experiments/walking/heading-servo-fresh-freeze-v1.json"
        if digest(suite_path) != json.loads(fresh_freeze.read_text())["suite_sha256"]:
            raise ValueError("fresh development bank changed")
    import numpy as np
    import torch
    import imageio.v2 as imageio
    from PIL import Image, ImageDraw
    from scripts.export_walking import export_walking
    from experiments.walking.heading_servo_world import HeadingServoWalkingWorld
    from experiments.walking.self_contact import SelfContactProbe, evaluate_self_contact
    from experiments.walking.heading import evaluate_heading
    from experiments.walking.posture import evaluate_case
    from experiments.laser.gait import GaitProbe
    torch.set_num_threads(1)
    a.output.mkdir(parents=True, exist_ok=False)
    policy, parity, exported = export_walking("walking-20260905-v9", a.output)
    if digest(policy) != "dc27ad221d2519b40e1c06979d254fdc308a17cc7a8d3ec9592668d6d39e7ab1":
        raise ValueError("actor is not the unchanged v9 FINAL ONNX")
    model_directory = ROOT/"experiments/walking/models/contact-v11"
    geometry = SelfContactProbe(model_directory/"scene.xml")
    suite = json.loads(suite_path.read_text())
    reports, real_error = [], 0.
    with (a.output/"trajectory.jsonl").open("w") as stream:
        for timing in suite["timing_profiles"]:
            for case in suite["cases"]:
                name = f'{timing["id"]}--{case["id"]}'
                world = HeadingServoWalkingWorld(policy, ROOT/".workspace/bam", model_directory=model_directory,
                    motor_ticks=timing["motor_ticks"], sensor_ticks=timing["sensor_ticks"],
                    yaw=case["yaw"], seed=suite["seed"], render=a.video)
                probe, rows, actions = GaitProbe(world.core), [], []
                writer = imageio.get_writer(a.output/f"{name}.mp4", fps=25, codec="libx264", quality=7) if a.video else None
                try:
                    for i in range(round(suite["duration_s"]*50)):
                        requested = case["command"] if suite["move_start_s"] <= i*.02 < suite["stop_start_s"] else [0, 0, 0]
                        row = probe.sample(world.step_command(requested))
                        row.update(case_id=name, actor_observation=world.last_observation[0].tolist())
                        np.testing.assert_array_equal(np.asarray(row["command"], np.float32), np.asarray(requested, np.float32))
                        np.testing.assert_array_equal(np.asarray(row["policy_command"], np.float32), world.last_observation[0, 48:51])
                        with torch.no_grad():
                            expected = exported(torch.from_numpy(world.last_observation)).numpy()[0]
                        error = float(np.abs(expected-world.last_action).max())
                        if not np.isfinite(error) or error >= 1e-4:
                            raise ValueError("real-observation parity failed")
                        real_error = max(real_error, error)
                        rows.append(row)
                        actions.append(world.last_action.copy())
                        stream.write(json.dumps(row)+"\n")
                        if writer and i % 2 == 0:
                            frame = Image.fromarray(world.walking_frame())
                            draw = ImageDraw.Draw(frame)
                            draw.rectangle((0, 0, 720, 38), fill=(15, 20, 30))
                            draw.text((10, 8), f"IMU HEADING COMMAND CONTROL | {name} | {row['time_s']:.2f}s", fill="white")
                            writer.append_data(np.asarray(frame))
                        if world.fell:
                            break
                    np.save(a.output/f"{name}-actions-float32.npy", np.asarray(actions, np.float32))
                    report = evaluate_case(rows, case, suite)
                    report.update(case_id=name, timing_profile=timing["id"], original_motor_posture_passed=report["passed"],
                                  heading=evaluate_heading(rows), self_contact=evaluate_self_contact(rows, geometry))
                    report["passed"] = report["passed"] and report["heading"]["passed"] and report["self_contact"]["passed"]
                    report["failures"] = list(report["failures"])+[prefix+reason
                        for prefix, gate in (("heading:", report["heading"]), ("self_contact:", report["self_contact"]))
                        for reason in gate["failures"]]
                    report["gait"]["boundary"] = "Complete-contact-v11 geometry with explicit v12 IMU heading command controller. Not an unassisted actor pass or physical acceptance."
                    reports.append(report)
                    print(json.dumps({k: v for k, v in report.items() if k != "gait"}), flush=True)
                finally:
                    if writer:
                        writer.close()
                    world.close()
    result = {"schema": "microduck.walking-evaluation/v1", "acceptance_variant": "imu-heading-command-servo-v12",
              "proof_class": "visible_development", "held_out": False, "fresh_development": a.fresh,
              "policy_sha256": digest(policy), "suite_sha256": digest(suite_path),
              "evaluator_freeze_sha256": digest(FREEZE), "passed_cases": sum(c["passed"] for c in reports),
              "total_cases": len(reports), "case_reports": reports, "export_parity": parity,
              "max_real_observation_action_error_rad": real_error,
              "physical_transfer_validated": False, "reserved_opened": False,
              "controller": "explicit upstream IMU heading servo; unchanged v9 actor and raw motor actions",
              "model_scope": {"variant": "complete-contact-v11", "scene_sha256": digest(model_directory/"scene.xml"),
                              "robot_sha256": digest(model_directory/"robot.xml"), "old_reduced_model_acceptance": False},
              "boundary": "All unchanged motor/head/heading/stop gates scored against user-requested commands plus complete body contact rejection. This evaluates v12 command controller plus fixed v9 actor, NOT improved raw-policy tracking, calibrated hardware IMU or physical transfer."}
    for name, sha in frozen["source_sha256"].items():
        if digest(ROOT/name) != sha:
            raise ValueError("source changed during controller evaluation")
    (a.output/"evaluation.json").write_text(json.dumps(result, indent=2)+"\n")
    shutil.copy2(FREEZE, a.output/"evaluator-freeze.json")
    shutil.copy2(suite_path, a.output/"suite.json")
    for name in SOURCES:
        dest = a.output/"evaluator-source"/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT/name, dest)
    (a.output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.relative_to(a.output)}\n" for f in sorted(a.output.rglob("*")) if f.is_file()))
    print(f'{result["passed_cases"]}/{len(reports)} controller-plus-actor cases passed', flush=True)


if __name__ == "__main__":
    main()
