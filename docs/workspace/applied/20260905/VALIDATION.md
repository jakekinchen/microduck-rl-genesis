# Applying the audit to active training — 2026-09-05

The source-checked working focus is the selected turn-correction policy versus
the preceding robust policy on visible development case `75003-figure-eight`.
`preflight.json` records the actual policy/trace/domain/source checks;
`comparison-summary.json` retains the first differences and coverage limits.
No new training or physics rollout was launched by this integration task.

The active training task received the applied workflow, next-experiment brief,
resource guard, reserved-seed boundary and exact diagnostic findings. It retains
ownership of training, physics and evaluator changes. Existing staged release
paths were preserved. The project skill and AGENTS now route subsequent work
through the same practical checks, without introducing another agent loop.

Executed validation: seven active-workspace tests, twenty workspace/viewer tests
and eighteen exchange tests pass. The active checks cover policy tampering,
source drift, missing manifest bindings, wrong suite identity, absent/blocked
focus and mismatched randomized domains. Runtime/package/MPS, frozen contract
and pinned BAM checks pass. JavaScript parses and Python compiles.

Actual browser inspection confirmed the default selection is turn-dev versus
robust-dev, case 75003. **First fall** selects 1.56 s in both the simulation
slider and the recorded sample; tilt is 78.23 degrees and the fall flag is true.
The domain panel exposes the retained perturbations. The case has no retained
video, which remains explicit; the trajectory supplies the inspection data.
The native evaluator recording offsets are now separate from the simulation
clock (legacy first video frame at 0.02 s, dynamic at 0.04 s).

The diagnostic comparison aligns only 78 rows before the fall against 2,400
comparison rows. It preserves incomplete coverage and missing contacts;
physics causality and new behavior acceptance remain unestablished.

## Live gait-lane follow-up

While this integration was being applied, the training owner advanced to gait
correction. The guard now recognizes `train_laser_gait.py`; a repository-owned
trainer was observed active. All ten gait-v3 source hashes initially matched.
A later preflight caught source drift against that record and a new gait-v4
starting record, retained in `gait-running-source-check.json`. Those records
are time-specific; no exact PID-to-run association is claimed. The training
owner received the finding and the requirement to preserve earlier source bytes
and terminal negative status when creating the successor.

Duck Lab now has a tested `microduck.laser-gait-evaluation/v3` reader. It keeps
target and gait gates separate, rejects contradictory composite counts/gates,
excludes reserved-opened reports, and uses the native gait video origin of
0.02 s. Actual gait evaluation is still the training owner's work; the reader
was tested with fixtures. Updated suites: eight active-workspace, twenty-two
viewer/workspace, eighteen exchange and twenty-three offline-diagnostic tests.
