"""Validation, assembly, and selection helpers for Apple scaling receipts."""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from pathlib import Path
from typing import Any

REQUIRED_SIZES = [64, 128, 256, 512, 1024]


def validate_row(row: dict[str, Any]) -> None:
    if row.get("schema_version") != "microduck.apple-scaling-row/v1":
        raise AssertionError("unexpected row schema")
    required = {
        "num_envs", "construction_s", "warmup_iteration_s", "collection_s",
        "learner_update_s", "total_iteration_s", "reset_s", "synchronization_s",
        "env_steps_per_s", "samples_per_minute", "peak_rss_bytes",
        "unified_memory", "devices", "backend", "thermal", "finite",
        "termination_reason", "benchmark", "source", "machine", "packages",
        "proof_class", "task_success",
    }
    missing = required - set(row)
    if missing:
        raise AssertionError(f"scaling row missing fields: {sorted(missing)}")
    if row["num_envs"] not in REQUIRED_SIZES:
        raise AssertionError("unexpected environment count")
    if row["devices"] != {"physics": "metal", "learner": "mps"}:
        raise AssertionError("Apple primary benchmark requires Metal + MPS")
    for key in (
        "construction_s", "warmup_iteration_s", "collection_s", "learner_update_s",
        "total_iteration_s", "reset_s", "synchronization_s", "env_steps_per_s",
        "samples_per_minute", "peak_rss_bytes",
    ):
        if not isinstance(row[key], (int, float)) or row[key] < 0:
            raise AssertionError(f"invalid metric: {key}")
    if row["finite"] != {"observations": True, "learner_parameters": True} or row["termination_reason"] != "completed":
        raise AssertionError("benchmark row is not a finite completion")
    if row["unified_memory"]["method"] != "peak_process_rss_proxy":
        raise AssertionError("unified-memory proxy must be explicit")
    if not row["unified_memory"].get("limitations"):
        raise AssertionError("unified-memory proxy limitations are required")
    if not row["thermal"]["method"] or not row["thermal"]["limitations"]:
        raise AssertionError("thermal method and limitations are required")
    if row["source"].get("dirty"):
        raise AssertionError("benchmark source must be a clean commit")
    if row["machine"].get("serial_recorded") is not False:
        raise AssertionError("machine identity must omit the serial number")
    if not all(name in row["packages"] for name in ("genesis-world", "torch", "rsl-rl-lib")):
        raise AssertionError("benchmark package identities are incomplete")
    if row["proof_class"] != "performance_characterization" or row["task_success"] != "not_evaluated":
        raise AssertionError("scaling row promoted task evidence")


def validate_sweep(receipt: dict[str, Any]) -> None:
    if receipt["schema_version"] != "microduck.apple-scaling-sweep/v1":
        raise AssertionError("unexpected sweep schema")
    rows = receipt["rows"]
    if [row["num_envs"] for row in rows] != REQUIRED_SIZES:
        raise AssertionError("sweep must contain required sizes in order")
    for row in rows:
        validate_row(row)
    commits = {row["source"]["commit"] for row in rows}
    if len(commits) != 1 or receipt.get("source_commit") not in commits:
        raise AssertionError("sweep rows must share the declared source commit")
    if receipt["proof_class"] != "performance_characterization" or receipt["task_success"] != "not_evaluated":
        raise AssertionError("scaling sweep promoted task evidence")


def assemble_sweep(row_paths: list[Path], run_id: str) -> dict[str, Any]:
    """Load required clean-commit rows and return a stable sweep receipt."""
    rows = [json.loads(path.read_text()) for path in row_paths]
    receipt = {
        "schema_version": "microduck.apple-scaling-sweep/v1",
        "run_id": run_id,
        "source_commit": rows[0]["source"]["commit"] if rows else "",
        "rows": rows,
        "proof_class": "performance_characterization",
        "task_success": "not_evaluated",
        "limitations": (
            "Short public development workload; no final candidate, held-out "
            "realization, transfer, physical result, or task-success evidence."
        ),
    }
    validate_sweep(receipt)
    return receipt


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def summarize_sustained(iterations: list[dict[str, Any]], num_envs: int, steps_per_env: int) -> dict[str, float]:
    if len(iterations) != 120:
        raise AssertionError("sustained receipt requires 120 measured iterations")
    totals = [float(item["total_iteration_s"]) for item in iterations]
    first_median = statistics.median(totals[:20])
    last_median = statistics.median(totals[-20:])
    ordered = sorted(totals)
    return {
        "first_20_median_total_iteration_s": first_median,
        "last_20_median_total_iteration_s": last_median,
        "slowdown_ratio": last_median / first_median,
        "p50_total_iteration_s": statistics.median(totals),
        "p95_total_iteration_s": ordered[math.ceil(0.95 * len(ordered)) - 1],
        "samples_per_minute": num_envs * steps_per_env * len(iterations) * 60.0 / sum(totals),
    }


def validate_sustained(receipt: dict[str, Any]) -> None:
    if receipt.get("schema_version") != "microduck.apple-sustained/v1":
        raise AssertionError("unexpected sustained schema")
    if receipt.get("num_envs") != 1024:
        raise AssertionError("unexpected sustained environment count")
    if receipt.get("devices") != {"physics": "metal", "learner": "mps"}:
        raise AssertionError("sustained test requires Metal + MPS")
    if receipt.get("source", {}).get("dirty"):
        raise AssertionError("sustained source must be a clean commit")
    if receipt.get("termination_reason") != "completed":
        raise AssertionError("sustained run did not complete")
    iterations = receipt.get("iterations", [])
    if len(iterations) != 120:
        raise AssertionError("sustained run is incomplete")
    if not all(item.get("finite") == {"observations": True, "learner_parameters": True} for item in iterations):
        raise AssertionError("sustained run contains non-finite state")
    if not all(sample.get("state") == "nominal" for sample in receipt.get("thermal_samples", [])):
        raise AssertionError("sustained run contains a thermal warning")
    memory = receipt.get("unified_memory", {})
    if memory.get("method") != "peak_process_rss_proxy" or not memory.get("limitations"):
        raise AssertionError("sustained memory proxy is incomplete")
    if memory.get("headroom_fraction_proxy", 0.0) < 0.25:
        raise AssertionError("sustained memory proxy headroom is below 25 percent")
    if receipt.get("summary", {}).get("slowdown_ratio", float("inf")) > 1.25:
        raise AssertionError("sustained slowdown gate failed")
    if receipt.get("proof_class") != "performance_characterization" or receipt.get("task_success") != "not_evaluated":
        raise AssertionError("sustained receipt promoted task evidence")


def select_default(rows: list[dict[str, Any]]) -> int:
    safe = []
    for row in rows:
        validate_row(row)
        if row["thermal"]["state_after"] != "nominal":
            continue
        if row["unified_memory"]["headroom_fraction_proxy"] < 0.25:
            continue
        safe.append(row)
    if not safe:
        raise AssertionError("no thermally and memory-safe Apple size")
    return max(safe, key=lambda row: (row["samples_per_minute"], -row["num_envs"]))["num_envs"]


def crossover_decision(rows: list[dict[str, Any]]) -> str | None:
    """Return the first matched grid size where Metal is no slower than CPU."""
    by_size: dict[int, dict[str, dict[str, Any]]] = {}
    for row in rows:
        by_size.setdefault(int(row["num_envs"]), {})[row["devices"]["physics"]] = row
    for size in REQUIRED_SIZES:
        pair = by_size.get(size, {})
        if set(pair) != {"cpu", "metal"}:
            continue
        if pair["metal"]["summary"]["median_total_iteration_s"] <= pair["cpu"]["summary"]["median_total_iteration_s"]:
            return "<=64" if size == 64 else str(size)
    return None
