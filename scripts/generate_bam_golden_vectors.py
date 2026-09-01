#!/usr/bin/env python3
"""Generate BAM M6 golden vectors from an exact Rhoban/BAM checkout.

This generator intentionally imports and executes the pinned authority. It must
run in an environment that provides the official mjlab dependencies because it
captures both BAM core behavior and the deployed ``bam.mjlab`` profile.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_COMMIT = "62bd8ce12154340be97e06f7f41a0ca8f116d967"
AUTHORITY_URL = "https://github.com/Rhoban/bam.git"
PARAMETER_PATH = ROOT / "microduck" / "assets" / "xl330_m6.json"
DEFAULT_OUTPUT = (
    ROOT
    / "microduck_contract"
    / "actuator"
    / "fixtures"
    / "bam-m6-xl330-v1-open-loop.json"
)


def command(*args: str, cwd: Path) -> str:
    return subprocess.check_output(args, cwd=cwd, text=True).strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def cases() -> list[dict[str, float | str]]:
    edge = [
        ("zero", 0.0, 0.0, 0.0, 7.35, 0.0, 0.0),
        ("positive_error", 0.5, 0.0, 0.0, 7.35, 0.1, -0.2),
        ("negative_error", -0.5, 0.0, 0.0, 7.35, -0.1, 0.2),
        ("positive_pwm_clip", 2.0, -2.0, 0.0, 6.5, 0.5, -0.5),
        ("negative_pwm_clip", -2.0, 2.0, 0.0, 8.2, -0.5, 0.5),
        ("positive_back_emf", 0.4, 0.1, 8.0, 7.35, 0.4, 0.2),
        ("negative_back_emf", -0.4, -0.1, -8.0, 7.35, -0.4, -0.2),
        ("high_speed_positive", 0.0, 0.0, 30.0, 6.5, 0.2, 0.1),
        ("high_speed_negative", 0.0, 0.0, -30.0, 6.5, -0.2, -0.1),
        ("same_sign_drive", 0.2, 0.0, 0.01, 8.2, 0.6, 0.1),
        ("same_sign_backdrive", 0.2, 0.0, -0.01, 8.2, 0.1, 0.6),
        ("opposite_sign_drive", 0.2, 0.0, 0.25, 7.35, 0.6, -0.1),
        ("opposite_sign_backdrive", -0.2, 0.0, -0.25, 7.35, -0.1, 0.6),
    ]
    output = [
        {
            "id": item[0],
            "q_target_rad": item[1],
            "q_rad": item[2],
            "dq_rad_s": item[3],
            "vin_v": item[4],
            "friction_motor_torque_nm": item[5],
            "friction_external_torque_nm": item[6],
        }
        for item in edge
    ]
    rng = np.random.default_rng(20260901)
    for index in range(16):
        output.append(
            {
                "id": f"seeded_{index:02d}",
                "q_target_rad": float(rng.uniform(-1.5, 1.5)),
                "q_rad": float(rng.uniform(-1.5, 1.5)),
                "dq_rad_s": float(rng.uniform(-12.0, 12.0)),
                "vin_v": float(rng.uniform(6.5, 8.2)),
                "friction_motor_torque_nm": float(rng.uniform(-0.7, 0.7)),
                "friction_external_torque_nm": float(rng.uniform(-0.7, 0.7)),
            }
        )
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bam-repo", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    bam_repo = args.bam_repo.resolve()
    output = args.output.resolve()

    head = command("git", "rev-parse", "HEAD", cwd=bam_repo)
    if head != AUTHORITY_COMMIT:
        raise SystemExit(f"BAM authority mismatch: expected {AUTHORITY_COMMIT}, got {head}")
    if command("git", "status", "--porcelain", cwd=bam_repo):
        raise SystemExit("BAM authority checkout is dirty")

    sys.path.insert(0, os.fspath(bam_repo))
    import bam  # noqa: PLC0415
    from bam.mjlab import BamActuator as AuthorityMjlabActuator  # noqa: PLC0415
    from bam.model import load_model  # noqa: PLC0415

    if not Path(bam.__file__).resolve().is_relative_to(bam_repo):
        raise SystemExit(f"Imported BAM from wrong path: {bam.__file__}")

    model = load_model(os.fspath(PARAMETER_PATH))
    model.actuator.kp = 200.0
    deployed = object.__new__(AuthorityMjlabActuator)
    deployed._bam_model = model

    vector_rows = []
    for item in cases():
        model.actuator.vin = float(item["vin_v"])
        control = float(
            model.actuator.compute_control(
                float(item["q_target_rad"]),
                float(item["q_rad"]),
                float(item["dq_rad_s"]),
                0.005,
            )
        )
        torque = float(
            model.actuator.compute_torque(
                control,
                True,
                float(item["q_rad"]),
                float(item["dq_rad_s"]),
            )
        )
        core_friction, damping = model.compute_frictions(
            float(item["friction_motor_torque_nm"]),
            float(item["friction_external_torque_nm"]),
            float(item["dq_rad_s"]),
        )
        dtype = torch.float64
        motor = torch.tensor([[item["friction_motor_torque_nm"]]], dtype=dtype)
        external = torch.tensor([[item["friction_external_torque_nm"]]], dtype=dtype)
        velocity = torch.tensor([[item["dq_rad_s"]]], dtype=dtype)
        stribeck = torch.exp(
            -torch.pow(
                torch.abs(velocity) / model.dtheta_stribeck.value,
                model.alpha.value,
            )
        )
        mjlab_friction = float(
            AuthorityMjlabActuator._compute_friction_budget(
                deployed, motor, external, stribeck
            ).item()
        )
        vector_rows.append(
            {
                "id": item["id"],
                "input": {key: value for key, value in item.items() if key != "id"},
                "expected": {
                    "control_voltage_v": control,
                    "motor_torque_nm": torque,
                    "friction_viscous_nms_rad": float(damping),
                    "bam_core_frictionloss_nm": float(core_friction),
                    "mjlab_deployed_frictionloss_nm": mjlab_friction,
                },
            }
        )

    deployed._delay_buffer = None
    deployed._prev_motor_torque = torch.tensor(
        [[1.0, -2.0], [3.0, -4.0]], dtype=torch.float64
    )
    deployed.vin_tensor = torch.tensor([[6.5], [8.2]], dtype=torch.float64)
    reset_before = deployed._prev_motor_torque.tolist()
    vin_before = deployed.vin_tensor.tolist()
    AuthorityMjlabActuator.reset(deployed, torch.tensor([1]))

    source_files = {}
    for relative in ("bam/actuator.py", "bam/model.py", "bam/mjlab.py", "LICENSE"):
        source_files[relative] = sha256(bam_repo / relative)

    payload = {
        "schema_version": "microduck.bam-golden-vectors/v1",
        "authority": {
            "repository_url": AUTHORITY_URL,
            "commit": head,
            "branch_context": "mjlab_frictionloss",
            "tree": command("git", "rev-parse", "HEAD^{tree}", cwd=bam_repo),
            "commit_date": command("git", "show", "-s", "--format=%aI", cwd=bam_repo),
            "license": "Apache-2.0",
            "source_files": source_files,
            "parameter_file": "microduck/assets/xl330_m6.json",
            "parameter_sha256": sha256(PARAMETER_PATH),
        },
        "generation": {
            "script": "scripts/generate_bam_golden_vectors.py",
            "command": (
                "python scripts/generate_bam_golden_vectors.py "
                "--bam-repo <clean-checkout-at-authority-commit>"
            ),
            "seed": 20260901,
            "physics_dt_s": 0.005,
            "firmware_kp": 200.0,
            "float64_absolute_tolerance": 1e-12,
            "float32_absolute_tolerance": 1e-6,
        },
        "profiles": {
            "bam_core": {
                "id": "bam-core-v1",
                "quadratic_sign_gate": True,
            },
            "mjlab_deployed": {
                "id": "mjlab-deployed-v1",
                "quadratic_sign_gate": False,
                "documented_divergence": (
                    "Pinned bam.mjlab omits the BAM core quadratic opposite-sign gate."
                ),
            },
        },
        "vectors": vector_rows,
        "reset_fixture": {
            "profile": "mjlab-deployed-v1",
            "env_ids": [1],
            "prev_motor_torque_before_nm": reset_before,
            "prev_motor_torque_after_nm": deployed._prev_motor_torque.tolist(),
            "vin_before_v": vin_before,
            "vin_after_v": deployed.vin_tensor.tolist(),
            "core_model_reset": "stateless_noop",
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    try:
        display_path = output.relative_to(ROOT)
    except ValueError:
        display_path = output
    print(f"wrote {display_path} with {len(vector_rows)} vectors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
