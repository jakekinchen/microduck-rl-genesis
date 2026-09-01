"""The Genesis BAM path must consume the pinned authoritative fixtures."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from microduck.bam_actuator import BamActuator
from microduck.constants import (
    BAM_KP_FW,
    BAM_XL330_M6_JSON,
    XL330_ERROR_GAIN,
    XL330_MAX_CURRENT,
    XL330_MAX_PWM,
)

FIXTURE = (
    ROOT
    / "microduck_contract"
    / "actuator"
    / "fixtures"
    / "bam-m6-xl330-v1-open-loop.json"
)


class ResetProbe:
    def __init__(self) -> None:
        self.env_ids = None

    def reset(self, env_ids) -> None:
        self.env_ids = env_ids.clone()


def actuator_from_parameters() -> BamActuator:
    params = json.loads(Path(BAM_XL330_M6_JSON).read_text())
    actuator = object.__new__(BamActuator)
    for name in (
        "kt",
        "R",
        "friction_base",
        "friction_stribeck",
        "load_friction_motor",
        "load_friction_external",
        "load_friction_motor_stribeck",
        "load_friction_external_stribeck",
        "load_friction_motor_quad",
        "load_friction_external_quad",
        "dtheta_stribeck",
        "alpha",
        "friction_viscous",
    ):
        setattr(actuator, name, float(params[name]))
    actuator.kp_fw = BAM_KP_FW
    actuator.error_gain = XL330_ERROR_GAIN
    actuator.max_current = XL330_MAX_CURRENT
    actuator.max_pwm = XL330_MAX_PWM
    actuator.friction_scale = torch.ones((1, 1), dtype=torch.float64)
    return actuator


def close(actual: torch.Tensor, expected: float, tolerance: float, label: str) -> None:
    error = abs(float(actual.item()) - expected)
    assert error <= tolerance, f"{label}: {error:.3e} > {tolerance:.3e}"


def main() -> int:
    fixture = json.loads(FIXTURE.read_text())
    assert fixture["authority"]["commit"] == (
        "62bd8ce12154340be97e06f7f41a0ca8f116d967"
    )
    tolerance = fixture["generation"]["float64_absolute_tolerance"]
    actuator = actuator_from_parameters()

    max_errors = {
        "control_voltage_v": 0.0,
        "motor_torque_nm": 0.0,
        "bam_core_frictionloss_nm": 0.0,
        "mjlab_deployed_frictionloss_nm": 0.0,
    }
    for row in fixture["vectors"]:
        inputs = row["input"]
        expected = row["expected"]
        tensor = lambda value: torch.tensor([[value]], dtype=torch.float64)
        target = tensor(inputs["q_target_rad"])
        position = tensor(inputs["q_rad"])
        velocity = tensor(inputs["dq_rad_s"])
        vin = tensor(inputs["vin_v"])
        kp = tensor(BAM_KP_FW)
        voltage = actuator._control_voltage(target, position, velocity, vin, kp)
        torque = actuator._motor_torque(voltage, velocity)
        stribeck = actuator._stribeck_coefficient(velocity)
        motor_load = tensor(inputs["friction_motor_torque_nm"])
        external_load = tensor(inputs["friction_external_torque_nm"])

        for gate, field in (
            (True, "bam_core_frictionloss_nm"),
            (False, "mjlab_deployed_frictionloss_nm"),
        ):
            actuator.quadratic_sign_gate = gate
            friction = actuator._friction_budget(
                motor_load, external_load, stribeck
            )
            error = abs(float(friction.item()) - expected[field])
            max_errors[field] = max(max_errors[field], error)
            close(friction, expected[field], tolerance, f"{row['id']} {field}")

        voltage_error = abs(float(voltage.item()) - expected["control_voltage_v"])
        torque_error = abs(float(torque.item()) - expected["motor_torque_nm"])
        max_errors["control_voltage_v"] = max(
            max_errors["control_voltage_v"], voltage_error
        )
        max_errors["motor_torque_nm"] = max(
            max_errors["motor_torque_nm"], torque_error
        )
        close(voltage, expected["control_voltage_v"], tolerance, row["id"])
        close(torque, expected["motor_torque_nm"], tolerance, row["id"])

    reset = fixture["reset_fixture"]
    actuator.prev_torque = torch.tensor(
        reset["prev_motor_torque_before_nm"], dtype=torch.float64
    )
    actuator.vin_nominal = torch.tensor(reset["vin_before_v"], dtype=torch.float64)
    actuator._delay = ResetProbe()
    env_ids = torch.tensor(reset["env_ids"])
    actuator.reset(env_ids)
    assert actuator.prev_torque.tolist() == reset["prev_motor_torque_after_nm"]
    assert actuator.vin_nominal.tolist() == reset["vin_after_v"]
    assert torch.equal(actuator._delay.env_ids, env_ids)

    print(f"{len(fixture['vectors'])} pinned BAM vectors verified")
    for name, error in max_errors.items():
        print(f"{name}: max error {error:.3e}")
    print("reset state verified; battery voltage preserved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
