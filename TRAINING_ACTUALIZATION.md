# Training actualization — process-review implementation

September 16, 2026. The owner accepted the methodology review and requested an
implementation PR. This is the only ordered execution queue. There are no
role cycles, autonomous launches, policy promotions, hardware operations or
paid-compute authorizations in this change.

The previous queue is preserved byte-for-byte in
[the archived queue](docs/workspace/history/TRAINING_ACTUALIZATION-pre-retool-20260916.md).
Its relative links resolve from the repository root; the original location is
[available at the base commit](https://github.com/jakekinchen/microduck-rl-genesis/blob/942430fb3aeddb9300f07ee99d71010db9ea6295/TRAINING_ACTUALIZATION.md).
Historical scores, source freezes and receipts are not edited or rescored.

## 0. Candidate implementation and verification

- [x] Accept the review direction: keep PPO, retained actors and native BAM;
  compare frameworks only on a matched task.
- [x] Add opt-in transition sampling, actor-gradient diagnostics, strict
  simulation-body step sequencing, complete in-memory state capture, bounded
  impact probes, and separate camera command candidates.
- [x] Add portable contract tests and an independent CI job; CI success is not
  behavior acceptance. See [implementation scope](docs/workspace/RETOOLING_20260916.md).
- [ ] Pass the pinned-RSL default-update equivalence test and retained-follower
  integration in a full checkout; inspect the new CI result, not just its exit.
- [ ] Run existing `./scripts/duck verify` on the full checkout.

## 1. Make the numerical/model decision finite

- [ ] Freeze the V11/V62 sources, full-state checkpoint and input schedules
  at 0.035 s. Require exact native 5 ms clone controls against V65 first.
- [ ] Run one 0.035–0.135 s fixed-output comparison per declared model/rate;
  compare live BAM feedback separately at its unchanged 200-Hz clock.
- [ ] Apply justified state/contact/load thresholds to complete traces. Choose
  retain, revise or reject; do not automatically add another refinement stage.
- [ ] Run closed-loop standing and walk–stop on the selected diagnostic model.
- [ ] Keep V62 as an offline geometry reference. Propose one simpler task model
  with audited support/dangerous collision pairs, not disabled real contacts.

Open-loop agreement and a detailed mesh are not closed-loop or calibrated
physical acceptance. `retool.impact` is a probe implementation, not a V65 replay
receipt or a new admitted timestep.

## 2. Close runtime compatibility

- [ ] Connect the actual Rust scheduler/observation builder to the step-tagged
  body seam in `retool.runtime`; no unvalidated replacement daemon is claimed.
- [ ] Prove observation/action, startup, motor/sensor FIFO and four-BAM-update
  conformance before a complete stand → walk → turn → stop rehearsal.
- [ ] Diagnose failures without HOME-pose rescue, action filtering or retries
  after partially advanced physics. Hardware remains out of scope.

## 3. Deliver the bounded visual skill

This scoped flat-V11 development need not wait for full-CAD or carpet admission.
It remains a separate, serialized task, not concurrent unguarded simulation.

- [ ] Reproduce the original RGB/controller bank, including duplicate-motion
  accounting and the first clipping event at 1.6 s.
- [ ] Freeze ONE candidate: `edge_speed` or `reacquisition_yaw`, not both.
- [ ] Verify unchanged detector, physical camera axes, actor outputs and all
  16 required development cases plus two negative controls.
- [ ] Only after complete development acceptance, freeze/open unfamiliar layouts.

## 4. Run one diagnosis-driven learning comparison

- [ ] Establish standing-pose feasibility through bounded independent pose/
  equilibrium search and dynamic settling, not only existing-policy behavior.
  Choose a justified target; preserve the existing 30-degree acceptance gate.
- [ ] Source-freeze a standing-only world-space posture comparison and a
  diagnostics-only control. The V56 frozen protocol remains unmodified.
- [ ] Use matched final-checkpoint rules and three training seeds (26091601,
  26091602, 26091603). Keep transition budgets/retention samples matched.
- [ ] Inspect gradient conflict, KL/clipping, critic error and realized task/
  transition exposure. Test sampling or retention weights as separate changes.
- [ ] Require retained flat/composition/surface behavior and all whole-session
  gates; do not promote a surviving but failing candidate.
- [ ] If evidence implicates critic quality, freeze a separate asymmetric-critic
  comparison with the deployable 61D actor unchanged. Actor memory is not bundled.

## 5. Conditional framework and broader-skill work

- [ ] Benchmark one unchanged upstream mjlab task after auditing model, actuator,
  delay, reward, reset and observation differences. CUDA purchase is NOT authorized.
- [ ] Migrate only for measured behavior, cost or required throughput benefits.
- [ ] Recovery, terrain families and physical validation retain their separate
  entry/exit/contact/calibration requirements. Public priors are not calibration.

## Rules shared by every stage

Use a new source-bound protocol/output directory and the existing compute guard
in the same conditional launch operation. Missing evidence is not a pass. Keep
exploratory capability, model validation and deployment acceptance distinct;
threshold margins inform prioritization but never change binary acceptance.
`python -m retool status` is read-only; its JSON is a work register, not another
queue, a source freeze, a launcher or an authorization service.
