# V35 contact patches on matched authored hulls

V34 closes sampled collider support import error to below 1 micrometre and
improves rigid/mild box-to-box prefixes, but softer profiles still diverge.
Retain V34 exact hulls and change only convex collision detection to GJK with
contact patches. V32's patch test had simplified hulls and cannot answer this
combined representation question. Reuse V31 controls, all five exact action
prefixes, geometry audit and unchanged 2-mm/5-degree comparison limits.
Keep actual contact telemetry, failures and unchanged native reproduction.
No physical calibration or behavior success is inferred from this diagnostic.
