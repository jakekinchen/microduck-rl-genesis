# Executor Session 032 - M5 deterministic evidence correction

**Date:** 2026-09-03

## Baseline And Authority

- Reviewer-accepted base: `60a642a`; slice opening commit: `5ab1062`; initial
  implementation: `bac0375`; Reviewer-032 correction: `d741e60`.
- Immutable source receipt:
  `receipts/m5/pilot/20260904T012843Z-7owxqf4pg/` with manifest SHA-256
  `90cbb02447d55594f71a1b35e1d00918f2f809acf3a182419d838d85186b3078`.
- Pilot-028 manifest remains
  `1e8d4948294b4a4c95a8a73c9e0a7c9ab0fcef4c354a2c11ac29f1eb4ce8566b`.
- `git diff 60a642a -- receipts` is empty. The frozen M5 contract/lock,
  `evaluator/core.py`, evaluator config, and development suite are also
  byte-unchanged.
- Pinned BAM authority is clean at `62bd8ce`; official walking authority is at
  `109e06d`. Existing untracked `work/` in the official checkout was preserved
  and not used as authority.
- Authenticated Brev inventory was empty before local work. No Brev create,
  start, exec, copy, stop, or delete command was issued in this slice.

## Failure Reproduction And Classification

### 1. Compiled model manifest

The A100 log failed the retained local-manifest digest assertion. A local
Linux/amd64 reproduction with MuJoCo 3.12.0 produced these raw hashes:

- walk `d27f7a4b...53aff`; all-collisions `f1a74e5c...27ab4`;
- walk-backlash `71b068f5...a5c8`; all-collisions-backlash
  `76cf5dae...69ea`;
- rollers `eff93218...53bd`; rollers-backlash `ddbbbe02...fcbbe`.

Against the retained Darwin manifests, every count, name, joint, actuator,
collision, keyframe, mass, and position matched. Only mesh-compiled body inertia
tails differed: 11 fields in each non-roller variant and 18 in each roller
variant, maximum absolute delta `1.0842021724855044e-19`. Classification:
**platform floating-point nondeterminism**, not semantic drift. The raw retained
manifest and its digest remain untouched as origin-host provenance.

### 2. Evaluator core expected bytes

The exact Linux report SHA-256 was `466e0023...94ebe` versus retained Darwin
`e8711a59...0b57`. Recursive comparison found exactly two fields:

- raw trajectory SHA-256 `ae8cf5db...817cb` on Linux versus
  `2b58cb21...11d4` on Darwin;
- truthful ONNX Runtime `1.29.0` versus `1.23.2`.

Measured row values differed only in floating tails: maximum absolute deltas
were `1.33e-16` root position, `9.99e-16` quaternion, `2.84e-15` joint
position, `1.48e-13` joint velocity, and `7.32e-15` actuator torque. Eleven
decimal places produce byte-identical canonical row evidence on both hosts;
the fixed home-smoke canonical digest is `25d48827...46e6`. Classification:
**platform floating-point nondeterminism plus environment provenance**, with
the old raw-byte assertion stale only as cross-host authority. The frozen raw
fixture remains unchanged.

### 3. Repeated evaluator bundle hashes

The A100 receipt records the repeated-hash assertion but the temporary bundles
and individual first/second hashes were not retained, so exact failing artifact
bytes cannot honestly be reconstructed. Producer audit found two materially
unbounded same-host channels: measured wall-clock ONNX latency was embedded in
case reports, and EGL offscreen rendering used multisample resolution. A local
Linux/amd64 OSMesa reproduction happened to be byte-identical even before the
fix, demonstrating that Linux metadata, output path, ordering, and timestamp
serialization were stable in that reproduction without identifying the
discarded A100 artifact. Classification: **runtime timing or GPU render
nondeterminism**, not evaluator semantics; exact A100 artifact attribution is
unavailable because the original test discarded its temporary outputs.

## Implementation

- `scripts/reconcile_models.py` now compares 14-significant-digit semantic
  projections of the current and retained full manifests while continuing to
  authenticate the retained raw manifest digest.
- `evaluator/determinism.py` supplies an 11-decimal canonical trajectory digest
  and a semantic report projection that excludes only runtime provenance and
  the separately checked raw trajectory digest.
- `evaluator/bundle.py` fixes synthetic development-bundle latency at zero and
  forces one-sample offscreen rendering. Task logic, observations, actions,
  thresholds, and the frozen evaluator core are unchanged.
- Regressions exercise the measured Darwin/Linux inertia pairs, float-row
  deltas, reordered mapping fields, Linux/x86-64 platform metadata, different
  output paths, deliberate 25 ms versus 1 ms inference timing, and exact
  repeated five-file bundle hashes. A `1e-9` inertia change and `1e-8` state
  change remain visible, guarding against semantic masking.
- No existing expected fixture was rebaselined.

## Reviewer 032 Nudge Resolution

Reviewer 032 demonstrated that the initial recursive model projection could
mask a one-ULP non-inertia mass change. A failing-first regression reproduced
that exact `0.12345678901234567` to `0.12345678901234568` defect. Commit
`d741e60` now deep-copies the manifest and applies 14-significant-digit
canonicalization only to `bodies[*].inertia_kg_m2`; every mass, inertial
position, joint, actuator, collision, keyframe, count, and name remains exact.
The measured Darwin/Linux inertia example still converges, a `1e-9` inertia
change still fails, and the one-ULP mass change now fails.

## Validation

- Failing-first: all four focused tests failed on missing canonicalization or
  missing deterministic bundle fields before implementation.
- Native focused tests: model reconciliation, evaluator core, evaluator bundle,
  and cross-platform determinism all pass with pinned BAM.
- Local Linux/amd64 reproduction: all four focused tests pass using Python
  3.12, MuJoCo 3.12.0, NumPy 2.5.2, ONNX Runtime 1.29.0, PyArrow 21.0.0,
  ImageIO 2.37.4, ImageIO-FFmpeg 0.6.0, and BAM `62bd8ce`.
- Full local authority suite:
  `BAM_REPO=/tmp/microduck-bam-authority-exact`, exact official checkout and
  locked MJLab Python, `GS_ENABLE_ZEROCOPY=1`, `tests/run_all.py` - pass with no
  failures.
- `tests/test_m5_experiment_contract.py` - pass; frozen bindings unchanged.
- `scripts/check_branch_hygiene.sh 60a642a` - pass, seven manifests and 53
  immutable logs.
- Workflow audit and diff checks - pass.
- After `d741e60`, the four focused tests and the complete authority-enabled
  `tests/run_all.py` suite passed again. M5 contract validation, branch hygiene,
  receipt immutability, and workflow audit remained clean.

## Evidence Boundary

Local cross-platform deterministic-evidence compatibility only. No A100 rerun,
training, checkpoint, ONNX candidate, held-out evaluation, task success,
publication, policy activation, transfer, or physical authority is claimed.

## Step-9 Flags For Reviewer

- Confirm Reviewer 032's exact mass negative probe now remains visible and that
  only `bodies[*].inertia_kg_m2` receives the measured tolerance.
- Confirm `evaluator/core.py`, the M5 experiment freeze, both accepted pilot
  receipts, 61D/14D/50 Hz/BAM contracts, and evaluator thresholds are
  unchanged.
- Re-run the focused and full authority suites and audit the local Linux/amd64
  evidence boundary.
- The separate third-pilot card is a draft with `compute_authorized=false`.
  Reviewer acceptance must not provision compute or grant later Manager
  authority.
