# Apple scaling sweep receipt

Run ID: `20260903T202404Z-aa4c567`

Source commit: `aa4c5676879e2681a127d90ccfa696307088adfa`

Machine class: `Mac15,14` (serial number deliberately not recorded)

Devices: Genesis Metal physics and PyTorch MPS learner

| Environments | Construction s | Warmup s | Collection s | PPO update s | Total iteration s | Samples/min | Peak RSS GiB | Proxy headroom | Thermal after |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 64 | 12.475 | 2.823 | 2.064 | 0.273 | 2.337 | 39,441 | 1.755 | 98.17% | nominal |
| 128 | 20.689 | 3.627 | 2.440 | 0.264 | 2.704 | 68,159 | 1.835 | 98.09% | nominal |
| 256 | 36.794 | 3.592 | 2.679 | 0.265 | 2.943 | 125,245 | 1.903 | 98.02% | nominal |
| 512 | 68.324 | 3.859 | 3.217 | 0.275 | 3.492 | 211,124 | 2.042 | 97.87% | nominal |
| 1024 | 130.958 | 4.492 | 3.982 | 0.289 | 4.271 | 345,246 | 2.164 | 97.75% | nominal |

The thermal field is the historical warning state returned by `pmset -g therm`;
it is not continuous temperature, power, fan, or throttling telemetry. Peak RSS
is an explicit process-resident-memory proxy, not complete Metal allocation or
system-wide unified-memory pressure.

This short public-development sweep is performance characterization only. It
does not train or rank a final candidate, realize held-out cases, classify task
success, demonstrate transfer, or authorize physical use. No everyday default
is selected until the separately preregistered sustained slice passes.
