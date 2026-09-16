# V20: localize the remaining paired-controller yaw residual

Frozen before execution. This is a three-case exposed diagnostic, not a new
candidate, training run, fixed-action causal comparison or acceptance bank.

Use the exact V18 FINAL walking ONNX and V15 FINAL standing ONNX retained in
`20260906-v18-current`, the V16 command ramp and V19 filtered heading servo.
Compare Genesis CPU, one environment, against the already retained V19 native
long-delay forward20, long-delay arc-right and nominal forward20 traces.
Each case is 18 seconds: STOP until 1 s, original command until 13 s, then STOP.
Use the original suite poses and seed, complete contact-v11 geometry, 5-ms
physics, 20-ms actor steps, fixed motor/sensor delays, 7.35 V and zero voltage
drop. No action interpolation, clipping change, reward change or policy update.

Before scoring, assert the actual encoder, gyro, gravity, previous action,
command, neutral pose and IMU history at every actor call. Independently check
every delayed motor target against the native HOME-initialized FIFO. Genesis
training's first-target initialization is explicitly different; initialize the
diagnostic FIFO to HOME after placement, without modifying training sources.
Reset all histories and verify pose, zero velocities/actions, delays and voltage
for every case. Retain raw actions, observations, qpos, substep torque and
Genesis applied internal force magnitudes. These magnitudes are not equivalent
to native contact normal-force sums. Reading contacts must not modify dynamics.

Report original 2..13-s requested-command tracking, planar heading, stopping,
head posture, joint margins and residual spectrum; preserve falls and missing
evidence. Do not call this diagnostic a gait or calibrated-physics pass.
Native gait, geometry and applied-load gates remain authoritative and unchanged.

Decision: if Genesis also exceeds the original .20-rad/s yaw MAE limit in the
failed long-delay buckets, investigate one shared actor/objective deficiency.
If Genesis passes them, localize the physics/actuator discrepancy before further
PPO. Correlation between closed-loop spectra does not establish a cause.

Validation-standard scope: the operating envelope is these three exposed
flat-floor timing cases. Independent metrics are separate from rewards. This
does not add domain randomization or unseen-environment coverage; broader
factor application/reset tests, environment families, repeat/endurance and
continuous-state composition tests remain required before library admission.
Cross-engine diagnostic agreement is not measurement-based calibration.
No hardware data, transfer claim, protected-bank access or policy activation.
Freeze exact source, policy, suite and baseline-manifest hashes; keep stdout,
all case trajectories and terminal status, including exceptions.
