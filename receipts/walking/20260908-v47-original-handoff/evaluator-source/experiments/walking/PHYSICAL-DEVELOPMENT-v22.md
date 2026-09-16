# V22: new exposed physical-combination development bank

Frozen only after V21 FINAL passed all original 21 and exposed repeated 42.
No further training or policy/controller selection. Exact V21/V15 actors,
V16 slew, V19 heading, complete-v11 geometry/BAM and unchanged acceptance limits.
Independent imported-physics audit confirms all 15 body masses, centers of mass
and inertia tensors match the authored model within float32 conversion tolerance.
That audit does not certify measurement-based physical accuracy.

Four flat-floor domain profiles, each crossed with three new command/heading
cases and two continuous 18-second start/move/stop windows: **24 windows**.
Control: nominal physical parameters. Traction: sliding friction .6x nominal.
Inertia: every positive body mass AND inertia tensor 1.1x nominal, unchanged COM.
Combined: both changes. All profiles retain 30-ms motor/20-ms sensor delays.
Forward .17 m/s at yaw -1.2; right turn -.45 rad/s at yaw .3; left arc
(.10 m/s, .35 rad/s) at yaw -1.7. Command from 1 to 13 s, then STOP.

These are deterministic exploratory stress bounds, not measured material or
robot uncertainty. Every geometry's sliding coefficient is set from immutable
nominal arrays, including floor and feet, so contact mixing cannot silently
leave traction unchanged. Torsional/rolling friction, geometry, actuator limits,
timing, reward and all controller logic remain fixed. Recompute model constants
then reset once before each two-window session; never reset between repeats.
Record actual mass/inertia/friction arrays, hashes and observed contact sliding
friction. Test reapplication, nominal restoration, immutable baselines and
independent model instances before executing the bank. No outcome-fitted values.

Operating envelope and tests: these twelve declared sessions only. Apply the
unchanged gait, task, torque, joint, posture, heading, geometry and 200-Hz load
gates to every window. No fall/missing repeat may leave the denominator. Retain
original actions, actor inputs, contact/torque telemetry, physical parameters,
videos, policy/source/suite bindings and every failure. Require all 24 for a
pass of this bank; a failure triggers diagnosis, not automatic PPO extension.

DR/generalization boundary: V21 was trained with randomized persistent timing,
not these mass/traction profiles. This tests new physical parameter combinations
and commands on flat terrain. It does not establish randomized-physics training,
unseen terrain/layout families, long endurance, dropout/cancel recovery, sensor
or perception generalization, calibrated physics, library admission or hardware
authority. Those mandatory gates remain separate and the protected bank stays
closed. This is an exposed development bank, not a final held-out claim.
