# Slice Brief 002 - M0 clean-clone receipt

**Date:** 2026-09-01

## Objective

Reproduce the complete Apple baseline from a separate clean clone of the exact
committed source and retain an auditable receipt bundle under
`receipts/apple-baseline/<run-id>/`.

## Product / Project Value

This is the remaining M0 gate. It distinguishes a working developer tree from
a reproducible Apple policy-production baseline before backend conformance or
success evaluation begins.

## Acceptance Criteria

- Create a separate clone with its own Git directory from the exact source
  commit; record the full commit and prove the tracked tree is clean before and
  after the run.
- Run `./scripts/setup_apple.sh` from the clone and verify the committed hash
  lock, Genesis Metal, and Torch MPS without changing repository dependencies.
- Run the contract check and `tests/run_all.py`; preserve complete stdout and
  list every skip or non-applicable coverage class.
- Run walking and backflip at 64 environments for 5 iterations through
  `./scripts/run_apple_smokes.sh`.
- Retain each task's config, initial/final checkpoints, exported normalized
  single-file ONNX, randomized export-parity stdout, and 60-step
  real-observation parity stdout.
- Record only non-sensitive environment metadata: model name/identifier, chip,
  core count, memory, architecture, macOS/build, Python, Torch, Genesis,
  MuJoCo, ONNX Runtime, rsl_rl package version, source commit, and clean status.
  Do not record serial number, hardware UUID, provisioning identifier,
  credentials, usernames, or absolute home paths.
- Create a relative-path SHA-256 manifest covering every retained receipt file
  except the manifest itself.
- Copy the completed receipt into this repository, validate its manifest, and
  write an Executor log. Do not promote M0 or alter task-success claims until
  Reviewer audit.

## Expected Artifacts

```text
receipts/apple-baseline/<run-id>/
  README.md
  environment.json
  source-status-before.txt
  source-status-after.txt
  setup.log
  contract-check.log
  tests-run-all.log
  apple-smokes.log
  walking/export.log
  walking/onnx-real-observation.log
  walking/cfgs.pkl
  walking/model_0.pt
  walking/model_4.pt
  walking/policy.onnx
  backflip/export.log
  backflip/onnx-real-observation.log
  backflip/cfgs.pkl
  backflip/model_0.pt
  backflip/model_4.pt
  backflip/policy.onnx
  SHA256SUMS
docs/session-logs/002-executor-m0-clean-clone-receipt.md
```

Event files may be retained if useful but are not a substitute for the listed
configs, checkpoints, exports, and stdout.

## Validation Commands

Run these from the separate clone, with stdout/stderr captured to the receipt:

```bash
./scripts/setup_apple.sh
.venv-apple/bin/python scripts/freeze_contract.py --check
GS_ENABLE_ZEROCOPY=1 .venv-apple/bin/python tests/run_all.py
./scripts/run_apple_smokes.sh
.venv-apple/bin/python export_onnx.py -e apple-smoke-walking -o <receipt>/walking/policy.onnx
.venv-apple/bin/python tests/test_onnx_deploy.py apple-smoke-walking
.venv-apple/bin/python export_onnx.py -e apple-smoke-backflip -o <receipt>/backflip/policy.onnx
.venv-apple/bin/python tests/test_onnx_deploy.py apple-smoke-backflip
```

Then verify `SHA256SUMS`, confirm no ONNX external-data sidecars exist, confirm
the clone's tracked status is still clean, and run `git diff --check` in the
source repository.

## Evidence Boundary

Passing this slice establishes `artifact_validated` pipeline reproducibility
only. Five PPO iterations, reward movement, finite state, randomized parity,
or rollout appearance do not establish walking, backflip, held-out reference,
hardware, or physical success.

## Out Of Scope

- Authoritative BAM download or golden-vector work.
- Official mjlab adapter work.
- Longer or multi-seed training.
- Brev or other paid compute.
- Publication, policy activation, or physical robot testing.

## Stop Conditions

- The exact committed lock cannot install without mutation.
- Metal physics or MPS learning is unavailable.
- Either smoke, export, or real-observation parity fails.
- Receipt generation would expose sensitive machine identifiers.
