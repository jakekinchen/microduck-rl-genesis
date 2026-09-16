"""Frozen V14 standing/walking pair and unchanged V13 baseline, additive load gate."""
import argparse
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.evaluate_laser import digest
from scripts.evaluate_walking_persistent_controller import SOURCES as PREVIOUS_SOURCES

SOURCES = list(dict.fromkeys(PREVIOUS_SOURCES + [
    "scripts/evaluate_walking_standing.py", "experiments/walking/STAND-SWITCH-v14.md",
    "experiments/walking/standing_world.py", "experiments/walking/self_load.py",
    "tests/test_walking_standing.py"]))
FREEZE = ROOT / "experiments/walking/evaluator-freeze-standing-v14.json"
RUNS = {"walking": ("walking-20260905-v13", "f31d47a5343b1283a1bbd28c2f7efb78f95ddd6940554b9c755b73d337c2b7f8"),
        "standing": ("walking-20260905-v5", "19fef3b5d443001f817169cecc660a2bef51b34791b5d84dfa59cc4e619a43c1")}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--freeze", action="store_true")
    p.add_argument("--baseline", action="store_true", help="unchanged V13 actor in both command modes")
    p.add_argument("--output", type=Path)
    p.add_argument("--video", action="store_true")
    a = p.parse_args()
    if a.freeze:
        with FREEZE.open("x") as f:
            json.dump({"schema": "microduck.walking-evaluator-freeze/v1", "held_out": False,
                       "candidate": "Fixed V5 FINAL standing / V13 FINAL walking pair, never yet run",
                       "runs": RUNS, "source_sha256": {name: digest(ROOT/name) for name in SOURCES}}, f, indent=2)
            f.write("\n")
        return
    if a.output is None:
        p.error("new output required")
    frozen = json.loads(FREEZE.read_text())
    for name, sha in frozen["source_sha256"].items():
        if digest(ROOT/name) != sha:
            raise ValueError(f"frozen source drift: {name}")
    import numpy as np
    import torch
    import imageio.v2 as imageio
    from PIL import Image, ImageDraw
    from scripts.export_walking import export_walking
    from experiments.walking.standing_world import StandingSwitchWalkingWorld
    from experiments.walking.heading_servo_world import HeadingServoWalkingWorld
    from experiments.walking.self_load import record_self_loads, evaluate_self_load
    from experiments.walking.self_contact import SelfContactProbe, evaluate_self_contact
    from experiments.walking.heading import evaluate_heading
    from experiments.walking.posture import evaluate_case
    from experiments.laser.gait import GaitProbe
    torch.set_num_threads(1)
    a.output.mkdir(parents=True, exist_ok=False)
    exports, policies, parities = {}, {}, {}
    for role, (run, sha) in RUNS.items():
        dest = a.output if role == "walking" else a.output/role
        dest.mkdir(parents=True, exist_ok=True)
        policies[role], parities[role], exports[role] = export_walking(run, dest)
        training = json.loads((dest/"training.json").read_text())
        if training["checkpoint_sha256"] != sha or training["checkpoint"] != "model_749.pt":
            raise ValueError("exact predeclared FINAL component required")
    model_dir = ROOT/"experiments/walking/models/contact-v11"
    suite_path = ROOT/"experiments/walking/tracking-suite-v1.json"
    suite = json.loads(suite_path.read_text())
    geometry = SelfContactProbe(model_dir/"scene.xml")
    reports, real_error = [], {"walking": 0., "standing": 0.}
    with (a.output/"trajectory.jsonl").open("w") as stream:
        for timing in suite["timing_profiles"]:
            for case in suite["cases"]:
                name = f'{timing["id"]}--{case["id"]}'
                kwargs = {} if a.baseline else {"standing_policy": policies["standing"]}
                cls = HeadingServoWalkingWorld if a.baseline else StandingSwitchWalkingWorld
                world = cls(policies["walking"], ROOT/".workspace/bam", model_directory=model_dir,
                            motor_ticks=timing["motor_ticks"], sensor_ticks=timing["sensor_ticks"],
                            yaw=case["yaw"], seed=suite["seed"], render=a.video, **kwargs)
                probe, rows, actions = GaitProbe(world.core), [], []
                writer = imageio.get_writer(a.output/f"{name}.mp4", fps=25, codec="libx264", quality=7) if a.video else None
                try:
                    with record_self_loads(world) as loads:
                        for i in range(round(suite["duration_s"]*50)):
                            requested = case["command"] if suite["move_start_s"] <= i*.02 < suite["stop_start_s"] else [0, 0, 0]
                            row = probe.sample(world.step_command(requested))
                            role = "walking" if a.baseline else row["actor_mode"]
                            row.update(case_id=name, actor_mode=role,
                                       actor_observation=world.last_observation[0].tolist(), self_load_physics=loads[-4:])
                            np.testing.assert_array_equal(np.asarray(row["command"], np.float32), np.asarray(requested, np.float32))
                            np.testing.assert_array_equal(np.asarray(row["policy_command"], np.float32), world.last_observation[0,48:51])
                            with torch.no_grad():
                                expected = exports[role](torch.from_numpy(world.last_observation)).numpy()[0]
                            error = float(np.abs(expected-world.last_action).max())
                            if not np.isfinite(error) or error >= 1e-4:
                                raise ValueError("selected actor real-observation parity failed")
                            real_error[role] = max(real_error[role], error)
                            rows.append(row)
                            actions.append(world.last_action.copy())
                            stream.write(json.dumps(row)+"\n")
                            if writer and i % 2 == 0:
                                frame = Image.fromarray(world.walking_frame())
                                draw = ImageDraw.Draw(frame)
                                draw.rectangle((0, 0, 720, 38), fill=(15, 20, 30))
                                draw.text((10, 8), f"V14 {role.upper()} | {name} | {row['time_s']:.2f}s", fill="white")
                                writer.append_data(np.asarray(frame))
                            if world.fell:
                                break
                    if len(loads) != len(rows)*4:
                        raise ValueError("missing physics-rate load samples")
                    np.save(a.output/f"{name}-actions-float32.npy", np.asarray(actions, np.float32))
                    report = evaluate_case(rows, case, suite)
                    report.update(case_id=name, timing_profile=timing["id"], original_motor_posture_passed=report["passed"],
                                  heading=evaluate_heading(rows), self_contact=evaluate_self_contact(rows, geometry),
                                  self_load=evaluate_self_load(loads, suite["duration_s"]))
                    for key in ("heading", "self_contact", "self_load"):
                        report["passed"] = report["passed"] and report[key]["passed"]
                        report["failures"] += [key+":"+reason for reason in report[key]["failures"]]
                    report["gait"]["boundary"] = "Fixed V14 command-selected ONNX pair, complete-contact-v11 and applied internal-load gate; visible development only."
                    reports.append(report)
                    print(json.dumps({"case_id": name, "passed": report["passed"], "failures": report["failures"],
                                      "self_load": report["self_load"]}), flush=True)
                finally:
                    if writer:
                        writer.close()
                    world.close()
    result = {"schema": "microduck.walking-evaluation/v1", "acceptance_variant": "command-stand-switch-v14" if not a.baseline else "self-load-v14-v13-baseline",
              "proof_class": "visible_development", "held_out": False, "fresh_development": False,
              "policy_sha256": digest(policies["walking"]), "standing_policy_sha256": digest(policies["standing"]),
              "standing_policy_used": not a.baseline, "suite_sha256": digest(suite_path),
              "evaluator_freeze_sha256": digest(FREEZE), "passed_cases": sum(c["passed"] for c in reports),
              "total_cases": len(reports), "case_reports": reports, "export_parity": parities,
              "max_real_observation_action_error_rad": max(real_error.values()), "component_real_observation_error_rad": real_error,
              "physical_transfer_validated": False, "reserved_opened": False,
              "controller": "Fixed v12 IMU command servo; exact-zero user command selects V5 standing, otherwise V13 walking" if not a.baseline else "Unchanged V13 plus V12 heading servo, additive load gate only",
              "model_scope": {"variant": "complete-contact-v11", "scene_sha256": digest(model_dir/"scene.xml"),
                              "robot_sha256": digest(model_dir/"robot.xml"), "old_reduced_model_acceptance": False},
              "boundary": "Every original motor/posture/heading/geometry gate AND full 200-Hz internal-load gate. No action filtering, blending, offsets or physical acceptance."}
    for name, sha in frozen["source_sha256"].items():
        if digest(ROOT/name) != sha:
            raise ValueError("source changed during evaluation")
    (a.output/"evaluation.json").write_text(json.dumps(result, indent=2)+"\n")
    shutil.copy2(FREEZE, a.output/"evaluator-freeze.json")
    shutil.copy2(suite_path, a.output/"suite.json")
    for name in SOURCES:
        dest = a.output/"evaluator-source"/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT/name, dest)
    (a.output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.relative_to(a.output)}\n" for f in sorted(a.output.rglob("*")) if f.is_file()))
    print(f'{result["passed_cases"]}/{len(reports)} all-gate cases passed', flush=True)


if __name__ == "__main__":
    main()
