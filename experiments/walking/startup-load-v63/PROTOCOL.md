# V63 local startup, passive settling and retained-action replay

The machine-readable `bank.json` was frozen before any V63 physics. It binds
247 inputs, two model variants, twelve independent cases, thresholds, stop rules
and all controller/source parameters. Every child has a 240-second deadline
under the existing process-group coordinator. Control runs are evaluated before
candidate launch. No new training, daemon, hardware or paid instance is involved.

| Mode | Duration | Control | Interpretation |
|---|---:|---|---|
| HOME hold | 5 s | BAM target equals declared HOME from the first physics step; no ramp or balancing actor | Tests a fixed joint-pose startup assumption; does not test the standing policy. |
| Passive | 5 s | Exactly zero electrical motor torque, with pinned BAM mechanical friction and rotor inertia | Falling is allowed; the final second must settle. This is an explicit unbraked model, not calibrated powered-off hardware. |
| Replay | 18 s | Original 900×14 float32 action array; HOME plus unmodified actions; four-tick motor FIFO | Includes original stand 0–1 s, forward motion 1–13 s and stop 13–18 s. No actor adapts to the new model. |

V11 and V62 each receive two freshly initialized executions per mode. The replay
start yaw is −0.8 radians; other starts have yaw zero. Root height is .125 m,
all velocities start at zero, and the declared HOME fills the target FIFO.
Every case compiles a new model, instantiates a new BAM model/controller and
creates a new MjData. Exact hashes compare repeat initial arrays and complete
qpos/qvel/target/torque/friction/load histories. Timing is excluded from state
repeatability. Two deterministic executions are a reset/repeatability check,
not evidence of a diverse start population.

## Controls and admission

The V11 replay must reproduce every retained qpos, qvel and final applied target
at 50 Hz and all four torque vectors per interval at 200 Hz within 1e-10.
Original action-file bytes are retained; matching parsed JSON values is only
an additional consistency check. Both control repeats must pass this conformance
gate before V62 launch. Control HOME failures do not erase retained actor scores.
Each V62 mode is an independent diagnostic, so an ordinary HOME fall does not
suppress a separately initialized replay. Missing or interrupted evidence cannot
pass. No result here admits a model, a walking behavior or a physical capability.

The two models share the same floor template and runtime BAM setup. V62's exact
62-array geometry check is against V57 full CAD, not V11. The baseline/candidate
comparison therefore includes their existing physical-export differences; it
must not be described as an isolated collision-only intervention.

## Measurements and thresholds

Every 5 ms step records applied contact forces with `mj_contactForce` after
`mj_step`, plus contact identities, penetration, qpos before/after, qvel, all
motor torques, actuator forces, actual joint margins, damping and friction.
No extra `mj_forward` is run on physical data. Contact frames refer to the solver
state for the recorded integration interval; loaded slip uses its contact
Jacobian with post-integration velocity and is explicitly a discrete diagnostic.
The two sole IDs are mapped by exact geometry name separately for each model;
foot shells and other floor-contacting shapes remain visible as nonsole support.

Active probes retain the existing 1 N internal-load limit, at most 1% loaded
samples and 50 ms continuous loading. Internal penetration must stay ≤1 mm,
nonsole support ≤.1 N, motor torque ≤.6405236195572268 Nm and actual joint margin
≥.02 radians. HOME also requires tilt ≤15° and drift ≤5 cm after one second.
A fall is root height <7 cm or tilt >70° and terminates an active case immediately.
The passive final second requires root speed ≤.02 m/s and angular speed ≤.2 rad/s;
its resting contact loads and falls are reported separately, without claiming
upright bracing acceptance. All modes require joint overshoot ≤.02 radians,
floor penetration ≤3 mm, finite ordered evidence and no MuJoCo warnings.
These are development diagnostics, not measured physical tolerances.

Hard stops include any MuJoCo warning, nonfinite state, penetration over1 cm or
root speed over5 m/s. Buffered traces preserve completed samples on exceptions;
a deadline or missing tail remains incomplete. No automatic reset or rescue is
allowed after a failure.

Instrumented control timing includes BAM updates, physics and contact/state
observation but excludes file encoding. The provisional 50 Hz budget requires
full duration, control p99 ≤20 ms and ≤1% deadline misses. Raw physics timing is
reported separately. This is serial local throughput, not real-time daemon or
hardware scheduling evidence. Longer terrain, endurance and calibrated-physics
acceptance remain outside this exposed diagnostic bank.
