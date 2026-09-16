# Controlled walking v2 — frozen training intervention

V1 was stopped after 8,773,632 logged completed transitions (plus an unknown
partial iteration). The retained checkpoint250 diagnostic stepped and turned,
but all four probes failed: 4.1–8.1% motor saturation, loaded slip and failure
to settle. Nominal median swing air time was 0.10 s; zero-lag 0.06 s. The flat
0.6-per-landing reward paid a rapid tapping gait; its training landing rate
grew to roughly 11/s. Preserve v1 source, logs, weights and terminal receipt.

Change only the reward/curriculum in a new subclass:

- Replace flat landing credit with 0.6 times a Gaussian of measured preceding
  air duration, centered at 0.16 s with 0.06 s width. This is an experimental
  controlled-step objective, not a calibrated hardware cadence. No phase clock.
- Observe the actual BAM motor torque at all four 200-Hz substeps. Penalize
  squared normalized effort above 70% of the unchanged kt × current limit,
  summed over joints, averaged over substeps, at weight -4/s.
- Increase action-rate cost from -0.12 to -0.25. This is a learning objective,
  not action smoothing, clipping, or a deployment filter.
- Sample 40% forward, 25% pure turn, 10% arc, 25% stop. Keep command ranges
  and 3–6 s switching. During stop, penalize normalized planar/yaw speed at
  weight -3/s in addition to existing zero-command tracking rewards.

Keep model, BAM law, collision geometry, 61D normalized actor, ordered 14D
actions, 50 Hz, physical/sensor timing training envelope, and every evaluator
threshold unchanged. This is a bundled controlled-motion reward hypothesis,
not an ablation claiming a unique cause for each individual change.

Warm-start actor/critic only from diagnostic v1 checkpoint250:
`c1ab3f1a8cb028c8c41426dd7c6eb4bffdd8dc5da837893f01ff912ba30efe8d`.
This initialization is not a selected or accepted policy. Reset optimizer and
iteration. Seed 26090512. Local 64×5 smoke, then at most 1,024×750×24 =
18,432,000 new transitions. Final-only candidate; intermediate checkpoints may
diagnose failure but may not be cherry-picked for acceptance. Stop a clearly
harmful or degenerate attempt and retain it. No automatic continuation.

Evaluate all 21 unchanged suite-v1 command/timing cases, including zero-lag,
pure turns and stops, using frozen evaluator-freeze-v1. Retain full actions,
state, 200-Hz torques, video and parity proof. All required buckets must pass;
software smoke or visually plausible steps are not proper-walking acceptance.
Reserved/held-out banks, paid compute, hardware, publication and activation
remain outside this local development run. No model adjustment is justified
by this reward diagnosis.
