# Dynamic laser pursuit build

Superseded walking-quality claim: these are target-only development results.
The owner identified abnormal gait. See [the systemic gait diagnosis and
correction](GAIT_DIAGNOSIS.md); the selected turn-v2 policy is rejected for gait.
Historical receipt bytes and counts below remain unchanged.

Request: moving and manually controlled red dot, stronger behavior under varied environments.
Repo: `/Users/kelly/Developer/microduck-rl-genesis`. Started 2026-09-05.
Owner constraints: single agent; local compute; preserve old evidence; no hardware or publication.

## Design and acceptance

The live physics viewport is the hero. A top-down pad shares target and robot
positions, so a drag has an immediately understandable consequence.

Color tokens: sheet `#eaf2f8`, ink `#16344a`, stage `#102c40`, blue `#286188`,
duck yellow `#efc847`, target red `#d62938`. Avenir Next for human-facing type;
tabular numerals in the same face for measurements. Type scale 14/16/22/36/54.
Left-aligned desktop layout: large stage (two thirds), control pad (one third);
on small screens, stage then controls. No ornamental dashboard cards.

```text
Move the dot. Watch the duck.               pause / reset
┌──────────────────────────────┬─────────────────┐
│ actual simulated robot       │ drag target map │
│ yellow duck / red dot trails │ route / terrain │
└──────────────────────────────┴─────────────────┘
gap / simulation time / measured speed / evidence boundary
```

Design critique before implementation: a metrics-first control dashboard would
hide the requested interaction. Make the stage dominant and attach controls to
the map. The palette identifies the physical traces, not arbitrary statuses.
No automatic entrance animations. Start paused; motion follows explicit Play.

Acceptance: manual and three reproducible moving routes; explicit loss and
reacquisition; fresh-world domain changes; no action assistance or auto-reset;
bounded local PPO and independent C MuJoCo/BAM evaluation against the previous
policy; reserved development seeds used only after freezing candidate choice.

## Implementation and provenance

One Codex task implements and verifies everything. AI Build Pipeline separates
core, integration, presentation, and measured proof; frontend-design informs the
control-pad layout. MuJoCo supplies every robot frame, not generated artwork.
The robot and BAM assets are the existing immutable evaluator assets.

Physical randomization follows established locomotion practice in
[legged_gym](https://github.com/leggedrobotics/legged_gym): friction, mass,
actuation, sensor noise/delay, and pushes. This is ordinary domain randomization,
not an RMA adaptation module. Exact training ranges live in
`microduck/laser_robust_env.py`; frozen test draws in `microduck/laser_dynamics.py`.

## Verification

The first robust pass completed 400 iterations / 9,830,400 new transitions in
1,102.4 seconds including startup. It retained the original 6/6 simpler cases,
but harder dynamic cases remained 1/6 on randomized development and 0/3 on
nominal routes. No falls occurred. This is not an improved pass-count result.
Both policies and all negative trajectories/videos are retained.

`turn-correction-v2.json` records the subsequent, bounded 250-iteration reward
intervention and its selection rule. Actual yaw stagnation is measured; reward
imbalance as its cause is an experimental hypothesis. No test thresholds or
target routes were relaxed. No reserved seeds had been realized at nomination.

The initial full BAM-enabled repository suite passed, with the generic deployment test
explicitly not applicable because `logs/microduck-velocity` has no checkpoint.
The actual laser exports separately run random and real-observation ONNX parity.
Eleven focused dynamic tests cover routes/dropouts, deterministic domain draws,
rejection of a stationary no-op, reward gating, real parameter randomization,
instant target-loss commands despite sensor lag, invalid actions/targets, and
loopback-only bounded HTTP controls.

A final broad rerun passed every applicable group except a test-fixture
assumption: it bound uncommitted `AGENTS.md` workspace edits to HEAD. The
admission fixture now uses the unchanged invariant `microduck/constants.py`
source, and a new negative probe confirms committed-source drift is still
rejected. Production admission code and frozen receipts were not changed.
The focused admission rerun passed; both broad logs and the rerun are retained.

Browser QA used the actual live server: Play/Pause, drag placement, keyboard
nudge, hide/show, figure-eight selection, and randomized-domain reset. Desktop
and 390×844 mobile layouts were inspected. The pad changed from circular to
square so the complete ±1 m control region stays visible; mobile copy spacing
was corrected. Rendering now frames the duck and dot together without changing
their physics. Paused rendering is cached to avoid idle graphics work.
The existing Duck Lab viewer also discovers the new nominal/development
receipts without an adapter change: its comparison shows 3/3 versus 0/3 and
verifies the case manifests. Reserved records remain excluded from that viewer.

An aborted helper initialization is retained in `20260905-baseline-dev/` and
explicitly excluded from behavior counts. A learning-curve packaging bug for
the first iterations (no completed episode yet) was fixed: missing episode
duration stays unknown, not zero, and retries only reuse byte-identical logs.

## Run the interactive playground

Use the chosen receipt recorded below after evaluation. The server binds only
`127.0.0.1`, starts paused, expires after 30 minutes by default, and rejects
foreign origins, invalid coordinates, arbitrary action commands, and log
overwrites. It operates only the local simulator.

```sh
.venv-apple/bin/python scripts/laser_playground.py \
  --policy-receipt receipts/laser-dynamic/20260905-turn-dev \
  --bam-repo /private/tmp/microduck-bam-authority-exact \
  --event-log /private/tmp/laser-playground-NEW.jsonl
```

Open `http://127.0.0.1:8947`. Press Play. Drag or use arrow keys on the map;
switch among waypoints, circle, figure eight, or manual placement. Domain
changes and Reset start a fresh paused trial. A fall requires explicit reset.
Interactive waypoints repeat every 48 seconds; the frozen evaluator still
measures exactly one 48-second route. The delivered server uses a one-hour
lifetime; the launch command above uses the 30-minute default.
Speed is actual robot speed and the clock is simulation time; the viewer does
not promise wall-clock real-time speed under resource contention.

For reproduction, `scripts/train_laser_robust.py` and
`scripts/train_laser_turn.py` accept unique run IDs and bounded budgets. Use
`scripts/evaluate_laser_dynamic.py --run-id RUN --split development` with
`--bam-repo` and a new `--output` folder. The `--video` flag saves 25 fps frames
from the 50 Hz rollout: each complete route is 48 seconds, not sped up.

## Final measured result

Selected ONNX: `7d634c6f64178f1bbb8cbe3a4129418ad8661dad6abfbaae3ac533244c3d0fed`.
The choice was frozen in `receipts/laser-dynamic/candidate-freeze.json` before
realizing the 12 reserved development draws. No subsequent tuning occurred.

| Fixed suite | Original laser policy | First DR pass | Turn-corrected policy |
| --- | --- | --- | --- |
| Original laser regression | 6/6 | 6/6 | 6/6 |
| Nominal dynamic routes | 0/3 | 0/3 | 3/3 |
| Randomized development | 1/6, no falls | 1/6, no falls | 5/6, one fall |
| Reserved randomized development | 2/12, no falls | Not evaluated | 11/12, one fall |

The final policy acquires all six waypoints in the nominal route and both
randomized development retarget cases. Nominal circle tracking stays within
30 cm for 100% of post-warmup samples; figure-eight tracking does so for 94.1%.
The duck keeps an intentional stand-off; it is not commanded to step on the dot.

Failures: development seed 75003 falls at 1.56 s; reserved seed 75109 falls at
1.36 s. Both are preserved. Early falls have no post-5-second distance metric;
they remain failed cases rather than becoming zero-distance scores or vanishing
from the pass denominator. This is improved pursuit, not complete robustness.

The turning run completed 250 iterations / 6,144,000 new transitions in
1,382.2 seconds including startup. Combined new main-run budget: 15,974,400
transitions; total selected-policy lineage: 30,720,000. The separate 64×5 smoke
adds 7,680 transitions but is not in that policy lineage. All compute was local.

Random-probe Torch/ONNX maximum error: 7.629e-6 rad; real-observation error:
3.338e-6 rad. Repeated development evaluation matches all 12,078 semantic rows
exactly, including the fall, excluding only measured inference latency.
`replay-equality.json` retains the canonical trajectory digest.

Videos: `receipts/laser-dynamic/20260905-turn-nominal/75201-retarget.mp4`,
`75202-circle.mp4`, and `75203-figure-eight.mp4`; each 48 s, 25 fps, 720×480.
The comparison JSON, raw training/evaluation records, source snapshots,
checkpoints, normalizers, and nested SHA-256 manifests are retained under
`receipts/laser-dynamic/`. The AI build workflow deliberately keeps this
interactive presentation separate from the randomized behavior evidence.

## Remaining work

Simulator target coordinates, not onboard camera perception. Flat ground only;
visual palette changes are presentation, not proof of lighting robustness.
No obstacle avoidance, uneven terrain, canonical blind acceptance, or hardware
authority. Frozen reserved *development* seeds are separate from the canonical
held-out evaluation, which remains unopened.

## Follow-up queue

See `TRAINING_ACTUALIZATION.md` for the ordered active work and remaining gates.
