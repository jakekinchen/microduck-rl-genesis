# Apple Silicon environment

This is the pinned Apple lane for Genesis Metal physics and PyTorch MPS PPO.
It is deliberately separate from `requirements.txt`: the Linux ROCm/CUDA
containers inherit their vendor PyTorch build, while Apple installs the macOS
arm64 PyTorch wheel.

## Install

Requirements: Apple Silicon, macOS, and `uv`.

```bash
./scripts/setup_apple.sh
```

The script creates `.venv-apple`, installs the hash-locked Python 3.12
environment, and fails unless both Genesis Metal and PyTorch MPS are visible.
Override the environment location with `MICRODUCK_APPLE_ENV=/absolute/path`.

## Acceptance ladder

```bash
# Deterministic, dependency-free contract drift check.
.venv-apple/bin/python scripts/freeze_contract.py --check

# CPU reference/conformance tests. BAM comparisons require BAM_REPO.
GS_ENABLE_ZEROCOPY=1 .venv-apple/bin/python tests/run_all.py

# Bounded 64-environment x 5-iteration walking and backflip smokes.
./scripts/run_apple_smokes.sh
```

A smoke proves that the simulator, learner, checkpoint path, and task code
execute together. It does not prove a usable gait, autonomous backflip,
held-out MuJoCo success, or physical transfer. Promotion gates and required
receipts are tracked in [`../../TRAINING_ACTUALIZATION.md`](../../TRAINING_ACTUALIZATION.md).

## Updating the lock

Only update the lock as an explicit dependency change, then rerun both smokes:

```bash
uv pip compile --python-platform aarch64-apple-darwin \
  --python-version 3.12 --generate-hashes \
  environments/apple/requirements.in \
  --output-file environments/apple/requirements.lock
```

Commit the input, lock, smoke receipts, and the reason for the change together.
