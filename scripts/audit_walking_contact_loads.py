"""Exact native replay with applied self-contact load, including terminal prefixes.

Forces are those computed by mj_step for the just-integrated 5-ms interval.
Reading them does not forward or mutate physical data. No acceptance threshold
is introduced here; 1-N occupancy is descriptive, not calibrated hardware proof.
"""
import argparse
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.evaluate_laser import digest


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--receipt", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--case", action="append", required=True)
    a = p.parse_args()
    import mujoco
    import numpy as np
    from scripts.evaluate_walking_heading import verify_input_manifest
    from experiments.walking.collision_world import CompleteContactWalkingWorld
    verify_input_manifest(a.receipt)
    manifest_sha = digest(a.receipt / "SHA256SUMS")
    evaluation = json.loads((a.receipt / "evaluation.json").read_text())
    model_dir = ROOT / "experiments/walking/models/contact-v11"
    if evaluation.get("model_scope", {}).get("variant") != "complete-contact-v11":
        raise ValueError("complete-contact input required")
    for field, name in (("scene_sha256", "scene.xml"), ("robot_sha256", "robot.xml")):
        if evaluation["model_scope"][field] != digest(model_dir / name):
            raise ValueError("model identity mismatch")
    suite_path = a.receipt / "suite.json"
    if not suite_path.exists():
        suite_path = ROOT / "experiments/walking/tracking-suite-v1.json"
    if digest(suite_path) != evaluation["suite_sha256"]:
        raise ValueError("suite identity mismatch")
    suite = json.loads(suite_path.read_text())
    wanted = set(a.case)
    if len(wanted) != len(a.case) or any(not name.replace("-", "").isalnum() for name in wanted):
        raise ValueError("unique safe case IDs required")
    rows = {name: [] for name in a.case}
    for line in (a.receipt / "trajectory.jsonl").open():
        row = json.loads(line)
        if row["case_id"] in wanted:
            rows[row["case_id"]].append(row)
    source_names = ["scripts/audit_walking_contact_loads.py", "experiments/walking/collision_world.py",
                    "experiments/walking/collision_model.py", "experiments/walking/sensor_world.py",
                    "experiments/walking/world.py"]
    sources = {name: digest(ROOT / name) for name in source_names}
    a.output.mkdir(parents=True, exist_ok=False)
    native_step = mujoco.mj_step
    reports = []
    with (a.output / "loads.jsonl").open("w") as stream:
        for name, trace in rows.items():
            if not trace or len(trace) > 900 or (len(trace) < 900 and trace[-1]["fell"] is not True):
                raise ValueError("complete schedule or explicitly recorded terminal fall required")
            actions = np.load(a.receipt / f"{name}-actions-float32.npy", allow_pickle=False)
            if actions.dtype != np.float32 or actions.shape != (len(trace), 14) or not np.isfinite(actions).all():
                raise ValueError("original finite float32 actions required; no padding")
            np.testing.assert_array_equal(actions, np.asarray([r["action_rad"] for r in trace], np.float32))
            case = next(c for c in suite["cases"] if c["id"] == name.split("--", 1)[1])
            world = CompleteContactWalkingWorld(a.receipt / "policy.onnx", ROOT / ".workspace/bam",
                model_directory=model_dir, yaw=case["yaw"], seed=suite["seed"],
                motor_ticks=trace[0]["motor_delay_physics_ticks"], sensor_ticks=trace[0]["sensor_delay_control_ticks"])
            samples = []

            def step_and_read(model, data, *args, **kwargs):
                native_step(model, data, *args, **kwargs)
                if model is not world.core.model or data is not world.core.data:
                    raise ValueError("unexpected physics step")
                pairs = {}
                for i, contact in enumerate(data.contact):
                    if not all(model.geom_bodyid[g] for g in (contact.geom1, contact.geom2)):
                        continue
                    key = tuple(sorted((int(contact.geom1), int(contact.geom2))))
                    force = np.zeros(6)
                    mujoco.mj_contactForce(model, data, i, force)
                    if not np.isfinite(force).all():
                        raise ValueError("nonfinite contact load")
                    pairs[key] = pairs.get(key, 0.) + max(0., float(force[0]))
                contacts = [{"geometries": [{"body": model.body(int(model.geom_bodyid[g])).name,
                                              "mesh": model.mesh(int(model.geom_dataid[g])).name,
                                              "geom_id": g} for g in pair], "normal_force_n": force}
                            for pair, force in pairs.items() if force > 0]
                sample = {"case_id": name, "interval_start_s": len(samples) * .005,
                          "interval_end_s": (len(samples)+1) * .005, "contacts": contacts,
                          "total_normal_n": sum(pairs.values()), "largest_pair_normal_n": max(pairs.values(), default=0.)}
                samples.append(sample)
                stream.write(json.dumps(sample) + "\n")

            try:
                mujoco.mj_step = step_and_read
                for index, row in enumerate(trace):
                    if abs(row["time_s"] - (index+1)*.02) > 1e-8:
                        raise ValueError("irregular input time axis")
                    world.step_command(row.get("policy_command", row["command"]), action_override=actions[index])
                    if world.last_action.tobytes() != actions[index].tobytes():
                        raise ValueError("motor action bytes changed")
                    if not np.array_equal(world.core.data.qpos, np.asarray(row["qpos"], np.float64)):
                        raise ValueError(f"recorded pose replay changed at {name} frame {index}")
                if len(samples) != 4*len(trace):
                    raise ValueError("missing physics samples")
                phases = {}
                for label, start, end in (("initial_stand", 0., 1.), ("moving", 2., 13.),
                                          ("braking", 13., 16.), ("settled_stop", 16., 18.)):
                    phase = [s for s in samples if start <= s["interval_start_s"] < end - 1e-8]
                    phases[label] = {"observed_samples": len(phase), "expected_samples": round((end-start)*200),
                                     "max_pair_normal_n": max((s["largest_pair_normal_n"] for s in phase), default=None),
                                     "pair_over_1n_fraction": float(np.mean([s["largest_pair_normal_n"] > 1 for s in phase])) if phase else None,
                                     "mean_total_normal_n": float(np.mean([s["total_normal_n"] for s in phase])) if phase else None}
                report = {"case_id": name, "input_frames": len(trace), "input_complete": len(trace) == 900,
                          "terminal_fall": trace[-1]["fell"], "physics_samples": len(samples), "phases": phases,
                          "original_action_file_sha256": digest(a.receipt / f"{name}-actions-float32.npy")}
                reports.append(report)
                print(json.dumps(report), flush=True)
            finally:
                mujoco.mj_step = native_step
                world.close()
    verify_input_manifest(a.receipt)
    if digest(a.receipt / "SHA256SUMS") != manifest_sha:
        raise ValueError("input changed during diagnostic")
    result = {"schema": "microduck.walking-self-contact-load-diagnostic/v1", "case_reports": reports,
              "input_manifest_sha256": manifest_sha, "source_sha256": sources,
              "model_scope": evaluation["model_scope"], "policy_sha256": evaluation["policy_sha256"],
              "motor_action_bytes_identical": True, "recorded_qpos_bytes_identical": True,
              "acceptance_eligible": False, "physical_transfer_validated": False,
              "boundary": "Applied native self-contact normal loads at 200 Hz, summed per geometry pair. Terminal inputs remain partial; missing stop data is unknown. Not calibrated hardware load, ground support, new control or walking acceptance."}
    (a.output / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
    for name, sha in sources.items():
        if digest(ROOT / name) != sha:
            raise ValueError("source changed during diagnostic")
        dest = a.output / "source" / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, dest)
    (a.output / "SHA256SUMS").write_text("".join(f"{digest(f)}  {f.relative_to(a.output)}\n"
        for f in sorted(a.output.rglob("*")) if f.is_file()))


if __name__ == "__main__":
    main()
