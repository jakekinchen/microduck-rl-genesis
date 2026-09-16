# V19: separate course correction from rapid gait oscillations

V18 FINAL remains rejected: original18/21, exposed repeated41/42. Three
long-delay yaw errors and one startup body-clearance failure remain; all63
avoid falls and sustained internal loading. The unchanged V18 trace analysis
finds mean yaw errors near zero but dominant oscillations at3–6Hz; IMU heading
rate corroborates the motion. The correction is not saturated and correlates
with body yaw. Closed-loop correlation does NOT prove the controller causes it.

Freeze one diagnostic: low-pass only the V12 outer heading CORRECTION at
tau=.12s, applied at50Hz, reset exactly to zero on STOP. Preserve original
reference integration, feed-forward user/ramped twist, correction cap .25,
policy yaw cap .75, V16 slew, V18 FINAL walking, V15 FINAL standing, native
complete V11 model, BAM, sensor FIFO, raw motor actions and all evaluation gates.
This is not gyro feedback, a post-policy filter or a new sensor. Preserve and
record raw/filtered/applied corrections. Existing external IMU requirements
still apply; hardware drift/noise are uncalibrated. No training is requested.

Predeclared diagnostic windows (seven): original long30/sensor20 forward12,
forward20 and arc-right; nominal20/sensor20 forward20; zero-lag turn-left;
exposed motor25/sensor20 arc-left117/448 repeated twice without reset. All four
known residual failures are represented alongside controls. Use original
requested commands and every existing motor/head/heading/geometry/load gate.
Retain every outcome and actual video; a finished process is not a pass.

If all seven pass, require full original21 plus exposed42 before any new
development bank. If any fail, retain the negative and inspect its first
failure before another bounded intervention. No gain sweep, checkpoint search,
model softening, acceptance relaxation, paid compute or hardware activation.
