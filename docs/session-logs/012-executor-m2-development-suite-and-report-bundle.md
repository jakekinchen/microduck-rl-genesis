# Executor log 012 - M2 development suite and report bundle

**Date:** 2026-09-02

**Role:** Executor

**Brief:** `docs/briefs/012-m2-development-suite-and-report-bundle.md`

## Implemented

- Added visible development suite `microduck.walking-visible-development.v1`
  with two public case IDs and seeds 74001/74002, disjoint from the frozen
  walking acceptance seeds. Candidate policies and held-out status are
  forbidden by the suite validator.
- Extended the evaluator core to emit typed per-physics-step rows and optional
  320x240 control-rate render frames without importing training rewards.
- Added a five-file bundle writer for `evaluation.json`,
  `trajectory.parquet`, `rollout.mp4`, `environment-lock.json`, and
  `attestation.json`.
- The Parquet schema retains root pose, all 14 joint positions/velocities,
  policy action, actuator target/torque, twist command, control/physics step,
  and finite-state marker for 160 rows.
- The 40-frame H.264 MP4 is decoded during validation. All four non-attestation
  artifacts are bound from the final attestation; the policy, task/interface,
  model scene/root, BAM commit/parameter, evaluator source/config/suite,
  dependency lock, and runtime are digest- or version-bound without absolute
  paths or wall-clock fields.
- Added PyArrow 21.0.0 to both dependency lanes and regenerated the hash-locked
  Apple environment.

## Validation receipts

```text
evaluator bundle verified: five files byte-identical across two same-host runs,
160 Parquet rows, 40 decoded MP4 frames
```

The reviewed Apple host reproduced identical SHA-256 values for all five files:

```text
evaluation.json       885d44f0512c7bc9f2b2097554cbd8e9b68df11803f6e361506eef925e21f8b0
trajectory.parquet    05f9045cb709a043b44dbc94e9a26d51253f553eb9c4b91ded4ec61592e9c7e5
rollout.mp4           c243f5dbbb85dc72836e6f5d4bea937dc4311e66fad80ed5fcece1b70af42055
environment-lock.json 1f3760bc42ca156ab5c2b55cb73794151129f335c0c17f00ad2f34d340f5f02b
attestation.json      4a1b92870eb1b7bec66cd46b7018765b3b57f9ca6b2513c8e89861c0dd995d13
```

The BAM-enabled full runner completed with `tous les tests passent`; `git diff
--check` passed.

## Evidence boundary

Byte repeatability is asserted only for repeated runs on the recorded host and
runtime profile, not across hosts or codecs. The zero policy and public cases
prove bundle plumbing only. Task success stays `not_evaluated`; no held-out
case, final candidate, training, paid compute, credential, publication, or
hardware action was used.
