# Additive heading-fidelity development protocol

Declared before inspecting any v8 candidate. This is an exposed regression
arising from the already-observed v5 slow-forward drift of about 35 degrees;
it is not a hidden or fresh generalization test and does not replace any old
motor, posture, timing or contact threshold.

For every complete 50-Hz case, use the same 2..13-second motion window and
the actual trunk +X horizontal heading from its unit body quaternion. Unwrap
the measured heading, subtract its value at t=2, and compare it with the
integrated requested planar yaw command over the same timestamps. Require
absolute endpoint error <=15 degrees and maximum phase error <=20 degrees.
These are engineering development tolerances, not measured hardware accuracy.
They reject persistent drift that an average yaw-rate error alone can accept.

Require all 551 frames, finite poses/commands, unit quaternions and a reliable
horizontal projection; missing evidence fails closed. Do not infer measured
heading by integrating gyro data. Keep planar heading intent distinct from
body-axis instantaneous gyro rate, especially while leaning. This requirement
is additive to the existing battery, not a reinterpretation of its scores.

Apply first to retained v5 as an exposed diagnostic baseline, then separately
report v6/v8 finals. It cannot be used to select an intermediate checkpoint or
change the frozen training plan. A policy is not called properly directional
walking merely because its old per-case yaw-rate gate passes. No physical
transfer, calibrated IMU yaw or laser navigation authority follows.
