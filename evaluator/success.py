"""Backend-independent walking and backflip acceptance classifiers."""

from __future__ import annotations

import itertools
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _no_assistance(observed: dict[str, bool], required: dict[str, bool]) -> bool:
    return set(observed) == set(required) and not any(observed.values())


def expected_walking_cells(task: dict[str, Any]) -> set[tuple[str, str, int]]:
    a = task["acceptance"]
    return set(itertools.product(
        [row["id"] for row in a["commands"]],
        [row["id"] for row in a["start_populations"]],
        a["seeds"],
    ))


def classify_walking(episodes: list[dict[str, Any]], task: dict[str, Any]) -> dict[str, Any]:
    acceptance = task["acceptance"]
    expected = expected_walking_cells(task)
    actual = {(e["command_id"], e["start_population_id"], e["seed"]) for e in episodes}
    failures: list[str] = []
    if len(actual) != len(episodes) or actual != expected:
        failures.append("coverage")
    metrics = acceptance["metrics"]
    for episode in episodes:
        if not _no_assistance(episode["assistance"], acceptance["assistance"]):
            failures.append("assistance")
            break
        survival_min = metrics["survival"]["nominal_fraction_min"] if episode["start_population_id"] == "nominal_home" else metrics["survival"]["perturbed_fraction_min"]
        checks = {
            "survival": not episode["fell"] and episode["survival_fraction"] >= survival_min,
            "tracking": episode["linear_velocity_rmse_m_s"] <= metrics["tracking_after_warmup"]["linear_velocity_rmse_m_s_mean_max"] and episode["linear_velocity_error_m_s_p95"] <= metrics["tracking_after_warmup"]["linear_velocity_error_m_s_p95_max"] and episode["yaw_rate_rmse_rad_s"] <= metrics["tracking_after_warmup"]["yaw_rate_rmse_rad_s_mean_max"] and episode["yaw_rate_error_rad_s_p95"] <= metrics["tracking_after_warmup"]["yaw_rate_error_rad_s_p95_max"] and episode["head_pose_error_rad"] <= metrics["tracking_after_warmup"]["head_pose_error_rad_mean_max"] and episode["head_pose_error_rad_p95"] <= metrics["tracking_after_warmup"]["head_pose_error_rad_p95_max"],
            "stop": episode["stop_planar_displacement_m"] <= metrics["stop"]["planar_displacement_m_p95_max"] and episode["stop_absolute_yaw_change_rad"] <= metrics["stop"]["absolute_yaw_change_rad_p95_max"],
            "slip": episode["stance_speed_m_s"] <= metrics["foot_slip"]["stance_speed_m_s_max"] and episode["stance_speed_m_s_p95"] <= metrics["foot_slip"]["stance_speed_m_s_p95_max"],
            "orientation": episode["absolute_roll_pitch_deg"] <= metrics["orientation"]["absolute_roll_pitch_deg_max"] and episode["absolute_roll_pitch_deg_p95"] <= metrics["orientation"]["absolute_roll_pitch_deg_p95_max"],
            "margin": episode["joint_limit_margin_rad"] >= metrics["joint_and_torque_margin"]["joint_limit_margin_rad_min"] and episode["torque_saturation_fraction"] <= metrics["joint_and_torque_margin"]["torque_saturation_fraction_max"] and episode["torque_limit_exceedance_count"] == 0,
            "integrity": episode["deadline_miss_count"] == 0 and episode["nan_or_inf_count"] == 0 and episode["evaluator_error_count"] == 0,
        }
        failures.extend(name for name, passed in checks.items() if not passed)
    return {"task": "walking", "passed": not failures, "failures": sorted(set(failures)), "episode_count": len(episodes), "ppo_return_used": False}


def expected_backflip_cells(task: dict[str, Any]) -> set[tuple[str, int]]:
    a = task["acceptance"]
    return set(itertools.product([row["id"] for row in a["start_populations"]], a["seeds"]))


def classify_backflip(episodes: list[dict[str, Any]], task: dict[str, Any]) -> dict[str, Any]:
    acceptance = task["acceptance"]
    metrics = acceptance["metrics"]
    expected = expected_backflip_cells(task)
    actual = {(e["start_population_id"], e["seed"]) for e in episodes}
    failures: list[str] = []
    if len(actual) != len(episodes) or actual != expected:
        failures.append("coverage")
    for episode in episodes:
        if not _no_assistance(episode["assistance"], acceptance["assistance"]):
            failures.append("assistance")
            continue
        checks = {
            "ordinary_start": episode["ordinary_standing_start"] and not episode["initial_flight_or_landing_latches"],
            "takeoff": episode["support_before_flight"] and not episode["robot_ground_contact_during_flight"] and episode["takeoff_root_height_m"] >= metrics["takeoff"]["root_height_m_min"],
            "rotation": episode["uninterrupted_airborne"] and episode["airborne_backward_rotation_rad"] >= metrics["rotation"]["airborne_accumulated_angle_rad_min"] and not episode["rotation_credit_after_recontact"],
            "recontact": episode["first_recontact"] == "feet_only" and episode["intervening_nonfoot_ground_contacts"] == 0,
            "landing": episode["stable_hold_s"] >= metrics["landing"]["continuous_feet_supported_hold_s_min"] and episode["stable_roll_pitch_deg"] <= metrics["landing"]["absolute_roll_pitch_deg_at_stability_max"] and episode["stable_angular_speed_rad_s"] <= metrics["landing"]["base_angular_speed_rad_s_at_stability_max"] and episode["stable_root_height_m"] >= metrics["landing"]["root_height_m_at_stability_min"],
            "margin": episode["joint_limit_margin_rad"] >= metrics["joint_and_torque_margin"]["joint_limit_margin_rad_min"] and episode["torque_saturation_fraction"] <= metrics["joint_and_torque_margin"]["torque_saturation_fraction_max"] and episode["torque_limit_exceedance_count"] == 0,
            "integrity": episode["deadline_miss_count"] == 0 and episode["nan_or_inf_count"] == 0 and episode["evaluator_error_count"] == 0,
        }
        failures.extend(name for name, passed in checks.items() if not passed)
    return {"task": "backflip", "passed": not failures, "failures": sorted(set(failures)), "episode_count": len(episodes), "ppo_return_used": False}


def load_task(name: str) -> dict[str, Any]:
    return json.loads((ROOT / f"microduck_contract/tasks/{name}-v1.json").read_text())
