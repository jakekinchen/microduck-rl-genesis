---
library_name: onnx
pipeline_tag: reinforcement-learning
tags: [microduck, microduck-policy, mjlab, robotics]
license: apache-2.0
---

# rough-walk-e

Velocity-commanded walking tuned for rough ground (grid tiles, small stairs, rubble, slopes): the shipped alpha_walking fine-tuned 800 iterations on a hostile-terrain ladder. Same command scheme, same motor-power envelope, roughly half the falls.

<video controls muted loop src="https://huggingface.co/RemiFabre/microduck-rough-walk-e/resolve/main/media/preview.mp4" style="max-width:640px;width:100%"></video>

**Command** — twist slots of the 13-D command block (head / body slots: 4 head-joint deltas from HOME, rad (neck_pitch, head_pitch, head_yaw, head_roll) — tracked, same as alpha_walking, unused (zeros)); idle = `[0, 0, 0]`

| slot | meaning |
|---|---|
| twist[0] | vx: forward velocity command, m/s, trained range -0.4 .. 0.4 |
| twist[1] | vy: lateral velocity command, m/s, trained range -0.3 .. 0.3 |
| twist[2] | wz: yaw rate command, rad/s, trained range -1.0 .. 1.0 (achieved ~0.41 at 1.0; ~0.22 at 0.5) |

**What it does** — drop-in replacement for `alpha_walking`: the same velocity-commanded walk (`twist = [vx, vy, wz]`, head commands tracked), fine-tuned 800 iterations on a rough-terrain ladder (grid tiles, small stairs, rubble, slopes). Half the falls of `alpha_walking` on the rough-ground battery (14/110 vs 32/110), crosses 6–9° slopes and ±1.3 cm rubble it previously failed, at the **same motor power** (1.02 W vs 1.03 W on flat — same servo heating).

**Limits (sim only, never run on hardware)** — falls when descending steps ≥ 2 cm; push recovery slightly weaker than `alpha_walking`; on rubble bumps ≥ ~2 cm it steps in place instead of advancing; turn response is more linear than alpha's but tops out lower (0.41 rad/s achieved for 1.0 commanded).

**Try it in simulation (laptop, no robot)**

```bash
git clone -b hostile-terrain https://github.com/pollen-robotics/microduck_rl.git && cd microduck_rl && uv sync   # once
hf download RemiFabre/microduck-rough-walk-e policy.onnx --local-dir policies/rough-walk-e
uv run scripts/infer_policy.py --walking policies/rough-walk-e/policy.onnx        # Linux
```
On macOS the MuJoCo window needs `mjpython` (one-time libpython symlink, then):
```bash
ln -s "$(.venv/bin/python -c 'import sys; print(sys.base_prefix)')/lib/libpython3.12.dylib" .venv/libpython3.12.dylib
uv run mjpython scripts/infer_policy.py --walking policies/rough-walk-e/policy.onnx
```
Keys (in the launching terminal): arrows = velocity, A/E = turn, SPACE = coast, T = pause.

**Try it on the robot** — it is a walking policy: point the `walk` role at it, change nothing else. Keep the stock `alpha_walking` path noted somewhere so you can switch back in one edit.

```bash
scp policy.onnx radxa@<robot>:/home/radxa/policies/rough-walk-e/                   # 1. file on the robot
# 2. on the robot, in /etc/robot/robotd.toml:   [policy]  walk = "/home/radxa/policies/rough-walk-e/policy.onnx"
sudo systemctl restart robotd                                                      # 3. drive it exactly like alpha_walking
```
First hardware test suggestion: flat ground first (gait should feel like alpha), then a doormat/carpet edge, then a gentle ramp. It has never touched hardware.

**Contract** `obs[1,61] f32 → actions[1,14] f32`, normalizer baked in, 50 Hz, targets around HOME × 1.0. Kind perpetual, entry pose standing.
**Provenance** `Mjlab-Hostile-FinetuneFeetProgress-MicroDuck` — pollen-robotics/microduck_rl @ `6cd45fc on branch hostile-terrain (https://github.com/pollen-robotics/microduck_rl/commit/6cd45fc)`, run `pollen-robotics/hostile-e-finetune-feet-progress-20260830-0103 (resumed from alpha_walking's checkpoint, wandb yr25mna4 model_9999)`; exported with `scripts/export.py`.
**Files** `policy.onnx` · `manifest.json` (all of the above, machine-readable) · `media/preview.mp4` (sim rollout)
Format: [Microduck policy sharing](https://github.com/pollen-robotics/microduck_rl/blob/main/docs/sharing-policies.md).
