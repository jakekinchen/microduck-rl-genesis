# Walking development is not yet a hardware handoff

Checked 2026-09-05 (local date), while v13 trained. No hardware was accessed,
no daemon configuration changed and no artifact was published or activated.
This is an additive compatibility audit, not permission to change frozen v13.

## Known compatibility boundary

The current public MicroDuck runtime at commit
`bc41fb5c9a9b39894669c1e022e375cf83800382` uses optional head/leg target filters
with defaults .5/.7, walking action scale .9, and standing-specific tuning.
Our source-bound walking lane instead uses scale 1 and unfiltered motor deltas.
V13 used one walk/stop actor; V14/V15 now explicitly select a separate standing
actor for exactly zero commands. That is still not the public runtime's full
selection/filter/gain contract. Matching 61D/14D shapes alone does not make
the two control paths equivalent. The physical runtime has 15 servos, but the
mouth is excluded from its 14D actor; that count is not itself a mismatch.
Sources: [control implementation](https://github.com/pollen-robotics/microduck/blob/bc41fb5c9a9b39894669c1e022e375cf83800382/robotd/src/control.rs),
[policy selection](https://github.com/pollen-robotics/microduck/blob/bc41fb5c9a9b39894669c1e022e375cf83800382/duck-control/src/policy.rs),
[runtime design](https://github.com/pollen-robotics/microduck/blob/bc41fb5c9a9b39894669c1e022e375cf83800382/docs/design/robotd-design.md).

The real v2 IMU supplies an onboard-fused quaternion. Its heading is relative
and drifts; the documented odometry has no magnetometer correction. The v12
outer heading controller was evaluated using simulated orientation with a
declared delay, not calibrated hardware yaw drift or stale-sample behavior.
Sources: [IMU decoder](https://github.com/pollen-robotics/microduck/blob/bc41fb5c9a9b39894669c1e022e375cf83800382/duck-control/src/imu.rs),
[odometry and heading limits](https://github.com/pollen-robotics/microduck/blob/bc41fb5c9a9b39894669c1e022e375cf83800382/docs/design/robotd-design.md#44-odometry-on-the-sample-the-loop-already-took).

The hardware safety range is actuator travel, not anatomical joint limits.
Accordingly, reference overshoot in our receipts is not equivalent to actual
joint-stop parking. Neither observation grants permission to send those
references to an unspecified robot. Source:
[safety implementation](https://github.com/pollen-robotics/microduck/blob/bc41fb5c9a9b39894669c1e022e375cf83800382/duck-control/src/safety.rs).

## Required before a physical trial

- Identify the actual hardware revision, fitted battery, joint order, HOME,
  mass/inertia and mechanical geometry. The corrected v11 CAD model proves
  its own coverage, not that a particular physical assembly matches it.
- Freeze the installed runtime/configuration and compare the complete
  observation/command/action path, gains, filtering, voltage behavior, stop
  policy selection, resets and safety handling with the trained contract.
  Do not disable real safety or silently turn filters on/off to make a demo
  work. Any necessary change needs a separately evaluated deployment variant.
- Measure IMU frame alignment, yaw drift, stale samples and end-to-end motor/
  sensor timing. Rehearse the resulting measured envelope in simulation,
  including controller loss/recovery, before a physical handoff.
- Validate motor loads/current/temperature, friction and contact compliance
  for that robot, then obtain explicit authority for a bounded physical trial.

V13/V14/V15 remain local complete-contact, flat-ground development experiments.
Passing them does not close these tasks, blind acceptance, laser perception or
rough-terrain generalization.
