"""Offline plots/videos and domain checks from immutable camera recordings."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    results = {p.parent.name: json.loads(p.read_text()) for p in args.receipt.glob("*/evaluation.json")}
    nominal = results["straight-r0"]["materialized_domain"]
    domain_records = []
    for name, result in sorted(results.items()):
        actual, case = result["materialized_domain"], result["case"]
        for field in ("body_mass_kg", "body_inertia_kg_m2"):
            np.testing.assert_array_equal(np.asarray(actual[field]), np.asarray(nominal[field])*case["mass"])
        expected = np.asarray(nominal["geometry_friction"])
        expected[:, 0] *= case["friction"]
        np.testing.assert_array_equal(np.asarray(actual["geometry_friction"]), expected)
        domain_records.append({"case": name, "factors": actual["factors"], "arrays_match_nominal_times_factor": True})
    pairs = [("straight-r0", "isolated-straight"), ("camera-drop-r0", "camera-stale-r0"),
             ("camera-drop-r1", "camera-stale-r1"), ("target-loss-r0", "occlusion-r0"),
             ("target-loss-r0", "distractor-r0"), ("target-loss-r1", "occlusion-r1"),
             ("target-loss-r1", "distractor-r1")]
    equalities = []
    for left, right in pairs:
        a = args.receipt/left/"motion.npz"
        b = (args.receipt.parent/"20260915-v3-straight-r0"/"motion.npz") if right == "isolated-straight" else args.receipt/right/"motion.npz"
        first, second = np.load(a), np.load(b)
        keys = ("actions", "observations", "qpos", "qvel")
        for key in keys:
            if first[key].tobytes() != second[key].tobytes():
                raise ValueError("expected same-motion control comparison differed")
        equalities.append({"left": left, "right": right, "byte_identical_arrays": keys})
    video_records = []
    selected = ("straight-r0", "combined-r0", "target-loss-r0")
    sheet = Image.new("RGB", (960, 280*3))
    for column, name in enumerate(selected):
        path = args.receipt/name
        rgb = np.load(path/"camera-frames.npz")["rgb"]
        metadata = json.loads((path/"camera-frames.json").read_text())
        if len(rgb) != 300:
            raise ValueError("selected camera video must contain all300 regular frames")
        output = args.output/f"{name}-camera.mp4"
        with imageio.get_writer(output, fps=10, codec="libx264", quality=9, ffmpeg_params=["-movflags", "+faststart"]) as writer:
            for i, pixels in enumerate(rgb):
                canvas = Image.new("RGB", (320, 288), "#10202a")
                canvas.paste(Image.fromarray(pixels), (0, 24))
                draw = ImageDraw.Draw(canvas)
                draw.text((4, 4), f"{name} | {metadata[i]['received_s']:04.1f}s | simulated RGB", fill="white")
                state = "LOCAL SIM PASS" if results[name]["passed"] else "SIM DEVELOPMENT FAILURE"
                draw.text((4, 270), state+" | 10fps original sensor rate", fill="white")
                writer.append_data(np.asarray(canvas))
        video_records.append({"case": name, "video": output.name, "sha256": sha(output), "frames": 300, "fps": 10,
                              "source_rgb_sha256": sha(path/"camera-frames.npz"), "source_metadata_sha256": sha(path/"camera-frames.json")})
        for row, index in enumerate((15, 131, 148)):
            image = Image.new("RGB", (320, 280), "#10202a")
            image.paste(Image.fromarray(rgb[index]), (0, 24))
            draw = ImageDraw.Draw(image)
            draw.text((3, 3), name+f" | {metadata[index]['received_s']:.1f}s", fill="white")
            draw.text((3, 266), metadata[index]["detection"]["reason"], fill="white")
            sheet.paste(image, (column*320, row*280))
    sheet.save(args.output/"camera-contact-sheet.png")
    report = {"schema": "microduck.visual-follow-offline-analysis/v1", "source_bank_sha256": sha(args.receipt/"bank.json"),
              "materialized_domain_checks": domain_records, "same_motion_comparisons": equalities, "camera_videos": video_records,
              "source_sha256": sha(Path(__file__)), "boundary": "Original RGB displayed at original10Hz sensor rate. No physics integration, generated frames, motion retiming or action edits. Same-motion conditions are not independent physical trials."}
    (args.output/"analysis.json").write_text(json.dumps(report, indent=2)+"\n")
    shutil.copy2(__file__, args.output/"report-source.py")
    (args.output/"SHA256SUMS").write_text("".join(f"{sha(p)}  {p.relative_to(args.output)}\n" for p in sorted(args.output.iterdir()) if p.is_file()))
    print(json.dumps({"domain_cases_verified": len(domain_records), "same_motion_pairs": len(equalities), "videos": len(video_records)}), flush=True)


if __name__ == "__main__":
    main()
