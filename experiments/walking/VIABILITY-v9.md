# Walking v9: posture-conditioned return and persistent steering error

## Evidence and scope

V8 completed 24,576,000 transitions. Its only eligible final model_999.pt is
`348030128f56145a5172fe8ad8469394cb5afab3fd5a6911ac124373493e818f`.
Normalized ONNX is
`8f4f12a254fdd246e66306cd81ed3e25c56f7cbef2f2e7b41b537b33d2d66647`.
All three complete 21-case protocols are 0/21: every case fails head posture.
Current-sensor stops have normal trunk tilt (6.30–6.77 degrees), no falls or
actual joint-stop/slip/torque failures, but the neck tips far back at stop.
Six cases also fail instantaneous yaw; only 9/21 pass separate cumulative
heading. Both neck regression and residual yaw occur in Genesis too.

The 150/500 checkpoints were diagnostic only. Their better head scores cannot
justify selecting them after seeing this regression. The final is retained.
The yaw-only draft was NOT trained: a yaw-only fix would omit a known failure.

The systemic problem is compensatory objective composition: high tracking
return can outweigh independent posture penalties. Quiet stopping still earns
nearly all tracking reward while the head is used as an unacceptable balance
configuration. A separate offline yaw audit finds that removing persistent
gyro bias from recorded wobble can produce little or even negative change in
the old instantaneous yaw objective. That algebra is not a feasible action or
causal learning experiment; it motivates explicitly scoring the DC error.

V9 changes one property group, reward composition, with two declared pieces:
posture conditions positive return, and persistent yaw bias has a linear cost.
This combined objective intervention does NOT isolate their separate causal
effects. It changes no physics, body masses, model geometry, reset/command
population, timing randomization, action, observation, termination, normalized
actor ABI, optimizer type or exploration behavior. Do not add anything else
to a running version.

## Exact objective

Keep every v8 term and every negative penalty. Compute a 1-second exponential
average of absolute neutral-head error per joint, with alpha = 1-exp(-dt/1s),
zeroed at each episode's first reward. Absolute errors cannot cancel by shaking.
The maximum of these four means has a 0.20-radian free range and 0.20-radian
scale. Current trunk lean has the existing 10-degree free range and 5-degree
scale. Let h and t be the positive excesses divided by their scales.
Multiply ALL existing positive reward contributions by exp(-h²-t²).
Do not multiply negative rewards by this factor. Known positive terms are
linear/angular tracking, upright, leg pose, head tracking, air time, sole lift
and duration-shaped landings; an unhandled positive parent term fails closed.
All existing nonsaturating head/trunk/command/motor penalties remain available
to recover from the low-positive-return region. No fixed HOME leg targets.

Separately maintain a 1-second EMA of current body-gyro yaw error against the
current command. Add -2 * max(abs(EMA)-0.005,0)/0.05 * dt. This prices persistent
bias without equating normal 4-Hz sway with steady turning. Body gyro is not
exactly world planar-heading rate; the independent quaternion-heading gate
remains unchanged and can still reject this candidate.

Both EMAs are reward-only privileged state. Neither is supplied to the actor,
used to change a command/action, or updated in deployment. Do not add inference
noise, filtering, mirror averaging, IK, root forces or startup assistance.

## Bounded local trial

Initialize actor and critic from retained v8 FINAL only. Bind source and all
three complete negative final protocols plus their heading reports before
learning. Reset optimizer and iteration, initial adaptive learning rate 5e-4.
Seed 26090519. Require reward-decomposition audit and unit tests before a 64x5
Metal/MPS smoke. Then at most 1024x750x24 = 18,432,000 new transitions. The only
eligible candidate is final model_749.pt. Early checkpoints diagnose all 21
current-sensor buckets; never promote a good intermediate. Clearly degenerate
training can be interrupted and retained as terminal negative.

## Required exit

All three frozen visible 21-case motor/posture protocols, separate unchanged
cumulative-heading checks, actual video/slow motion, full-CAD clearance and
real-observation normalized ONNX parity. Preserve all failed buckets. Compare
native and Genesis responses. These banks are exposed regression tests, not
fresh generalization or physical proof. Only after all pass, freeze and run
a fresh development bank before pursuing target following or physical work.

Native MuJoCo/BAM local worker feasibility was measured, not a native trainer:
about 10,110 control transitions/s across four workers under concurrent v8
training, excluding PPO/reward/batched inference. A native training lane may
be a later explicit dynamics-domain intervention if cross-engine failures
remain; do not claim that this v9 reward change calibrates either simulator.

Update GOAL and the ordered queue in this task. No agent cycles, paid compute,
hardware, policy activation, publication or external contact.
