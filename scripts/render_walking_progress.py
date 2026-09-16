"""Make a labeled video from actual retained V18 native simulator recordings."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.evaluate_walking_heading import verify_input_manifest
from scripts.evaluate_laser import digest


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    source = ROOT/"receipts/walking/20260906-v18-current"
    verify_input_manifest(source)
    report = json.loads((source/"evaluation.json").read_text())
    if report["acceptance_variant"] != "unbraced-walking-ramped-v18":
        raise ValueError("exact final V18 native recording required")
    clips = [("nominal-20-20ms--forward-12", "WALK + STOP | LATEST FINAL POLICY"),
             ("nominal-20-20ms--turn-left", "TURN + STOP | LATEST FINAL POLICY"),
             ("long-30-20ms--forward-20", "STRESS TEST | YAW STABILITY STILL FAILS")]
    a.output.mkdir(parents=True, exist_ok=False)
    import imageio.v2 as imageio
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"
    font = ImageFont.truetype(font_path, 22)
    small = ImageFont.truetype(font_path, 15)
    output = a.output/"duck-progress.mp4"
    records = []
    with imageio.get_writer(output, fps=25, codec="libx264", quality=8,
                           macro_block_size=16, ffmpeg_params=["-movflags", "+faststart"]) as writer:
        for case_id, title in clips:
            case = next(c for c in report["case_reports"] if c["case_id"] == case_id)
            if case["passed"] != (case_id != "long-30-20ms--forward-20"):
                raise ValueError("video label does not match the measured outcome")
            video = source/f"{case_id}.mp4"
            before = digest(video)
            frames = 0
            with imageio.get_reader(video) as reader:
                for frame in reader:
                    if frame.shape != (480,720,3):
                        raise ValueError("unexpected recording size")
                    # Keep every original scene pixel, frame and timestamp.
                    canvas = Image.new("RGB", (720,544), (15,20,30))
                    canvas.paste(Image.fromarray(frame), (0,40))
                    draw = ImageDraw.Draw(canvas)
                    draw.text((14,8), title, font=font, fill="white")
                    draw.text((14,523), "Actual simulation footage, 1x speed. Development only; not hardware validated.",
                              font=small, fill=(200,210,225))
                    writer.append_data(np.asarray(canvas))
                    frames += 1
            if frames != 450 or before != digest(video):
                raise ValueError("incomplete or changing source video")
            records.append({"case_id": case_id, "source": str(video.relative_to(ROOT)),
                            "sha256": before, "frames": frames, "reported_case_passed": case["passed"]})
    provenance = {"schema": "microduck.walking-progress-video/v1", "video_sha256": digest(output),
        "source_manifest_sha256": digest(source/"SHA256SUMS"), "clips": records,
        "source_current_passed_cases": report["passed_cases"], "source_current_total_cases": report["total_cases"],
        "walking_policy_sha256": report["policy_sha256"], "standing_policy_sha256": report["standing_policy_sha256"],
        "duration_s": 54, "fps": 25, "playback_speed": 1, "generated_robot_frames": False,
        "edits": "Three complete 18-second recordings concatenated, title/footer padding only; no scene pixel replacement, cropping, interpolation or action assistance.",
        "boundary": "Two passing current examples and one failing stress case, not the full expanded-bank result or physical transfer.",
        "render_source_sha256": digest(Path(__file__))}
    (a.output/"provenance.json").write_text(json.dumps(provenance,indent=2)+"\n")
    (a.output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.name}\n" for f in sorted(a.output.iterdir()) if f.is_file()))
    print(json.dumps(provenance), flush=True)


if __name__ == "__main__":
    main()
