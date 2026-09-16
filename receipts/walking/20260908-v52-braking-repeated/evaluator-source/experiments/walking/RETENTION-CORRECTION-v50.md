# V50: downhill yaw correction with original standing retained

V49's original downhill walking prefixes have mean absolute yaw error
.24418568/.24099902 rad/s during 2–13 s, above the unchanged .20 gate. Their
signed means are near zero; left/right oscillations must not cancel in scoring.
V46's all-terrain teacher anchor did not fix this. Keep original V21 walking as
initialization and original V15 standing deterministic and frozen. Train only
the walker; V16 command ramp and V30 heading controller remain fixed.

One 24x5x24 smoke (2,880 transitions), then one 48x750x24 run (864,000), seed
26090850. FINAL749 only, no checkpoint selection, extension or second full run.
Fixed learning rate 3e-5, gamma .999, original clipped nonrecurrent PPO, five
epochs/four batches. Cold critic/optimizer; both parent normalizers and the
original V21 teacher remain frozen. Walking exploration starts at one quarter
of parent std with [.005,.15] bounds; standing has no exploration. Require at
least 3 GB free and a passing process guard immediately before launch.

The targeted reward change adds `3 * abs(actual_yaw_rate - requested_yaw_rate)
/ .20` to cost only while the walking actor is active on +3-degree downhill
cells. This is an instantaneous absolute error, never a signed average or a
heading-only proxy. All V46 posture, actual joint-margin, applied internal-load,
effort, tracking and stop costs remain. Retain original actions on current flat
walking inputs plus 512 replay rows per minibatch, each using .03-radian scaled
L2 loss with weight one. Release the online teacher anchor on slopes. Replay
uses every walking row from 63 passing flat windows, both whole passing
180-second compositions, and the five whole passing surface sessions; labels
are original stored float32 action tensors aligned to actual actor inputs.
Terrain labels affect reward/optimizer retention only, never the 61D actor or
critic input. This combined correction is not a causal ablation.

Twenty-four equally represented cells cross two flat command orders, downhill
+3 and uphill -3 degrees, delays (motor physics ticks, sensor controls)
(4,1)/(0,0)/(6,1), and initial yaw 0/.12 radians. Two environments per cell in
the full run; one per cell in smoke. Use V46 command ordering, expanded to ten
18-second windows and 180-second continuous episodes. Reset only at falls or
full timeouts, never at stops/restarts; preserve endogenous controller/FIFO
history. These fixed exposed cells are scoped training coverage, not broad
randomization or unseen-terrain evidence. Before learning, audit actual geometry,
delay values and two complete original-policy/action-insertion continuations
per cell, up to 180 seconds or terminal fall, with exact action/observation and
physical-state equality plus non-accumulating HOME resets.

Physics is unchanged contact-v11/native MuJoCo 3.12/BAM, raw 50-Hz actions,
200-Hz integration, 61D/14D ABI. Record every training input/output and yaw reward
component, full switch histories, actual coverage and finite learning telemetry.
Check normalized ONNX parity on random and every actual evaluation observation.

Freeze all evaluator sources and exposed banks before learning. Evaluate all
63 flat cases, both complete 180-second compositions, both original downhill
sessions and all 14 exposed surface sessions even if earlier gates fail. Keep
every task/gait/loaded-slip/joint/torque/posture/fall/non-foot-support/heading/
body-geometry/applied-200-Hz-internal-load/full-duration gate unchanged. Require
63/63 flat, 4/4 endurance (including both downhill), and no loss of the original
five surface passes before opening V44's separately frozen fresh sequence bank.
Fresh and protected terrain banks stay closed on any prerequisite failure.

Report the original and candidate 2–13-second downhill mean absolute yaw errors
and full-sequence results separately. A prefix improvement cannot admit a
failed stop or session. Missing evidence fails closed. Reward, export, process
exit zero, source integrity and cross-engine agreement are not physical success.
On rejection retain V30 and classify the earliest remaining failure before
recommending the next activity. V49's three privileged stopping witnesses are
reserved for subsequent state-conditioned braking work, not used here. No paid
compute, policy activation, publication, hardware, measurement-calibrated or
carpet-transfer claim is authorized by this experiment.
