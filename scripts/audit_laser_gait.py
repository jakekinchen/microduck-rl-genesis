"""Instrument unchanged laser policy with independent gait/servo/face checks."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import imageio.v2 as imageio
import mujoco
import numpy as np
from experiments.laser.world import LaserWorld
from experiments.laser.gait import GaitProbe, summarize_gait
from experiments.laser.face_world import FaceFirstLaserWorld
from microduck.laser_dynamics import domain_draw, program_target


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--policy", type=Path, required=True)
    p.add_argument("--bam-repo", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--seconds", type=float, default=16)
    p.add_argument("--program", choices=("retarget", "circle", "figure-eight"), default="circle")
    p.add_argument("--video", action="store_true")
    p.add_argument("--steering", choices=("legacy-v2", "physical-face-v4"), default="legacy-v2")
    p.add_argument("--rotation", type=float, default=0., help="Explicit visible route rotation in radians")
    a = p.parse_args()
    if not 2 <= a.seconds <= 60: raise ValueError("bounded audit duration required")
    a.output.mkdir(parents=True, exist_ok=False)
    world_type = LaserWorld if a.steering == "legacy-v2" else FaceFirstLaserWorld
    world = world_type(a.policy, a.bam_repo, domain_draw(76031, False), render=a.video)
    probe = GaitProbe(world.core)
    writer = imageio.get_writer(a.output/"fixed-side.mp4", fps=25, codec="libx264", quality=7) if a.video else None
    camera = mujoco.MjvCamera()
    camera.lookat[:] = [.3, .1, .13]
    camera.distance, camera.azimuth, camera.elevation = 1.1, 90., -15.
    rows, actions = [], []
    try:
        with (a.output/"gait.jsonl").open("w") as f:
            for step in range(round(a.seconds*50)):
                target, visible, _, _ = program_target(a.program, step*.02, rotation=a.rotation)
                row = world.step(target, visible)
                actions.append(world.last_action.copy())
                observed = probe.sample(row)
                rows.append(observed)
                f.write(json.dumps(observed)+"\n")
                if writer and step%2 == 0:
                    world.renderer.update_scene(world.core.data, camera=camera)
                    writer.append_data(world.renderer.render())
                if world.fell: break
        np.save(a.output/"original-actions-float32.npy", np.array(actions, dtype=np.float32))
        report = {"schema": "microduck.laser-gait-audit/v3", "policy_sha256": digest(a.policy),
                  "face_reference": "CAD head_camera SITE +X, corroborated by mouth position; not legacy CAMERA optical axis",
                  "policy_path": str(a.policy), "program": a.program, "domain": world.domain,
                  "steering": a.steering, "rotation_rad": a.rotation,
                  "model_root_sha256": world.core.model_root_digest,
                  "bam_commit": "62bd8ce12154340be97e06f7f41a0ca8f116d967",
                  "diagnostic_data": "50Hz copied-state forward dynamics; never modifies rollout",
                  "gait": summarize_gait(rows)}
        (a.output/"audit.json").write_text(json.dumps(report, indent=2)+"\n")
        for source in ("scripts/audit_laser_gait.py", "experiments/laser/gait.py", "experiments/laser/world.py", "experiments/laser/face_world.py", "experiments/laser/camera_alignment.py", "microduck/laser_face_command.py"):
            destination = a.output/"source"/source
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT/source, destination)
    finally:
        if writer: writer.close()
        world.close()
    (a.output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.relative_to(a.output)}\n" for f in sorted(a.output.rglob("*")) if f.is_file() and f.name != "SHA256SUMS"))
    print(json.dumps({k:v for k,v in report["gait"].items() if k != "swing_events"}, indent=2))


if __name__ == "__main__": main()
