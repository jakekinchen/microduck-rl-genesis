# Public-data surface development: results, September 6, 2026

**V30 improves the tested simulated walking/turning/STOP compositions while
retaining all 63 original flat-floor gates. Broad carpet support is not achieved.**
Three motor-policy refinements completed, but none passed the surface matrix.
Public data supports scoped priors, not matched Ducky physical calibration.
All local runs are complete; failed experiments and the storage-interrupted
partial evaluation remain retained alongside the completed retry.

## Research and model scope

Collected and checked public carpet studies and the 30,709-row, 49-column
[ISRD dataset](https://zenodo.org/records/45874). Its engineered Sony ERS-7
features were excluded from Ducky policy training and material fitting.
Published carpet geometry, compression endpoints and friction retain their
source specimen, load, timescale and counterface limitations. Details and a
bibliographic identifier correction are in
[RESEARCH-NOTES.md](public-surfaces-v1/RESEARCH-NOTES.md).

The [shared-biped curriculum study](https://arxiv.org/abs/2504.13619)
supports testing staged exposure to different surfaces. Its robot and contact
parameters are not a Ducky calibration. V25/V27 preserve the 61D observation,
14D action, 50-Hz control, complete collision geometry and BAM interfaces.
They use explicit numerical contact hypotheses, with fixed panel geometry;
no ground movement, privileged terrain label in the actor or motor assistance.

The four training profiles are friction/time-constant pairs (1, .02 s),
(.51, .035 s), (1, .05 s), and (1.8, .07 s). The friction endpoints describe
different published contact pairs, not a measured Ducky distribution. The time
constants are exploratory, not inferred from static compression. Lowering sole
friction to .1 also changes sole-to-sole friction if the feet touch; other body
collider coefficients and every internal-load/interference gate remain intact.

## Completed training and surface comparison

Three 1,024-environment, 250-iteration runs each completed 6,144,000 new
transitions, following separate 64-by-5 smoke runs. Only FINAL 249 was evaluated;
no intermediate checkpoint was selected. Every logged scalar and final actor
parameter is finite, and all bound sources match their retained copies.

| Run | Change and initializer | Elapsed seconds | Bound sources |
|---|---|---:|---:|
| V25 walking | Four-surface curriculum from V21 FINAL | 838.93 | 176 |
| V25 standing | Same curriculum from V15 FINAL | 876.66 | 160 |
| V27 walking | Gradual three-surface curriculum from V21 FINAL; at least 50% rigid episodes | 791.88 | 181 |

The V27 strongest profile was excluded from training and retained in testing.
Its loaded robot/ground contact counts are 6,705,563 / 2,539,685 / 269,528 / 0.
These counters include all loaded robot/ground contacts, not just soles. Final
snapshots independently verify actual sole-contact friction and timing on all
three intended V27 surfaces. V25 walking's final snapshot lacks sole contacts
on its hardest profile despite earlier robot/ground exposure; that limitation
is retained. V25 standing's final snapshot includes soles on all four.

The same exposed bank contains seven profiles, two starts per profile and two
continuous 18-second windows per start. Three parameter combinations were absent
from training; all are now exposed development, not untouched final validation.
Each window retains task, bilateral stepping, loaded slip, torque/joint, posture,
non-foot support, body-interference and internal-load gates. Whole-session
heading is additional. Every required session must pass; lower fall count alone
is insufficient. All evaluations completed, including explicit missing windows.

| Fixed pair, all using V24 heading | Sessions passed | Windows passed | Sessions falling | Windows unrun after a fall |
|---|---:|---:|---:|---:|
| Original V21 walker + V15 stander | 5/14 | 13/28 | 4 | 4 |
| V25 walker + original stander | 1/14 | 10/28 | 3 | 2 |
| Original walker + V25 stander (V26 isolation) | 5/14 | 13/28 | 5 | 4 |
| V25 walker + V25 stander | 4/14 | 10/28 | 3 | 3 |
| V27 walker + original stander | 5/14 | 11/28 | 2 | 2 |

All new motor policies are rejected for promotion. V27 restores both rigid
controls and reduces falls, but retains yaw/slip failures and adds no fully
passing surface bucket. The isolated new stander provides no overall gain;
therefore a V27/new-stander pair was not selected for another comparison.
These are single-seed development experiments, not statistical reliability
estimates or evidence that a real carpet will cause the same failure.

## Verified heading improvement and retained regressions

V30 uses the original V21 walking and V15 standing actors, establishes the
course at first motion, and preserves it through subsequent exact-zero STOP.
Its explicit correction headroom permits policy yaw commands up to .80 rad/s;
the requested command limit stays .75, with unchanged gains and filtering.
This is up to .05 rad/s of actor-command extrapolation beyond training, not
raw-policy learning or physical transfer. No motor actions are filtered or
assisted, and no physics or acceptance threshold changes.

| Controller version | Original flat | Repeated flat | Three-minute compositions |
|---|---:|---:|---:|
| Retained V21/V19 baseline | 21/21 | 42/42 | 0/2 under whole-session audit |
| V24: course held from reset | 21/21 | 41/42 | 2/2 |
| V28: course established at first motion | 21/21 | 41/42 | 2/2 |
| V29: extra headroom, unintended arithmetic change | 21/21 | 42/42 | 1/2; one falls |
| **V30: headroom with original float32 arithmetic** | **21/21** | **42/42** | **2/2** |

For V30's two 180-second compositions, endpoint heading error falls from
64.04/86.44 degrees to **6.24/8.95 degrees**; maximum errors are 15.88/14.45
against the unchanged 20-degree limit. Both whole sessions and all 20 windows
pass. Both downhill sessions still fall. V30 is a limited development
improvement, not full locomotion or physical admission.

![Recorded V30 course comparison](/Users/kelly/Developer/microduck-rl-genesis/receipts/walking/20260906-v25-verification/heading-persistence-v30.png)

The final original-motor-pair/V30 surface comparison remains **5/14 sessions,
12/28 windows, five falls and four unrun windows**. No new surface bucket fully
passes. Its results are separate from the five V24-controller comparisons above.

The regression sequence is preserved because it explains the final design.
V24's first near-limit left turn ends 18.182 degrees short. V28 restores all
21 original first-window action files exactly, but its second turn ends 15.887
degrees short. The controller saturates at .75 rad/s for all 550 scored samples,
while actual yaw averages .717536 against a .738 request. V29 adds headroom,
but also changes float32 rounding even below saturation, causing an endurance
fall with body-interference evidence. V30 restores the original rounding order.
A 1,000-step nonsaturating equivalence test passes; all 24 V28/V30 diagnostic
action files and 19,382 recorded qpos/action rows match exactly, including the
failed downhill runs. This is an implementation correction, not a gain search.

[Full V30 three-minute recorded simulation](../../receipts/walking/20260906-v25-verification/videos/v30-continuous-composition-start-1.mp4)
and [rejected V27 moderate-surface session](../../receipts/walking/20260906-v25-verification/videos/rejected-v27-soft-middle-start-1.mp4)
are visualizations of retained poses at original speed. Their sidecars bind
source trajectory, model, renderer and video hashes. They do not run another
policy, repair motion or replace the frozen evaluator results.

## Numerical physics verification

Native passive contact settling and half-timestep checks pass 24/24 cases.
Genesis/MuJoCo passive cuboid comparisons pass 8/8, with maximum indentation
error about 8.3 nanometres for this simple probe. Neither result establishes
material calibration. Changing probe mass from .2 to .737243 kg barely changes
indentation: the normalized soft-contact model does not reproduce an identified
load-dependent carpet constitutive response.

Robot-level replay completes all five predeclared initial-standing prefixes:
211 identical float32 action vectors, 844 physics steps, and every final-substep
delayed target agrees within its 2e-7-radian numeric check. Two of five pass the
frozen base-position/joint-discrepancy limits (2 mm / 5 degrees).

| Prefix | Maximum base error, mm | Maximum joint error, degrees | Numerical comparison |
|---|---:|---:|---|
| Original stander, rigid | 2.374 | 1.820 | Fail |
| Original stander, mild | 1.082 | .913 | Pass |
| Original stander, moderate | 1.129 | 1.064 | Pass |
| Original stander, strongest | 4.073 | .586 | Fail |
| V25 stander, strongest | 4.087 | 1.316 | Fail |

The strongest original prefix reproduces low base height in both lanes by
.22 seconds (native .06968 m, Genesis .06607 m), but already exceeds the
comparison tolerance at .12 seconds. These initial-standing prefixes are not
new closed-loop gait passes. The native plane and Genesis fixed panels differ
in contact representation despite equal local top height. Diagnose those
representations, contact timing and applied dynamics before attributing the
mismatch only to a solver or spending more training on that discrepancy.

No retrieved dataset supplies matched Ducky soles and representative carpet/
underlay loading, unloading and drag responses at gait rates with independent
validation trials. Public inputs were not inserted as fictitious entries in
Ducky's physical-calibration intake. User measurements were not requested.
Loose rugs, snagging, underlay hysteresis and physical thermal/battery endurance
remain outside this numerical bank.

## Evidence and reproduction

Sources, candidate checkpoints, source hashes, real observations, action arrays,
physics-rate internal loads, failed windows and evaluator results are retained
under `receipts/walking/20260906-v24-*`, `20260906-v25-*`, `20260906-v26-*`
through `20260906-v30-*`. Retained manifests bind each completed run. Setup failures
before learning remain separate receipts and do not count as successful trials.

Fresh output directories are required. Completed training is not repeated by
these commands; each runner verifies its frozen sources and exact FINAL:

```sh
./scripts/duck-ops guard && .venv-apple/bin/python scripts/evaluate_public_curriculum_v27.py --bank surface --candidate walking --output receipts/walking/NEW-v27-comparison
./scripts/duck-ops guard && .venv-apple/bin/python scripts/evaluate_heading_headroom_flat_v30.py --run-id walking-20260906-v21 --fresh --output receipts/walking/NEW-heading-regression
./scripts/duck-ops guard && .venv-apple/bin/python scripts/probe_public_surface_action_replay_v1.py --output receipts/walking/NEW-action-replay
```

132 workspace tests and 13 focused controller/contact/reset tests pass.
Actual-observation ONNX/Torch error is at most 1.79e-6 rad in the final surface
comparison, below the unchanged 1e-4 limit. Behavioral acceptance is separate.

One V30 repeated evaluation stopped on `ENOSPC` after 32 completed windows.
Its partial trace, source snapshot, printed results and manifest remain intact.
The unchanged retry completes 42/42 and reproduces all 32 prior action files
byte for byte; it is not counted as another independent trial. The storage
audit found 17.43 GiB free after the write failure. Closing internal free space is 13.72 GiB. No user files, caches or
checkpoints were deleted or offloaded.

Next local work should isolate the robot-level contact discrepancy using
matched support representations and fixed actions, then repair slope/soft-
surface standing transitions. More broad randomization alone is not supported
by these results. Keep one shared locomotion capability with per-surface,
transition and endurance gates; specialists require a demonstrated tradeoff. The ordered remaining work
is in `TRAINING_ACTUALIZATION.md`; this report does not authorize activation.
