# V51: revalidate and retarget recovery before braking learning

V50 retains the original passing banks but has downhill absolute yaw
.202639/.202257 above .20 and falls at its first stop. The three clean V49
stopping witnesses used V48 as their standing base, so they cannot be assumed
to survive transfer to V50 with V15 steady standing fixed.

Freeze this eligibility diagnostic before any transfer outcome. Reproduce both
complete V50 downhill traces, and capture complete states at control650/657
for start1 and650 for start2. Verify two exact25-control resets for each state.
For each state run four complete36-second continuations twice: unmodified V15;
old witness residual on V15; old witness residual on V48; old witness residual
on V48 for2.5s then V15. Reuse the exact five14D V49 residual knots, timing,
physics, action precision and evaluators. V48-continuous is a comparison only.
A transient V48 base is diagnostic assistance, not a trained deployable actor.

If no compatible comparison passes stopping checks, retarget once: three
states, two anchors (V15 or V48-for2.5s-then-V15), eight generations of24
candidates per anchor, elite6, initialstd.18rad/floor.02, residualbound1.5rad,
seed26090851 plus state index. Maximum1152 trajectories through the first
18-second window. Initialize mean and one candidate at the original witness;
include zero residual as a control. Use unchanged V49 proxy cost and half-step
CEM updates. Select one lowest-proxy candidate per state before validation,
then continue the complete36s session twice. No alternate chosen from scores.
If a compatible comparison passes, reuse it in the declared order V15 then
transient and skip its search. Preserve every search action/input and cost.

Demonstration eligibility is separate from walking/session acceptance: a full
first window must pass every original stop/posture/gait/joint/torque/slip/contact/
200Hz internal-load component, allowing only the already-exposed pre-braking
mean-absolute-yaw failure. Require all three eligible demonstrations with V15
steady standing before defining and freezing a learning run. Missing or failed
eligibility ends this activity with a negative receipt and a revised next step;
never train on failed recoveries or silently weaken the admission rule.
Even eligible demonstrations do not establish successive-stop generalization.
The .20 yaw threshold remains required for complete behavior acceptance.

No physical properties, V50 walker weights, steady V15 weights or original
acceptance thresholds change. No actor is trained in this diagnostic stage.
Keep V30 retained and all fresh/protected banks closed. No paid compute,
activation, external contact, hardware or calibrated/carpet-transfer claim.
Check3GB free and the process guard immediately before each compute launch.
