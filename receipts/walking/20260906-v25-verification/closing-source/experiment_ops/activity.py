"""Read compute process identity without importing or controlling a simulator."""
from datetime import datetime, timezone
from pathlib import Path
import os
import json
import sys
import re
import shlex
import shutil
import subprocess

SIMULATION_TESTS = {
    "smoke_env.py", "bench.py", "test_bam_closed_loop_fixture.py",
    "test_evaluator_core.py", "test_bam_vs_mujoco.py", "test_dr.py",
    "test_external_torque.py", "test_backlash.py", "test_laser_task.py",
    "test_onnx_deploy.py", "test_obs_contract.py", "test_walking.py",
    "test_walking_sensor_phase.py", "test_walking_ground.py",
    "test_walking_terrain_v23.py",
}
SIMULATION_DIAGNOSTICS = {
    "probe_walking_pair_genesis.py", "probe_walking_pair_genesis_r2.py",
    "evaluate_walking_yaw_refinement.py", "audit_walking_imported_physics.py",
    "evaluate_walking_physical_development.py",
    "evaluate_walking_terrain_endurance.py",
    "evaluate_walking_heading_persistence.py", "evaluate_walking_public_surfaces.py",
    "evaluate_walking_public_standing_v26.py", "render_public_surface_receipt.py",
    "evaluate_public_curriculum_v27.py", "evaluate_heading_regression_v24.py",
    "audit_public_surface_physics.py", "probe_public_surface_genesis.py",
    "probe_public_surface_action_replay_v1.py",
    "evaluate_motion_heading_flat_v28.py", "evaluate_motion_heading_endurance_v28.py",
    "evaluate_heading_headroom_flat_v29.py", "evaluate_heading_headroom_endurance_v29.py",
    "evaluate_heading_headroom_surfaces_v29.py",
    "evaluate_heading_headroom_flat_v30.py", "evaluate_heading_headroom_endurance_v30.py",
    "evaluate_heading_headroom_surfaces_v30.py",
}


def python_entrypoint(argv):
    """Locate the script/module operand, never a filename embedded in code or data."""
    i = 1
    while i < len(argv):
        token = argv[i]
        if token == "-c" or token == "-" or token.startswith("-c"):
            return None
        if token == "-m":
            return argv[i + 1].replace(".", "/") + ".py" if i + 1 < len(argv) else None
        if token == "--":
            return argv[i + 1] if i + 1 < len(argv) else None
        if token in {"-W", "-X"}:
            i += 2
        elif token.startswith(("-W", "-X")) or token in {
            "-u", "-B", "-O", "-OO", "-E", "-s", "-S", "-I", "-q", "-v", "-b", "-bb",
        }:
            i += 1
        elif token.startswith("-"):
            return None
        else:
            return token
    return None


def workload(script):
    name = Path(script).name
    if name == "train.py" or name.startswith("train_") and name.endswith(".py"):
        return "training"
    if name == "run_all.py":
        return "simulation_suite"
    if name in SIMULATION_TESTS:
        return "simulation_test"
    if name in SIMULATION_DIAGNOSTICS:
        return "simulation_diagnostic"
    return None


def parse_processes(text):
    result = []
    for line in text.splitlines():
        columns = line.strip().split(None, 3)
        if len(columns) != 4 or not columns[0].isdigit() or not columns[1].isdigit():
            continue
        try:
            argv = shlex.split(columns[3])
        except ValueError:
            continue
        if not argv or not re.match(r"^python(?:\d+(?:\.\d+)*)?$", Path(argv[0]).name):
            continue
        script = python_entrypoint(argv)
        kind = workload(script) if script else None
        if kind:
            result.append({"pid": int(columns[0]), "ppid": int(columns[1]), "elapsed": columns[2],
                           "entrypoint": Path(script).name, "workload": kind})
    return result


def inspect(root: Path):
    root = root.resolve(strict=True)
    result = {"schema_version": "microduck.ops.activity.v1", "root": str(root),
              "generated_at": datetime.now(timezone.utc).isoformat(), "read_only": True,
              "status": "unknown", "processes": [],
              "boundary": "Instantaneous advisory inventory of known Python training and simulation-test entrypoints. The legacy no_known_training_process status means no recognized compute candidate; absence is not proof of idleness; unrecognized launchers and remote jobs are outside coverage. No lock, admission, process control or training status mutation."}
    try:
        completed = subprocess.run(["ps", "-axo", "pid=,ppid=,etime=,args="],
                                   text=True, capture_output=True, timeout=5, check=True)
        candidates = parse_processes(completed.stdout)
        if len(candidates) > 32:
            raise ValueError("more than 32 compute candidates; ownership check is incomplete")
        lsof = shutil.which("lsof") or ("/usr/sbin/lsof" if Path("/usr/sbin/lsof").exists() else None)
        for item in candidates:
            if item["pid"] == os.getpid():
                continue
            cwd = None
            if lsof:
                try:
                    probe = subprocess.run([lsof, "-a", "-p", str(item["pid"]), "-d", "cwd", "-Fn"],
                                           text=True, capture_output=True, timeout=2, check=False)
                    cwd = next((s[1:] for s in probe.stdout.splitlines() if s.startswith("n")), None)
                except (OSError, subprocess.SubprocessError):
                    pass
            same_root = cwd and (Path(cwd).resolve() == root or Path(cwd).resolve().is_relative_to(root))
            item["ownership"] = ("cwd_matches_repository" if same_root else
                                 "different_directory" if cwd else "unknown")
            result["processes"].append(item)
        result["status"] = "busy" if result["processes"] else "no_known_training_process"
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        result["error"] = str(error)
    return result


def require_idle(root: Path):
    """Fail closed before a full simulation suite; exclude only this process itself."""
    result = inspect(root)
    if result["status"] != "no_known_training_process":
        print(json.dumps(result, indent=2), file=sys.stderr)
        print("Compute preflight refused launch. Wait for the listed job to finish; "
              "use ./scripts/duck verify for workspace-only checks.", file=sys.stderr)
        raise SystemExit(3 if result["status"] == "busy" else 2)
