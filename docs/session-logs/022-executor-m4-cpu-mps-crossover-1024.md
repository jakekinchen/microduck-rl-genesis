# Executor log 022 - M4 CPU+MPS crossover at 1024

**Date:** 2026-09-03

**Role:** Executor

**Brief:** `docs/briefs/022-m4-cpu-mps-crossover-1024.md`

## Implementation

- Extended only the accepted crossover schema, CLI size choice, and decision
  grid to admit the preregistered 1024 pair.
- The seed/configuration, two warmups, 20 measured PPO iterations, devices,
  timing, thermal, memory, and finite-state protocol are unchanged.

## Verification

- Focused Apple scaling/crossover tests - passed in `.venv-apple`.
- Python compilation, schema parsing, and `git diff --check` - passed.

## Evidence boundary

Implementation only at this point; no new performance or task evidence claimed.
