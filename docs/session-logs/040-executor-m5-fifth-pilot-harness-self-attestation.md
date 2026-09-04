# Executor Session 040 - M5 fifth-pilot harness self-attestation

**Date:** 2026-09-04

## Baseline And Authority

- Accepted terminal-negative fourth-pilot Reviewer HEAD: `957499a`.
- Reviewer 039 NUDGE record: `7fa65b9`.
- Correction opening commit: `abe42b1`.
- Correction implementation commit: `579627b`.
- This slice remained local and non-authorizing. No Brev provisioning, remote
  execution, training, smoke, or export was performed.

## Correction

- The fifth harness now requires exactly
  `$INPUT_ROOT/run_m5_cuda_pilot_5.sh`.
- It retains exactly `$RECEIPT_ROOT/run_m5_cuda_pilot_5.sh` and hashes that
  same fifth-specific file into `harness-sha256.txt`.
- The semantic validator requires each of those three exact statements once
  and rejects any dependency on the fourth-harness filename.
- The deterministic regression stages only the fifth-specific native filename
  plus nonempty bundle placeholders. It advances beyond bootstrap to the
  deliberately unavailable `host-nvidia-smi` gate, verifies retained bytes and
  hashes against the proposal binding, and confirms neither input nor receipt
  contains a fourth-harness alias.

## Frozen Hashes

- Fifth-specific harness SHA-256:
  `2856fce10b8e829f9f290975621cbf900821b7f946fca02239cda79a41df5b29`.
- Corrected proposal byte SHA-256:
  `1d27fd55dee168fcf4f54f38432b2bad65a067aef8f821c4e1746a2afaeca4b1`.
- Corrected proposal semantic SHA-256:
  `dd62db31aa5e1dd6b35d1213b744342a17d1a1099008d5764b399dbcfbdb6d57`.
- Unchanged schema SHA-256:
  `5ffa816b0e4c649359e07500974c29dc1674565577ed8dd63fc285c598688102`.
- Preserved fourth-pilot harness SHA-256:
  `86e964348ec5bb64f22b64bdee6b3eb446923b2e35f2b8e5f54390eda08798ef`.

## Validation

- Fifth-pilot validator and fail-closed tests: pass with 153 scalar mutations,
  182 deletions, extra-field and explicit authority rejection, historical-rate
  rejection, fourth-alias rejection, and native-name receipt self-attestation.
- Full authority-enabled `.venv-apple/bin/python tests/run_all.py`: pass with
  clean BAM `62bd8ce`, official walking `109e06d`, locked official MJLab
  Python, and `GS_ENABLE_ZEROCOPY=1`; both environment smokes pass.
- Static CUDA runtime, artifact, Python compilation, Bash syntax, and
  shellcheck gates: pass.
- All nine tracked manifests and 68 immutable logs: pass.
- Branch hygiene from `957499a`, accepted-receipt immutability,
  fourth-harness immutability, diff checks, and workflow audit: pass.
- Closing authenticated `brev ls --json`: `{"workspaces": null}`.

## Evidence And Authority Boundary

The proposal remains `compute_authorized=false`. No Brev resource was created
or mutated. This proves only the local proposal's exact native-name staging and
receipt self-attestation behavior, not CUDA smoke, M5, task, policy, candidate,
held-out, publication, activation, transfer, or physical success. Independent
Reviewer acceptance and fresh exact committed Manager authority are still
required before any paid creation.

## Step-9 Flags For Reviewer

- Recompute all frozen hashes and verify the original fourth harness and every
  accepted receipt are unchanged.
- Run the native-name failure probe and independently inspect its retained file
  and manifest; ensure no fourth-harness alias is staged or retained.
- Rerun the focused/full suites, static/artifact/Bash/shellcheck gates,
  manifests, hygiene, workflow audit, diff checks, and final authenticated
  empty inventory.
- Do not create a Manager record or mutate Brev.
