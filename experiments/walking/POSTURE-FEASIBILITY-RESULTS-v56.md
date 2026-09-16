# V56 feasibility is complete; paired learning remains unlaunched

September 15–16, 2026. Thirty complete 10-second downhill standing cases
were evaluated under native MuJoCo/BAM, the retained V11 model and exact
declared motor/sensor delays. **No recipe met the proposed 25-degree face
target across all six conditions.** The paired learning experiment therefore
remains a prepared, unexecuted draft. V30 remains retained.

| Recipe | Cases meeting every feasibility gate | Final mean face pitch range |
|---|---:|---:|
| Original V15, unchanged | 0/6 | 28.95–30.04 degrees |
| V54 shared actor, unchanged | 0/6 | 25.48–26.75 degrees |
| Shared actor plus fixed head-pitch adjustment −0.08 rad | 3/6 | 24.20–25.45 degrees |
| Shared actor, zero-adjustment diagnostic control | 0/6 | 25.48–26.75 degrees |
| Shared actor plus fixed head-pitch adjustment +0.08 rad | 0/6 | 26.75–28.00 degrees |

Conditions cross motor delay 0/4/6 physics ticks with initial yaw 0/.12 rad,
one sensor-delay control tick, a +3-degree Y-axis slope, nominal mass/friction
and 50 Hz control / 200 Hz physics. Score the final two seconds of each
10-second HOME-start episode. The original behavior threshold remains
30 degrees; 25 degrees was a proposed training-headroom target, not a new
retrospective acceptance threshold.

Every case completed without a fall. Settled speed, yaw rate and trunk tilt,
non-foot support, actual joint-stop occupancy, joint excursions, actuator
torque bounds, V11 geometric self-contact and physics-rate internal loading
passed their declared feasibility checks. In the negative head adjustment,
all three yaw-zero cases meet the target; all three yaw-.12 cases miss it.
The separate assisted diagnostic also checks inherited neutral-head limits.

The second experiment adds a declared constant to only head-pitch action
index 6, ramped over the first second. Raw actor outputs and delivered actions
are both retained. These are assisted diagnostic trajectories, never scored
as unchanged-policy or learned-behavior success. No offset enters the prepared
learning environments or any retained controller.

This bounded test does not show that a 25-degree pose is physically impossible
or that RL cannot learn it. An existing policy can oppose a head adjustment
through its observations and previous-action feedback. It shows that the
chosen feasibility witnesses did not establish the proposed target across
the declared conditions. No further adjustment search or learning run was
automatically launched. Full-state transitions and repeated walking stops
remain untested by these HOME-start probes.

## Integrity and scope

The independent verifier reconstructs **15,000 raw/assisted action rows**,
checks both manifests and source bindings, accounts for **60,000 physics-load
samples**, and reproduces the zero-adjustment branch's **3,000 controls**
exactly against the original shared-actor run: actions, observations, positions,
velocities and all load records. Its retained result is
`posture-feasibility-review-v56/verification.json`.

These contact results cover V11's **11 active colliders**, not every visible
CAD part. The current upstream audit found 70 active colliders and additional
coverage gaps in each model. Broader geometry reconciliation takes priority
before terrain or recovery capability admission. Source comparison alone
cannot establish measured physical accuracy.

Prepared V56 training, conformance and evaluator scripts have compilation and
focused contract-test coverage. Their paired simulation conformance, source
freeze, smokes, main PPO runs and candidate evaluation banks **have not run**.
The trainer requires a complete passing feasibility receipt; do not bypass
that check to resume this draft.

## Retained artifacts

- Protocol: `posture-feasibility-v56.json`.
- Unassisted receipt: `../../receipts/walking/20260916-v56-posture-feasibility/`.
- Separate diagnostic: `posture-head-diagnostic-v56.json` and
  `../../receipts/walking/20260916-v56-head-diagnostic/`.
- Independent verifier: `../../scripts/verify_posture_feasibility_v56.py`.
- Prepared comparison: `POSTURE-REFINEMENT-v56.md`.
- Geometry findings: `upstream-audit-v56/README.md`.

All are exposed simulation development. Protected banks remain closed;
physical calibration, carpet support and hardware transfer remain unestablished.
