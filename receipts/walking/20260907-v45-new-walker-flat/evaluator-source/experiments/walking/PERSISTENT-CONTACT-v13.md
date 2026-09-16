# V13: learn stable device timing on corrected contact physics

The full fixed V12 command-controller battery is 17/21. All 21 cumulative
heading gates now pass (worst endpoint 6.38 degrees, worst phase 8.94 degrees),
with no falls, head/stop/joint/torque/slip/stepping or self-contact failures.
Only 30-ms motor / 20-ms sensor forward12, forward20, arc-left and arc-right
fail instantaneous yaw-rate MAE: 0.2088, 0.2194, 0.2249, 0.2095 versus the
unchanged 0.20-rad/s limit. They are rejected, not rounded into passes.
The fresh development bank remains unopened.

## Next active property: temporal delay sampling

Use the separately tested `EpisodeDelayBuffer` from the conditional v10 draft:
same 0..6 motor physics-tick and independent 0..1 sensor control-tick uniform
ranges, but hold each device's delays for its episode instead of resampling
motor delay every 0.32 s and sensors every 1.28 s. Preserve exact FIFO call,
first-value priming, no interpolation, actions/observations, all v9 reward
functions, command/pose/reset/termination functions, voltage and BAM law.

The simulator is the already verified complete-contact-v11 geometry. Unlike
v9 training, this first new learning run therefore includes BOTH corrected
collision coverage and persistent delays; do not claim a clean causal
ablation against the old v9 training run. V11's model-only training proposal
was not run: its closed-loop baseline removed motor/posture/body interference
failures except long-delay yaw before further learning. V12 heading correction
is fixed and available for explicitly labeled controller-plus-actor evaluation;
it is NOT part of the training reward, observations or motor-output path.

## Bounded run and gates

Initialize only from retained v9 FINAL model_749.pt,
`c79e02bc00dabca146b83592582926fc2053114cc5e44cdf822f95aa8ff8fb17`.
Reset optimizer/iteration; fixed public seed 26090523; learning rate 5e-4,
unchanged PPO settings. Freeze source and complete-controller evaluator first.
Require model/self-contact/heading/FIFO/composition tests and a 64x5 smoke.
Then at most 1024x750x24 = 18,432,000 new transitions, final model_749.pt only.
Intermediate checkpoints diagnose regressions, never become the selected
candidate. Clearly degenerate behavior can stop early as a retained negative.

Evaluate final raw policy with the unchanged v11 complete-model battery and
all old reduced-model regressions as separately labeled model sensitivity.
Evaluate final plus unchanged v12 IMU command servo with identical 21 current
cases, all original motor/head/heading limits and additive self-contact gate,
normalized real-observation parity and actual step/stop video. No threshold
relaxation and no claim that servo-assisted command tracking is raw-policy
performance. Only after all complete-controller cases pass, freeze and run
fresh exposed-development headings/commands; no hidden or physical acceptance.
No paid compute, external contact, hardware, policy activation or agent cycles.
