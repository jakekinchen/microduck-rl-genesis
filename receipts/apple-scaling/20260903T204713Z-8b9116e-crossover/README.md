# Apple CPU+MPS fallback crossover receipt

Run ID: `20260903T204713Z-8b9116e-crossover`

Source commit: `8b9116e4e417eec9adc28590d8212b1b187e6e84`

Each row uses two warmups and 20 measured PPO iterations with identical seed
and configuration. Only Genesis physics changes; the learner remains MPS.

| Environments | CPU median s | Metal median s | CPU samples/min | Metal samples/min |
| ---: | ---: | ---: | ---: | ---: |
| 64 | 0.4475 | 2.1608 | 208,876 | 42,615 |
| 128 | 0.5417 | 2.2552 | 340,646 | 81,536 |
| 256 | 0.9432 | 2.2923 | 390,770 | 160,159 |
| 512 | 1.5747 | 2.3473 | 468,447 | 310,617 |

The CPU+MPS debug fallback is operational and faster throughout the frozen
64-512 grid. Therefore the honest preregistered result is that the crossover
was not observed and is above 512; this receipt does not infer its exact point.
All rows were finite, all thermal warning-state samples were nominal, and the
minimum RSS-proxy headroom was 97.69%.

This is performance characterization only. The thermal and memory methods are
bounded proxies, and no checkpoint, final candidate, held-out result,
task-success, transfer, activation, or physical evidence was produced.
