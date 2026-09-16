# Proper walking: command-only foundation v1

Owner request: solve proper walking. Work in one thread; no paid compute or
hardware. Preserve every old frozen source and negative evaluation.

## Measured diagnosis before this intervention

The same gait-v4 weights step in Genesis at +0.12 m/s, but not in the zero-lag
MuJoCo evaluator. Total modeled mass agrees at 0.73724318 kg. A factorial timing
probe distinguishes a deployment-loop mismatch from simply a weak reward:

| Motor / sensor delay | +0.12 m/s swings L/R | +0.25 m/s swings L/R |
|---|---:|---:|
| 0 / 0 ms | 0 / 0 | 0 / 0 |
| 0 / 20 ms | 0 / 0 | 13 / 37 |
| 20 / 0 ms | 0 / 0 | 34 / 35 |
| 20 / 20 ms | 33 / 33 | 31 / 31 |
| 30 / 20 ms | 29 / 29 | 29 / 28 |

The last two timing profiles pass the old **forward** gait rejection checks.
Every pure-turn probe still fails. These are feedback interventions, not
fixed-action physics isolation or calibration of actual hardware latency.
Training already includes motor lag 15–30 ms and sensor lag up to 20 ms; the
old evaluator omitted both. Preserve its failures and fix this as an explicit
versioned control-loop model, not by changing old thresholds or policy outputs.

## Intervention

- Command-only curriculum: 55% forward 0.08–0.22 m/s, 30% left/right in-place
  turn 0.35–0.75 rad/s, 10% arcs and 5% stop. Change every 3–6 seconds.
- No mass/COM/friction/push perturbations yet; preserve model/BAM constants.
- Train motor delay 0–30 ms and sensor delay 0–20 ms so the zero-delay
  evaluator is part of the requested timing envelope, not the only model.
- Use collision-sole minimum height rather than center-site height. Dense
  single-support lift feedback and a 0.6-per-valid-landing event reward replace
  the requirement to earn both steps before receiving full movement credit.
- Keep actual-joint-stop, slip, smoothness and fall costs. No scripted actions,
  phase clock, external forces, joint clipping or assisted gait starts.
- Compatible actor: 61D input, 14D actions, normalized ONNX, 50 Hz unfiltered
  output. Physical latency is distinct from an action smoothing filter.

## Bounded run and selection

Warm start actor and critic from the retained gait-v4 final checkpoint
`aa6cb4c3b1dcca6c3d4f60dc0e8de0095f10607776879fd70033f986526e5bb0`,
but reset optimizer/iteration for the new objective. Local 64×5 smoke, then
at most 1,024×1,000×24 = 24,576,000 new transitions, seed 26090511. Retain
intermediate checkpoints for diagnostics; only the final checkpoint may be
the candidate. A setup/software exception is a retained failed attempt.

## Evaluation frozen before candidate inspection

Fresh visible cases: +0.08, +0.12, +0.20 m/s, ±0.5 rad/s pure turn, and ±0.4
rad/s arcs at +0.12 m/s. Each is 18 s: stand 1 s, move 12 s, stop 5 s.
Nominal timing: 20 ms motor and 20 ms sensor lag. Zero-lag and 30/20-ms
versions are separately required robustness buckets. No reserved bank opened.

Require full duration, no fall/non-foot support, old actual-joint/slip/step
thresholds, mean absolute forward error ≤0.05 m/s, yaw error ≤0.20 rad/s,
lateral mean absolute speed ≤0.05 m/s; last 2 s speed ≤0.04 m/s and yaw speed
≤0.15 rad/s, tilt ≤15 degrees. Pure turns require sustained bilateral steps
during actual turning, not translation; their XY excursion must stay ≤0.20 m.
Movement cases need ≥60% sustained bilateral stepping during movement and
at least two qualified swings per foot. Standing still cannot pass a turn.
Report every timing/case bucket, no aggregate hiding a failed required bucket.

Freeze evaluator sources before looking at the candidate. Retain real rendered
foot-close-up video, complete 50 Hz traces and original float32 actions.
Development walking acceptance is not physical calibration or transfer proof.

Research context: periodic foot-contact objectives are established in biped RL
([Siekmann et al.](https://arxiv.org/abs/2011.01387)); this intervention uses
measured contact events rather than adding a clock to the deployed interface.
