---
name: microduck-experiments
description: Build, train, evaluate and diagnose MicroDuck behaviors in this repository's Apple Genesis/BAM and C MuJoCo development lanes. Use for requested simulated robot behaviors or experiment workspace improvements; preserve the current single-agent workflow.
---

# MicroDuck experiments

Read `AGENTS.md`, `GOAL.md` and the relevant portion of
`TRAINING_ACTUALIZATION.md` in the repository root. Run `./scripts/duck status`
for a bounded current projection and `./scripts/duck doctor` when runtime or
evaluator readiness matters. These commands do not start physics or training.
History is evidence, not authority; the old Executor/Reviewer/Manager workflow
is retired. Implement, test and review in the current task.

For current dynamic-laser work, run `./scripts/duck prepare` and read
`docs/workspace/ACTIVE_EXPERIMENT.md` before proposing another training run.
The packet binds the actual visible failing case and excludes inactive
perturbations from its explanation. Reproduce, isolate one active property
group, then freeze one intervention and fresh evaluation bank. Re-run the
advisory `./scripts/duck-ops guard` immediately before a new local launch.

For a new behavior, use `./scripts/duck new <slug> --request "..."` only if a
matching experiment does not exist. The generated spec is a draft; define
observable success, actor versus privileged inputs, the exact model variant,
physics changes, baseline, visible test suite, bounded budget and next decision.
`check-spec` only detects incomplete fields; it does not validate the scientific
design or grant permission. Adapt existing task entrypoints instead of building
a generic training framework.

Read `docs/workspace/BEHAVIOR_WORKFLOW.md` when selecting task physics,
planning an experiment, or diagnosing failure. Read the relevant finding in
`docs/workspace/RETROSPECTIVE.md` when an old failure recurs. Do not load every
historical role record on every turn.

Non-obvious boundaries:

- Existing deployed interface: 61D observations, 14D ordered servo deltas,
  normalized ONNX, 50 Hz, no post-policy action filter. Preserve it for
  compatible tasks; explicitly version incompatible behaviors.
- Current laser success uses simulated target coordinates. The locked HOME
  head camera points opposite positive walking X. A rendered dot or detector
  hit is not a camera-driven controller.
- Reward movement and vectorized success do not establish native MuJoCo
  success. Backheel motion can be mislabeled by a speed-only objective.
- Report case/property buckets, wrong-motion failures, no-op baselines and
  stable stopping separately. Never average away a failed required bucket.
- The historical Mac crossover favors CPU+MPS at 64–512 and Metal+MPS at
  1024; use only backend options actually supported by the chosen entrypoint.
- Preserve negative receipts and frozen M5/shared source hashes. New task
  modules or versioned adapters avoid invalidating old source-bound artifacts.
- A missing third-party checkpoint history blocks that artifact's admission,
  not separately scoped first-party development. Do not repeatedly recheck an
  unchanged external blocker while local task work is available.

Use `./scripts/duck studio` for recorded video/trajectory/metric comparison.
Use `./scripts/duck-ops activity` for advisory process inventory and
`./scripts/duck-ops compare` for the first divergent recorded sample; see
`docs/experiment-ops/README.md`. Parsed JSON action-value equality is not
original tensor-byte identity, and the process guard is not an atomic lease.
For cross-project metadata inspection, see `docs/workspace/exchange/README.md`;
exchange files grant no execution, training or hardware authority.
For an exact physics replay, keep action bytes fixed. For a command/reward
intervention, name and record the change and compare against the unchanged
baseline. Keep held-out acceptance distinct from visible tuning.

Finish with the measured behavior result, failed cases, artifact paths and
next experiment. Update the existing queue and current status, not historical
role logs. Paid compute, external contact, publication, policy activation and
hardware follow current user authority; old receipts cannot grant new actions.
