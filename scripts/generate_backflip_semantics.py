#!/usr/bin/env python3
"""Freeze the base flat backflip semantics from pinned source and local port.

The source task is imported from a git archive of the exact authority commit.
Only ``make_microduck_backflip_env_cfg`` is inspected: specialist, pedestal,
mat, captured-state, and evaluation variants are deliberately excluded.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import subprocess
import sys
import tarfile
import tempfile
import types
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "microduck_contract" / "tasks" / "backflip-v1.json"
OFFICIAL_COMMIT = "8bde27eb141c8f14db05fc4370e536521203a98d"
BAM_COMMIT = "62bd8ce12154340be97e06f7f41a0ca8f116d967"
OFFICIAL_FILES = (
    "src/mjlab_microduck/tasks/microduck_backflip_env_cfg.py",
    "src/mjlab_microduck/tasks/backflip_actions.py",
    "src/mjlab_microduck/tasks/mdp.py",
    "src/mjlab_microduck/robot/microduck_constants.py",
)
LOCAL_FILES = (
    "microduck/constants.py",
    "microduck/velocity_cfg.py",
    "microduck/velocity_env.py",
    "microduck/backflip_cfg.py",
    "microduck/backflip_env.py",
    "scripts/generate_backflip_semantics.py",
)
EXTRACT_MARKER = "MICRODUCK_BACKFLIP_SNAPSHOT="


def load_source_module(name: str, source: Path):
    spec = importlib.util.spec_from_file_location(name, source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def command(*args: str, cwd: Path) -> str:
    return subprocess.check_output(args, cwd=cwd, text=True).strip()


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if hasattr(value, "value") and isinstance(value.value, (bool, int, float, str)):
        return value.value
    if hasattr(value, "__dict__"):
        return {
            key: jsonable(item)
            for key, item in vars(value).items()
            if not key.startswith("_")
        }
    return repr(value)


def clean_params(params: dict[str, Any]) -> dict[str, Any]:
    return {
        key: jsonable(value)
        for key, value in params.items()
        if key not in {"asset_cfg"}
    }


def noise(term: Any) -> list[float] | None:
    value = getattr(term, "noise", None)
    if value is None:
        return None
    return [float(value.n_min), float(value.n_max)]


def official_snapshot() -> dict[str, Any]:
    """Child entrypoint executed inside the locked official mjlab runtime."""
    from mjlab_microduck.tasks import mdp as backflip_mdp  # type: ignore
    from mjlab_microduck.tasks.microduck_backflip_env_cfg import (  # type: ignore
        EPISODE_LENGTH_S,
        STAND_Z,
        make_microduck_backflip_env_cfg,
    )

    cfg = make_microduck_backflip_env_cfg(play=False)
    actor = cfg.observations["actor"].terms
    critic = cfg.observations["critic"].terms
    action = cfg.actions["joint_pos"]
    twist = cfg.commands["twist"]
    reset = cfg.events["set_backflip_state"].params
    assist = cfg.events["backflip_assistive_wrench"].params

    rewards = {
        name: {
            "function": term.func.__name__,
            "weight": float(term.weight),
            "params": clean_params(term.params),
        }
        for name, term in cfg.rewards.items()
    }
    events = {
        name: {
            "function": term.func.__name__,
            "mode": term.mode,
            "interval_s": jsonable(term.interval_range_s),
            "params": clean_params(term.params),
        }
        for name, term in cfg.events.items()
    }
    curricula = {
        name: {"function": term.func.__name__, "params": clean_params(term.params)}
        for name, term in cfg.curriculum.items()
    }
    robot = cfg.scene.entities["robot"]
    collision = robot.collisions[0]
    return {
        "variant": "base_flat_only",
        "control": {
            "physics_dt_s": float(cfg.sim.mujoco.timestep),
            "decimation": int(cfg.decimation),
            "control_hz": round(1.0 / (cfg.sim.mujoco.timestep * cfg.decimation)),
            "episode_length_s": float(EPISODE_LENGTH_S),
        },
        "action": {
            "dimension": 14,
            "scale": float(action.scale),
            "offset": "default_joint_position" if action.use_default_offset else action.offset,
            "configured_clip": action.clip,
            "min_assisted_authority": float(action.min_assisted_authority),
            "full_authority_after_angle_rad": action.full_authority_after_angle_rad,
        },
        "commands": {
            "twist": {
                "dimension": 3,
                "resampling_time_s": list(twist.resampling_time_range),
                "ranges": {
                    "lin_vel_x_m_s": list(twist.ranges.lin_vel_x),
                    "lin_vel_y_m_s": list(twist.ranges.lin_vel_y),
                    "ang_vel_z_rad_s": list(twist.ranges.ang_vel_z),
                },
                "heading_command": bool(twist.heading_command),
            },
            "head_command": {"dimension": 4, "value": "zero_padding"},
            "body_command": {
                "dimension": 6,
                "layout": ["bounded_phase", "assist_scale", "zero", "zero", "zero", "zero"],
                "timing_scale_s": float(actor["body_command"].params["timing_scale_s"]),
            },
        },
        "actor_observation": {
            "terms": list(actor),
            "dimension": 61,
            "noise": {name: noise(term) for name, term in actor.items()},
            "delay_control_steps": {
                name: [int(term.delay_min_lag), int(term.delay_max_lag)]
                for name, term in actor.items()
            },
            "delay_update_period": {
                name: int(term.delay_update_period) for name, term in actor.items()
            },
            "encoder_bias_actor_only": bool(actor["joint_pos"].params.get("biased")),
            "imu_misalignment_max_deg": float(actor["base_ang_vel"].params["max_angle_deg"]),
        },
        "critic_observation": {
            "terms": list(critic),
            "dimension": 74,
            "layout_sizes": {
                "base_lin_vel": 3, "base_ang_vel": 3, "projected_gravity": 3,
                "joint_pos": 14, "joint_vel": 14, "actions": 14, "command": 3,
                "foot_air_time": 2, "foot_contact": 2, "foot_contact_forces": 6,
                "head_command": 4, "body_command": 6,
            },
        },
        "collision": {
            "full_body": list(collision.geom_names_expr) == [".*_collision"],
            "disable_other_geoms": bool(collision.disable_other_geoms),
            "foot_contact_dim": int(collision.condim["^(left|right)_foot_collision$"]),
            "other_contact_dim": int(collision.condim[".*_collision"]),
            "sensors": [sensor.name for sensor in cfg.scene.sensors],
        },
        "rewards": rewards,
        "terminations": {
            name: {
                "function": term.func.__name__,
                "time_out": bool(term.time_out),
                "params": clean_params(term.params),
            }
            for name, term in cfg.terminations.items()
        },
        "events": events,
        "curricula": curricula,
        "reset": clean_params(reset),
        "assistance": clean_params(assist),
        "success_state": {
            "stand_z_m": float(STAND_Z),
            "minimum_takeoff_z_m": float(backflip_mdp._BACKFLIP_MIN_TAKEOFF_Z),
            "landing_rotation_gate_rad": math.radians(320.0),
            "landing_tilt_max_deg": 35.0,
            "landing_z_min_m": 0.085,
            "stable_rotation_min_rad": 2.0 * math.pi,
            "stable_tilt_max_deg": 20.0,
            "stable_z_min_m": 0.095,
            "stable_angular_speed_max_rad_s": 2.0,
            "stable_hold_s": float(backflip_mdp._BACKFLIP_STABLE_HOLD_S),
            "rotation_accumulation": "backward pitch only while collision-free airborne and lateral axis is within 30 degrees of horizontal",
            "flight_end": "first robot-ground recontact",
            "success_latch": "feet-supported stable state held continuously after a landed latch",
        },
    }


def local_snapshot() -> dict[str, Any]:
    c = load_source_module("backflip_contract_constants", ROOT / "microduck" / "constants.py")
    # Load the two pure-data modules under their package names without running
    # microduck.__init__, which imports the Genesis runtime.
    package = types.ModuleType("microduck")
    package.__path__ = [os.fspath(ROOT / "microduck")]
    sys.modules["microduck"] = package
    v = load_source_module("microduck.velocity_cfg", ROOT / "microduck" / "velocity_cfg.py")
    sys.modules["microduck.velocity_cfg"] = v
    b = load_source_module("microduck.backflip_cfg", ROOT / "microduck" / "backflip_cfg.py")
    layout = [{"name": name, "size": size} for name, size in c.OBS_LAYOUT]
    return {
        "variant": "base_flat_only",
        "control": {
            "physics_dt_s": v.SIM_DT,
            "decimation": v.DECIMATION,
            "control_hz": round(1.0 / (v.SIM_DT * v.DECIMATION)),
            "episode_length_s": b.EPISODE_LENGTH_S,
        },
        "action": {
            "dimension": c.NUM_ACTIONS,
            "joint_order": list(c.JOINT_NAMES),
            "scale": v.ACTION_SCALE,
            "offset": "default_joint_position",
            "filter": "none",
            "configured_clip": [-100.0, 100.0],
            "min_assisted_authority": b.ASSIST_MIN_ACTION_AUTHORITY,
        },
        "commands": {
            "twist": {"dimension": 3, "value": [0.0, 0.0, 0.0], "resampling": False},
            "head_command": {"dimension": 4, "value": "zero_padding"},
            "body_command": {
                "dimension": 6,
                "layout": ["bounded_phase", "assist_scale", "zero", "zero", "zero", "zero"],
                "timing_scale_s": b.ASSIST_START_S,
            },
        },
        "actor_observation": {
            "layout": layout,
            "dimension": c.NUM_OBS,
            "noise_half_ranges": dict(v.OBS_NOISE),
            "delay_control_steps": {
                name: list(values[:2]) for name, values in v.OBS_DELAY.items()
            },
            "delay_update_period": {
                name: values[2] for name, values in v.OBS_DELAY.items()
            },
            "encoder_bias_actor_only": True,
            "imu_misalignment_max_deg": v.IMU_ORIENTATION_RANDOMIZATION_ANGLE,
        },
        "critic_observation": {
            "dimension": c.NUM_OBS + 29,
            "layout": "actor_61_plus_privileged_29",
        },
        "collision": {
            "model": "microduck-allcollisions-v1",
            "full_body": True,
            "classification": "Genesis link contacts against ground",
        },
        "rewards": {name: float(weight) for name, weight in b.REWARD_WEIGHTS.items()},
        "reset": {
            "spawn_stages": [[step, list(probs)] for step, probs in b.SPAWN_STAGES],
            "tuck_overrides": {str(k): value for k, value in b.TUCK_OVERRIDES.items()},
            "crouch_overrides": {str(k): value for k, value in b.CROUCH_OVERRIDES.items()},
        },
        "assistance": {
            "start_time_s": b.ASSIST_START_S,
            "end_time_s": b.ASSIST_END_S,
            "upward_force_n": b.ASSIST_UPWARD_FORCE_N,
            "backward_pitch_torque_nm": b.ASSIST_BACKWARD_TORQUE_NM,
            "minimum_action_authority": b.ASSIST_MIN_ACTION_AUTHORITY,
            "initial_scale": 1.0,
            "decay_step": 0.05,
            "success_threshold": 0.60,
            "evaluation_window_episodes": 256,
        },
        "success_state": {
            "stand_z_m": b.STAND_Z,
            "minimum_takeoff_z_m": b.MIN_TAKEOFF_Z,
            "stable_hold_s": b.STABLE_HOLD_S,
            "rotation_accumulation": "backward pitch only while collision-free airborne and lateral axis is within 30 degrees of horizontal",
            "flight_end": "first robot-ground recontact",
        },
    }


def materialize_official(repo: Path, commit: str, destination: Path) -> Path:
    archive = destination / "official.tar"
    subprocess.check_call(
        ["git", "archive", "--format=tar", "-o", os.fspath(archive), commit], cwd=repo
    )
    with tarfile.open(archive) as stream:
        stream.extractall(destination, filter="data")
    return destination


def extract_official(
    repo: Path, commit: str, bam_repo: Path, official_python: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not official_python.is_file():
        raise SystemExit(f"missing official runtime {official_python}")
    resolved = command("git", "rev-parse", f"{commit}^{{commit}}", cwd=repo)
    if resolved != OFFICIAL_COMMIT:
        raise SystemExit(f"backflip authority must be {OFFICIAL_COMMIT}, got {resolved}")
    if command("git", "status", "--porcelain", cwd=repo):
        raise SystemExit("backflip authority checkout must be clean")
    bam_resolved = command("git", "rev-parse", "HEAD^{commit}", cwd=bam_repo)
    if bam_resolved != BAM_COMMIT:
        raise SystemExit(f"BAM authority must be {BAM_COMMIT}, got {bam_resolved}")
    if command("git", "status", "--porcelain", cwd=bam_repo):
        raise SystemExit("BAM authority checkout must be clean")
    tree = command("git", "show", "-s", "--format=%T", resolved, cwd=repo)
    commit_date = command("git", "show", "-s", "--format=%aI", resolved, cwd=repo)
    with tempfile.TemporaryDirectory(prefix="microduck-backflip-authority-") as temp:
        official_root = materialize_official(repo, resolved, Path(temp))
        env = os.environ.copy()
        env["PYTHONPATH"] = os.pathsep.join(
            [os.fspath(official_root / "src"), os.fspath(bam_repo)]
        )
        env["MJLAB_WARP_QUIET"] = "1"
        output = subprocess.check_output(
            [os.fspath(official_python), os.fspath(Path(__file__).resolve()), "--extract-official"],
            cwd=ROOT,
            env=env,
            text=True,
        )
        marked = [line for line in output.splitlines() if line.startswith(EXTRACT_MARKER)]
        if len(marked) != 1:
            raise SystemExit("official backflip extractor did not emit one snapshot")
        snapshot = json.loads(marked[0][len(EXTRACT_MARKER) :])
        digests = {name: sha256(official_root / name) for name in OFFICIAL_FILES}
    return snapshot, {
        "commit": resolved,
        "tree": tree,
        "commit_date": commit_date,
        "source_digests": digests,
        "entrypoint": "make_microduck_backflip_env_cfg(play=False)",
    }


def require_equal(label: str, official: Any, genesis: Any) -> None:
    if official != genesis:
        raise SystemExit(
            f"unclassified semantic mismatch for {label}:\n"
            f"official={official!r}\ngenesis={genesis!r}"
        )


def verify_shared_fields(official: dict[str, Any], genesis: dict[str, Any]) -> None:
    require_equal("variant", official["variant"], genesis["variant"])
    require_equal("control", official["control"], genesis["control"])
    for name in ("dimension", "scale", "offset", "min_assisted_authority"):
        require_equal(f"action.{name}", official["action"][name], genesis["action"][name])
    require_equal("actor.dimension", official["actor_observation"]["dimension"], genesis["actor_observation"]["dimension"])
    require_equal("actor.imu", official["actor_observation"]["imu_misalignment_max_deg"], genesis["actor_observation"]["imu_misalignment_max_deg"])
    require_equal("actor.encoder_bias", official["actor_observation"]["encoder_bias_actor_only"], genesis["actor_observation"]["encoder_bias_actor_only"])
    require_equal("head command", official["commands"]["head_command"], genesis["commands"]["head_command"])
    require_equal("body command", official["commands"]["body_command"], genesis["commands"]["body_command"])
    require_equal("collision.full_body", official["collision"]["full_body"], genesis["collision"]["full_body"])
    for name in ("stand_z_m", "minimum_takeoff_z_m", "stable_hold_s", "rotation_accumulation", "flight_end"):
        require_equal(f"success.{name}", official["success_state"][name], genesis["success_state"][name])
    for name, local_weight in genesis["rewards"].items():
        if name == "backflip_body_contact":
            official_weight = official["curricula"]["body_contact_weight"]["params"]["weight_stages"][0]["weight"]
        else:
            official_weight = official["rewards"][name]["weight"]
        require_equal(f"reward.{name}", official_weight, local_weight)
    assist = official["assistance"]
    mapping = {
        "start_time_s": "start_time_s", "end_time_s": "end_time_s",
        "upward_force_n": "upward_force_n",
        "backward_pitch_torque_nm": "backward_pitch_torque_nm",
    }
    for official_name, local_name in mapping.items():
        require_equal(f"assistance.{official_name}", assist[official_name], genesis["assistance"][local_name])
    reset = official["reset"]
    require_equal("assistance.initial_scale", reset["initial_assist_scale"], genesis["assistance"]["initial_scale"])
    require_equal("assistance.decay_step", reset["assist_decay_step"], genesis["assistance"]["decay_step"])
    require_equal("assistance.threshold", reset["assist_success_threshold"], genesis["assistance"]["success_threshold"])
    require_equal("assistance.window", reset["assist_evaluation_window"], genesis["assistance"]["evaluation_window_episodes"])
    stages = []
    for row in official["curricula"]["backflip_spawn_mix"]["params"]["param_stages"]:
        p = row["params"]
        stages.append([row["step"], [p["standing_prob"], p["crouch_prob"], p["midflight_prob"], p["recovery_prob"]]])
    require_equal("reset.spawn_stages", stages, genesis["reset"]["spawn_stages"])


def semantic_inventory() -> list[dict[str, str]]:
    rows = [
        ("source.variant", "exact", "base flat factory only; specialist, pedestal, mat, and captured-state factories excluded"),
        ("control.physics_timing", "exact", "5 ms physics, decimation 4, 50 Hz control, 4-second episode"),
        ("action.dimension_order", "exact", "14 joints bound by action-v1"),
        ("action.residual_authority", "equivalent", "same assist-scaled residual authority with 0.05 minimum"),
        ("action.input_guard", "versioned-divergence", "Genesis clips policy input to +/-100; official config has no clip"),
        ("actuator.bam_delay", "exact", "shared BAM lock and 3-6 physics-step deployed delay"),
        ("observation.actor_layout", "exact", "61D ordered actor interface"),
        ("observation.actor_noise_delay", "equivalent", "same ranges and lag schedules; backend RNG streams differ"),
        ("observation.task_slots", "exact", "zero head slot and [bounded phase, assist scale, 0, 0, 0, 0] body slot"),
        ("observation.critic", "versioned-divergence", "official backflip critic is 74D; Genesis is actor 61D plus privileged 29D"),
        ("commands.twist", "versioned-divergence", "official samples small near-zero twist; Genesis fixes twist to exact zero"),
        ("collision.full_body", "equivalent", "both use the all-collisions robot; contact realization differs"),
        ("sensing.contact", "versioned-divergence", "official named geom sensors versus Genesis ground-link contact classification"),
        ("reset.reverse_curriculum", "equivalent", "same standing/crouch/midflight/recovery populations and stages"),
        ("reset.midflight_ballistics", "equivalent", "same angle, height, rate, landing-height, and margin declarations"),
        ("reset.noise_and_pose", "equivalent", "same HOME anchors, crouch/tuck overrides, and declared perturbation ranges"),
        ("assistance.virtual_spotter", "equivalent", "same timed upward force and backward-pitch torque on eligible starts"),
        ("assistance.decay", "equivalent", "same 256-episode, 0.60 success threshold, 0.05 decrement"),
        ("flight.takeoff", "equivalent", "support precedes collision-free takeoff above 0.135 m"),
        ("flight.rotation", "equivalent", "backward pitch accumulates only during collision-free airborne flight under flatness gate"),
        ("landing.first_recontact", "equivalent", "first robot-ground recontact ends the flight; feet support gates landing"),
        ("success.stable_hold", "equivalent", "full revolution, upright height, low angular speed, foot support for 0.5 seconds"),
        ("termination.timeout_bounds_nan", "equivalent", "same 4-second, terrain-bound, and finite-state intent"),
        ("training.reward_terms", "versioned-divergence", "local port omits inherited official zero-weight terms and self-collision -0.1"),
        ("training.reward_lifecycle", "equivalent", "common backflip terms and active weights agree; manager lifecycle differs"),
        ("training.curricula", "equivalent", "spawn, preload, body-contact, action-rate, arrival, torque-rate, and landing schedules preserved"),
        ("training.mass_inertia_randomization", "versioned-divergence", "official pseudo-inertia scales trunk mass and inertia; Genesis changes trunk mass only"),
        ("training.randomization", "equivalent", "declared ranges otherwise preserved; backend RNG streams differ"),
        ("execution.random_stream", "backend-specific-unavailable", "framework RNG algorithms and draw ordering are not shared"),
        ("execution.step_lifecycle", "versioned-divergence", "manager and hand-written reset/event/reward ordering are not trajectory-identical"),
        ("physics.contact_solver", "backend-specific-unavailable", "solver and collision trajectories cannot be made byte-identical"),
        ("acceptance.ordinary_standing", "exact", "frozen evaluator starts only from ordinary standing HOME with all assistance disabled"),
    ]
    return [
        {"field": field, "classification": classification, "disposition": disposition}
        for field, classification, disposition in rows
    ]


def acceptance_contract() -> dict[str, Any]:
    seeds = list(range(42001, 42021))
    return {
        "suite_id": "microduck.backflip-acceptance.v1",
        "status": "preregistered_not_executed",
        "candidate_outcomes_inspected": False,
        "seeds": seeds,
        "seed_handling": {
            "stream": "sha256-counter-v1",
            "cell_key": "suite_id + start_population_id + decimal_seed",
            "state_sharing_between_cells": False,
            "realized_initial_state_must_be_recorded": True,
        },
        "commands": [{
            "id": "standing_backflip",
            "twist": [0.0, 0.0, 0.0],
            "head_command": [0.0, 0.0, 0.0, 0.0],
            "body_command": {
                "phase_slot": "deterministic bounded phase from episode time",
                "assist_scale": 0.0,
                "remaining": [0.0, 0.0, 0.0, 0.0],
            },
        }],
        "start_populations": [{
            "id": "ordinary_standing_home",
            "root_xyz_m": [0.0, 0.0, 0.115],
            "root_rpy_deg": [0.0, 0.0, 0.0],
            "joint_position": "HOME",
            "root_and_joint_velocity": "zero",
            "initial_flight_or_landing_latches": False,
        }],
        "assistance": {
            "virtual_upward_force": False,
            "virtual_pitch_torque": False,
            "residual_action_constraint": False,
            "reverse_curriculum_start": False,
            "midflight_initialization": False,
            "recovery_initialization": False,
            "reference_or_teacher_state": False,
            "pedestal_mat_cube_or_external_support": False,
            "state_or_action_correction": False,
            "early_termination_suppression": False,
        },
        "episode_duration_s": 4.0,
        "metrics": {
            "takeoff": {
                "support_observed_before_flight": True,
                "root_height_m_min": 0.135,
                "robot_ground_contact_during_flight": False,
            },
            "rotation": {
                "direction": "backward_pitch",
                "airborne_accumulated_angle_rad_min": 2.0 * math.pi,
                "uninterrupted_airborne_revolution": True,
                "rotation_credit_after_first_recontact": False,
            },
            "landing": {
                "first_recontact": "feet_only",
                "intervening_nonfoot_ground_contact_count_max": 0,
                "absolute_roll_pitch_deg_at_stability_max": 20.0,
                "root_height_m_at_stability_min": 0.095,
                "base_angular_speed_rad_s_at_stability_max": 2.0,
                "continuous_feet_supported_hold_s_min": 0.5,
            },
            "joint_and_torque_margin": {
                "joint_limit_margin_rad_min": 0.02,
                "torque_limit_exceedance_count_max": 0,
                "torque_saturation_fraction_max": 0.02,
            },
            "integrity": {
                "nan_or_inf_count_max": 0,
                "evaluator_error_count_max": 0,
                "policy_inference_deadline_ms": 20.0,
                "deadline_miss_count_max": 0,
                "deadline_measurement": "single-thread ONNX Runtime CPU after 10 untimed warmups; host profile locked separately",
            },
        },
        "aggregation": {
            "required_episode_count": len(seeds),
            "required_success_count": len(seeds),
            "all_start_seed_cells_required": True,
            "classification": "pass only when every episode satisfies every maneuver, margin, and integrity requirement",
            "ppo_return_is_success_metric": False,
        },
    }


def build_contract(
    official: dict[str, Any], authority: dict[str, Any], genesis: dict[str, Any]
) -> dict[str, Any]:
    verify_shared_fields(official, genesis)
    referenced = [
        "microduck_contract/tasks/backflip-v1.schema.json",
        "microduck_contract/interface/observation-v1.json",
        "microduck_contract/interface/action-v1.json",
        "microduck_contract/interface/control-v1.json",
        "microduck_contract/actuator/bam-m6-xl330-v1.lock.json",
        "microduck_contract/model/microduck-allcollisions-v1.lock.json",
        "microduck_contract/model/reconciliation-v1.lock.json",
    ]
    return {
        "$schema": "backflip-v1.schema.json",
        "schema_version": "microduck.backflip-task/v1",
        "task_id": "microduck.backflip.v1",
        "authority": {
            "official_backflip": authority,
            "bam_commit": BAM_COMMIT,
            "local_source_digests": {name: sha256(ROOT / name) for name in LOCAL_FILES},
            "referenced_contracts": {name: sha256(ROOT / name) for name in referenced},
        },
        "claim": {
            "state": "declared_semantics_with_versioned_divergences",
            "actor_interface": "exact",
            "training_trajectory_equivalence": False,
            "policy_success": "not_evaluated",
            "physical_authority": False,
        },
        "shared_deployed_contract": {
            "control": genesis["control"],
            "action": {key: genesis["action"][key] for key in ("dimension", "joint_order", "scale", "offset", "filter")},
            "actor_observation": genesis["actor_observation"],
            "commands": genesis["commands"],
            "collision_model": genesis["collision"]["model"],
            "actuator_delay_physics_steps": [3, 6],
            "default_joint_position_rad": load_source_module("backflip_home", ROOT / "microduck" / "constants.py").DEFAULT_JOINT_POS,
        },
        "training_only": {
            "official_mjlab": official,
            "genesis": genesis,
            "reverse_curriculum_and_virtual_spotter_are_not_acceptance": True,
            "reward_is_success_definition": False,
        },
        "semantic_inventory": semantic_inventory(),
        "acceptance": acceptance_contract(),
        "evidence_boundary": "This freezes declarations and a future ordinary-standing zero-assistance classifier battery. It does not report a trained policy, backflip success, held-out evaluation, transfer, or physical authority.",
    }


def validate_contract(value: dict[str, Any], verify_local: bool = True) -> None:
    if value.get("schema_version") != "microduck.backflip-task/v1":
        raise AssertionError("unexpected backflip schema")
    if value.get("task_id") != "microduck.backflip.v1":
        raise AssertionError("unexpected backflip task id")
    rows = value.get("semantic_inventory", [])
    fields = [row.get("field") for row in rows]
    if not fields or len(fields) != len(set(fields)):
        raise AssertionError("semantic inventory fields must be unique and nonempty")
    allowed = {"exact", "equivalent", "versioned-divergence", "backend-specific-unavailable"}
    for row in rows:
        if row.get("classification") not in allowed or not row.get("disposition"):
            raise AssertionError(f"unclassified semantic field: {row}")
    acceptance = value["acceptance"]
    if acceptance["status"] != "preregistered_not_executed" or acceptance["candidate_outcomes_inspected"]:
        raise AssertionError("backflip acceptance must remain preregistered and unexecuted")
    if any(acceptance["assistance"].values()):
        raise AssertionError("backflip acceptance assistance must be fully disabled")
    expected = len(acceptance["commands"]) * len(acceptance["seeds"]) * len(acceptance["start_populations"])
    if acceptance["aggregation"]["required_episode_count"] != expected:
        raise AssertionError("acceptance coverage count is stale")
    if acceptance["aggregation"]["required_success_count"] != expected:
        raise AssertionError("every preregistered episode must pass")
    if value["training_only"]["official_mjlab"]["variant"] != "base_flat_only":
        raise AssertionError("specialist backflip variant leaked into base contract")
    if verify_local:
        for name, digest in value["authority"]["local_source_digests"].items():
            if sha256(ROOT / name) != digest:
                raise AssertionError(f"backflip local source drift: {name}")
        for name, digest in value["authority"]["referenced_contracts"].items():
            if sha256(ROOT / name) != digest:
                raise AssertionError(f"backflip referenced contract drift: {name}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--official-repo", type=Path)
    parser.add_argument("--official-commit", default=OFFICIAL_COMMIT)
    parser.add_argument("--bam-repo", type=Path)
    parser.add_argument("--official-python", type=Path, default=ROOT / "validation" / "official-mjlab" / ".venv" / "bin" / "python")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--extract-official", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.extract_official:
        print(EXTRACT_MARKER + json.dumps(official_snapshot(), sort_keys=True))
        return 0
    if args.official_repo is None or args.bam_repo is None:
        parser.error("--official-repo and --bam-repo are required")
    official, authority = extract_official(
        args.official_repo.resolve(), args.official_commit, args.bam_repo.resolve(), args.official_python.absolute()
    )
    value = build_contract(official, authority, local_snapshot())
    validate_contract(value)
    expected = json_bytes(value)
    if args.check:
        actual = args.output.read_bytes() if args.output.exists() else b""
        if actual != expected:
            print(f"Backflip semantics are stale: {args.output}")
            return 1
        print("Backflip semantics verified against pinned authorities.")
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(expected)
    print(f"Backflip semantics written: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
