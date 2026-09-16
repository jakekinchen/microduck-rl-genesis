# Native-contact walking v6

V5 final completed 18,432,000 new transitions. It passes 6/21 old regression,
5/21 v5-heading legacy-clock cases, and 6/21 corrected-current-sensor cases.
Head posture passes 21/21 in each. Joint-stop parking, torque and loaded-slip
failures are absent. Remaining corrected-sensor failures: yaw 15, stop tilt 5,
and one zero-lag right turn without useful bilateral steps. No full acceptance.
Its final, not checkpoint150, is the initialization. Preserve all negatives.

The only active intervention is the independently diagnosed native contact
default: Genesis constraint_timeconst 0.01 -> 0.02 seconds. Runtime readback
matches the reference floor/foot solver parameters. The prior byte-identical
action replay reduced first-impact load error from 27.68 N to about 0.62 N,
and root difference from 0.95 mm to 0.049 mm. It did NOT establish full dynamic
agreement. Do not adopt the separately tested broad solver-compatibility flags;
they did not fix five-second divergence. No fitting of mass, inertia, geometry,
servo law or policy actions to an outcome.

Use existing MicroduckContactTrackingWalkingEnv. Tests prove that its scene
adds only the native 20-ms constraint default and that every reward, observation,
action, timing-randomization and reset function is identical to v5. All v5
objectives remain fixed. In particular do not add a hip/tilt reward in response
to the now-repaired checkpoint150 shortcut, and do not force exact HOME leg
targets: a fixed HOME diagnostic tips forward, whereas v3/v5 can balance.

Initialize actor and critic only from retained v5 FINAL model_749.pt, SHA256
`19fef3b5d443001f817169cecc660a2bef51b34791b5d84dfa59cc4e619a43c1`.
Optimizer and iteration reset as in the preceding intervention. Same 5e-4
adaptive learning-rate initial setting, seed 26090516, 61D/14D/50Hz unfiltered
normalized ONNX interface, 200-Hz BAM. Nominal rigid model plus unchanged
inherited battery/drop and timing variation. No paid compute or hardware.

Run local 64x5 smoke first, then at most 1024x1500x24 = 36,864,000 new
transitions. The larger bounded consolidation run is deliberate: v5's final
repaired the early checkpoint's hip-stop shortcut. Preserve source for the
whole run and retain terminal counts, all checkpoints, logs and tests. The
declared final checkpoint alone is eligible; intermediate diagnostics can stop
a clearly degenerate run but cannot be selected or used to rewrite this plan.

Reuse the three independently frozen **visible development** protocols:
evaluate_walking_posture.py (original headings, legacy sensor clock),
evaluate_walking_tracking.py (v5 headings, legacy sensor clock), and
evaluate_walking_sensor.py (v5 headings, copied-current-state IMU). Their
numerical thresholds and source remain unchanged. These banks are now exposed;
do not call them fresh, reserved or hidden tests for v6. Require all 21 in each,
full-CAD body-clearance audit, actual slow-motion video and normalized-action
parity. Passing sampled training rewards or one nominal speed is not acceptance.
Only after full visible passes may a separately frozen new generalization bank
be opened. Physical transfer and calibrated contact/latency remain unproved.

If the final still fails, compare the first residual failures against v5 in
both engines. A separate untested timing concern is that motor lag changes
every 64 physics ticks and IMU delays every 64 control ticks during training,
while evaluation holds a device profile constant. Do not change that here or
claim it caused a failure without a scoped diagnostic. Preserve one active
intervention and update GOAL.md and TRAINING_ACTUALIZATION.md in this task.
