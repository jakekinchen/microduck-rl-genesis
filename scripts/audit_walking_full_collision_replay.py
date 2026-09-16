"""Same raw motor actions, native reduced/full CAD collision models.

This is an explicitly alternate-model diagnostic. It cannot inherit the frozen
walking model's acceptance or authority metadata from the core used to wire BAM.
"""
import argparse
import json
from pathlib import Path
import shutil
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--receipt", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    import numpy as np
    import mujoco
    from experiments.walking.sensor_world import ConsistentSensorWalkingWorld
    from experiments.laser.gait import GaitProbe
    from experiments.laser.camera_alignment import align_head_camera
    from scripts.evaluate_laser import digest
    from scripts.evaluate_walking_heading import verify_input_manifest
    verify_input_manifest(a.receipt)
    parent = json.loads((a.receipt / "evaluation.json").read_text())
    parent_cases = {case["case_id"]: case for case in parent["case_reports"]}
    a.output.mkdir(parents=True, exist_ok=False)
    suite = json.loads((ROOT/"experiments/walking/tracking-suite-v1.json").read_text())
    results = []
    checked_fields = ("jnt_qposadr", "jnt_range", "jnt_axis", "jnt_pos", "body_mass", "body_inertia", "body_ipos", "body_iquat", "body_pos", "body_quat", "dof_damping", "dof_armature")
    for case in (suite["cases"][0], suite["cases"][3]):
        name = "nominal-20-20ms--"+case["id"]
        action_path = a.receipt/f"{name}-actions-float32.npy"
        actions = np.load(action_path, allow_pickle=False)
        if (actions.dtype != np.float32 or actions.ndim != 2 or actions.shape[1] != 14
                or not 1 <= len(actions) <= 900 or not np.isfinite(actions).all()):
            raise ValueError("bounded original raw float32 action trace required")
        if len(actions) < 900 and (parent_cases[name]["passed"] is not False or parent_cases[name]["gait"]["fell"] is not True):
            raise ValueError("a partial action trace requires a recorded terminal fall")
        pair = {}
        for full in (False, True):
            tag = "full-collision" if full else "reduced-reference"
            world = ConsistentSensorWalkingWorld(a.receipt/"policy.onnx", ROOT/".workspace/bam", yaw=case["yaw"], seed=suite["seed"])
            c = world.core
            if full:
                raw_reference = mujoco.MjModel.from_xml_path(str(ROOT/"microduck/assets/microduck/scene_walk.xml"))
                alternate = mujoco.MjModel.from_xml_path(str(ROOT/"microduck/assets/microduck/scene.xml"))
                for field in checked_fields:
                    if not np.array_equal(getattr(raw_reference, field), getattr(alternate, field)):
                        raise ValueError(f"alternate model changes {field}")
                configured = {field: getattr(c.model, field).copy() for field in ("dof_armature", "dof_damping")}
                # Explicit alternate-model diagnostic, not validation under the
                # reduced reference model lock. No authoritative core report is
                # emitted; actual model and source identities are recorded below.
                c.model = alternate
                c.data = mujoco.MjData(alternate)
                c._validate_model()
                c._configure_torque_actuators()
                c.controller = c._build_bam_controller(ROOT/".workspace/bam")
                for field, expected in configured.items():
                    if not np.array_equal(getattr(c.model, field), expected):
                        raise ValueError(f"BAM-configured alternate model changes {field}")
                align_head_camera(c.model)
                world.sensor_data = mujoco.MjData(c.model)
                c.reset([0., 0., .125], [np.cos(case["yaw"]/2), 0., 0., np.sin(case["yaw"]/2)])
            probe = GaitProbe(c)
            rows, pairs = [], {}
            try:
                for i, action in enumerate(actions):
                    command = case["command"] if 1 <= i*.02 < 13 else [0., 0., 0.]
                    row = probe.sample(world.step_command(command, action_override=action))
                    if world.last_action.tobytes() != action.tobytes():
                        raise ValueError("replay changed action bytes")
                    for con in c.data.contact:
                        geoms = [int(con.geom1), int(con.geom2)]
                        bodies = [c.model.body(int(c.model.geom_bodyid[g])).name for g in geoms]
                        is_floor = [c.model.geom(g).name == "floor" for g in geoms]
                        if any(is_floor):
                            robot_geom = geoms[0] if not is_floor[0] else geoms[1]
                            if c.model.geom(robot_geom).name in ("left_foot_collision", "right_foot_collision"):
                                continue
                        key = " / ".join(sorted(bodies))
                        stats = pairs.setdefault(key, {"contact_samples": 0, "minimum_distance_m": 1.})
                        stats["contact_samples"] += 1
                        stats["minimum_distance_m"] = min(stats["minimum_distance_m"], float(con.dist))
                    rows.append(row)
                    if world.fell:
                        break
                (a.output/f"{name}-{tag}.jsonl").write_text("".join(json.dumps(r)+"\n" for r in rows))
                pair[tag] = {"rows": rows, "additional_contact_pairs": pairs, "fell": world.fell}
            finally:
                world.close()
        old, new = pair["reduced-reference"], pair["full-collision"]
        count = min(len(old["rows"]), len(new["rows"]))
        q0 = np.asarray([r["qpos"] for r in old["rows"][:count]])
        q1 = np.asarray([r["qpos"] for r in new["rows"][:count]])
        result = {"case_id": name, "action_sha256": digest(action_path), "identical_input_action_bytes": True,
            "scheduled_frames": 900, "original_action_frames": len(actions),
            "complete_original_rollout": len(actions) == 900,
            "original_reported_passed": parent_cases[name]["passed"],
            "compared_frames": count, "max_qpos_difference": float(np.abs(q0-q1).max()),
            "qpos_byte_identical": q0.tobytes() == q1.tobytes(),
            "reference_fell": old["fell"], "full_collision_fell": new["fell"],
            "reference_additional_contact_pairs": old["additional_contact_pairs"],
            "full_additional_contact_pairs": new["additional_contact_pairs"]}
        results.append(result)
        shutil.copy2(action_path, a.output/action_path.name)
        print(json.dumps(result), flush=True)
    report = {"schema": "microduck.full-collision-fixed-action-diagnostic/v2", "cases": results,
        "input_manifest_sha256": digest(a.receipt / "SHA256SUMS"), "input_policy_sha256": parent["policy_sha256"],
        "matched_physical_fields": checked_fields, "acceptance_eligible": False,
        "matched_after_bam_configuration": ["dof_armature", "dof_damping"],
        "boundary": "Original float32 policy actions replayed unchanged through identical native BAM and timing, swapping only bundled collision model. Partial inputs are allowed only for a retained terminal fall and are never padded or called complete. Alternate-model diagnostic, not the frozen reduced-model acceptance contract or hardware calibration. Contacts sampled at control boundaries; copied pose clearance is a separate all-frame audit."}
    (a.output/"audit.json").write_text(json.dumps(report, indent=2)+"\n")
    for name in ("scripts/audit_walking_full_collision_replay.py", "experiments/walking/world.py", "experiments/walking/sensor_world.py", "experiments/laser/gait.py", "evaluator/core.py", "experiments/laser/camera_alignment.py", "experiments/walking/tracking-suite-v1.json", "microduck/assets/microduck/scene.xml", "microduck/assets/microduck/scene_walk.xml", "microduck/assets/microduck/robot_walk.xml", "microduck/assets/microduck/robot_allcollisions.xml"):
        dest = a.output/"source"/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT/name, dest)
    assets = ROOT/"microduck/assets/microduck/assets"
    (a.output/"mesh-input-sha256.json").write_text(json.dumps({str(f.relative_to(ROOT)): digest(f) for f in sorted(assets.iterdir()) if f.is_file()}, indent=2)+"\n")
    (a.output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.relative_to(a.output)}\n" for f in sorted(a.output.rglob("*")) if f.is_file()))


if __name__ == "__main__":
    main()
