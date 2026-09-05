# MicroDuck / sim2claw diagnostic contract

Version: `microduck.ops.trace-comparison.v1`. This is an offline diagnostic,
not the neutral exchange envelope being developed in the sister repositories.
The envelope may reference it by path and hash without copying its producer.

Implementation: `experiment_ops/compare.py`; CLI: `scripts/duck-ops compare`.
Activity is separately versioned `microduck.ops.activity.v1`.

## Inputs and interpretation

Input is JSONL with `case_id` string and strictly increasing per-case `time_s`
numeric seconds. Optional signals are `action_rad` (default 14 numeric values),
`command` (3), `robot_xyz_m` (3), `target_xy_m` (2 or null), `fell`/`visible`
booleans and `contacts` as canonical pair-name strings. `--action-width N`
supports an explicitly adapted robot interface; it does not infer joint order.
The current reader handles retained MicroDuck laser trajectories directly.

Field suffixes define metres, radians and seconds. Coordinate frame, time
origin, simulator versus wall clock, action semantics/joint order and sample
schedule must be bound by the producing evaluator or the exchange adapter.
For the retained laser examples: robot/target position is in the simulation
world frame; time is case-relative simulation time after each 20 ms control
step; actions are unfiltered deltas from HOME, in the frozen 14-joint order.
Do not infer those semantics for another producer just from matching shapes.

The output contains:

- `sources`: raw path, SHA-256, bytes and row count for both inputs.
- `cases`: stable case IDs, left/right/aligned row counts and unmatched times.
- `coverage`: presence counts per signal, separately for each source.
- `first_differences`: time, original line numbers and raw values per signal.
- `different_rows`, `max_abs_component_error` and aligned plot `points`.
- `recorded_action_values_equal`: true/false only with complete observed
  alignment and actions; otherwise null. This is parsed-value identity, never
  original tensor-byte identity.
- `physics_causality: not_established`, `behavior_acceptance: not_evaluated`,
  `proof_class: offline_trace_diagnostic`, `hardware_authority: false`.

## Concepts shared, authority kept separate

| sim2claw idea inspected read-only | MicroDuck adoption |
|---|---|
| `src/sim2claw/agent_context.py` distinguishes current authority and historical sources | Read live GOAL/task list; historical role records do not start a new loop. |
| `src/sim2claw/ops/core.py` identifies indexed evidence by path/content | Report raw path/hash and exact divergent row anchors; comparison is a derived artifact. |
| `configs/operations/lessons.v1.json` links lessons to source spans | Physics/operations guide links concrete failures to the next diagnostic. |
| Separate fixture/simulation/replay/learned/physical proof classes | Keep repeatability, observed action equality, physics causality and learned behavior separate. |

The exchange adapter must separately identify the **evaluator owner** (for
example C MuJoCo/BAM development evaluator versus Genesis diagnostic), producer
revision, model variant, interface hashes, normalizer, suite/seed/reset,
coordinate frame and clock. Missing fields remain unknown. Do not convert a
successful parser/checksum or `fixed_recorded_actions` into accepted behavior.
The report's field tolerance is not permission to change a frozen evaluator.

## A future causal replay

Use a separately named experiment with a saved raw action tensor and SHA-256,
dtype/endian/shape, joint order, dt/decimation, initial qpos/qvel/actuator state,
model/asset/BAM hashes and common perturbation schedule. Apply those exact
actions to each engine; do not call the actor again after step zero. Record
pre/post-step state, observations, commanded targets, realized torques and
contact pairs/forces. Compare the first event under a frozen diagnostic plan.

Current offline comparisons help locate that plan. They neither execute this
replay nor close the historical backheel qualification gate.
