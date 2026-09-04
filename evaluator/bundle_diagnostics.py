"""Fail-closed byte and semantic diagnostics for evaluator bundles."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import imageio.v2 as imageio
import numpy as np
import pyarrow.parquet as pq


def _digest(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _json_value(value: Any) -> Any:
    if isinstance(value, bytes):
        return {"bytes_hex": value.hex()}
    if isinstance(value, dict):
        return {
            str(key): _json_value(item)
            for key, item in sorted(value.items(), key=lambda row: str(row[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def _json_differences(left: Any, right: Any, path: str = "$") -> list[dict[str, Any]]:
    if type(left) is not type(right):
        return [{"path": path, "left": left, "right": right}]
    if isinstance(left, dict):
        differences = []
        for key in sorted(set(left) | set(right)):
            child = f"{path}.{key}"
            if key not in left:
                differences.append(
                    {"path": child, "left": {"missing": True}, "right": right[key]}
                )
            elif key not in right:
                differences.append(
                    {"path": child, "left": left[key], "right": {"missing": True}}
                )
            else:
                differences.extend(_json_differences(left[key], right[key], child))
        return differences
    if isinstance(left, list):
        differences = []
        for index in range(max(len(left), len(right))):
            child = f"{path}[{index}]"
            if index >= len(left):
                differences.append(
                    {"path": child, "left": {"missing": True}, "right": right[index]}
                )
            elif index >= len(right):
                differences.append(
                    {"path": child, "left": left[index], "right": {"missing": True}}
                )
            else:
                differences.extend(
                    _json_differences(left[index], right[index], child)
                )
        return differences
    return [] if left == right else [{"path": path, "left": left, "right": right}]


def _first_byte_difference(left: bytes, right: bytes) -> dict[str, Any]:
    shared = min(len(left), len(right))
    offset = next(
        (index for index in range(shared) if left[index] != right[index]), shared
    )
    start = max(0, offset - 8)
    end = min(max(len(left), len(right)), offset + 9)
    return {
        "offset": offset,
        "left_hex": left[start : min(end, len(left))].hex(),
        "right_hex": right[start : min(end, len(right))].hex(),
        "window_start": start,
    }


def _parquet_details(left: Path, right: Path) -> dict[str, Any]:
    left_file = pq.ParquetFile(left)
    right_file = pq.ParquetFile(right)
    left_table = left_file.read()
    right_table = right_file.read()
    return {
        "semantic_table_equal": left_table.equals(right_table),
        "schema_equal": left_table.schema.equals(
            right_table.schema, check_metadata=True
        ),
        "left_metadata": _json_value(left_file.metadata.to_dict()),
        "right_metadata": _json_value(right_file.metadata.to_dict()),
    }


def _read_video(path: Path) -> tuple[dict[str, Any], list[np.ndarray]]:
    reader = imageio.get_reader(path, "ffmpeg")
    try:
        metadata = _json_value(reader.get_meta_data())
        frames = [frame for frame in reader]
    finally:
        reader.close()
    return metadata, frames


def _video_details(left: Path, right: Path) -> dict[str, Any]:
    try:
        left_metadata, left_frames = _read_video(left)
        right_metadata, right_frames = _read_video(right)
    except Exception as error:  # retain the original byte mismatch on decode failure
        return {"decode_error": f"{type(error).__name__}: {error}"}
    first_frame_difference = None
    for index, (left_frame, right_frame) in enumerate(
        zip(left_frames, right_frames)
    ):
        if not np.array_equal(left_frame, right_frame):
            delta = np.abs(
                left_frame.astype(np.int16) - right_frame.astype(np.int16)
            )
            first_frame_difference = {
                "frame_index": index,
                "different_values": int(np.count_nonzero(delta)),
                "max_channel_delta": int(delta.max()),
                "left_rgb24_sha256": _digest(left_frame.tobytes(order="C")),
                "right_rgb24_sha256": _digest(right_frame.tobytes(order="C")),
            }
            break
    return {
        "decoded_frame_count": {
            "left": len(left_frames),
            "right": len(right_frames),
        },
        "decoded_frames_equal": (
            len(left_frames) == len(right_frames)
            and first_frame_difference is None
        ),
        "first_decoded_frame_difference": first_frame_difference,
        "metadata_differences": _json_differences(
            left_metadata, right_metadata
        ),
    }


def compare_bundle_bytes(
    left_root: Path, right_root: Path, names: Iterable[str]
) -> list[dict[str, Any]]:
    """Describe every byte mismatch without weakening exact equality."""
    differences = []
    for name in names:
        left_path = left_root / name
        right_path = right_root / name
        left = left_path.read_bytes()
        right = right_path.read_bytes()
        if left == right:
            continue
        detail: dict[str, Any] = {
            "name": name,
            "left_sha256": _digest(left),
            "right_sha256": _digest(right),
            "left_size": len(left),
            "right_size": len(right),
            "first_byte_difference": _first_byte_difference(left, right),
        }
        if name.endswith(".json"):
            left_json = json.loads(left)
            right_json = json.loads(right)
            detail["json_differences"] = _json_differences(left_json, right_json)
            if name == "attestation.json":
                left_artifacts = left_json.get("artifacts", {})
                right_artifacts = right_json.get("artifacts", {})
                detail["changed_attested_artifacts"] = sorted(
                    artifact
                    for artifact in set(left_artifacts) | set(right_artifacts)
                    if left_artifacts.get(artifact) != right_artifacts.get(artifact)
                )
        elif name.endswith(".parquet"):
            detail["parquet"] = _parquet_details(left_path, right_path)
        elif name.endswith(".mp4"):
            detail["video"] = _video_details(left_path, right_path)
        differences.append(detail)
    return differences


def format_bundle_differences(differences: list[dict[str, Any]]) -> str:
    return json.dumps(
        {"bundle_byte_differences": differences},
        indent=2,
        sort_keys=True,
    )
