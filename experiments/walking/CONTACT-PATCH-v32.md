# V32 convex collision detection isolation

V31 matched boxes worsen the original comparison (0/5). Original plane and
Genesis controls reproduce. Contact support points differ at the first landing,
before the strongest-profile discrepancy crosses 2 mm at 0.10 s. Test one
collision detection property group in Genesis: GJK with full contact patches,
instead of default MPR with perturbed contacts. Keep all V25 solver iteration
limits, integration, parameters, geometry, initialization and fixed actions.
The installed Genesis options expose `use_gjk_collision=True` and
`enable_contact_patch=True`; this option is experimental, not assumed accurate.

Run the same five prefixes and all V31 native controls. Require original native
reproduction, unchanged action bytes and all realized delayed targets. Retain
200-Hz telemetry and unchanged 2-mm/5-degree 50-Hz diagnostic limits. Report
every case and original Genesis difference; changed Genesis dynamics cannot be
claimed as reproduction of the previous simulator. No candidate promotion,
new motor learning or physical calibration. A negative result narrows the
next diagnosis and does not justify changing stiffness to match a trajectory.

Reference: MuJoCo's native convex detector can construct multiple contact
points from contacting faces. Different detection routines have different
manifolds: https://mujoco.readthedocs.io/en/latest/computation.html
