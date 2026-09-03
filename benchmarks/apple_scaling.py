"""Validation, assembly, and selection helpers for Apple scaling receipts."""

from __future__ import annotations

import hashlib
import json
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
    return min(safe, key=lambda row: (row["total_iteration_s"], row["num_envs"]))["num_envs"]
