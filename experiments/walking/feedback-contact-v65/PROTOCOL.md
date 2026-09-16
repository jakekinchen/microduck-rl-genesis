# V65: force-input age and an isolated sole impact

This exposed, local diagnostic continues V64. It cannot admit a walking policy,
establish calibrated physics, or demonstrate carpet transfer. Historical scores
and closed V62–V64 artifacts stay unchanged. No training or hardware is involved.

## Feedback experiment

Use the exact retained 900 by 14 float32 action array, original 50 Hz commands,
200 Hz BAM updates, four-tick (20 ms) motor FIFO, reset and fall/hard-stop rules.
Geometry, contact parameters, integrator and all V64 diagnostic thresholds stay
fixed. Fresh model, MjData and BAM controller for every run. Two repeats per case.

Native feedback reads the preceding solver interval's force fields. Fixed-age
feedback instead reads the saved fields whose solver interval began exactly
5 ms before the current BAM update. Current qpos/qvel and controller time are
unchanged. Both use reset mj_forward fields at time zero. Capture all six actual
force/constraint arrays after every mj_step, tagged with interval start/end and
integer step; no interpolation, extra physical mj_forward, or physical-force
array overwrite. Record every BAM field access, selected snapshot, generalized
forces, friction subtraction and output, and assert that physical solver arrays
and qpos/qvel/time survive the controller call unchanged.

MuJoCo's documented pipeline computes forward dynamics before integrating state:
https://mujoco.readthedocs.io/en/stable/programming/simulation.html#forward-dynamics
The timestamp interpretation follows that pipeline and the pinned Euler/BAM
sources. This is solver-field age, not a newly measured hardware sensor latency.

Execution order, with completed JSON prerequisites checked in the launch shell:

1. Eight 5 ms controls: V11/V62, native/fixed-age, two repeats. All initial/dynamic
   arrays must exactly reproduce the corresponding V64 replay before proceeding.
2. Eight native 2.5/1.25 ms cases. Every initial/dynamic array must exactly
   reproduce V64. This verifies instrumentation at the changed integration rates.
3. Eight fixed-age 2.5/1.25 ms cases. Compare to those verified native runs.

Require exact repeats, actions, FIFO, BAM/output holds and force selections;
missing/failed controls block dependent phases. Exit zero is completion only.
Every physics job runs serially under the existing bounded V59 coordinator after
`duck-ops guard`; no shared guard-source changes. Each child has a 240 s deadline.

Preregistered numerical screen on the two finest integration steps, separately
for each model and feedback rule: root position maximum difference <=1 mm,
joint maximum difference <=1 degree on the common 2.5 ms grid, common-prefix
floor-penetration peak difference <=0.5 mm, internal-penetration peak difference
<=0.25 mm, same terminal reason and terminal times within 20 ms. Require complete
physics evidence through each declared stop. Report full-prefix peaks separately.
Passing this screen alone would still not admit a behavior. Report native/fixed
trajectory differences and terminal times without selecting a favorable seed,
changing thresholds, or assuming that one isolated negative eliminates interactions.

## Contact experiment

Freeze its own bank before any drop integration. Extract the original sole assets
and V11 ankle inertial data. For each foot, align both mesh versions using the
same V11 HOME body/feature frame, mass and inertia. A vertical guide constrains
rotation and horizontal motion; gravity drops the isolated CAD ankle load from
5 mm sole clearance for 1 s. No BAM, electrical torque, body shells or robot
balance controller. This is a numerical bench, not an articulated robot or a
measurement of sole compliance. Keep original contact softness/friction and
solver options; do not tune them to obtain a pass.

Use V11/V62 sole assets, left/right feet, integration 5/2.5/1.25/0.625 ms and two
repeats (32 cases). Before integration, verify compiled sole support against the
source CAD, common reference mass/inertia/pose/contact options, zero actuation,
one vertical DOF and the prescribed clearance. Failed static controls block drops.
Record every solver contact force and interval, pre/post position/velocity,
constraint generalized force, solver warnings and momentum balance. Separate
force sums from different engines are not involved here.

Bench screens: complete finite 1 s trace, no warnings, peak penetration <=3 mm,
final 0.2 s speed <=0.02 m/s, impulse/momentum residual <=1e-8 N s and <=1e-7 m
initial CAD/compiled support discrepancy. Numerical agreement on 1.25/0.625 ms:
position <=0.1 mm on the common grid, peak penetration difference <=0.1 mm,
total normal impulse difference <=2% of m*g*T, first loaded impact time within
1.25 ms. Also report the preceding 2.5/1.25 ms comparison and cross-asset results.
No robot numerical reference or policy change follows a bench result alone.

## Decision

Conclude whether force-input age materially changes the replay, whether its
fine-step numerical screen closes, and whether the simple matched contact bench
agrees. Preserve all negatives. If full-robot numerical agreement remains open,
choose the next narrowly isolated numerical/actuator check before runtime policy
handoff; do not keep training against unresolved timestep sensitivity.
