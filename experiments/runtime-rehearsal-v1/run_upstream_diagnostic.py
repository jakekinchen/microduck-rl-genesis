"""One bounded, localhost-only unmodified upstream daemon/body diagnostic."""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import socket
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / ".workspace/runtime-rehearsal-v1"
SOURCE = ROOT / "receipts/walking/20260906-v30-flat-regression"
PHASES = [(2.0, "stand", 0.0, 0.0), (6.0, "walk", .12, 0.0),
          (8.0, "turn", 0.0, .4), (12.0, "stop", 0.0, 0.0)]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class RPC:
    def __init__(self, address, family=socket.AF_INET):
        self.socket = socket.socket(family)
        self.socket.settimeout(.5)
        self.socket.connect(address)
        self.stream = self.socket.makefile("rw")
        self.ident = 0

    def call(self, request):
        self.stream.write(json.dumps(request) + "\n")
        self.stream.flush()
        line = self.stream.readline()
        if not line:
            raise RuntimeError("RPC connection closed")
        return json.loads(line)

    def daemon(self, method, params=None):
        self.ident += 1
        answer = self.call({"jsonrpc": "2.0", "id": self.ident, "method": method,
                            "params": params or {}})
        if "error" in answer:
            raise RuntimeError(f"{method}: {answer['error']}")
        if method in ("robot.enable", "robot.move") and answer.get("result", {}).get("accepted") is not True:
            raise RuntimeError(f"{method} was not accepted: {answer}")
        return answer

    def close(self):
        self.stream.close()
        self.socket.close()


def main():
    output = WORK / "upstream-diagnostic"
    output.mkdir(exist_ok=False)
    state = WORK / "s"
    state.mkdir(exist_ok=False)
    sock = state / "d.sock"
    tof_sock = state / "t.sock"
    assert len(str(sock).encode()) < 104
    policies = {"walk": SOURCE / "policy.onnx", "stand": SOURCE / "standing/policy.onnx"}
    expected = {"walk": "402d8a8c2b5c67baac9e5cebcf347f8cc5e6159278230d2c452b9826ae4ce017",
                "stand": "2fddc9a9bc4ff9a17a34af51215a31c43503cbe68a1b815a97b3042abf248db8"}
    assert {k: sha(p) for k, p in policies.items()} == expected
    params = state / "params.toml"
    params.write_text(f'''[policy]
enabled = true
walk = "{policies['walk']}"
stand = "{policies['stand']}"
sitstand = "none"
ground_pick = "none"
kick_left = "none"
kick_right = "none"
roulade = "none"
action_scale = 1.0
standing_action_scale = 1.0
standing_gain_ratio = 1.0
head_lowpass = 1.0
legs_lowpass = 1.0
voltage_adapt = false
[chorale]
accept = false
[tof]
socket = "{tof_sock}"
''')
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    python = ROOT / ".venv-apple/bin/python"
    binaries = WORK / "runtime/target/debug"
    dylib, = (ROOT / ".venv-apple/lib").glob("python*/site-packages/onnxruntime/capi/libonnxruntime*.dylib")
    env = {**os.environ, "PYTHONPATH": str(WORK / "rl/src"), "ORT_DYLIB_PATH": str(dylib),
           "DUCK_RUNTIME_DIR": str(state), "DUCK_IDENTITY": "isolated-runtime-rehearsal-v1"}
    commands = {
        "body": [str(python), "-m", "mjlab_microduck.sim.body_server", "--host", "127.0.0.1",
                 "--port", str(port), "--ducks", "1", "--headless", "--keyframe", "HOME"],
        "tofd": [str(binaries / "tofd"), "--sim", f"127.0.0.1:{port}", "--socket", str(tof_sock)],
        "robotd": [str(binaries / "robotd"), "--sim", f"127.0.0.1:{port}",
                   "--params", str(params), "--socket", str(sock)],
    }
    result = {"schema": "microduck.upstream-runtime-diagnostic.v1",
              "scope": "changed-controller and changed-physics integration diagnostic",
              "behavior_acceptance": False, "physics_conformance": False, "hardware_authority": False,
              "protocol_sha256": sha(Path(__file__).with_name("PROTOCOL.md")),
              "script_sha256": sha(__file__), "params_sha256": sha(params),
              "policy_sha256": expected, "commands": commands,
              "planned_phases": PHASES, "completed_phases": [], "failures": [],
              "startup_held_body": True, "camera": False}
    processes, files, rpcs = {}, {}, []
    start = time.monotonic()
    body = daemon = None
    observations = []
    health = []
    acknowledgements = []
    try:
        for name in ("body", "tofd", "robotd"):
            files[name] = (output / f"{name}.log").open("w")
            processes[name] = subprocess.Popen(commands[name], cwd=WORK, env=env,
                                                stdout=files[name], stderr=subprocess.STDOUT)
        while time.monotonic() - start < 10:
            if any(p.poll() is not None for p in processes.values()):
                raise RuntimeError("A startup subprocess exited")
            try:
                if body is None:
                    body = RPC(("127.0.0.1", port)); rpcs.append(body)
                if daemon is None:
                    daemon = RPC(str(sock), socket.AF_UNIX); rpcs.append(daemon)
                h = daemon.daemon("robot.health")
                health.append({"stage": "startup", "answer": h})
                # Policy startup may finish after the socket begins answering.
                if h.get("result", {}).get("healthy"):
                    break
            except (ConnectionRefusedError, FileNotFoundError):
                pass
            time.sleep(.1)
        else:
            raise RuntimeError("Startup did not become healthy within 10 seconds")
        acknowledgements.append(daemon.daemon("robot.enable", {"on": True}))
        enabled = time.monotonic()
        first_sim = body.call({"op": "read"})["sim_time"]
        tick = 0
        while True:
            elapsed = time.monotonic() - enabled
            if elapsed >= 12:
                result["completed_phases"] = [phase[1] for phase in PHASES]
                break
            if time.monotonic() - start > 45:
                raise RuntimeError("Whole-run deadline exceeded")
            phase = next(phase for phase in PHASES if elapsed < phase[0])
            result["completed_phases"] = [p[1] for p in PHASES if elapsed >= p[0]]
            if tick % 5 == 0:
                acknowledgements.append(daemon.daemon("robot.move", {"vx": phase[2], "vy": 0., "vyaw": phase[3]}))
            sample = body.call({"op": "read"})
            gravity = sample["imu"]["gravity"]
            tilt = math.degrees(math.acos(max(-1., min(1., -gravity[2]))))
            sample.update(wall_elapsed_s=elapsed, phase=phase[1], tilt_deg=tilt)
            observations.append(sample)
            if not all(math.isfinite(v) for v in sample["trunk"] + gravity + sample["imu"]["gyro"]):
                raise RuntimeError("Nonfinite body telemetry")
            if sample["trunk_z"] < .07 or tilt > 70:
                result["failures"].append("fall")
                break
            if any(p.poll() is not None for p in processes.values()):
                raise RuntimeError("A subprocess exited during sequence")
            if tick % 25 == 0:
                health.append({"wall_elapsed_s": elapsed, "answer": daemon.daemon("robot.health")})
            tick += 1
            time.sleep(max(0., enabled + tick * .02 - time.monotonic()))
        final = observations[-1]
        result["elapsed_s"] = final["wall_elapsed_s"]
        result["simulated_s"] = final["sim_time"] - first_sim
        result["real_time_factor"] = result["simulated_s"] / max(result["elapsed_s"], 1e-9)
        if len(result["completed_phases"]) != 4:
            result["failures"].append("incomplete_phase_sequence")
    except Exception as exc:
        result["failures"].append(f"{type(exc).__name__}: {exc}")
    finally:
        if daemon is not None:
            try:
                acknowledgements.append(daemon.daemon("robot.enable", {"on": False}))
            except Exception as exc:
                result["disable_error"] = str(exc)
        for rpc in rpcs:
            try:
                rpc.close()
            except Exception as exc:
                result.setdefault("rpc_close_errors", []).append(str(exc))
        # Owned Popen handles only. Never signal by name or process group.
        for process in reversed(list(processes.values())):
            if process.poll() is None:
                process.terminate()
        for name, process in processes.items():
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill(); process.wait(timeout=3)
        for stream in files.values():
            stream.close()
        result["child_exit_codes"] = {name: p.returncode for name, p in processes.items()}
        result["all_owned_processes_reaped"] = all(p.poll() is not None for p in processes.values())
        with socket.socket() as check:
            check.settimeout(.2)
            result["listener_gone"] = check.connect_ex(("127.0.0.1", port)) != 0
        result["bounded_sequence_completed_without_fall"] = not result["failures"]
        result["status"] = "completed_diagnostic" if not result["failures"] else "terminal_negative"
        (output / "samples.json").write_text(json.dumps(observations, indent=2) + "\n")
        (output / "health.json").write_text(json.dumps(health, indent=2) + "\n")
        (output / "acknowledgements.json").write_text(json.dumps(acknowledgements, indent=2) + "\n")
        (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
