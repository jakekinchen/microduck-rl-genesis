# Retained-controller runtime contract

The unmodified upstream runtime is useful for IPC integration but does not
implement the retained controller. Do not retune V21/V15 to compensate for its
startup ramp or import its current simulator as evidence for the local physics.

`command_adapter.py` supplies the small, isolated command component. It reuses
the exact existing CommandRamp and V30 heading implementations. It does **not**
implement robotd replacement, a socket body, a startup bypass or a new controller
claim. Its offline verification reconstructs six retained course recordings;
that is component evidence only.

## Boundary to implement next

Keep the official runtime checkout immutable. A separately versioned simulator
integration must explicitly select this contract and report that its control
adapter differs from stock robotd. The following are prerequisites to any
new physics run; they are not all implemented here.

1. **Startup is an episode boundary.** Load/hash-check both actors and warm
   inference before the first physics control interval. Initialize the single
   accepted HOME placement, BAM controller, motor FIFO, sensor FIFOs, command
   ramp and V30 heading state once. Obtain a finite timestamp-consistent sensor
   sample. First simulated actuator interval is the standing actor's raw output
   through the motor FIFO. There is no two-second HOME_RAMP, pose interpolation,
   actor-free settling or root-state write after activation. Initialization is
   explicitly excluded from behavior duration. Mid-episode reconnect must never
   reset a fallen body or teleport it back to HOME.

2. **Commands and actor selection.** At 50 Hz, ramp requested float32 twist by
   `[.75, .75, 2.5]` units/s using the existing float64 accumulator. Select V15
   only when all three resulting float32 components are exactly zero; otherwise
   select V21. Then apply V30 heading using the separate orientation FIFO.
   The ramp and heading state survive all walk/turn/stop transitions. A command
   lease timeout supplies a zero requested twist through this same path, never
   a reset or an immediate substituted motor pose. Record requested, routed and
   actor-facing commands separately.

3. **Observations and raw actions.** Preserve the ordered 61D float32 input:
   gyro, gravity, 14 joint-relative positions, 14 joint velocities, previous
   14 raw actor outputs, twist, four head commands and six body commands.
   Keep previous action shared across walking/standing. Preserve the normalized
   ONNX files byte-for-byte. No post-policy clipping, filtering, gain reduction,
   voltage scaling, IK or offsets: reference = exact HOME float64 + raw float32
   action widened to float64. An unexpected shape/dtype or nonfinite action
   fails the interval. No approximate fallback actor is allowed.

4. **BAM and contact physics.** Reuse the existing complete-contact-v11 physical
   arrays and pinned BAM `62bd8ce12154340be97e06f7f41a0ca8f116d967`. Every 20 ms
   control interval contains exactly four 5 ms updates: enqueue/sample the
   physics-rate target FIFO, set all BAM joint targets, run controller.update,
   capture applied torque/load, then mj_step. Nominal motor FIFO is four physics
   ticks; declared 30 ms case is six. Initial FIFO values are HOME. Static XML
   position gains cannot substitute for BAM. Keep contact masks, exclusions,
   armature and friction identical; read internal loads without changing dynamics.

5. **Sensor timing.** Sample current sensors with mj_copyData/mj_forward on a
   separate data object. For sensor_ticks=1, retain the declared one-control-tick
   history for gyro, projected gravity and joint velocity; position remains
   current. On the first interval use the first available sample. Heading has
   its own orientation history with the same declared delay. Do not introduce
   a second implicit pre-integration sensor delay or reset histories at a stop.

6. **Transport and time ownership.** Protocol 1 does not carry a control epoch,
   step index or sensor timestamp and cannot prove fixed-lag parity across
   independently paced processes. A new, explicit protocol must carry those
   identities. Exactly one body process owns physics advancement; a duplicate,
   missing or out-of-order interval fails instead of advancing twice. Keep
   lockstep conformance and wall-clock scheduling tests separate. A high real
   time factor does not prove correct motor/sensor phase.

## Required conformance tests before a new runtime walking claim

- **Already implemented:** six immutable course recordings, 19,800 intervals;
  compare requested→routed→actor-facing command float32 bytes, exact-zero actor
  choice and raw-action-derived target. Include both motor timing profiles and
  mirrored/initial-yaw conditions. Preserve negative malformed-action cases.
- **Already implemented:** unmodified upstream Rust ONNX inference against all
  3,300 nominal recorded observation/action rows, both retained actors.
- **Pending:** first-actuator-write witness showing actor invocation at interval
  zero; no startup ramp or post-activation root writes.
- **Pending:** paired direct/transport replay with identical input action bytes;
  verify every qpos/qvel, applied target, torque, contact/load and sensor buffer
  at every 5 ms tick. Include motor4/motor6 × sensor0/sensor1, boundary transitions,
  full reset replays, duplicate/drop/delay injections, and abrupt disconnect.
- **Pending:** compare Rust observation construction and the complete daemon
  command/actor scheduler, then a continuous closed-loop flat walk/turn/stop bank.
- **Pending:** real-time timing, full-duration component acceptance and the
  mandatory BEHAVIOR_VALIDATION matrix. Synthetic frames or parser tests cannot
  replace these.

Replacing real robotd control with a wrapper around TerrainWorld would exercise
the existing local controller, not the real daemon's controller. Label that
choice honestly; do not use it to claim the upstream integration now works.
