# Pinned recipe comparison audit

September 9, 2026. Static source comparison; not imported-policy conformance.
The [research note](../../docs/workspace/CAPABILITY_FEASIBILITY_RESEARCH.md)
contains primary-source evidence and limitations.

| Property | Pinned official recipe | Local V54 decision |
|---|---|---|
| Source | `pollen-robotics/microduck_rl@2b581c641406a48346e696212930ea881c222c52`; four captured files match immutable URLs by SHA-256. | Record the pin; do not update the local BAM or model dependencies. |
| Observation/action contract | Current 61D observations and 14 servo outputs, baked normalizer; task-specific command use. | Preserve local observation construction, joint order, units and zero-padded head/body commands. No foreign weights are admitted from shape alone. |
| Command experience | Explicit turn-in-place fraction; increasing zero-command allocation. | Preserve current commanded movements and timing profiles; add repeated short-to-long continuous stop/restart practice. This is inspired by the curriculum principle, not an upstream reproduction. |
| Actor/critic | Current-observation actor; critic additionally receives base velocity. | Test sharing within the existing actor interface; keep the same 61D critic in both arms. |
| Collisions | Velocity uses stripped trunk/head contacts; recovery uses curated ground contacts. The newly named true full-collision model is unused by tasks. | Unchanged complete-contact-v11 and all applied-load, geometric-interference and support rejection. No claim that additional contacts alone prove physical accuracy. |
| Sensors | Separate angular-velocity and joint-velocity lag/noise/misalignment settings. | Preserve the three already tested local motor/sensor timing profiles and exact observation-insertion conformance. No equivalence claim for the upstream sensor stochastic process. |
| Motors | BAM voltage/friction modeling and actuator randomization. | Preserve the local pinned BAM parameters, 200-Hz integration and non-accumulating resets. Randomization is not broadened in this comparison. |
| Rewards and thresholds | Different task rewards; comparatively weak slip shaping supports its turning style. | Preserve V50 reward for both arms and the independent local composite evaluator. No copied coefficient or relaxed slip/yaw gate. |
| Controller boundaries | Same-platform examples include both combined tasks and switched policies. | Compare a shared MLP against jointly trained routed MLPs. Keep initialization and exposure differences visible. |

This comparison can answer which bounded local recipe performs better. It cannot
show that the official task fails our physics, that its published behaviors meet
our gates, or that our simulator matches an individual physical Ducky.
