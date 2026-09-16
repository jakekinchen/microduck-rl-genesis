"""Offline reflection diagnostic, not an action correction or training change."""
import argparse
import json
from pathlib import Path
import shutil
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def reflection_tables():
    import numpy as np
    p = np.array([9, 10, 11, 12, 13, 5, 6, 7, 8, 0, 1, 2, 3, 4])
    s = np.array([-1, -1, -1, -1, -1, 1, 1, -1, -1, -1, -1, -1, -1, -1], np.float32)
    op = np.r_[np.arange(6), 6+p, 20+p, 34+p, np.arange(48, 61)]
    os = np.r_[[-1, 1, -1], [1, -1, 1], s, s, s, [1, -1, -1], [1, 1, -1, -1], [1, -1, 1, -1, 1, -1]].astype(np.float32)
    if not np.array_equal(p[p], np.arange(14)) or not np.array_equal(s[p]*s, np.ones(14)):
        raise ValueError("action reflection not involutive")
    if not np.array_equal(op[op], np.arange(61)) or not np.array_equal(os[op]*os, np.ones(61)):
        raise ValueError("observation reflection not involutive")
    return p, s, op, os


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--receipt", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    import numpy as np
    import mujoco
    from scipy.spatial import ConvexHull
    from evaluator.core import OnnxPolicy
    from microduck.constants import DEFAULT_JOINT_POS, JOINT_NAMES
    from scripts.evaluate_laser import digest
    a.output.mkdir(parents=True, exist_ok=False)
    perm, signs, obs_perm, obs_signs = reflection_tables()
    model = mujoco.MjModel.from_xml_path(str(ROOT/"microduck/assets/microduck/scene_walk.xml"))
    data = mujoco.MjData(model)
    flip = np.array([1., -1., 1.])
    def geometry(q):
        data.qpos[:] = np.r_[[0., 0., .125, 1., 0., 0., 0.], q]
        mujoco.mj_forward(model, data)
        feet = []
        for side in ("left", "right"):
            g = model.geom(side+"_foot_collision").id
            mesh = model.geom_dataid[g]
            start, count = model.mesh_vertadr[mesh], model.mesh_vertnum[mesh]
            v = model.mesh_vert[start:start+count]
            v = v[ConvexHull(v).vertices]
            feet.append(v@data.geom_xmat[g].reshape(3, 3).T+data.geom_xpos[g])
        return feet, data.subtree_com[1].copy()
    rng = np.random.default_rng(76546)
    poses, hull_error, com_error = [], 0., 0.
    for _ in range(30):
        q = np.asarray(DEFAULT_JOINT_POS)+rng.uniform(-.1, .1, 14)
        first, cm = geometry(q)
        second, cm2 = geometry(q[perm]*signs)
        for i in range(2):
            u, v = first[i]*flip, second[1-i]
            for vertices, hull in ((u, ConvexHull(v)), (v, ConvexHull(u))):
                hull_error = max(hull_error, float(np.max(vertices@hull.equations[:, :3].T+hull.equations[:, 3])))
        com_error = max(com_error, float(np.linalg.norm(cm*flip-cm2)))
        poses.append(q.tolist())
    config = json.loads((ROOT/"evaluator/config-v1.json").read_text())
    policy = OnnxPolicy(a.receipt/"policy.onnx", config["inference"])
    errors, ids = [], []
    trace = a.receipt/"trajectory.jsonl"
    for i, line in enumerate(trace.read_text().splitlines()):
        if i % 20:
            continue
        row = json.loads(line)
        obs = np.asarray(row["actor_observation"], np.float32)[None]
        out, _ = policy.infer(obs)
        mirrored, _ = policy.infer((obs[:, obs_perm]*obs_signs).astype(np.float32))
        errors.append(mirrored[0]-out[0, perm]*signs)
        ids.append({"row_index": i, "case_id": row["case_id"], "time_s": row["time_s"]})
    error = np.asarray(errors)
    np.save(a.output/"mirror-action-errors-float32.npy", error)
    (a.output/"samples.json").write_text(json.dumps(ids, indent=2)+"\n")
    (a.output/"geometry-poses.json").write_text(json.dumps(poses, indent=2)+"\n")
    report = {"schema": "microduck.walking-symmetry-diagnostic/v1", "acceptance_eligible": False,
        "policy_sha256": digest(a.receipt/"policy.onnx"), "trace_sha256": digest(trace),
        "joint_order": list(JOINT_NAMES), "action_permutation": perm.tolist(), "action_signs": signs.tolist(),
        "observation_permutation": obs_perm.tolist(), "observation_signs": obs_signs.tolist(),
        "geometry_pose_count": len(poses), "maximum_outside_mirrored_sole_hull_m": hull_error,
        "maximum_mirrored_whole_com_difference_m": com_error,
        "inference_sample_count": len(errors), "mirror_action_rms_rad": float(np.sqrt(np.mean(error*error))),
        "per_joint_mirror_action_rms_rad": np.sqrt(np.mean(error*error, axis=0)).tolist(),
        "boundary": "Offline sagittal-reflection inference and approximate model-symmetry diagnostic. No inference action averaging, policy intervention or training change. Asymmetry does not by itself prove a cause of heading drift or justify enabling a loss in an active run.",
        "reference": "https://github.com/pollen-robotics/microduck_rl/blob/develop/src/mjlab_microduck/tasks/symmetry.py"}
    (a.output/"audit.json").write_text(json.dumps(report, indent=2)+"\n")
    for name in ("scripts/audit_walking_symmetry.py", "microduck/constants.py", "evaluator/core.py", "evaluator/config-v1.json", "microduck/assets/microduck/scene_walk.xml", "microduck/assets/microduck/robot_walk.xml"):
        dest = a.output/"source"/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT/name, dest)
    assets = ROOT/"microduck/assets/microduck/assets"
    (a.output/"mesh-input-sha256.json").write_text(json.dumps({str(f.relative_to(ROOT)): digest(f) for f in sorted(assets.iterdir()) if f.is_file()}, indent=2)+"\n")
    (a.output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.relative_to(a.output)}\n" for f in sorted(a.output.rglob("*")) if f.is_file()))
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
