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
- [x] Commit only this slice, retain validation, and expose it from the live
  repository without changing active training sources.

The ordered project queue remains `TRAINING_ACTUALIZATION.md`. This file tracks
only the bounded software improvement requested in this task.

## Closeout

Implementation `f227530` on isolated `codex/experiment-diagnostics` was replayed
as `578aa31` on the live `main` checkout. All 14 destinations were new and
the shared index was empty before replay. The 22 offline tests pass there
(0.262 s); no simulator or training dependency was imported. Existing dirty
workspace/laser files remain owned by their original tasks.

The report passed browser case switching, time scrubbing at 4.000 s, and a
390-pixel layout check over localhost. Direct file-URL navigation was rejected
by browser policy, so standalone file opening is not claimed as browser-tested.
The source is self-contained HTML without network calls.

Read-only activity observed PID 46386 running train_laser_turn.py during
verification. A later 10:03 UTC snapshot found no known training entrypoint;
no process was signaled, stopped or restarted by this work. This snapshot
is not a learned-policy completion claim.

Duck Lab and Sim2Claw task owners received the interface and commit. Their
neutral exchange adapters are separate work; this comparison does not certify
robot ABI compatibility. No Brev resource was used or provisioned.
