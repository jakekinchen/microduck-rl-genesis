# September 16 review entry point

The [process-review packet](PROCESS_REVIEW_20260916.md) reconciles subsequent
walking, terrain, runtime, perception and V62–V66 physics work. The dated audit
below remains historical evidence. Private session extracts under `.workspace/`
are excluded from publication; the repository contains the resulting lessons,
coverage metadata and experiment evidence.

# MicroDuck experiment retrospective and workspace improvements

Audit date: 2026-09-05. Initial Genesis checkout: `eabc933e2562` on `main`.
This is a retrospective and an implementation report, not a new policy result.

## Main conclusion

The Mac is already a useful robot-learning workstation. The next improvement
is a tighter connection between behavior requests, task physics, measurable
evaluation and inspection. More orchestration, larger training budgets and
more elaborate provenance paperwork alone will not make the duck do the
requested behavior.

The productive pattern is visible in the laser result: retain the negative,
localize why it failed, change one component, and test the unchanged baseline
under the same intervention. Preserve the serious evidence controls, but keep
external artifact admission separate from first-party development.

## Coverage and limits of this review

The audit queried the local Codex SQLite index read-only for MicroDuck paths,
titles and initial messages, including archived tasks and worktrees. It also
included the separately named laser task
`01a05ebe-bcf2-7ce2-821a-b1c5c6ebba59` and the original checkout naming task
`01a04bac-eb76-7de0-a98c-7d573e3090f6`, found through the prior-context registry.
Tasks created on September 5 for this workspace audit were excluded. The scan
read **126 session files, 118,803 JSONL lines**, and extracted **2,777 user and
assistant text messages**. It did not attempt to interpret encrypted reasoning.

The repository corpus contains **307 historical Markdown logs/briefs**:
170 files / 11,135 lines in this Genesis checkout, and 137 files / 19,236 lines
in `../microduck-rl`. These include all available `docs/briefs`,
`docs/session-logs`, `docs/reviewer-messages`, `docs/manager-log`, and root run
logs at the scan snapshot. Decision/failure passages and the primary training,
physics, export and evaluator sources were inspected in depth. This is a
systematic indexed review with focused source inspection, not a claim that
every historical tool action was independently reproduced.

`history-coverage.json` records the source paths, hashes and line counts at the
scan time. The local source corpus and extracted text are in
`.workspace/history-20260905-final/`; private raw conversation text is not added
to version control or served by the web viewer. Local session files can continue to
grow after the scan. The SQLite discovery rule can miss a differently named,
unindexed, remote or deleted task; those are not claimed as covered.

Reproduce or extend discovery into a new private local output directory:

```sh
.venv-apple/bin/python scripts/scan_microduck_history.py --before 2026-09-05 \
  --extra-thread 01a05ebe-bcf2-7ce2-821a-b1c5c6ebba59 \
  --extra-thread 01a04bac-eb76-7de0-a98c-7d573e3090f6 \
  --output .workspace/history-NEW
```

The sibling `sim2claw` was inspected read-only. No implementation, runtime,
checkpoint, physical data or orchestration system was copied from it. Current
MicroDuck instructions explicitly retire role cycles and supersede old logs.
New dynamic-laser work appeared concurrently; it is separate from this audit's
initial evidence snapshot and is not promoted here.

## What the experiments actually taught us

| Experiment / stage | Evidence | Learning for the next behavior |
|---|---|---|
| Initial backheel, Aug 28 | Checkpoint 250 achieved speed by turning around; final nominal policy 1750 had a stronger heading/foot/handoff battery. | Encode the requested motion, not just its consequence. A ball moving backward is insufficient to establish a backheel. |
| Expanded kick suite, Aug 29 | Front 3616 ended at 239/256 in a required bucket. Backheel 2248 passed vectorized development and validation but only 3/6 native property profiles. | Bucketed stress tests and native deployment rehearsal can reverse an apparently positive result. Preserve the nominal success and expanded-envelope failure as different claims. |
| Early Apple preflight | Metal stepping and MPS learning were feasible; geometry accounting mixed visual/collision domains. Later receipt corrections caught impossible DOF mappings and CPU conversions inside a supposedly CPU-free interval. | Observe the candidate backend directly. Separate a finite step, semantic conformance and performance measurements. Classify fields instead of comparing unlike counts. |
| Dependency/runtime work | A moved BAM branch broke reproducibility; CUDA needed a specific Torch wheel source. | Pin immutable objects and package indexes. Test the exact installation command before paying for a runtime. |
| M0–M3 actualization | Clean-clone smokes, 61D/14D/50 Hz contracts, six model variants, BAM fixtures, independent C MuJoCo evaluation and synthetic success classifiers were established. | Reuse this foundation. Synthetic positive classifier fixtures prove the classifier's logic, not a learned behavior. |
| M4 scaling | CPU+MPS won the 64–512 grid; Metal+MPS won at 1024; 120 sustained iterations were finite. | Choose backend and batch size by total PPO time. Thermals and peak RSS were declared proxies, not exhaustive hardware measurements. |
| M5 CUDA attempts | Seven bounded pilots ended negative: runtime/installation, frozen evidence/determinism, then four provisioning/readiness failures. | Separate code failure from provider failure. Local preflight before provisioning; no unchanged retry loop. Historical authorization is consumed. |
| M6 artifact provenance | Official/community artifacts lacked immutable roles; legacy media/policies remained quarantined. Broad queue progress initially stopped at that boundary. | Preserve artifact admission rules while giving first-party development its own explicit lane. Do not make an unavailable third-party history a universal learning blocker. |
| First-party walking, Sep 4 | 2,457,600 transitions; normalized ONNX parity and deterministic development replay; near-standing behavior. | A correct pipeline can produce an ineffective policy. Evaluate behavior before presenting the checkpoint as useful. |
| Laser v1 and v2, Sep 4 | Same trained policy: v1 2/6 C MuJoCo versus 5/6 Genesis; v2 command gain 3/s instead of 1.5/s passed 6/6 in each. Old baseline with the new gain stayed at 2/6. | Diagnose small-command response and separate locomotion learning from command adaptation. Retain the failed result and a baseline ablation. |
| Camera audit | Simulated ground-truth targeting; HOME head-camera optical forward is −X, opposite positive walking X. | Viewer pixels and onboard pixels are different interfaces. Verify frame geometry before claiming camera control. |
| Walking contact audit, Sep 5 | Actual raw-CAD battery/leg intersections in v9; every old current-sensor trace fails the new self-contact gate. The reduced model omitted battery contacts, while the bundled full model also changed leg masks. The corrected model retains mass/joints/visuals and the same v9 actor completes all 21 without falls. | Visual meshes, floor clearance and a model filename did not establish body-contact coverage. Verify exact collider identities and active pair filters before reward tuning. Separate copied-pose geometry, exact-action replay and closed-loop control evidence. |
| Heading and delay separation, Sep 5 | Corrected-model raw v9 actor passes 6/21 combined; explicit upstream IMU heading feedback passes 17/21 with heading 21/21. Four long-delay moving-yaw errors still fail. | Score against the user's command, retain the actor's distinct command input, and do not let a heading-controller pass hide locomotion-rate failures. Stable heading and stable instantaneous yaw are different properties. |
| Internal body bracing, Sep 6 | V13 can hold a small-penetration pose while loading its legs against the battery at about 14.93 N summed native normal force. Adding a read-only 200-Hz force observer preserves all original qpos/action bytes but rejects all 21. | Geometry alone does not prove physically credible support. Require sustained-load rejection as well as collider coverage, and keep simulator force conventions distinct. V15 reward gating fixes standing but does not automatically fix the separate walking actor. |
| Repeated transitions, Sep 6 | V15 paired actors pass 21 original cases but only 33/42 new repeated windows: four STOP falls and one WALK-start bracing failure. V16 command slew improves the six-case diagnosis to 5/6; gentler yaw V17 regresses to 4/6. | Test continued state across repeated starts/stops, not just fresh resets. Standing quality, walking quality and safe actor handoffs are separate properties. Keep the best nominal demonstration subordinate to failed required transition cases; do not keep tuning acceleration when the measured defect persists in the learned gait. |

Primary local anchors:

- `../microduck-rl/BACKHEEL_RUN_LOG.md` and
  `../microduck-rl/KICK_ACTION_SUITE_RUN_LOG.md` — nominal success, reward hacks,
  rejected lineages, per-ball envelope and the exact-action-diff next step.
- `../microduck-rl/docs/reviewer-messages/003-nudge-genesis-semantic-evidence.md`,
  `005-nudge-genesis-control-receipt.md`, `006-nudge-genesis-receipt-fail-closed.md`,
  `008-redirect-genesis-walk-runtime-proof.md` — observed defects in claims and
  mapping/runtime checks.
- `docs/reviewer-messages/014-m2-pinned-bam-materializer.md`,
  `029-m5-linux-cuda-runtime-reconciliation.md`,
  `031-m5-second-cuda-pilot.md`, `032-m5-deterministic-evidence-correction.md`,
  `046-m5-seventh-cuda-pilot.md` — dependency/provisioning and determinism lessons.
- `docs/reviewer-messages/049-m6-local-provenance-archaeology.md`,
  `051-m6-local-distribution-gate.md`, `053-m6-external-authority-handoff.md` —
  validator completeness, portable archive bytes and the real upstream limit.
- `experiments/first_party/DEVELOPMENT-AMENDMENT-v1.md`,
  `experiments/laser/README.md`, and `receipts/laser-follow/` — productive local
  development, diagnostic comparisons, ablation and camera boundary.
- `experiments/walking/RESULTS.md`, `receipts/walking/20260905-v9-raw-cad-intersections-r2/`,
  `20260905-v11-native-baseline/` and `20260905-v12-current-sensor/` (the latter
  two under `receipts/walking/`) — contact witnesses, corrected-model baseline
  and separately labeled heading-controller result; not physical acceptance.

These paths are relative to the Genesis repository root, not this document.

## Environment and physics strategy

Keep Genesis for local parallel training and the existing C MuJoCo/BAM CPU
evaluator for independent measurements. “Any requested behavior” needs a family
of task definitions, not one universal reward. Locomotion commands, contact
skills, perception-driven behaviors and deformable interactions require
different observability and physics contracts.

Start with articulated rigid-body dynamics, gravity, foot/object contacts,
joint limits and the existing servo model. Preserve mass/inertia and actuator
friction/current limits. Validate reset contacts and passive behavior before
learning. Add ball dynamics for kicks, terrain contact for rough locomotion,
or sensor latency/noise and calibrated projection for perception. Add soft-body,
fluid or acoustic physics only if it changes the success criterion and there
is an observable calibration target.

For contact/solver tuning, use small, diagnostic probes: passive settling,
one-servo response, friction/slide, loaded-foot contact, and exact-action replay
at the first diverging event. Separate commanded actions from forces, states
and detected contacts. Fixing a contact gap by altering the policy actions
would invalidate the comparison.

Genesis's current documentation distinguishes a human viewer, an on-demand
render camera and a control sensor. Its contact documentation separates
collision detection from contact resolution. These are useful design
distinctions, but `latest` API details are **not** the project's 1.3.3 lock;
inspect the installed implementation before adopting APIs. No dependency
upgrade was made in this audit. Sources: [Genesis camera sensors](https://genesis-world.readthedocs.io/en/latest/user_guide/sensing/camera_sensors.html),
[collision detection](https://genesis-world.readthedocs.io/en/latest/user_guide/theory/rigid_solver/collision_detection.html).

MuJoCo models contacts, friction and constraints together, and camera orientation
has an explicit coordinate convention. Use its model/solver definitions when
building the independent task, while preserving this repository's pinned
timesteps and model locks. Sources: [MuJoCo modeling](https://mujoco.readthedocs.io/en/stable/modeling.html),
[computation](https://mujoco.readthedocs.io/en/stable/computation/index.html).

## Borrow from sim2claw selectively

| Inspected source in `../sim2claw/src/sim2claw/` | Useful idea | Adoption here |
|---|---|---|
| `agent_context.py` | Compile a small current-state view; reject stale or ambiguous references. | `duck status` projects the two existing authority documents and receipts. No role packets or extra authoritative manifest. |
| `doctor.py` | State readiness as separate observable checks. | `duck doctor`: locked packages, MPS availability, contract drift, exact BAM checkout. No heavy training probe during startup. |
| `learning_factory_studio.py` | Read-only evidence projection with explicit proof classes and linked artifacts. | Duck Lab reads existing development reports and makes integrity and evidence limits visible. No mutation endpoint. |
| `visible_divergence_studio.py` | Use the recorded timeline to align visual inspection and measurements. | Case playback, simulation-time scrubber, trajectory and metric plots. |
| `replay_eligibility.py` | Keep requested/applied action semantics and bytes explicit. | A requirement for the next cross-backend diagnosis; no six-joint arm assumptions copied into the duck. |

Avoid bringing over the large learning-factory controller, role routing,
historical board/chess registration logic, or a physical gateway. They would
add unrelated state and violate the current single-agent choice.

## Improvements implemented in this audit

- A small `duck` CLI: current state, readiness, behavior draft/completeness
  checks, and local visualization. It reuses existing receipt formats.
- Duck Lab: side-by-side case video, simulation-time scrubbing, equal-scale
  XY paths, distance/speed plots, case scores, PPO curve, checksum status and
  exact artifact links. No invented 3D reenactment or score-based auto-promotion.
- A training/queue view with recorded statuses and optional TensorBoard
  iteration/reward timestamps; no false process-liveness claim.
- A repository skill and a task-physics/experiment guide. Instructions are
  loaded selectively; historical role logs remain historical.
- Focused tests for negative-result preservation, report tampering, missing
  evidence, unknown schemas, held-out exclusion, path/symlink handling,
  draft overwrite prevention, HTTP range playback and the read-only boundary.
- A separate dependency-free CI job for the workspace tools, leaving frozen
  M5 training/evaluator sources intact.

The project skill lives in `.agents/skills/microduck-experiments/SKILL.md`.
This is the official repository scope for local skills; concise trigger
descriptions and progressive disclosure keep irrelevant instructions out of
routine work. No global Codex configuration was changed.
[Official skill documentation](https://learn.chatgpt.com/docs/build-skills).

## Priorities and tradeoffs

These are evidence-based design judgments, not measured productivity gains.
Scores use the installed Refactor Score rubric. New product functionality is
labeled as a feature rather than a behavior-preserving refactor.

### R-001: Make current evidence easy to inspect
- **Priority:** P1
- **Score:** 87
- **Confidence:** High
- **Type:** Other — workspace feature
- **Scope:** `duck_workspace/`, `scripts/duck`, workspace docs and tests.
- **Current problem:** The user has to traverse role logs, run folders and separate videos to understand outcomes.
- **Proposed change:** A read-only projection and synchronized viewer over existing receipts.
- **Why this is valuable:** Makes negative cases and the exact intervention visible during diagnosis.
- **Why this is simpler:** Localizes repeated manual discovery without adding a second queue or execution controller.
- **Evidence:** Laser baseline/v1/v2 reports, ten development reports discovered at initial implementation, sim2claw's read-only projections.
- **Safety plan:** Test corruption, unknown schema and file boundaries; compare UI values with retained reports; remove new files to roll back.
- **Forward option-value:** Add one reader for a new task's recorded data when needed.
- **Senior judgment notes:** No web framework, external service, synthetic 3D renderer or policy activation button.
- **Score breakdown:** Impact 18/20; simplification 16/20; safety 14/15; evidence 14/15; option value 9/10; ROI 8/10; judgment 8/10. Applied caps: none; repeated discovery is localized.
- **Recommended next step:** Implemented; extend only from actual new receipt schemas.

### R-002: Use one behavior definition and a narrow project skill
- **Priority:** P1
- **Score:** 85
- **Confidence:** High
- **Type:** Other — workflow feature
- **Scope:** Behavior draft command, project skill, `BEHAVIOR_WORKFLOW.md`.
- **Current problem:** Broad requests can drift into infrastructure work, implicit privileged inputs or rewards that encode the wrong motion.
- **Proposed change:** Draft the task's observable success, sensing, physics, baseline and budget before training.
- **Why this is valuable:** Exposes the missing decision early while retaining task-specific flexibility.
- **Why this is simpler:** Reuses one concise guide; avoids recreating planner/reviewer/manager documents.
- **Evidence:** Kick reward exploit, camera-frame audit, provenance-related queue stops, retired role cycles.
- **Safety plan:** Drafts cannot execute or overwrite an existing experiment; structural validation never implies authority.
- **Forward option-value:** Supports new behavior families without a speculative environment registry.
- **Senior judgment notes:** Do not require a new draft for a tiny fix to an existing experiment or add approval rituals for ordinary local work.
- **Score breakdown:** Impact 18/20; simplification 16/20; safety 13/15; evidence 14/15; option value 8/10; ROI 8/10; judgment 8/10. Applied caps: none.
- **Recommended next step:** Implemented; evaluate its usefulness on the next requested behavior.

### R-003: Close the perception/control and robustness gap
- **Priority:** P1
- **Score:** 86
- **Confidence:** High
- **Type:** Other — behavior feature and evaluation work
- **Scope:** Versioned laser perception/command adapter and independent case suite.
- **Current problem:** Current accepted development pursuit sees privileged targets and a limited motion envelope.
- **Proposed change:** Dynamic target/occlusion stress followed by calibrated pixel-to-target control with explicit latency and confidence.
- **Why this is valuable:** Addresses the difference between the demo and the requested onboard behavior.
- **Why this is simpler:** Keeps the learned motor policy and perception/steering responsibilities separate.
- **Evidence:** Locked camera audit, retained moving-target case, v1/v2 command-response diagnosis.
- **Safety plan:** Version camera changes, freeze a new suite, compare oracle and pixel lanes, preserve no-detection stopping and old results; no hardware action.
- **Forward option-value:** Reusable perception/control contract for ball and waypoint tasks.
- **Senior judgment notes:** Coordinate with the already ongoing dynamic-laser work; do not duplicate or overwrite it. Hold-out and physical gates stay separate.
- **Score breakdown:** Impact 20/20; simplification 14/20; safety 13/15; evidence 15/15; option value 10/10; ROI 6/10; judgment 8/10. Applied caps: none; versioned local feature with a rollback path.
- **Recommended next step:** Next behavior milestone; not claimed implemented by this workspace audit.

### R-004: Consolidate historical pilot/receipt validators
- **Priority:** Research
- **Score:** 54
- **Confidence:** Medium
- **Type:** Simplification
- **Scope:** Repeated M5/M6 proposal validators and receipt plumbing.
- **Current problem:** Repeated validators and re-freezes consumed many historical slices.
- **Proposed change:** Identify a genuinely identical boundary before extracting a shared implementation.
- **Why this is valuable:** Could reduce future repeated mistakes if the lane becomes active again.
- **Why this is simpler:** Only worthwhile if it removes parallel implementations without changing frozen semantics.
- **Evidence:** Review corrections 026/029/032/038/039/044/049/051; historical source bindings.
- **Safety plan:** Characterize retained positive/negative receipts and mutation cases; preserve all historical bytes; use a versioned new validator.
- **Forward option-value:** Useful if paid comparison or artifact packaging resumes.
- **Senior judgment notes:** Defer now: broad refactoring can invalidate the very evidence being protected and does not teach a new behavior.
- **Score breakdown:** Impact 10/20; simplification 12/20; safety 8/15; evidence 9/15; option value 5/10; ROI 3/10; judgment 7/10. Applied caps: none; raw score 54.
- **Recommended next step:** Defer until a concrete active lane needs it.

## How to judge whether the workspace improves outcomes

For the next few behavior requests, record request-to-first-smoke time,
request-to-first-independent-evaluation time, training transitions/wall time,
number of interventions before improvement, per-case failures, and whether the
next experiment follows from a measured diagnosis. Track external-blocked time
separately. Do not use log count, commit count, reward or agent activity as the
outcome measure. No productivity improvement is claimed until those timings
and accepted behavior envelopes are measured.

## Additive workspace integration

The follow-up metadata adapter implements the transferable inspection boundary
without merging robot runtimes or action contracts. Both workspaces read
`robotics.workspace_exchange.v1`, preserve native source ordering and hashes,
and keep execution, training, hardware and policy-portability claims closed.
See [the exchange contract and validation](exchange/README.md).

The separately integrated [offline diagnostics](../experiment-ops/README.md)
add first-divergence trace inspection and advisory process inventory. Their
parsed action-value comparison does not replace an original tensor-byte replay
or establish which physics parameter caused a discrepancy. These tools address
diagnostic friction; their impact on training outcomes remains to be measured.
