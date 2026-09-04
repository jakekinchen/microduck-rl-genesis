#!/usr/bin/env python3
"""Verify the exact rejected and accepted Genesis wheel API surfaces."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path


SOLVER_PATH = "genesis/engine/solvers/rigid/rigid_solver.py"
EXPECTED = {
    "1.2.2": {
        "filename": "genesis_world-1.2.2-py3-none-any.whl",
        "wheel_sha256": "567d49f287e597b7118421a8d63ed3259875a5f3906c0a4b8585fc21a9a0fb9a",
        "solver_sha256": "cf664fdc9bc7b7fda5560f12ef4bb56cd4837848d1449327891d2058b5117c7e",
        "dyn_state_assignment": False,
    },
    "1.3.3": {
        "filename": "genesis_world-1.3.3-py3-none-any.whl",
        "wheel_sha256": "74fcece3f080d2de86a25da9c26c979c192ed4a115d556133e8103169f74b3bf",
        "solver_sha256": "39e2af4ca559ece184ad4a12e8e59490f8127c89ced631299767a98ae58fd183",
        "dyn_state_assignment": True,
    },
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def probe(wheel_dir: Path) -> dict[str, object]:
    results: dict[str, object] = {}
    for version, expected in EXPECTED.items():
        wheel = wheel_dir / str(expected["filename"])
        assert wheel.is_file(), f"missing exact wheel: {wheel}"
        wheel_digest = digest(wheel.read_bytes())
        assert wheel_digest == expected["wheel_sha256"], f"wheel digest drift: {wheel.name}"
        with zipfile.ZipFile(wheel) as archive:
            solver = archive.read(SOLVER_PATH)
        solver_digest = digest(solver)
        assert solver_digest == expected["solver_sha256"], f"RigidSolver source drift: {wheel.name}"
        has_assignment = b"self.dyn_state = self.data_manager.dyn_state" in solver
        assert has_assignment is expected["dyn_state_assignment"], f"dyn_state API result drift: {wheel.name}"
        results[version] = {
            "dyn_state_assignment": has_assignment,
            "filename": wheel.name,
            "rigid_solver_sha256": f"sha256:{solver_digest}",
            "wheel_sha256": f"sha256:{wheel_digest}",
        }
    return {"probe": "genesis-wheel-rigid-solver-api/v1", "results": results}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheel-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(probe(args.wheel_dir), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
