# Training a requested behavior on the Mac

Use the existing Genesis/BAM learner and C MuJoCo evaluator as the foundation.
The goal is a short, reproducible route from a request to a measured behavior.
This guide does not imply every requested behavior is physically achievable,
observable with the available sensors, or learnable within a particular budget.

## Start and inspect

```sh
./scripts/duck status
./scripts/duck prepare                # current case, source bindings and next experiment prerequisites
./scripts/duck doctor
./scripts/duck studio                 # http://127.0.0.1:8766
```

`status` projects `GOAL.md`, `TRAINING_ACTUALIZATION.md`, visible development
receipts and recorded training metadata. It creates no replacement queue.
`doctor` checks package/MPS availability and frozen contract drift without
stepping physics. It reports missing BAM separately. It is not a smoke test.

For the current laser startup investigation, follow
[the applied experiment brief](ACTIVE_EXPERIMENT.md). Run `prepare` before
reproducing that case and inspect the first failure before selecting a new
reward or domain intervention. It does not launch training or grant a budget.

For a portable local BAM checkout, use the existing immutable materializer:

```sh
.venv-apple/bin/python scripts/materialize_bam_authority.py .workspace/bam
export BAM_REPO="$PWD/.workspace/bam"
./scripts/duck doctor
```

`.workspace/` is disposable local tooling state, excluded from Git. Never keep
the sole copy of experiment evidence there. The reference dependency is pinned
at `62bd8ce12154340be97e06f7f41a0ca8f116d967`; branch names are not authority.

Duck Lab plays retained case videos with matching case time, robot/target
paths, distance, speed and inference snapshots. The comparison defaults to the
retained laser baseline and v2 development result; this is navigation, not
candidate selection. With an active-workspace file, the current source-checked
development case opens instead. The timeline uses recorded simulation seconds;
video offsets follow the retained capture schedule (first frame at 20 ms for
legacy laser, 40 ms for dynamic laser). Refresh discovers new reports.
The training view refreshes every 15 seconds while visible and reads optional
TensorBoard reward/iteration telemetry. A last logged iteration or a
`starting` receipt is not proof of process liveness. For detailed live losses:

```sh
.venv-apple/bin/tensorboard --logdir logs --host 127.0.0.1 --port 6006
```

The current metric adapters support `microduck.laser-evaluation/v1` and the
nominal/development splits of `microduck.dynamic-laser-evaluation/v1`.
Reserved/held-out/acceptance-named folders are excluded before parsing. Other
visible-development schemas remain discoverable through `duck status`; add a
small tested reader when a new schema is introduced. The viewer serves only
indexed development artifacts, has no execution endpoint, and never searches
hidden acceptance suites. Manifest verification checks integrity against the
local manifest; it does not independently validate provenance or classifier
correctness.

For the first divergent trace sample or an advisory inventory of running jobs,
use `./scripts/duck-ops compare`, `activity` and `guard` as documented in the
[offline diagnostics guide](../experiment-ops/README.md). The guard cannot
reserve the Mac or prove it is idle. A comparison of parsed action values
cannot prove original tensor-byte identity or identify a physics cause.

For source-bound metadata inspection across projects, use the additive
[workspace exchange](exchange/README.md). The two robot runtimes, policies,
training commands and acceptance gates remain separately defined.

## Turn the request into an experiment

```sh
./scripts/duck new turn-to-sound --request "Turn toward a sound source"
./scripts/duck check-spec experiments/behaviors/turn-to-sound/spec.json
```

The generator creates a draft and notes file and refuses overwrites. It does
not invent a reward, implement an environment or start training. `check-spec`
checks completeness only; its output cannot authorize execution.

Before implementation, answer these questions in the behavior spec:

| Decision | Concrete example |
|---|---|
| What should the robot do? | Face a visible target within 2 s and hold orientation for 1 s. |
| How is success measured? | Heading error, acquisition time, overshoot, falls; predeclare limits. |
| What can the deployed actor observe? | Existing proprioception and an upstream command adapter; no hidden target pose masquerading as pixels. |
| What may the critic/reward see? | Simulation state explicitly marked privileged and excluded from deployment. |
| Does this need a new learned motor behavior? | Waypoint following can reuse locomotion; a kick or jump changes contact dynamics. |
| Which physics can determine the outcome? | Foot contact and servo limits for a turn; ball rolling and impact for a kick. |
| What is the baseline? | Zero command, existing walking policy, or previous first-party checkpoint with explicit lineage. |
| What result decides the next step? | If small commands fail in both engines, diagnose command response before adding training time. |

For sound, first define an observable bearing estimate, noise and delay. A
request to turn toward sound does not automatically justify an acoustic wave
solver or imply the microphone can localize direction. The same distinction
applies to vision, balance, navigation and manipulation.

## Choose the smallest useful physics scope

| Behavior family | Start with | Before training, prove |
|---|---|---|
| Walk, turn, stop, dance via commands | Existing rigid robot, plane, BAM, body/head command contract | Joint order, actuator/reset conformance, stable nominal state, zero-action baseline. |
| Rough-ground locomotion | Versioned heightfield/collision geometry | Foot support, step/slope envelope, collision counts and passive settling. |
| Front kick/backheel/lateral pass | Explicit sphere mass/radius/inertia, friction, rolling/contact response | No initial overlap or passive launch; correct strike foot/direction; native property envelope. |
| Jump/backflip | Correct mass/inertia, all required body collisions, actuator saturation and contact timing | Ordinary-start, zero-assistance takeoff/rotation/feet-first landing/continuous hold classifier. |
| Visual target following | Rigid locomotion plus calibrated camera and a perception/command adapter | Camera axes/FOV, metric projection, confidence, stale frame stop, occlusion and reacquisition. |
| Deformable interaction | Add a deformable solver only when deformation changes task success | A measured deformation/contact requirement and a bounded performance/conformance spike. |

Keep six model variants distinct. Do not copy parameters between tasks simply
because the MJCF files look alike. Preserve the current 61D actor, 14D servo
order, normalized ONNX and 50 Hz unfiltered action loop for compatible tasks.
If a behavior requires more deployed observations or another actuator, version
the interface and evaluator deliberately rather than squeezing hidden state
into the existing contract.

At the physics boundary, validate mass/inertia, joint limits, reset populations,
contact geometry/masks, timestep/decimation, friction and servo current/torque
limits. BAM's friction/constraint coupling matters as much as its motor formula.
Do not tune rendering, contact stiffness, gravity, clipping or assistance to
make a video look successful. Record every intentional training-only aid and
remove it from the acceptance start population.

## Run a bounded learning cycle in this task

1. Read current instructions and the ordered queue. Inspect dirty files and
   existing processes. Keep concurrent work separate by file scope or worktree;
   no role cycles or delegated review are needed.
2. Establish task reachability: reset, observation, command, action, reward,
   termination, export, evaluator and rendered case. Test the fragile boundary
   rather than adding a new receipt framework for every task.
3. Freeze a **visible-development** suite and baseline before reading the new
   outcome. Include failures that can earn high reward: standing still,
   wrong-direction contact, support from the head, target teleport reward,
   lost-target motion, and assisted starts where applicable.
4. Run an authorized 64×5 smoke in the correct task lane. Measure total PPO
   iteration time. General walking/backflip support CPU+MPS; the historical
   laser entrypoint explicitly uses Metal, so do not invent a CPU flag for it.
5. Use the measured 1024 Metal+MPS setting for a bounded longer local run when
   appropriate. Record the requested transition budget, public seed, parent
   checkpoint, versions, source bytes and final checkpoint. Preserve stdout
   and learning curves. A setup exception should produce a terminal record,
   including exceptions before `runner.learn`.
6. Export with normalization and check Torch/ONNX on random and real
   observations. Evaluate the exact ONNX in the independent C MuJoCo/BAM lane.
   Inspect case videos and task metrics in Duck Lab.
7. If it fails, classify the first problem: sensing/frame convention, command
   response, policy, observation/action contract, actuator, reset or contact.
   Compare identical case/seed/model variants. For a physics-isolation replay,
   preserve the exact action bytes; changing the command adapter is a separate
   intervention, as in the retained laser v2 experiment.
8. Change one hypothesis, retain the negative, and freeze a new named
   intervention. Never relax the same acceptance threshold after seeing a
   failure. After repeated tuning, use fresh development data and preserve
   blind acceptance data for a separate candidate-freeze gate.
9. Record the outcome, receipt path, elapsed time/transitions, and next decision
   in the experiment notes. Update the current queue/status concisely. Make no
   new records in historical role-cycle directories.

Keep immutable source bindings intact. In particular, M5 hashes bind shared
files: changing them for an unrelated behavior can invalidate old export or
comparison paths. Prefer a separate behavior module and a versioned adapter;
do not regenerate frozen receipts to fit the current checkout.

## Use skills when they change the decision

- **microduck-experiments**: repository-local training, simulation and diagnosis.
- **frontend-design**: substantial changes to experiment inspection UI.
- **refactor-score**: ranking a specific cleanup or performance opportunity.
- **OpenAI Docs / skill-creator**: Codex configuration or a requested skill change.
- **brev-cli**: only a specifically authorized Brev task; retain teardown proof.
- **advisors-skill**: a bounded external research question when uncertainty
  materially blocks progress and the information-sharing scope is appropriate.

Do not trigger autonomous-project-workflow, role pairs, deep research or a
cloud service just because an experiment mentions agents, research or GPUs.
Routine fixes and local review stay in this single task. Ask for user input
when the desired behavior or authority is genuinely missing, after doing the
independent work that makes the question concrete.
