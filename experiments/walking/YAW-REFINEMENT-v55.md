# V55: matched downhill yaw refinement

September 12, 2026. Local simulated development authorized by “Proceed.”
One active property group: the downhill walking absolute yaw-error weight.
The retained reference remains original V21/V15 with V30. V54 shared is a
promising development initializer, not an accepted or activated policy.

## Fixed comparison

Both arms load the exact V54 shared FINAL actor AND critic from
`recipe-native-20260909-v54-shared/model_1499.pt`, SHA-256
`9a3e57d975c080f72541eabcd2bcccc4f5a573b98ff299969befef684b5b7f26`.
Keep its learned exploration standard deviations unchanged at initialization,
frozen observation normalizer, architecture and 61D critic inputs. Optimizers
start cold in both arms. This is continuation, not a repeat of V54's cold critic.

Control uses the existing downhill walking cost
`3 * abs(actual yaw rate - requested yaw rate) / .20`.
Intervention uses weight **6** in the identical expression. This doubles the
cost of alternating rate excursions as well as constant rate error. It does
not identify the physical cause of V54's approximately 3.27-Hz oscillation.
All other rewards, original V21/V15 online flat teachers, V54's 83,700-row
mode-balanced replay, normalization and PPO settings stay unchanged. Failed
V54 downhill sessions supply no imitation targets. Flat rehearsal remains
weight one, 256 moving plus 256 standing rows per minibatch, scaled by .03 rad.
PPO remains 3e-5 fixed, gamma .999, five epochs/four minibatches, zero entropy
bonus and [.005,.15] learned exploration limits. Shared actor in both slots.

Each arm gets exactly one 24-env × 5-iteration × 24-step smoke (2,880
transitions), then one 48 × **2250** × 24 run (**2,592,000** transitions).
Seed **26091255** in both arms. Final iteration **2249** only; no best-checkpoint
selection, extensions or retuning after inspecting results. Main total
5,184,000 transitions, smoke total 5,760. The extra 750 iterations relative to
V54 give more opportunity for complete 180-second training episodes; coverage
is measured, never inferred from budget. Stop and retain failed/interrupted
runs. A smoke failure blocks that arm's main run pending a separately recorded
implementation correction; do not silently restart or count it as success.

## Physics, experience and preflight

Use unchanged native MuJoCo 3.12.0, complete-contact-v11 model, pinned BAM,
V16 ramp, V30 float32 heading controller, raw 50-Hz position actions and
200-Hz physics. No filtering, new observation, privileged critic, physical
parameter fit or terrain motion. V54's fixed 24 template/timing/yaw cells,
18/36/180-second outcome-gated curriculum, advancement rule and full HOME
resets remain byte-for-byte source-equivalent except yaw-weight plumbing.
Templates retain the original deterministic seed; learner seed is above.

Verify old source-bound 72-cell/layout conformance evidence. Before learning,
compare the actual V54 environment against each new coefficient environment
for 1,200 controls across all 24 cells with identical V54 shared ONNX actions.
Require byte-identical observations, actions, physical states/constraint loads
and non-accumulating reset histories; independently reconstruct the changed
reward from retained components. This is conformance, not behavior success.
Record every training actor input/action, reward components, episode outcomes,
mode switches and realized curriculum exposure. Evaluation retains complete
physics-rate internal-load evidence and raw ONNX actions.

## Frozen evaluation and decisions

Freeze all evaluator sources and `yaw-development-v55.json` before either
smoke, training or candidate evaluation. Keep old gates/thresholds unchanged:
63/63 flat, both full 180-second compositions, both complete 36-second downhill
sessions, and retention of all five originally passing surface sessions.
Run all 14 exposed surface sessions even if earlier banks fail.

Two newly preregistered visible downhill sessions use initial headings .04
and .08 rad, otherwise the same fixed +3-degree slope, nominal mass/friction,
6-tick motor/1-tick sensor delay and two successive 18-second walk/stop windows.
Seeds 260912550 and 260912551. Evaluate the V54 initializer and both new finals
on these two sessions. These are heading interpolation checks on the same
terrain, **not unseen-terrain or protected-bank generalization evidence**.
No results from these starts are added to training or replay in this activity.

Advancement requires every old required task/gait/heading/posture/contact/load
and settling gate, both new sessions, and at least one complete level-2 episode
plus both transition directions in every one of the 24 training cells. In
particular, downhill mean absolute yaw error must be <=.20 rad/s and final
standing face pitch <=30 degrees. Survival and reward cannot waive these.
Missing/partial cases fail admission. Read every component result; evaluator
exit zero means completion only. Compare paired case values and failures,
not just means. Identical starting tensors do not ensure identical experience
once the policies differ; report realized curriculum differences explicitly.

If only yaw6 passes all prerequisites, prefer it for two newly preregistered
replication seeds. If both pass, prefer yaw6 only if all four original downhill
walking-window yaw errors are no worse and all control surface passes are
retained; otherwise prefer the lower-weight control. If neither passes, retain
V30, keep V54 as the last development starting point, inspect the first failed
component and select the next isolated experiment from results/research.
Do not open protected terrain, add physical claims or automatically broaden
training. Head-posture, retention, coverage and critic/history changes are
separate possible follow-ups, not part of this intervention.

New bulk artifacts use the UUID-checked second external drive under
`CodexOffload/MicroDuck/20260912-yaw-v55`. Preserve existing artifacts. Guard
and condition each local compute launch; no overlapping simulation jobs,
paid compute, publication, activation or hardware work. Dedicated artifact
verification is separate from the workspace viewer's external-symlink limit.
