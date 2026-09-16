# V25 public-data-informed surface development

User authorizes local research, implementation, training and evaluation without
supplying measurements. No hardware, paid compute or physical acceptance.
Public source extraction and its exclusions: `public-surfaces-v1/evidence.json`.

## Frozen intervention

Keep V21 walking and V15 standing architecture, BAM, complete body model,
persistent timing, commands and rewards. Warm-start each actor separately.
Change the training distribution only: four static, level 16-m panels with
effective contact (friction, time constant) pairs (1,.02), (.51,.035), (1,.05),
(1.8,.07). Foot friction becomes .1 to allow the surface to determine the
pair maximum; other body contacts retain the original coefficient. Ground
time constants compensate for equal pair averaging with the .02-s foot.
Check actual imported parameters and loaded panel identities. No moving terrain,
force assistance, randomization while loaded or post-policy action filtering.

Compliance constants are preregistered *exploratory hypotheses*, not identified
from the published 30-second carpet tests. Friction endpoints come from different
published counterfaces. Physical fit/admission remains false. Flat panel tops
isolate contact response; pile texture, hysteresis, snagging and carpet-edge
geometry are not represented by the training panels.

First 2000 control steps sample equal rigid/mild panels; subsequent resets
sample all four evenly. Inherited random translation/yaw and timing remain.
Panels do not change between steps or episodes. Leaving the 7.5-m usable radius
ends an episode. Count actual loaded contacts by panel, not just sampled IDs.

For each actor: seed26090625, 64x5 smoke, then at most 1024x250 PPO iterations,
LR2e-4, 24-step rollouts (6,144,000 new transitions). Exact final iteration249,
no best-intermediate selection. Warm-start optimizer disabled. Smoke is pipeline
evidence. Two long runs maximum in this version, sequential local compute.

## Evaluation and decision

`public-surfaces-v25.json` freezes visible development: four exact contact
profiles and three withheld parameter combinations, two independent starts
each, repeated forward/turn/stop windows. These are unfamiliar *proxy contact
combinations*, not unseen physical specimens. Withheld combinations never enter
training; this is an exposed final-development bank, not the protected library
acceptance bank. Record baseline before candidate evaluation.

Use V24 persistent reference, V16 ramp, fixed motor/sensor delays and exact
normalized ONNX actors. No controller selection per material. All V23 task,
posture, bilateral step/slip, torque/joint, non-foot support, internal-load and
body interference gates apply. Whole-session heading 15/20 degrees. Every case
must pass; no replacement of early falls by new seeds. Audit complete durations
and actual contact-pair parameters. The rigid control must not regress.

Run passive contact settling and half-timestep checks before PPO. Require all
four training panels to receive actual load. Cross-engine material-response
and policy tests are separate evidence. A negative is retained and cannot be
presented as carpet readiness. If all proxy gates pass, run original walking
and terrain/endurance regressions before any broader capability claim.
