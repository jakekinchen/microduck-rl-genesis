"""V29 correction-headroom heading on the exposed flat regression."""
import argparse
import json
from pathlib import Path
import shutil
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.evaluate_laser import digest
from scripts.evaluate_walking_standing import SOURCES as PRIOR_SOURCES

SOURCES = list(dict.fromkeys(PRIOR_SOURCES + ["scripts/evaluate_walking_yaw_refinement.py", "scripts/train_walking_yaw_refinement.py", "microduck/walking_yaw_refinement_env.py", "tests/test_walking_yaw_refinement.py", "experiments/walking/YAW-REFINEMENT-v21.md", "microduck/filtered_heading_servo.py", "experiments/walking/filtered_heading_world.py", "tests/test_filtered_heading.py", "scripts/evaluate_walking_unbraced.py",
    "scripts/train_standing.py", "microduck/standing_env.py", "tests/test_standing_reward.py",
    "experiments/walking/STANDING-v15.md", "microduck/walking_unbraced_env.py",
    "scripts/train_walking_unbraced.py", "tests/test_walking_unbraced.py",
    "experiments/walking/UNBRACED-WALKING-v18.md", "experiments/walking/command_ramp.py",
    "tests/test_command_ramp.py"]))
SOURCES = list(dict.fromkeys(SOURCES + ["scripts/evaluate_heading_regression_v24.py", "microduck/persistent_heading_servo_v24.py", "tests/test_persistent_heading_v24.py", "experiments/walking/HEADING-REGRESSION-v24.md", "experiments/walking/tracking-suite-v1.json", "experiments/walking/standing-fresh-development-v1.json", "experiments/walking/standing-fresh-freeze-v1.json"]))
SOURCES = list(dict.fromkeys(SOURCES + ['microduck/motion_heading_servo_v28.py', 'tests/test_motion_heading_v28.py', 'experiments/walking/MOTION-HEADING-v28.md', 'scripts/evaluate_motion_heading_flat_v28.py']))
FREEZE = ROOT/"experiments/walking/heading-headroom-flat-freeze-v29.json"
STAND_SHA = "acab8402e262dbb6af5a3fab9b67fa4ce5e34a4d23cadb127fe6dfa475a70e46"

SOURCES=list(dict.fromkeys(SOURCES+['microduck/heading_headroom_v29.py', 'tests/test_heading_headroom_v29.py', 'experiments/walking/HEADING-HEADROOM-v29.md', 'scripts/evaluate_motion_heading_flat_v28.py', 'scripts/evaluate_heading_headroom_flat_v29.py']))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--freeze", action="store_true")
    p.add_argument("--run-id")
    p.add_argument("--output", type=Path)
    p.add_argument("--video", action="store_true")
    p.add_argument("--fresh", action="store_true")
    a = p.parse_args()
    if a.freeze:
        with FREEZE.open("x") as f:
            json.dump({"schema": "microduck.walking-evaluator-freeze/v1", "held_out": False,
                       "candidate": "V21 FINAL walker, V15 FINAL stander, V16 ramp and fixed V29 heading; exposed regression",
                       "source_sha256": {name: digest(ROOT/name) for name in SOURCES}}, f, indent=2)
            f.write("\n")
        return
    if a.output is None or not a.run_id or not a.run_id.replace("-", "").isalnum():
        p.error("completed V21 run ID and new output required")
    frozen = json.loads(FREEZE.read_text())
    for name, sha in frozen["source_sha256"].items():
        if digest(ROOT/name) != sha:
            raise ValueError(f"frozen source drift: {name}")
    record = json.loads((ROOT/"logs"/a.run_id/"run.json").read_text())
    if (record["status"] != "completed" or record["variant"] != "walking-v21"
            or record["checkpoint"] != "model_249.pt" or record["new_transitions"] != 6_144_000
            or record["args"]["seed"] != 26090621):
        raise ValueError("exact bounded V21 FINAL required")
    suite_path = ROOT/"experiments/walking/tracking-suite-v1.json"
    if a.fresh:
        # This is exposed regression now, not a newly opened or hidden bank.
        suite_path = ROOT/"experiments/walking/standing-fresh-development-v1.json"
        fresh_freeze = ROOT/"experiments/walking/standing-fresh-freeze-v1.json"
        if digest(suite_path) != json.loads(fresh_freeze.read_text())["suite_sha256"]:
            raise ValueError("exposed bank changed")
    import numpy as np
    import torch
    import imageio.v2 as imageio
    from PIL import Image, ImageDraw
    from scripts.export_walking import export_walking
    from experiments.walking.filtered_heading_world import FilteredHeadingWalkingWorld as StandingSwitchWalkingWorld
    from experiments.walking.self_load import record_self_loads, evaluate_self_load
    from experiments.walking.self_contact import SelfContactProbe, evaluate_self_contact
    from microduck.heading_headroom_v29 import HeadingHeadroomServo
    from experiments.walking.heading import evaluate_heading
    from experiments.walking.posture import evaluate_case
    from experiments.laser.gait import GaitProbe
    torch.set_num_threads(1)
    a.output.mkdir(parents=True, exist_ok=False)
    (a.output/"standing").mkdir()
    walk, walk_parity, walk_export = export_walking(a.run_id, a.output)
    stand, stand_parity, stand_export = export_walking("standing-20260906-v15", a.output/"standing")
    if json.loads((a.output/"training.json").read_text())["checkpoint_sha256"] != record["checkpoint_sha256"]:
        raise ValueError("walking component changed")
    if json.loads((a.output/"standing/training.json").read_text())["checkpoint_sha256"] != STAND_SHA:
        raise ValueError("fixed standing component changed")
    model_dir = ROOT/"experiments/walking/models/contact-v11"
    geometry = SelfContactProbe(model_dir/"scene.xml")
    suite = json.loads(suite_path.read_text())
    repeats = suite.get("repeated_windows", 1)
    if type(repeats) is not int or not 1 <= repeats <= 3 or (not a.fresh and repeats != 1):
        raise ValueError("one current window or at most three predeclared fresh windows")
    reports, errors = [], {"walking": 0., "standing": 0.}
    with (a.output/"trajectory.jsonl").open("w") as stream:
        for timing in suite["timing_profiles"]:
            for case in suite["cases"]:
                base = f'{timing["id"]}--{case["id"]}'
                world = StandingSwitchWalkingWorld(walk, ROOT/".workspace/bam", standing_policy=stand,
                    model_directory=model_dir, motor_ticks=timing["motor_ticks"], sensor_ticks=timing["sensor_ticks"],
                    yaw=case["yaw"], seed=suite["seed"], render=a.video)
                world.heading_servo = HeadingHeadroomServo()
                probe = GaitProbe(world.core)
                try:
                    with record_self_loads(world) as all_loads:
                        for repeat in range(repeats):
                            name = base if repeats == 1 else f"{base}--repeat-{repeat+1}"
                            rows, actions, offset = [], [], repeat*suite["duration_s"]
                            start_load = len(all_loads)
                            writer = imageio.get_writer(a.output/f"{name}.mp4", fps=25, codec="libx264", quality=7) if a.video else None
                            try:
                                for i in range(round(suite["duration_s"]*50)):
                                    if world.fell:
                                        break
                                    requested = case["command"] if suite["move_start_s"] <= i*.02 < suite["stop_start_s"] else [0,0,0]
                                    row = probe.sample(world.step_command(requested))
                                    role = row["actor_mode"]
                                    # Relative scoring window; actual continuous world time remains recorded.
                                    row.update(case_id=name, session_time_s=row["time_s"], time_s=(i+1)*.02,
                                               actor_observation=world.last_observation[0].tolist(),
                                               self_load_physics=[{**s, "interval_start_s": (start_load+i*4+j)*.005-offset}
                                                                  for j,s in enumerate(all_loads[-4:])])
                                    np.testing.assert_array_equal(np.asarray(row["command"], np.float32), np.asarray(requested, np.float32))
                                    np.testing.assert_array_equal(np.asarray(row["policy_command"], np.float32), world.last_observation[0,48:51])
                                    with torch.no_grad():
                                        expected = (stand_export if role == "standing" else walk_export)(torch.from_numpy(world.last_observation)).numpy()[0]
                                    error = float(np.abs(expected-world.last_action).max())
                                    if not np.isfinite(error) or error >= 1e-4:
                                        raise ValueError("selected actor parity failed")
                                    errors[role] = max(errors[role], error)
                                    rows.append(row)
                                    actions.append(world.last_action.copy())
                                    stream.write(json.dumps(row)+"\n")
                                    if writer and i%2 == 0:
                                        frame = Image.fromarray(world.walking_frame())
                                        draw = ImageDraw.Draw(frame)
                                        draw.rectangle((0,0,720,38), fill=(15,20,30))
                                        draw.text((10,8), f"V29 {role.upper()} | {name} | {row['session_time_s']:.2f}s", fill="white")
                                        writer.append_data(np.asarray(frame))
                                np.save(a.output/f"{name}-actions-float32.npy", np.asarray(actions, np.float32).reshape(-1,14))
                                if not rows:
                                    # A previous terminal fall makes later windows unknown; never reset or omit them.
                                    report = {"case_id": name, "passed": False, "failures": ["not_run_after_terminal_fall"],
                                              "original_motor_posture_passed": False, "motor_battery_passed": False,
                                              "posture": {"passed": False}, "gait": {"fell": True}, "metrics": {}}
                                    for key in ("heading", "self_contact", "self_load"):
                                        report[key] = {"passed": False, "failures": ["missing_evidence"]}
                                else:
                                    report = evaluate_case(rows, case, suite)
                                    report.update(original_motor_posture_passed=report["passed"], heading=evaluate_heading(rows),
                                                  self_contact=evaluate_self_contact(rows, geometry),
                                                  self_load=evaluate_self_load([s for row in rows for s in row["self_load_physics"]], suite["duration_s"]))
                                    for key in ("heading", "self_contact", "self_load"):
                                        report["passed"] = report["passed"] and report[key]["passed"]
                                        report["failures"] += [key+":"+reason for reason in report[key]["failures"]]
                                report.update(case_id=name, timing_profile=timing["id"], repeated_window=repeat+1, session_window_start_s=offset)
                                reports.append(report)
                                print(json.dumps({"case_id": name, "passed": report["passed"], "failures": report["failures"], "metrics": report["metrics"]}), flush=True)
                            finally:
                                if writer:
                                    writer.close()
                finally:
                    world.close()
    result = {"schema": "microduck.walking-evaluation/v1", "acceptance_variant": "heading-headroom-v29-flat-regression",
              "proof_class": "visible_development", "held_out": False, "fresh_development": False, "exposed_repeated_bank": a.fresh,
              "policy_sha256": digest(walk), "standing_policy_sha256": digest(stand), "standing_policy_used": True,
              "suite_sha256": digest(suite_path), "evaluator_freeze_sha256": digest(FREEZE),
              "passed_cases": sum(c["passed"] for c in reports), "total_cases": len(reports), "case_reports": reports,
              "export_parity": {"walking": walk_parity, "standing": stand_parity},
              "max_real_observation_action_error_rad": max(errors.values()), "component_real_observation_error_rad": errors,
              "physical_transfer_validated": False, "reserved_opened": False,
              "controller": "Fixed V16 command slew and V29 correction-headroom persistent-reference filtered IMU feedback; V21 FINAL walking / V15 FINAL standing; exact-zero ramped-command routing",
              "model_scope": {"variant": "complete-contact-v11", "scene_sha256": digest(model_dir/"scene.xml"),
                              "robot_sha256": digest(model_dir/"robot.xml"), "old_reduced_model_acceptance": False},
              "boundary": "Unchanged motor/head/heading/geometry/internal-load gates. Explicit command-selected pair, unfiltered actions; repeated windows preserve full physical/action/controller history. Visible simulation development, not physical acceptance."}
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
