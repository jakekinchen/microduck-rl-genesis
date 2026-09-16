# V56: matched standing face-posture refinement

**Status: prepared but unexecuted; feasibility prerequisite failed.** See
`POSTURE-FEASIBILITY-RESULTS-v56.md`. No paired conformance, training freeze,
smoke, PPO arm or candidate evaluation has run. Reassess the contact model and
target-feasibility question before resuming this draft.

September 15–16, 2026. The owner authorized the full researched sequence and
subagents. This is a bounded local development experiment; V30 remains retained.

The V54 shared actor and critic initialize both arms, with the exact checkpoint
and frozen normalizers used in V55. Both keep downhill yaw weight 3, the existing
61D observation/14D action contract, unfiltered 50 Hz control, 200 Hz native
MuJoCo/BAM and complete-contact-v11 model. V54 replay, online teachers, cold
optimizers, PPO 3e-5 fixed, gamma .999, entropy zero, architecture and learned
exploration initialization remain unchanged. No failed V55 examples are labels.

Control adds no cost. Face2 adds only, during exact-zero-command standing:
`2 * (max(abs(world-space face pitch in degrees) - 25, 0) / 5)^2`.
The face metric is the same geometric quantity used by final-standing evaluation.
The 25-degree target provides five degrees of headroom below the unchanged
30-degree acceptance threshold. Existing head-joint/body costs stay active.
Walking rewards and all physical parameters remain unchanged. Record the actual
face angle, applied cost and every observation/action/reward for reconstruction.

Before learning, freeze and run the separate zero-command standing-feasibility
protocol, and complete the current upstream contact/runtime audit. Feasibility
requires at least one unchanged standing actor to satisfy all six declared
downhill timing/yaw cases with the 25-degree target and contact/settling checks.
A failure leaves feasibility unresolved, and blocks this proposed objective
pending a separately recorded diagnostic. It is not proof of impossibility.

Require existing V54/V55 source bindings. Compare the actual V55 weight-3
environment against face weights 0 and 2 over 1,200 controls in all 24 cells
using the same V54 shared actions. Observations, physics, loads, resets and
coverage must be byte-identical; control rewards must match exactly. Reconstruct
the intervention cost independently from recorded face angles and mode flags.
Retain the earlier full-layout conformance evidence. Source freeze includes
all new scripts, model dependencies, protocol and evaluation suites.

Each arm gets one 24×5×24 smoke (2,880 transitions) and one 48×2250×24 main
run (2,592,000 transitions), with seed 26091656. Final2249 only. No extensions,
alternate checkpoint selection or tuning after outcomes. Failures/interruption
are retained. The 18/36/180-second curriculum and all 24 terrain/timing/yaw
training cells are unchanged. Stop a main run if source/finite-data/storage
checks fail. Each compute launch is conditional on the advisory guard; all
subagent simulation jobs are serialized with these runs.

Run all frozen exposed banks for both finals: 21 flat, 42 repeated flat,
two full 180-second compositions, original two 36-second downhill sessions,
two already-exposed heading-interpolation sessions and all 14 surface sessions.
The old V55 "fresh" file label is historical: these headings are now exposed,
not a new generalization test. Preserve their source values without relabeling
them as protected data. Parent evaluation on these same headings supplies a
current reproducibility reference. Freeze every evaluator before candidate runs.

Advancement requires all 63 flat cases, both compositions, all four downhill
sessions, all five original surface passes, every inherited component gate,
and at least one complete level-2 training episode plus both handoff directions
in every training cell. Mean absolute walking yaw remains <=.20 rad/s and final
standing face pitch <=30 degrees. Missing cases are failures. An evaluator's
exit code does not determine acceptance.

If only one arm passes all requirements, use that recipe for two further
preregistered seeds. If both pass, select face2 only when every downhill final
face metric improves and no control surface pass is lost; otherwise keep
control. If neither passes, retain V30 and diagnose the first failed component,
including actual experience and per-mode optimization, before choosing one
additional change. Do not automatically launch replication or terrain training.

All results are exposed simulation development. Protected environment families,
unseen-terrain acceptance, assembly/carpet calibration, physical endurance and
hardware transfer remain separate gates under BEHAVIOR_VALIDATION.md. No paid
compute, hardware, activation or publishing is authorized by this protocol.
Bulk artifacts use the UUID-verified second external drive. No existing frozen
source or receipt is rewritten.
