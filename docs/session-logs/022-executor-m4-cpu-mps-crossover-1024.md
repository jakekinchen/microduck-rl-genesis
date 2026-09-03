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

## Execution result

- Ran CPU+MPS and Metal+MPS at 1024 from clean commit `e6d35ce`.
- Both rows completed 20/20 finite measured iterations, every thermal sample
  was nominal, and minimum RSS-proxy headroom was 97.53%.
- CPU median total PPO iteration was 3.0963 s (475,915 samples/min); Metal was
  2.5271 s (572,862 samples/min).
- The frozen on-grid crossover is therefore 1024 environments.
- Durable receipt:
  `receipts/apple-scaling/20260903T205359Z-e6d35ce-crossover-1024/`.

## Default recommendation

Select 1024 environments with Metal physics and MPS learning as the everyday
Apple default. This uses the primary sweep's highest total-iteration-derived
throughput, the passing 120-iteration sustained gate, safe memory/thermal
proxies, and the matched crossover. Retain CPU physics plus MPS learning as the
debug fallback; it was valid and faster from 64 through 512.

## Evidence boundary

Performance characterization only. No final candidate, held-out realization,
task-success, transfer, activation, paid compute, or hardware action occurred.
