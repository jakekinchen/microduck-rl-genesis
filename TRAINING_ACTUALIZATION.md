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
| Canonical contract | Candidate scaffold | Repo-local interface, model, and BAM snapshots exist; official mjlab parity is open. |
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
- [ ] Define walking and backflip semantic files, including assistance/curriculum state and success definitions.
- [ ] Submit the backend-independent contract upstream or record an explicit versioned divergence decision.

Exit gate: Genesis and official mjlab pass byte-identical interface fixtures and
thresholded BAM/model conformance tests. Model variants remain distinct.

### M2 — Build the independent C MuJoCo evaluator (P0)

- [ ] Create a CPU-only evaluator using official MuJoCo, BAM's C controller, ONNX Runtime CPU, 5 ms physics, decimation 4, and no action filter.
- [ ] Import the observation builder and model lock by pinned authority; do not reuse a training backend's self-reported metrics.
- [ ] Implement deterministic standing, command-grid, start/stop/reversal, perturbation, friction, joint-margin, NaN, deadline, and termination cases.
- [ ] Emit `evaluation.json`, `trajectory.parquet`, `rollout.mp4`, `environment-lock.json`, and `attestation.json` bound to the exact policy digest.
- [ ] Split visible development cases from held-out acceptance seeds/cases.
- [ ] Prove deterministic reports with the official walking ONNX before evaluating Genesis policies.

Exit gate: repeated evaluation of the same ONNX and suite ID yields identical
classification and stable numerical metrics within declared tolerances.

### M3 — Freeze task-specific success gates (P0)

- [ ] Walking: predeclare command ranges, survival duration, tracking error, fall rate, stop drift, foot slip, orientation, and joint/torque margins.
- [ ] Backflip: require ordinary standing start, zero assistance, takeoff, one uninterrupted airborne revolution, feet-first contact, landing orientation, and continuous stable hold.
- [ ] Store curriculum start populations separately from acceptance start populations.
- [ ] Test the classifiers against known positive, assisted, and failure trajectories.

Exit gate: success state machines classify fixtures correctly before any final
candidate results are inspected. PPO return is never a success definition.

### M4 — Characterize Apple scaling and stability (P1)

- [ ] Benchmark 64, 128, 256, 512, and, if memory permits, 1,024 environments.
- [ ] Record physics SPS, rollout time, PPO update time, synchronization, reset cost, peak unified memory, thermals, NaNs, and samples/minute.
- [ ] Run sustained thermal tests and define the default everyday environment count.
- [ ] Keep Genesis CPU + MPS as the debug fallback and record its crossover point.

Exit gate: a checked-in benchmark report selects defaults from measured total
iteration time and stability, not pure physics SPS.

### M5 — Run the decisive cross-backend training experiment (P1)

- [ ] Freeze task semantics, reward, DR, actor/PPO configuration, transition checkpoints, seed list, and evaluator before candidate training.
- [ ] Development: at least three fixed public seeds per backend.
- [ ] Candidate comparison: five seeds per backend or a predeclared equivalent power analysis.
- [ ] Match Genesis Metal/MPS and official mjlab/CUDA by transitions, not iterations or wall time.
- [ ] Export every predetermined checkpoint through its canonical normalized ONNX path.
- [ ] Evaluate every frozen ONNX in the same held-out C MuJoCo suite.
- [ ] Compare time to threshold, task metrics, variance, and simulator/reference ranking consistency.

Exit gate: Genesis remains primary only if it is non-inferior on predeclared
reference outcomes. Higher training reward alone cannot close this milestone.

### M6 — Package immutable, attributable artifacts (P1)

- [ ] Add policy manifest v2 and reference/hardware attestation JSON Schemas.
- [ ] Validate one official and one community artifact without executing repository code.
- [ ] Bind ONNX, normalizer, source checkpoint, exporter, model, BAM, task, evaluator, evidence, and license files by SHA-256.
- [ ] Publish source on GitHub and immutable policy artifacts on Hugging Face.
- [ ] Keep download, library import, evaluation, approval, and activation as separate actions.
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

## Immediate next three runs

1. Pin the exact authoritative BAM revision and produce versioned golden vectors.
2. Make Genesis and official mjlab consume the same BAM/interface fixtures.
3. Implement the deterministic C MuJoCo evaluator MVP before spending on multi-seed training.

This order maximizes information: it first proves reproducibility, then semantic
equivalence, then independently measured policy quality.
