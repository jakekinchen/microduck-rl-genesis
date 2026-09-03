# Training actualization plan

This is the execution queue for turning the working Genesis/MPS pipeline into a
reproducible, independently evaluated policy-production system. Work is judged
by closed gates and durable receipts, not by reward movement or a visually
plausible rollout.

## Current evidence boundary

| Gate | State on 2026-09-01 | What is established |
|---|---|---|
| Public Apple code | Present | Metal physics and MPS learner selection are committed on `main`. |
| Apple model preflight | Observed | Genesis 1.3.3 loaded a real Microduck MJCF and completed one finite Metal step. |
| Walking/backflip pipeline | Clean-clone reproduced | Receipt `20260901T215219Z-2ce72a94` passed both 64x5 smokes, two normalized ONNX exports, two randomized parity checks, and two real-observation parity checks from committed state. |
| Canonical contract | Closed M1 contract evidence | Interface/model/BAM locks, pinned BAM fixtures, official mjlab consumption, six model variants, walking/backflip semantics, and the local versioned-divergence decision are frozen. The tasks record 28 and 32 classified fields respectively and do not claim identical training trajectories. |
| Task success | Open | No frozen success battery has accepted an Apple-trained walking or backflip policy. |
| Held-out C MuJoCo | Open | No independent frozen-ONNX acceptance suite exists yet. |
| Physical validation | Open | No policy from this repository has physical authority. |

The only promotable statuses are `artifact_validated`, `sim_previewed`,
`reference_evaluated`, `hardware_observed`, and `physically_accepted`. Each
status requires its own receipt; no earlier status implies a later one.

## Ordered task queue

Only one milestone should be promoted at a time. A checked implementation item
does not close its milestone until every exit gate and receipt is present.

### M0 — Freeze and reproduce the Apple baseline (P0)

- [x] Separate the Apple dependency lane from vendor-PyTorch ROCm/CUDA installs.
- [x] Pin Genesis 1.3.3, PyTorch 2.9.1, and rsl-rl 5.4.2 in a hash-locked macOS arm64 environment.
- [x] Provide explicit Metal/MPS walking and backflip 64-env x 5-iteration commands.
- [x] From a clean clone, run `./scripts/setup_apple.sh` on Apple Silicon.
- [x] Run `python tests/run_all.py`; record every skip, especially missing BAM/checkpoint coverage.
- [x] Run `./scripts/run_apple_smokes.sh` for both bounded tasks.
- [x] Retain clean-run stdout, configs, checkpoints, and SHA-256 manifests.
- [x] Export both smoke checkpoints and run Torch-versus-ONNX randomized and real-observation checks.
- [x] Record machine model, macOS, Python, Torch, Genesis, MuJoCo, rsl_rl, commit, and dirty-tree state without recording a hardware serial.

Exit gate: a second clean Apple checkout reproduces both 64x5 smokes and ONNX
checks from the committed lock. Receipt root: `receipts/apple-baseline/<run-id>/`.

Local readiness verification on 2026-09-01 (current dirty checkout): the locked
environment installed and selected Genesis Metal plus Torch MPS; the full test
runner passed after updating two stale Genesis 1.2 API references. BAM formula
and full MuJoCo+BAM-loop tests skipped because the optional authoritative BAM
checkout was absent. Walking ran at 560–785 env-steps/s and backflip at 622–910
over five iterations. Single-file ONNX randomized parity was at most 3.695e-6
rad; both real-observation checks were 1.341e-7 rad. This is pipeline evidence,
not gait, backflip-success, held-out, or physical evidence.

M0 closed on 2026-09-01 with clean-clone receipt
`receipts/apple-baseline/20260901T215219Z-2ce72a94/`, bound to source commit
`2ce72a9492789c23d2191c7517e28a5b6bb12678`. All 20 manifest entries are
tracked and verified. Walking randomized/real-observation ONNX parity was
2.146e-6/1.341e-7 rad; backflip was 4.768e-6/1.043e-7 rad. This promotes only
reproducible `artifact_validated` pipeline evidence.

### M1 — Establish the shared semantic contract (P0)

- [x] Freeze repo-local model/asset, observation, action, control, and BAM input snapshots.
- [x] Fail CI when generated snapshots drift from their source.
- [x] Add BAM open-loop golden vectors and reset/internal-state fixtures from the authoritative BAM implementation.
- [x] Add short 14-servo closed-loop trajectory fixtures.
- [x] Make the official mjlab/MuJoCo Warp adapter consume and pass the same fixtures.
- [x] Reconcile Genesis/MuJoCo model counts, collision variants, masses, inertias, keyframes, joint limits, and actuator ordering.
- [x] Define the walking semantic file, including training-only curriculum state, 28 classified backend fields, and a preregistered zero-assistance success battery.
- [x] Define the backflip semantic file, including assistance/reverse-curriculum state and ordinary-start zero-assistance success definitions.
- [x] Submit the backend-independent contract upstream or record an explicit versioned divergence decision.

Exit gate: Genesis and official mjlab pass byte-identical interface fixtures and
thresholded BAM/model conformance tests. Model variants remain distinct.

M1 closed on 2026-09-02 with a local, not-submitted versioned divergence
decision covering all 45 non-exact walking/backflip semantic fields. The
deployed 61D/14D/50 Hz interface and BAM/model conformance are retained; no
training-trajectory equivalence, task success, held-out result, transfer, or
physical authority is claimed.

### M2 — Build the independent C MuJoCo evaluator (P0)

- [x] Create a CPU-only evaluator using official MuJoCo, BAM's C controller, ONNX Runtime CPU, 5 ms physics, decimation 4, and no action filter.
- [x] Import the observation builder and model lock by pinned authority; do not reuse a training backend's self-reported metrics.
- [x] Implement deterministic standing, command-grid, start/stop/reversal, perturbation, friction, joint-margin, NaN, deadline, and termination cases.
- [x] Emit `evaluation.json`, `trajectory.parquet`, `rollout.mp4`, `environment-lock.json`, and `attestation.json` bound to the exact policy digest.
- [x] Split visible development cases from held-out acceptance seeds/cases.
- [ ] Prove deterministic reports with the official walking ONNX before evaluating Genesis policies.

Exit gate: repeated evaluation of the same ONNX and suite ID yields identical
classification and stable numerical metrics within declared tolerances.

Core accepted on 2026-09-02: official MuJoCo C through Python bindings,
single-thread ONNX Runtime CPU, and pinned BAM `MujocoController` produced two
byte-identical 40-step infrastructure reports from the retained zero-policy
fixture. Both walking and backflip model lanes validate. This does not close M2
or evaluate task success; the full artifact bundle and designated official
walking ONNX repeatability proof remain open.

Development bundle accepted on 2026-09-02: two public non-candidate cases emit
all five required artifacts. Two same-host runs reproduced every artifact byte,
including 160-row Parquet and 40-frame decoded MP4 outputs. This remains
infrastructure-only; deterministic acceptance cases, held-out separation, and
the designated official walking ONNX proof remain open.

Official walking authority search stopped on 2026-09-02 with durable result
`official_policy_authority_missing`. The exact project-owned runtime/Hugging
Face artifact is 61D-to-14D, contains a Sub/Div normalizer, and is immutable at
SHA-256 `e36332d383997d51401897734cd3e79cf5038406feddb18b4d57ecfb141daa6c`.
Neither its ONNX metadata nor the project-owned schema-v2 manifest binds a
checkpoint, training run, exact task-source commit, exporter invocation, or the
normalizer statistics to their source. It was not executed. M2 remains open;
only the official-policy repeatability sub-gate is blocked until upstream
supplies one of the acceptable authority paths recorded in
`microduck_contract/policies/official-walking-authority-v1.json`. Independent
local evaluator cases, held-out preregistration, and M3 classifier work remain
authorized.

BAM authority materialization corrected on 2026-09-02: fresh checkouts now
fetch and detach at the exact locked commit rather than the moved
`mjlab_frictionloss` branch. A local-git regression proves later branch movement
cannot repin the checkout; existing BAM fixtures and evaluator evidence were
not regenerated.

Deterministic case matrix accepted on 2026-09-02: ten visible zero-policy cases
cover all nine required infrastructure families with byte-identical repeated
reports. This is not held-out or task-success evidence.

Held-out protocol accepted on 2026-09-02: visible development data and public
acceptance definitions are distinct from an unrealized seed set derived only
from public randomness published after an immutable candidate freeze. No live
beacon, held-out seed, candidate, or result was inspected.

### M3 — Freeze task-specific success gates (P0)

- [x] Walking: predeclare command ranges, survival duration, tracking error, fall rate, stop drift, foot slip, orientation, and joint/torque margins.
- [x] Backflip: require ordinary standing start, zero assistance, takeoff, one uninterrupted airborne revolution, feet-first contact, landing orientation, and continuous stable hold.
- [x] Store curriculum start populations separately from acceptance start populations.
- [x] Test the classifiers against known positive, assisted, and failure trajectories.

Exit gate: success state machines classify fixtures correctly before any final
candidate results are inspected. PPO return is never a success definition.

M3 closed on 2026-09-02 with executable classifiers covering all 230 walking
cells and 20 ordinary-start backflip cells. Synthetic positive fixtures pass;
assisted, metric-failure, and incomplete-coverage fixtures fail closed. No
policy trajectory or candidate result was inspected.

### M4 — Characterize Apple scaling and stability (P1)

Harness implementation accepted on 2026-09-03 at commit `05c05e3`: it records
a real Metal/MPS PPO iteration, clean source/package/machine provenance,
finiteness, thermal-method limitations, and an explicit peak-RSS unified-memory
proxy. M4 remains active pending the preregistered sweep, sustained stability,
and CPU+MPS fallback crossover.

Primary scaling sweep accepted on 2026-09-03: all five sizes through 1024 were
finite, thermally nominal by the declared `pmset` warning-state method, and
above 97.75% RSS-proxy headroom. At 1024, total PPO iteration was 4.271 s and
total-iteration-derived throughput was highest at 345,246 samples/min. This
selects only the preregistered sustained-test candidate, not the default.

Sustained 1024-environment stability accepted on 2026-09-03: 120/120 measured
iterations were finite, all 15 declared thermal samples were nominal, RSS-proxy
headroom was 97.15%, and last/first median iteration slowdown was 0.9730 against
the frozen 1.25 ceiling. It remains eligible as the everyday default; M4 still
requires the CPU+MPS fallback crossover.

Matched fallback grid accepted on 2026-09-03: CPU+MPS is operational and had
lower median total PPO iteration than Metal+MPS at 64, 128, 256, and 512. The
honest frozen result is `>512`; one separately preregistered matched 1024 pair
will determine whether the on-grid crossover is 1024 or above the tested range.

M4 closed on 2026-09-03. The matched 1024 extension measured Metal+MPS median
total PPO iteration at 2.5271 s versus CPU+MPS at 3.0963 s, locating the grid
crossover at 1024. The everyday Apple default is therefore 1024 environments
with Metal physics and MPS learning; CPU+MPS remains the verified debug
fallback and was faster at 64-512. These are performance defaults only, under
the explicit `pmset` warning-state and peak-RSS-proxy limitations.

- [x] Benchmark 64, 128, 256, 512, and, if memory permits, 1,024 environments.
- [x] Record physics SPS, rollout time, PPO update time, synchronization, reset cost, peak unified memory, thermals, NaNs, and samples/minute.
- [x] Run sustained thermal tests and define the default everyday environment count.
- [x] Keep Genesis CPU + MPS as the debug fallback and record its crossover point.

Exit gate: a checked-in benchmark report selects defaults from measured total
iteration time and stability, not pure physics SPS.

### M5 — Run the decisive cross-backend training experiment (P1)

Immutable experiment contract accepted on 2026-09-03 at `b2a1ab6`: exact
sources/hashes, full actor/PPO configuration, public/candidate seeds, equal
transition budgets, predetermined checkpoints/normalized exports, evaluator,
held-out timing, decision rules, receipts, resumability, and a proposal-only
CUDA budget are frozen. Its 32-row dry-run executes nothing. M5 execution remains
blocked by official-policy authority, immutable CUDA container digest, and
explicit compute authorization.

Slice 026 amends only the execution-authority layer under dated Manager
authorization. It binds NVIDIA CUDA 12.8.1 cuDNN development Ubuntu 24.04 for
linux/amd64 at manifest digest
`sha256:3986465b3dd3b4d602c07061f2cff417e0bfb24810129408d4eb12e111015a6c`,
prefers one non-stoppable Brev `hyperstack_A100_80G` at $1.62/hour, and limits
the pilot to two hours/$3.24. The 32 experiment rows remain unexecuted and
unauthorized; an independent Reviewer must accept this amendment before the
pilot, and must separately accept the recovered pilot receipts before the
104-GPU-hour/$210 full CUDA envelope becomes eligible. Official-policy
provenance and held-out timing remain blocking gates.

Reviewer 026 returned `NO-GO`: the first amendment did not apply its digest in
the Brev create command, mislabeled `cloud=hyperstack` as the provider rather
than recording `provider=shadeform`, and left several safety rules mutable under
the semantic validator. Corrective slice 027 makes the actual container-mode
provisioning command digest-addressed, fixes the catalog fields, requires an
empty inventory and exactly one no-fallback workspace, and schema/validator
locks the pilot contents, recovery, independent checksums, deletion, and later
full-run Reviewer gate. No paid workspace may start until slice 027 receives a
new independent `GO`.

- [x] Freeze task semantics, reward, DR, actor/PPO configuration, transition checkpoints, seed list, and evaluator before candidate training.
- [ ] Development: at least three fixed public seeds per backend.
- [ ] Candidate comparison: five seeds per backend or a predeclared equivalent power analysis.
- [ ] Match Genesis Metal/MPS and official mjlab/CUDA by transitions, not iterations or wall time.
- [ ] Export every predetermined checkpoint through its canonical normalized ONNX path.
- [ ] Evaluate every frozen ONNX in the same held-out C MuJoCo suite.
- [ ] Compare time to threshold, task metrics, variance, and simulator/reference ranking consistency.

Exit gate: Genesis remains primary only if it is non-inferior on predeclared
reference outcomes. Higher training reward alone cannot close this milestone.

### M6 — Package immutable, attributable artifacts (P1)

Schema foundation accepted on 2026-09-03 at `973a204`: policy manifest v2 and
reference/hardware attestations bind all required artifact roles and keep
download, import, evaluation, approval, activation, task evidence, and physical
authority separate. Validation is byte-only against synthetic fixtures; no real
policy is accepted or executed.

File-level inventory accepted on 2026-09-03 at `e91ac2e`: 70 files are covered,
with 63 complete, 2 partial, and 5 missing. Exact negatives are retained for
`ball.xml`, the actuator parameter source path, three policy weights, and two
media files. No dataset files are present and none are invented. M6 remains open
for real fully attributable official/community artifacts and publication under
separate authority.

- [x] Add policy manifest v2 and reference/hardware attestation JSON Schemas.
- [ ] Validate one official and one community artifact without executing repository code.
- [ ] Bind ONNX, normalizer, source checkpoint, exporter, model, BAM, task, evaluator, evidence, and license files by SHA-256.
- [ ] Publish source on GitHub and immutable policy artifacts on Hugging Face.
- [x] Keep download, library import, evaluation, approval, and activation as separate actions.
- [ ] Resolve file-level MJCF/mesh, policy-weight, dataset, and media license provenance.

Exit gate: a fresh machine retrieves by exact revision/digest, validates locally,
and reaches the library without executing untrusted code or activating a policy.

### M7 — Optional NVIDIA and challenger lanes (P2)

- [ ] Use NVIDIA only for official-stack A/B runs, unported tasks, or large frozen sweeps.
- [ ] Before any cloud run, freeze commits, dependency/container digests, task/model/BAM hashes, seeds, and transition budget.
- [ ] Run a bounded MuJoCo-MLX-Cpp compatibility spike only after defining BAM-required mutation/state hooks.
- [ ] Eliminate any challenger that cannot reproduce model, BAM, observation, reset, and ONNX-loop conformance before PPO.
- [ ] Require about 2x time-to-held-out-threshold improvement or materially better MuJoCo agreement before replacing Genesis.

Brev cost gate: inspect authenticated inventory before provisioning; recover
checkpoints/evaluator outputs/checksums before teardown; then stop/delete idle
resources and verify disappearance with `brev ls --json` before ending the task.

### M8 — Staged physical validation (blocked until M0–M6)

- [ ] Bind the exact ONNX digest to robot hardware revision, runtime/firmware, operator protocol, and environmental limits.
- [ ] Require explicit user approval at activation time.
- [ ] Progress through quiet stand, small head/body command, very-low-speed walk, stop, and gentle recovery before dynamic tasks.
- [ ] Record synchronized observations, actions, servo telemetry, video, stops, and failure reasons.
- [ ] Issue `hardware_observed` or `physically_accepted` only for the exact artifact and declared protocol; preserve negative results.

Exit gate: the exact ONNX passes or fails the declared physical protocol. No
simulation or reference result grants physical authority.

## Blocked continuation order

1. Ingest an upstream immutable manifest or reproducible checkpoint/export
   chain that closes `official_policy_authority_missing`.
2. Prove report repeatability with that official policy on visible development
   cases only.
3. Split visible development cases from held-out acceptance seeds and cases.

The BAM fixture, official-adapter consumption, and model-reconciliation runs
are complete and must not be reopened without new contradictory evidence.
