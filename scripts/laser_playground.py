"""Loopback-only live MuJoCo/BAM policy playground, initially paused."""
import argparse
import io
import json
import math
from pathlib import Path
import queue
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from PIL import Image
from experiments.laser.world import LaserWorld
from experiments.laser.gait import GaitProbe
from experiments.laser.face_world import FaceFirstLaserWorld
from microduck.laser_dynamics import PROGRAMS, domain_draw, program_target
from scripts.evaluate_laser import digest


def validate_control(data):
    if not isinstance(data, dict) or not data or set(data)-{"mode", "target", "paused", "hidden", "reset", "domain", "view"}:
        raise ValueError("unknown or empty control")
    if "mode" in data and data["mode"] not in PROGRAMS:
        raise ValueError("unknown route")
    if "view" in data and data["view"] not in ("inspection", "fixed", "activity"):
        raise ValueError("unknown camera view")
    for key in ("paused", "hidden", "reset"):
        if key in data and not isinstance(data[key], bool):
            raise ValueError(f"{key} must be boolean")
    if "domain" in data and data["domain"] not in ("nominal", "low-grip", "randomized"):
        raise ValueError("unknown domain")
    if "target" in data:
        xy = data["target"]
        if not isinstance(xy, list) or len(xy) != 2 or not all(type(v) in (int, float) and math.isfinite(v) and abs(v) <= 1 for v in xy):
            raise ValueError("target must be two finite coordinates within ±1 m")
    return data


def playground_target(mode, t, rotation=0.):
    return program_target(mode, t % 48 if mode == "retarget" else t, rotation=rotation)


class Simulation:
    def __init__(self, policy, bam, event_log):
        self.policy, self.bam, self.event_log = policy, bam, event_log
        self.commands = queue.Queue(maxsize=64)
        self.lock, self.stop = threading.Lock(), threading.Event()
        self.state, self.jpeg = {"ready": False, "paused": True, "error": None}, None
        self.thread = threading.Thread(target=self.run, daemon=True)

    def run(self):
        world = None
        paused, hidden, mode, target, domain_name = True, False, "retarget", [.6, 0.], "nominal"
        view, inspected_step, diagnostic = "inspection", -1, None
        seed, generation = 76000, 0
        rebuild = True
        started = time.monotonic()
        try:
            with self.event_log.open("x") as log:
                log.write(json.dumps({"policy_sha256": digest(self.policy), "source": "interactive local simulation", "started_unix": time.time()})+"\n")
                while not self.stop.is_set():
                    tick = time.monotonic()
                    redraw = False
                    while not self.commands.empty():
                        data = self.commands.get_nowait()
                        redraw = True
                        log.write(json.dumps({"wall_elapsed_s": tick-started, "simulation_time_s": world.steps*.02 if world else 0, "control": data})+"\n")
                        log.flush()
                        mode = data.get("mode", mode)
                        view = data.get("view", view)
                        paused, hidden = data.get("paused", paused), data.get("hidden", hidden)
                        if "target" in data:
                            target, mode = data["target"], "manual"
                        if "domain" in data:
                            domain_name = data["domain"]
                            rebuild, paused = True, True
                        if data.get("reset"):
                            rebuild, paused = True, True
                    if rebuild:
                        if world:
                            world.close()
                        seed += 1
                        domain = domain_draw(seed, domain_name == "randomized")
                        if domain_name == "low-grip":
                            domain["friction_ratio"] = .6
                        world = FaceFirstLaserWorld(self.policy, self.bam, domain, True)
                        probe, inspected_step = GaitProbe(world.core), -1
                        generation += 1
                        rebuild, hidden = False, False
                        if mode != "manual":
                            target = playground_target(mode, 0., domain["route_rotation_rad"])[0]
                        world.step(target)
                        redraw = True
                    t = world.steps*.02
                    if mode != "manual":
                        target, route_visible, label, _ = playground_target(mode, t, domain["route_rotation_rad"])
                    else:
                        route_visible, label = True, "Your target"
                    visible = route_visible and not hidden
                    if not paused and not world.fell:
                        world.step(target, visible)
                        if world.fell:
                            paused = True
                            redraw = True
                    if redraw or (not paused and world.steps % 2 == 0):
                        frame = world.frame(target, visible, view=view)
                        buf = io.BytesIO()
                        Image.fromarray(frame).save(buf, format="JPEG", quality=85)
                        with self.lock:
                            self.jpeg = buf.getvalue()
                    row = dict(world.latest)
                    if inspected_step != world.steps:
                        diagnostic = probe.sample(row)
                        inspected_step = world.steps
                    row.update({k:diagnostic[k] for k in ("face_world", "foot_normal_n", "sole_clearance_m", "loaded_contact_slip_m_s", "joint_limit_margin_fraction", "face_velocity_cosine")})
                    row.update(target_xy_m=list(map(float, target)), visible=visible,
                               distance_m=math.dist(target, row["robot_xyz_m"][:2]),
                               ready=True, paused=paused, hidden=hidden, mode=mode, label=label,
                               domain_name=domain_name, domain=domain, generation=generation,
                               robot_trail=[p[:2].tolist() for p in list(world.robot_trail)[::5]],
                               target_trail=[p[:2].tolist() for p in list(world.target_trail)[::5]],
                               policy_sha256=digest(self.policy) if not hasattr(self, "policy_hash") else self.policy_hash,
                               gait_status="UNVALIDATED — diagnostic only", view=view,
                               camera_revision=world.camera_revision,
                               error=None)
                    self.policy_hash = row["policy_sha256"]
                    with self.lock:
                        self.state = row
                    self.stop.wait(max(0, (.1 if paused else .02)-(time.monotonic()-tick)))
        except Exception as exc:
            with self.lock:
                self.state.update(error=f"Simulation stopped: {type(exc).__name__}: {exc}", paused=True)
        finally:
            if world:
                world.close()


def handler_for(sim):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def respond(self, status, data, content_type="application/json"):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(data)

        def local_request(self):
            expected = f"127.0.0.1:{self.server.server_port}"
            return self.headers.get("Host") == expected and self.headers.get("Origin", f"http://{expected}") == f"http://{expected}"

        def do_GET(self):
            if not self.local_request():
                return self.respond(403, b'{"error":"loopback origin required"}')
            route = self.path.split("?")[0]
            assets = {"/": ("playground.html", "text/html; charset=utf-8"),
                      "/playground.css": ("playground.css", "text/css"),
                      "/playground.js": ("playground.js", "text/javascript")}
            if route in assets:
                name, mime = assets[route]
                return self.respond(200, (ROOT/"experiments/laser"/name).read_bytes(), mime)
            with sim.lock:
                state, jpeg = sim.state.copy(), sim.jpeg
            if route == "/state":
                return self.respond(200, json.dumps(state).encode())
            if route == "/frame.jpg" and jpeg:
                return self.respond(200, jpeg, "image/jpeg")
            self.respond(404, b'{"error":"not ready or not found"}')

        def do_POST(self):
            if not self.local_request() or self.path != "/control":
                return self.respond(403, b'{"error":"loopback control origin required"}')
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 1024 or self.headers.get("Content-Type") != "application/json":
                    raise ValueError("small JSON object required")
                data = validate_control(json.loads(self.rfile.read(size)))
                sim.commands.put_nowait(data)
                self.respond(202, b'{"queued":true}')
            except (ValueError, queue.Full) as exc:
                self.respond(400, json.dumps({"error": str(exc)}).encode())
    return Handler


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--policy-receipt", required=True, type=Path)
    p.add_argument("--bam-repo", required=True, type=Path)
    p.add_argument("--port", type=int, default=8947)
    p.add_argument("--max-seconds", type=int, default=1800)
    p.add_argument("--event-log", required=True, type=Path)
    args = p.parse_args()
    if not 1 <= args.max_seconds <= 43200 or not 1024 <= args.port <= 65535:
        p.error("duration 1..43200 seconds; nonprivileged port required")
    policy = args.policy_receipt/"policy.onnx"
    record = json.loads((args.policy_receipt/"evaluation.json").read_text())
    if digest(policy) != record["policy_sha256"]:
        raise ValueError("policy receipt digest mismatch")
    if args.event_log.exists() or not args.event_log.parent.is_dir():
        raise ValueError("event log must be a new file in an existing directory")
    sim = Simulation(policy, args.bam_repo, args.event_log)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler_for(sim))
    sim.thread.start()
    timer = threading.Timer(args.max_seconds, server.shutdown)
    timer.daemon = True
    timer.start()
    print(f"http://127.0.0.1:{args.port} / initially paused / expires after {args.max_seconds}s", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        timer.cancel()
        server.server_close()
        sim.stop.set()
        sim.thread.join(timeout=10)


if __name__ == "__main__":
    main()
