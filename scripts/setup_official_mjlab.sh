#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VALIDATION_PROJECT="$PROJECT_ROOT/validation/official-mjlab"
VALIDATION_PYTHON="$VALIDATION_PROJECT/.venv/bin/python"

if ! command -v uv >/dev/null 2>&1; then
    echo "uv is required: https://docs.astral.sh/uv/" >&2
    exit 1
fi
if [[ ! -f "$VALIDATION_PROJECT/uv.lock" ]]; then
    echo "Missing frozen lock: $VALIDATION_PROJECT/uv.lock" >&2
    exit 1
fi

uv sync \
    --project "$VALIDATION_PROJECT" \
    --frozen \
    --no-install-project

"$VALIDATION_PYTHON" - <<'PY'
from importlib import metadata

expected = {
    "colorama": "0.4.6",
    "mjlab": "1.3.0",
    "mujoco": "3.10.0",
    "mujoco-warp": "3.8.1",
    "scipy": "1.18.0",
    "torch": "2.9.1",
    "warp-lang": "1.12.0",
}
observed = {name: metadata.version(name) for name in expected}
if observed != expected:
    raise SystemExit(f"official mjlab runtime mismatch: {observed}")
print("Official mjlab validation environment ready:")
for name, version in observed.items():
    print(f"  {name}: {version}")
PY

echo "Environment: $VALIDATION_PROJECT/.venv"
echo "Next: $PROJECT_ROOT/scripts/materialize_bam_authority.py /tmp/microduck-bam-authority"
echo "Gate: BAM_REPO=/tmp/microduck-bam-authority $PROJECT_ROOT/scripts/verify_official_mjlab_fixtures.sh"
