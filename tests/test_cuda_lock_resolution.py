"""Replay the harness CUDA-lock resolution with its exact pinned uv release."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UVX = shutil.which("uvx")
PYTHON = ROOT / ".venv-apple/bin/python"
LOCK = ROOT / "environments/cuda/requirements.lock"

assert UVX is not None, "uvx is required for the pinned-uv resolution regression"
assert PYTHON.is_file(), "the verified Python 3.12 environment is required"

python_version = subprocess.run(
    [str(PYTHON), "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
    check=True,
    capture_output=True,
    text=True,
).stdout.strip()
assert python_version == "3.12"

uv_command = [UVX, "--from", "uv==0.8.19", "uv"]
uv_version = subprocess.run(
    [*uv_command, "--version"], check=True, capture_output=True, text=True
).stdout.strip()
assert uv_version.startswith("uv 0.8.19 "), uv_version

with tempfile.TemporaryDirectory(prefix="m5-cuda-lock-resolution-") as target:
    result = subprocess.run(
        [
            *uv_command,
            "pip",
            "install",
            "--dry-run",
            "--python",
            str(PYTHON),
            "--python-platform",
            "x86_64-manylinux_2_39",
            "--torch-backend",
            "cu128",
            "--require-hashes",
            "--strict",
            "--target",
            target,
            "-r",
            str(LOCK),
        ],
        cwd=ROOT,
        env={**os.environ, "UV_NO_PROGRESS": "1"},
        capture_output=True,
        text=True,
    )
output = result.stdout + result.stderr
assert result.returncode == 0, "\n".join(output.splitlines()[-80:])
assert "Resolved 126 packages" in output
assert "torch==2.9.1+cu128" in output
assert "genesis-world==1.3.3" in output

harness = (ROOT / "scripts/run_m5_cuda_pilot.sh").read_text()
install_start = harness.index('run_logged genesis-dependencies "$UV" pip install')
install_end = harness.index("\n\n", install_start)
install_block = harness[install_start:install_end]
assert "--torch-backend cu128" in install_block
assert "--require-hashes --strict" in install_block
assert "environments/cuda/requirements.lock" in install_block

print("pinned uv 0.8.19 linux/amd64 cu128 lock resolution verified: 126 packages")
