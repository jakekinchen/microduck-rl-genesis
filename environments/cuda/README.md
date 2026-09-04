# Linux CUDA environment

This lane is the immutable linux/amd64 counterpart to the Apple lock. It fixes
the terminal pilot-028 mismatch by pairing frozen training source
`93cd5f261200acb5176f12c417c31c1d877be41a` with Genesis World 1.3.3, whose
tagged wheel exposes the `RigidSolver.dyn_state` surface consumed by the source.

Regenerate only with the command embedded in `runtime-v1.json`, then update the
lock digest and pass `scripts/validate_cuda_runtime.py`. The lock targets Python
3.12, glibc 2.39-compatible x86-64 wheels, and Torch cu128. Installation in an
evidence run must use `uv pip install --require-hashes -r requirements.lock`.

To reproduce the precise API boundary after downloading both named wheels, run
`scripts/probe_genesis_runtime_wheels.py --wheel-dir <download-directory>`.
The probe verifies whole-wheel and embedded `rigid_solver.py` digests and proves
that 1.2.2 lacks, while 1.3.3 contains, the required `dyn_state` assignment.

The runtime contract is local refreeze evidence only. It does not authorize a
workspace, training, candidate execution, held-out realization, or GPU claim.
