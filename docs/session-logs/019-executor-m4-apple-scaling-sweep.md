# Executor log 019 - M4 Apple scaling sweep

**Date:** 2026-09-03

**Role:** Executor

**Brief:** `docs/briefs/019-m4-apple-scaling-sweep.md`

## Execution

- A 64-environment preflight against `05c05e3` exposed an RSL-RL 5.4 API
  mismatch in the learner-finiteness check. It produced no accepted row.
- Commit `aa4c567` corrected the check to cover the installed separate actor
  and critic modules and added a deterministic regression test.
- Ran 64, 128, 256, and 512 sequentially in fresh processes from the clean
  `aa4c567` source state.
- The preregistered 512 gate passed: finite state, nominal thermal warning
  state, and 97.87% peak-RSS-proxy headroom. Ran 1024 in a fresh process.
- All five rows completed and were assembled into
  `receipts/apple-scaling/20260903T202404Z-aa4c567/`.

## Result

Every row reports finite observations and learner parameters, nominal thermal
warning state, and at least 97.75% RSS-proxy headroom. Total PPO iteration time
ranged from 2.337 s at 64 to 4.271 s at 1024. Total-iteration-derived throughput
ranged from 39,441 to 345,246 samples/min and was highest at 1024.

## Verification

- The sweep assembler validated all five rows, their order, common clean source
  commit, package/machine provenance, and proof boundary.
- `shasum -a 256 -c SHA256SUMS` passed for all raw JSON, raw process logs, and
  `sweep.json`.
- Focused schema/finiteness/default tests pass in `.venv-apple`.

## Evidence boundary

Short public development workload only. No final candidate, held-out seed,
task-success classification, transfer, publication, policy activation, paid
compute, or hardware action occurred. The sweep alone does not select the
everyday default; sustained thermal/stability evidence remains required.
