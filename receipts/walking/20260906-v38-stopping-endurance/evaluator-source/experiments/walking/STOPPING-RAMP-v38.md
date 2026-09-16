# V38 downhill stopping intervention

The retained V30 downhill stop at 13 s reaches the standing actor at 13.16 s
while carrying forward momentum and descending into one-foot support. Test one
command property: reduce X/Y slew rates to 0.25 m/s² only when the requested
three-axis command is exactly zero. Preserve 0.75 m/s² acceleration, all moving
command changes and 2.5 rad/s² yaw slew. Do not blend actors or filter/clip their
actions. Standing still requires the routed command to reach exact zero. The
requested task, timing, physics, V21/V15 actors and V30 heading remain fixed.

Before outcome inspection, freeze the existing two downhill sessions and two
180-second compositions with every original motor/gait/posture/heading,
body-interference and 200-Hz internal-load gate. Then require all 21+42 flat
regressions before any promotion; evaluate all 14 exposed surface sessions.
No reduced stopping threshold or longer task duration is allowed. Keep
compressed raw full-session telemetry and action arrays. Missing windows fail.
Numerical Genesis surface issues remain separate; this is a native command
transition intervention and grants no calibrated or unseen-terrain acceptance.
