> Historical execution record. Subsequent V62–V66 results and the current
> review priority are summarized in the [process-review packet](PROCESS_REVIEW_20260916.md).
> The proposed next steps below describe the decision at the time of this record.

# September 16 community-research execution

The subsequent [collision-geometry execution](COLLISION_GEOMETRY_EXECUTION_20260916.md)
resolves the compiler issue and passes the bearing component, while the three
remaining shapes still fail material accuracy. That follow-through and the
current ordered queue supersede the first geometry step proposed below.

The owner authorized the researched sequence and bounded subagents. Three
specialists handled upstream physics, runtime/recovery and pixel following;
integration, review and standing feasibility remained in the current task.
There were no role cycles, paid instances, hardware operations or policy
activation. Existing models, policies, failed receipts and protected banks
remain preserved.

## Results and decisions

| Area | Executed evidence | Decision |
|---|---|---|
| Upstream physics | Two MuJoCo versions reproduce actual collision configuration; 108 source bindings checked. V11 has 11 active colliders, current upstream 70. | Preserve V11 as a scoped reference. Reconcile full-CAD coverage before broad skill admission. |
| CAD contact shapes | 201 copied poses expose jaw/neck convex-hull overlap when those pairs are enabled. Eight original-surface checks locate the deepest hull contact in empty CAD space; canonical containment diagnostics are retained. | Replace false-filled cavities with justified collision proxies; do not simply disable the pairs. Global surface clearance and dynamic loads remain separate checks. |
| V58 collision proxies | One frozen CoACD configuration generates all four meshes in 152.8 s. Every mesh fails the 0.25 mm sampled excess-material limit; MuJoCo rejects a bearing part with too-small volume. | Terminal negative. No proxy model is admitted; compilation-dependent coverage, cavity and pose checks remain unavailable. |
| Standing posture | 12 unchanged-actor cases and 18 fixed-head diagnostic cases, all ten seconds. 15,000 actions and 60,000 load samples verified; the zero-offset control reproduces 3,000 original controls exactly. | No recipe meets the proposed 25-degree target across all six conditions. Paired PPO remains prepared but unlaunched. This is a bounded negative, not proof of physical or learning impossibility. |
| Official runtime | Mac build; 3,300 Rust ONNX rows exactly match; a new command adapter reconstructs 19,800 recorded intervals. One daemon/body rehearsal falls at 0.904 s during HOME_RAMP. | Inference and command components are verified. The actual runtime/BAM transport and startup integration still need implementation and conformance. |
| Pixel following | One complete straight run passes, then 11/16 required development cases pass; both stationary negatives reject. Independent RGB/command/action verification covers the complete bank. | Functional exposed sensor-driven following exists, but the bank does not advance to unfamiliar layouts or library admission. |
| Recovery/handoffs | Non-actuating state-machine preview and 16 synthetic tests; pinned upstream artifact metadata assessed. | No recovery actor admitted. Cancellation, missing evidence and invalid sensing inhibit progression; actual control/receipt integration remains absent. |
| Carpet/terrain | Existing public-source evidence and required model/calibration gates reassessed. | No new carpet training or physical claim. Broader collision-model and locomotion prerequisites remain unmet. |

## What the following controller can currently do

V3 follows a 70 mm diameter red marker centered 40 mm above a nonreflective,
flat simulated floor. It receives RGB-derived bearing/range plus capture,
receive and frame-sequence data. Simulator target/root coordinates are used
only by rendering and independent scoring. It commands the unchanged V21
walking/V15 standing actors through V30 heading and the existing command ramp.

The isolated 30-second straight run covers 1.682 m, maintains the declared
range band for all scored tracking samples, has 2.74 cm maximum cross-track
error, and passes gait, posture, joint/torque, V11 contact/load and final-stop
checks. The 18-session development bank includes two starts per condition:
straight/curved paths, combined latency/mass/friction/appearance changes,
target loss, dropped/stale frames, occlusion, distractors and stationary controls.

Five required cases fail. Both combined cases lose the clipped marker and
stop without useful pursuit. Start zero in target-loss, occlusion and distractor
cases fails yaw response after reacquisition: 0.2002463513 rad/s against the
unchanged 0.20 limit. Their fault-stop checks pass. These cases are failures,
even though the margin is small. Source code and gates stayed frozen throughout
the bank. Fresh layouts remain unopened; one draft fresh configuration also
fails the new preflight because its material factors are unsupported by the
retained domain implementation.

The earlier V1/V2 failures are retained. V1 missed dim pixels; V2 could detect
a floor reflection while the direct marker was outside the camera view. V3
therefore changes the sensor-task fixture explicitly, without widening the
detector or motor acceptance thresholds. All 484 compiled ndarray fields were
compared; only reflectance changed. This does not calibrate camera intrinsics,
support reflective-floor tracking or establish real laser tracking.

## Why physics is the next prerequisite

The original-surface audit gives concrete evidence that a convex collision
shape fills empty CAD cavities at the recorded contact points. It does not
prove global freedom from interference. V58 tested one fixed decomposition
recipe, with 120 seconds per mesh, 480 seconds total generation and 360 seconds
for independent validation. All four exports completed without retry or timeout,
using 64 pieces each. Generation took 152.8 seconds; validation stopped after
23.2 seconds at model compilation.

| Original mesh | Maximum sampled excess material | Frozen limit |
|---|---:|---:|
| Bearing | 0.343 mm | 0.250 mm |
| Neck bracket | 1.150 mm | 0.250 mm |
| Bottom head shell | 2.468 mm | 0.250 mm |
| Jaw | 1.066 mm | 0.250 mm |

Bearing part 37 fails the Trimesh convexity check. Separately, MuJoCo reports
too-small volume for part 52, whose stored convex hull has positive volume
of 1.431e-16 m³. These are failed geometry gates, not a simulator
timing or policy-training problem. Removing the troublesome piece, changing
collision exclusions or increasing the hull budget would create a new candidate
and cannot repair this receipt retroactively. The frozen evaluator, partial
report, generated geometry and error log remain preserved. No dynamics ran on
the proxy model. The numbers above describe sampled error, not a global bound.

A separately labeled posthoc check preserves all eight original cavity-point
witnesses in the generated convex unions. This supports decomposition as a
way to address the identified cavity mechanism, but does not erase the material
errors or supply the missing compiled-model tests. All 31 closure artifacts,
five frozen implementation bindings and ten protocol inputs verify.

## Reassessed order

1. **Make one cavity-preserving collision representation compile and satisfy
   the existing geometry checks.** Start with the isolated bearing and its
   source CAD, checking compiler-compatible volume and convexity before
   assembly. Keep geometry validation available when compilation fails. A
   separately versioned compiler probe can test per-mesh shell inertia on
   unchanged V58 vertices, requiring exact body/actuator arrays; that would
   preserve V58's rejection. All four native warnings identify forced merging
   at the 64-hull cap, so a subsequent bounded 64-to-256 cap comparison is a
   justified hypothesis, not an assured fix. Freeze that candidate separately
   and rerun the fixed material, cavity, collision-pair and 201-pose
   checks. Passing those permits separately frozen passive and action-frozen
   dynamic/load probes; it does not establish physical calibration.
2. **Close runtime startup and transport conformance.** Implement the
   documented adapter against the actual BAM evaluator, preserving the exact
   retained actor outputs, command routing, motor/sensor delay state and
   post-step loads. Diagnose HOME_RAMP before another full walk/turn/stop
   rehearsal. The existing inference/component replay does not test this
   integration.
3. **Improve the useful sensor capability within its exposed flat envelope.**
   Isolate the first clipping event at 1.6 seconds and camera pose during
   stop/reacquisition, one property group at a time. Freeze a candidate and
   require all 16 development cases and both negative controls before opening
   new layouts. This can continue as scoped development while full model
   admission remains blocked.
4. **Resume learning and recovery only after their prerequisites pass.**
   The prepared posture ablation needs a source-bound all-case feasibility
   witness. Recovery needs an admitted actor/model, a sitting endpoint and
   continuous-state seated-to-stand comparisons before other fallen starts.
   Broader terrain and carpet families follow retained walking/stop/endurance
   success and verified parameter coverage. Public data remains useful for
   bounded priors, with physical calibration separately unresolved.

The next single active milestone is collision geometry. The other results
define concrete follow-on work rather than completed skill-library acceptance.

## Verification and cleanup

The fast workspace suite passes all 141 tests. The posture/compute focused
suite passes 10 tests (seven overlap the workspace suite); pixel following
passes 14 focused tests and recovery passes 16 synthetic protocol tests.
Independent receipt checks cover the action/load counts above, exact runtime
and adapter reconstruction, source bindings and geometry artifacts. None of
these tooling checks is a behavior or physical-calibration pass.

The final `duck status` projection still reports 24 inspection errors for
older V54/V55 records because the workspace viewer does not serve symlinked
evidence. That existing viewer limitation remains open; direct experiment
receipt verification above is separate from viewer inspection.

Local simulation and training entrypoints were serialized. The advisory
inventory at 2026-09-16 00:43 UTC contains no recognized compute processes;
that inventory does not cover arbitrary launchers or remote jobs. No Brev
resource was created or used. Training drafts remain unlaunched, and no hardware
or policy activation occurred. Existing workspace edits and historical results
remain preserved.

## Evidence links

- [Upstream contact/runtime source audit](../../experiments/walking/upstream-audit-v56/README.md).
- [Full-CAD copied-pose audit](../../experiments/walking/contact-reconciliation-v57/README.md)
  and [original-surface cavity audit](../../experiments/walking/contact-reconciliation-v57/cavity-audit/README.md).
- [V58 failed proxy experiment](../../experiments/walking/contact-reconciliation-v57/proxy-experiment-v58/README.md).
- [Standing feasibility and unlaunched training decision](../../experiments/walking/POSTURE-FEASIBILITY-RESULTS-v56.md).
- [Runtime results](../../experiments/runtime-rehearsal-v1/RESULTS.md) and
  [corrected transport contract](../../experiments/runtime-rehearsal-v1/ADAPTER_CONTRACT-v2.md).
- [Pixel-following bank](../../receipts/visual-follow/20260915-v3-development/bank.json).
- [Pixel-following results and failed cases](../../experiments/visual-follow-v1/RESULTS.md)
  and [independent RGB/ONNX verification](../../outputs/visual-follow-20260915/development-verification.json).
- [Recovery readiness](../../experiments/recovery-readiness-v1/README.md).
- [Terrain generalization strategy](TERRAIN_GENERALIZATION.md).

The ordered queue remains `TRAINING_ACTUALIZATION.md`; `GOAL.md` summarizes
current status. Completed infrastructure checks do not substitute for the
mandatory behavior acceptance matrix or measurement-based physical calibration.
