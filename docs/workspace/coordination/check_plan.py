"""Check accepted workcell plan bytes; never inspect models or run a simulator."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat

ACCEPTED_SHA256 = "0ec9b9e0bee51bd78680d132ba65b8cd1edc113cd21fa0d82c28a1f5865f9a31"
LIMIT = 1024 * 1024


def digest(path: Path) -> str:
    if not stat.S_ISREG(path.stat(follow_symlinks=False).st_mode):
        raise ValueError("Plan must be a regular file")
    descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    with os.fdopen(descriptor, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError("Plan must be a regular file")
        data = stream.read(LIMIT + 1)
    if len(data) > LIMIT:
        raise ValueError("Plan exceeds the inspection limit")
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sim2claw-root", type=Path)
    args = parser.parse_args()
    result = {"schema_version": "microduck.workcell_plan_mirror_check.v1",
              "valid": False, "scope": "accepted_plan_bytes_and_optional_mirror_only",
              "accepted_sha256": ACCEPTED_SHA256, "peer_mirror_verified": False,
              "source_hashes_checked": False, "execution_authorized": False,
              "simulation_executed": False, "training_authorized": False}
    try:
        local = Path(__file__).resolve().with_name("arm_duck_workcell.v1.json")
        result["local_sha256"] = digest(local)
        if result["local_sha256"] != ACCEPTED_SHA256:
            raise ValueError("Local plan differs from the accepted shared version")
        if args.sim2claw_root is not None:
            peer = args.sim2claw_root.expanduser().resolve()
            for part in ("configs", "operations", "arm_duck_workcell.v1.json"):
                peer /= part
                if peer.is_symlink():
                    raise ValueError("Peer mirror cannot use a symlink path")
            result["peer_sha256"] = digest(peer)
            if result["peer_sha256"] != ACCEPTED_SHA256:
                raise ValueError("Peer plan differs from the accepted shared version")
            result["peer_mirror_verified"] = True
        result["valid"] = True
    except (OSError, ValueError) as error:
        result["error"] = str(error)
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
