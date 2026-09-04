# Executor Session 035 - M5 evaluator-bundle determinism

**Date:** 2026-09-03

## Baseline And Authority

- Reviewer-accepted base: `2f780f2`.
- Slice-opening commit: `1669aae`.
- Immutable third-pilot receipt manifest:
  `4bac1d24a78f3940c56dba0785a5721755cd869e3fdc0a78d39ec4ce7797deee`.
- Slice opened for local diagnostic/correction only. No paid compute, training,
  receipt mutation, or fourth-pilot authority is permitted.

## Failing-First Diagnosis

- The retained A100 log proves only that the five-file maps differed at
  `test_evaluator_bundle.py:69`. Its temporary first/second bundles and
  individual hashes were discarded, so the historical differing filename and
  bytes remain unavailable and are not reconstructed here.
- Before the producer change, ten repeated full bundles under mocked
  Linux/x86-64 metadata produced one hash per file locally. Captured evaluator
  rows and raw rendered RGB frames were exactly equal across runs.
- Twelve isolated writes of identical captured inputs produced one Parquet hash
  and one MP4 hash. This rules out ordinary output-path, stable-JSON, PyArrow,
  and single-process single-thread encoder variation in the local reproduction;
  it does not upgrade the missing A100 attribution.
- Failing-first coverage then required the MP4 producer to request FFmpeg
  bit-exact muxer and codec behavior plus explicit x264 frame/lookahead
  threading. It failed because `-fflags +bitexact` was absent.
- A controlled identical-frame comparison between the old and corrected
  encoder settings changed only encoded/container bytes (1,912 versus 1,876
  bytes); all eight decoded frames and reported video metadata remained equal.
  FFmpeg's documented `bitexact` contract is specifically to omit
  platform-, build-, and time-dependent data for regression checks.
- Classification: the exact discarded A100 artifact remains **unattributed
  same-host byte nondeterminism**. The smallest concrete producer defect found
  is an unbounded FFmpeg codec/muxer reproducibility contract, not Parquet
  metadata or stable JSON. No claim is made that absent A100 bytes proved a
  specific filename.

## Implementation

- Added `evaluator/bundle_diagnostics.py`. Exact equality remains the gate,
  but failures now report every differing filename, both SHA-256 values and
  sizes, first differing byte offset/windows, JSON field paths, Parquet
  table/schema/metadata equality, decoded MP4 metadata/frame differences and
  first pixel delta, and changed attestation dependencies.
- `evaluator/bundle.py` now asks both the FFmpeg muxer and video codec for
  bit-exact output and binds x264 to one frame thread, one lookahead thread, no
  sliced threads, and zero sync lookahead. Existing metadata stripping and
  synthetic latency/offscreen-sample controls remain.
- The video stays libx264/yuv420p at 320x240, 25 fps and 40 decoded frames.
  Runtime provenance, raw five-file hashes, exact attestation chain, Parquet
  rows, evaluator thresholds, and the model/task/interface/control freezes are
  unchanged.
- Regression coverage now creates six complete bundles in distinct directories
  under Linux-style metadata and deliberately different measured inference
  latencies; captures and compares raw rows and RGB frames; repeats isolated
  Parquet and MP4 producers six times; and injects JSON, Parquet-encoding,
  container-only, rendered-frame, and attestation differences to prove the
  diagnostics distinguish each class while failing closed.

## Validation

- Failing-first `tests/test_evaluator_bundle.py`: failed because
  `-fflags` was absent before the producer correction.
- Corrected focused bundle test: pass; six complete same-host bundles are
  byte-identical, isolated Parquet/MP4 producers are stable, controlled
  diagnostics pass, and 160 rows / 40 decoded frames remain.
- Eight additional complete bundles generated in separate Python processes:
  one hash per each of the five files.
- Focused authority tests with clean BAM `62bd8ce`, official walking checkout
  `109e06d`, locked official MJLab Python, and `GS_ENABLE_ZEROCOPY=1`:
  evaluator bundle, cross-platform determinism, evaluator core, and model
  reconciliation all pass.
- Full authority-enabled `.venv-apple/bin/python tests/run_all.py`: pass with
  no failures, including the revised bundle gate and both environment smokes.
- Python compilation, M5 immutable contract/negative probes,
  `scripts/check_branch_hygiene.sh 2f780f2`, workflow audit, and diff checks:
  pass.
- `git diff --quiet 2f780f2 -- receipts`: pass. All eight tracked receipt
  manifests and 68 immutable receipt logs revalidated; no accepted receipt byte
  changed.
- No Brev create/start/exec/copy/stop/delete, training, checkpoint, export, or
  fourth-pilot action occurred.

## Evidence Boundary

Local same-host deterministic producer compatibility only. No CUDA smoke, M5,
task, policy, candidate, held-out, transfer, or physical success is claimed.

## Step-9 Flags For Reviewer

- Confirm exact differing-file diagnostics remain fail-closed.
- Confirm the fix is limited to an evidenced producer boundary and preserves
  raw provenance, five-file completeness, decoded semantics, and all freezes.
- Preserve the distinction between the identified unbounded FFmpeg bit-exact
  contract and the unavailable historical A100 per-file attribution.
- Re-run stress/focused/full authority checks and accepted receipt manifests.
- Do not authorize paid compute or a fourth pilot from this local result.
