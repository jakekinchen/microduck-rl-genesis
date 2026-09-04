"""Deterministic, reward-independent MuJoCo/ONNX/BAM evaluator core.

This module provides infrastructure only. It intentionally does not implement
the walking or backflip success classifiers and never promotes task success.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import mujoco
import numpy as np
import onnxruntime as ort

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = Path(__file__).with_name("config-v1.json")
BAM_COMMIT = "62bd8ce12154340be97e06f7f41a0ca8f116d967"


class EvaluationError(RuntimeError):
    """Fail-closed evaluator input or runtime error."""


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def stable_json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def sha256_counter_uniform(cell_key: str, count: int) -> np.ndarray:
    """Return deterministic [0, 1) values using independent SHA-256 counters."""
    values = []
    key = cell_key.encode()
    for counter in range(count):
        digest = hashlib.sha256(key + b"\0" + counter.to_bytes(8, "big")).digest()
        word53 = int.from_bytes(digest[:8], "big") >> 11
        values.append(word53 / float(1 << 53))
    return np.asarray(values, dtype=np.float64)


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()


def projected_gravity(quaternion_wxyz: np.ndarray) -> np.ndarray:
    """Rotate world gravity direction into the quaternion's local frame."""
    w, x, y, z = quaternion_wxyz
    rotation = np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ])
    return rotation.T @ np.array([0.0, 0.0, -1.0])


class OnnxPolicy:
    def __init__(self, path: Path, config: dict[str, Any]):
        if not path.is_file():
            raise EvaluationError(f"missing ONNX policy: {path}")
        options = ort.SessionOptions()
        options.intra_op_num_threads = int(config["intra_op_threads"])
        options.inter_op_num_threads = int(config["inter_op_threads"])
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        self.session = ort.InferenceSession(
            os.fspath(path), sess_options=options, providers=[config["provider"]]
        )
        if self.session.get_providers() != ["CPUExecutionProvider"]:
            raise EvaluationError(f"non-CPU ONNX provider: {self.session.get_providers()}")
        inputs = self.session.get_inputs()
        outputs = self.session.get_outputs()
        if len(inputs) != 1 or len(outputs) != 1:
            raise EvaluationError("policy must have exactly one input and one output")
        expected_input = list(config["input_shape"])
        expected_output = list(config["output_shape"])
        if inputs[0].shape != expected_input or inputs[0].type != "tensor(float)":
            raise EvaluationError(f"invalid ONNX input contract: {inputs[0].shape} {inputs[0].type}")
        if outputs[0].shape != expected_output or outputs[0].type != "tensor(float)":
            raise EvaluationError(f"invalid ONNX output contract: {outputs[0].shape} {outputs[0].type}")
        self.input_name = inputs[0].name
        self.output_name = outputs[0].name
        self.path = path
        zeros = np.zeros(expected_input, dtype=np.float32)
        for _ in range(int(config["warmup_calls"])):
            self.infer(zeros)

    def infer(self, observation: np.ndarray) -> tuple[np.ndarray, float]:
        if observation.shape != (1, 61) or observation.dtype != np.float32:
            raise EvaluationError(f"invalid observation: {observation.shape} {observation.dtype}")
        started = time.monotonic_ns()
        action = self.session.run([self.output_name], {self.input_name: observation})[0]
        elapsed_ms = (time.monotonic_ns() - started) / 1_000_000.0
        action = np.asarray(action, dtype=np.float32)
        if action.shape != (1, 14) or not np.isfinite(action).all():
            raise EvaluationError("policy returned an invalid action")
        return action, elapsed_ms


class EvaluatorCore:
    def __init__(
        self,
        policy_path: Path,
        bam_repo: Path,
        task_id: str,
        proof_class: str = "infrastructure_only",
    ):
        self.config = json.loads(CONFIG_PATH.read_text())
        self._validate_static_config()
        if task_id not in self.config["tasks"]:
            raise EvaluationError(f"unsupported task: {task_id}")
        self.task_id = task_id
        if proof_class not in {"infrastructure_only", "first_party_development"}:
            raise EvaluationError(f"unsupported proof class: {proof_class}")
        self.proof_class = proof_class
        self.task_cfg = self.config["tasks"][task_id]
        self.task_path = ROOT / self.task_cfg["task_contract"]
        self.model_lock_path = ROOT / self.task_cfg["model_lock"]
        self.scene_path = ROOT / self.task_cfg["scene"]
        self._validate_authorities(bam_repo)
        self.policy = OnnxPolicy(policy_path, self.config["inference"])
        self.policy_path = policy_path
        self.model = mujoco.MjModel.from_xml_path(os.fspath(self.scene_path))
        self.data = mujoco.MjData(self.model)
        self._validate_model()
        self._configure_torque_actuators()
        self.controller = self._build_bam_controller(bam_repo)

    def _validate_static_config(self) -> None:
        physics = self.config["physics"]
        if physics != {
            "engine": "official-mujoco-c-via-python-bindings",
            "timestep_s": 0.005,
            "control_decimation": 4,
            "control_hz": 50,
            "action_filter": "none",
        }:
            raise EvaluationError("evaluator physics/control configuration drift")
        if self.config["proof_class"] != "infrastructure_only":
            raise EvaluationError("core smoke may only use infrastructure proof class")

    def _validate_authorities(self, bam_repo: Path) -> None:
        if not bam_repo.is_dir():
            raise EvaluationError(f"missing BAM checkout: {bam_repo}")
        if git(bam_repo, "rev-parse", "HEAD^{commit}") != BAM_COMMIT:
            raise EvaluationError("BAM checkout is not at the pinned commit")
        if git(bam_repo, "status", "--porcelain"):
            raise EvaluationError("BAM checkout must be clean")
        task = json.loads(self.task_path.read_text())
        if task["task_id"] != self.task_id:
            raise EvaluationError("task contract id mismatch")
        if task["claim"]["policy_success"] != "not_evaluated":
            raise EvaluationError("evaluator input task unexpectedly claims success")
        model_lock = json.loads(self.model_lock_path.read_text())
        root_model = ROOT / model_lock["root_model"]
        if sha256(root_model) != model_lock["root_sha256"]:
            raise EvaluationError("model root digest mismatch")
        scene_relative = self.scene_path.relative_to(ROOT).as_posix()
        if sha256(self.scene_path) != model_lock["files"].get(scene_relative):
            raise EvaluationError("model scene digest mismatch")
        for referenced_path, digest in task["authority"]["referenced_contracts"].items():
            if sha256(ROOT / referenced_path) != digest:
                raise EvaluationError(f"task referenced-contract drift: {referenced_path}")
        self.task_digest = sha256(self.task_path)
        self.model_lock_digest = sha256(self.model_lock_path)
        self.model_root_digest = sha256(root_model)
        self.scene_digest = sha256(self.scene_path)
        self.bam_lock_path = ROOT / "microduck_contract/actuator/bam-m6-xl330-v1.lock.json"
        bam_lock = json.loads(self.bam_lock_path.read_text())
        if bam_lock["golden_vectors"]["authority_commit"] != BAM_COMMIT:
            raise EvaluationError("BAM lock authority drift")
        if sha256(ROOT / bam_lock["parameter_file"]) != bam_lock["parameter_sha256"]:
            raise EvaluationError("BAM parameter digest mismatch")
        self.bam_lock_digest = sha256(self.bam_lock_path)
        self.obs_path = ROOT / "microduck_contract/interface/observation-v1.json"
        self.action_path = ROOT / "microduck_contract/interface/action-v1.json"
        self.control_path = ROOT / "microduck_contract/interface/control-v1.json"
        self.observation = json.loads(self.obs_path.read_text())
        self.action = json.loads(self.action_path.read_text())
        self.control = json.loads(self.control_path.read_text())
        if self.observation["shape"] != [1, 61] or self.action["shape"] != [1, 14]:
            raise EvaluationError("interface shape drift")
        if self.control["control_hz"] != 50 or self.control["action_filter"] != "none":
            raise EvaluationError("control contract drift")
        self.home = np.asarray(self.observation["home_joint_position_rad"], dtype=np.float64)
        self.joint_names = list(self.action["joint_order"])
        if self.joint_names != self.observation["joint_order"]:
            raise EvaluationError("observation/action joint order mismatch")

    def _validate_model(self) -> None:
        self.model.opt.timestep = 0.005
        names = [self.model.actuator(index).name for index in range(self.model.nu)]
        if names != self.joint_names:
            raise EvaluationError(f"actuator order mismatch: {names}")
        self.joint_ids = np.asarray([self.model.joint(name).id for name in self.joint_names])
        self.qpos_indices = self.model.jnt_qposadr[self.joint_ids]
        self.dof_indices = self.model.jnt_dofadr[self.joint_ids]

    def _configure_torque_actuators(self) -> None:
        for name in self.joint_names:
            actuator = self.model.actuator(name)
            self.model.actuator_gaintype[actuator.id] = mujoco.mjtGain.mjGAIN_FIXED
            self.model.actuator_biastype[actuator.id] = mujoco.mjtBias.mjBIAS_NONE
            self.model.actuator_gainprm[actuator.id, :] = 0.0
            self.model.actuator_gainprm[actuator.id, 0] = 1.0
            self.model.actuator_biasprm[actuator.id, :] = 0.0
            self.model.actuator_forcerange[actuator.id] = [-10.0, 10.0]

    def _build_bam_controller(self, bam_repo: Path):
        sys.path.insert(0, os.fspath(bam_repo))
        from bam.model import load_model  # type: ignore
        from bam.mujoco import MujocoController  # type: ignore

        bam_lock = json.loads(self.bam_lock_path.read_text())
        bam_model = load_model(os.fspath(ROOT / bam_lock["parameter_file"]))
        bam_model.actuator.kp = float(bam_lock["firmware_kp"])
        bam_model.actuator.vin = float(self.config["actuator"]["supply_voltage_v"])
        return MujocoController(
            bam_model,
            self.joint_names,
            self.model,
            self.data,
            vin_drop_gain=float(self.config["actuator"]["voltage_drop_resistance_ohm"]),
            vin_min=float(bam_lock["supply_voltage_floor_v"]),
        )

    def reset(self, root_xyz: list[float], root_quaternion_wxyz: list[float]) -> None:
        mujoco.mj_resetData(self.model, self.data)
        self.data.qpos[0:3] = root_xyz
        self.data.qpos[3:7] = root_quaternion_wxyz
        self.data.qpos[self.qpos_indices] = self.home
        self.data.qvel[:] = 0.0
        mujoco.mj_forward(self.model, self.data)
        self.controller.last_ts = self.data.time
        self.controller.reset(self.data.qpos)
        for index, name in enumerate(self.joint_names):
            self.controller.set_q_target(name, self.home[index])

    def observation_vector(
        self,
        last_action: np.ndarray,
        twist: np.ndarray,
        head: np.ndarray,
        body: np.ndarray,
    ) -> np.ndarray:
        angular_velocity = self.data.sensor("imu_ang_vel").data.copy()
        quaternion = self.data.sensor("orientation").data.copy()
        parts = [
            angular_velocity,
            projected_gravity(quaternion),
            self.data.qpos[self.qpos_indices] - self.home,
            self.data.qvel[self.dof_indices],
            last_action,
            twist,
            head,
            body,
        ]
        observation = np.concatenate(parts).astype(np.float32).reshape(1, 61)
        if not np.isfinite(observation).all():
            raise EvaluationError("non-finite observation")
        return observation

    def run_case(
        self, case: dict[str, Any], capture_frames: bool = False
    ) -> tuple[dict[str, Any], list[dict[str, Any]], list[np.ndarray]]:
        if case["task_id"] != self.task_id:
            raise EvaluationError("case task mismatch")
        if self.proof_class == "first_party_development" and "synthetic_inference_latency_ms" in case:
            raise EvaluationError("first-party learned-policy reports require measured inference latency")
        self.reset(case["root_xyz_m"], case["root_quaternion_wxyz"])
        initial_offset = np.asarray(
            case.get("initial_joint_offset_rad", [0.0] * 14), dtype=np.float64
        )
        if initial_offset.shape != (14,) or not np.isfinite(initial_offset).all():
            raise EvaluationError("invalid initial joint offset")
        self.data.qpos[self.qpos_indices] += initial_offset
        friction_scale = float(case.get("geom_friction_scale", 1.0))
        if not np.isfinite(friction_scale) or friction_scale <= 0.0:
            raise EvaluationError("invalid geometry friction scale")
        self.model.geom_friction[:] *= friction_scale
        mujoco.mj_forward(self.model, self.data)
        last_action = np.zeros(14, dtype=np.float32)
        twist = np.asarray(case.get("twist_command", [0.0, 0.0, 0.0]), dtype=np.float32)
        head = np.asarray(case["head_command"], dtype=np.float32)
        body = np.asarray(case["body_command"], dtype=np.float32)
        schedule = sorted(case.get("twist_schedule", []), key=lambda row: row["control_step"])
        decimation = int(self.config["physics"]["control_decimation"])
        deadline_ms = float(self.config["inference"]["deadline_ms"])
        deadline_misses = 0
        synthetic_latency_ms = case.get("synthetic_inference_latency_ms")
        if synthetic_latency_ms is not None:
            synthetic_latency_ms = float(synthetic_latency_ms)
            if not np.isfinite(synthetic_latency_ms) or synthetic_latency_ms < 0.0:
                raise EvaluationError("invalid synthetic inference latency")
        policy_calls = 0
        measured_latencies_ms: list[float] = []
        records = []
        rows: list[dict[str, Any]] = []
        frames: list[np.ndarray] = []
        renderer = None
        camera = None
        if capture_frames:
            renderer = mujoco.Renderer(self.model, height=240, width=320)
            camera = mujoco.MjvCamera()
            camera.type = mujoco.mjtCamera.mjCAMERA_FREE
            camera.lookat[:] = [0.0, 0.0, 0.12]
            camera.distance = 0.65
            camera.azimuth = 145.0
            camera.elevation = -18.0
        target = self.home.copy()
        force_steps = 0
        terminated_step: int | None = None
        min_joint_margin_rad = float("inf")
        joint_ranges = self.model.jnt_range[self.joint_ids]
        try:
            for step in range(int(case["physics_steps"])):
                if step % decimation == 0:
                    for stage in schedule:
                        if int(stage["control_step"]) <= policy_calls:
                            twist = np.asarray(stage["value"], dtype=np.float32)
                    observation = self.observation_vector(last_action, twist, head, body)
                    if case.get("inject_nonfinite_at_control_step") == policy_calls:
                        observation[0, 0] = np.nan
                    if not np.isfinite(observation).all():
                        raise EvaluationError("non-finite observation")
                    action, latency_ms = self.policy.infer(observation)
                    measured_latencies_ms.append(latency_ms)
                    if synthetic_latency_ms is not None:
                        latency_ms = synthetic_latency_ms
                    deadline_misses += int(latency_ms > deadline_ms)
                    policy_calls += 1
                    last_action = action[0].copy()
                    target = self.home + last_action.astype(np.float64)
                    for index, name in enumerate(self.joint_names):
                        self.controller.set_q_target(name, float(target[index]))
                self.data.xfrc_applied[:] = 0.0
                for force in case.get("external_force_schedule", []):
                    if int(force["start_physics_step"]) <= step < int(force["end_physics_step"]):
                        body_id = self.model.body(force["body"]).id
                        self.data.xfrc_applied[body_id] = np.asarray(
                            force["wrench_force_torque"], dtype=np.float64
                        )
                        force_steps += 1
                self.controller.update()
                mujoco.mj_step(self.model, self.data)
                state = np.concatenate([
                    np.asarray([self.data.time], dtype=np.float64),
                    self.data.qpos[:7].copy(),
                    self.data.qpos[self.qpos_indices].copy(),
                    self.data.qvel[self.dof_indices].copy(),
                    self.data.ctrl.copy(),
                    last_action.astype(np.float64),
                ])
                if not np.isfinite(state).all():
                    raise EvaluationError(f"non-finite state at physics step {step}")
                joint_position = self.data.qpos[self.qpos_indices]
                margins = np.minimum(
                    joint_position - joint_ranges[:, 0],
                    joint_ranges[:, 1] - joint_position,
                )
                min_joint_margin_rad = min(min_joint_margin_rad, float(np.min(margins)))
                records.append(state)
                rows.append({
                    "case_id": case["case_id"],
                    "physics_step": step + 1,
                    "control_step": (step // decimation) + 1,
                    "time_s": float(self.data.time),
                    "root_position_m": self.data.qpos[:3].astype(float).tolist(),
                    "root_quaternion_wxyz": self.data.qpos[3:7].astype(float).tolist(),
                    "joint_position_rad": self.data.qpos[self.qpos_indices].astype(float).tolist(),
                    "joint_velocity_rad_s": self.data.qvel[self.dof_indices].astype(float).tolist(),
                    "action_rad": last_action.astype(float).tolist(),
                    "target_position_rad": target.astype(float).tolist(),
                    "actuator_torque_nm": self.data.ctrl.astype(float).tolist(),
                    "twist_command": twist.astype(float).tolist(),
                    "finite": True,
                })
                if renderer is not None and (step + 1) % decimation == 0:
                    renderer.update_scene(self.data, camera=camera)
                    frames.append(renderer.render().copy())
                threshold = case.get("terminate_root_z_below_m")
                if threshold is not None and float(self.data.qpos[2]) < float(threshold):
                    terminated_step = step + 1
                    break
        finally:
            if renderer is not None:
                renderer.close()
        trajectory = np.asarray(records, dtype="<f8")
        trajectory_digest = "sha256:" + hashlib.sha256(trajectory.tobytes(order="C")).hexdigest()
        case_key = f"{case['case_id']}\0{case['seed']}".encode()
        prefix = "development" if self.proof_class == "first_party_development" else "infrastructure"
        classification = f"{prefix}_completed"
        if self.proof_class == "infrastructure_only":
            classification = "infrastructure_pass"
        joint_margin_threshold = case.get("joint_margin_min_rad")
        if terminated_step is not None:
            classification = f"{prefix}_terminated"
        elif joint_margin_threshold is not None and min_joint_margin_rad < float(joint_margin_threshold):
            classification = f"{prefix}_joint_margin_violation"
        elif deadline_misses:
            classification = f"{prefix}_deadline_miss"
        report = {
            "schema_version": "microduck.evaluator-report/v1",
            "evaluator_id": self.config["evaluator_id"],
            "proof_class": self.proof_class,
            "classification": classification,
            "task_success": "not_evaluated",
            "held_out": False,
            "case": {
                "id": case["case_id"],
                "seed": case["seed"],
                "seed_material_sha256": "sha256:" + hashlib.sha256(case_key).hexdigest(),
                "seed_stream": "sha256-counter-v1",
            },
            "policy": {"sha256": sha256(self.policy_path), "execution_provider": "CPUExecutionProvider"},
            "authorities": {
                "evaluator_config_sha256": sha256(CONFIG_PATH),
                "evaluator_core_sha256": sha256(Path(__file__)),
                "task_contract_sha256": self.task_digest,
                "model_lock_sha256": self.model_lock_digest,
                "model_root_sha256": self.model_root_digest,
                "model_scene_sha256": self.scene_digest,
                "bam_lock_sha256": self.bam_lock_digest,
                "bam_commit": BAM_COMMIT,
                "observation_contract_sha256": sha256(self.obs_path),
                "action_contract_sha256": sha256(self.action_path),
                "control_contract_sha256": sha256(self.control_path),
            },
            "loop": {
                "physics_dt_s": 0.005,
                "control_decimation": decimation,
                "control_hz": 50,
                "action_filter": "none",
                "physics_steps": len(records),
                "policy_calls": policy_calls,
                "bam_updates": len(records),
            },
            "integrity": {
                "finite": True,
                "inference_deadline_ms": deadline_ms,
                "deadline_miss_count": deadline_misses,
                "trajectory_sha256": trajectory_digest,
            },
            "runtime": {
                "mujoco": mujoco.__version__,
                "onnxruntime": ort.__version__,
                "numpy": importlib.metadata.version("numpy"),
            },
            "evidence_boundary": (
                "First-party learned-policy execution on visible development cases only; "
                "not gait success, held-out acceptance, transfer, or physical authority."
                if self.proof_class == "first_party_development"
                else "Synthetic zero-policy plumbing proof only; no walking/backflip success, held-out result, transfer, or physical authority."
            ),
        }
        if self.proof_class == "first_party_development":
            latency = np.asarray(measured_latencies_ms, dtype=np.float64)
            report["integrity"]["deadline_latency_source"] = "measured_wall_clock"
            report["integrity"]["measured_inference_latency_ms"] = {
                "count": int(latency.size),
                "minimum": float(latency.min()),
                "maximum": float(latency.max()),
                "mean": float(latency.mean()),
                "p50": float(np.percentile(latency, 50)),
                "p95": float(np.percentile(latency, 95)),
            }
        if synthetic_latency_ms is not None:
            report["integrity"]["deadline_latency_source"] = "synthetic_case_fixture"
        if any(
            key in case
            for key in (
                "initial_joint_offset_rad",
                "geom_friction_scale",
                "external_force_schedule",
                "joint_margin_min_rad",
                "terminate_root_z_below_m",
            )
        ):
            report["case_metrics"] = {
                "geom_friction_scale": friction_scale,
                "external_force_physics_steps": force_steps,
                "minimum_joint_margin_rad": min_joint_margin_rad,
                "terminated": terminated_step is not None,
                "termination_physics_step": terminated_step,
            }
        if terminated_step is not None:
            report["loop"]["requested_physics_steps"] = int(case["physics_steps"])
        return report, rows, frames

    def run_synthetic_smoke(self) -> dict[str, Any]:
        report, _, _ = self.run_case(self.config["synthetic_smoke"])
        return report
