# V12: explicit heading command feedback on corrected contact physics

V11's model-only closed-loop baseline changes the decision: the retained v9
FINAL actor now finishes all 21 current-sensor cases without falls, normal
head/stopping and no >1-mm self-penetration. Motor/posture is 17/21. Four
long-delay yaw-rate failures and cumulative heading drift leave only 6/21
combined passes. Unlike replaying fixed actions, the actor can react to the
new collisions. No v11 training has started; its bounded trial remains unused.
Actual nominal slow-forward footage shows alternating lifted feet and normal
head posture. This is partial simulated behavior, not calibrated gait quality.

## One intervention: an explicit upstream command controller

Keep exact v9 FINAL weights, normalized 61D -> 14D actor, unfiltered motor
actions, complete-contact-v11 model, BAM, timing and all evaluation thresholds.
Integrate the user's requested yaw velocity into a desired heading. Compare
with the IMU's horizontal orientation estimate, using the same 0/20-ms sensor
FIFO as the actor. Add 2/s times heading error to the ordinary policy yaw
command, capped at +/-0.25 rad/s correction and +/-0.75 total. Translational
commands are untouched. Stop commands are exactly zero and clear the heading
reference; no deferred turn after a stop. Reset state at each new episode.

The 0.5-s nominal proportional timescale is ten times the maximum 50-ms
combined modeled motor/sensor lag. These constants are frozen before the
first controller rollout, not selected from a parameter sweep. No command
uses ground-truth position, target location, joint assistance or future state.
Malformed orientation/command evidence aborts the diagnostic, never a pass.

This is **not improved raw-policy tracking**. It versions the surrounding
controller and explicitly needs a validated IMU orientation estimate outside
the actor's existing 61D input. The simulator supplies that IMU reading; no
real hardware IMU calibration or yaw-drift guarantee is claimed. Record both
requested and policy commands, orientation source/delay, reference/error and
unchanged raw ONNX actions. Score against the USER command, not the correction.

## Frozen decision

Require unit tests and the complete 21-case current-sensor v11 battery:
all earlier motor/head, heading and self-contact gates, unchanged limits.
No hidden suite, physical run, action filter, training or policy activation.
If all exposed cases pass, freeze a fresh development start-heading/command
bank before reintroducing laser pursuit. Also inspect actual step and stop
video and retained motor/contact traces. Old raw-policy scores stay unchanged;
do not call an upstream-servo result an unassisted actor pass.
