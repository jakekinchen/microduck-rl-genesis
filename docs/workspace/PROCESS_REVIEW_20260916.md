# MicroDuck process-review packet — September 16, 2026

This is the evidence handoff for the owner's requested review of progress,
tools, frameworks and methodology. It organizes completed work and unresolved
questions; it does not conclude that a framework change is necessary. New
experiments are paused while the repository is synchronized and this review is
prepared. [GOAL](../../GOAL.md) is current status;
[TRAINING_ACTUALIZATION](../../TRAINING_ACTUALIZATION.md) remains the only queue.

## What the project is trying to achieve

Develop useful, composable MicroDuck behaviors with credible locomotion across
declared environments, independently checked contact/motor behavior, and
eventual physical validation. Walking, stopping and transitions are the
foundation for perception, pursuit, navigation and recovery. The owner asked
for public-source research and local development without requiring new physical
measurements from them. That supports simulation work and public parameter
priors; it cannot establish calibration of this particular robot or carpet.

## What works, and under which evidence boundary

| Area | Best retained evidence | Remaining limit |
|---|---|---|
| Development pipeline | Apple Genesis/MPS training, normalized ONNX, 61 observations/14 actions, independent native MuJoCo/BAM evaluation; reproducible interface and runtime checks. | A functioning pipeline is not a behavior pass. Current later native-training lanes differ from the initial Genesis lane. |
| Flat locomotion | V21 walking/V15 standing; V30 heading retained. V21 cleared 63 original/repeated windows and V22 24 flat physical-combination windows. | Exposed development envelope on V11; not calibrated, general terrain, or full-CAD admission. |
| Endurance and composition | Retained V30 and V54 shared complete both exposed 180-second compositions; V55 yaw arm retains only 1/2. | Whole-session gates matter even when individual windows pass. Two starts do not establish reliability. |
| Surface generalization | V54/V55 preserve 5/14 exposed surface passes. V55 yaw arm survives four downhill sessions, but all four still fail combined acceptance. | These are numerical surface profiles and exposed cases, not 14 calibrated carpet types. No general carpet capability. |
| Coordinate-target course | Six 66-second course conditions pass the frozen v2 course/contact/gait gates; 19,800 exact actor rows and 79,200 load samples checked. | Privileged target coordinates, exposed flat course, retained V11. Not vision or physical success. |
| Camera-driven following | V3 RGB marker following passes 11/16 required development cases; both stationary negatives reject. | Combined conditions lose the target; three reacquisition cases fail yaw. Fresh layouts remain unopened. |
| Official runtime | 3,300 Rust inference rows match; adapter reproduces 19,800 command intervals. | Actual body/runtime rehearsal falls during HOME_RAMP, before walking. Components do not prove integration. |
| Collision geometry | V62 satisfies sampled 0.25 mm material checks, eight cavity checks, and 201 copied poses; 7,592 colliders compile. | Static consistency with V57 CAD/physical arrays, not full-robot dynamics or physical accuracy. |
| Contact integration | V66 guided ankle bench passes all 16 finest-step model/phase buckets; 96 cases and 48 exact repeats. | Only the guided bench. V63–V65 full-robot diagnostic gates remain negative. |
| Recovery and physical use | Non-actuating recovery preview and synthetic contract tests; public-source research and calibration plans. | No admitted recovery actor, Ducky-specific measured calibration, hardware deployment, or physical behavior acceptance. |

## Development history and changes of direction

| Period / lane | Question and outcome | Primary record |
|---|---|---|
| Initial port and Apple foundation | Preserve the observation/action/BAM contract across Genesis backends. Smokes and export parity established infrastructure; CUDA pilot failures did not supply task evidence. | [Foundation queue](../../TRAINING_ACTUALIZATION.md), [early retrospective](RETROSPECTIVE.md) |
| Laser and gait correction | Target-only success concealed poor stepping; camera-axis assumptions and backheel/reward shortcuts caused rejected attempts. Gait and load checks became explicit. | [Gait diagnosis](../../experiments/laser/GAIT_DIAGNOSIS.md) |
| Walking V1–V22 | Iterative actor/reward/controller fixes produced useful flat-floor gait. Geometry and internal-load gates rejected earlier apparent wins. V21/V22 passed their exposed banks. | [Historical walking results](../../experiments/walking/RESULTS.md) |
| V23–V30 | Longer continuous sessions and surface variations exposed heading drift and stopping problems. V30 heading retained useful flat/endurance behavior. | [V23 results](../../experiments/walking/V23-RESULTS.md), [dated status history](STATUS_HISTORY_20260916.md) |
| V31–V53 | Native learning, retention, braking, handoff coverage and recovery diagnostics pursued downhill stopping. Multiple selected improvements did not produce broad all-case acceptance. | [Queue and per-version receipt links](../../TRAINING_ACTUALIZATION.md), [status history](STATUS_HISTORY_20260916.md) |
| V54 | Routed versus shared learning recipes, 1,728,000 PPO transitions per arm. Shared retained both compositions and improved familiar downhill survival, but neither passed all gates; both stayed at 5/14 surfaces. | [Recipe comparison](../../experiments/walking/RECIPE-RESULTS-v54.md) |
| V55 | Matched yaw-weight comparison, 2,592,000 transitions per arm. Yaw6 improves downhill survival but still fails yaw/posture and regresses one composition; retain original actors. | [Yaw results](../../experiments/walking/YAW-RESULTS-v55.md) |
| September 13 course | Scoped coordinate-target demonstration completed with independent full-session checks. It establishes a useful narrow application of retained actors. | [Course results](../../experiments/laser/COURSE-RESULTS-v2.md) |
| September 15–16 research and V56 | Community/upstream audit, runtime, perception and standing feasibility. No six-condition posture recipe meets 25 degrees; paired training remains unlaunched. | [Research](COMMUNITY_RESEARCH_20260915.md), [execution](COMMUNITY_EXECUTION_20260916.md), [posture](../../experiments/walking/POSTURE-FEASIBILITY-RESULTS-v56.md) |
| V57–V61 | Audited real collision pairs and original CAD cavities. CoACD recipe fails material limits; compiler correction and higher hull cap solve only part of the problem. | [Geometry execution](COLLISION_GEOMETRY_EXECUTION_20260916.md) |
| V62 | Source-aware partitioning passes the static geometry gates with 7,592 colliders and preserved V57 physical arrays. | [V62 result](../../experiments/walking/contact-reconciliation-v57/surface-refinement-v62/README.md) |
| V63 | Fixed HOME falls on both V11/V62; passive V62 exceeds floor penetration; V62 action replay falls. Original V11 replay reproduced but fails the new 3 mm floor gate. | [V63 result](../../experiments/walking/startup-load-v63/README.md) |
| V64 | Matching V11 physical arrays and masking shell/floor pairs do not rescue replay. Finer integration changes both models' outcomes. An early launch is stopped and quarantined; fresh valid cases follow verified controls. | [V64 result and deviation](../../experiments/walking/contact-isolation-v64/README.md) |
| V65 | Holding BAM force-input age at 5 ms does not rescue fine-step robot replay. Matched isolated ankles agree across assets, but their timestep screen initially fails. | [V65 result](../../experiments/walking/feedback-contact-v65/README.md) |
| V66 | Further timestep refinement plus four impact phases closes the guided-bench screen; 16/16 finest buckets pass, versus 12/16 coarser. | [V66 result](../../experiments/walking/impact-convergence-v66/README.md) |

The dated history and original results are preserved verbatim. Documents titled
"latest" within an older experiment refer to that experiment's date, not the
repository's present state. Earlier target-only or reduced-model scores are
not silently rescored as later walking/full-model acceptance.

## Evidence relevant to possible stagnation

There is a concrete plateau on the comparable V54/V55 surface denominator:
5/14 passes across retained, routed, shared and yaw-refined policies. Improved
downhill survival has not crossed the complete behavior gate. V62–V66 then
advance geometry and numerical diagnosis without adding a walking capability.
These observations justify the review; they do not, by themselves, identify
Genesis, MuJoCo, BAM, architecture or reward design as the cause.

The strongest recent contact result is a deliberately simplified guided ankle,
not a whole robot. Increasing collider count, tightening a numerical tolerance,
or collecting more exact repeats must be judged by whether it changes a
decision about useful locomotion. Exact repeats establish repeatability under
fixed conditions; they do not provide independent generalization trials.

Some acceptance gates were added after earlier plausible demos exposed missing
physics/behavior checks. Preserve that history explicitly: a newly failing
gate is not automatically a policy regression, while unchanged benchmark
failure is not success merely because more diagnostics now pass. Thresholds
and sampled geometry requirements also need engineering justification; more
strictness is not a substitute for measured task relevance.

The publication audit also found 166 local commits beyond origin and 44.3 GB
of logical experiment, receipt, output and training-log files. Deduplication
and compression reduce the evidence transfer to 14.9 GB. Include this evidence
management and synchronization cost when comparing experiment workflows;
useful review should not require reconstructing weeks of unpublished state.

## Toolchain and methodological distinctions to audit

- **Simulation:** Genesis 1.3.3 for the original Apple parallel-training lane;
  later native MuJoCo/BAM learning and independent evaluation. V65/V66 record
  MuJoCo 3.12.0; the upstream audit also retains a separate 3.10 runtime probe.
  Always use each run's runtime/source record rather than assuming one version
  covers the whole project.
- **Learning/inference:** local Python 3.12.12, PyTorch 2.9.1,
  RSL-RL 5.4.2, ONNX Runtime 1.23.2 were inspected locally for this publication; the latest diagnostic runtime receipt separately records Python and MuJoCo.
  Retained actor interface is 61D/14D at 50 Hz. BAM update timing, input age,
  delay FIFO, friction and damping are part of the controller/model contract.
- **Geometry:** historical reduced model, V11 scoped contact model, V57 full
  CAD reference and V62 detailed collider assembly are distinct experimental
  treatments. Visual identity and a model filename do not prove active pairs.
- **Evaluation:** task, gait, slip, joint stops, non-foot support, penetration,
  applied internal loads, continuous transitions, endurance, actual variation
  coverage, and unseen banks remain separate gates. Open-loop action replay
  diagnoses integration; it cannot replace a closed-loop policy score.
- **Research/calibration:** public sources establish provenance and plausible
  priors. Cross-engine agreement establishes agreement on a model, not calibrated
  physical accuracy. See [terrain strategy](TERRAIN_GENERALIZATION.md) and
  [acceptance standard](BEHAVIOR_VALIDATION.md).
- **Operations:** one task, one ordered queue, advisory compute guard, no role
  cycles. Fast tooling checks are shared with CI. Bulky immutable evidence is
  archived with file hashes, not embedded as ordinary Git blobs.

## Questions the subsequent review should answer

1. **Define useful progress.** Which smallest capability and operating envelope
   should be the next deliverable? Which fixed behavioral metric should improve,
   and what finite negative result would stop that approach?
2. **Separate plant, feedback and learning.** Does a short, complete-state,
   fixed-input impact comparison answer a decision-relevant question? Can the
   smallest justified collision model settle it before another long replay or
   7,592-collider training proposal?
3. **Compare frameworks on one matched task.** Would an unchanged upstream
   native recipe provide a stronger baseline than further port-specific fixes?
   Compare semantics, contact/actuator fidelity, throughput, observability and
   reproducibility separately. No provider purchase or paid launch is implied.
4. **Audit the learning objective and task distribution.** Are posture targets
   feasible, transition states adequately represented, and stop/handoff losses
   competing with velocity/gait objectives? V56 says the proposed 25-degree
   posture target lacks a witness; it does not prove learning impossible.
5. **Audit generalization evidence.** Which surface/environment families are
   still genuinely unseen? What calibration limits remain unavoidable with
   public-only data? Avoid renaming repeatedly inspected cases as held-out.
6. **Audit experiment cost and decision value.** Reconstruct transitions,
   wall time, storage and failed/aborted cases from receipts before asserting an
   overall ROI. This packet deliberately does not invent a total compute cost
   or aggregate success rate across changing denominators.

The previously proposed next diagnostic is a 0.035–0.135 s full-robot impact
window with a complete solver/BAM/FIFO checkpoint and exact 5 ms clone controls,
then separately fixed motor schedules and live feedback. It is a **candidate
for this review**, not an instruction to launch automatically. Runtime startup,
pixel-following failure isolation, posture learning and broader terrain remain
downstream proposals until the review chooses priorities.

## How to inspect and reproduce

Read this packet, then the primary result linked for the disputed claim. Use
the [publication guide](publication-20260916/README.md) for archive scope,
hashes, external-path mapping and restoration. Read-only tooling is available
without a simulator via `./scripts/duck status` and `./scripts/duck verify`.
The [verification guide](VERIFICATION.md) distinguishes tooling checks from
runtime and behavior acceptance. A full simulation rerun is not required to
read the retained evidence and must not be launched implicitly by this review.

No paid compute, hardware movement, policy activation, protected-bank
evaluation or new training is included in the documentation/publication task.
