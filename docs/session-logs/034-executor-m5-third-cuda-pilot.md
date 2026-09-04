# Executor Session 034 - M5 third CUDA pilot

**Date:** 2026-09-03

## Authority And Preflight

- Manager authorization 009 was committed at `d29c8dc` before provisioning.
- Reviewer 033 accepts implementation `d741e60` at the local deterministic
  evidence class; the pilot contract is bound to `2376821`.
- The proposal remains historically `compute_authorized=false`; this one
  pilot's authority exists only in Manager authorization 009.
- Immediately before creation, the repository was clean; all four bound hashes
  matched; authenticated inventory was empty; and the fresh catalog row exactly
  matched `hyperstack_A100_80G`, shadeform/hyperstack, x86-64, one A100 80 GB,
  non-stoppable/non-rebootable, `$1.62/hour`.
- Created only `microduck-m5-pilot3-20260904` (`4qe7ph6p7`) with the immutable
  linux/amd64 CUDA image. Upload and execution waited until inventory reported
  `RUNNING`, `COMPLETED`, `READY`, and `HEALTHY`.
- Local and remote input SHA-256 values matched: Genesis bundle
  `098421bf...2bbae`, official walking `09acf542...2f36`, official backflip
  `6d8b39ca...6b11`, and harness `86e96434...98ef`.

## Execution

- Receipt root: `20260904T030457Z-4qe7ph6p7`; reviewed contract commit
  `2376821`, training source `93cd5f2`, official walking `109e06d`, official
  backflip `8bde27e`, and BAM `62bd8ce`.
- An atomic run-ID guard created exactly one `once` directory and launched one
  detached harness process under `timeout 4800`; there was no reconnect replay.
- Runtime preflight passed: NVIDIA A100 80 GB PCIe, driver 570.195.03, CUDA
  12.8, Python/Torch 2.9.1+cu128 with CUDA visible, Genesis 1.3.3, MuJoCo
  3.12.0, RSL-RL 5.4.2, EGL/headless selected. The official lane reported
  MJLab 1.3.0, MuJoCo 3.10.0, Warp 1.12.0, and MuJoCo Warp 3.8.1.
- The full suite retained one failure: `test_evaluator_bundle.py` line 69,
  where the five-file hashes from two same-host evaluator-bundle generations
  differed. `test_model_reconciliation.py`, cross-platform determinism, and the
  rest of the completed suite passed.
- The harness exited 1 at `full-suite`. All four 64-environment x five-iteration
  smoke commands and every normalized ONNX export were skipped; `artifacts/`
  is empty.

## Receipt And Independent Verification

- Terminal status is `terminal_negative`, exit 1, failure stage `full-suite`,
  `pilot_smoke_pipeline_completed=false`.
- The final remote `SHA256SUMS` passed all 23 entries. The complete 24-file
  receipt was recovered locally.
- Remote manifest, recovered manifest, and an independently regenerated
  byte-sorted local manifest matched exactly at
  `4bac1d24a78f3940c56dba0785a5721755cd869e3fdc0a78d39ec4ce7797deee`.

## Cost And Teardown

- Harness interval: `2026-09-04T03:05:06Z` through `03:15:11Z`, 605 seconds;
  its internal estimate is `$0.272250` and explicitly requires Manager
  reconciliation.
- Conservative pre-create-to-empty interval: `2026-09-04T02:52:47Z` through
  `03:19:02Z`, 1,575 seconds / `$0.708750` at `$1.62/hour`.
- Deletion was issued by exact ID after verified recovery. The transient
  control-plane entry cleared without a second delete request; three successive
  authenticated polls and a closing audit reported empty inventory.

## Evidence Boundary

At most third-pilot CUDA pipeline compatibility. A passed smoke is not M5,
task, policy, candidate, held-out, transfer, or physical success.

This terminal-negative receipt proves that the corrected runtime reaches and
runs the complete A100 suite and narrows the remaining blocker to same-host
evaluator-bundle byte determinism on A100. It is not a successful smoke pilot.

## Step-9 Flags For Reviewer

- Verify the fresh Manager authority, exact bound hashes, and pre-create gates.
- Verify the harness ran no more than once for the bound receipt ID.
- Independently check the complete recovered receipt and manifest equality.
- Audit the single `test_evaluator_bundle.py` same-host hash mismatch and
  confirm no smoke command or artifact ran after the failed suite gate.
- Recompute the conservative create-to-empty cost and confirm final inventory.
- Keep all M5/task/policy/transfer/physical claims outside this smoke boundary.
