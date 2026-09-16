# V47: matched downhill and flat stopping diagnosis

Run original V21/V15 and V46/V15, with fixed V16/V30 command control, on the
two original 36-second downhill sessions and their matched flat counterparts.
Only terrain changes in each match; commands, start orientations, seeds,
six motor ticks, one sensor tick and all physics settings/gates stay fixed.
These eight sessions are exposed diagnosis, not generalization or promotion.

Retain complete MjData, actual joint damping/friction, BAM state, motor FIFO,
sensor history, last action, command ramp and heading-controller history just
before braking (13.00 s) and just before the first standing action (13.14 s).
Capture only reads/copies state; it does not forward or reset the live world.
Verify decoded states against recorded subsequent raw actions, observations and
physical poses before using the state bank for further work. Reproduce original
downhill action tensors and numeric poses against their retained receipts.

Inspect yaw, posture, support/slip, internal loads and FIFO/actor discontinuity
around the handoff. An actor label at the fall alone does not establish cause.
Do not repair or suppress failed cases. Full-duration, whole-session heading,
posture, torque, actual joint margin/occupancy, gait and all body/load checks
remain independent. Any missing restart window after a fall remains a failure.

Use the result to choose one bounded retention-constrained correction. Preserve
63/63 flat, both 180-second compositions and all five passing exposed surfaces;
require both downhill sessions before opening a fresh sequence bank. No hardware,
paid compute, policy activation, carpet transfer or calibrated-physics claim.
