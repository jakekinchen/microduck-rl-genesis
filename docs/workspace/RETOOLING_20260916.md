# Process-review implementation: candidates, not new behavior results

Base: `942430fb3aeddb9300f07ee99d71010db9ea6295`. The owner accepted the review
and asked for implementation and a PR. No existing actor, frozen evaluator,
V1–V66 implementation or receipt is modified. No training, physical operation,
paid resource, protected bank or automatic policy promotion is performed.

## What this PR implements

| Recommendation | Code delivered | Remaining evidence/work |
|---|---|---|
| Finite numerical investigation | `retool.checkpoint.WorldCheckpoint`, `retool.impact.run_window`, common-grid comparison | Restore V65 evidence; capture source-bound schedules; require exact native clone controls; execute full-robot comparisons and closed-loop tests. |
| Faithful runtime boundary | `retool.runtime.LockstepBody`: epoch/step tokens, observation-byte checks, raw float32 actions, four BAM/load ticks, partial-step poisoning | Actual Rust scheduler, wire transport and observation-builder integration are NOT implemented here. Full native rehearsal remains required. |
| Transition-aware learning | Metadata-required phase labels and fixed-size balanced replay; `microduck.recipe_ppo_review.ReviewPPO` | Reconstruct episode-aware replay from retained receipts; pin and conformance-test the new trainer configuration; run matched learning. |
| Objective/critic diagnosis | Weighted actor-gradient norms/cosines, per-mode flat/nonflat gradient/advantage/value diagnostics, KL/clipping, explained variance; world-space standing-face cost helper | No newly trained posture actor or privileged critic. Independent feasibility and a new source-bound comparison remain required. |
| Camera capability | Opt-in `edge_speed` and `reacquisition_yaw` candidates wrapping the retained detector/follower | Recorded RGB replay, first-failure isolation, all 16 cases plus negatives, and unfamiliar layouts remain unrun. |
| Useful progress reporting | Signed gate margins, missing/hard failures, complete matched three-seed comparison, portable CLI and CI | These summaries do not authenticate input receipts or promote behavior. |
| Model/framework simplification | Explicit queue and decision rules; detailed V62 model stays an offline reference | Simplified collision generation, asymmetric critic and matched mjlab benchmark are design-only. No migration is claimed. |

The owner subsequently authorized review and merge of these **opt-in
foundations**. Portable contracts and workspace tooling are validated; the
native experiments remain ordered follow-up work, not claimed PR outcomes.
See [the merge review](PR1_REVIEW_20260916.md) and
[the continuation prompt](NEXT_AGENT_PROMPT.md). Helper unit tests do not mean
all recommendations have been executed end to end.

## Offline entry points

```sh
python -m retool status
python -m retool doctor  # returns nonzero for missing native inputs; launches nothing
python -m unittest discover -s tests/retool -v
python -m compileall -q retool microduck/recipe_ppo_review.py
```

`status` validates the compact work register, not an experimental source freeze.
`doctor` checks package/path presence without importing a simulator. It cannot
establish version compatibility, source integrity or readiness to operate a robot.
The existing `./scripts/duck verify` remains the full-checkout workspace check.

For new, validated replay examples:

```sh
python -m retool label-replay --input replay-with-metadata.npz --output new-phased-replay.npz
python -m retool compare --input matched-seed-results.json
```

Replay input must contain `observations` (N×61), raw float32 `actions` (N×14),
`env_ids`, `episode_ids`, and `control_steps`. Episode/control metadata is not
invented from concatenation. Each episode starts at control zero; gaps and
out-of-order rows fail. The output uses exclusive creation, retains a source
SHA-256 and contains phase labels. A phase denotes a sampling interval, not
observed physical settling. Keep provenance and validation of imitation labels
separate; failed walking segments cannot silently become teacher examples.

Comparison input has `seeds`, exactly two `arms`, and one `runs` entry per pair.
Each run needs `training_seed`, `arm`, `status: completed`,
`split: exposed_development`, `comparison_sha256`, `bank_sha256`, `model_sha256`,
`gates_sha256`, `required_case_ids`, and `cases` mapping every required ID to a
boolean. Missing/aborted runs and changed denominators reject aggregation. Exact
repeats are not extra training seeds. This is descriptive, not a confidence bound.
All four identity fields must be 64-character lowercase hexadecimal SHA-256s;
format/equality checks do not authenticate the underlying receipts.

## Native integration contracts

### Short impact window

Capture `WorldCheckpoint` on a source-bound retained TerrainWorld at 0.035 s.
It copies complete MjData, sensor scratch state, Python BAM controller state,
mutable damping/friction and the command/heading/motor/sensor histories. It is
in-memory; it does not deserialize arbitrary pickle files or pretend a qpos/qvel
NPZ is a full snapshot. Cross-model or changed-option restores fail. Restore the
original model first, then change the integration timestep as an explicit arm.

Use a separately verified `ImpactSchedule`: 20 rows at 5 ms, containing applied
torque/damping/friction and PRE-delay motor references. First require exact 5 ms
clone parity against original V65 output. `fixed_output` holds the recorded
outputs; `live_bam` advances the restored FIFO and original BAM at 200 Hz.
No policy inference is added. All-rate contact traces remain necessary: common-
grid root differences alone do not score joint, impulse, penetration or load gates.
Each result declares its start/end time. Comparison checks the full sample count,
timestamps and finite qpos at every integration tick, including finer-rate rows
that are absent from the common grid. Truncated traces cannot be compared.
The native clone gate MUST catch any unsupported mutable world/controller state.
Do not infer a complete whole-robot reference from a synthetic unit test.

### Runtime body seam

`LockstepBody.prepare(Token(epoch, step), float32_twist)` returns the expected
61D observation without advancing physical time. An identical pending request
is idempotent. `advance(token, raw_float32_action)` inserts that exact action at
the actual retained inference call and checks the observation bytes, one control
interval and four load/torque samples. It retains all controller history through
walk/stand changes. Bad tokens or malformed actions never step physics; an error
after stepping poisons the bridge because a partial step is not safely retryable.

This is a simulation-only library seam. It does not open sockets, enable motors,
remove hardware startup interlocks or claim that the upstream Rust daemon has
been patched. Wire protocol, scheduler and Rust observation parity are still
required before the actual startup/stand/walk/turn/stop rehearsal.

### Learning candidate

Use a NEW, source-frozen experiment config; do not point old V54/V55 launchers at
changed code or weaken V56's frozen prerequisite. In that new config, use
`microduck.recipe_ppo_review:ReviewPPO` and a new `diagnostics_path` inside the
run directory. Defaults preserve the original objective and mode sampler;
normalizers, teacher, deployment ABI and checkpoint selection remain the caller's
explicit unchanged contract. Unsupported recurrent/adaptive/multi-GPU/entropy
settings fail rather than being silently ignored.

Diagnostics inspect one minibatch every 25 updates by default, report weighted
loss gradients before clipping, and never assign `.grad` or consume Torch RNG.
CPU float64 accumulation avoids requiring MPS float64. Flat/nonflat is not a
complete per-terrain diagnosis; extend a NEW observation metadata group for
finer conditions if the initial result warrants it.

For a separate transition-sampling arm, attach row-aligned `replay_labels` from
validated metadata and select `replay_sampling="transition"`. Both mode and
transition paths present exactly 512 replay rows/minibatch. Missing declared
phases reject training; do not silently backfill steady walking. Retention
coefficients are explicit candidates, not an automatic tuning schedule. The
world-space face helper does not on its own wire a new reward into native PPO.

The first learning comparison remains standing-only posture after independent
pose/equilibrium search and settling. Keep the original 30° acceptance gate;
25° was a proposed training margin, not evidence of physical impossibility.
A privileged critic is a separately justified future intervention, not bundled
with posture, sampling, retention weights or actor memory.

### Visual candidates

`retool.vision.make_follower("control")` wraps the retained pixel implementation.
`edge_speed` reduces only forward request near the observed circular marker's
image edge. It does not widen detector acceptance or infer hidden coordinates.
`reacquisition_yaw` limits only the upstream nonzero yaw-request slew; a fault
zero remains immediate. Motor actions remain raw/unfiltered in both arms.
These are hypotheses, not established fixes. Test one arm at a time with the
original camera geometry and frozen behavior gates; do not combine interventions.

## Test evidence and limitations

The original sandbox validation used a partial checkout. Its immutable
`experiments/retool-v1/local-validation.json` records 40 passes and two skips;
it is historical, not the current full-checkout result. Subsequent pinned CPU CI
passed all 42 tests. Review on the local Apple checkout passed all 46 candidate
tests after regression fixes and all 141 existing workspace tests, without skips.
Both doctors found the expected inputs; this is readiness, not native execution.
Synthetic physics/runtime doubles test sequencing and restoration contracts,
not MuJoCo correctness or actual daemon performance.

The new CI job uses a full checkout, CPU Torch 2.9.1 and pinned RSL-RL 5.4.2.
It also checks the default custom-PPO update against the original implementation
on synthetic batches and the real retained perception/follower interface.
Its resolved package list and test log are uploaded. Native numerical/behavior
experiments are not run by CI, and no CI pass changes the retained skill scores.

## Engineering references

MuJoCo's [simulation/state documentation](https://mujoco.readthedocs.io/en/stable/programming/simulation.html)
explains derived force timing, full data copies and warm starts. The
[PyTorch gradient API](https://docs.pytorch.org/docs/stable/generated/torch.autograd.grad.html)
returns gradients separately from parameter `.grad`. These are API references,
not evidence of our native execution. Project-specific diagnoses are retained
in the unchanged [review packet](PROCESS_REVIEW_20260916.md), V54/V55 results,
V63–V66 diagnostics and runtime/visual result documents.
