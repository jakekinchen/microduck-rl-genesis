"""Check imported inertial parameters against the frozen MJCF, without rollout.

This establishes import consistency only. Authored CAD numbers are not measured
robot calibration. Tolerances are float32 conversion tolerances, not hardware
accuracy tolerances. Read runtime mass as well as loaded inertial descriptors.
"""
import argparse
import importlib.metadata
import json
from pathlib import Path
import shutil
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    import genesis as gs
    import mujoco
    import numpy as np
    import torch
    from microduck.walking_yaw_refinement_env import MicroduckYawRefinementEnv
    from scripts.evaluate_laser import digest
    training = json.loads((ROOT / "logs/walking-20260906-v21/run.json").read_text())
    for name, sha in training["source_sha256"].items():
        if digest(ROOT / name) != sha:
            raise ValueError(f"training source drift before audit: {name}")
    torch.set_num_threads(1)
    gs.init(backend=gs.cpu, logging_level="warning", seed=26090621)
    env = MicroduckYawRefinementEnv(1, demo=True,
        model_directory=ROOT / "experiments/walking/models/contact-v11")
    native = mujoco.MjModel.from_xml_path(str(env.robot_xml))
    actual_mass = env.robot.get_links_inertial_mass().cpu().numpy().reshape(-1)
    rows, failures = [], []

    def rotated_inertia(quat, inertia):
        matrix = np.empty(9, np.float64)
        mujoco.mju_quat2Mat(matrix, np.asarray(quat, np.float64))
        rotation = matrix.reshape(3, 3)
        return rotation @ np.asarray(inertia, np.float64) @ rotation.T

    def check(name, actual, expected, atol):
        actual, expected = np.asarray(actual), np.asarray(expected)
        passed = (actual.shape == expected.shape and np.isfinite(actual).all()
                  and np.allclose(actual, expected, rtol=1e-5, atol=atol))
        if not passed:
            failures.append(name)
        return {"passed": bool(passed), "actual": actual.tolist(), "expected": expected.tolist(),
                "rtol": 1e-5, "atol": atol}

    for index, link in enumerate(env.robot.links):
        body = mujoco.mj_name2id(native, mujoco.mjtObj.mjOBJ_BODY, link.name)
        if body < 1:
            failures.append("missing_native_body:" + link.name)
            continue
        row = {"body": link.name,
            "runtime_mass_kg": check(link.name+":mass", actual_mass[index], native.body_mass[body], 1e-8),
            "imported_center_of_mass_m": check(link.name+":com", link.inertial_pos, native.body_ipos[body], 1e-8),
            "imported_body_frame_inertia_kg_m2": check(link.name+":inertia",
                rotated_inertia(link.inertial_quat, link.inertial_i),
                rotated_inertia(native.body_iquat[body], np.diag(native.body_inertia[body])), 1e-10)}
        rows.append(row)
    expected_names = {native.body(i).name for i in range(1, native.nbody) if native.body_mass[i] > 0}
    if expected_names != {row["body"] for row in rows}:
        failures.append("body_inventory_mismatch")
    result = {"schema": "microduck.imported-physics-audit/v1", "passed": not failures,
        "failures": failures, "bodies": rows,
        "total_runtime_mass_kg": float(actual_mass.sum()),
        "total_native_mass_kg": float(native.body_mass.sum()),
        "required_battery_leg_contact_pairs": "verified by exact geometry identities in environment construction",
        "integration_dt_s": env.sim_dt, "actor_dt_s": env.dt,
        "actual_control_steps": 0, "physical_transfer_validated": False,
        "packages": {p: importlib.metadata.version(p) for p in ("genesis-world", "torch", "mujoco")},
        "model_sha256": digest(Path(env.robot_xml)), "source_sha256": digest(Path(__file__)),
        "training_source_sha256": training["source_sha256"],
        "boundary": "Runtime mass and imported COM/inertia consistency with authored MJCF, not contact-solver equivalence, measurement calibration or behavior success."}
    (args.output / "audit.json").write_text(json.dumps(result, indent=2)+"\n")
    shutil.copy2(__file__, args.output / "audit-source.py")
    shutil.copy2(env.robot_xml, args.output / "robot-source.xml")
    shutil.copy2(ROOT / "logs/walking-20260906-v21/run.json", args.output / "training-at-audit.json")
    (args.output / "SHA256SUMS").write_text("".join(f"{digest(p)}  {p.name}\n" for p in sorted(args.output.iterdir()) if p.is_file()))
    print(json.dumps({k: v for k, v in result.items() if k != "bodies"}), flush=True)
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
