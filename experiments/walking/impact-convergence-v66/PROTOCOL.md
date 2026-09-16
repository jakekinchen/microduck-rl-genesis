# V66: finer guided impacts with fixed phase coverage

This exposed numerical diagnostic follows V65. It changes only integration step
and a preregistered initial free-fall phase. It uses the four immutable V65 guided
sole/ankle models, with the same mass, inertia, solver, contact softness, friction,
vertical constraint and 5 mm reference clearance. No BAM, policy, whole-body
support, physical calibration or terrain acceptance is involved.

## Frozen cases and sequence

Four models (V11/V62 by left/right), three integration steps (0.625, 0.3125,
0.15625 ms), four start advances and two exact repeats: **96 one-second cases**.
Start advances are 0, 5/16, 10/16 and 15/16 of 0.625 ms: 0, 0.1953125,
0.390625 and 0.5859375 ms. Each starts at q0 = -g*tau^2/2, v0 = -g*tau,
on the same analytic free-fall trajectory. This preserves initial mechanical
energy and continuous impact velocity. At the finest step these cover all four
quarter-step phases; the coarser steps also receive four distinct phases.
All three rates in a bucket get exactly the same physical initial state.

First run the eight zero-advance 0.625 ms controls. Require byte-identical dynamic
arrays and equal physics rows against the V65 counterparts, plus exact repeats,
before the other 88 cases. Check completed prerequisite JSON and the compute
guard in the same launch shell. Use the existing V59 bounded serial coordinator,
60 s per child, fresh model and MjData per case. Hash source and inputs before
every case. Preserve failed cases; do not retry a changed recipe under its ID.

## Physical-rate evidence and analytic audit

Read actual contact forces after every Euler step without another physical
forward call. Keep the V65 contact, state, impulse and zero-actuation telemetry.
Record the applied initial advance and actual compiled clearance and validate
model arrays/options against V65. Use continuous and discrete free-fall formulas
to audit the first loaded solver interval and its incoming velocity.

Before loaded contact, the exact semi-implicit Euler sequence is
q_n = q0 + n*dt*v0 - g*dt^2*n*(n+1)/2 and v_n = v0 - g*n*dt.
Require position/velocity residuals <=1e-10 in SI units and the first loaded step
to equal the first predicted nonpositive sole clearance. Report signed onset
error relative to sqrt(2*H/g)-tau and incoming velocity error relative to
-sqrt(2*g*H). Bound them by one integration step and g*dt respectively (plus
1e-9 numerical tolerance). H is the original actual compiled clearance, not a
new measurement of physical material compliance.

The inherited diagnostic requires a complete finite one-second trace, no warnings,
penetration <=3 mm, final 0.2 s speed <=0.02 m/s and momentum residual <=1e-8 N s.
An independent checker reconstructs each Euler velocity/position update from the
recorded forces, including nonzero initial momentum; missing samples are failures.

## Decision rules frozen before outcomes

For each of 16 model/phase buckets, compare 0.3125 vs 0.15625 ms on their common
grid. Keep V65 limits: position difference <=0.1 mm, peak penetration difference
<=0.1 mm, total normal impulse difference <=2% of m*g*T and first loaded impact
time difference <=1.25 ms. Require both repeats, all case diagnostics and analytic
audits. **Every bucket must pass** to accept the 0.15625 ms step as a candidate
reference for this guided bench only. Also report 0.625/0.3125 ms comparisons and
all matched cross-asset comparisons; do not average away failures or select a
favorable phase. No posthoc shift or resampling of the primary time axis.

A passing bench authorizes the next planned short full-robot impact investigation,
not standing-policy admission. That investigation needs its own freeze, complete
solver/BAM/FIFO snapshots and controlled clocks. If any bucket fails, preserve
the negative and inspect the first discrepancy before another intervention.
