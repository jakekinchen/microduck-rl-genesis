# Manager Log 008 - M5 second-pilot reconciliation

**Date:** 2026-09-03

## Terminal Classification

The authorized second pilot is **terminal negative**. The corrected CUDA
runtime and exact Genesis 1.3.3 dependency path passed on an A100, but the full
authority-supplied suite failed three deterministic gates before any smoke
training. This result is not pilot success, task success, candidate admission,
held-out evidence, policy acceptance, transfer, or physical authority.

## Resource And Billing Reconciliation

- Final pre-create inventory was empty and the exact catalog row matched the
  authorized `hyperstack_A100_80G` constraints at `$1.62/hour`.
- Exactly one workspace was created:
  `microduck-m5-pilot2-20260903`, ID `7owxqf4pg`.
- Conservative billing anchor: `2026-09-04T01:16:28Z` immediately before
  creation. Authenticated empty inventory was observed at
  `2026-09-04T01:41:43Z` after deletion.
- The 1,515-second create-to-empty upper bound is `$0.681750` at the frozen
  rate, below the two-hour / `$3.24` ceiling. This is elapsed-time arithmetic,
  not a provider invoice.
- Deletion was requested by name at `2026-09-04T01:40:39Z`; after a transient
  `DELETING` to `STARTING` control-plane regression, deletion was retried by the
  exact ID. Final `brev ls --json` returned `{"workspaces": null}`.

## Brev Exec Replay Anomaly

After the first harness invocation finished the failing full suite and finalized
its receipt, the Brev exec wrapper reported a connection failure and replayed
the same remote command automatically. The duplicate invocation reused the same
receipt root and reran idempotent setup/preflight stages. It was interrupted at
`runtime-versions`, before the suite or any training, and no harness, suite, or
training process survived.

The second finalizer therefore replaced `TERMINAL_STATUS.json`, `cost.json`,
`end-utc.txt`, several stage logs, and `SHA256SUMS`. The final remote state is
self-consistent and fully checksummed, but its 15-second `$0.006750` internal
cost record describes only the replay and is not the billing envelope. The
create-to-empty bound above is authoritative for cost control. The retained
`full-suite.log` is from the first invocation because the replay stopped before
that stage.

## Recovered Receipt

- Path: `receipts/m5/pilot/20260904T012843Z-7owxqf4pg/`.
- 24 files, with 23 non-manifest entries.
- Remote, recovered, and independently regenerated manifests were byte-identical
  at SHA-256
  `90cbb02447d55594f71a1b35e1d00918f2f809acf3a182419d838d85186b3078`.
- The final terminal record is `exit_code=141`,
  `failure_stage=runtime-versions`, and `pilot_smoke_pipeline_completed=false`
  because it records the interrupted wrapper replay. The retained full-suite
  log independently records the earlier decisive three-test failure.

## Preserved Authority Boundary

No Genesis or official-mjlab smoke training started. No checkpoint, normalized
ONNX output, candidate or held-out seed, full matrix row, evaluator result,
publication, activation, transfer, or physical work was produced. The full
CUDA envelope remains unauthorized pending independent review and a later
separate Manager decision.
