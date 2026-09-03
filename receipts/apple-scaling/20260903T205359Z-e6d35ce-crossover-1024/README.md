# Apple CPU+MPS crossover extension at 1024

Run ID: `20260903T205359Z-e6d35ce-crossover-1024`

Source commit: `e6d35cedae747cc7960cabe10aff269fd2850194`

The matched 1024-environment pair used identical seed/configuration, two
warmups, and 20 measured PPO iterations. CPU and Metal were separate fresh
processes; both used the MPS learner.

| Physics | Median total iteration | p95 | Samples/min | Peak RSS proxy | Proxy headroom |
| --- | ---: | ---: | ---: | ---: | ---: |
| CPU | 3.0963 s | 3.1179 s | 475,915 | 1.645 GiB | 98.29% |
| Metal | 2.5271 s | 2.6460 s | 572,862 | 2.375 GiB | 97.53% |

Metal is no slower than CPU for the first time on the frozen grid, so the
measured crossover is 1024 environments. Both rows completed 20/20 finite
iterations and every thermal warning-state sample was nominal.

Together with the accepted primary sweep and 120-iteration sustained receipt,
this supports 1024 Metal/MPS as the everyday Apple default. CPU+MPS remains the
verified debug fallback and is faster on the measured 64-512 grid.

This is performance characterization only. No checkpoint, final candidate,
held-out result, task-success, transfer, activation, or physical evidence was
produced.
