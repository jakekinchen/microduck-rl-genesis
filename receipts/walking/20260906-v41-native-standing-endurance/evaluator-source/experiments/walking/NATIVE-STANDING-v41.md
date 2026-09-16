# V41 focused native standing refinement

The V31–V40 comparison narrows geometry/import and algorithm discrepancies but
does not close the five-prefix surface-conformance gate. V38 slower STOP slew
prevents the two downhill falls but fails other gates and introduces composition
falls; reject that controller. Keep original V30 command behavior and V21 walker.

Train only the V15 standing actor in the native C MuJoCo/BAM lane. This explicitly
changes the development training backend and objective; it does not certify the
Genesis lane or original-model physical transfer. No new broad surface training.
Use complete-contact-v11 geometry, original native detector, 5-ms physics,
four-tick held actions, 61D observation and 14D action order. No action filtering.
Use a cold 61D critic; load only the exact V15 FINAL actor and its normalizer.

Build a deterministic exposed handoff bank with original V21/V15/V30 policies:
flat forward .10/.20, flat turns ±.60, flat arcs .12/±.35, downhill +3° and uphill
−3° forward .12. Use yaw zero, motor lag six ticks and sensor lag one tick.
Run original controls (standing 0–1 s, moving 1–13 s, STOP afterwards) and capture
the complete native state immediately before the first standing action after
motion. Also retain ordinary initial HOME states for each model. If a source
falls before a handoff, report and exclude it; require both slope templates and
at least six complete handoffs. Preserve input action hashes and snapshot data.

Every training environment owns a separate model/data/BAM controller. Reset by
copying the entire native MjData plus mutated joint damping/friction, motor FIFO,
previous motor torque, controller timestamp and sensor FIFO. Never reset the
base alone. Verify an original-state continuation repeats exactly after reset.
Choose a handoff half the time and HOME half the time; uniform template choices.
Each episode is three seconds of exact zero commands. No randomization is claimed
beyond applied initial-state/terrain choices. Record reset counts and loads.

Preregister reward: positive 4/s times speed/upright/head-pose exponentials;
penalize actual internal loading above .5 N (2 per N/s), joint margins below
.04 rad (10/s), action-rate squared (.1/s), and terminal fall (8). This reward
does not replace any independent gait, posture, heading, torque or load gate.

Bounded seed 26090641: smoke 8 environments ×5 iterations, then at most one
64×250 run (384,000 transitions). PPO 24 steps/iteration, initial LR 1e-4,
original actor architecture and optimizer settings otherwise; FINAL249 only.
Run time/space checks before the full run. No checkpoint search or extension.

Freeze the original downhill/composition, 21+42 flat and 14-surface evaluators
before learning. A candidate must preserve all 63 flat and both long compositions
and improve the targeted stop gates before a fresh terrain bank is evaluated.
If it fails, retain the negative and do not expand training or label carpet-ready.
Any matched-physics/public-data/calibration gaps remain explicit blockers.
