"""Frozen dynamic programs, randomized flat domains, and real-time-rate video."""
import argparse
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scripts.evaluate_laser import digest, export_own
from experiments.laser.world import LaserWorld
from microduck.laser_dynamics import program_target, domain_draw

SUITE = ROOT/"experiments/laser/dynamic-suite-v1.json"


def metrics(rows, program, thresholds):
    visible = [r for r in rows if r["visible"] and r["time_s"] >= 5]
    tracking = float(np.mean([r["distance_m"] <= thresholds["acquisition_radius_m"] for r in visible])) if visible else 0.
    acquisitions = {}
    for row in rows:
        if row["visible"] and row["distance_m"] <= thresholds["acquisition_radius_m"]:
            acquisitions.setdefault(str(row["target_epoch"]), row["time_s"])
    fell = any(r["fell"] for r in rows)
    behavior = len(acquisitions) >= thresholds["minimum_waypoints_acquired"] if program == "retarget" else tracking >= thresholds["minimum_tracking_fraction_after_5s"]
    loss = [r for r in rows if not r["visible"] and r["time_s"] >= 38.5]
    loss_ok = not loss or max(r["speed_m_s"] for r in loss) < .08
    return {"passed": bool(behavior and loss_ok and not fell and rows[-1]["time_s"] >= 48),
            "fell": fell, "duration_s": rows[-1]["time_s"], "tracking_fraction": tracking,
            "waypoints_acquired": len(acquisitions), "first_acquisition_times_s": acquisitions,
            "mean_visible_distance_m": float(np.mean([r["distance_m"] for r in visible])) if visible else None,
            "max_lost_target_speed_m_s": max((r["speed_m_s"] for r in loss), default=None),
            "deadline_misses": sum(r["latency_ms"]>20 for r in rows)}


def annotate(frame, row, title):
    image = Image.fromarray(frame)
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 18)
    small = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 14)
    draw.rectangle((0, 0, image.width, 70), fill=(13, 37, 59))
    draw.text((18, 12), title, font=font, fill="white")
    draw.text((18, 40), f'{row["target_label"]}   {row["time_s"]:04.1f}s   gap {row["distance_m"]:.2f}m   '+("FELL — stopped" if row["fell"] else "live physics"), font=small, fill=(199, 220, 230))
    draw.rectangle((0, image.height-30, image.width, image.height), fill=(13, 37, 59))
    draw.text((18, image.height-24), "Yellow: duck trail   Red: target trail   Simulated coordinates, not camera detection", font=small, fill=(222, 234, 240))
    return np.array(image)


def main():
    p = argparse.ArgumentParser()
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument("--policy-receipt", type=Path)
    source.add_argument("--run-id")
    p.add_argument("--bam-repo", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--split", choices=("nominal", "development", "reserved"), default="nominal")
    p.add_argument("--video", action="store_true")
    args = p.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    parity, exported = None, None
    if args.run_id:
        policy, parity, exported = export_own(args.run_id, output)
    else:
        record = json.loads((args.policy_receipt/"evaluation.json").read_text())
        policy = args.policy_receipt/"policy.onnx"
        if digest(policy) != record["policy_sha256"]:
            raise ValueError("policy receipt hash mismatch")
        shutil.copy2(policy, output/"policy.onnx")
        policy = output/"policy.onnx"
    suite = json.loads(SUITE.read_text())
    (output/"suite.json").write_text(json.dumps(suite, indent=2)+"\n")
    seeds = [75201, 75202, 75203] if args.split == "nominal" else suite[args.split+"_seeds"]
    reports = []
    max_parity = 0.
    with (output/"trajectory.jsonl").open("w") as stream:
        for i, seed in enumerate(seeds):
            program = suite["programs"][i%len(suite["programs"])]
            domain = domain_draw(seed, args.split != "nominal")
            world = LaserWorld(policy, args.bam_repo, domain, args.video)
            rows = []
            writer = imageio.get_writer(output/f"{seed}-{program}.mp4", fps=25, codec="libx264", quality=7) if args.video else None
            try:
                for step in range(int(suite["seconds"]*50)):
                    target, visible, label, epoch = program_target(program, step*.02, rotation=domain["route_rotation_rad"])
                    row = world.step(target, visible)
                    if exported is not None:
                        import torch
                        with torch.no_grad():
                            max_parity = max(max_parity, float(np.abs(exported(torch.from_numpy(world.last_observation)).numpy()[0]-world.last_action).max()))
                    row.update(case_id=f"{seed}-{program}", target_label=label, target_epoch=epoch)
                    rows.append(row)
                    stream.write(json.dumps(row)+"\n")
                    if writer and step%2 == 1:
                        writer.append_data(annotate(world.frame(target, visible), row, f"Microduck / {program} / {args.split}"))
                    if row["fell"]:
                        break
            finally:
                world.close()
                if writer:
                    writer.close()
            report = {"case_id": f"{seed}-{program}", "program": program, "domain": domain,
                      **metrics(rows, program, suite["thresholds"])}
            reports.append(report)
            print(json.dumps(report), flush=True)
    if exported is not None and max_parity >= 1e-4:
        raise ValueError(f"real observation ONNX parity failed: {max_parity}")
    result = {"schema": "microduck.dynamic-laser-evaluation/v1", "split": args.split,
              "canonical_held_out": False, "policy_sha256": digest(policy), "target_source": "simulated-ground-truth",
              "suite_sha256": digest(SUITE), "passed_cases": sum(r["passed"] for r in reports),
              "total_cases": len(reports), "falls": sum(r["fell"] for r in reports), "case_reports": reports,
              "export_random_parity": parity, "export_real_observation_max_error_rad": max_parity if exported is not None else None, "boundary": suite["boundary"]}
    (output/"evaluation.json").write_text(json.dumps(result, indent=2)+"\n")
    for source in ("scripts/evaluate_laser_dynamic.py", "experiments/laser/world.py", "microduck/laser_dynamics.py", "microduck/laser_steering.py", "microduck/laser_task.py"):
        dest = output/"source"/source
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT/source, dest)
    (output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.relative_to(output)}\n" for f in sorted(output.rglob("*")) if f.is_file() and f.name != "SHA256SUMS"))
    print(f'{result["passed_cases"]}/{len(reports)} cases passed, {result["falls"]} falls')


if __name__ == "__main__":
    main()
