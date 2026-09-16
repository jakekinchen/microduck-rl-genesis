# V16 diagnostic: policy handoff command dynamics

V15 final passes the original 21 cases, but fresh development is 33/42.
Four first-cycle fast-forward stops fall; four subsequent windows are not
run after those terminal falls. One second-cycle turn has sustained internal
loading during startup (1.615–2.09 s), not at stop. Standing-only HOME
training does not establish arbitrary moving-to-standing recovery or stable
standing-to-walking transitions. No walking acceptance is declared.

Before another training intervention, isolate command-transition dynamics:
use the same exact V13 walking and V15 standing ONNX pair, complete-contact
model, BAM, sensor timing, heading servo and raw actions. Add a command-only
rate limiter, 0.75 m/s squared on each translational axis and 2.5 rad/s squared
on yaw, at the same 50 Hz. Max trained .22 m/s / .75 rad/s commands ramp in
about 0.3 s. Rate-limit all changes, not a case-specific stop schedule. Route
exactly zero ramped commands to standing and nonzero ramped commands to
walking. No blending, post-policy filtering, hidden simulator state or model
change. Evaluate against original USER commands; retain routed and corrected
policy commands separately.

Predeclared diagnostic population: two consecutive unchanged 18-s windows
for each of motor10/sensor20 forward211, motor15/sensor0 forward201 and
motor15/sensor0 turn-right380 from the newly exposed fresh suite. Every old
motor/head/heading/geometry/load limit remains unchanged. Retain all six
outcomes, actions and videos, including missing windows after falls. This
tests the handoff hypothesis; it is not full-bank acceptance. Freeze exact
sources and these inputs before the first ramped rollout. If useful, require
all 21+42 exposed cases and separately new development before promotion.
