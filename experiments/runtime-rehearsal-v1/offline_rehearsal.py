"""Compare pinned Rust actor inference with retained, hash-verified course rows.

No physics, policy activation, daemon, socket, device, or network connection.
Run with .venv-apple/bin/python; build the upstream policy-rehearsal example first.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / ".workspace/runtime-rehearsal-v1"
SOURCE = ROOT / "receipts/walking/20260906-v30-flat-regression"
TRACE = ROOT / "receipts/laser-course/20260913-v2-development-r2/nominal"
ACTORS = {
    "walking": ("policy.onnx", "402d8a8c2b5c67baac9e5cebcf347f8cc5e6159278230d2c452b9826ae4ce017"),
    "standing": ("standing/policy.onnx", "2fddc9a9bc4ff9a17a34af51215a31c43503cbe68a1b815a97b3042abf248db8"),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_file(path: Path, root: Path) -> str:
    entries = dict(line.split(maxsplit=1)[::-1] for line in (root / "SHA256SUMS").read_text().splitlines())
    digest = sha(path)
    if entries[str(path.relative_to(root))] != digest:
        raise ValueError(f"Recorded evidence changed: {path}")
    return digest


def main() -> None:
    output = WORK / "offline"
    output.mkdir(exist_ok=False)
    executable = WORK / "runtime/target/debug/examples/policy-rehearsal"
    dylibs = list((ROOT / ".venv-apple/lib").glob("python*/site-packages/onnxruntime/capi/libonnxruntime*.dylib"))
    if len(dylibs) != 1:
        raise ValueError("Expected exactly one local ONNX Runtime dylib")
    hashes = {str(TRACE / name): check_file(TRACE / name, TRACE)
              for name in ("motion.npz", "trajectory.jsonl.gz")}
    with gzip.open(TRACE / "trajectory.jsonl.gz", "rt") as stream:
        rows = [json.loads(line) for line in stream]
    with np.load(TRACE / "motion.npz") as motion:
        observations = motion["observations"]
        expected = motion["actions"]
    assert observations.shape == (3300, 61) and observations.dtype == np.float32
    assert expected.shape == (3300, 14) and expected.dtype == np.float32
    assert len(rows) == len(expected)
    roles = np.array([row["actor_mode"] for row in rows])
    result = {"schema": "microduck.runtime-offline-rehearsal.v1",
              "runtime_revision": "fead66bb21195971fcbb2858a19b1e290a9f2031",
              "runtime_binary_sha256": sha(executable), "ort_dylib_sha256": sha(dylibs[0]),
              "trace_hashes": hashes, "actors": {}, "scope": "recorded-observation actor inference",
              "observation_builder_evaluated": False, "daemon_evaluated": False,
              "physics_evaluated": False, "hardware_authority": False}
    for role, (name, digest) in ACTORS.items():
        policy = SOURCE / name
        if check_file(policy, SOURCE) != digest:
            raise ValueError(f"Wrong retained {role} actor")
        indices = np.flatnonzero(roles == role)
        trace = output / f"{role}-trace.json"
        trace.write_text(json.dumps([{"obs": observations[i].tolist()} for i in indices]) + "\n")
        raw = subprocess.run([str(executable), str(policy), str(trace)], check=True,
                             env={**os.environ, "ORT_DYLIB_PATH": str(dylibs[0])},
                             capture_output=True, text=True, timeout=60)
        (output / f"{role}-rust.json").write_text(raw.stdout)
        (output / f"{role}-rust.stderr").write_text(raw.stderr)
        data = json.loads(raw.stdout)
        actual = np.asarray(data.pop("actions"), dtype=np.float32)
        assert actual.shape == expected[indices].shape and np.isfinite(actual).all()
        matches = np.all(actual.view(np.uint32) == expected[indices].view(np.uint32), axis=1)
        result["actors"][role] = {
            **data, "policy_sha256": digest, "rows": len(indices),
            "bit_identical_rows": int(matches.sum()), "all_actions_bit_identical": bool(matches.all()),
            "max_absolute_error": float(np.max(np.abs(actual - expected[indices]))),
            "trace_sha256": sha(trace), "rust_output_sha256": sha(output / f"{role}-rust.json"),
        }
    result["passed"] = all(a["all_actions_bit_identical"] for a in result["actors"].values())
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
