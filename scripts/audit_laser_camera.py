"""Read-only model camera-frame audit; never rotate a frozen camera silently."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import imageio.v2 as imageio
import mujoco
import numpy as np
from evaluator.core import EvaluatorCore
from scripts.evaluate_laser import digest
from microduck.laser_task import detect_red_spot


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bam-repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    # Policy is not executed; the validated infrastructure fixture just admits
    # construction of the exact locked model and controller.
    core = EvaluatorCore(ROOT/"tests/fixtures/evaluator/zero-policy.onnx", args.bam_repo, "microduck.walking.v1")
    core.reset([0, 0, .125], [1, 0, 0, 0])
    camera_id = core.model.camera("head_camera").id
    position = core.data.cam_xpos[camera_id].copy()
    rotation = core.data.cam_xmat[camera_id].reshape(3, 3).copy()
    target = np.array([.65, 0., .006])
    target_camera = rotation.T @ (target-position)
    renderer = mujoco.Renderer(core.model, height=480, width=640)
    try:
        renderer.update_scene(core.data, camera="head_camera")
        geom = renderer.scene.geoms[renderer.scene.ngeom]
        mujoco.mjv_initGeom(geom, mujoco.mjtGeom.mjGEOM_SPHERE, np.array([.012]*3),
                           target, np.eye(3).reshape(-1), np.array([1., 0., 0., 1.]))
        geom.emission = 1
        renderer.scene.ngeom += 1
        frame = renderer.render().copy()
    finally:
        renderer.close()
    imageio.imwrite(args.output/"head-camera-home.png", frame)
    result = {"schema": "microduck.laser-camera-audit/v1", "policy_executed": False,
              "model_modified": False, "physical_authority": False,
              "camera": "head_camera", "pose": "HOME, root=(0,0,0.125), yaw=0",
              "camera_world_position_m": position.tolist(),
              "camera_world_optical_forward": (-rotation[:, 2]).tolist(),
              "camera_world_image_right": rotation[:, 0].tolist(),
              "camera_world_image_up": rotation[:, 1].tolist(),
              "target_world_m": target.tolist(), "target_camera_m": target_camera.tolist(),
              "target_behind_camera": bool(target_camera[2] >= 0),
              "detected_pixel": detect_red_spot(frame, max_pixels=300),
              "source_sha256": digest(Path(__file__)),
              "scene_sha256": digest(core.scene_path), "model_root_sha256": core.model_root_digest,
              "convention_source": "https://mujoco.readthedocs.io/en/latest/modeling.html#cameras",
              "conclusion": "Resolve camera/body frame conventions with a versioned adapter before onboard pixel control; oracle targeting is not visual proof."}
    (args.output/"camera-audit.json").write_text(json.dumps(result, indent=2)+"\n")
    (args.output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.name}\n" for f in sorted(args.output.iterdir()) if f.is_file() and f.name != "SHA256SUMS"))
    print(json.dumps(result))


if __name__ == "__main__":
    main()
