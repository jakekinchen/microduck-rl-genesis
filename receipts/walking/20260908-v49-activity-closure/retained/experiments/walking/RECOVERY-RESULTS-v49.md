# V49 completes the recovery diagnostic; retain V30

The bounded full-state recovery activity is complete. **The late V48 failure
is recoverable with original V15 standing, and three selected downhill branches
achieve a clean first stop. No downhill branch passes its full session.**
No policy was trained, promoted or activated; original V21/V15 with V30 remains
retained. This is exposed simulator diagnosis, not carpet or physical acceptance.

## Same-state actor comparisons

Twelve complete states cover two original downhill starts and their matched-flat
controls at 13.00/13.14 s, plus original/V48 late-composition states at
85.00/85.12 s. Compare original V15 and V48 standing from every state, retaining
original V21 walking, all actuator/sensor/controller history and the full
original 36-second or 180-second endpoint. Repeat every continuation exactly.

| Captured state family | Original V15 standing | V48 standing |
|---|---|---|
| Four matched-flat states | 4/4 complete sessions pass | 4/4 pass |
| Four original downhill states | 0/4; all fall at 13.82 s | 0/4; all fall at 13.82 s |
| Two original late-composition states | 2/2 finish 180 s and pass | Immediate stop/restart pass, then both fall at 139.92 s |
| Two V48 late-composition states | 2/2 finish 180 s and pass | Both reproduce the 86.28-s fall |

These are controlled state branches, not independent population trials. In the
two V48 late states, replacing standing with V15 is sufficient to avoid the
recorded failure and satisfy all remaining gates. V48 also fails later when
given original-controller late states. This identifies a standing-policy
regression in this exposed bank; it does not identify its internal mechanism.
Keep original V15 for steady standing and long-composition retention.

## Bounded downhill search

The two V48 late states are skipped under the frozen rule because an unmodified
comparison arm already passes. The four downhill states each receive eight
generations of 24 candidates per original/V48 anchor: **1,536 trajectories and
245,794 actual control steps**. The bound was 2,304 trajectories/576,000 controls.
There is no extension or parameter retuning.

Each candidate uses five optimized 14D timed residual knots and a fixed zero
at 2.5 s, around a frozen actor. Its raw outputs enter the original BAM and
delays unchanged. Incoming-action bridge candidates provide explicit search
initialization. The single lowest proxy-cost candidate per state is selected
before full-session scoring and continued twice through subsequent windows.
The optimizer costs do not replace acceptance gates. These time-indexed,
state-specific action sequences are privileged diagnostics, not deployable
general braking policies or unchanged-action physics comparisons.

| Downhill state | Selected anchor | First stop | Full-session outcome |
|---|---|---|---|
| Start 1, 13.00 s | V48 | Stopping/posture/contact checks pass | Second stop falls at 31.90 s |
| Start 1, 13.14 s | V48 | Stopping/posture/contact checks pass | Second stop falls at 31.84 s |
| Start 2, 13.00 s | V48 | Stopping/posture/contact checks pass | Second stop falls at 31.78 s |
| Start 2, 13.14 s | V15 | Survives; final face pitch fails | Second stop falls at 31.78 s |

All four first windows have zero measured geometric self-penetration and zero
200-Hz internal-load samples above 1 N. Their final two seconds satisfy the
original speed, yaw-rate and trunk-tilt limits. Three also satisfy the complete
posture checks; the fourth has mean absolute face pitch **30.68 degrees** against
the 30-degree limit. Final speed maxima range .00231–.00403 m/s and trunk-tilt
maxima 5.68–9.24 degrees. Joint/torque and loaded-contact checks pass in these
first windows. This establishes a limited clean stopping witness in three
captured states, not full-window or whole-session acceptance.

**Every first window still fails its original yaw-tracking gate.** The unchanged
walk before the intervention has mean absolute yaw rate **.24419/.24100 rad/s**
against the .20 limit. Those measurements cover 551 controls from 2–13 s, before
any searched action. The later stop cannot repair that historical violation.
Completing the window exposes this tracking failure separately from missing
stop evidence in the original early-fall evaluations. The second windows then
fail on falls, incomplete duration, support/contact/load and missing final
posture. No searched branch passes a full 36-second session.

An offline check of retained V46 and V48 downhill prefixes finds the same
problem (.241–.246 rad/s). Signed mean yaw rates are close to zero, so an average
signed-rate score would conceal the alternating error. For original V30, the
mean absolute policy yaw commands are only .0139/.0211 rad/s versus actual
.2442/.2410 rad/s; this supports investigating gait yaw oscillation rather than
assuming a large requested turn. It does not yet prove which physical or
controller component produces that oscillation. Raw measurements are retained
in the closure's `v49-prestop-audit.json`.

## Verification and preserved boundaries

All source sessions reproduce **18,296 controls** with byte-identical actions
and observations, exact poses and velocities. Twelve serialized full states
each reproduce two 25-control continuations: 600 exact reset controls. Paired
actor comparisons reproduce 34,068 continuation controls on their second run;
14,352 source-arm controls also match the historical episode suffix exactly.

The independent offline audit verifies every one of the 245,794 stored search
action/observation rows, all trial offsets, parameter bounds, finite costs,
generation/population counts and lowest-cost selection. Zero-residual fixtures
match 600 comparison controls byte-for-byte. All 986 selected search controls
match the corresponding full-validation prefixes exactly; the complete selected
continuations repeat another 3,751 controls exactly. No candidate is reselected
from validation results.

The source freeze binds 219 files and the three input receipt manifests. Native
MuJoCo 3.12, pinned BAM, contact-v11, 61D actor observations, 14D raw actions,
50-Hz control, 200-Hz physics, the V16 ramp and V30 heading control remain fixed.
Original window and session gates are reused, including body geometry and
actual applied internal loads. Full-state branch resets occur only at branch
start; all subsequent stop/restart state remains continuous. Composite scores
include the verified original prefix, identified separately from new suffix
evidence. Same-state repeats test reproducibility, not held-out generalization.

Capture, comparison and search take 24.75, 112.23 and 156.99 s respectively.
**140 workspace tests and two focused boundary tests pass.** Source/receipt
integrity verification completes successfully. All activity compute is finished.
The workspace reader verifies nested V49 branch reports against their complete,
manifested frozen parent before listing them as counterfactual or privileged
diagnostics, with no invented standalone policy score. Original receipt bytes
remain unchanged. The initial reader verification failure and corrected pass
are retained in the closure.
Fresh sequence and protected terrain banks remain unrun. No calibrated Ducky
physics, carpet transfer, library admission or hardware readiness is established.

## Next activity

First address **downhill yaw oscillation during walking**, which already fails
before braking. Freeze one walking-only correction from the retained original
walker with V15 standing and V30 control fixed. Target the existing absolute
yaw-error gate under the longest-delay downhill conditions; preserve bilateral
stepping, loaded slip, joint margin, body/load gates, all 63 flat cases, both
180-second compositions and the five original passing surfaces. Verify the
changed actor through full sequences; an improved prefix alone is not promotion.
Do not lower the yaw threshold or substitute signed-average heading success.

Retain the three clean V49 stopping witnesses as future braking demonstrations.
After the walking correction, develop and test a repeatable, state-conditioned
braking transition across successive stops and gait phases, with original V15
standing retained outside that transition. The current one-time searched action
sequences cannot supply that capability. Keep broad terrain expansion behind
the original downhill and retention gates.

## Evidence

- Frozen protocol: `experiments/walking/RECOVERY-FEASIBILITY-v49.md` and `recovery-v49.json`.
- Freeze SHA-256: `5ca76a040ec9239cd02ffa1fd5f264ed460c053c73e3de1b9fe5e0715b039443`.
- Capture: `receipts/walking/20260908-v49-recovery-capture`.
- Paired branches: `receipts/walking/20260908-v49-recovery-comparisons`.
- Search parameters, all trial actions/observations and selected continuations: `receipts/walking/20260908-v49-recovery-search`.
- Independent integrity audit and comparison table: `receipts/walking/20260908-v49-recovery-analysis`.
- Plots: `outputs/walking-recovery-v49-r2`; the first render remains retained with a superseded imprecise caption about full gates.
- Final review, current status, tests and prefix audit: `receipts/walking/20260908-v49-activity-closure`.
