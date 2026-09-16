"""Add heading-fidelity results beside an immutable completed walking receipt."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.evaluate_laser import digest
from experiments.walking.heading import evaluate_heading


def verify_input_manifest(receipt):
    receipt = receipt.resolve()
    required = {"training.json", "evaluation.json", "trajectory.jsonl", "policy.onnx"}
    covered = set()
    for line in (receipt / "SHA256SUMS").read_text().splitlines():
        expected, name = line.split("  ", 1)
        path = (receipt / name).resolve()
        if not path.is_relative_to(receipt) or digest(path) != expected:
            raise ValueError(f"input receipt manifest mismatch: {name}")
        covered.add(str(path.relative_to(receipt)))
    if not required <= covered:
        raise ValueError("input manifest does not cover all required final evidence")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = args.receipt.resolve()
    verify_input_manifest(receipt)
    training = json.loads((receipt / "training.json").read_text())
    original = json.loads((receipt / "evaluation.json").read_text())
    if training["status"] != "completed" or original["total_cases"] != 21:
        raise ValueError("completed final with 21-case report required")
    if digest(receipt / "policy.onnx") != original["policy_sha256"]:
        raise ValueError("policy digest mismatch")
    names = [case["case_id"] for case in original["case_reports"]]
    if len(names) != 21 or len(set(names)) != 21:
        raise ValueError("unique complete case bank required")
    rows = defaultdict(list)
    for line in (receipt / "trajectory.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row["case_id"] not in names:
            raise ValueError("unexpected trajectory case")
        rows[row["case_id"]].append(row)
    sources = {name: digest(ROOT / name) for name in (
        "scripts/evaluate_walking_heading.py", "experiments/walking/heading.py",
        "experiments/walking/HEADING-v1.md", "tests/test_walking_heading.py")}
    reports = []
    for case in original["case_reports"]:
        heading = evaluate_heading(rows[case["case_id"]])
        reports.append({"case_id": case["case_id"], "heading": heading,
                        "original_passed": case["passed"],
                        "combined_passed": case["passed"] and heading["passed"]})
    report = {"schema": "microduck.walking-heading-evaluation/v1", "held_out": False,
              "policy_sha256": original["policy_sha256"],
              "checkpoint_sha256": training["checkpoint_sha256"], "total_cases": 21,
              "original_passed_cases": original["passed_cases"],
              "heading_passed_cases": sum(case["heading"]["passed"] for case in reports),
              "combined_passed_cases": sum(case["combined_passed"] for case in reports),
              "case_reports": reports, "source_sha256": sources,
              "input_receipt": str(receipt),
              "input_sha256": {name: digest(receipt / name) for name in
                               ("SHA256SUMS", "evaluation.json", "trajectory.jsonl", "training.json")},
              "physical_transfer_validated": False,
              "boundary": "Additive exposed heading diagnostic on immutable final traces; preserves original scores. Neither hidden generalization nor physical calibration."}
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "evaluation.json").write_text(json.dumps(report, indent=2) + "\n")
    for name, expected in sources.items():
        target = args.output / "source" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
        if digest(target) != expected:
            raise ValueError("heading source changed")
    (args.output / "SHA256SUMS").write_text("".join(
        f"{digest(path)}  {path.relative_to(args.output)}\n"
        for path in sorted(args.output.rglob("*")) if path.is_file()))
    print(json.dumps({key: report[key] for key in
                     ("original_passed_cases", "heading_passed_cases", "combined_passed_cases", "total_cases")}))


if __name__ == "__main__":
    main()
