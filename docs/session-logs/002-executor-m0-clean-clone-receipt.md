# Executor Session Log 002 - M0 clean-clone receipt

**Date:** 2026-09-01

## Slice

Executed `docs/briefs/002-m0-clean-clone-receipt.md` from a separate clone with
its own Git directory at source commit
`2ce72a9492789c23d2191c7517e28a5b6bb12678`.

## Generated Artifacts

Receipt root:
`receipts/apple-baseline/20260901T215219Z-2ce72a94/`

The bundle contains:

- setup, contract, full-suite, and combined smoke stdout;
- sanitized environment metadata and empty tracked-status receipts from before
  and after the run;
- walking and backflip configs plus `model_0.pt` and `model_4.pt` checkpoints;
- normalized, single-file walking and backflip ONNX exports;
- randomized export-parity and 60-step real-observation parity logs for both
  tasks; and
- a relative-path SHA-256 manifest covering all 20 other files.

No ONNX external-data sidecar exists. The temporary clone and its fresh 2.5 GB
environment were removed only after the copied receipt passed its manifest.

## Validation Results

- Fresh locked install: Python 3.12.12, Torch 2.9.1, Genesis 1.3.3,
  rsl-rl-lib 5.4.2, MuJoCo 3.12.0, ONNX Runtime 1.23.2.
- Setup proved `mps=True` and Genesis Metal.
- Contract snapshots verified from committed state.
- `tests/run_all.py` ended with `tous les tests passent`.
- Walking completed 64 environments x 5 iterations on Metal/MPS.
- Backflip completed 64 environments x 5 iterations on Metal/MPS.
- Walking randomized Torch/ONNX maximum difference: `2.146e-06` rad.
- Walking 60-step real-observation maximum difference: `1.341e-07` rad.
- Backflip randomized Torch/ONNX maximum difference: `4.768e-06` rad.
- Backflip 60-step real-observation maximum difference: `1.043e-07` rad.
- Both source-status files are zero bytes, proving no tracked-tree mutation.
- `shasum -a 256 -c SHA256SUMS` passed in staging and again from the copied
  receipt.

## Explicit Coverage Gaps

- BAM formula and full MuJoCo+BAM-loop comparisons skipped because the optional
  authoritative BAM checkout was absent. That authority is M1 work.
- The default `logs/microduck-velocity` deployment test was initially not
  applicable, as expected in a clean clone. The same deployment test then ran
  explicitly against both newly generated smoke checkpoints and passed.

## Recovery Note

The first manifest-finalization attempt failed after all substantive tests had
passed because a zsh loop variable named `path` overwrote zsh's executable
search-path array, making `shasum` unavailable. This was a receipt-tooling
failure, not a model or pipeline failure. The clone and staging artifacts were
preserved, sensitive-field checks were rerun, the manifest was generated with
an absolute checksum executable and a non-special loop variable, and the
result was verified twice before cleanup.

## Evidence Boundary

This slice establishes reproducible `artifact_validated` pipeline evidence for
the exact source commit. It does not establish a usable gait, autonomous
backflip, frozen task success, held-out C MuJoCo success, hardware observation,
or physical acceptance. Five PPO iterations and reward movement are not task
success.

## Suggested Next Slice

Reviewer should audit the receipt, close M0 only if every invariant artifact is
present and verified, then open M1 with the narrowest safe source-authority
step: locate or pin the authoritative BAM implementation and produce versioned
open-loop golden vectors without changing backend semantics.
