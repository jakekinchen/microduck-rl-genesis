#!/usr/bin/env python3
"""Materialize the exact BAM revision frozen by the repository contract."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "microduck_contract/actuator/bam-m6-xl330-v1.lock.json"
FIXTURE_PATH = (
    ROOT / "microduck_contract/actuator/fixtures/bam-m6-xl330-v1-open-loop.json"
)


def git(*args: str, cwd: Path | None = None) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def locked_authority() -> tuple[str, str]:
    lock = json.loads(LOCK_PATH.read_text())
    fixture = json.loads(FIXTURE_PATH.read_text())
    commit = lock["golden_vectors"]["authority_commit"]
    authority = fixture["authority"]
    if authority["commit"] != commit:
        raise RuntimeError("BAM lock and frozen fixture disagree on authority commit")
    return authority["repository_url"], commit


def materialize(repository_url: str, authority_commit: str, destination: Path) -> Path:
    destination = destination.resolve()
    if destination.exists():
        if not (destination / ".git").exists():
            raise RuntimeError(f"destination exists but is not a git checkout: {destination}")
        if git("status", "--porcelain", "--untracked-files=all", cwd=destination):
            raise RuntimeError(f"refusing dirty BAM authority checkout: {destination}")
        origin = git("remote", "get-url", "origin", cwd=destination)
        if origin != repository_url:
            raise RuntimeError(
                f"BAM authority origin mismatch: expected {repository_url}, got {origin}"
            )
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        git("clone", "--filter=blob:none", "--no-checkout", repository_url, str(destination))

    # Fetch the immutable object directly. No branch or tag participates in
    # selection, so a moved mjlab_frictionloss head cannot silently repin it.
    git("fetch", "--no-tags", "origin", authority_commit, cwd=destination)
    git("checkout", "--detach", authority_commit, cwd=destination)

    head = git("rev-parse", "HEAD^{commit}", cwd=destination)
    if head != authority_commit:
        raise RuntimeError(f"BAM authority mismatch: expected {authority_commit}, got {head}")
    if git("status", "--porcelain", "--untracked-files=all", cwd=destination):
        raise RuntimeError(f"materialized BAM checkout is dirty: {destination}")
    return destination


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    repository_url, authority_commit = locked_authority()
    path = materialize(repository_url, authority_commit, args.destination)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
