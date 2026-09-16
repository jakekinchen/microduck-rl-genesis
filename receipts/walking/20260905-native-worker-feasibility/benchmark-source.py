"""Bounded native MuJoCo/BAM throughput feasibility, not behavior acceptance.

No training or new policy. Workers run the same existing unfiltered ONNX in
independent native worlds. Report synchronized stepping separately from setup.
"""
import argparse
import json
import multiprocessing as mp
from pathlib import Path
import shutil
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def worker(barrier, queue, steps):
    world = None
    try:
        from experiments.walking.sensor_world import ConsistentSensorWalkingWorld
        world = ConsistentSensorWalkingWorld(
            ROOT / "receipts/walking/20260905-v6-current-sensor/policy.onnx",
            ROOT / ".workspace/bam", motor_ticks=4, sensor_ticks=1, yaw=.2,
            seed=76701, render=False)
        barrier.wait(timeout=60)
        started = time.monotonic()
        inference_ms = 0.
        completed = 0
        for _ in range(steps):
            row = world.step_command([.12, 0, 0])
            inference_ms += row["latency_ms"]
            completed += 1
            if world.fell:
                break
        finished = time.monotonic()
        queue.put({"pid": __import__("os").getpid(), "started_monotonic_s": started,
                   "finished_monotonic_s": finished, "completed_control_steps": completed,
                   "loop_s": finished - started, "inference_ms": inference_ms,
                   "fell": world.fell, "last_qpos": world.core.data.qpos.tolist()})
    except BaseException as error:
        barrier.abort()
        queue.put({"error": f"{type(error).__name__}: {error}"})
    finally:
        if world is not None:
            world.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    from scripts.evaluate_laser import digest
    policy = ROOT / "receipts/walking/20260905-v6-current-sensor/policy.onnx"
    expected = "948f6e601098845bf394c60de61cb38aa435d61934b86fc46dd39e4c9908c8cb"
    if digest(policy) != expected:
        raise ValueError("known retained v6 policy required")
    args.output.mkdir(parents=True, exist_ok=False)
    ctx = mp.get_context("spawn")
    reports = []
    for count in (1, 2, 4):
        queue = ctx.Queue()
        barrier = ctx.Barrier(count)
        processes = [ctx.Process(target=worker, args=(barrier, queue, 500)) for _ in range(count)]
        started = time.monotonic()
        try:
            for process in processes:
                process.start()
            results = [queue.get(timeout=60) for _ in processes]
            for process in processes:
                process.join(timeout=5)
            if any("error" in result for result in results):
                raise RuntimeError(str(results))
            if any(process.is_alive() or process.exitcode != 0 for process in processes):
                raise RuntimeError("benchmark worker failed or did not finish")
            span = max(result["finished_monotonic_s"] for result in results) - min(result["started_monotonic_s"] for result in results)
            steps = sum(result["completed_control_steps"] for result in results)
            report = {"workers": count, "control_steps_completed": steps,
                      "synchronized_step_span_s": span,
                      "control_transitions_per_s": steps / span,
                      "end_to_end_s_including_spawn_and_model_setup": time.monotonic() - started,
                      "worker_results": results}
            reports.append(report)
            print(json.dumps(report), flush=True)
        finally:
            # Only these newly created benchmark child processes are owned here.
            for process in processes:
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=5)
            queue.close()
            queue.join_thread()
    if digest(policy) != expected:
        raise ValueError("policy changed")
    report = {"schema": "microduck.native-walking-worker-feasibility/v1", "cases": reports,
              "policy_sha256": expected, "training_performed": False,
              "boundary": "Native C MuJoCo + pinned Python BAM + per-worker ONNX, one env/worker, 1/2/4 spawned processes, under concurrent v8 Metal training. No reward computation, batched MPS inference, PPO, exclusive-host scaling or walking acceptance is measured. Children are joined or terminated; no other process is controlled."}
    (args.output / "benchmark.json").write_text(json.dumps(report, indent=2) + "\n")
    shutil.copy2(Path(__file__), args.output / "benchmark-source.py")
    shutil.copytree(ROOT / "receipts/walking/20260905-v6-current-sensor/evaluator-source", args.output / "evaluator-source")
    (args.output / "SHA256SUMS").write_text("".join(
        f"{digest(path)}  {path.relative_to(args.output)}\n"
        for path in sorted(args.output.rglob("*")) if path.is_file()))


if __name__ == "__main__":
    main()
