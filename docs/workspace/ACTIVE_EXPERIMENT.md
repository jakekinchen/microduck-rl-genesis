# Apply the lessons: randomized laser startup

This is the working brief for the next investigation in the existing L2
queue. `TRAINING_ACTUALIZATION.md` remains authoritative for task ordering.
The active training task retains ownership of physics, reward and evaluator
changes. The workspace task supplies source-checked inspection and preflight.

## Current lane: versioned gait correction

The training task has advanced to the versioned face-first gait correction in
`experiments/laser/gait-correction-v3.json`. The initially observed running record was
`laser-gait-20260905-v3`: 1,024 environments, 600 iterations, 14,745,600 planned
transitions. All ten source hashes matched at the recorded check; the updated
process guard recognizes `train_laser_gait.py`. A later snapshot detected a
gait-v4 starting record and source drift against the earlier gait-v3 record.
`duck prepare` lists these separately; exact process-to-run identity is not
asserted. Read the current records for the live version, preserve each version's
source bytes and terminal status, and do not interrupt or duplicate a run merely
to adopt this workflow.

The evaluator now requires both target pursuit and measured gait rejection
gates. Its negative controls cover standing, backward motion, loaded-foot
sliding, one-foot hopping, mechanical-stop parking, and legitimate BAM target
overshoot. Candidate selection is the declared final checkpoint only. The
fresh reserved bank remains closed until all visible composite gates pass.
Current robot/world code differs from the old startup receipt, so `prepare`
correctly refuses direct reproduction through that changed source while
separately checking the running gait record's source hashes.

The retained startup comparison below is a negative control and an example of
the diagnosis process. It is not a direction to restart the old intervention.
Duck Lab reads the new `microduck.laser-gait-evaluation/v3` composite reports
under `receipts/laser-gait/` or `receipts/laser-dynamic/` when they are retained.

```sh
./scripts/duck prepare
./scripts/duck doctor
./scripts/duck-ops guard
./scripts/duck studio
```

`prepare` launches nothing. It verifies the selected development policies,
manifests, suite identity, matching randomized case, complete trace bindings
and current versus retained experiment implementation. It prints the exact
first-fall sample and the prerequisites for any next training intervention.
The process inventory is advisory; rerun `guard` immediately before launching
any separately authorized local job. A successful inspection does not reserve
the Mac or authorize a training budget.

Duck Lab now opens on `20260905-turn-dev` versus `20260905-robust-dev`, case
`75003-figure-eight`. Use **First fall** to inspect the 1.56-second sample and
expand **Recorded domain for this case**. The two recorded policies differ;
this comparison is a policy-intervention diagnostic, not fixed-action physics
replay. Refresh retains a user's selected experiment and case.

## What the retained evidence already tells us

- The selected policy falls at 1.56 s; the previous DR policy remains upright
  for the recorded 48-second case but fails tracking. Keep both negatives.
- The scheduled push is at 23 s. It cannot explain this startup fall.
- Sensor delay is zero in this draw. Delay injection is not active here.
- The first recorded action and position differences are already at 0.02 s;
  commands diverge at 0.04 s. Only 78 rows align before the selected policy
  falls, versus 2,400 rows in the previous policy's complete case. The offline
  comparison correctly labels the pair incomplete rather than asserting action
  identity. Contact telemetry is absent in both retained traces.
- Friction is about 1.342×, trunk mass/inertia 0.909×, and motor gain 0.906×.
  CoM shift, encoder bias and sensor noise are active. These are candidates
  for controlled property tests, not demonstrated causes.

## Next bounded diagnosis

1. Reproduce the selected policy on visible seed 75003 with unchanged source,
   reset and domain. Preserve the first-step state and first-fall row.
2. Keep policy bytes, target route, model/BAM and all other conditions fixed.
   Neutralize one active group per trial: friction; mass/inertia together;
   CoM; motor gain; encoder bias; sensor noise. Record actual applied values
   and fixed random schedules. Do not spend trials on the later push or the
   already-zero delay as explanations for this startup event.
3. Record pre/post-step qpos/qvel, actor inputs, commanded actions, realized
   actuator output and contacts where available. Missing telemetry stays
   unknown. A fixed-policy feedback test can measure a property intervention;
   causal claims about engine differences require original saved action bytes.
4. Choose one next intervention from the measured result. Freeze its hypothesis,
   bounded budget and a fresh evaluation bank before training. Do not tune on
   any consumed reserved seed, including 75109, or relax the old thresholds.
5. Run a smoke, then the bounded experiment, then independent development and
   original regression checks. Freeze candidate choice before fresh reserved
   evaluation. Report falls and incomplete episodes in every denominator.

Camera-driven behavior remains a separate next step. Ground-truth targeting
and floor appearance changes provide no camera robustness evidence.

Update `active-experiment.json` when the working candidate or case changes.
The selector fails closed on policy/suite drift instead of silently pointing
the agent or viewer at a different result. This brief adds no new agent loop.
