# GOAL

## Work Mode

Work directly in one Codex task. No delegated roles or autonomous goal loops.
Use `TRAINING_ACTUALIZATION.md` as the only ordered queue. Preserve original
scores, negative receipts and physical-authority boundaries.

## Active Mission

Build useful, composable MicroDuck behaviors with independently evaluated
locomotion and an explicit operating envelope. Preserve the versioned 61D/14D
policy contract and distinguish simulation development from physical acceptance.

## Current Milestone

Document and publish the complete project state, then review the approach

## Current Status

The owner requested repository and evidence synchronization before assessing
whether progress has stagnated and whether tools, frameworks or methodology
should change. New training and simulation are paused for that review.
The review entry point is [PROCESS_REVIEW_20260916.md](docs/workspace/PROCESS_REVIEW_20260916.md).

Latest experiment: **V66 guided first-impact numerical gate passes in all
16 model/phase buckets.** All 96 cases, 358,400 physics samples and 48 exact
repeat pairs verify; eight controls reproduce V65. The finest comparison
(0.3125/0.15625 ms) stays within 0.1 mm: maximum position difference 0.064698 mm,
penetration-peak difference 0.061970 mm. The coarser pair passes only 12/16.
This establishes only a guided ankle-bench numerical reference.
[Result](experiments/walking/impact-convergence-v66/README.md).

**Full-robot dynamics remain unresolved.** V62 passes static collision-geometry
checks with 7,592 colliders. V63–V65 full-robot diagnostic gates fail; fixing
BAM force-input age does not rescue fine-step replay. Fixed HOME falls on both
reference models. No full-robot numerical reference or calibrated model is
admitted by these results.

**Retained behavior:** original V21 walking/V15 standing with V30 heading.
V54 shared remains a development starting point, not a promoted replacement.
V54/V55 retain 5/14 exposed surface passes; V55 improves downhill survival but
still fails complete acceptance and regresses one 180-second composition.
The coordinate-target course passes six exposed conditions. Camera-driven
following passes 11/16 required development cases. Official runtime inference
and command replay pass component checks, but its body rehearsal falls during
HOME_RAMP. There is no general carpet, recovery or physical capability admission.

## Next Decision

Complete publication and review the process before selecting another experiment.
The prior proposal is a short 0.035–0.135 s full-robot impact window, capturing
complete solver/BAM/FIFO state at 0.035 s and reproducing exact 5 ms controls
before finer comparisons. Fixed-input plant integration and live BAM feedback
would be separate stages. This is a review candidate, not an automatic launch.
Runtime startup, perception failure isolation and broader terrain remain queued.

## Verification and Evidence

- Publication tooling check: 141 tests pass, with no failures or skips.
  Publication verification and archive checks are recorded in
  [the evidence guide](docs/workspace/publication-20260916/README.md).
- V66 has seven focused tests; V65 has nine. Their closed results remain scoped
  to those diagnostics; passing tooling tests is not walking acceptance.
- [Process-review packet](docs/workspace/PROCESS_REVIEW_20260916.md) links the
  dated experiment reports, research and limitations.
- [Prior status history](docs/workspace/STATUS_HISTORY_20260916.md) preserves
  the complete status document before this consolidation. Its historical
  next-step language does not override the current milestone.

## Current Boundaries

Publication to `jakekinchen/microduck-rl-genesis` is explicitly authorized by the
owner's September 16 request. This authority does not activate a policy, operate
hardware, launch paid compute, or admit incomplete third-party artifacts.
Do not reuse prior Brev pilot authorizations or start a CUDA matrix. No new
compute is required for the publication task.

Behavior/library acceptance still requires `docs/workspace/BEHAVIOR_VALIDATION.md`:
independent behavior/contact/load gates, actual parameter coverage, unseen
families, continuous transitions, endurance and evidence-bound physics checks.
Public datasets and simulator agreement do not provide Ducky-specific physical
calibration. Missing or failed cases remain missing or failed.
