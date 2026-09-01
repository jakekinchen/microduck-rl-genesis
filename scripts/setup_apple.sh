#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APPLE_ENV="${MICRODUCK_APPLE_ENV:-$PROJECT_ROOT/.venv-apple}"
LOCK_FILE="$PROJECT_ROOT/environments/apple/requirements.lock"

if [[ "$(uname -s)" != "Darwin" || "$(uname -m)" != "arm64" ]]; then
    echo "Apple setup requires macOS on Apple Silicon." >&2
    exit 1
fi
if ! command -v uv >/dev/null 2>&1; then
    echo "uv is required: https://docs.astral.sh/uv/" >&2
    exit 1
fi
if [[ ! -f "$LOCK_FILE" ]]; then
    echo "Missing lock file: $LOCK_FILE" >&2
    exit 1
fi

uv venv --python 3.12 "$APPLE_ENV"
uv pip sync --python "$APPLE_ENV/bin/python" --require-hashes "$LOCK_FILE"

GS_ENABLE_ZEROCOPY=1 "$APPLE_ENV/bin/python" - <<'PY'
import genesis as gs
import torch

if not torch.backends.mps.is_available():
    raise SystemExit("PyTorch MPS is unavailable")
gs.init(backend=gs.metal, logging_level="warning")
if gs.backend != gs.metal:
    raise SystemExit(f"Genesis Metal requested but got {gs.backend}")
print(f"Apple environment ready: torch={torch.__version__}, mps=True, genesis={gs.__version__}")
PY

echo "Environment: $APPLE_ENV"
echo "Next gate: $PROJECT_ROOT/scripts/run_apple_smokes.sh"
