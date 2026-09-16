# V46: preserve V15 standing and correct walking under explicit retention

V45 isolates V44's near-limit/zero-delay regressions to its walking replacement
and composition falls to its standing replacement in the tested pairs. Revert
both learned components as initialization: original V21 walking and V15 standing.
Train only the walker. Standing stays deterministic with frozen parameters and
normalizer, and is excluded from PPO's actor objective. The original V15 export
is used in evaluation. No new stander or general-terrain training is authorized
by this experiment.

One 12x5x24 smoke (1,440 transitions) and one 60x250x24 full run (360,000), seed
26090746, FINAL249 only. No checkpoint selection or automatic extension. Same
native contact-v11/BAM physics and V16/V30 controllers, 61D/14D ABI, 50-Hz raw
actions and 200-Hz integration as V44. Fixed actor normalizers; cold critic and
optimizer. V21 walking exploration std starts at one quarter of the parent.
Standing actions have no exploration. Applied action/observation checks and full
recording remain. Twelve equal cells (five environments each) cross V44's two
flat orders, downhill and uphill with original timings (4,1), (0,0), (6,1).
54-second continuous episodes and all resets retain full controller/FIFO state.

The correction combines restricted trainable parameters, timing coverage and
retention; it is not an ablation identifying each training design choice.
Before learning, compare original closed-loop controls and repeated HOME resets
in all twelve cells, including fall cases. Materialized terrain and delay values
must be recorded; configuration is not sufficient evidence.

Use a scoped nonrecurrent PPO update with the original clipped surrogate and
critic objective, fixed learning rate 1e-5, gamma .999, five epochs, four batches.
No RND, symmetry, recurrence or multi-GPU path. Actor surrogate uses moving
samples only. Each minibatch adds equally weighted squared action deviations,
normalized by .03 radians, from the frozen V21 teacher on current moving inputs
and from 512 uniformly sampled original passing flat replay rows. Replay labels
are original stored action tensor values, aligned to their actual observations.
All 63 replay-source windows are exposed development; they are not held out.

Reward otherwise follows V44, except the binary absolute .04-radian joint cost
becomes a continuous per-joint cost:
`10 * sum(max((.07 - actual_margin / joint_range) / .05, 0)^2)`.
This gives gradients through the policy objective before the independent 5%-range
occupancy band. It does not redefine the 20% occupancy or .02-radian margin gates.
Reward evidence never substitutes for applied-load, body geometry or gait checks.

Acceptance: all 63 original flat windows, both 180-second compositions, both
original downhill sessions, and no loss of V30's five passing exposed surface
sessions. Evaluate all four exposed banks even if earlier prerequisites fail,
to retain a complete diagnosis. Promote no result on partial survival or reward.
V44's separately frozen fresh sequence bank and protected terrain banks remain
unrun unless all prerequisites pass. Physical calibration and carpet/robot
transfer remain unmet. On failure, stop and retain V30, report exact failed gates
and recommend the next targeted experiment. No paid compute or hardware.
