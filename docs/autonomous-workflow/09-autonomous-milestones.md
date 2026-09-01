# Autonomous Milestones

This file defines invariant milestones for autonomous work on this project.

Milestones are required outcomes, not detailed subtasks. The Executor and Reviewer choose the implementation slices needed to satisfy the next milestone.

## Overall Goal

Produce immutable Microduck walking and bounded-backflip policy artifacts whose
contracts are shared across Genesis and the official mjlab stack, whose success
is measured by a frozen independent C MuJoCo evaluator, and whose proof class is
accurately separated from physical authority. `TRAINING_ACTUALIZATION.md` is the
authoritative ordered task queue; this file records only its invariant gates.

## Milestone Rules

- Milestones are invariant outcomes, not task lists.
- Agents choose implementation slices needed to satisfy the next milestone.
- The Reviewer may not mark a milestone complete without running or recording its verification gate.
- The Manager challenges work that optimizes beyond the current milestone before the gate is satisfied.
- If a milestone gate proves wrong or incomplete, update this file.

## M0 - Reproducible Apple Baseline

**Required outcome:** A second clean Apple checkout installs the committed lock,
runs both 64-environment x 5-iteration tasks, exports both smoke checkpoints,
passes ONNX parity, and retains a complete versioned receipt bundle.

**Why this is invariant:** Backend conformance and policy evaluation are not
credible if the primary local training lane cannot be reproduced from committed
state.

**Verification gate:**

```bash
./scripts/setup_apple.sh
.venv-apple/bin/python scripts/freeze_contract.py --check
GS_ENABLE_ZEROCOPY=1 .venv-apple/bin/python tests/run_all.py
./scripts/run_apple_smokes.sh
```

**Completion evidence:**

- `receipts/apple-baseline/<run-id>/` contains bounded stdout, environment and
  git metadata without hardware serials, configs, checkpoints, exports, and a
  SHA-256 manifest.
- The receipt identifies the clean source commit and records every test skip.

## M1 - Shared Semantic Contract

**Required outcome:** Genesis and the official mjlab adapter consume the same
byte-identical interface/BAM fixtures and pass thresholded BAM/model conformance
tests without collapsing distinct model variants.

**Why this is invariant:** A policy comparison is meaningless if observation,
action, actuator, reset, or model semantics differ between backends.

**Verification gate:** Contract drift, authoritative BAM golden-vector,
14-servo closed-loop, model reconciliation, and official adapter tests all pass.

**Completion evidence:** Generated fixtures, pinned authority digests, test
outputs for both backends, and a versioned upstream-or-divergence decision.

## M2 - Independent C MuJoCo Evaluator

**Required outcome:** A CPU-only official-MuJoCo/ONNX-Runtime evaluator runs the
frozen 5 ms physics and 50 Hz unfiltered policy loop with BAM's C controller and
emits policy-bound deterministic reports.

**Why this is invariant:** Training-backend self-reported reward cannot establish
reference task success.

**Verification gate:** Repeated official-walking-ONNX evaluations under one
suite ID produce identical classifications and stable metrics within declared
tolerances.

**Completion evidence:** `evaluation.json`, `trajectory.parquet`, `rollout.mp4`,
`environment-lock.json`, and `attestation.json` bound to the policy digest.

## M3 - Frozen Task Success Gates

**Required outcome:** Predeclared walking and ordinary-start, zero-assistance
backflip state machines correctly classify positive, assisted, and failure
fixtures before candidate inspection.

**Why this is invariant:** PPO return, movement, and visually plausible motion
are not task-success definitions.

**Verification gate:** Classifier fixture tests pass with curriculum and
acceptance populations stored separately.

**Completion evidence:** Versioned semantic files, fixtures, and test results.

## M4 - Measured Apple Scaling

**Required outcome:** A checked-in benchmark report selects the default everyday
environment count and CPU+MPS crossover from total iteration time, memory,
thermal stability, resets, synchronization, NaNs, and samples/minute.

**Why this is invariant:** Longer local work needs a stable, measured operating
point rather than a physics-only throughput guess.

**Verification gate:** Bounded 64/128/256/512 and feasible 1024-environment
benchmarks plus a sustained thermal run complete without hidden instability.

**Completion evidence:** Raw benchmark receipts and the selected defaults.

## M5 - Decisive Cross-Backend Experiment

**Required outcome:** Genesis and official mjlab candidates are trained with
frozen semantics, matched transition budgets, predeclared seeds/checkpoints, and
evaluated by the same held-out M2 suite.

**Why this is invariant:** Genesis remains primary only if reference outcomes,
not reward, are non-inferior under a fair comparison.

**Verification gate:** The predeclared multi-seed analysis reports time to
threshold, task metrics, variance, and simulator/reference ranking consistency.

**Completion evidence:** Frozen configs, all predetermined exports/evaluations,
and the signed comparison report.

## M6 - Immutable Attributable Artifacts

**Required outcome:** Policy manifest v2 binds policy, normalizer, checkpoint,
exporter, model, BAM, task, evaluator, evidence, and licensing by SHA-256; one
official and one community artifact validate without executing repo code.

**Why this is invariant:** Retrieval, validation, library import, approval, and
activation must remain separable and auditable.

**Verification gate:** A fresh machine retrieves exact revisions/digests and
validates locally without activation.

**Completion evidence:** Schemas, manifests, provenance resolution, and fresh
machine receipts. Publication remains a human-owned boundary.

## M7 - Optional NVIDIA and Challenger Lanes

**Required outcome:** Any optional lane first proves model/BAM/observation/reset/
ONNX-loop conformance and is retained only for an official-stack gap or a
predeclared material improvement.

**Why this is invariant:** Optional compute must not bypass semantic gates or
become spend without decision value.

**Verification gate:** Frozen digests/seeds/budgets and conformance pass before
PPO; replacement requires about 2x time-to-held-out-threshold improvement or
materially better MuJoCo agreement.

**Completion evidence:** Local spike receipts or explicitly authorized cloud
receipts plus verified Brev teardown.

## M8 - Staged Physical Validation

**Required outcome:** With explicit action-time authority, the exact policy
digest passes or fails the declared staged physical protocol with synchronized
telemetry and preserved negative results.

**Why this is invariant:** No simulation or reference result grants physical
authority.

**Verification gate:** The digest-bound quiet-stand through dynamic-task protocol
is executed under declared hardware/runtime/environment limits.

**Completion evidence:** Hardware attestation, synchronized observations,
actions, servo telemetry, video, stops, and final proof classification.
