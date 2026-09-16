"""Plot retained stop telemetry without integrating physics or changing scores."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    cases = [("downhill-3deg-start-1", 13., (11.5, 15.5)),
             ("continuous-composition-start-2", 31., (29.5, 34.))]
    lanes = [("Retained V30", "20260906-v30-heading-endurance", "#536170"),
             ("V54 routed", "20260909-v54-routed-endurance", "#0072B2"),
             ("V54 shared", "20260909-v54-shared-endurance", "#D55E00")]
    fields = [("tilt_deg", "Base tilt (degrees)"),
              ("speed_m_s", "Horizontal speed (m/s)"),
              ("minimum_actual_joint_margin_rad", "Smallest joint margin (rad)")]
    fig, axes = plt.subplots(3, 2, figsize=(11, 8), sharex="col", constrained_layout=True)
    provenance = {}
    for label, name, color in lanes:
        folder = args.root / "receipts/walking" / name
        report = json.loads((folder / "probe.json").read_text())
        if not report["complete"] or report["held_out"]:
            raise ValueError("complete exposed recording required")
        path = folder / "trajectory.jsonl.gz"
        if not path.exists():
            path = folder / "trajectory.jsonl"
        before = digest(path)
        rows = {case: [] for case, _, _ in cases}
        opener = gzip.open if path.suffix == ".gz" else open
        with opener(path, "rt") as stream:
            for line in stream:
                row = json.loads(line)
                if row["session_id"] in rows:
                    rows[row["session_id"]].append(row)
        if digest(path) != before:
            raise ValueError("source recording changed")
        provenance[label] = {"trajectory": str(path), "sha256": before,
                             "report_sha256": digest(folder / "probe.json")}
        for col, (case, stop, span) in enumerate(cases):
            full = rows[case]
            selected = [row for row in full if span[0] <= row["session_time_s"] <= span[1]]
            if not full:
                raise ValueError("missing selected session")
            for index, (field, title) in enumerate(fields):
                ax = axes[index, col]
                ax.plot([row["session_time_s"] for row in selected],
                        [row[field] for row in selected], label=label, color=color, linewidth=1.6)
                if selected and selected[-1]["fell"]:
                    ax.scatter([selected[-1]["session_time_s"]], [selected[-1][field]],
                               marker="x", color=color, zorder=5)
                ax.set_ylabel(title)
            if not selected:
                axes[0, col].text(.03, .93 - .12 * lanes.index((label, name, color)),
                                 f"{label}: recording ended at {full[-1]['session_time_s']:.2f}s",
                                 transform=axes[0, col].transAxes, color=color, fontsize=8)
    for col, (case, stop, span) in enumerate(cases):
        axes[0, col].set_title(case.replace("-", " "), fontsize=11)
        for ax in axes[:, col]:
            ax.axvline(stop, color="#969696", linestyle="--", linewidth=1)
            ax.set_xlim(*span)
            ax.grid(alpha=.2)
        axes[-1, col].set_xlabel("Recorded session time (s); dashed line = stop request")
    axes[0, 0].legend(fontsize=8)
    fig.suptitle("V54 stop diagnostics — actual recorded feedback rollouts", fontsize=14)
    args.output.mkdir(parents=True)
    fig.savefig(args.output / "stop-telemetry.png", dpi=180)
    plt.close(fig)
    shutil.copy2(__file__, args.output / Path(__file__).name)
    result = {"sources": provenance, "cases": [case for case, _, _ in cases],
              "figure_sha256": digest(args.output / "stop-telemetry.png"),
              "boundary": "Post-hoc zooms of two exposed sessions. Crosses mark recorded falls; curves end at terminal recording. Policies take different actions, so this is not a physics-isolation replay. No gate thresholds, trajectories or actions are changed."}
    (args.output / "provenance.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
