# Slice Brief 017 - M3 success classifiers

**Date:** 2026-09-02

## Objective

Freeze executable walking and backflip acceptance classifiers and synthetic
known-positive, assisted, and failure fixtures before any candidate result.

## Acceptance Criteria

- Walking requires exact command/start/seed coverage plus every frozen
  survival, tracking, stop, slip, orientation, joint/torque, deadline, and
  finite-state threshold.
- Backflip requires ordinary standing start, zero assistance, supported
  takeoff, one uninterrupted backward airborne revolution, feet-only first
  recontact, landing margins, and a continuous stable hold.
- Curriculum/recovery starts remain distinct from acceptance starts.
- PPO return is never an input.
- Known-positive, assisted, and failure fixtures classify as preregistered;
  malformed/incomplete coverage fails closed.

## Evidence Boundary

Synthetic classifier fixtures only. Passing them validates state-machine logic,
not any policy, task success, backend comparison, transfer, or hardware result.
