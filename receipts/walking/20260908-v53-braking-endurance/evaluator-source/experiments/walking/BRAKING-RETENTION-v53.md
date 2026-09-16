# V53: retain successful stops while correcting learner-visited states

V52 is rejected: 38/63 flat cases, 0/2 endurance sessions and 3/14 surfaces.
Its first nominal braking action has 0.019819 rad maximum error on an exact
zero-label training example. Diagnose worst zero-label errors before fitting.
This is one local, supervised data/loss intervention with fixed V50/V15 base
actors, V30 controller, contact-v11 physics and the V52 125-tick event router.
No new PPO transitions, terrain switches, action clipping or activation.

## Collection, fixed before branch inspection

Reproduce three V52 flat cases byte-exactly: nominal forward-08, nominal
forward-12 and zero-lag arc-left. Capture full physics/BAM, delay, command-ramp,
heading and braking-event state at controls 655, 670 and 690 (13.10, 13.40 and
13.80 s). Nine states maximum, no search or adaptive state selection. Repeat
each continuation twice: unchanged V52, and original V50/V15 with no braking
residual. Evaluate complete 18-second windows, including immutable prefixes,
with the same motor/posture, heading, geometry and 200-Hz internal-load gates.
Only a complete all-gate passing original-actor continuation can supply new
zero labels; failed branches remain explicit negative evidence. Retain every
state, action/observation tensor and full continuation. No physical resets
within a continuation. Reproduction must include original float32 action and
observation bytes, qpos and qvel, and the exact braking age/active flags.

The learner data retain the 11,625 V52 zero-label rows. Replace the 375 mixed
V51 search demonstrations with the 500 actual V52 braking rows from all four
successful downhill stop events; those four windows fail only their existing
yaw gates. This preserves a demonstrated state-conditioned controller, not
privileged timed knots. Add zero labels from admitted new branches while the
original event is active (through control 775). Missing recovery labels are
not filled with zeros. Require at least one new admitted branch before learning.
All data are exposed. No protected/fresh acceptance bank is opened.

## One learner and decision

Keep V52's 61-64-64-14 ELU architecture and exact normalization tensors.
Initialize from V52 FINAL. One 8,000-update Adam run, seed 26090853, learning
rate 1e-4 and gradient norm 1. Each update uses 128 positive examples, 128
random zero-label examples, and the 128 worst zero-label examples by maximum
absolute output (refresh that pool every 50 updates, stable index tie-break).
Loss: .03-rad-scaled positive MSE + 8 times zero-label MSE + 8 times the mean
per-row maximum squared zero-label error. No runtime clamping or gating change.
FINAL only, no checkpoint selection, extension, or second learner. Retain every
loss and every hard-example pool. Report exact-input fitting errors separately
from closed-loop behavior. Verify normalized ONNX parity on all dataset inputs
and 1,000 fixed random inputs below 1e-4 rad.

Freeze versioned evaluators before learning. Run all 21 flat cases, 42 repeated
windows, two 36-second downhill sessions, two 180-second compositions and 14
surface sessions regardless of a failed earlier bank. Require all original
gates; keep the .20 absolute-yaw threshold and successive-stop checks unchanged.
Regressions reject the candidate. Original V21/V15 with V30 remains retained
unless all required admission gates pass; exposed improvements do not establish
unseen-environment, calibrated physical accuracy or carpet transfer. Preserve
all negatives and choose the next task from the earliest remaining failure.

Maximum collection: nine states, 36 continuations, no candidate search.
Minimum available local disk before compute: 3 GB. Guard each physics/training
launch. No paid compute, publication or hardware operation.
