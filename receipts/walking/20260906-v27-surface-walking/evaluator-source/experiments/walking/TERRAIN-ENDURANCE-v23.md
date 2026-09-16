# V23: frozen V21/V15 pair on new terrain and longer sessions

Preregister before inspecting any V23 candidate rollout. Candidate: walking
FINAL249 SHA `7b5e166c13a8086fdd21b5ad237a0e69aa75828ad6f8fb5536f3ea057535a322`,
V15 standing FINAL, V16 command ramp, V19 filtered heading. No training,
controller change, post-policy filter or protected-bank access.

`terrain-endurance-v23.json` is the numerical authority. Seven terrain buckets,
two independent worlds with specified initial headings, two continuous 18-second
windows each: 28 windows / 14 sessions. Flat control, uphill/downhill/cross-slope
3 degrees, 3-mm narrow seams, 2/4/6-mm uneven tiles, and a new uneven layout
combined with .6 sliding friction and 1.1 body mass/inertia. These are new
environment families relative to the flat V21 training, with exploratory bounds.
They become exposed development evidence; they are not a protected final bank.

Endurance: six independent 180-second sessions. Two nominal sustained forward
walks, two sustained walks at combined .6 friction / 1.1 mass+inertia, and two
10-window walking/turning/stopping compositions. Sustained commands run 1..175 s;
the final five seconds command STOP. No state, sensor FIFO, action history,
heading controller or physics reset within a session. Two initial headings per
bucket are a deterministic bounded probe, not a statistical reliability claim.

Use original numerical task, gait, posture, heading, joint, torque, internal-load
and self-interference limits. Foot clearance uses compiled ground geometry;
boxes conservatively bound the sole footprint so a seam between mesh vertices
cannot inflate stepping clearance. All static terrain colliders count as ground
for slip/non-foot support. The .07-m base fall floor becomes ground-relative;
the world-vertical 70-degree tilt limit is unchanged. Record actual friction,
ground poses/sizes/masks, model/source hashes and contacts. Require at least ten
loaded raised-surface samples for seam/tile sessions; absence is failed exposure.

Full-horizon heading keeps 15-degree endpoint / 20-degree maximum limits.
Sustained walks additionally face the same velocity-error limits in every
30-second bucket, including the final shorter bucket. Score final standing head
posture separately. All windows and all component gates must pass; a partial
trial or a later window after a fall remains a failure. Windows in one session
are correlated and never counted as independent repetitions.

Retain original float32 actions, 50-Hz observations/trajectories, 200-Hz applied
internal loads/torques, all videos at actual speed and negative results. Compile
and probe terrain before freezing: robot-array equality, mask application,
ray/height consistency, narrow-seam clearance, reproducible materialization and
isolated models. No outcome-based adjustment of thresholds or selection.

These tests do not model actual battery depletion, temperature or wear. They
cannot establish physical endurance or calibration. Measurement acquisition,
held-out calibration residuals, broader randomized learning, disturbances,
dropout, protected final validation and terrain cross-engine/timestep sensitivity
remain distinct gates. MuJoCo primitive geometry semantics are documented at
https://mujoco.readthedocs.io/en/stable/XMLreference.html#body-geom .
