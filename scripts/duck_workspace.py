#!/usr/bin/env python3
"""One entry point for local workspace inspection and behavior drafts."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from duck_workspace.core import ROOT, Inspector, check_spec, doctor, new_behavior


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    status = sub.add_parser("status", help="current queue and discovered development receipts")
    status.add_argument("--json", action="store_true")
    sub.add_parser("doctor", help="read-only runtime, contract and BAM checks")
    from scripts.verify_workspace import add_arguments
    add_arguments(sub.add_parser("verify", help="run dependency-free workspace tooling tests"))
    studio = sub.add_parser("studio", help="serve the local read-only Duck Lab viewer")
    studio.add_argument("--port", type=int, default=8766)
    new = sub.add_parser("new", help="create a behavior draft; does not start training")
    new.add_argument("slug")
    new.add_argument("--request", required=True)
    check = sub.add_parser("check-spec", help="list incomplete planning fields; does not authorize execution")
    check.add_argument("path", type=Path)
    export = sub.add_parser("exchange-export", help="emit source-bound, read-only workspace metadata")
    export.add_argument("--owner-task", required=True, help="task responsible for this metadata export")
    inspect = sub.add_parser("exchange-inspect", help="validate metadata; never execute its entrypoints")
    inspect.add_argument("path", type=Path)
    inspect.add_argument("--source-root", type=Path, help="explicit matching repository for optional byte verification")
    sub.add_parser("exchange-conformance", help="check the shared synthetic metadata fixtures")
    sub.add_parser("prepare", help="inspect the active development case and next-experiment prerequisites; no launch")
    args = parser.parse_args()
    try:
        if args.command == "status":
            data = Inspector().snapshot()
            if args.json:
                print(json.dumps(data, indent=2, allow_nan=False))
            else:
                print(f"{data['branch']} @ {data['head'][:12]}\n{data['goal'].get('Current Milestone', 'Read GOAL.md')}")
                print(f"{len(data['evaluations'])} development evaluations; {len(data['training'])} training records; {len(data['errors'])} inspection errors")
                print("Worktree: " + ("changes present" if data["dirty"] else "clean"))
                for row in data["evaluations"]:
                    score = f"{row['passed']}/{row['total']}" if row['total'] else "see report"
                    print(f"  {row['name']}: {score}; {row['proof_class']}; {row['integrity']['status']}")
                for error in data["errors"]:
                    print(f"  Cannot inspect {error['path']}: {error['error']}")
                print("Open viewer: ./scripts/duck studio")
        elif args.command == "doctor":
            data = doctor()
            print(json.dumps(data, indent=2))
            return 0 if data["ready_for_evaluator_setup"] else 1
        elif args.command == "verify":
            from scripts.verify_workspace import verify
            return verify(args)
        elif args.command == "new":
            print(new_behavior(ROOT, args.slug, args.request))
        elif args.command == "check-spec":
            missing = check_spec(args.path)
            print(json.dumps({"missing": missing, "structurally_complete": not missing,
                              "execution_authorized": False, "note": "Structural check only; review the actual metrics, physics and budget."}, indent=2))
            return 1 if missing else 0
        elif args.command == "studio":
            from duck_workspace.server import serve
            serve(args.port)
        elif args.command == "exchange-export":
            from duck_workspace.exchange import export_workspace
            print(json.dumps(export_workspace(args.owner_task), indent=2, allow_nan=False))
        elif args.command == "exchange-inspect":
            from duck_workspace.exchange import load_packet, validate
            result = validate(load_packet(args.path), args.source_root)
            print(json.dumps(result, indent=2, allow_nan=False))
            return 0 if result["valid"] else 1
        elif args.command == "exchange-conformance":
            from duck_workspace.exchange import check_conformance
            result = check_conformance()
            print(json.dumps(result, indent=2, allow_nan=False))
            return 0 if result["passed"] else 1
        elif args.command == "prepare":
            from duck_workspace.active import prepare
            result = prepare()
            print(json.dumps(result, indent=2, allow_nan=False))
            return 0 if result["ready_for_diagnosis"] else 1
    except (OSError, ValueError) as error:
        parser.exit(1, f"duck: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
