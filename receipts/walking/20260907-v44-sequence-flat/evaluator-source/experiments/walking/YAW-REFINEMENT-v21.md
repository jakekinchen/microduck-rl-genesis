# V21: reduce instantaneous yaw error under persistent delays

Preregistered before training. V20 reproduces V19's two residual failures in
Genesis CPU with exactly matched paired actors and checked timing histories:
long forward20 .23446 rad/s, long arc-right .20235, nominal forward20 .17279.
Native counterparts are .21639, .20257 and a passing nominal control. Small
signed biases and large oscillatory error support a bounded objective trial;
this does not establish physics equivalence or a unique causal mechanism.

Change exactly one objective component: add -2 * max(abs(body yaw rate minus
requested yaw rate) - .05, 0) / .20 * dt for nonzero twist. This doubles V5's
instantaneous yaw coefficient during movement. Preserve all V18 positive
rewards, posture and internal-load conditions, negative costs, commands,
termination, raw 14D servo deltas, 61D observation, model and BAM. No new
filter, reference trajectory, action correction or motion assistance.

Initialize from exact V18 FINAL249 checkpoint, reset optimizer/iteration,
learning rate 2e-4, seed 26090621. First 64 environments x 5 iterations =
7,680 transitions; require finite rewards, actions, parameters and internal
loads, neutral pose commands, expected timing bounds and all sources matching.
Then one 1024 x 250 x 24 = 6,144,000-transition Metal/MPS run. Only FINAL249 is
eligible. No extension, intermediate checkpoint selection or weight sweep.
Preserve permanent stdout, configs, package/source hashes, complete checkpoints,
TensorBoard and a terminal record. Stop for numerical failures/source drift.

Evaluation is the exact V15 FINAL standing actor, V16 ramp and V19 outer heading
servo, all fixed before training. Evaluate all original 21 and already exposed
42 repeated windows with unchanged task/motor/head/heading/self-contact and
200-Hz applied internal-load gates; include every missing case in the failure
denominator. ONNX must match Torch on random and actual observations. Score
original user commands; preserve continuous physical and controller histories
across repeated windows. Retain actions, observations, torques, contacts and
actual videos. Require all 63 before opening a separately frozen NEW exposed
development bank; the protected final bank stays closed. Any failed required
case rejects this candidate and calls for diagnosis, not an automatic PPO rerun.

Six-part validation plan:

1. Envelope: existing flat-floor forward .08..22 m/s, turns/arcs up to .75
   rad/s, STOP and restart; motor delays 0..30 ms at 5-ms resolution, independent
   gyro/gravity/joint-velocity delays 0..20 ms. External orientation is required
   by the heading controller; this is not camera-derived or privileged-free.
2. Independent acceptance: unchanged 21+42 exposed gates, gait/contact/load
   audits, negative-control evaluator tests and source/parity checks. Longer
   endurance, disturbances, dropouts/cancel and composition remain unachieved.
3. DR: episode-persistent timing only, as V18. Record actual lag vectors and
   joint-factor counts before/after training; require legal actual values.
   Existing episode/reset tests verify constant lags and no historical leakage.
   This does not claim materialized friction/mass/COM/terrain/sensor-noise DR.
4. Generalization: original and consumed repeated banks are regression, not
   unseen families. Preregister combined physics/terrain and repeated endurance
   development after 63/63; protect final families from feedback. Report each
   bucket and missing repeat. Library admission remains blocked until complete.
5. Physics: retain complete-v11 active collision geometry, BAM, masses, inertia,
   constraints, 5-ms/20-ms clocks and actual substep telemetry. V20 is cross-engine
   diagnostic evidence only. Measurement-based held-out calibration is missing,
   remains a physical-accuracy blocker and is not replaced by simulated scores.
6. Reproducibility: source/evaluator/policy/suite hashes, fixed final selection,
   seeds, materialized timing values, successful and failed traces, stdout and
   videos. No hardware, paid compute, publication, activation or library claim.
