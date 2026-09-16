"""Single-attempt, process-bounded coordinator for static V59 cases."""
from pathlib import Path
import hashlib
import json
import os
import signal
import subprocess
import sys
import time

P = Path(__file__).resolve().parent


def interrupt(signum, frame):
    raise InterruptedError(f'signal {signum}')


def main():
    signal.signal(signal.SIGINT, interrupt)
    signal.signal(signal.SIGTERM, interrupt)
    protocol = json.loads((P / 'protocol.json').read_text())
    for name, digest in json.loads((P / 'implementation.lock.json').read_text()).items():
        assert hashlib.sha256((P / name).read_bytes()).hexdigest() == digest, name
    with (P / 'attempt-started.json').open('x') as file:
        json.dump({'pid': os.getpid(), 'started_unix': time.time()}, file)
    results = []
    for case in protocol['cases']:
        start = time.monotonic()
        child = None
        row = {'case': case['id'], 'timed_out': False}
        try:
            with (P / f'{case["id"]}.log').open('wb') as log:
                old = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT, signal.SIGTERM})
                try:
                    child = subprocess.Popen([sys.executable, str(P / 'probe_compiler_v59.py'), case['id']],
                                             stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                finally:
                    signal.pthread_sigmask(signal.SIG_SETMASK, old)
                try:
                    child.wait(timeout=case['wall_seconds'])
                except subprocess.TimeoutExpired:
                    row['timed_out'] = True
        except BaseException as error:
            row['error'] = repr(error)
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
            results.append(row)
            (P / 'processes.json').write_text(json.dumps(results, indent=2) + '\n')
        print(json.dumps(row), flush=True)


if __name__ == '__main__':
    main()
