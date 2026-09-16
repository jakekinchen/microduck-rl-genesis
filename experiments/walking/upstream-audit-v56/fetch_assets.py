#!/usr/bin/env python3
"""Restore only missing, hash-locked upstream CAD assets; no package install."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import urllib.request

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def main():
    files = json.loads((HERE / "sources.lock.json").read_text())["files"]
    prefix = HERE.relative_to(ROOT).as_posix() + "/sources/src/mjlab_microduck/robot/microduck/assets/"
    selected = [(path, record) for path, record in files.items() if path.startswith(prefix)]

    def fetch(item):
        rel, record = item
        path = ROOT / rel
        if path.is_symlink():
            raise ValueError(f"unexpected symlink: {path}")
        data = path.read_bytes() if path.exists() else urllib.request.urlopen(record["upstream_url"], timeout=60).read()
        if hashlib.sha256(data).hexdigest() != record["sha256"]:
            raise ValueError(f"source hash mismatch: {rel}")
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as output:
                output.write(data)
        return len(data)

    with ThreadPoolExecutor(max_workers=4) as pool:
        total = sum(pool.map(fetch, selected))
    print(f"Verified {len(selected)} CAD assets, {total} bytes; no physics or package installation.")


if __name__ == "__main__":
    main()
