# V52: state-conditioned braking residual from V51 demonstrations

V51 admitted all three first-stop demonstrations after one384-trial retargeting
search. They do not establish repeatable recovery or complete walking success.
Train one supervised residual actor on their first125 control observations and
actual action deltas relative to frozen V50 walking/V15 standing. Include zero
residual labels from13–15.5s of all63 passing V50 flat windows, both passing
180s compositions and five passing whole surface sessions. Data are exposed.
This is supervised demonstration distillation, not additional PPO/RL training.

One CPU run, seed26090852, FINAL step2000 only. MLP61-64-64-14 with ELU,
empirical input normalization/std floor.05, zero final layer initialization,
Adam3e-4,256 samples/update equally split demonstration/retention, .03rad-scaled
MSE, gradientnorm1. Fixed512000 sample draws, no validation-driven checkpoint
selection or extension. Export normalized ONNX, verify every training input and
1000 random inputs within1e-4rad. Retain all2000 losses and exact data hashes.
No time, terrain label or world state enters the61D actor input.

Versioned controller adds the learned14D residual for125 control ticks after
a requested-motion-to-zero edge, cancelling on a new moving command. Steady
standing and ordinary walking outside this2.5s event use their frozen original
actors. This event routing is a declared controller change; it is not action
filtering, clipping or deployment of the time-indexed search controller. The
late13.14s demonstration contains a different recovery onset; state-only
imitation is evaluated under the same13s requested-stop event as every case.

Freeze all code and unchanged evaluator suites before learning. Evaluate all63
flat cases, both downhill36s sessions, both180s compositions and14 surface
sessions. Require every original gate, including .20 absolute yaw, head posture,
successive stops, internal loads, gait and full-session heading. Parent V50
walking still misses the pre-braking yaw gate, which this transient controller
cannot retroactively fix. No full admission unless every required component
passes. Do not open fresh/protected banks. On failure keep V30, preserve
negative results and identify the earliest failed component for the next task.
No physics changes, paid compute, hardware, activation or physical-transfer claim.
