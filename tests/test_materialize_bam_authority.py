"""Prove moving branch heads cannot change materialized BAM authority."""

from __future__ import annotations

import importlib.util
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/materialize_bam_authority.py"

spec = importlib.util.spec_from_file_location("bam_materializer", SCRIPT)
assert spec is not None and spec.loader is not None
materializer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(materializer)


def command(*args: str, cwd: Path | None = None) -> str:
    return subprocess.run(
        args, cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


repository_url, frozen_commit = materializer.locked_authority()
assert repository_url == "https://github.com/Rhoban/bam.git"
assert frozen_commit == "62bd8ce12154340be97e06f7f41a0ca8f116d967"

with tempfile.TemporaryDirectory(prefix="bam-materializer-test-") as raw:
    root = Path(raw)
    source = root / "source"
    remote = root / "remote.git"
    checkout = root / "checkout"
    source.mkdir()
    command("git", "init", "-q", "-b", "mjlab_frictionloss", cwd=source)
    command("git", "config", "user.name", "Authority Test", cwd=source)
    command("git", "config", "user.email", "authority@example.invalid", cwd=source)
    (source / "authority.txt").write_text("frozen\n")
    command("git", "add", "authority.txt", cwd=source)
    command("git", "commit", "-q", "-m", "frozen", cwd=source)
    pinned = command("git", "rev-parse", "HEAD", cwd=source)
    command("git", "clone", "-q", "--bare", str(source), str(remote))

    materializer.materialize(str(remote), pinned, checkout)
    assert command("git", "rev-parse", "HEAD", cwd=checkout) == pinned

    # Move the named branch after the first materialization.
    (source / "authority.txt").write_text("moved\n")
    command("git", "commit", "-q", "-am", "moved", cwd=source)
    moved = command("git", "rev-parse", "HEAD", cwd=source)
    command("git", "push", "-q", str(remote), "mjlab_frictionloss", cwd=source)
    assert moved != pinned

    materializer.materialize(str(remote), pinned, checkout)
    assert command("git", "rev-parse", "HEAD", cwd=checkout) == pinned
    assert command("git", "status", "--porcelain", cwd=checkout) == ""
    assert (checkout / "authority.txt").read_text() == "frozen\n"

print("BAM authority materializer verified: moved branch cannot repin exact commit")
