# Mandatory validation for every behavior

Owner requirement, September 6: every library behavior must be thoroughly
tested, domain randomized, robust across different environments, and grounded
in validated physics. This applies to learned actors, deterministic controllers,
perception adapters, recovery, and their compositions. It is a requirement,
not evidence that any current behavior satisfies it.

"Fully tested" means all preregistered gates pass for a named operating
envelope and exact implementation. It never means all possible environments
or guaranteed physical transfer. Missing evidence, omitted required cases,
failed buckets and unresolved physics discrepancies stay explicit. An old
nominal pass is not grandfathered into a robustness or accuracy claim.

## Six required parts of every plan and acceptance record

| Part | Required content before claiming a capability |
|---|---|
| Operating envelope | Named environment families, numerical speed/terrain/object/sensor limits, units and frames, supported initial states, exclusions, and tested out-of-envelope refusal or fallback. |
| Independent tests | Nominal, boundaries, failure/negative controls, disturbances, ordinary starts, repeated/long-horizon operation, continuous transitions, cancellation, timeout and sensor loss. Task success AND physical-quality gates; never reward alone. |
| Domain randomization | Explicit factor matrix and sampling process, randomized learning for learned policies, randomized closed-loop testing for every controller, and proof the intended parameters actually varied. |
| Generalization | Disjoint training/development/final populations, unseen environment families and combinations, preregistered repeats/sample sizes/uncertainty reporting and per-bucket thresholds, evaluated on a frozen candidate. |
| Physics validation | Exact model/actuator/sensor identities, geometry and dynamics audits, contact/timestep/solver checks, cross-engine diagnostics, measurement-based calibration, known discrepancies and uncertainty. |
| Reproducible evidence | Source/policy/controller/model/suite bindings, materialized parameters and seeds, complete per-case outcomes including failures, original actions/telemetry, actual videos and reproduction commands. |

The `microduck.behavior-draft/v2` generator includes a `quality_plan` with these
six sections. Each field must describe the concrete plan or reference a specific
plan section. `duck check-spec` rejects omissions, malformed fields and bare
"N/A" exemptions. It checks **planning completeness only**: nonempty text is
not executed evidence, an adequate scientific design, or capability admission.
Legacy v1 drafts need a separately versioned v2 plan for new work; the checker
does not rewrite them or alter any historical receipt or result.

## Domain randomization must affect the actual task

For every factor, record units, nominal value, numerical bounds, distribution,
sampling frequency, correlations, engine implementation and source/rationale.
Distinguish measured variation from exploratory uncertainty. Cover:

- Robot: mass, center of mass, physically valid inertia, payload and geometry
  uncertainty where relevant; preserve kinematic and actuator feasibility.
- Actuators: battery voltage/drop, torque/current/speed limits, friction,
  backlash and response lag within the declared hardware/model envelope.
- Sensing/timing: noise, bias/drift, latency/jitter, dropout, stale observations
  and frame/calibration uncertainty using the actual deployed inputs.
- Surfaces/terrain: friction, compliance, slopes, uneven ground, seams and
  obstacles, with valid collision geometry and feasible support conditions.
- Task/perception: layouts, targets/distractors/occlusion, camera pose/intrinsics,
  illumination and appearance for vision-driven behaviors. Randomized rendering
  is not evidence of perceptual robustness when control reads privileged state.
- Initial conditions/interactions: heading, pose, velocity, preceding behavior,
  bounded pushes and object properties where relevant, without assisted resets.

An irrelevant factor can have a specific, recorded rationale (for example,
lighting does not enter a purely proprioceptive actor). Do not use one blanket
exemption to avoid randomized testing. Deterministic controllers do not need
invented RL training; they still face randomized closed-loop tests.

Test application against actual runtime parameters and their logged coverage,
not just configuration ranges. Reset randomizations from an immutable nominal
model; test for accumulation, cross-environment leakage and unintended correlated
sampling. Use staged curricula for diagnosis, then test combined variations and
corner cases. Preserve a no-randomization baseline or bounded ablation to measure
tradeoffs. Record worst-bucket performance; averages cannot hide required failures.

## Generalization is a separate experiment

New random seeds on the same flat floor do not establish unseen-environment
generalization. Partition environment/layout/object/appearance families where
applicable, not just individual frames or episodes. Include unseen combinations
within the declared envelope and explicit beyond-envelope stress tests that
check fallback without pretending arbitrary environments must be solvable.

Freeze split definitions, candidate policy AND controller, evaluator, thresholds,
trial counts, repeat seeds and decision rule before final evaluation. Report
success/failure counts, uncertainty, worst-case safety metrics and each required
bucket. Repeated windows in one continuous rollout are not independent trials.
Never tune on final results and keep calling that population untouched: preserve
the result as exposed evidence and preregister a new final test when appropriate.
Do not open existing protected acceptance banks early. Versioned local development
banks and the established final-evaluation protocol retain their distinct roles.

## Accurate physics needs measurements, not just two agreeing simulators

Audit collider coverage and mesh/frame alignment; mass/COM/full inertia; joint
axes/limits; motor torque/friction/battery; sensor timestamps and reset histories.
Validate contact response, slip, body interference and applied internal loads,
non-foot support, timestep/solver sensitivity and conservation/passive-response
checks appropriate to the task. Do not equate unlike contact-force aggregates.

Use byte-identical actions and declared initial states for physics-isolation
replays. Closed-loop tests with differing actions diagnose system performance,
not a causal solver mismatch. Cross-engine agreement is corroboration, not
ground truth. Bind calibration to measured hardware/objects/surfaces and report
uncertainty and residuals against preregistered tolerances. Validate on measurements
not used for fitting. If those measurements are absent, physics remains
provisional: local simulation development may continue, but calibrated accuracy
and real-world transfer claims remain blocked. Never soften physics or acceptance
thresholds solely to rescue a candidate. Physical trials require separate authority.

## Admission and current work

The future capability catalog must require evaluator-owned evidence for every
applicable part above; it may not accept self-asserted booleans or completed
planning text as proof. Safety failures, missing data or relevant physics gaps
block the corresponding capability claim. Passing a prerequisite does not admit
an entire composition. Retain both successful and failing videos at honest speed;
inspect motion/contact/pose as well as scalar task scores.

Walking is still a development candidate, not generalized locomotion. V21
passed 63 exposed original/repeated windows; V22 passed 24 flat-floor physical
parameter windows. V23 then passed only 2/12 new terrain sessions (plus 2/2 flat
controls): downhill, cross-slope, seam and uneven-ground buckets failed. Its
180-second endurance bank passes four sustained walks, while two compositions
fail whole-session heading despite passing their individual windows. Ducky-specific physical
measurements remain absent from the inspected corpora; the passive calibration
intake does not admit missing measurements. None of these results completes this
standard. L2 in `TRAINING_ACTUALIZATION.md` remains active; B1 contains subsequent
library work. New requirements supplement frozen evaluations without rewriting
their thresholds, hashes, original scores or proof classes.
