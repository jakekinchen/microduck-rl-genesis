# Turn historical failures into the next experiment

The concurrent workspace audit indexed 126 local Codex sessions (118,803 JSONL
lines, 2,777 extracted user/assistant messages) and 307 repository history
documents. Its coverage index and retrospective live in `docs/workspace/`.
This complementary slice reused that private text index, searched all extracted
messages by reward semantics, simulation gaps, runtime, orchestration, lineage
and physical-evidence themes, and inspected the cited primary logs and retained
traces. This is an indexed review with focused diagnosis, not an independent
reproduction of every historical command. Deleted, remote, unindexed or
differently named logs may be missing; active logs continue to grow.

## Highest-value lessons

| History source (relative to repository root) | Observed problem | Apply now |
|---|---|---|
| `../microduck-rl/BACKHEEL_RUN_LOG.md` and `KICK_ACTION_SUITE_RUN_LOG.md` | Motion consequence can conceal wrong heading/strike; a front candidate ended at 239/256 in a required bucket. | Define the motion and each required case/property bucket before reward design. Include a no-op and wrong-motion counterexample. |
| `../microduck-rl/KICK_ACTION_SUITE_RUN_LOG.md:374` and `:420` | Backheel 2248 passed vectorized cells but only 3/6 native profiles; next step was first-divergence replay. | Inspect action/state timing before more reward tuning or longer training. Use the new offline comparison to design, not substitute for, a controlled replay. |
| `docs/reviewer-messages/032-m5-deterministic-evidence-correction.md:11` | Rounding every compiled-model float hid non-inertia drift. | Preserve raw hashes. Limit a tolerance to the measured field; never normalize away action, mass or timing differences. |
| `docs/reviewer-messages/014-m2-pinned-bam-materializer.md` | A moving dependency branch was not reproducible authority. | Reuse the existing exact-commit materializer; never upgrade the active runtime as incidental cleanup. |
| `docs/reviewer-messages/022-m4-cpu-mps-crossover-1024.md` | Backend ranking changed with batch size. | Reuse measured 1024 Metal/MPS for the supported larger lane; small debug runs use only supported CPU options. Benchmark after a relevant change, outside other active training. |
| `experiments/laser/README.md` | v1 passed 2/6 C MuJoCo versus 5/6 Genesis; changed steering with unchanged policy later passed visible cases. | Name command adaptation separately from locomotion learning. Retain v1, v2 and the baseline ablation. |
| `experiments/laser/README.md` and camera-audit receipt | Target ground truth was not pixels; HOME camera faces opposite walking X. | Verify camera projection and frame conventions before choosing perception or policy training. |
| Current `AGENTS.md`, user instruction to preserve ongoing training | Historical role workflows were retired; simultaneous workers can touch live state. | Stay in the current task, use additive worktrees, inspect process ownership, stage exact paths, and avoid shared imports/runtime upgrades during training. |

## Minimal physics for the behavior

Start from the articulated rigid robot, gravity, contact geometry and BAM servo
model. Foot or ball behavior depends on actuator, contact and constraint
semantics together. MuJoCo describes how applied forces, constraints and
friction enter its dynamics in the [primary computation documentation](https://mujoco.readthedocs.io/en/stable/computation/index.html).
This reference informs probe design; it does not change the repository's lock.

| Request family | Add only what the outcome requires | Diagnostic before learning |
|---|---|---|
| Walk, turn, stop, command-driven dance | Existing rigid contact and servo dynamics | HOME settling; zero-command drift; small signed command steps; exact joint/action order and raw previous-action history. |
| Kick or push a ball | Explicit radius/mass/inertia plus sliding/rolling/contact response | Passive no-launch reset; sphere clearance; strike-foot/heading detection; low/high property corners; native same-action impact. |
| Jump or backflip | Correct inertia, saturation and all landing collisions | Ordinary unassisted start; takeoff/rotation/feet-first landing/continuous hold event sequence; reject head support and assisted resets. |
| Follow a visual target | Calibrated camera, perception, confidence and latency | Render known points; camera/body/world sign test; stale/dropout stop; occlusion and reacquisition; no oracle coordinates in deployed actor inputs. |
| Uneven terrain | Contact geometry over a declared slope/step envelope | Support-contact audit, penetration, passive settle and no hidden supports before curriculum. |
| Sound following or soft-object interaction | A measured bearing/deformation need first | Prove the available sensor observes the target quantity before adding acoustic or deformable solvers. |

Genesis distinguishes viewer rendering and sensor observations in its
[camera sensor documentation](https://genesis-world.readthedocs.io/en/latest/user_guide/sensing/camera_sensors.html).
Latest documentation is conceptual guidance, not proof that a new API exists
in the pinned 1.3.3 installation. Do not upgrade while a run is active.

## Short decision sequence for a failed behavior

1. **Observation/frame:** Can the deployed actor observe the requested cue?
   Check the source of each feature, not just the observation dimension.
2. **Reset/contract:** Are model variant, HOME, qpos/qvel, action order, delay
   buffer, normalizer and dt/decimation matched?
3. **Command response:** Does the existing motor policy respond to small signed
   commands? Compare against its unchanged baseline.
4. **First-step dynamics:** Compare pre/post-step position, applied torques and
   contact state before feedback produces different actions.
5. **Learning/objective:** Only once the task and dynamics are reachable, alter
   one reward/curriculum hypothesis and preregister a new visible-development
   comparison. Separate failure counts by case; do not average away misses.
6. **New evidence:** Freeze the candidate and use fresh evaluation conditions
   when repeated development tuning has consumed the original suite's value.

## Agent operations and skill use

Use the repo's `microduck-experiments` skill and behavior guide for task design;
use `duck status`/Duck Lab for the current evidence; use `duck-ops` when an active
process or first-divergence question exists. A skill should resolve a concrete
decision, not start another workflow merely because its name contains agent,
research or GPU. Current repository instructions supersede historical prompts.

Keep one hypothesis, one bounded run and one next decision in experiment notes.
Record request-to-smoke time, request-to-independent-evaluation time, transitions,
wall time, required-bucket failures and the intervention count. External blocked
time belongs in a separate field. File count, token spend, commit count, reward
and checkpoint size are not measures of learning success.

While training is active, restrict workspace improvements to disjoint source
paths and lightweight tests. No environment sync, cache deletion, benchmark,
global process cleanup or common evaluator/model changes. Leave incomplete
active outputs alone. Retain negatives and archive only after evidence is
copied and checked; never remove large artifacts just because they are large.

This work has not used or provisioned Brev. Historical failures do not authorize
another paid pilot. For any future explicitly Brev-backed task, bind cost and
duration, test the exact install recipe, retain outputs, and verify teardown.
