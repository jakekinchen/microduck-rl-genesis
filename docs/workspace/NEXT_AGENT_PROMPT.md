# Continue MicroDuck after PR #1

Work in `/Users/kelly/Developer/microduck-rl-genesis` as a single agent. Continue
from [PR #1](https://github.com/jakekinchen/microduck-rl-genesis/pull/1),
“Implement methodology-review foundations and bounded skill-improvement plan.”
Check its merge state and the live checkout before relying on this handoff.

## What we are trying to achieve

Build Ducky a useful, composable skill set: reliable standing, walking, turning,
stopping, and camera-driven following, then broader terrain and recovery skills.
We ultimately want credible walking across unfamiliar surfaces, including carpet.
Progress means better measured behavior within a stated operating envelope, not
more training runs, tests, or convincing videos.

The methodology review is accepted. Keep PPO, the retained policies and the
native BAM actuator model while testing specific failure hypotheses. Do not
restart an open-ended framework search. A switch of simulator or learning stack
needs a matched comparison showing a useful behavior, cost, or throughput gain.

## Read and verify first

Read `AGENTS.md`, `GOAL.md`, `TRAINING_ACTUALIZATION.md`,
`docs/workspace/RETOOLING_20260916.md`, `docs/workspace/PR1_REVIEW_20260916.md`,
and `docs/workspace/BEHAVIOR_VALIDATION.md`. Use the experiment skill and
`BEHAVIOR_WORKFLOW.md` when designing the next experiment. Consult
`PROCESS_REVIEW_20260916.md` for the supporting history, not every old role log.
The ordered queue is authoritative; this prompt explains how to resume it.

Inspect the branch, worktree, origin and any running jobs. Run `./scripts/duck
status`, `./scripts/duck doctor`, and `.venv-apple/bin/python -m retool doctor`.
The workspace viewer deliberately refuses external symlinks: its inspection
errors are not evidence that those experiments failed or disappeared. Locate
and hash-check the retained external artifacts directly. The guide at
`docs/workspace/publication-20260916/README.md` explains the published evidence
archive if restoration is necessary. Preserve existing dirty work and receipts.

## What PR #1 does and does not establish

It adds opt-in replay sampling, learning diagnostics, checkpoint/impact helpers,
a simulation body interface, two separate camera-command candidates, and
comparison reporting. Review fixed incomplete-trace acceptance and missing
comparison identities. The 46 candidate tests and 141 workspace tests pass;
the PPO parity test uses synthetic batches and the follower test checks its
retained interface. Neither establishes native trainer or robot behavior.

V21 walking, V15 standing and V30 heading remain retained. V54 shared is only
a development initializer. V54/V55 still pass 5/14 exposed surface sessions;
visual following still passes 11/16 required cases. V62 is an offline detailed
geometry reference. V66's guided ankle benchmark does not validate full-robot
physics. Actual Rust/body integration, the new native impact experiments, and
the new learning and RGB comparisons remain unfinished.

## Your first deliverable

Complete the bounded numerical/model decision in stage 1 of the queue. Answer:
can we reproduce the retained native state exactly, and which model/integration
choice is defensible for the next behavior experiment?

1. Recover and verify the relevant V11/V62 models and V65 evidence. Create a
   new experiment directory. Before looking at candidate outcomes, freeze its
   sources, input schedules, cases, rates, thresholds, budget and stopping rule.
2. Capture the complete native state at 0.035 seconds, including solver state,
   BAM history, motor/sensor delay queues and applied damping/friction. Require
   exact 5 ms clone controls against the V65 reference before changing rates.
   A positions/velocities file alone is insufficient. If the clone fails,
   diagnose that first; a finer-rate result would be uninterpretable.
3. Run the single declared 0.035–0.135 second comparison per model/rate. Separate
   fixed recorded actuator outputs from live BAM feedback; keep BAM at 200 Hz.
   Inspect complete state/contact/load traces. Root-position agreement alone
   is insufficient. Do not automatically extend the window or add finer rates.
4. Write an explicit retain/revise/reject decision. For a selected diagnostic
   model, run bounded closed-loop standing and walk–stop with unchanged gates.
   Audit any proposed simpler collision model against the detailed reference,
   preserving support and dangerous body contacts. Do not disable real contacts
   to obtain a pass. If no model qualifies, record that negative conclusion and
   the specific next intervention instead of starting another unbounded sweep.

## What follows that decision

Continue the existing queue as prerequisites permit: connect the actual Rust
scheduler and observation builder to the body interface; demonstrate startup,
stand → walk → turn → stop conformance; reproduce the flat RGB bank and test
one camera candidate; then establish standing feasibility and run one
instrumented posture-learning comparison with three matched seeds. Sampling,
retention weights, privileged critic and actor memory are separate interventions.
The queue supplies exact seeds and gates. Flat camera development can remain a
separate scoped task if broader model admission is blocked; serialize compute.

Expand the walking operating envelope through explicit terrain families and
unseen combinations once retained behavior passes. Do not assume a separately
named “carpet skill” is necessary, or that more randomization guarantees it.
Use research and public data to justify parameter priors. Do not require new
measurements from the user to continue simulation work, and do not represent
those priors as measurement-based calibration of this particular robot/carpet.

## How to work and finish

Use one active milestone, one testable hypothesis per comparison, fixed budgets,
and a clear decision at the end. Change versioned candidate code rather than
old source-frozen V1–V66 implementations. Keep the deployed 61D observation /
14D action, 50 Hz interface and raw policy actions unless an experiment explicitly
versions a change. Run `./scripts/duck-ops guard && <command>` in the same shell
operation before simulation or training. Never overlap competing compute jobs.
Use `./scripts/duck verify` for tooling changes and the candidate suite for
`retool` changes; passing software tests is not behavior acceptance.

Preserve per-case failures, negative results, continuous-state transitions,
contact/slip/joint-stop/non-foot-support telemetry, endurance, and separate
exposed and protected banks. Missing evidence is unknown, not a pass. Follow
current authority for protected data, publication and merges. Do not start paid
compute, operate hardware or activate a policy without the necessary authority.
No subagents, role cycles or autonomous goal loops. If authorized Brev work is
ever used, shut down idle resources and verify their final state.

Finish the first deliverable with a concise result, receipt paths, exact failed
gates, resource use and the next best experiment justified by what you learned.
Update `GOAL.md` and the existing queue. Keep the distinction between a useful
simulation capability, a validated model, and physical acceptance explicit.
