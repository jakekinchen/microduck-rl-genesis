# Experiment diagnostics improvement

User request: learn from MicroDuck logs, improve operations and simulation
diagnostics, complement sim2claw, use Git, and preserve active Mac training.

This additive slice runs in an isolated worktree at baseline `eabc933`.
The concurrent workspace task owns Duck Lab, behavior drafts, history indexing,
and the project skill. The concurrent laser task owns training and evaluation.
Neither is modified here. No role cycle is created.

## Acceptance

- [x] Diagnose retained trajectories by case, timestamp, exact recorded action,
  command, position and event; expose missing/truncated or malformed evidence.
- [x] Show the first divergence and distinguish feedback-policy comparison
  from fixed-action replay; never infer physics causality from two videos.
- [x] Provide bounded read-only process preflight and a machine-readable busy
  exit for future launches, without signaling or attaching to running jobs.
- [x] Produce a portable interactive offline report with source hashes and
  per-case traces; preserve negative outcomes and original receipt bytes.
- [x] Record reusable physics probes, history lessons and sister-repo mapping.
- [x] Verify with standard-library fixture tests and retained trace comparisons;
  no simulator, learner, dependency installation or GPU test.
- [ ] Commit only this slice, retain validation, and expose it from the live
  repository without changing active training sources.

The ordered project queue remains `TRAINING_ACTUALIZATION.md`. This file tracks
only the bounded software improvement requested in this task.
