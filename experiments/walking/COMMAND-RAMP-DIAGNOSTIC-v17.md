# V17: bounded yaw acceleration diagnostic

V16 fixes four of the six repeated handoff windows that failed or were not run
in V15. It passes 5/6, but repeated right-turn startup still has 245 ms of
continuous internal loading over 1 N. It is rejected, not accepted walking.

Before this run, change only the command yaw slew from 2.5 to .75 rad/s^2:
maximum trained yaw .75 rad/s takes one second to reach. Translational slew
stays .75 m/s^2. Keep the exact V13 walking and V15 standing ONNXs, V12 heading
feedback, robot, BAM and all original gates. Record requested, routed and
actor commands separately; score the user's original commands. No action
blending/filtering, extra observations, privileged-state controller or physics
change. Braking uses the same rates as startup.

Run the same three diagnostic worlds twice continuously: motor10/sensor20
forward211, motor15/sensor0 forward201, motor15/sensor0 turn-right380.
Do not select a checkpoint. If all six pass, evaluate all 21 original and
42 exposed windows before creating any new development bank. If not, retain
the negative and inspect the actual transition-state/action gap rather than
run an unconstrained gain sweep. No physical acceptance follows this test.
