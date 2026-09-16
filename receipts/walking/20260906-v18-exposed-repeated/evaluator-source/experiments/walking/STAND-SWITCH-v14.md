# V14: separate standing and walking, with load-based body-bracing rejection

Visible development only. No physical authority, policy activation or new
training. V13 FINAL completes 18,432,000 transitions, but its controller result
is 20/21: long-delay fast forward falls at 14.98 s after the stop at 13 s.
Its exact-action, bit-identical native replay additionally reveals sustained
internal leg/battery loading at stop, despite <1-mm geometric penetration.
Moving intervals in three measured cases have zero internal load. This is a
reward/evaluation blind spot; it does not alone establish the cause of the fall.
The old reward counts Genesis self contacts over 10 N; native summed contact
forces are not equivalent to Genesis contact-manifold counts.

## Single intervention

Use the exact first-party V5 FINAL actor for exactly zero user commands, and
V13 FINAL for nonzero commands. V5 is a diagnostic standing component, not an
accepted walking policy: three replayed cases showed zero self-load, but its
old full task result was poor. There is no search over checkpoints. Fixed V12
IMU heading command feedback remains unchanged. Select on command alone, never
case identity, time, simulator state or future commands. Preserve the previous
raw action across switching and send the selected actor output unfiltered at
scale one. No blending, IK, target offsets, gain or model changes. Keep all
61D/14D observation/action, contact-v11 geometry, BAM and timing semantics.

Walking checkpoint: f31d47a5343b1283a1bbd28c2f7efb78f95ddd6940554b9c755b73d337c2b7f8

Standing checkpoint: 19fef3b5d443001f817169cecc660a2bef51b34791b5d84dfa59cc4e619a43c1

## Additive acceptance, frozen before the pair is run

All original motor, posture, heading, geometry and completeness gates remain.
Additionally record applied self-contact normal force after EVERY native
5-ms step, without forwarding or changing physical data. Sum positive contact
normal forces across internal geometry pairs. Reject >1 N total internal load
for more than 50 ms continuously OR more than 1% of the full 18-s schedule.
Require all 3,600 ordered samples, finite nonnegative loads and the full stop.
Missing or terminal-prefix evidence cannot pass. This is a conservative
simulation design rule against using unintended body contacts for support,
not a calibrated hardware damage or force threshold. Intentional foot-floor
loads are excluded. Initial settling, acceleration and braking are included.

First score unchanged V13 plus its heading controller under this additive
gate as baseline; then score the fixed pair on the same complete 21-case
tracking suite. Retain exact ONNXs, float32 actions, source bindings, per-step
load data and videos. Test routing and fail-closed loads before freezing.
If any required case fails, reject the pair and diagnose the first transition;
do not change thresholds or cherry-pick a better checkpoint. No fresh bank or
pursuit integration until all current composite cases pass. A later fresh bank
must include unseen commands/headings and repeated start/stop transitions.
