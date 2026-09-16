# Controlled walking with neutral head command v3

V2 is stopped, not accepted. Checkpoint250 fixes nominal motor saturation
(7.6% → 0.04%), slip, qualifying swing duration (0.10 → 0.16 s) and stop speed
(0.090 → 0.0019 m/s), but still drifts. Zero-lag turning does not turn/step.
Video plus qpos audit exposes another unacceptable workaround: mean neck
command error about -88 degrees, face pitch about -83 degrees. The HOME model
itself renders correctly. The learned posture, not the renderer, is wrong.

The inherited head reward averages four Gaussian joint scores. Sacrificing one
joint costs only one quarter of its bounded reward; large errors lie in its
flat tail. Add one non-saturating objective: -6/s times the SUM of each head
joint's absolute command error beyond 0.20 rad. Preserve v2's effort, stepping,
stopping, command mix, all model parameters and unfiltered 61D/14D interface.
This does not pin the head kinematically or inject a corrective action.

Keep suite-v1 and the old motor evaluator byte-identical. A separately frozen
additive posture evaluator calls every old motor gate, then also requires:

- Maximum over the four per-joint mean absolute neutral-command errors ≤0.35 rad.
- 95th percentile of the worst per-frame head-joint error ≤45 degrees.
- Mean absolute physical face pitch ≤30 degrees.

Score from 1 s through the final stop. Missing qpos/face vectors fail closed.
These broad visible-development tolerances distinguish ordinary head motion
from a persistently folded neck; they are not hardware calibration. Existing
negative policies must fail the new checks; no old threshold is relaxed.

Warm-start actor/critic only from explicitly identified v2 diagnostic checkpoint250
`1742d3b4dccc12a6437158ade211984a4282b7339f9a32ef1216acdfb69ab4c6`.
Initialization only, not a selected policy. Reset optimizer and iteration.
Seed 26090513. Local 64×5 smoke then at most 1,024×750×24 = 18,432,000 new
transitions. Final-only candidate; intermediate failure diagnostics cannot be
promoted. Retain interrupted attempts and their exact source/weight lineage.

Train/evaluate command-only proper walking before pursuit. No new agents,
paid compute, third-party policy execution, publication, activation or hardware.
BAM still samples 6.5–8.2 V and 0–0.2 ohm drop in training; native nominal
is 7.35 V / zero drop. Reserved and canonical held-out banks remain unopened.
