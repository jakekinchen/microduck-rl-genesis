#!/usr/bin/env python3
"""Generate the committed walking task contract from pinned authorities.

The official mjlab configuration is imported from a git-archived commit using
the repo-owned optional runtime. The Genesis side is read from pure-data local
modules. The resulting document records exact agreements, semantic
equivalences, and every known backend divergence without executing a policy.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import subprocess
import tarfile
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "microduck_contract" / "tasks" / "walking-v1.json"
OFFICIAL_COMMIT = "109e06d4ce4921b635c5609e5304079fc30960ae"
BAM_COMMIT = "62bd8ce12154340be97e06f7f41a0ca8f116d967"
OFFICIAL_FILES = (
    "src/mjlab_microduck/tasks/microduck_velocity_env_cfg.py",
    "src/mjlab_microduck/tasks/mdp.py",
    "src/mjlab_microduck/robot/microduck_constants.py",
)
LOCAL_FILES = (
    "microduck/constants.py",
    "microduck/velocity_cfg.py",
    "microduck/velocity_env.py",
    "microduck/terrain.py",
    "scripts/generate_walking_semantics.py",
)
EXTRACT_MARKER = "MICRODUCK_WALKING_SNAPSHOT="


def load_source_module(name: str, source: Path):
    spec = importlib.util.spec_from_file_location(name, source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def command(*args: str, cwd: Path) -> str:
    return subprocess.check_output(args, cwd=cwd, text=True).strip()


def sha256_bytes(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


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


def noise(term: Any) -> list[float] | None:
    value = getattr(term, "noise", None)
    if value is None:
        return None
    return [float(value.n_min), float(value.n_max)]


def official_snapshot() -> dict[str, Any]:
    """Internal child entrypoint; runs inside the pinned official environment."""
    from mjlab_microduck.tasks.microduck_velocity_env_cfg import (  # type: ignore
        MicroduckRlCfg,
        make_microduck_velocity_env_cfg,
    )

    flat = make_microduck_velocity_env_cfg(play=False, rough=False)
    rough = make_microduck_velocity_env_cfg(play=False, rough=True)
    actor = flat.observations["actor"].terms
    critic = flat.observations["critic"].terms

    reward_params: dict[str, Any] = {}
    for name, term in flat.rewards.items():
        reward_params[name] = {
            "function": term.func.__name__,
            "weight": float(term.weight),
            "params": {
                key: jsonable(value)
                for key, value in term.params.items()
                if key != "asset_cfg"
            },
        }

    commands = flat.commands
    twist = commands["twist"]
    snapshot = {
        "control": {
            "physics_dt_s": float(flat.sim.mujoco.timestep),
            "decimation": int(flat.decimation),
            "control_hz": round(1.0 / (flat.sim.mujoco.timestep * flat.decimation)),
            "episode_length_s": float(flat.episode_length_s),
            "flat_solver_iterations": int(flat.sim.mujoco.iterations),
            "flat_line_search_iterations": int(flat.sim.mujoco.ls_iterations),
            "rough_solver_iterations": int(rough.sim.mujoco.iterations),
            "rough_line_search_iterations": int(rough.sim.mujoco.ls_iterations),
        },
        "action": {
            "dimension": 14,
            "scale": float(flat.actions["joint_pos"].scale),
            "offset": "default_joint_position",
            "configured_clip": flat.actions["joint_pos"].clip,
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
                "standing_fraction_initial": float(twist.rel_standing_envs),
                "forward_only_fraction": float(twist.rel_forward_envs),
                "turn_in_place_fraction": float(twist.rel_turn_in_place_envs),
                "turn_in_place_magnitude_fraction": [0.4, 1.0],
                "heading_fraction": float(twist.rel_heading_envs),
                "world_frame_fraction": float(twist.rel_world_envs),
                "initial_velocity_probability": float(twist.init_velocity_prob),
            },
            "head_pose": {
                "dimension": 4,
                "resampling_time_s": list(commands["head_pose"].resampling_time_range),
                "initial_ranges": jsonable(commands["head_pose"].ranges),
                "semantics": "delta_from_home_rad",
            },
            "body_pose": {
                "dimension": 6,
                "resampling_time_s": list(commands["body_pose"].resampling_time_range),
                "ranges": jsonable(commands["body_pose"].ranges),
                "semantics": "delta_from_nominal_xyz_m_rpy_rad",
            },
        },
        "actor_observation": {
            "terms": list(actor),
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
            "dimension": 76,
            "layout_sizes": {
                "base_lin_vel": 3,
                "base_ang_vel": 3,
                "projected_gravity": 3,
                "joint_pos": 14,
                "joint_vel": 14,
                "actions": 14,
                "command": 3,
                "foot_height": 2,
                "foot_air_time": 2,
                "foot_contact": 2,
                "foot_contact_forces": 6,
                "head_command": 4,
                "body_command": 6,
            },
        },
        "rewards": reward_params,
        "terminations": {
            name: {
                "function": term.func.__name__,
                "time_out": bool(term.time_out),
                "params": jsonable(term.params),
            }
            for name, term in flat.terminations.items()
        },
        "events": {
            name: {
                "function": term.func.__name__,
                "mode": term.mode,
                "interval_s": jsonable(term.interval_range_s),
            }
            for name, term in flat.events.items()
        },
        "domain_randomization": {
            "trunk_com": "randomize_com" in flat.events,
            "head_com": "randomize_head_com" in flat.events,
            "mass_inertia_scale": [
                math.exp(2.0 * flat.events["randomize_mass_inertia"].params["alpha_range"][0]),
                math.exp(2.0 * flat.events["randomize_mass_inertia"].params["alpha_range"][1]),
            ],
            "mass_inertia_operation": "pseudo_inertia_scales_mass_and_inertia",
            "joint_friction_scale": jsonable(
                flat.events["randomize_joint_friction"].params["scale_range"]
            ),
            "armature_scale": jsonable(flat.events["randomize_armature"].params["ranges"]),
            "foot_friction": jsonable(flat.events["foot_friction"].params["ranges"]),
            "velocity_push_interval_s": jsonable(flat.events["push_robot"].interval_range_s),
            "velocity_push_xy_m_s": jsonable(
                flat.events["push_robot"].params["velocity_range"]["x"]
            ),
            "encoder_bias_rad": jsonable(flat.events["encoder_bias"].params["bias_range"]),
            "imu_misalignment_max_deg": float(
                actor["base_ang_vel"].params["max_angle_deg"]
            ),
            "kp_enabled": False,
            "kd_enabled": False,
        },
        "curricula": {
            name: jsonable(term.params) for name, term in flat.curriculum.items()
        },
        "reset": {
            "base_pose_range": jsonable(flat.events["reset_base"].params["pose_range"]),
            "joint_position_offset_range_rad": [0.0, 0.0],
            "joint_velocity_range_rad_s": [0.0, 0.0],
        },
        "runner": {
            "num_steps_per_env": int(MicroduckRlCfg.num_steps_per_env),
            "actor_hidden_dims": list(MicroduckRlCfg.actor.hidden_dims),
            "actor_activation": MicroduckRlCfg.actor.activation,
            "actor_observation_normalization": bool(MicroduckRlCfg.actor.obs_normalization),
            "max_iterations": int(MicroduckRlCfg.max_iterations),
        },
        "rough_terrain": {
            "representation": "mjlab_box_and_heightfield_generators",
            "patch_size_m": list(rough.scene.terrain.terrain_generator.size),
            "source_declared_rows": 10,
            "source_declared_columns": 20,
            "effective_rows_after_task_registration": int(
                rough.scene.terrain.terrain_generator.num_rows
            ),
            "effective_columns_after_task_registration": int(
                rough.scene.terrain.terrain_generator.num_cols
            ),
            "effective_curriculum_after_task_registration": bool(
                rough.scene.terrain.terrain_generator.curriculum
            ),
            "effective_state_note": (
                "The package registers rough training then rough play configs with "
                "one shared terrain object; the play mutation is visible in the "
                "already-registered training config at this authority commit."
            ),
            "subterrain_proportions": {
                "flat": 0.25,
                "pyramid_stairs": 0.25,
                "random_grid": 0.30,
                "pyramid_slope": 0.20,
            },
            "stair_height_m": [0.0, 0.015],
            "grid_height_m": [0.0, 0.010],
            "slope": [0.03, 0.10],
            "foot_height_sensor": "two-ray ring radius 0.04 m per foot",
        },
    }
    return snapshot


def local_snapshot() -> dict[str, Any]:
    constants = load_source_module("walking_constants", ROOT / "microduck" / "constants.py")
    cfg = load_source_module("walking_cfg", ROOT / "microduck" / "velocity_cfg.py")
    return {
        "control": {
            "physics_dt_s": cfg.SIM_DT,
            "decimation": cfg.DECIMATION,
            "control_hz": round(1.0 / (cfg.SIM_DT * cfg.DECIMATION)),
            "episode_length_s": cfg.EPISODE_LENGTH_S,
            "flat_solver_iterations": 10,
            "flat_line_search_iterations": 20,
            "rough_solver_iterations": 30,
            "rough_line_search_iterations": 50,
        },
        "action": {
            "dimension": constants.NUM_ACTIONS,
            "joint_order": list(constants.JOINT_NAMES),
            "scale": cfg.ACTION_SCALE,
            "offset": "default_joint_position",
            "input_guard": [-100.0, 100.0],
            "filter": "none",
        },
        "commands": {
            "twist": {
                "dimension": 3,
                "resampling_time_s": list(cfg.TWIST_CMD_RESAMPLE_S),
                "ranges": {
                    "lin_vel_x_m_s": list(cfg.CMD_LIN_VEL_X),
                    "lin_vel_y_m_s": list(cfg.CMD_LIN_VEL_Y),
                    "ang_vel_z_rad_s": list(cfg.CMD_ANG_VEL_Z),
                },
                "standing_fraction_initial": cfg.STANDING_ENVS_STAGES[0][1],
                "forward_only_fraction": cfg.REL_FORWARD_ENVS,
                "turn_in_place_fraction": cfg.TURN_IN_PLACE_FRACTION,
                "turn_in_place_magnitude_fraction": [0.4, 1.0],
                "heading_fraction": 0.0,
                "world_frame_fraction": 0.0,
                "initial_velocity_probability": 0.0,
            },
            "head_pose": {
                "dimension": 4,
                "resampling_time_s": list(cfg.HEAD_POSE_CMD_RESAMPLE_S),
                "initial_ranges": jsonable(cfg.HEAD_POSE_RANGE_STAGES[0][1]),
                "semantics": "delta_from_home_rad",
            },
            "body_pose": {
                "dimension": 6,
                "resampling_time_s": list(cfg.BODY_POSE_CMD_RESAMPLE_S),
                "ranges": jsonable(cfg.BODY_POSE_RANGES),
                "semantics": "delta_from_nominal_xyz_m_rpy_rad",
            },
        },
        "actor_observation": {
            "dimension": constants.NUM_OBS,
            "layout": [{"name": name, "size": size} for name, size in constants.OBS_LAYOUT],
            "noise_half_ranges": dict(cfg.OBS_NOISE),
            "delay_control_steps": {
                name: list(values[:2]) for name, values in cfg.OBS_DELAY.items()
            },
            "delay_update_period": {
                name: values[2] for name, values in cfg.OBS_DELAY.items()
            },
            "encoder_bias_actor_only": cfg.ENABLE_ENCODER_BIAS,
            "imu_misalignment_max_deg": cfg.IMU_ORIENTATION_RANDOMIZATION_ANGLE,
        },
        "critic_observation": {
            "groups": ["policy", "privileged"],
            "dimension": 90,
            "privileged_dimension": 29,
            "privileged_layout_sizes": {
                "base_lin_vel": 3,
                "joint_pos_true": 14,
                "foot_contact": 2,
                "foot_air_time": 2,
                "foot_height": 2,
                "foot_contact_forces": 6,
            },
            "nonfinite_handling": "nan_to_num_entire_privileged_vector",
        },
        "rewards": {
            name: {"weight": weight} for name, weight in cfg.REWARD_WEIGHTS.items()
        },
        "reward_parameters": jsonable(cfg.REWARD_PARAMS),
        "curricula": {
            "action_rate_weight": jsonable(cfg.ACTION_RATE_WEIGHT_STAGES),
            "standing_envs": jsonable(cfg.STANDING_ENVS_STAGES),
            "head_pose_range": jsonable(cfg.HEAD_POSE_RANGE_STAGES),
            "body_pose_range": [[0, jsonable(cfg.BODY_POSE_RANGES)]],
            "com_range": jsonable(cfg.COM_RANGE_STAGES),
            "head_com_range": jsonable(cfg.HEAD_COM_RANGE_STAGES),
            "head_pose_bias_weight": jsonable(cfg.HEAD_POSE_BIAS_WEIGHT_STAGES),
        },
        "domain_randomization": {
            "trunk_com": cfg.ENABLE_COM_RANDOMIZATION,
            "head_com": cfg.ENABLE_HEAD_COM_RANDOMIZATION,
            "mass_inertia_scale": list(cfg.MASS_INERTIA_RANDOMIZATION_RANGE),
            "mass_inertia_operation": "mass_shift_only_no_inertia_scaling",
            "joint_friction_scale": list(cfg.JOINT_FRICTION_RANDOMIZATION_RANGE),
            "armature_scale": list(cfg.ARMATURE_RANDOMIZATION_RANGE),
            "foot_friction": list(cfg.FOOT_FRICTION_RANDOMIZATION_RANGE),
            "velocity_push_interval_s": list(cfg.VELOCITY_PUSH_INTERVAL_S),
            "velocity_push_xy_m_s": list(cfg.VELOCITY_PUSH_RANGE),
            "encoder_bias_rad": list(cfg.ENCODER_BIAS_RANGE),
            "imu_misalignment_max_deg": cfg.IMU_ORIENTATION_RANDOMIZATION_ANGLE,
            "kp_enabled": cfg.ENABLE_KP_RANDOMIZATION,
            "kd_enabled": cfg.ENABLE_KD_RANDOMIZATION,
        },
        "reset": {
            "base_pose_range": {
                "x": [-0.5, 0.5],
                "y": [-0.5, 0.5],
                "z": list(cfg.RESET_HEIGHT_RANGE),
                "yaw": [-math.pi, math.pi],
            },
            "joint_position_offset_range_rad": [0.0, 0.0],
            "joint_velocity_range_rad_s": [0.0, 0.0],
            "history": "actions, BAM delay, observation delays, contacts, air time, and bias EMA reset",
        },
        "termination": {
            "fell_over_tilt_deg": cfg.TERMINATION_TILT_DEG,
            "nan_state": True,
            "time_out_s": cfg.EPISODE_LENGTH_S,
            "rough_out_of_bounds": True,
        },
        "runner": jsonable(cfg.TRAIN_CFG),
        "rough_terrain": {
            "representation": "genesis_shared_heightfield",
            "rows": 10,
            "columns": 10,
            "patch_size_m": 3.0,
            "horizontal_scale_m": 0.05,
            "vertical_scale_m": 0.001,
            "subterrain_proportions": {
                "flat": 0.25,
                "pyramid_stairs": 0.25,
                "random_grid": 0.30,
                "pyramid_slope": 0.20,
            },
            "stair_height_m": [0.0, 0.015],
            "grid_height_m": [0.0, 0.010],
            "slope": [0.03, 0.10],
            "foot_height_sensor": "bilinear heightfield at foot site",
        },
    }


def materialize_official(repo: Path, commit: str, destination: Path) -> Path:
    archive = destination / "official.tar"
    subprocess.check_call(
        ["git", "archive", "--format=tar", "-o", os.fspath(archive), commit],
        cwd=repo,
    )
    with tarfile.open(archive) as stream:
        stream.extractall(destination, filter="data")
    return destination


def extract_official(
    repo: Path, commit: str, bam_repo: Path, official_python: Path
) -> tuple[dict[str, Any], dict[str, str]]:
    if not official_python.is_file():
        raise SystemExit(
            f"missing official runtime {official_python}; run scripts/setup_official_mjlab.sh"
        )
    resolved = command("git", "rev-parse", f"{commit}^{{commit}}", cwd=repo)
    if resolved != OFFICIAL_COMMIT:
        raise SystemExit(f"walking authority must be {OFFICIAL_COMMIT}, got {resolved}")
    bam_resolved = command("git", "rev-parse", "HEAD^{commit}", cwd=bam_repo)
    if bam_resolved != BAM_COMMIT:
        raise SystemExit(f"BAM authority must be {BAM_COMMIT}, got {bam_resolved}")
    if command("git", "status", "--porcelain", cwd=bam_repo):
        raise SystemExit("BAM authority checkout must be clean")

    tree = command("git", "show", "-s", "--format=%T", resolved, cwd=repo)
    commit_date = command("git", "show", "-s", "--format=%aI", resolved, cwd=repo)
    with tempfile.TemporaryDirectory(prefix="microduck-walking-authority-") as temp:
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
            raise SystemExit("official config extractor did not emit one snapshot")
        snapshot = json.loads(marked[0][len(EXTRACT_MARKER) :])
        source_digests = {
            file_name: sha256(official_root / file_name) for file_name in OFFICIAL_FILES
        }
    authority = {
        "commit": resolved,
        "tree": tree,
        "commit_date": commit_date,
        "source_digests": source_digests,
    }
    return snapshot, authority


def require_equal(label: str, official: Any, genesis: Any) -> None:
    if official != genesis:
        raise SystemExit(
            f"unclassified semantic mismatch for {label}:\n"
            f"official={official!r}\ngenesis={genesis!r}"
        )


def verify_shared_fields(official: dict[str, Any], genesis: dict[str, Any]) -> None:
    for name in ("physics_dt_s", "decimation", "control_hz", "episode_length_s"):
        require_equal(f"control.{name}", official["control"][name], genesis["control"][name])
    for name in ("dimension", "scale", "offset"):
        require_equal(f"action.{name}", official["action"][name], genesis["action"][name])
    require_equal("commands", official["commands"], genesis["commands"])
    official_actor_terms = [
        "base_ang_vel",
        "projected_gravity",
        "joint_pos",
        "joint_vel",
        "actions",
        "command",
        "head_command",
        "body_command",
    ]
    require_equal("actor_observation.terms", official["actor_observation"]["terms"], official_actor_terms)
    require_equal(
        "actor_observation.imu_misalignment",
        official["actor_observation"]["imu_misalignment_max_deg"],
        genesis["actor_observation"]["imu_misalignment_max_deg"],
    )
    require_equal(
        "actor_observation.encoder_bias",
        official["actor_observation"]["encoder_bias_actor_only"],
        genesis["actor_observation"]["encoder_bias_actor_only"],
    )
    expected_noise = {
        "base_ang_vel": [-0.03, 0.03],
        "projected_gravity": [-0.01, 0.01],
        "joint_pos": [-0.001, 0.001],
        "joint_vel": [-0.25, 0.25],
        "actions": None,
        "command": None,
        "head_command": None,
        "body_command": None,
    }
    require_equal("actor_observation.noise", official["actor_observation"]["noise"], expected_noise)
    for name, half_range in genesis["actor_observation"]["noise_half_ranges"].items():
        require_equal(f"actor_observation.noise.{name}", expected_noise[name], [-half_range, half_range])
    for name in ("base_ang_vel", "projected_gravity", "joint_vel"):
        require_equal(
            f"actor_observation.delay.{name}",
            official["actor_observation"]["delay_control_steps"][name],
            genesis["actor_observation"]["delay_control_steps"][name],
        )
        require_equal(
            f"actor_observation.delay_period.{name}",
            official["actor_observation"]["delay_update_period"][name],
            genesis["actor_observation"]["delay_update_period"][name],
        )
    official_weights = {name: term["weight"] for name, term in official["rewards"].items()}
    genesis_weights = {name: term["weight"] for name, term in genesis["rewards"].items()}
    require_equal("reward_weights", official_weights, genesis_weights)
    curriculum_fields = {
        "action_rate_weight": ("weight_stages", "weight"),
        "standing_envs": ("standing_stages", "rel_standing_envs"),
        "head_pose_range": ("range_stages", "ranges"),
        "body_pose_range": ("range_stages", "ranges"),
        "com_range": ("range_stages", "range"),
        "head_com_range": ("range_stages", "range"),
        "head_pose_bias_weight": ("weight_stages", "weight"),
    }
    for name, (list_key, value_key) in curriculum_fields.items():
        normalized = [
            [stage["step"], jsonable(stage[value_key])]
            for stage in official["curricula"][name][list_key]
        ]
        require_equal(f"curriculum.{name}", normalized, genesis["curricula"][name])
    for name in (
        "trunk_com",
        "head_com",
        "mass_inertia_scale",
        "joint_friction_scale",
        "armature_scale",
        "foot_friction",
        "velocity_push_interval_s",
        "velocity_push_xy_m_s",
        "encoder_bias_rad",
        "imu_misalignment_max_deg",
        "kp_enabled",
        "kd_enabled",
    ):
        require_equal(
            f"domain_randomization.{name}",
            official["domain_randomization"][name],
            genesis["domain_randomization"][name],
        )
    require_equal(
        "termination.fall_tilt_deg",
        math.degrees(official["terminations"]["fell_over"]["params"]["limit_angle"]),
        genesis["termination"]["fell_over_tilt_deg"],
    )
    require_equal(
        "reset.xyz",
        {key: official["reset"]["base_pose_range"][key] for key in ("x", "y", "z")},
        {key: genesis["reset"]["base_pose_range"][key] for key in ("x", "y", "z")},
    )
    require_equal(
        "reset.joints",
        {
            "position": official["reset"]["joint_position_offset_range_rad"],
            "velocity": official["reset"]["joint_velocity_range_rad_s"],
        },
        {
            "position": genesis["reset"]["joint_position_offset_range_rad"],
            "velocity": genesis["reset"]["joint_velocity_range_rad_s"],
        },
    )


def semantic_inventory() -> list[dict[str, str]]:
    rows = [
        ("control.physics_timing", "exact", "5 ms physics, decimation 4, 50 Hz control"),
        ("action.dimension_order", "exact", "14 joints bound by action-v1"),
        ("action.delta_scale_filter", "exact", "unfiltered delta from HOME, scale 1"),
        ("action.input_guard", "versioned-divergence", "Genesis clips policy input to +/-100; official config has no clip"),
        ("actuator.bam_delay", "exact", "3-6 physics steps, reset per episode"),
        ("observation.actor_layout", "exact", "61D ordered actor interface"),
        ("observation.actor_noise", "exact", "same uniform training noise ranges"),
        ("observation.actor_delay", "equivalent", "same lag ranges/update periods; RNG streams differ"),
        ("observation.encoder_bias", "equivalent", "actor-only startup bias in the same range"),
        ("observation.imu_misalignment", "equivalent", "actor-only random-axis rotation up to 6 degrees"),
        ("observation.critic", "versioned-divergence", "official critic is 76D; Genesis critic is policy 61D plus privileged 29D"),
        ("commands.ranges_resampling", "exact", "same twist/head/body distributions and intervals"),
        ("commands.population_buckets", "equivalent", "same standing/forward/turn fractions; draw order is backend-specific"),
        ("reset.base_and_joints", "versioned-divergence", "same x/y/z and HOME/zero-velocity joint reset; official yaw is +/-3.14 while Genesis uses +/-pi"),
        ("reset.internal_history", "equivalent", "both clear action, actuator-delay, and relevant observation histories"),
        ("termination.fall_timeout_nan", "equivalent", "same 70-degree/20-second intent with backend-native NaN detection"),
        ("termination.rough_bounds", "versioned-divergence", "backend-native terrain-bound calculations are not trajectory-identical"),
        ("training.reward_terms", "equivalent", "same names and weights; sensor realization differences remain below"),
        ("training.curricula", "equivalent", "same declared global-step stages; manager lifecycle differs"),
        ("training.domain_randomization", "equivalent", "same declared ranges except the separately classified mass-inertia operation; backend RNG streams are not shared"),
        ("training.mass_inertia_randomization", "versioned-divergence", "official pseudo-inertia scales trunk mass and inertia together; Genesis currently applies only a trunk mass shift"),
        ("terrain.rough_realization", "versioned-divergence", "official effective registered terrain is 5x5 with curriculum disabled after a shared play-config mutation; Genesis is a 10x10 curriculum heightfield"),
        ("sensing.foot_height", "versioned-divergence", "mjlab two-ray ring versus Genesis bilinear height at the foot site"),
        ("sensing.contact", "versioned-divergence", "mjlab geom sensors versus Genesis link-net-force thresholding"),
        ("physics.contact_solver", "backend-specific-unavailable", "solver and collision realizations cannot be made byte-identical"),
        ("execution.random_stream", "backend-specific-unavailable", "framework RNG algorithms and draw ordering differ"),
        ("execution.step_lifecycle", "versioned-divergence", "manager and hand-written event/reward/reset ordering are not claimed identical"),
        ("acceptance.policy_loop", "exact", "frozen evaluator uses interface locks, fixed starts, and no assistance"),
    ]
    return [
        {"field": field, "classification": classification, "disposition": disposition}
        for field, classification, disposition in rows
    ]


def acceptance_contract() -> dict[str, Any]:
    command_grid = [
        ("stop", 0.0, 0.0, 0.0),
        ("forward_slow", 0.2, 0.0, 0.0),
        ("forward_max", 0.4, 0.0, 0.0),
        ("backward_slow", -0.2, 0.0, 0.0),
        ("backward_max", -0.4, 0.0, 0.0),
        ("left_max", 0.0, 0.3, 0.0),
        ("right_max", 0.0, -0.3, 0.0),
        ("turn_left_slow", 0.0, 0.0, 0.5),
        ("turn_left_max", 0.0, 0.0, 1.0),
        ("turn_right_slow", 0.0, 0.0, -0.5),
        ("turn_right_max", 0.0, 0.0, -1.0),
        ("forward_left", 0.3, 0.0, 0.5),
        ("forward_right", 0.3, 0.0, -0.5),
        ("backward_left", -0.3, 0.0, 0.5),
        ("backward_right", -0.3, 0.0, -0.5),
    ]
    commands = [
        {"id": name, "twist": [vx, vy, wz], "head_pose": [0.0] * 4, "body_pose": [0.0] * 6}
        for name, vx, vy, wz in command_grid
    ]
    for name, joint_index, target in (
        ("neck_up", 0, 0.5),
        ("neck_down", 0, -0.5),
        ("head_pitch_up", 1, 0.5),
        ("head_pitch_down", 1, -0.5),
        ("head_yaw_left", 2, 0.7),
        ("head_yaw_right", 2, -0.7),
        ("head_roll_left", 3, 0.15),
        ("head_roll_right", 3, -0.15),
    ):
        head_pose = [0.0] * 4
        head_pose[joint_index] = target
        commands.append(
            {
                "id": name,
                "twist": [0.2, 0.0, 0.0],
                "head_pose": head_pose,
                "body_pose": [0.0] * 6,
            }
        )
    return {
        "suite_id": "microduck.walking-acceptance.v1",
        "status": "preregistered_not_executed",
        "candidate_outcomes_inspected": False,
        "seeds": [31001, 31002, 31003, 31004, 31005],
        "seed_handling": {
            "stream": "sha256-counter-v1",
            "cell_key": "suite_id + command_id + start_population_id + decimal_seed",
            "uniform_mapping": "successive 53-bit unsigned words divided by 2^53",
            "state_sharing_between_cells": False,
            "realized_initial_state_must_be_recorded": True,
        },
        "episode_duration_s": 10.0,
        "metric_warmup_s": 1.0,
        "commands": commands,
        "start_populations": [
            {
                "id": "nominal_home",
                "root_xyz_m": [0.0, 0.0, 0.125],
                "root_rpy_deg": [0.0, 0.0, 0.0],
                "joint_position": "HOME",
                "root_and_joint_velocity": "zero",
            },
            {
                "id": "seeded_upright_perturbation",
                "root_xyz_m": {"x": [-0.02, 0.02], "y": [-0.02, 0.02], "z": [0.12, 0.13]},
                "root_roll_pitch_deg": [-5.0, 5.0],
                "root_yaw_rad": [-math.pi, math.pi],
                "joint_offset_rad": [-0.02, 0.02],
                "root_planar_velocity_m_s": [-0.05, 0.05],
                "joint_velocity_rad_s": [-0.05, 0.05],
            },
        ],
        "assistance": {
            "external_pushes": False,
            "command_resampling": False,
            "curriculum": False,
            "domain_randomization": False,
            "observation_noise": False,
            "random_actuator_or_sensor_delay": False,
            "state_or_action_correction": False,
            "early_termination_suppression": False,
        },
        "metrics": {
            "survival": {
                "nominal_fraction_min": 0.98,
                "perturbed_fraction_min": 0.90,
                "fall_rate_max": 0.05,
            },
            "tracking_after_warmup": {
                "linear_velocity_rmse_m_s_mean_max": 0.12,
                "linear_velocity_error_m_s_p95_max": 0.25,
                "yaw_rate_rmse_rad_s_mean_max": 0.25,
                "yaw_rate_error_rad_s_p95_max": 0.50,
                "head_pose_error_rad_mean_max": 0.15,
                "head_pose_error_rad_p95_max": 0.30,
            },
            "stop": {
                "planar_displacement_m_p95_max": 0.15,
                "absolute_yaw_change_rad_p95_max": 0.35,
            },
            "foot_slip": {
                "stance_speed_m_s_p95_max": 0.08,
                "stance_speed_m_s_max": 0.20,
            },
            "orientation": {
                "absolute_roll_pitch_deg_p95_max": 15.0,
                "absolute_roll_pitch_deg_max": 45.0,
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
                "deadline_measurement": (
                    "monotonic wall time around single-thread ONNX Runtime CPU "
                    "inference; exclude 10 untimed warmup calls and bind the host "
                    "profile in environment-lock.json"
                ),
            },
        },
        "aggregation": {
            "required_episode_count": len(commands) * 5 * 2,
            "all_command_start_seed_cells_required": True,
            "classification": "pass only when every coverage/integrity requirement and every metric threshold passes",
            "ppo_return_is_success_metric": False,
        },
    }


def build_contract(
    official: dict[str, Any], authority: dict[str, Any], genesis: dict[str, Any]
) -> dict[str, Any]:
    verify_shared_fields(official, genesis)
    bindings = {
        file_name: sha256(ROOT / file_name) for file_name in LOCAL_FILES
    }
    referenced = [
        "microduck_contract/tasks/walking-v1.schema.json",
        "microduck_contract/interface/observation-v1.json",
        "microduck_contract/interface/action-v1.json",
        "microduck_contract/interface/control-v1.json",
        "microduck_contract/actuator/bam-m6-xl330-v1.lock.json",
        "microduck_contract/model/microduck-walk-v1.lock.json",
        "microduck_contract/model/reconciliation-v1.lock.json",
    ]
    shared_action = {
        key: genesis["action"][key]
        for key in ("dimension", "joint_order", "scale", "offset", "filter")
    }
    shared_control = {
        key: genesis["control"][key]
        for key in ("physics_dt_s", "decimation", "control_hz", "episode_length_s")
    }
    return {
        "$schema": "walking-v1.schema.json",
        "schema_version": "microduck.walking-task/v1",
        "task_id": "microduck.walking.v1",
        "authority": {
            "official_microduck": authority,
            "bam_commit": BAM_COMMIT,
            "local_source_digests": bindings,
            "referenced_contracts": {
                file_name: sha256(ROOT / file_name) for file_name in referenced
            },
        },
        "claim": {
            "state": "declared_semantics_with_versioned_divergences",
            "actor_interface": "exact",
            "training_trajectory_equivalence": False,
            "policy_success": "not_evaluated",
            "physical_authority": False,
        },
        "shared_deployed_contract": {
            "control": shared_control,
            "action": shared_action,
            "actor_observation": genesis["actor_observation"],
            "commands": genesis["commands"],
            "actuator_delay_physics_steps": [3, 6],
            "default_joint_position_rad": load_source_module(
                "walking_contract_constants", ROOT / "microduck" / "constants.py"
            ).DEFAULT_JOINT_POS,
        },
        "training_only": {
            "official_mjlab": official,
            "genesis": genesis,
            "reward_is_success_definition": False,
        },
        "semantic_inventory": semantic_inventory(),
        "acceptance": acceptance_contract(),
        "evidence_boundary": (
            "This file freezes declarations and a future zero-assistance acceptance "
            "battery. It does not report a policy result, held-out success, transfer, "
            "or physical authority."
        ),
    }


def validate_contract(value: dict[str, Any], verify_local: bool = True) -> None:
    if value.get("schema_version") != "microduck.walking-task/v1":
        raise AssertionError("unexpected walking schema")
    if value.get("task_id") != "microduck.walking.v1":
        raise AssertionError("unexpected walking task id")
    rows = value.get("semantic_inventory", [])
    fields = [row.get("field") for row in rows]
    if len(fields) != len(set(fields)) or not fields:
        raise AssertionError("semantic inventory fields must be unique and nonempty")
    allowed = {"exact", "equivalent", "versioned-divergence", "backend-specific-unavailable"}
    for row in rows:
        if row.get("classification") not in allowed or not row.get("disposition"):
            raise AssertionError(f"unclassified semantic field: {row}")
    acceptance = value["acceptance"]
    if acceptance["status"] != "preregistered_not_executed":
        raise AssertionError("walking acceptance must remain unexecuted in this slice")
    if acceptance["candidate_outcomes_inspected"]:
        raise AssertionError("candidate outcomes cannot inform the frozen thresholds")
    if any(acceptance["assistance"].values()):
        raise AssertionError("walking acceptance assistance must be fully disabled")
    expected = len(acceptance["commands"]) * len(acceptance["seeds"]) * len(
        acceptance["start_populations"]
    )
    if acceptance["aggregation"]["required_episode_count"] != expected:
        raise AssertionError("acceptance coverage count is stale")
    if verify_local:
        for file_name, digest in value["authority"]["local_source_digests"].items():
            if sha256(ROOT / file_name) != digest:
                raise AssertionError(f"walking local source drift: {file_name}")
        for file_name, digest in value["authority"]["referenced_contracts"].items():
            if sha256(ROOT / file_name) != digest:
                raise AssertionError(f"walking referenced contract drift: {file_name}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--official-repo", type=Path)
    parser.add_argument("--official-commit", default=OFFICIAL_COMMIT)
    parser.add_argument("--bam-repo", type=Path)
    parser.add_argument(
        "--official-python",
        type=Path,
        default=ROOT / "validation" / "official-mjlab" / ".venv" / "bin" / "python",
    )
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
        args.official_repo.resolve(),
        args.official_commit,
        args.bam_repo.resolve(),
        args.official_python.absolute(),
    )
    value = build_contract(official, authority, local_snapshot())
    validate_contract(value)
    expected = json_bytes(value)
    if args.check:
        actual = args.output.read_bytes() if args.output.exists() else b""
        if actual != expected:
            print(f"Walking semantics are stale: {args.output}")
            return 1
        print("Walking semantics verified against pinned authorities.")
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(expected)
    print(f"Walking semantics written: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
