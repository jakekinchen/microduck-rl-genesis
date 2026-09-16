# A capable, context-aware MicroDuck behavior library

Owner direction, September 6: build toward a broad, smart behavior library.
This is the architecture and roadmap, not a claim that these behaviors already
work. The only execution queue remains `TRAINING_ACTUALIZATION.md`; walking
quality is the current prerequisite. No new agents, goal loops or hardware
activation are introduced here.

Every behavior must satisfy the [mandatory validation standard](BEHAVIOR_VALIDATION.md):
thorough independent tests, applied domain randomization, unseen-environment
generalization and validated physics within an explicit operating envelope.
This includes deterministic controllers, perception and complete compositions.
The standard is required work, not a claim that existing behaviors meet it.

## What makes a behavior a capability

A checkpoint is one component, not a complete capability. For example, follow
a red dot requires perception, target persistence and loss handling, a motion
command controller, locomotion, and safe stopping. A successful target tracker
cannot override failed foot contact or motor limits. A video cannot prove the
controller used camera pixels when it actually used simulated target positions.

Each capability needs a versioned behavior card with:

| Contract | Required information |
|---|---|
| Purpose and parameters | Observable behavior, supported speeds/distances/headings, units and coordinate frames. |
| Inputs | Actual sensors, freshness/confidence limits, absent-input handling; privileged simulation inputs explicitly excluded from deployment. |
| Entry conditions | Upright/support state, required observations, compatible robot/model/runtime variant, preceding behavior and state/history assumptions. |
| Execution | Exact policy/controller identities, observation/action contract, resource ownership, update rate and parameter bounds. |
| Lifecycle | Start, update, cancel, completed, timed out, failed; observable completion/failure reasons and interruptibility. |
| Exit and fallback | A tested next state, not merely a zero action vector. STOP is a learned/controller behavior; it is not automatically safe when fallen or observations are stale. |
| Evidence | Full per-bucket test results, model/physics envelope, visual examples including failures, controller ablations, transition tests, source/artifact hashes. |
| Availability | Planned, development candidate, or admitted for a named simulation/runtime envelope. Physical authority remains a separate explicit gate. |

As of September 16, no general or physical walking capability is admitted.
Retained V21 walking/V15 standing with V30 heading supports scoped exposed
flat-floor development; V54/V55 still pass only 5/14 exposed surface sessions.
Full-CAD dynamic acceptance remains open after V63–V65; V66 admits only a
guided ankle-impact numerical reference. The standing component is tested
within specific compositions, not as a universal standing skill. Neutral-head
training does not establish safe arbitrary attention motions. The
[process-review packet](PROCESS_REVIEW_20260916.md) distinguishes these results
from earlier V18/V19 failures and from future library requirements.

## Two layers of intelligence

The decision layer uses goals, observations and capability contracts to choose
what to do: acquire a target, approach, turn, wait, search, stop, or report why
it cannot proceed. It remembers target identity and task progress, notices
stale observations, and uses hysteresis to avoid constantly changing behavior.
It should log a short human-readable reason for each selection or refusal.

The execution layer performs a tested behavior with bounded commands and one
owner of each actuator. Learned policies can coexist with simple deterministic
controllers. An optional language model may select a high-level intent later;
it does not write arbitrary servo actions or bypass admission/safety checks.

Missing preconditions mean unavailable, not "try it and see." Simulation-only
experimentation remains possible as an explicitly labeled development run,
not an advertised robot capability. Compatible tensor shapes are insufficient:
gains, filters, delays, model geometry, normalization and last-action history
must match the complete deployment variant.

## Build order and observable exits

| Stage | Behaviors | Exit before expansion |
|---|---|---|
| Foundation | Stand, commanded walk/turn/arc, stop | Close all current residuals, then pass separately frozen new development; bilateral stepping, contact/slip, head/posture, motor limits and complete stopping. |
| Attention | Look toward a bearing, scan, reacquire | Verified head/camera frame, safe head motion without destabilizing stance, observable sensor-based target acquisition. |
| Perceptual interaction | Follow laser/visual target, maintain distance, approach and park | Real rendered-camera input, occlusion/stale-frame stop, reacquisition and target identity; target AND locomotion gates. |
| Navigation | Move to waypoint, turn in place, avoid obstacle | Feasible geometry and sensing, bounded clearance, blocked-path behavior, arrival and stable stopping. |
| Recovery | Recover from supported perturbations; later explicitly scoped get-up | Declare reachable states and required hardware/geometry first; no reset teleport, hidden assistance or unsupported universal recovery claim. |
| Compositions | Find → face → approach → follow → stop; task-level games | Continuous-state sequence and interruption tests, no silent reset between behaviors, correct refusal/fallback when a component is unavailable. |

Kicks, expressive motions, balancing and more dynamic skills can be added after
their mechanical reachability and sensing needs are established. A broad list
of names is not the target; reliable combinations are.

## Transitions are first-class tests

Test walking→standing, standing→turning, left→right, approach→target-lost stop,
cancel→stop, and repeated sequences without resetting physics, controller
state, actuator delays or action history. Cover successful completion, timeout,
invalid/stale input and cancellation mid-motion. Actor switching must not
silently blend/filter actions unless that exact variant is trained and tested.

This follows a measured failure: V15 passed 21 fresh-reset cases but only 33/42
new repeated windows. A library that evaluates behaviors only in isolation
would advertise unsafe compositions. Candidate identity and transition results
belong in the library contract, not just a demo gallery.

## Generalization without inflated transfer claims

Grow one declared variation group at a time: timing, sensor noise/dropout,
friction/compliance, mass/COM, slopes/roughness, and visual appearance/lighting.
Choose physically plausible bounds and separate training/development/final
evaluation populations. Report the worst required bucket, not just an average.
Do not change collider stiffness or tolerance solely to rescue a candidate.
Physical trials require actual robot/runtime identification, calibration,
measured actuator/sensor limits and explicit user authority.

These are mandatory admission gates for each behavior, not optional future
polish. Test actual randomization coverage, disjoint unseen environment families,
combined shifts, repeated transitions and worst-case failures. Cross-engine
agreement alone cannot certify physical accuracy; measurement-based calibration
and uncertainty are required for that claim. See the validation standard for
the per-behavior matrix and unavailable-by-default evidence requirements.

The next implementation after the walking gate is a small machine-readable
catalog and validator with unavailable-by-default behavior cards, followed by
one real two-behavior composition. Build a larger planner only when those
contracts and transitions have executable evidence.
