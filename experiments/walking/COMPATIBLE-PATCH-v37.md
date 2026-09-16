# V37 numerical compatibility diagnostic

V36 disabling pruning leaves the V35 trajectories unchanged. Test the installed
Genesis `enable_mujoco_compatibility=True` mode on the same exact-hull/GJK-patch
model. This is one configured numerical implementation group, not a claim that
one solver equation explains the discrepancy: the mode affects constraint
ordering, refresh conventions and imported compatibility defaults. Keep the
explicit 10/20 iteration limits, dt, gravity, authored body parameters, surface
solref/friction, actions and native controls unchanged. Retain V34 all-collider
support/mass audit and V31 five-prefix 2-mm/5-degree gates. No broad training or
material fit is implied; if this fails, retain the numerical blocker and scope
subsequent native stopping diagnosis independently of Genesis surface claims.
