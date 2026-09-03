# Apple sustained stability receipt

Run ID: `20260903T203517Z-3223b26-sustained`

Source commit: `3223b260697f222cc29bd47ced48e81110e6d917`

Candidate size: 1024 environments

Devices: Genesis Metal physics and PyTorch MPS learner

- Measured PPO iterations: 120 after two warmups
- Rollout steps per environment: 24
- First-20 median total iteration: 2.5049 s
- Last-20 median total iteration: 2.4372 s
- Last/first median ratio: 0.9730 (acceptance ceiling: 1.25)
- Overall p50 / p95 total iteration: 2.4801 s / 2.6064 s
- Total-iteration-derived throughput: 591,736 samples/min
- Peak RSS proxy: 2.741 GiB; proxy headroom: 97.15%
- Finiteness: 120/120 observations and actor/critic parameter checks passed
- Thermal: all 15 declared `pmset -g therm` samples nominal
- Termination: completed

The thermal method exposes warning state, not continuous temperature, power,
fan speed, or throttling telemetry. Peak process RSS is an explicit proxy and
does not capture every Metal allocation or system-wide unified-memory pressure.

This is performance and stability characterization on public development data.
It retains no checkpoint and provides no final-candidate, held-out,
task-success, transfer, activation, or physical evidence.
