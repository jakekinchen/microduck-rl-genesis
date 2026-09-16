"""200-Hz copied-geometry audit of exact retained actions in complete native physics.

Supplementary diagnosis, not a replacement evaluator. Recorded 50-Hz poses
must replay byte-for-byte; sensor/geometry sampling never mutates physical data.
"""
import argparse
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.evaluate_laser import digest

SOURCES = ["scripts/audit_walking_substep_contacts.py", "experiments/walking/self_contact.py",
           "experiments/walking/collision_world.py", "experiments/walking/collision_model.py",
           "experiments/walking/sensor_world.py", "experiments/walking/world.py"]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--receipt", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    from scripts.evaluate_walking_heading import verify_input_manifest
    import mujoco
    import numpy as np
    from experiments.walking.collision_world import CompleteContactWalkingWorld
    from experiments.walking.self_contact import SelfContactProbe, MAXIMUM_SELF_PENETRATION_M
    verify_input_manifest(a.receipt)
    input_manifest_sha = digest(a.receipt / "SHA256SUMS")
    source_sha = {name: digest(ROOT / name) for name in SOURCES}
    result = json.loads((a.receipt / "evaluation.json").read_text())
    model_directory = ROOT / "experiments/walking/models/contact-v11"
    scope = result.get("model_scope", {})
    if scope.get("variant") != "complete-contact-v11" or any(
            scope.get(field) != digest(model_directory / name)
            for field, name in (("scene_sha256", "scene.xml"), ("robot_sha256", "robot.xml"))):
        raise ValueError("exact complete-contact model receipt required")
    if digest(a.receipt / "policy.onnx") != result["policy_sha256"]:
        raise ValueError("policy identity mismatch")
    rows = {}
    for row in map(json.loads, (a.receipt / "trajectory.jsonl").read_text().splitlines()):
        rows.setdefault(row["case_id"], []).append(row)
    if set(rows) != {c["case_id"] for c in result["case_reports"]}:
        raise ValueError("case coverage mismatch")
    actions = {}
    for name, trajectory in rows.items():
        if not name.replace("-", "").isalnum():
            raise ValueError("unsafe case identifier")
        array = np.load(a.receipt / f"{name}-actions-float32.npy", allow_pickle=False)
        if array.dtype != np.float32 or array.shape != (900, 14) or len(trajectory) != 900:
            raise ValueError("complete 900-frame original float32 action arrays required; no padding")
        if not np.isfinite(array).all():
            raise ValueError("nonfinite original actions")
        np.testing.assert_array_equal(array, np.asarray([r["action_rad"] for r in trajectory], np.float32))
        actions[name] = array
    a.output.mkdir(parents=True, exist_ok=False)
    probe = SelfContactProbe(model_directory / "scene.xml")
    original_step = mujoco.mj_step
    reports = []
    with (a.output / "contacts.jsonl").open("w") as stream:
        for name, trajectory in rows.items():
            # Read the actual preregistered initial yaw; the first recorded
            # pose has already advanced 20 ms and is not a valid reset pose.
            suite_path = a.receipt / "suite.json"
            suite = json.loads((suite_path if suite_path.exists() else ROOT / "experiments/walking/tracking-suite-v1.json").read_text())
            if digest(suite_path if suite_path.exists() else ROOT / "experiments/walking/tracking-suite-v1.json") != result["suite_sha256"]:
                raise ValueError("suite identity mismatch")
            case_name = name.split("--", 1)[1]
            case = next(c for c in suite["cases"] if c["id"] == case_name)
            world = CompleteContactWalkingWorld(a.receipt / "policy.onnx", ROOT / ".workspace/bam",
                model_directory=model_directory,
                motor_ticks=trajectory[0]["motor_delay_physics_ticks"],
                sensor_ticks=trajectory[0]["sensor_delay_control_ticks"],
                yaw=case["yaw"], seed=suite["seed"])
            qposes, depths = [], []
            first = None

            def observe_step(model, data, *args, **kwargs):
                nonlocal first
                original_step(model, data, *args, **kwargs)
                if model is not world.core.model or data is not world.core.data:
                    raise ValueError("unexpected physical step during isolated replay")
                qposes.append(data.qpos.copy())
                contacts = probe.sample(data.qpos.copy())
                depth = max((c["penetration_m"] for c in contacts), default=0.)
                depths.append(max(0., depth))
                if contacts:
                    sample = {"case_id": name, "time_s": len(qposes) * .005,
                              "contacts": contacts}
                    stream.write(json.dumps(sample) + "\n")
                    if depth > MAXIMUM_SELF_PENETRATION_M and first is None:
                        first = sample

            try:
                mujoco.mj_step = observe_step
                for index, row in enumerate(trajectory):
                    command = row.get("policy_command", row["command"])
                    world.step_command(command, action_override=actions[name][index])
                    if not np.array_equal(world.core.data.qpos, np.asarray(row["qpos"], np.float64)):
                        raise ValueError(f"physical replay is not byte-identical: {name} frame {index}")
                    if world.last_action.tobytes() != actions[name][index].tobytes():
                        raise ValueError("action bytes changed")
                if len(qposes) != 3600:
                    raise ValueError("missing physics-substep coverage")
                np.save(a.output / f"{name}-qpos-200hz-float64.npy", np.asarray(qposes, np.float64))
                report = {"case_id": name, "frames_50hz_exact": len(trajectory), "physics_samples": len(qposes),
                          "maximum_self_penetration_m": max(depths), "first_violation": first,
                          "violating_physics_samples": sum(d > MAXIMUM_SELF_PENETRATION_M for d in depths),
                          "original_action_file_sha256": digest(a.receipt / f"{name}-actions-float32.npy")}
                reports.append(report)
                print(json.dumps(report), flush=True)
            finally:
                mujoco.mj_step = original_step
                world.close()
    verify_input_manifest(a.receipt)
    if digest(a.receipt / "SHA256SUMS") != input_manifest_sha:
        raise ValueError("input changed during audit")
    audit = {"schema": "microduck.walking-substep-contact-audit/v1", "case_reports": reports,
             "input_manifest_sha256": input_manifest_sha, "source_sha256": source_sha,
             "policy_sha256": result["policy_sha256"], "model_scope": scope,
             "total_cases": len(reports), "total_physics_samples": sum(c["physics_samples"] for c in reports),
             "maximum_self_penetration_m": max(c["maximum_self_penetration_m"] for c in reports),
             "violating_physics_samples": sum(c["violating_physics_samples"] for c in reports),
             "threshold_m": MAXIMUM_SELF_PENETRATION_M, "sample_hz": 200,
             "recorded_qpos_replay_byte_identical": True, "original_action_bytes_identical": True,
             "acceptance_eligible": False, "physical_transfer_validated": False,
             "boundary": "Supplementary 200-Hz copied contact geometry on exact native fixed-action replay. Not new closed-loop control, raw-CAD exhaustive collision coverage, calibrated clearance or physical acceptance."}
    (a.output / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    for name in SOURCES:
        if digest(ROOT / name) != source_sha[name]:
            raise ValueError(f"source changed during audit: {name}")
        target = a.output / "source" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
    (a.output / "SHA256SUMS").write_text("".join(f"{digest(f)}  {f.relative_to(a.output)}\n"
        for f in sorted(a.output.rglob("*")) if f.is_file()))
    print(json.dumps({k: v for k, v in audit.items() if k != "case_reports"}), flush=True)


if __name__ == "__main__":
    main()
