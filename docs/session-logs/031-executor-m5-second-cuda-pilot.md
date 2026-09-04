# Executor Session 031 - M5 second CUDA pilot

**Date:** 2026-09-03

## Authority And Preflight

- Manager authorization 007 was committed at `f1864c3`; execution brief/status
  was committed at `fd0a88e` before provisioning.
- Proposal SHA-256 `f020df3f1cfb29b160ec86765a06e184a696af940fe62d690fda371653aa536e`,
  runtime `c9f64efb52d7ae0c220ff0f03c9b207af11a792251bd1eb69ef9357e1658f46d`,
  lock `e813cbdaec942ad2de23d70532b664286bed4f12965f5b933dd8c9ff342b749f`,
  and harness `86e964348ec5bb64f22b64bdee6b3eb446923b2e35f2b8e5f54390eda08798ef`
  matched immediately before execution.
- Authenticated inventory was empty. The fresh catalog row exactly matched
  `hyperstack_A100_80G`, shadeform/hyperstack, x86-64, one A100 80 GB,
  non-stoppable/non-rebootable, `$1.62/hour`.
- Created only `microduck-m5-pilot2-20260903` (`7owxqf4pg`) with the immutable
  linux/amd64 CUDA image. It became healthy/SSH-ready after its initial
  300-second CLI wait timed out; no upload occurred while unhealthy.
- Local and remote input SHA-256 values matched: Genesis bundle
  `e00251b0...94c2`, official walking `6d22533c...ed7a`, official backflip
  `9d6def20...638a`, harness `86e96434...98ef`.

## Execution

- Receipt root: `20260904T012843Z-7owxqf4pg`; reviewed contract commit
  `764d923`, training source `93cd5f2`, official walking `109e06d`, official
  backflip `8bde27e`, BAM `62bd8ce`.
- A100/driver/CUDA preflight passed: NVIDIA A100 80 GB PCIe, driver 570.195.03,
  CUDA 12.8, Python 3.12.3, Torch 2.9.1+cu128 with CUDA visible, Genesis 1.3.3,
  MuJoCo 3.12.0, RSL-RL 5.4.2, EGL/headless selected.
- The corrected strict cu128 lock installed all 126 packages. The official lane
  synced MJLab 1.3.0, MuJoCo 3.10.0, Warp 1.12.0, and MuJoCo Warp 3.8.1.
- The full suite failed `test_model_reconciliation.py`,
  `test_evaluator_core.py`, and `test_evaluator_bundle.py` on frozen manifest or
  byte-determinism assertions. All later smoke-training commands were skipped.
- After the first finalization, Brev exec automatically replayed the command on
  reconnect. The duplicate was interrupted at `runtime-versions`; no suite or
  training started on the replay and no relevant process survived. Manager log
  008 reconciles the overwritten terminal/cost metadata.

## Receipt And Independent Verification

- The final remote `SHA256SUMS` passed all 23 entries. The complete 24-file
  receipt was recovered locally.
- Remote manifest, recovered manifest, and an independent byte-sorted local
  regeneration matched exactly at
  `90cbb02447d55594f71a1b35e1d00918f2f809acf3a182419d838d85186b3078`.
- Final recorded status is terminal negative, exit 141 at `runtime-versions`,
  reflecting the interrupted replay. The retained `full-suite.log` contains the
  first invocation's decisive three failures. `artifacts/` is empty.

## Cost And Teardown

- Conservative pre-create-to-empty interval: `2026-09-04T01:16:28Z` through
  `2026-09-04T01:41:43Z`, 1,515 seconds / `$0.681750` at `$1.62/hour`.
- The internal `$0.006750` receipt cost covers only the replay after its reset
  `START_EPOCH`; it is not the billing bound and remains unedited evidence.
- Deletion was requested by name then retried by exact ID after a transient
  control-plane state regression. Final authenticated inventory is empty.

## Evidence Boundary

Terminal-negative CUDA pipeline evidence. It proves that the corrected
Genesis 1.3.3 / Torch cu128 runtime reaches and runs the full A100 suite; it
does not prove a successful pilot, task success, candidate or held-out results,
policy acceptance, publication, transfer, or physical authority.

## Step-9 Flags For Reviewer

- Independently verify the full recovered manifest and accepted pilot-028
  receipt immutability.
- Distinguish the first invocation's suite failure from the Brev wrapper's
  duplicate replay and overwritten terminal/cost metadata.
- Audit all three frozen suite failures and confirm no training/artifacts exist.
- Recompute the create-to-empty cost bound and verify final empty inventory.
- Do not authorize a third pilot or the full CUDA matrix from this result.
