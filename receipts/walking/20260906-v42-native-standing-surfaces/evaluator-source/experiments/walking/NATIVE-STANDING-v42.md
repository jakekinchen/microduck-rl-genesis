# V42 native stationary-posture objective

V41 FINAL fails all four sessions and all 24 windows. Downhill falls now occur
near 3.1 s, and both otherwise complete compositions violate standing posture.
Reject V41. Its positive posture exponential can vanish while a folded posture
avoids an explicit cost; standing yaw rate also lacked a direct objective.

Repeat the V41 native experiment from exact V15 FINAL with the same seed
26090641, eight full-state templates, 50/50 HOME/handoff process, cold critic,
PPO settings, 8×5 smoke and one 64×250 run (384,000 transitions), FINAL only.
The sole intervention group is the stationary-posture objective. Subtract
these additional rates (multiplied by .02 seconds each control step):

- `4 * (max(trunk_tilt_deg - 10, 0) / 5)^2`;
- `2 * mean((max(abs(head_joint_error_rad) - .2, 0) / .15)^2)`;
- `.5 * (yaw_rate_rad_s / .3)^2`.

All V41 physics, reset continuation and action identity checks remain. All
original flat, downhill/composition and surface acceptance thresholds remain.
Freeze the candidate before evaluation. Preserve V41 and V38 negatives; no
checkpoint search, accepted raw-policy claim or broad Genesis surface training.
The unresolved cross-engine and physical-calibration limitations still apply.
The complete operating envelope, observation contract, independent verification,
split/coverage/transition rules and expansion gate are inherited explicitly
from `NATIVE-STANDING-v41.md` and `docs/workspace/BEHAVIOR_VALIDATION.md`.
