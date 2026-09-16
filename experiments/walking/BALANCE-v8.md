# Balanced-trunk walking v8 — conditional next intervention

Prepared during the still-running v6 trial. Do not start v8 until v6 has a
terminal retained record and its final candidate has been evaluated. If v6
already satisfies the full frozen protocols, this intervention is unnecessary.
No intermediate v6 checkpoint may be selected as the initializer.

Activation evidence (v6 now completed): 36,864,000 new transitions, retained
final model_1499.pt SHA256
`0f0cad5839cf22c492e69dfd1d1e41c26ce430a0363018bf5fa13faf6333afba`.
All three complete exposed protocols are 0/21. Current-sensor failures:
20 stopping-tilt failures, seven yaw-rate failures, and one long-delay fast-
forward fall with insufficient duration/actual joint margin. Legacy new
headings also include a long-delay arc fall, with one terminal full-CAD jaw
penetration. No omitted-body support is accepted. All negatives are retained.
The separate Genesis final probe also stops leaning 26–31 degrees. Two scoped
native reduced/full-collision action replays have identical qpos. The evidence
supports the planned reward-only trunk-balance correction; it does not prove
that it will repair long-delay fast walking or cumulative heading. Keep those
as required independent failures, not excuses to add more changes to v8.

## Mechanism and hypothesis

V6's four current-sensor checkpoint750 diagnostics pass motion, yaw, bilateral
stepping, contact-slip and actual-motor gates, but all stops lean 30–34 degrees
(fixed allowed maximum 15 degrees). Checkpoint500 leaned 26–29 degrees. This
is not the old v5 intermediate joint-stop shortcut: actual joint boundaries
are separate gates and generally remain unoccupied. Preserve both diagnoses.

The inherited upright reward is a bounded Gaussian, only 2 reward units/s
at perfect upright and almost zero by 30 degrees. Quiet zero-command velocity
tracking can still pay up to 11 units/s. Thus a quiet, deeply leaning stance
can retain most of its tracking return. These reward bounds demonstrate an
objective trade-off; they do not prove why a particular neural weight changed.

V8 changes exactly one property group: trunk balance in the reward. Add
`-20 * max(tilt_radians - radians(10), 0) * dt`, using current projected gravity
and `atan2(norm(g_xy), -g_z)` over all commands. The 10-degree free region permits
ordinary sway/lean without requiring exact HOME joint targets. Additional cost
is 1.7453 units/s at 15 degrees, 6.9813 at 30, and continues growing. All old
rewards remain, including neutral-head, command-error, landing duration,
substep effort and stopping speed. Do not change body mass, contact solver,
terminations, timing randomization, exploration distribution or normalization.
No IK, deployment noise, mirroring/averaging or action filtering.

## Conditional run contract

Initialize actor and critic only from the retained v6 **final** checkpoint,
after verifying its terminal training record, checkpoint/source digests and
complete negative/partial evaluation. Bind the exact initialization digest to
the new run record before learning. Reset optimizer and iteration, preserve
the 5e-4 adaptive initial learning rate. Seed 26090518. Local Apple Metal/MPS,
64x5 smoke then at most 1024x1000x24 = 24,576,000 new transitions. Source-bind
this plan, all parent source, the new environment, tests and trainer. Only
declared final model_999.pt can be the new candidate. Intermediates diagnose
only; a clearly degenerate run may be stopped and retained, not promoted.

## Acceptance and boundary

Reuse the three frozen exposed visible 21-case protocols unchanged: original
heading/legacy clock, v5 heading/legacy clock, and v5 heading/current clock.
Require all cases, all additive posture gates, actual video/slow motion,
full-CAD body clearance and normalized ONNX parity. Compare residual errors
in Genesis and native MuJoCo before any further intervention. Training scores
are not acceptance, and these now-exposed banks are not hidden generalization.
Separately report the additive exposed `HEADING-v1.md` check, declared before
any v8 candidate. Its cumulative-heading limits are also required before
calling the result properly directional walking; preserve old scores verbatim.
Only after full visible passes may a separately frozen fresh bank be opened.
Physical transfer, calibrated timing/contact and vision-based laser tracking
remain separate. Update the single task's GOAL and ordered queue; no agents,
roles, paid compute, hardware, publication or external contacts.
