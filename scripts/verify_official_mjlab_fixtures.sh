#!/bin/sh
set -eu

: "${BAM_REPO:?set BAM_REPO to the clean pinned Rhoban/BAM checkout}"
: "${OFFICIAL_MJLAB_PYTHON:?set OFFICIAL_MJLAB_PYTHON to the locked mjlab Python}"

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
export MJLAB_WARP_QUIET=1
exec "$OFFICIAL_MJLAB_PYTHON" \
  "$ROOT/tests/test_official_mjlab_fixtures.py" \
  --bam-repo "$BAM_REPO"
