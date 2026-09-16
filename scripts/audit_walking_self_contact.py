"""Copied-pose collider audit; no policy, dynamics, forces or acceptance claim."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def geom_label(model, index):
    mesh = int(model.geom_dataid[index])
    return {"id": int(index), "name": model.geom(index).name,
            "body": model.body(int(model.geom_bodyid[index])).name,
            "mesh": model.mesh(mesh).name if mesh >= 0 else None,
            "contype": int(model.geom_contype[index]),
            "conaffinity": int(model.geom_conaffinity[index])}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--receipt", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--no-decimation", action="store_true")
    p.add_argument("--complete-model", action="store_true")
    a = p.parse_args()
    import numpy as np
    import mujoco
    import torch
    import genesis as gs
    from genesis.utils.misc import qd_to_numpy
    from microduck.constants import MICRODUCK_WALK_XML, JOINT_NAMES, DEFAULT_JOINT_POS
    from scripts.evaluate_walking_heading import verify_input_manifest
    from scripts.evaluate_laser import digest
    verify_input_manifest(a.receipt)
    selected = {"nominal-20-20ms--"+n for n in ("forward-08", "forward-12", "turn-left")}
    rows = [json.loads(line) for line in (a.receipt/"trajectory.jsonl").read_text().splitlines()]
    rows = [r for r in rows if r["case_id"] in selected]
    if {r["case_id"] for r in rows} != selected:
        raise ValueError("missing preregistered diagnostic cases")
    a.output.mkdir(parents=True, exist_ok=False)
    robot_xml = MICRODUCK_WALK_XML
    complete_scene = None
    if a.complete_model:
        from experiments.walking.collision_model import materialize
        robot_xml, complete_scene = materialize(a.output/"model")
    torch.set_num_threads(1)
    gs.init(backend=gs.cpu, logging_level="warning", seed=76551)
    scene = gs.Scene(sim_options=gs.options.SimOptions(dt=.005, substeps=1),
                     rigid_options=gs.options.RigidOptions(constraint_timeconst=.02,
                        batch_dofs_info=True, enable_self_collision=True,
                        iterations=10, ls_iterations=20, max_collision_pairs=120 if a.complete_model else 30),
                     show_viewer=False)
    scene.add_entity(gs.morphs.Plane(contype=1, conaffinity=1))
    morph_args = {"decimate": False} if a.no_decimation else {}
    robot = scene.add_entity(gs.morphs.MJCF(file=str(robot_xml), pos=(0, 0, .125), **morph_args))
    scene.build(n_envs=1)
    models = {tag: mujoco.MjModel.from_xml_path(str(ROOT/"microduck/assets/microduck"/name))
              for tag, name in (("reduced", "scene_walk.xml"), ("full", "scene.xml"))}
    if complete_scene is not None:
        models["complete"] = mujoco.MjModel.from_xml_path(str(complete_scene))
    data = {tag: mujoco.MjData(model) for tag, model in models.items()}
    source_tag = "complete" if a.complete_model else "reduced"
    m = models[source_tag]
    for i, name in enumerate(JOINT_NAMES):
        j = robot.get_joint(name)
        if j.q_start != 7+i or m.jnt_qposadr[m.joint(name).id] != 7+i:
            raise ValueError("copied qpos ordering mismatch")
    home = np.r_[0., 0., .125, 1., 0., 0., 0., DEFAULT_JOINT_POS]
    robot.set_qpos(torch.tensor(home[None], dtype=torch.float32))
    data[source_tag].qpos[:] = home
    mujoco.mj_forward(m, data[source_tag])
    rng = np.random.default_rng(76551)
    directions = np.r_[np.eye(3), -np.eye(3), rng.normal(size=(1024, 3))]
    directions /= np.linalg.norm(directions, axis=1, keepdims=True)
    geometry = []
    labels = {}
    for g in robot.geoms:
        matched = [i for i in range(m.ngeom) if m.body(int(m.geom_bodyid[i])).name == g.link.name
                   and int(m.geom_contype[i]) == g.contype and int(m.geom_conaffinity[i]) == g.conaffinity
                   and m.mesh(int(m.geom_dataid[i])).name == Path(g.metadata.get("mesh_path", "")).stem
                   and (g.contype or g.conaffinity)]
        if len(matched) != 1:
            raise ValueError(f"ambiguous collision geom mapping: {g.link.name}")
        i = matched[0]
        label = geom_label(m, i)
        labels[g.idx] = label
        mesh = int(m.geom_dataid[i])
        vs = m.mesh_vert[m.mesh_vertadr[mesh]:m.mesh_vertadr[mesh]+m.mesh_vertnum[mesh]]
        native = vs @ data[source_tag].geom_xmat[i].reshape(3, 3).T + data[source_tag].geom_xpos[i]
        genesis = g.get_verts()[0].cpu().numpy()
        support_error = np.max(np.abs((native@directions.T).max(0)-(genesis@directions.T).max(0)))
        geometry.append({"native": label, "genesis_id": g.idx,
                         "genesis_vertices": len(genesis), "native_vertices": len(vs),
                         "max_sampled_support_difference_m": float(support_error)})
    if a.complete_model:
        from microduck.walking_collision_env import assert_battery_contacts_enabled
        assert_battery_contacts_enabled(robot, scene.rigid_solver.collider)
    print(json.dumps({"geometry": geometry}), flush=True)
    summaries = defaultdict(lambda: {"frames": 0, "pairs": {}})
    output_rows = []
    for r in rows:
        q = np.asarray(r["qpos"], float)
        if q.shape != (21,) or not np.isfinite(q).all():
            raise ValueError("invalid copied pose")
        found = {}
        for tag, model in models.items():
            d = data[tag]
            d.qpos[:] = q
            mujoco.mj_forward(model, d)
            contacts = []
            for c in d.contact:
                if not all(model.geom_bodyid[int(g)] for g in (c.geom1, c.geom2)):
                    continue
                contacts.append({"a": geom_label(model, int(c.geom1)), "b": geom_label(model, int(c.geom2)),
                                 "penetration_m": -float(c.dist)})
            found[tag] = contacts
        robot.set_qpos(torch.tensor(q[None], dtype=torch.float32))
        pairs = robot.detect_collision()
        state = scene.rigid_solver.collider._collider_state
        penetrations = qd_to_numpy(state.contact_data.penetration)[:len(pairs), 0]
        # detect_collision includes floor contacts too, in the same solver order;
        # this scene has only the floor and robot, so no unrelated pair is removed.
        contacts = []
        for (i, j), penetration in zip(pairs, penetrations):
            if int(i) in labels and int(j) in labels:
                contacts.append({"a": labels[int(i)], "b": labels[int(j)], "penetration_m": float(penetration)})
        found["genesis"] = contacts
        output_rows.append({"case_id": r["case_id"], "time_s": r["time_s"], "contacts": found})
        for tag, contacts in found.items():
            s = summaries[r["case_id"]+":"+tag]
            s["frames"] += 1
            for c in contacts:
                key = " / ".join(sorted(c[k]["body"]+":"+str(c[k]["mesh"]) for k in ("a", "b")))
                ps = s["pairs"].setdefault(key, {"samples": 0, "maximum_penetration_m": 0., "first_time_s": r["time_s"]})
                ps["samples"] += 1
                ps["maximum_penetration_m"] = max(ps["maximum_penetration_m"], c["penetration_m"])
    report = {"schema": "microduck.copied-pose-self-contact-diagnostic/v1",
              "input_manifest_sha256": digest(a.receipt/"SHA256SUMS"),
              "input_trace_sha256": digest(a.receipt/"trajectory.jsonl"),
              "genesis_decimation": not a.no_decimation, "genesis_model": source_tag, "geometry": geometry,
              "model_geometry": {tag: [geom_label(model, i) for i in range(model.ngeom)
                    if model.geom_contype[i] or model.geom_conaffinity[i]] for tag, model in models.items()},
              "cases": dict(summaries), "acceptance_eligible": False,
              "boundary": "Identical recorded poses copied into explicitly identified native and Genesis models for collision detection. No dynamics, forces or physical truth claim. Contact sample counts are manifold POINTS, not distinct frame counts. Sampled convex support difference is not an exhaustive Hausdorff bound. All original actions and evaluators are unchanged."}
    (a.output/"contacts.jsonl").write_text("".join(json.dumps(r)+"\n" for r in output_rows))
    (a.output/"audit.json").write_text(json.dumps(report, indent=2)+"\n")
    for name in ("scripts/audit_walking_self_contact.py", "microduck/constants.py",
                 "experiments/walking/collision_model.py", "microduck/walking_collision_env.py",
                 "microduck/assets/microduck/robot_walk.xml", "microduck/assets/microduck/robot_allcollisions.xml",
                 "microduck/assets/microduck/scene_walk.xml", "microduck/assets/microduck/scene.xml"):
        dest = a.output/"source"/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT/name, dest)
    for name in ("genesis/engine/solvers/rigid/collider/collider.py", "genesis/options/morphs.py"):
        src = Path(gs.__file__).parent.parent/name
        dest = a.output/"dependency-source"/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
    (a.output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.relative_to(a.output)}\n" for f in sorted(a.output.rglob("*")) if f.is_file()))
    print(json.dumps({"cases": dict(summaries)}), flush=True)


if __name__ == "__main__":
    main()
