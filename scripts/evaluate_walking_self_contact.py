"""Add complete-body interference rejection beside an immutable old receipt."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import shutil
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--receipt", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    from scripts.evaluate_walking_heading import verify_input_manifest
    from scripts.evaluate_laser import digest
    from experiments.walking.collision_model import materialize
    from experiments.walking.self_contact import SelfContactProbe, evaluate_self_contact
    verify_input_manifest(a.receipt)
    original = json.loads((a.receipt/"evaluation.json").read_text())
    a.output.mkdir(parents=True, exist_ok=False)
    _, model = materialize(a.output/"model")
    probe = SelfContactProbe(model)
    rows = defaultdict(list)
    for line in (a.receipt/"trajectory.jsonl").open():
        row = json.loads(line)
        rows[row["case_id"]].append(row)
    cases = []
    for case in original["case_reports"]:
        result = {"case_id": case["case_id"], **evaluate_self_contact(rows.pop(case["case_id"], []), probe),
                  "original_reported_passed": case["passed"]}
        cases.append(result)
        print(json.dumps(result), flush=True)
    if rows:
        raise ValueError("unreported trace cases")
    report = {"schema": "microduck.walking-self-contact-rejection/v1", "case_reports": cases,
              "passed_cases": sum(c["passed"] for c in cases), "total_cases": len(cases),
              "policy_sha256": original["policy_sha256"],
              "input_manifest_sha256": digest(a.receipt/"SHA256SUMS"),
              "input_trace_sha256": digest(a.receipt/"trajectory.jsonl"),
              "model_sha256": digest(model), "held_out": False, "acceptance_eligible": False,
              "boundary": "Additive visible-development copied-state self-contact rejection only. Original scores and files remain unchanged; passing does not imply dynamics, whole-task or physical acceptance."}
    (a.output/"evaluation.json").write_text(json.dumps(report, indent=2)+"\n")
    for name in ("scripts/evaluate_walking_self_contact.py", "experiments/walking/self_contact.py",
                 "experiments/walking/collision_model.py", "experiments/walking/COLLISION-v11.md",
                 "tests/test_walking_self_contact.py", "tests/test_walking_collision_model.py",
                 "microduck/assets/microduck/scene.xml", "microduck/assets/microduck/robot_allcollisions.xml"):
        dest = a.output/"source"/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT/name, dest)
    assets = ROOT/"microduck/assets/microduck/assets"
    (a.output/"mesh-input-sha256.json").write_text(json.dumps({str(f.relative_to(ROOT)): digest(f) for f in sorted(assets.iterdir()) if f.is_file()}, indent=2)+"\n")
    (a.output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.relative_to(a.output)}\n" for f in sorted(a.output.rglob("*")) if f.is_file()))


if __name__ == "__main__":
    main()
