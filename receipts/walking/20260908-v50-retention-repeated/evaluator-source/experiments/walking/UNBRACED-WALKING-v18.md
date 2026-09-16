# V18: walking must not earn return by bracing against its own body

V15 standing refinement passes 21/21 original but 33/42 fresh windows.
V16 command slew (.75 m/s^2, 2.5 rad/s^2) repairs tested fast-forward stops
but is 5/6 in the repeated handoff diagnostic: one walking startup braces.
V17 gentler yaw slew is worse, 4/6, and is rejected. These are exposed
development results, not a gain search or physical validation.

Train exactly V13 FINAL as initializer, actor/critic only, not optimizer or
iteration. Change one training property group: apply the same V15 summed
internal-force gate/cost to ALL walking commands. Keep V13 command sampling,
HOME resets, complete V11 contacts, persistent timing randomization, BAM,
61D/14D actor, head/body commands, all inherited negative costs and raw actions.
No hand-crafted reset corpus or action teacher is introduced. The existing
5-percent standing command population stays unchanged. This is a hypothesis
about learned low-speed transitions, not proof that HOME resets cover all
handoff states or that the two simulators' force sums are equivalent.

Frozen budget: seed26090618, LR2e-4, 64x5 smoke then 1024x250x24 = 6,144,000
new transitions on local Metal/MPS. FINAL249 only; no best-of-checkpoint
selection. Abort for nonfinite state or broken interface/source conformance.
Retain the final even if it fails. Do not extend this run based on reward.

Evaluation: exact V15 FINAL standing component and fixed V16 command slew,
V12 IMU heading feedback, V11 model and every existing acceptance limit.
Evaluate original 21 and exposed repeated 42 windows with the same evaluator,
real-observation ONNX parity, native 200-Hz loads, actual videos and full
negative retention. Score original user commands, never ramped references.
Freeze evaluator/source identities before training. Fresh means the already
exposed V15 bank for this regression, not hidden validation. Only after all
63 pass may a new, separately frozen development bank be opened. No camera
pursuit, policy activation, paid compute or physical transfer claim.
