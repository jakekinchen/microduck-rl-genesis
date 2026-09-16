# V11: complete body contact before further walking training

## Measured reason

V9 FINAL is rejected. Even the reduced-model passing nominal slow-forward
case intersects the battery: raw watertight CAD triangles cross at 0.90 s
(left leg) and 1.16 s (right leg), not just convex-hull cavity overlap.
Same float32 motor actions fall at 1.94 s in the bundled full-collision model.
The full model also removes reduced support/leg contacts by assigning leg
bit 1 versus support bit 2. Neither is a physically calibrated authority.

Copied identical poses show only one self-contact-pair-presence disagreement
in 2,654 frames between Genesis/reduced native. Raw contact POINT counts are
not contact FRAME counts: MuJoCo often emits four points versus Genesis one.
Disabling Genesis mesh decimation reduces sampled support-surface difference
from at most 0.338 mm to 1.48e-8 m, but does not remove the one pair-presence
disagreement. It is not yet shown to fix dynamic tracking or braking.

## Active intervention: collision coverage only

`collision_model.py` materializes the bundled full model with the support
collision mask changed from 2/2 to 1/1. This retains full-model contacts AND
restores the reduced support/leg contacts. All collision meshes now share the
floor/self-contact bit. Preserve every original model. Prove identical
compiled mass, inertia, joint frames/ranges/order and BAM parameters; visuals
and camera adapter stay unchanged. No invented leg dimensions or balance aid.

Use this same materialized collision model for Genesis and a separately
identified native development lane. Genesis default mesh processing remains
unchanged for this coverage-only intervention; changing decimation requires
its own dynamics diagnostic. Do not infer calibrated fidelity from shared CAD.
Check Genesis neutral-pair filtering explicitly so it cannot silently remove
the newly required battery contacts.

## Before any training

1. Model tests: physical-array identity, preserved reduced/full contact pair
   sets, all intended body-floor colliders present, HOME self-contact state,
   exact raw-CAD witness poses detected. No writes to canonical assets.
2. Compare complete-model Genesis/native copied-pose contact presence and
   replay the same retained raw actions. A negative is expected; do not hide it.
3. Add additive all-frame self-penetration rejection at >1 mm, with missing,
   malformed or nonfinite poses unknown/failing. This is a conservative visible
   development geometric rejection, not a calibrated contact-force threshold.
   Keep every old gait/head/heading/stop/joint/torque threshold unchanged.
4. Freeze model/source bytes and explicit initialization/budget before a
   64x5 smoke. No longer run is active or authorized by this draft itself.

After these prerequisites, define the smallest bounded learning run in this
same task. Preserve v9 reward/action/observation/command/timing functions for
the collision-only test. V10 persistent timing is still paused, not silently
combined. Complete current-model and old-model regressions, heading, body-floor
and self-contact checks plus actual video remain mandatory. Final-only
candidate; no held-out, physical, paid-compute or activation authority.

## Prerequisites measured and bounded trial frozen

Six model tests, five additive self-contact tests and three raw-triangle
witness tests pass. V9's entire current-sensor bank fails self-penetration:
0/21. Both complete-model engines detect required battery/leg contacts;
Genesis neutral filtering does not remove them. Contact pair presence differs
in two of 2,654 copied poses, not hundreds of missing-contact frames.
Default processing differs by up to 0.581 mm in sampled support extent on the
additional head geometry; dynamic equivalence is not established.

Same original v9 actions on the complete model make Genesis fall at 1.52 s
slow forward and 1.56 s left turn. Both replays stop at that first engine fall;
native had not yet fallen at those timestamps. This is a negative baseline,
not faithful cross-engine behavior or a claim the native replay completes.
No action has been altered to obtain a better result.

Initialize only from retained v9 FINAL model_749.pt,
`c79e02bc00dabca146b83592582926fc2053114cc5e44cdf822f95aa8ff8fb17`.
Reset optimizer/iteration, retain algorithm and initial learning rate 5e-4.
Seed 26090521. Require complete-model old-policy baseline, source freeze,
tests and a 64x5 smoke. Then at most 1024x750x24 = 18,432,000 new transitions,
final-only model_749.pt. A clearly degenerate run may stop early as a retained
negative, never an intermediate promotion. No reward, timing, action, sensor,
reset or mesh-decimation intervention is combined with collision coverage.
Only collision capacity grows to 120 to accommodate the extra geometries.

The additive native complete-model battery is frozen in
`evaluator-freeze-collision-v11.json` before v11 training. It applies the same
21 current-sensor schedules, earlier motor/head gates, existing heading gates
and the separately defined all-frame 1-mm self-contact rejection. Also require
all three original reduced-model regression protocols and actual video.
