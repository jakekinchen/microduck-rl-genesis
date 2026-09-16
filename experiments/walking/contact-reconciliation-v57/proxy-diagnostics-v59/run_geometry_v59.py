"""Execute frozen local geometry steps with process deadlines and one attempt."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[4]


def interrupt(signum, frame):
    raise InterruptedError(f'signal {signum}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('plan', type=Path)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    out = args.plan.resolve().parent
    for name, digest in plan['input_sha256'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    with (out / plan['attempt_marker']).open('x') as stream:
        json.dump({'pid': os.getpid(), 'start_unix': time.time(),
                   'plan_sha256': hashlib.sha256(args.plan.read_bytes()).hexdigest()}, stream)
    signal.signal(signal.SIGINT, interrupt)
    signal.signal(signal.SIGTERM, interrupt)
    rows = []
    for step in plan['steps']:
        start = time.monotonic()
        row = {'id': step['id'], 'timed_out': False}
        child = None
        try:
            with (out / step['log']).open('wb') as stream:
                mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT, signal.SIGTERM})
                try:
                    child = subprocess.Popen([sys.executable, str(ROOT / step['script']), *step['args']],
                                             stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
                finally:
                    signal.pthread_sigmask(signal.SIG_SETMASK, mask)
                try:
                    child.wait(timeout=step['wall_seconds'])
                except subprocess.TimeoutExpired:
                    row['timed_out'] = True
        except BaseException as error:
            row['interruption'] = repr(error)
            raise
        finally:
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            try:
                if child is not None and child.poll() is None:
                    os.killpg(child.pid, signal.SIGTERM)
                    try:
                        child.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        os.killpg(child.pid, signal.SIGKILL)
                        child.wait()
            finally:
                signal.signal(signal.SIGINT, interrupt)
                signal.signal(signal.SIGTERM, interrupt)
            row.update(exit_code=child.returncode if child else None, elapsed_seconds=time.monotonic()-start)
            rows.append(row)
            (out / plan['process_report']).write_text(json.dumps(rows, indent=2) + '\n')
        print(json.dumps(row), flush=True)


if __name__ == '__main__':
    main()
