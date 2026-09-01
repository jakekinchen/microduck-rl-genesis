#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APPLE_ENV="${MICRODUCK_APPLE_ENV:-$PROJECT_ROOT/.venv-apple}"
PYTHON="$APPLE_ENV/bin/python"

if [[ ! -x "$PYTHON" ]]; then
    echo "Apple environment missing. Run ./scripts/setup_apple.sh first." >&2
    exit 1
fi

cd "$PROJECT_ROOT"
export GS_ENABLE_ZEROCOPY=1

"$PYTHON" train.py \
    --task walking \
    --physics-backend metal \
    --learner-device mps \
    --num-envs 64 \
    --max-iterations 5 \
    --exp-name apple-smoke-walking

"$PYTHON" train.py \
    --task backflip \
    --physics-backend metal \
    --learner-device mps \
    --num-envs 64 \
    --max-iterations 5 \
    --exp-name apple-smoke-backflip

echo "Apple 64x5 walking and backflip smokes completed."
echo "This is pipeline evidence only; see TRAINING_ACTUALIZATION.md for promotion gates."
