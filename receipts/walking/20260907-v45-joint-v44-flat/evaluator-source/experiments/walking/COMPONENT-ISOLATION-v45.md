# V45: isolate V44 walker, stander and their interaction

Freeze before any mixed-pair rollout. Compare exactly four pairs: original
V21/V15, joint V44 FINAL499, V44 walker/V15 stander, V21 walker/V44 stander.
No learned parameters, observation normalization, runtime physics, original
V16 ramp/V30 heading controller or action filtering changes. Preserve the
61D/14D ABI, native contact-v11 model, pinned BAM and 200/50-Hz rates.

Each pair runs the same six independent sessions: original flat nominal-delay
forward-08, original zero-delay forward-08, both original +/-initial-yaw downhill
starts, and both original 180-second compositions. The two selected flat cases
retain their original 18-second windows and seeds. The four diagnostic sessions
retain every original window, threshold and initial state. No reset within a
session; terminate on fall, mark all later windows unrun failures. This is exposed
diagnosis and cannot establish a new terrain or physical capability.

Use all original reward-independent task, joint-margin/occupancy, bilateral gait,
loaded slip, nonfoot support, torque, posture, heading, body penetration and
200-Hz internal-load checks. Compare each required component and session; an
aggregate score cannot substitute for a failed component. Verify original and
joint control action-array bytes and numeric poses against retained receipts.
A mismatch is a harness/replication failure, not policy improvement.

Predeclared interpretation: a regression reproduced by new-walker/original-stander
is attributable to replacing the walking component in this tested pair, including
its endogenous incoming/outgoing state effects. Apply the symmetric rule to the
standing component. Failure only with both replacements indicates an interaction
on these cases. A mixed pair passing the small bank still requires all original
63 flat and remaining surfaces before any broader claim. Where both mixed pairs
fail, retain both component concerns; do not declare one innocent from averages.

After review, use the findings to select at most one bounded correction or a more
specific diagnosis. Do not resume unrestricted joint PPO or open the V44 fresh
sequence/protected terrain banks. Ducky calibration and carpet transfer remain
unmet. No hardware, paid compute, publication or activation.
