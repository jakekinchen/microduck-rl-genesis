# Incomplete diagnostic, not a passing full-collision receipt

The v1 script completed the slow-forward pair, then refused the nominal
left-turn input because its original v9 FINAL rollout fell before 900 frames.
The original action trace and failed controller result remain unchanged.
Stdout: `/private/tmp/walking-v9-full-collision-replay.log`.

A separately retained r2 diagnostic permits the exact partial action prefix
only for a manifest-verified terminal-fall case, labels its limited duration,
and neither pads the trace nor changes original acceptance. This directory
must not be presented as a completed two-case audit.
