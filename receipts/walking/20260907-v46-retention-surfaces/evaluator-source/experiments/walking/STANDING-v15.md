# V15: learn upright unbraced standing without retraining walking

V14 fixed V5-standing/V13-walking pair completes all21 cases, with zero
applied self-contact load across75,600 physics samples, no falls, and heading,
geometry and head gates21/21. Combined13/21: eight settled stops tilt15.0712
to16.5418degrees beyond the unchanged15-degree limit. Walking, stepping, slip,
actual joints, torque and speed/yaw settling otherwise pass. This localizes
the remaining failure to standing posture. Full original ONNX videos retained
at `receipts/walking/20260906-v14-standing-pair/`.

## One bounded standing specialization

Keep V13 FINAL walking weights, V12 IMU heading command controller and V14
exact-zero command switch fixed. Train only a new standing actor from V5 FINAL
`19fef3b5d443001f817169cecc660a2bef51b34791b5d84dfa59cc4e619a43c1`.
Use V13 complete-contact model, persistent0..6 motor/0..1 sensor delays,
unchanged BAM, unfiltered scale-one61D/14D interface and reset population.
Velocity, head and body commands are always zero. No phase clock, simulator
state, blending, offset or privileged reset is added to deployment.

Use the inherited V9 objective, including its explicit non-saturating trunk
lean penalty above10degrees and posture-conditioned positive return. Add
internal-force rejection to prevent recovering upright reward by body bracing:
sum valid Genesis self-contact `force_a` vector magnitudes. Above0.5N, multiply
the surviving posture-gated positive return by exp(-((force-0.5)/0.5)^2), and
retain every old penalty plus -2*(force-0.5) N-scaled rate cost. This is a
50-Hz training diagnostic/reward from the last physics substep, not the native
200-Hz normal-force measure, contact-manifold equivalence or hardware calibration.

Seed26090615. Initial LR2e-4, otherwise unchanged PPO defaults. First64x5
smoke (7,680 transitions), then exactly1024x250 (6,144,000 transitions) if
finite and command/reward/contract checks pass. Actor and critic initialization
only, no prior optimizer/iteration. Only declared FINAL model249 is eligible;
intermediates are diagnosis, not fallback selection. No new paid resources.

Standing training starts from the unchanged nominal HOME reset distribution;
this does not establish transition coverage. The independent native evaluation
must test the pair's full stand/walk/stop sequence without reset or action-history
clearing at either switch. Preserve V14 motor/posture/heading/geometry/load gates
and all21 original command/timing cases. Freeze evaluator before learning.
Reject any regression. Only after a full current composite pass, freeze fresh
commands/headings/timing combinations and repeated start/stop sequences for
the unchanged pair. No hidden-bank opening, pursuit integration, activation or
physical transfer follows from a training score or the current bank alone.
