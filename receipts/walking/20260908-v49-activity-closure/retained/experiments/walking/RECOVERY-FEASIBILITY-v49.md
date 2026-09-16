# V49: full-state recovery feasibility before further learning

Reproduce the original matched-flat/downhill sessions and original/V48 first
long composition, preserving action and observation bytes, poses and velocities.
Capture twelve complete states at the times in `recovery-v49.json`. Include full
MjData, BAM, model damping/friction, motor FIFO, sensors, last action, command
ramp and heading history. Verify each decoded reset twice for 25 controls.
The actual receipt inputs and all source files are frozen before execution.

Compare original V15 and V48 standing from every captured state, with original
V21 walking and V30 command control fixed. Continue each branch without resets
through its original 36-second or 180-second endpoint or fall, twice. Preserve
and verify the original measured prefix in composite scoring; do not treat it
as new optimized evidence. Require exact reproduction in the source actor arm.

For each of the four downhill and two V48 late-composition target states where
neither unmodified arm passes the full session, run the bounded search in the
JSON protocol. Eight generations, 24 candidates per anchor, two anchors; at
most 2,304 trajectories and 576,000 search controls. Use five time-indexed 14D
residual knots plus a fixed zero at 2.5 seconds. Original/V48 actor outputs are
anchors. Three explicit incoming-action bridge candidates initialize each
population alongside mean and best/zero. This is a privileged diagnostic action
controller, not a compatible deployed-policy update, actor-retention claim,
post-policy deployment filter or unchanged-action simulator comparison.

Search parameters are bounded to +/-1.5 radians; physical actions are applied
unchanged to the existing BAM and delays. The proxy integrates squared speed
/.04, yaw /.15 and tilt /15, plus 100 times squared joint-margin shortfall
below .02 rad, 100 times squared internal load above 1 N and 10 times torque
saturation fraction. Integrate at .02 s; add 100,000 plus 10,000 times missing
seconds on a fall. These are optimizer costs, not acceptance gates. Search
runs until the current window endpoint; full validation continues through all
later standing and restart windows. Keep every candidate's actual action and
observation rows, parameter values, cost, identity and stop length.

Select exactly one candidate per searched state by proxy cost across the two
anchors. Repeat its entire continuation twice, retain the raw trajectory, then
apply the unchanged original task, motor, joint, posture, gait/slip, geometry,
200-Hz internal-load, duration and whole-session heading gates. Record current
window recovery, next restart window, and full-session acceptance separately.
An early fall leaves later windows failed. Surviving through bracing is not a
recovery. Do not try a second candidate after validation failure. Matched-state
replays do not establish held-out robustness or physical reliability.

The search follows the model-based trajectory-search framing documented by
[MuJoCo MPC](https://github.com/google-deepmind/mujoco_mpc/blob/main/docs/OVERVIEW.md),
implemented inside this repository's existing native world. No MJPC install,
physics-model substitution or extra external state measurement is required.
[MuJoCo's simulation documentation](https://mujoco.readthedocs.io/en/stable/programming/simulation.html)
informs state copying; the actual native reproduction gates determine whether
our complete actuator/controller snapshots are usable here.

One bounded diagnostic activity, no PPO, no budget extension and no promotion.
Keep V30. A finite failed search means unresolved within the search family and
budget, not proof of physical impossibility. Fresh sequence/protected terrain,
calibrated physics, carpet transfer and hardware remain outside this evidence.
Use the resulting recovery or earliest failure to choose the next activity;
any later learned correction must retain 63 flat cases, both full 180-second
compositions and the five original passing surfaces.
