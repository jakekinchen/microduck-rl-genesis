"""Source-bound full-state replay and paired standing counterfactuals."""
import argparse
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import pickle
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.evaluate_laser import digest
from scripts.verify_walking_sequence_v42 import verify_manifest

FREEZE = ROOT / "experiments/walking/handoff-coverage-freeze-v43-r2.json"
INPUTS = {"v30": "receipts/walking/20260906-v30-heading-endurance",
          "v42": "receipts/walking/20260906-v42-native-standing-endurance"}
GROUPS = {"gyro": (0, 3), "gravity": (3, 6), "joints": (6, 20),
          "joint_velocity": (20, 34), "last_action": (34, 48)}


def binding():
    prior = json.loads((ROOT / "experiments/walking/native-standing-freeze-v42.json").read_text())
    sources = prior["source_sha256"].copy()
    for name in ["scripts/probe_handoff_coverage_v43_r2.py", "scripts/probe_handoff_coverage_v43.py", "scripts/verify_walking_sequence_v42.py",
                 "experiments/walking/HANDOFF-COVERAGE-v43.md"]:
        sources[name] = digest(ROOT / name)
    for name, sha in sources.items():
        if digest(ROOT / name) != sha:
            raise ValueError("source drift: " + name)
    return {"schema": "microduck.handoff-coverage-freeze/v43", "source_sha256": sources,
            "inputs": {key: verify_manifest(ROOT / value) for key, value in INPUTS.items()}}


def make_world(scene, standing, session):
    from experiments.walking.terrain_v23 import TerrainWorld
    from microduck.heading_headroom_v30 import Float32HeadingHeadroomServo
    world = TerrainWorld(ROOT / INPUTS["v30"] / "policy.onnx", ROOT / ".workspace/bam",
        standing_policy=standing, model_directory=ROOT / "experiments/walking/models/contact-v11",
        terrain_scene=scene, domain=session["domain"], motor_ticks=6, sensor_ticks=1,
        yaw=session["yaw"], seed=session["seed"])
    world.heading_servo = Float32HeadingHeadroomServo()
    return world


def seal(directory):
    paths = sorted(p for p in directory.rglob("*") if p.is_file() and p.name != "SHA256SUMS")
    (directory / "SHA256SUMS").write_text("".join(
        digest(path) + "  " + str(path.relative_to(directory)) + "\n" for path in paths))


def branch(world, state, policy, case_id, stream, geometry):
    import numpy as np
    from microduck.native_standing_env_v42 import restore, observation, raw_step, clone_world
    from experiments.walking.terrain_v23 import TerrainGaitProbe
    from experiments.walking.self_load import record_self_loads, evaluate_self_load
    from experiments.walking.self_contact import evaluate_self_contact
    from experiments.walking.posture import posture_metrics, POSTURE_LIMITS
    w = clone_world(world)
    restore(w, state)
    probe, rows = TerrainGaitProbe(w.core), []
    try:
        with record_self_loads(w) as loads:
            for index in range(250):
                action = policy.infer(observation(w))[0][0]
                row = probe.sample(raw_step(w, action))
                row.update(time_s=(index + 1) * .02, case_id=case_id,
                           actor_observation=w.last_observation[0].tolist(), actor_mode="standing",
                           session_id=case_id, session_time_s=(index + 1) * .02,
                           self_load_physics=loads[-4:])
                rows.append(row)
                stream.write(json.dumps(row) + "\n")
                if w.fell:
                    break
        failures = []
        if len(rows) != 250:
            failures.append("incomplete_duration")
        if any(r["fell"] for r in rows):
            failures.append("fall")
        if any(r["nonfoot_ground_contacts"] for r in rows):
            failures.append("nonfoot_support")
        if min(r["minimum_actual_joint_margin_rad"] for r in rows) < .02:
            failures.append("joint_margin")
        saturation = float((np.abs([r["motor_torque_physics_nm"] for r in rows]) >= .6405236195572268 * .99).mean())
        if saturation > .02:
            failures.append("torque_saturation")
        settled = [r for r in rows if r["time_s"] >= 3]
        metrics = {"torque_saturation_fraction": saturation}
        if len(settled) != 101:
            failures.append("missing_final_standing")
        else:
            for field, limit in [("speed_m_s", .04), ("yaw_rate_rad_s", .15), ("tilt_deg", 15)]:
                metrics[field] = max(abs(r[field]) for r in settled)
                if metrics[field] > limit:
                    failures.append(field)
            metrics["posture"] = posture_metrics(settled)
            failures += ["posture:" + k for k, limit in POSTURE_LIMITS.items() if metrics["posture"][k] > limit]
        body = evaluate_self_contact(rows, geometry, 250)
        internal = evaluate_self_load(loads, 5.)
        failures += ["self_contact:" + f for f in body["failures"]]
        failures += ["self_load:" + f for f in internal["failures"]]
        loaded = np.array([r["foot_normal_n"] for r in rows]) > 1.
        slip = np.array([r["loaded_contact_slip_m_s"] for r in rows])
        metrics["loaded_slip_over_3cm_s_fraction"] = float((slip[loaded] > .03).mean()) if loaded.any() else None
        return {"case_id": case_id, "passed": not failures, "failures": failures,
                "duration_s": len(rows) * .02, "alive_at_3s": len(rows) >= 150 and not rows[149]["fell"],
                "metrics": metrics, "self_contact": body, "self_load": internal}
    finally:
        w.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    frozen = binding()
    if args.freeze:
        with FREEZE.open("x") as stream:
            json.dump(frozen, stream, indent=2)
        return
    if frozen != json.loads(FREEZE.read_text()):
        raise ValueError("freeze drift")
    if args.output is None:
        parser.error("new output required")
    output = args.output
    output.mkdir(parents=True, exist_ok=False)
    import numpy as np
    import torch
    from evaluator.core import OnnxPolicy
    from microduck.native_standing_env_v42 import build_templates, snapshot, restore, observation, raw_step, clone_world
    from experiments.walking.self_contact import SelfContactProbe
    torch.set_num_threads(1)
    for name in frozen["source_sha256"]:
        dest = output / "source" / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, dest)
    shutil.copy2(FREEZE, output / "freeze.json")
    templates, template_reports = build_templates(output / "original-templates")
    states, report, training_obs = [], {"schema": "microduck.handoff-coverage/v43", "replays": [], "states": [], "complete": False}, []
    policies = {key: OnnxPolicy(ROOT / value / "standing/policy.onnx", templates[0][0].core.config["inference"])
                for key, value in INPUTS.items()}
    geometry = SelfContactProbe(ROOT / "experiments/walking/models/contact-v11/scene.xml")

    def retain(world, state, identity, meta):
        dest = output / "states" / (identity + ".pkl")
        dest.parent.mkdir(exist_ok=True)
        dest.write_bytes(pickle.dumps(state, protocol=5))
        expected_sha = digest(dest)
        # Only self-created, hash-bound snapshots are deserialized.
        if digest(dest) != expected_sha:
            raise ValueError("snapshot changed")
        decoded = pickle.loads(dest.read_bytes())
        a, b = clone_world(world), clone_world(world)
        try:
            restore(a, state); restore(b, decoded)
            obs = observation(a).copy()
            np.testing.assert_array_equal(obs, observation(b))
            action = policies["v42"].infer(obs)[0][0]
            raw_step(a, action); raw_step(b, action)
            for field in ("qpos", "qvel", "ctrl", "qfrc_constraint"):
                np.testing.assert_array_equal(getattr(a.core.data, field), getattr(b.core.data, field))
        finally:
            a.close(); b.close()
        item = dict(id=identity, state_file=str(dest.relative_to(output)), state_sha256=expected_sha,
                    observation=obs[0].tolist(), exact_serialized_continuation=True, **meta)
        states.append((world, decoded, item))
        report["states"].append(item)
        return item

    try:
        for index, (world, home, handoff) in enumerate(templates):
            for kind, state in [("home", home), ("handoff", handoff)]:
                item = retain(world, state, f"train-{index}-{kind}",
                    dict(source="training-reset", template=index, kind=kind, terrain=template_reports[index]["terrain"]))
                training_obs.append(item["observation"])
        for source, relative in INPUTS.items():
            directory = ROOT / relative
            suite = json.loads((directory / "suite.json").read_text())
            sessions = {s["id"]: s for s in suite["sessions"] if s["bank"] == "diagnostic"}
            path = directory / "trajectory.jsonl"
            if not path.exists():
                path = directory / "trajectory.jsonl.gz"
            opener = gzip.open if path.suffix == ".gz" else open
            with opener(path, "rt") as stream:
                for session_id, group in itertools.groupby((json.loads(line) for line in stream), lambda r: r["session_id"]):
                    session = sessions[session_id]
                    scene = directory / "terrain-models" / session_id / "scene.xml"
                    world = make_world(scene, directory / "standing/policy.onnx", session)
                    previous = None; count = 0; max_error = 0.; actions = hashlib.sha256()
                    for saved in group:
                        if saved["actor_mode"] == "standing" and previous != "standing":
                            retain(world, snapshot(world), f"{source}-{session_id}-step-{count}",
                                dict(source=source, session=session_id, before_step=count, time_s=count*.02,
                                     kind="home" if count == 0 else "handoff", terrain=session["terrain"],
                                     scene=str(scene.relative_to(ROOT))))
                        action = np.asarray(saved["action_rad"], np.float32)
                        actions.update(action.tobytes())
                        current = world.step_command(saved["command"])
                        error = float(np.max(np.abs(world.core.data.qpos - saved["qpos"])))
                        max_error = max(max_error, error)
                        np.testing.assert_allclose(world.core.data.qpos, saved["qpos"], rtol=0, atol=1e-10)
                        np.testing.assert_array_equal(world.last_observation[0], np.asarray(saved["actor_observation"], np.float32))
                        np.testing.assert_array_equal(world.last_action, action)
                        if current["fell"] != saved["fell"]:
                            raise ValueError("terminal mismatch")
                        previous = saved["actor_mode"]; count += 1
                    report["replays"].append(dict(source=source, session=session_id, steps=count,
                        max_qpos_error=max_error, action_bytes_sha256=actions.hexdigest(), exact_observations=True))
                    print(json.dumps(report["replays"][-1]), flush=True)
        reference = np.asarray(training_obs)
        with gzip.open(output / "branches.jsonl.gz", "wt") as stream:
            for world, state, item in states:
                obs = np.asarray(item["observation"])
                item["reset_bank_min_max_component_distances"] = {
                    name: float(np.max(np.abs(reference[:, lo:hi] - obs[lo:hi]), axis=1).min())
                    for name, (lo, hi) in GROUPS.items()}
                item["branches"] = {key: branch(world, state, policy, item["id"] + "--" + key, stream, geometry)
                                    for key, policy in policies.items()}
                print(json.dumps({"state": item["id"], "branches": {k: {f: v[f] for f in ("passed", "failures", "duration_s")} for k,v in item["branches"].items()}}), flush=True)
                (output / "progress.json").write_text(json.dumps(report, indent=2) + "\n")
        report.update(complete=True, physical_calibration=False, held_out=False,
                      boundary="Paired full-state standing diagnostics and reset-bank distances; not full PPO coverage, locomotion acceptance or physical transfer.")
        (output / "probe.json").write_text(json.dumps(report, indent=2) + "\n")
        if binding() != frozen:
            raise ValueError("source/input changed during diagnosis")
        seal(output)
    finally:
        closed = set()
        for world, _, _ in states:
            if id(world) not in closed:
                world.close(); closed.add(id(world))


if __name__ == "__main__":
    main()
