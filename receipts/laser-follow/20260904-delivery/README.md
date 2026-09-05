# Before / after: simulated laser-target pursuit

`baseline-left-trained-right.mp4`: **left** is the earlier first-party policy;
**right** is the new 500-iteration PPO policy plus the versioned v2 approach
steering. Both use the same forward-target scene, initial state, camera, and
MuJoCo/BAM evaluator. Twelve seconds, real-time 50 fps, 1280×480, no audio.
Only the two rendered videos are stacked; no motion is edited or accelerated.

The baseline moves about 1.4 cm; the trained system moves about 44.2 cm and
settles 20.9 cm from the target. The full suite—not only this selected view—
passes 6/6 visible-development cases in MuJoCo and Genesis with the v2 adapter.
An old-policy/new-steering ablation still fails pursuit, and the original
trained-policy/v1-steering failure is retained.

The red dot is a non-colliding rendered marker at the simulator's target.
Control currently uses its known simulated coordinates, not camera pixels.
This is not a hardware demonstration, blind held-out result, or camera-loop
acceptance. Next: resolve the head-camera frame and validate pixel-based control.

Sources:

- `../20260904-v1-baseline/forward.mp4`
- `../20260904-v2-steering/forward.mp4`
- `../20260904-v2-steering/evaluation.json`
- `../20260904-v2-genesis/evaluation.json`
- `../../../experiments/laser/README.md` (from repository root: `experiments/laser/README.md`)
