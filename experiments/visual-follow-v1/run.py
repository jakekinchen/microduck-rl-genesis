"""Frozen RGB marker-following development evaluation; no training/hardware."""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import gzip
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
import mujoco
import numpy as np

from perception import Camera, Follower, detect
from preflight import check_cases
from experiments.laser.course_v2 import CourseWorld, materialize_course, obstacle_contacts
from experiments.laser.gait import GaitProbe, summarize_gait
from experiments.walking.self_contact import SelfContactProbe, evaluate_self_contact
from experiments.walking.self_load import evaluate_self_load
from experiments.walking.posture import posture_metrics, POSTURE_LIMITS
from evaluator.core import OnnxPolicy
from scripts.evaluate_laser_course import physics_observer, verify_actor_sources, sha, SOURCE

PROTOCOL = json.loads((HERE / "protocol.json").read_text())


def route_y(x, family):
    if family == "straight":
        return 0.
    if family in ("sine", "mirror-sine"):
        return (.12 if family == "sine" else -.12) * math.sin(2*math.pi*x/2.4)
    if family == "dogleg":
        return .12 * float(np.clip((x-1.)/.6, 0, 1))
    if family == "half-cosine":
        return -.10 * (1-math.cos(math.pi*float(np.clip(x/3., 0, 1))))
    raise ValueError("unknown preregistered path")


def target_at(t, case):
    start, end = PROTOCOL["target_active_s"]
    x = PROTOCOL["target_start_x_m"] + PROTOCOL["target_speed_m_s"]*np.clip(t-start, 0, end-start)
    return np.array([x, route_y(x, case["path"]), PROTOCOL["target_height_m"]]), start <= t < end


def materialize_scene(destination, case, floor_reflectance=None):
    scene = materialize_course(destination)
    root = ET.parse(scene).getroot()
    reflectance = PROTOCOL["floor_reflectance"] if floor_reflectance is None else floor_reflectance
    root.find("./asset/material[@name='groundplane']").set("reflectance", str(reflectance))
    body = root.find("worldbody")
    # This is a following corridor, not the previous obstacle-course task.
    # Keep complete robot CAD; remove course gates/chicane decorations only.
    for geom in list(body.findall("geom")):
        name = geom.get("name", "")
        if name.startswith(("course_", "stage_")) and not name.startswith("course_wall_"):
            body.remove(geom)
    half_width = .55 if case["layout"] == "narrow-corridor" else .85
    for geom in body.findall("geom"):
        if geom.get("name", "").startswith("course_wall_"):
            sign = -1 if geom.get("name").endswith("_-1") else 1
            geom.set("pos", f"2.4 {sign*half_width} .075")
    if case["layout"] == "offset-bay":
        for i, (x, y) in enumerate(((1.1, .6), (2.2, -.6))):
            ET.SubElement(body, "geom", name=f"course_bay_{i}", type="box", pos=f"{x} {y} .12",
                          size=".22 .12 .12", rgba=".15 .3 .4 1", contype="1", conaffinity="1", friction="1 .005 .0001")
    ET.indent(root)
    scene.write_text(ET.tostring(root, encoding="unicode")+"\n")
    return scene


def camera_audit(world):
    m = world.core.model
    d = mujoco.MjData(m)
    mujoco.mj_copyData(d, m, world.core.data)
    mujoco.mj_forward(m, d)
    camera, site = m.camera("head_camera").id, m.site("head_camera").id
    optical = -d.cam_xmat[camera].reshape(3, 3)[:, 2]
    image_up = d.cam_xmat[camera].reshape(3, 3)[:, 1]
    physical = d.site_xmat[site].reshape(3, 3)
    np.testing.assert_allclose(optical, physical[:, 0], rtol=0, atol=1e-10)
    np.testing.assert_allclose(image_up, physical[:, 2], rtol=0, atol=1e-10)
    np.testing.assert_allclose(d.cam_xpos[camera], d.site_xpos[site], rtol=0, atol=1e-10)
    fovy = float(m.cam_fovy[camera])
    if fovy != PROTOCOL["camera"]["vertical_fov_deg"]:
        raise ValueError("camera FOV differs from preregistration")
    return {"revision": "microduck.head-camera-site-aligned.v2", "optical_forward_world": optical.tolist(),
            "physical_site_forward_world": physical[:, 0].tolist(), "image_up_world": image_up.tolist(),
            "local_quaternion_wxyz": m.cam_quat[camera].tolist(), "vertical_fov_deg": fovy,
            "camera_site_position_error_m": float(np.linalg.norm(d.cam_xpos[camera]-d.site_xpos[site])),
            "calibrated": False, "physics_changed": False}


def collision_audit(world):
    m, d = world.core.model, world.core.data
    robot = [i for i in range(m.ngeom) if m.geom_bodyid[i] and (m.geom_contype[i] or m.geom_conaffinity[i])]
    records = []
    for g in sorted(world.obstacles):
        pairs = [r for r in robot if (m.geom_contype[g]&m.geom_conaffinity[r]) or (m.geom_contype[r]&m.geom_conaffinity[g])]
        if len(pairs) != len(robot):
            raise ValueError("missing corridor/body mask pair")
        copied = mujoco.MjData(m)
        mujoco.mj_copyData(copied, m, d)
        copied.qpos[:2] = m.geom_pos[g, :2]
        mujoco.mj_forward(m, copied)
        witness = obstacle_contacts(m, copied, world.obstacles)
        if m.geom(g).name not in witness["obstacles"] or witness["maximum_penetration_m"] <= 0:
            raise ValueError("missing copied-state corridor collision witness")
        records.append({"name": m.geom(g).name, "position": m.geom_pos[g].tolist(), "size": m.geom_size[g].tolist(),
                        "active_robot_mask_pairs": len(pairs), "witness": witness})
    return {"obstacles": records, "copied_state_only": True}


def source_freeze(output, case, duration):
    paths = set(HERE.glob("*.py")) | set(HERE.glob("*.json")) | set(HERE.glob("*.md"))
    for module in list(sys.modules.values()):
        file = getattr(module, "__file__", None)
        if file:
            path = Path(file).resolve()
            if (path.is_file() and path.is_relative_to(ROOT) and path.suffix == ".py"
                    and not path.is_relative_to(ROOT/".venv-apple") and not path.is_relative_to(ROOT/".workspace")):
                paths.add(path)
    # Include exact robot meshes and reference model/config identities; do not
    # duplicate 3-D assets in every case, but bind and recheck their bytes.
    assets = list((ROOT/"microduck/assets/microduck/assets").glob("*.stl"))
    assets += list((HERE/"fixtures").glob("*")) if (HERE/"fixtures").exists() else []
    configs = [ROOT/"experiments/walking/models/contact-v11"/name for name in ("scene.xml", "robot.xml")]
    record = {"schema": "microduck.visual-follow-source-freeze/v1", "created_at": datetime.now(timezone.utc).isoformat(),
              "case": case, "duration_s": duration, "actors": verify_actor_sources(),
              "source_sha256": {str(p.relative_to(ROOT)): sha(p) for p in sorted(paths)},
              "asset_sha256": {str(p.relative_to(ROOT)): sha(p) for p in sorted(assets+configs)},
              "materialized_model_sha256": {p.name: sha(p) for p in (output/"model").glob("*.xml")},
              "proof_class": "exposed_simulation_development", "protected_bank_opened": False}
    for p in paths:
        dest = output/"source"/p.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dest)
    (output/"freeze.json").write_text(json.dumps(record, indent=2)+"\n")
    return record


def append_visual(scene, kind, size, position, rgba):
    geom = scene.geoms[scene.ngeom]
    mujoco.mjv_initGeom(geom, kind, np.asarray(size), np.asarray(position), np.eye(3).ravel(), np.asarray(rgba))
    geom.emission = 1.
    scene.ngeom += 1


def render_pixels(renderer, world, target, visible, fault):
    m, actual = world.core.model, world.core.data
    before = [v.copy() for v in (actual.qpos, actual.qvel, actual.ctrl, actual.act)]
    copied = mujoco.MjData(m)
    mujoco.mj_copyData(copied, m, actual)
    mujoco.mj_forward(m, copied)
    renderer.update_scene(copied, camera="head_camera")
    if visible and fault != "target-loss":
        radius = PROTOCOL["camera"]["marker_radius_m"]
        append_visual(renderer.scene, mujoco.mjtGeom.mjGEOM_SPHERE, [radius]*3, target, [1., .025, .03, 1.])
        if fault == "distractor":
            append_visual(renderer.scene, mujoco.mjtGeom.mjGEOM_SPHERE, [radius]*3, target+np.array([0, .20, 0]), [1., .025, .03, 1.])
        if fault == "occlusion":
            eye = copied.cam_xpos[m.camera("head_camera").id]
            append_visual(renderer.scene, mujoco.mjtGeom.mjGEOM_BOX, [.04, .12, .12], eye+.6*(target-eye), [.25, .3, .35, 1.])
    pixels = renderer.render().copy()
    for expected, actual_array in zip(before, (actual.qpos, actual.qvel, actual.ctrl, actual.act)):
        if expected.tobytes() != actual_array.tobytes():
            raise ValueError("renderer changed physics state")
    return pixels


def stop_metrics(rows):
    return {"speed_m_s": max(r["speed_m_s"] for r in rows),
            "yaw_rad_s": max(abs(r["yaw_rate_rad_s"]) for r in rows),
            "tilt_deg": max(r["tilt_deg"] for r in rows)}


def score(rows, samples, scene, case, duration):
    thresholds = PROTOCOL["thresholds"]
    failures = []
    full = duration == PROTOCOL["duration_s"] and len(rows) == round(duration*50)
    if not full:
        failures.append("diagnostic_or_incomplete_duration")
    gait = summarize_gait(rows)
    geometry = evaluate_self_contact(rows, SelfContactProbe(scene), round(duration*50))
    loads = evaluate_self_load(samples, duration)
    posture = posture_metrics(rows)
    failures += gait["rejection_reasons"]+geometry["failures"]+loads["failures"]
    for key, limit in POSTURE_LIMITS.items():
        if posture[key] > limit:
            failures.append("posture_"+key)
    active = [r for r in rows if 3 <= r["time_s"] < 24 and not 10 <= r["time_s"] < 14]
    low, high = thresholds["target_range_band_m"]
    tracking = float(np.mean([low <= r["target_distance_m"] <= high for r in active])) if active else 0.
    cross_track = max((r["route_cross_track_m"] for r in rows if r["time_s"] >= 3), default=math.inf)
    progress = rows[-1]["robot_xyz_m"][0]-rows[0]["robot_xyz_m"][0]
    if tracking < thresholds["minimum_target_tracking_fraction"]:
        failures.append("target_tracking")
    if cross_track > thresholds["maximum_route_cross_track_m"]:
        failures.append("route_cross_track")
    if progress < thresholds["minimum_forward_progress_m"]:
        failures.append("insufficient_forward_progress")
    max_load = max((s["course_contact"]["maximum_load_n"] for s in samples), default=math.inf)
    max_depth = max((s["course_contact"]["maximum_penetration_m"] for s in samples), default=math.inf)
    if max_load > thresholds["maximum_obstacle_load_n"] or max_depth > thresholds["maximum_obstacle_penetration_m"]:
        failures.append("robot_obstacle_contact")
    final = [r for r in rows if r["time_s"] >= 28]
    stop = None
    if len(final) != 101:
        failures.append("missing_final_stop")
    else:
        stop = stop_metrics(final)
        for key in stop:
            if stop[key] > thresholds["maximum_stop_"+key]:
                failures.append("final_stop_"+key)
        for key, value in posture_metrics(final).items():
            if key in POSTURE_LIMITS and value > POSTURE_LIMITS[key]:
                failures.append("final_posture_"+key)
    fault_stop = None
    if case["fault"] not in ("none", "negative-control"):
        after = [r for r in rows if 10.14+1e-8 <= r["control_time_s"] < 13.]
        late_commands = [r for r in after if any(r["pixel_command"])]
        settling = [r for r in rows if 12 <= r["time_s"] < 13]
        fault_stop = {"zero_command_samples": len(after)-len(late_commands), "total_samples": len(after),
                      "settling": stop_metrics(settling) if settling else None}
        if len(after) != 142 or late_commands:
            failures.append("fault_command_stop")
        if len(settling) != 50:
            failures.append("missing_fault_settling")
        elif any(fault_stop["settling"][key] > thresholds["maximum_stop_"+key] for key in fault_stop["settling"]):
            failures.append("fault_physical_stop")
    torque = np.abs(np.asarray([r["motor_torque_physics_nm"] for r in rows]))
    torque_limit = .6405236195572268
    saturation = float(np.mean(torque >= .98*torque_limit))
    margin = min(r["minimum_actual_joint_margin_rad"] for r in rows)
    if torque.max() > torque_limit+1e-6 or saturation > thresholds["maximum_torque_saturation_fraction"]:
        failures.append("torque_limit_or_saturation")
    if margin < thresholds["minimum_actual_joint_margin_rad"]:
        failures.append("actual_joint_margin")
    response_rows = [r for r in active if r["command"][0] > .03]
    response = {}
    if response_rows:
        response = {"forward_error_m_s": float(np.mean([abs(r["body_velocity_m_s"][0]-r["command"][0]) for r in response_rows])),
                    "yaw_error_rad_s": float(np.mean([abs(r["yaw_rate_rad_s"]-r["command"][2]) for r in response_rows]))}
        for key, value in response.items():
            if value > thresholds["maximum_"+key]:
                failures.append(key)
    else:
        failures.append("missing_command_response")
    return {"passed": not failures, "complete": full, "failures": sorted(set(failures)), "gait": gait,
            "self_contact": geometry, "self_load": loads, "posture": posture, "stop": stop, "fault_stop": fault_stop,
            "task": {"tracking_fraction": tracking, "maximum_cross_track_m": cross_track, "forward_progress_m": progress},
            "obstacles": {"maximum_load_n": max_load, "maximum_penetration_m": max_depth},
            "motor": {"saturation_fraction": saturation, "minimum_actual_margin_rad": margin}, "command_response": response}


def run_case(output, case, repeat, duration, anchor_binding=None):
    output.mkdir(parents=True, exist_ok=False)
    case = dict(case, repeat=repeat, seed=PROTOCOL["repeats"][repeat], initial_yaw_rad=case["yaw"]+.01*repeat)
    scene = materialize_scene(output/"model", case)
    world = CourseWorld(SOURCE/"policy.onnx", ROOT/".workspace/bam", standing_policy=SOURCE/"standing/policy.onnx",
                        model_directory=ROOT/"experiments/walking/models/contact-v11", terrain_scene=scene,
                        domain={"mass_inertia_scale": case["mass"], "sliding_friction_scale": case["friction"]},
                        motor_ticks=case["motor_ticks"], sensor_ticks=1, yaw=case["initial_yaw_rad"], seed=case["seed"], render=False)
    camera = Camera(**PROTOCOL["camera"])
    renderer = None
    rows, frames, frame_metadata, actions, observations = [], [], [], [], []
    try:
        camera_record = camera_audit(world)
        collision_record = collision_audit(world)
        freeze = source_freeze(output, case, duration)
        if anchor_binding is not None and any(freeze[key] != anchor_binding[key] for key in anchor_binding):
            raise ValueError("candidate source differs from bank-start anchor before first step")
        renderer = mujoco.Renderer(world.core.model, height=camera.height, width=camera.width)
        probe, follower = GaitProbe(world.core), Follower()
        actors = {role: OnnxPolicy(SOURCE/name, world.core.config["inference"])
                  for role, name in (("walking", "policy.onnx"), ("standing", "standing/policy.onnx"))}
        rng = np.random.default_rng(case["seed"])
        last_frame = None
        with gzip.open(output/"trajectory.jsonl.gz", "wt") as stream, physics_observer(world) as samples:
            for i in range(round(duration*50)):
                t = i*.02
                target, visible = target_at(t, case)
                fault = case["fault"] if 10 <= t < 13 else "none"
                if i % 5 == 0 and fault != "camera-drop":
                    if fault == "camera-stale" and last_frame is not None:
                        pixels, captured, sequence = last_frame
                    else:
                        pixels = render_pixels(renderer, world, target, visible, fault)
                        pixels = np.clip(pixels.astype(float)*case["gain"]+rng.normal(0, case["noise"], pixels.shape), 0, 255).astype(np.uint8)
                        captured, sequence = t, i//5
                        last_frame = pixels, captured, sequence
                    detection = detect(pixels, camera)
                    follower.ingest(detection, captured, sequence, t)
                    frames.append(pixels)
                    frame_metadata.append({"received_s": t, "captured_s": captured, "sequence": sequence,
                                           "fault": fault, "detection": asdict(detection), "rgb_sha256": hashlib.sha256(pixels.tobytes()).hexdigest()})
                command = follower.command(t)
                if case["fault"] == "negative-control":
                    command[:] = 0
                row = probe.sample(world.step_command(command))
                expected, _ = actors[row["actor_mode"]].infer(world.last_observation)
                if expected[0].tobytes() != world.last_action.tobytes():
                    raise ValueError("motor action differs from exact ONNX inference")
                # Privileged evaluation data is added only after command/action.
                row.update(control_time_s=t, pixel_command=command.tolist(), perception_reason=follower.reason,
                           detection=asdict(follower.latest), capture_time_s=follower.capture_s,
                           target_xyz_m=target.tolist(), target_visible=visible,
                           target_distance_m=float(np.linalg.norm(target-world.core.data.qpos[:3])),
                           route_cross_track_m=abs(float(world.core.data.qpos[1])-route_y(float(world.core.data.qpos[0]), case["path"])),
                           actor_observation=world.last_observation[0].tolist(), physics_samples=samples[-4:])
                rows.append(row)
                observations.append(world.last_observation[0].copy())
                actions.append(world.last_action.copy())
                stream.write(json.dumps(row, separators=(",", ":"))+"\n")
                if i % 250 == 249:
                    print(json.dumps({"case": case["id"], "repeat": repeat, "time_s": row["time_s"],
                                      "position": row["robot_xyz_m"], "perception": follower.reason, "fell": row["fell"]}), flush=True)
                if world.fell:
                    break
        result = score(rows, samples, scene, case, duration)
        result.update(schema=PROTOCOL["schema"], case=case, requested_duration_s=duration,
                      actual_duration_s=len(rows)/50, source_freeze_sha256=sha(output/"freeze.json"),
                      camera=camera_record, collision_audit=collision_record, materialized_domain=world.materialized_domain,
                      exact_onnx_rows=len(rows), physics_samples=len(samples), camera_frames=len(frames),
                      resets_within_session=0, original_actor_outputs=True,
                      controller_input="RGB-derived detection plus capture/receive timestamps; no privileged target/root state",
                      boundary="Artificial visual marker, exposed simulation development. No obstacle-perception, protected-final, calibrated-physics or physical-transfer claim.")
        np.savez_compressed(output/"motion.npz", qpos=np.array([r["qpos"] for r in rows]), qvel=np.array([r["qvel"] for r in rows]),
                            target=np.array([r["target_xyz_m"] for r in rows]), visible=np.array([r["target_visible"] for r in rows]),
                            actions=np.array(actions, np.float32), observations=np.array(observations, np.float32))
        np.savez_compressed(output/"camera-frames.npz", rgb=np.asarray(frames, np.uint8))
        (output/"camera-frames.json").write_text(json.dumps(frame_metadata, indent=2)+"\n")
        for group in ("source_sha256", "asset_sha256"):
            for path, digest in freeze[group].items():
                if sha(ROOT/path) != digest:
                    raise ValueError("frozen source changed: "+path)
        (output/"evaluation.json").write_text(json.dumps(result, indent=2)+"\n")
        (output/"SHA256SUMS").write_text("".join(f"{sha(p)}  {p.relative_to(output)}\n" for p in sorted(output.rglob("*")) if p.is_file()))
        print(json.dumps({"case": case["id"], "repeat": repeat, "passed": result["passed"], "failures": result["failures"], "task": result["task"]}), flush=True)
        return result
    except BaseException as exc:
        (output/"terminal-error.json").write_text(json.dumps({"error": repr(exc), "rows": len(rows)}, indent=2)+"\n")
        raise
    finally:
        if renderer is not None:
            renderer.close()
        world.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--case", choices=[c["id"] for c in PROTOCOL["cases"]], default="straight")
    parser.add_argument("--repeat", choices=(0, 1), type=int, default=0)
    parser.add_argument("--duration", type=float, default=PROTOCOL["duration_s"])
    parser.add_argument("--bank", choices=("development", "fresh-layouts"))
    parser.add_argument("--development-receipt", type=Path)
    args = parser.parse_args()
    if args.preflight:
        print(json.dumps({"development": check_cases(PROTOCOL["cases"]),
                          "fresh_layouts": check_cases(PROTOCOL["fresh_layout_development_cases"])}, indent=2), flush=True)
        return
    if args.output is None:
        parser.error("--output is required for evaluation")
    if not 3 <= args.duration <= PROTOCOL["duration_s"]:
        raise ValueError("duration outside bounded protocol")
    if args.bank:
        if args.duration != PROTOCOL["duration_s"]:
            raise ValueError("full bank requires full preregistered duration")
        selected_cases = PROTOCOL["cases"] if args.bank == "development" else PROTOCOL["fresh_layout_development_cases"]
        readiness = check_cases(selected_cases)
        if not readiness["all_supported"]:
            raise ValueError("bank configuration is unsupported before launch: "+json.dumps(readiness))
        if args.bank == "fresh-layouts":
            if not args.development_receipt:
                raise ValueError("verified passed development bank required")
            record = json.loads((args.development_receipt/"bank.json").read_text())
            if record.get("next_stage_allowed") is not True or record.get("protocol_sha256") != sha(HERE/"protocol.json"):
                raise ValueError("development did not pass this exact protocol")
            for group in ("source_sha256", "asset_sha256"):
                for path, digest in record["candidate_binding"][group].items():
                    if sha(ROOT/path) != digest:
                        raise ValueError("candidate changed since development: "+path)
            if record["candidate_binding"]["actors"] != verify_actor_sources():
                raise ValueError("actor changed since development")
            for path, digest in record["result_sha256"].items():
                if sha(args.development_receipt/path) != digest:
                    raise ValueError("development results changed")
        args.output.mkdir(parents=True, exist_ok=False)
        anchor = source_freeze(args.output, {"bank": args.bank, "role": "bank_anchor"}, args.duration)
        anchor_binding = {key: anchor[key] for key in ("source_sha256", "asset_sha256", "actors")}
        cases = selected_cases
        results = []
        for case in cases:
            for repeat in range(2):
                path = args.output/f"{case['id']}-r{repeat}"
                results.append(run_case(path, case, repeat, args.duration, anchor_binding))
                frozen = json.loads((path/"freeze.json").read_text())
                if any(frozen[key] != anchor_binding[key] for key in anchor_binding):
                    raise ValueError("case source differs from bank-start anchor")
        ordinary = [r for r in results if r["case"]["fault"] != "negative-control"]
        negatives = [r for r in results if r["case"]["fault"] == "negative-control"]
        negative_valid = all(r["complete"] and not r["passed"] and "insufficient_forward_progress" in r["failures"]
                             and not r["gait"]["rejection_gate_passed"] for r in negatives)
        freezes = [json.loads(p.read_text()) for p in sorted(args.output.glob("*/freeze.json"))]
        bindings = [{key: item[key] for key in ("source_sha256", "asset_sha256", "actors")} for item in freezes]
        if any(binding != bindings[0] for binding in bindings):
            raise ValueError("candidate sources changed between bank cases")
        result = {"schema": "microduck.visual-follow-bank/v1", "bank": args.bank,
                  "protocol_sha256": sha(HERE/"protocol.json"), "next_stage_allowed": all(r["passed"] for r in ordinary) and negative_valid,
                  "candidate_binding": bindings[0],
                  "negative_control_valid": negative_valid, "cases_passed": sum(r["passed"] for r in ordinary),
                  "cases_required": len(ordinary), "protected_bank_opened": False,
                  "result_sha256": {str(p.relative_to(args.output)): sha(p) for p in sorted(args.output.glob("*/evaluation.json"))}}
        (args.output/"bank.json").write_text(json.dumps(result, indent=2)+"\n")
        print(json.dumps(result), flush=True)
    else:
        run_case(args.output, next(c for c in PROTOCOL["cases"] if c["id"] == args.case), args.repeat, args.duration)


if __name__ == "__main__":
    main()
