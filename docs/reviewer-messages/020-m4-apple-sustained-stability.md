# Reviewer Message 020 - M4 Apple sustained stability

**Date:** 2026-09-03

## Decision

`CONTINUE`

## Evidence Reviewed

- Executor commits `3223b26` and `de89b17` contain the preregistered harness,
  120-iteration receipt, process log, and passing SHA-256 manifest.
- All 120 iterations passed observation and actor/critic finiteness checks.
- All 15 thermal warning-state samples were nominal; peak RSS proxy was
  2.741 GiB with 97.15% proxy headroom.
- The last/first 20-iteration median ratio was 0.9730 against the frozen 1.25
  ceiling; p50/p95 total iteration were 2.4801/2.6064 s.

## Findings

The 1024-environment candidate passes the sustained stability gate and remains
eligible as the everyday Metal/MPS default. The result is performance evidence
only and retained no policy artifact. The declared `pmset` and RSS proxy
limitations remain explicit.

## Milestone State

Sustained Apple stability is accepted. M4 remains active only for the bounded
CPU+MPS debug-fallback crossover measurement and final default decision.

## Next Slice

Proceed to `docs/briefs/021-m4-cpu-mps-crossover.md`.
