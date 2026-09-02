#!/usr/bin/env python3
"""Inspect an ONNX artifact without creating an inference session.

This command parses protobuf structure and initializer tensors with ``onnx``.
It deliberately does not import ONNX Runtime or execute graph nodes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import onnx
from onnx import numpy_helper


def sha256_bytes(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def tensor_shape(value: onnx.ValueInfoProto) -> list[int | str]:
    return [
        dimension.dim_value
        if dimension.HasField("dim_value")
        else dimension.dim_param
        for dimension in value.type.tensor_type.shape.dim
    ]


def inspect(path: Path) -> dict[str, object]:
    payload = path.read_bytes()
    model = onnx.load_model(path, load_external_data=False)
    onnx.checker.check_model(model, full_check=False)

    initializers = {value.name: value for value in model.graph.initializer}
    normalized_frontend: dict[str, object] = {"detected": False}
    nodes = list(model.graph.node)
    if len(nodes) >= 2 and nodes[0].op_type == "Sub" and nodes[1].op_type == "Div":
        mean_name = nodes[0].input[1] if len(nodes[0].input) > 1 else ""
        scale_name = nodes[1].input[1] if len(nodes[1].input) > 1 else ""
        if mean_name in initializers and scale_name in initializers:
            mean = numpy_helper.to_array(initializers[mean_name])
            scale = numpy_helper.to_array(initializers[scale_name])
            normalized_frontend = {
                "detected": True,
                "operations": ["Sub", "Div"],
                "mean_shape": list(mean.shape),
                "mean_sha256": sha256_bytes(mean.tobytes(order="C")),
                "scale_shape": list(scale.shape),
                "scale_sha256": sha256_bytes(scale.tobytes(order="C")),
            }

    return {
        "inspection_mode": "protobuf_structure_only_no_execute",
        "path_basename": path.name,
        "size_bytes": len(payload),
        "sha256": sha256_bytes(payload),
        "checker": "pass",
        "ir_version": model.ir_version,
        "opsets": [
            {"domain": item.domain, "version": item.version}
            for item in model.opset_import
        ],
        "producer": {
            "name": model.producer_name,
            "version": model.producer_version,
        },
        "metadata": {
            item.key: item.value for item in sorted(model.metadata_props, key=lambda x: x.key)
        },
        "inputs": [
            {
                "name": value.name,
                "element_type": value.type.tensor_type.elem_type,
                "shape": tensor_shape(value),
            }
            for value in model.graph.input
        ],
        "outputs": [
            {
                "name": value.name,
                "element_type": value.type.tensor_type.elem_type,
                "shape": tensor_shape(value),
            }
            for value in model.graph.output
        ],
        "node_count": len(nodes),
        "node_operations": sorted({node.op_type for node in nodes}),
        "normalizer_frontend": normalized_frontend,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--no-execute",
        action="store_true",
        help="required acknowledgement that graph execution is forbidden",
    )
    parser.add_argument("artifact", type=Path)
    args = parser.parse_args()
    if not args.no_execute:
        parser.error("--no-execute is required")
    print(json.dumps(inspect(args.artifact), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
