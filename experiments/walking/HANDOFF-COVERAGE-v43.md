# V43 full-state handoff coverage diagnosis

Replay the four exposed V30 and V42 downhill/composition sessions. Preserve
the recorded float32 actions, original command ramp, native complete-contact-v11
physics, BAM, 30-ms motor delay and one-control-tick sensor delay. Require every
recorded pose to reproduce within 1e-10 and every recorded actor input exactly.
Capture complete state before initial standing and every walking-to-standing
switch. Missing switches after a fall remain missing, not successful cases.

Rebuild all eight original training templates from frozen V42 construction code.
Compare actual switch inputs against the 16 HOME/handoff reset inputs using
separate maximum differences in gyro, gravity, joint positions, joint velocities
and previous actions. Also compare complete motor FIFO and sensor history.
These are reset-bank distances, not statistical coverage of PPO trajectories:
the previous runs did not retain every training observation. No arbitrary
distance threshold becomes a generalization or failure-causality claim.

From every captured state, independently test V15 and V42 standing actors for
five seconds with zero commands, unchanged actions and full dynamics. Fork both
from identical MjData, joint friction/damping, BAM state and delay histories.
The original three-second episode horizon is reported alongside the five-second
outcome. Score final two seconds: speed <= .04 m/s, yaw <= .15 rad/s, tilt <=15°,
existing independent head-pose limits; entire branch: no falls/nonfoot support,
joint margin >= .02 rad, torque saturation <= .02, existing body interference
and 200-Hz internal loading gates. Report loaded-foot slip separately. These
branch diagnostics do not replace walking, transitions or full-session gates.

Serialize complete trusted local snapshots and validate disk round-trip and
cross-world continuation with the same action. Check hashes before deserializing.
Retain the complete source/model identities, original action prefixes, case
denominators, per-branch trajectories and all failures. MuJoCo state and copying:
https://mujoco.readthedocs.io/en/stable/python.html
https://mujoco.readthedocs.io/en/stable/computation/index.html#the-state

Choose any subsequent single bounded refinement only after this diagnosis.
Keep V30 retained. All old 63 flat, both long composition and slope/surface
requirements remain; fresh terrain and protected banks stay closed. Public-data
priors and simulator consistency are not measurement-based physical calibration.
