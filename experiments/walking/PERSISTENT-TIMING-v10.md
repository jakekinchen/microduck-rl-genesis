# Conditional v10: persistent device delays, not faster parameter jitter

Prepared while the fixed v9 reward-composition run is active. This file is NOT
a launch instruction and v10 has no trainer or run yet. Do not hot-edit v9.
Only consider activation after its retained FINAL and all final evaluations.
If that final passes the visible battery and heading checks, do not launch
this correction. If non-yaw gait/posture/stopping failures recur, inspect them
before attributing everything to delay sampling.

## Evidence

V8 FINAL in Genesis CPU: with the actual fast training delay process, all
seven command yaw MAEs are 0.125–0.163 rad/s. Slow-forward signed yaw bias is
-0.0026 rad/s. Holding the same envelope's individual device delays fixed gives
-0.0918 at 20/20 ms, +0.0546 at zero, -0.0989 at 30/20 ms. This is a seeded
closed-loop timing-process diagnostic, not fixed-action physics isolation or
proof of learning causality. Head posture was wrong under both processes.
V9 checkpoint150 repairs head/trunk/stop posture but still has fixed-profile
direction errors; it is intermediate and does not activate this proposal.

Changing delay every 0.32 seconds (motor) or 1.28 seconds (sensors) is not the
same training distribution as keeping a device characteristic stable across
its rollout. Biases can cancel under rapid random changes while persisting
for one device. This conditional intervention changes the temporal sampling
of the existing delay domain, not its limits or an outcome-fitted contact law.

## Exact proposed change and tests

Use the same integer uniform motor range 0..6 PHYSICS ticks and each independent
sensor range 0..1 CONTROL ticks. Sample each environment's delay at initialization
and episode reset, then hold it throughout that episode. Preserve the exact
inherited FIFO call, first-value priming, no interpolation/filter, BAM dynamics,
voltage/drop variation, sensor independence, actor/critic interface, all v9
rewards, command sampling, physical resets and termination rules. Resetting one
environment must not disturb another's lag or history. Zero lag returns the
original tensor unchanged. This remains an uncalibrated timing envelope.

The separately tested implementation is `microduck/walking_persistent_timing_env.py`.
It is not imported by v9. Unit checks cover 4,000 constant-delay ticks,
independent partial resets, first-value priming, reproducibility, endpoints,
zero-delay identity and inherited reward/physics/control methods. Runtime
smoke and source-bound final-parent admission are still required if activated.

## Research context, not hardware authority

[Imai et al., Multi-Modal Delay Randomization](https://arxiv.org/pdf/2109.14549)
section IV-C samples proprioceptive delay per episode and treats the visual
stream differently. [Peng et al., Dynamics Randomization](https://arxiv.org/pdf/1710.06537)
section IV-C holds mass and damping fixed per episode, but action-timestep
jitter and observation noise still vary per step (the timestep distribution's
rate parameter is fixed per episode). It is not a precedent for removing all
jitter. Different uncertainty sources need different temporal models.
These are useful precedents, not evidence for a specific MicroDuck delay,
sensor correlation, observation history or successful transfer. In particular,
do not copy their robot, parameter ranges, interpolation or policy architecture.
The present one-factor proposal deliberately tests constant-delay coverage
first. It does not establish that real device latency is constant or that a
later measured combination of persistent offset and per-tick jitter is needless.

Keep all frozen visible motor/posture and cumulative-heading gates. No physical
acceptance, policy activation, paid compute, external contact or agent cycles.
