#!/bin/sh
set -eu

: "${BAM_REPO:?set BAM_REPO to the clean pinned Rhoban/BAM checkout}"

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
OFFICIAL_MJLAB_PYTHON=${OFFICIAL_MJLAB_PYTHON:-"$ROOT/validation/official-mjlab/.venv/bin/python"}
if [ ! -x "$OFFICIAL_MJLAB_PYTHON" ]; then
  echo "Missing locked official-mjlab environment." >&2
  echo "Run: $ROOT/scripts/setup_official_mjlab.sh" >&2
  exit 1
fi
export MJLAB_WARP_QUIET=1
exec "$OFFICIAL_MJLAB_PYTHON" \
  "$ROOT/tests/test_official_mjlab_fixtures.py" \
  --bam-repo "$BAM_REPO"
