"""Read process identity; never signal, attach to, or import a training process."""
from datetime import datetime, timezone
from pathlib import Path
import os
import re
import shlex
import shutil
import subprocess

ENTRYPOINTS = {"train_laser.py", "train_laser_robust.py", "train_laser_turn.py", "train_laser_gait.py",
               "train.py", "train_backflip.py", "train_first_party.py",
               "train_first_party_development.py"}


def parse_processes(text):
    result = []
    for line in text.splitlines():
        columns = line.strip().split(None, 3)
        if len(columns) != 4 or not columns[0].isdigit() or not columns[1].isdigit():
            continue
        try:
            argv = shlex.split(columns[3])
        except ValueError:
            continue
        if not argv or not re.match(r"^python(?:\d+(?:\.\d+)*)?$", Path(argv[0]).name):
            continue
        script = next((a for a in argv[1:] if Path(a).name in ENTRYPOINTS), None)
        if script:
            result.append({"pid": int(columns[0]), "ppid": int(columns[1]), "elapsed": columns[2],
                           "entrypoint": Path(script).name})
    return result


def inspect(root: Path):
    root = root.resolve(strict=True)
    result = {"schema_version": "microduck.ops.activity.v1", "root": str(root),
              "generated_at": datetime.now(timezone.utc).isoformat(), "read_only": True,
              "status": "unknown", "processes": [],
              "boundary": "Instantaneous advisory inventory of known Python training entrypoints. Absence is not proof of idleness; unrecognized launchers and remote jobs are outside coverage. No lock, admission, process control or training status mutation."}
    try:
        completed = subprocess.run(["ps", "-axo", "pid=,ppid=,etime=,args="],
                                   text=True, capture_output=True, timeout=5, check=True)
        candidates = parse_processes(completed.stdout)
        if len(candidates) > 32:
            raise ValueError("more than 32 training candidates; ownership check is incomplete")
        lsof = shutil.which("lsof") or ("/usr/sbin/lsof" if Path("/usr/sbin/lsof").exists() else None)
        for item in candidates:
            if item["pid"] == os.getpid():
                continue
            cwd = None
            if lsof:
                try:
                    probe = subprocess.run([lsof, "-a", "-p", str(item["pid"]), "-d", "cwd", "-Fn"],
                                           text=True, capture_output=True, timeout=2, check=False)
                    cwd = next((s[1:] for s in probe.stdout.splitlines() if s.startswith("n")), None)
                except (OSError, subprocess.SubprocessError):
                    pass
            same_root = cwd and (Path(cwd).resolve() == root or Path(cwd).resolve().is_relative_to(root))
            item["ownership"] = ("cwd_matches_repository" if same_root else
                                 "different_directory" if cwd else "unknown")
            result["processes"].append(item)
        result["status"] = "busy" if result["processes"] else "no_known_training_process"
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        result["error"] = str(error)
    return result
