"""Cross-platform canonicalization for non-semantic evaluator evidence fields."""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

TRAJECTORY_DECIMAL_PLACES = 11


def _canonicalize_trajectory_value(value: Any) -> Any:
    if isinstance(value, float):
        canonical = round(value, TRAJECTORY_DECIMAL_PLACES)
        return 0.0 if canonical == 0.0 else canonical
    if isinstance(value, list):
        return [_canonicalize_trajectory_value(item) for item in value]
    if isinstance(value, dict):
        return {
            key: _canonicalize_trajectory_value(item)
            for key, item in value.items()
        }
    return value


def canonical_trajectory_bytes(rows: list[dict[str, Any]]) -> bytes:
    """Serialize evaluator rows after removing measured cross-host FP tails."""
    canonical = _canonicalize_trajectory_value(rows)
    return (json.dumps(canonical, sort_keys=True, separators=(",", ":")) + "\n").encode()


def canonical_trajectory_sha256(rows: list[dict[str, Any]]) -> str:
    return "sha256:" + hashlib.sha256(canonical_trajectory_bytes(rows)).hexdigest()


def semantic_report_projection(report: dict[str, Any]) -> dict[str, Any]:
    """Return the byte-comparable report projection, retaining provenance elsewhere.

    Exact package versions and the raw IEEE-754 trajectory digest remain in the
    emitted report as truthful host provenance. They are excluded only from the
    cross-host semantic comparison, which separately binds canonical row bytes.
    """
    projected = copy.deepcopy(report)
    projected.pop("runtime", None)
    projected.get("integrity", {}).pop("trajectory_sha256", None)
    return projected
