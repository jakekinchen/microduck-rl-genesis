# Public surface action replay, version 1

Replay the first second of each original baseline start-1 training-profile
session in Genesis CPU; truncate only at the native terminal record. Also
replay the newly trained standing actor's start-1 strongest-surface prefix.
These prefixes cover the initial standing phase, not walking.
No actor inference, feedback correction, action modification, extra suffix or
post-fall continuation. Source actions are the retained float32 NPY arrays;
assert byte identity at the Genesis environment's action buffer every step.

Use original native initialization (.125-m base, declared yaw, HOME joints,
zero velocities and actuator state), V25 static panels/contact parameters and
matching declared motor and sensor delays. Translate world Y by the panel's
fixed center, then subtract that translation only in comparison coordinates.
The native lane uses a plane while the training lane uses large fixed boxes;
local support tops agree, but contact-manifold representations can differ.
This compares the actual two lanes, not an isolated solver implementation.
Do not edit either lane's geometry. Verify realized delayed targets against each
native record, all finite states and no automatic reset.

This is a diagnostic, not policy selection or a gait pass. Before replay,
freeze numerical comparison thresholds: maximum base-position discrepancy
2 mm and maximum joint-angle discrepancy 5 degrees over the retained prefix.
Report per-case outcomes, raw errors and the first divergence. Primitive
agreement alone is insufficient; these robot-level traces include actuator,
joint and contact interactions. Matching an engine is not physical calibration.
