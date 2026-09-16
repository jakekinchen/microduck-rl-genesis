# V29 bounded correction-headroom experiment

V28 restores every original first-window action file exactly, but the second
25-ms motor-delay, .738-rad/s left-turn window ends 15.887 degrees short.
Across its 550 scored samples the policy yaw command is saturated at .75 rad/s
100% of the time; actual mean yaw is .717536 rad/s and mean controller course
error is .486134 rad. This is evidence of insufficient correction headroom.

Test one fixed change: expand the heading controller's total policy yaw command
limit from .75 to .80 rad/s. The requested command envelope stays at .75; heading
gain 2/s, correction limit .25 rad/s, filter .12 s, course establishment/STOP
semantics, actors, motor actions, physics and every test threshold stay fixed.
Keep the original order: constrain correction by the total-command cap before
filtering, then cap the filtered command. This deliberately extrapolates the
actor's yaw-command input by at most .05 rad/s beyond its training range. It is
an explicit local simulation experiment, not hardware or activation authority.

Freeze one candidate and rerun all 21+42 original flat cases and both 180-second
compositions plus the two downhill diagnostics. Accept only the limited heading
improvement if all 63 and both full compositions pass. Keep any failed slope
or surface case and the original V24/V28 negatives. If that condition passes,
compare the fixed original motor pair plus V29 on all 14 public surface sessions.
No additional training, gain search, intermediate selection or relaxed gate.
