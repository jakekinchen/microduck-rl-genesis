# Command-responsive walking v5

V3 completed 18,432,000 new transitions. The final candidate passes posture in
21/21 cases and all independent stepping, loaded-slip, torque and joint gates,
but the composite result is 0/21: yaw error fails all 21; stopping fails 11;
lateral speed fails 9. Preserve these exact results. Native action-export parity
is 1.67e-6 rad. All 18,900 frames clear the full-collision non-foot meshes by
at least 14.27 mm. This is not a hardware result.

Genesis response diagnostics also fail yaw (0.28–0.49 rad/s MAE) while their
stops settle below 0.0016 m/s. Changing only the native initial motor FIFO fill
does not fix its turn-and-stop failure. There is no evidence to fix mass, pose
frames, foot geometry or camera optics again. The v3 head correction is kept.

One active intervention: add a non-saturating command-error cost at every
control step, including stop commands. Rate = -2 times the sum of absolute
body X/Y velocity errors beyond 0.01 m/s, divided by 0.05 m/s, and absolute
yaw-rate error beyond 0.05 rad/s, divided by 0.20 rad/s. Preserve existing
Gaussian tracking rewards and every v3 stepping/effort/posture objective.
The extra term keeps direction and amount of error distinguishable where
the existing Gaussian reward tails and clipped stop cost become flat.

Use the separately tested v4-native-floor environment as the base. Its sole
scene change is 1/1 floor collision masks; those extra contacts were inactive
in saved probes and a paired fixed-action prefix was byte-identical. This is
a conformance prerequisite, not the active explanation for tracking improvement.
No assistance, phase input, IK, action smoothing, joint clipping, added sensors,
mass/inertia change, or hidden correction to policy outputs. ABI stays 61/14
at 50 Hz with the existing BAM 200 Hz loop.

Warm-start actor and critic only from the retained v3 FINAL checkpoint749:
`29eb856aa48bfbb2191e77279f9f90fc8ce82772f815727a7b834e8e4bee41c2`.
Optimizer and iteration reset. Seed 26090515. Local 64×5 smoke, then at most
1024×750×24 = 18,432,000 new transitions. Final-only candidate. Intermediate
diagnostics may identify a stop condition but cannot be promoted. Keep the
training source frozen for the entire run and retain its terminal evidence.

Before training, freeze `tracking-suite-v1.json`: same commands, timing buckets,
durations and every numerical motor/posture threshold, but new initial headings
and seed 76541. Evaluate v3 on it as the unchanged baseline. Evaluate v5 final
on this fresh visible-development bank AND the old 21-case regression battery.
Require all cases, independent body-clearance audit, and actual close-up video;
do not accept nominal averages or a prettier motion. No canonical held-out bank,
physical acceptance, paid compute, publication, activation or extra agent.

If heading remains bad in both engines, inspect the first-party controller's
measured error tradeoff before another intervention. If Genesis control passes
but native stopping fails, isolate the first divergent fixed-action physical
state/contact/actuator sample; do not label unmeasured dynamics as calibrated.
