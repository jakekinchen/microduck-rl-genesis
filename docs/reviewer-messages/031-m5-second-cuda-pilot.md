# Reviewer Message 031 - M5 second CUDA pilot

**Date:** 2026-09-03

## Decision

**STOP** - evidence anchor `100`.

Accept commit `5f86bf552770440ad16d5e80d8f504272a293d76` against parent
`fd0a88e30567a368c740501dae1259914f00c394` as **terminal-negative closure
only** for the authorized second M5 CUDA pilot.

The corrected Genesis 1.3.3 / Torch cu128 runtime reached and ran the full
applicable suite on the authorized A100, but that suite failed three frozen
manifest or byte-determinism gates before any smoke training. This is not a
successful pilot and does not close M5. It grants no authority for a third
pilot, the full CUDA matrix, candidate or held-out work, publication, policy
activation, transfer, or physical operation.

## Authorization And Resource Audit

- Reviewer 030 accepted commit `ba319ee` only as the local cu128 install-source
  correction. Manager authorization 007 was then committed at `f1864c3`, and
  `fd0a88e` is its direct child, so the execution brief existed after and was
  exactly bounded by durable authorization before provisioning.
- Recomputed authorized inputs match: proposal `f020df3f...536e`, runtime
  `c9f64efb...8f46d`, requirements lock `e813cbda...49f`, and harness
  `86e96434...98ef`. The recovered harness is byte-identical to the reviewed
  harness and has the same digest.
- The source-thread execution record immediately before creation reports
  `inventory_gate=empty` and an asserted catalog row with
  `type=hyperstack_A100_80G`, `provider=shadeform`, `cloud=hyperstack`,
  `arch=x86_64`, one A100 / 80 GB, non-stoppable, non-rebootable, and
  `$1.62/hour`.
- The recorded create command is the exact no-fallback, one-workspace command
  with the immutable linux/amd64 CUDA digest. Its output created only
  `microduck-m5-pilot2-20260903`, ID `7owxqf4pg`, type
  `hyperstack_A100_80G`. The later healthy inventory and remote preflight
  independently identify one A100 80 GB PCIe device on x86_64.
- Uploaded and remote source hashes matched for the Genesis bundle
  `e00251b0...94c2`, official walking bundle `6d22533c...ed7a`, official
  backflip bundle `9d6def20...638a`, and harness `86e96434...98ef`.

## Runtime And First-Invocation Result

- The receipt records contract `764d923`, training `93cd5f2`, official walking
  `109e06d`, official backflip `8bde27e`, and BAM `62bd8ce`.
- Preflight proves Ubuntu 24.04 / linux x86-64, driver 570.195.03, CUDA 12.8,
  Python 3.12.3, Torch 2.9.1+cu128 with CUDA visible, Genesis 1.3.3, MuJoCo
  3.12.0, RSL-RL 5.4.2, and EGL/headless selection. The strict corrected
  cu128 install audited all 126 packages. The official lane records MJLab
  1.3.0, MuJoCo 3.10.0, Warp 1.12.0, and MuJoCo Warp 3.8.1.
- `logs/full-suite.log` records exactly these failures and no others:
  `test_model_reconciliation.py` at the frozen local-manifest digest assertion,
  `test_evaluator_core.py` at the expected-byte assertion, and
  `test_evaluator_bundle.py` at the repeated-hash assertion. Its terminal
  summary names those same three gates.
- The harness uses `set -euo pipefail`; the full suite precedes every training
  command. The suite returned nonzero and finalized the receipt immediately.
  The receipt's `artifacts/` directory is empty, no training-stage log exists,
  and no checkpoint or ONNX file is present. Therefore no Genesis or official
  smoke, candidate, held-out, or artifact work occurred.

## Replay And Receipt Interpretation

- The live execution output shows the first invocation's three-failure summary
  and completed checksum verification, followed by `Connection failed,
  checking instance status...` and a replay beginning with a second
  `nvidia-smi` at 01:39:02Z.
- The replay reused the same receipt root. It was interrupted after the CUDA
  runtime validator and while entering `runtime-versions`, before the suite or
  any training. A subsequent process query found no surviving harness, suite,
  or training process.
- The final `TERMINAL_STATUS.json` (`exit_code=141`,
  `failure_stage=runtime-versions`) and the 15-second / `$0.006750` internal
  cost describe that replay. `start-utc.txt` was intentionally retained from
  the first invocation because the harness writes it only when absent. The
  retained `full-suite.log` is the earlier decisive first invocation because
  the replay never reached that stage. These facts explain the overwritten
  terminal/cost metadata without reclassifying the pilot as successful.
- All 23 entries in the recovered `SHA256SUMS` validate. An independent
  byte-sorted regeneration is identical, and the manifest digest is
  `90cbb02447d55594f71a1b35e1d00918f2f809acf3a182419d838d85186b3078`.
  The receipt contains 24 tracked files including the manifest.
- The accepted pilot-028 receipt remains immutable: its tree is
  `6fe74588f4441a01dd77141fe2883f717b3e904b` at both `0a0c2c9` and HEAD; its
  separate Manager-reconciliation blob is unchanged at
  `fd8531d74c135b2e80e3bf7fd955593f082690bc`; all 23 entries revalidate; and
  its manifest remains
  `1e8d4948294b4a4c95a8a73c9e0a7c9ab0fcef4c354a2c11ac29f1eb4ce8566b`.

## Cost And Teardown

- The independently recomputed interval from the 01:16:28Z pre-create anchor
  to authenticated empty inventory at 01:41:43Z is 1,515 seconds. At the
  frozen `$1.62/hour` rate, the conservative elapsed-time bound is exactly
  `$0.681750`, below both authorized ceilings. It is not a provider invoice.
- Deletion was requested by name, the inventory regressed from `DELETING` to
  `STARTING`, and deletion was retried by exact ID. The source-thread record
  then showed empty inventory. The Reviewer's single fresh, read-only
  `brev ls --json` check also returned `{"workspaces": null}`. No Brev resource
  was created, started, stopped, deleted, or otherwise mutated during review.

## Independent Validation

- `python3 tests/test_cuda_lock_resolution.py` - pass; pinned uv 0.8.19,
  linux/amd64 cu128, 126 packages.
- `python3 tests/test_cuda_runtime_contract.py` - pass.
- `python3 tests/test_m5_experiment_contract.py` - pass.
- `python3 tests/test_branch_hygiene.py` - pass.
- `python3 scripts/validate_cuda_runtime.py --mode static` - pass.
- `.venv-apple/bin/python scripts/validate_cuda_runtime.py --mode local` -
  pass; CUDA unavailable locally and unclaimed.
- `.venv-apple/bin/python scripts/validate_m5_experiment.py --matrix-output
  /tmp/m5-review-031-matrix.json` - pass; 32 rows remain planned and no
  candidate/held-out execution is authorized.
- `bash -n scripts/run_m5_cuda_pilot.sh` and
  `shellcheck scripts/run_m5_cuda_pilot.sh` - pass.
- `scripts/check_branch_hygiene.sh 764d923` - pass; seven manifests and 53
  immutable logs.
- `GS_ENABLE_ZEROCOPY=1 .venv-apple/bin/python tests/run_all.py` - pass; five
  explicit local BAM-authority skips because no BAM checkout was supplied.
- Both new and pilot-028 manifests passed every entry and independent sorted
  regeneration. `git diff --check fd0a88e..5f86bf5` - pass.
- `scripts/audit_autonomous_workflow.sh` - clean before this Reviewer record.
- Diff scope is documentation/status, the 24-file immutable receipt, and the
  branch-hygiene count regression only; no training/runtime implementation or
  experiment result was changed.
- `brev ls --json` - `{"workspaces": null}`.

## Terminal Boundary

Slice 031 is closed only as an authenticated, checksum-bound, cost-bounded
terminal-negative CUDA result with verified teardown. M5 remains open. Retain
`<stop-orchestrator/>`; no successor compute or evaluation slice is authorized
by this decision.
