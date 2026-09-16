# Runtime rehearsal v1 — September 15, 2026

**The pinned official daemons build on this Apple Silicon Mac, and their Rust
ONNX inference preserves our retained actors' output bytes. The unmodified
daemon/body combination does not complete the startup rehearsal.** It falls
during the daemon's two-second HOME ramp, before a walking or turning command.
This does not establish a failure of V15 under the retained physics.

| Check | Actual result | Boundary |
|---|---|---|
| Locked two-job Rust build | robotd, robotctl, tofd and policy-rehearsal built | macOS arm64 compatibility; no container/systemd test |
| Source identity | 355 runtime and 239 RL files match pinned Git blob IDs | Seven non-build runtime symlinks intentionally omitted |
| Rust ONNX output | 3,300/3,300 nominal recorded rows bit-identical: V21 3,005, V15 295 | Actor inference only, not observation-builder/daemon parity |
| Inference timing | Max 0.1365 ms walking; 0.0551 ms standing; no sample >20 ms | Local cached inference only; no I/O or hardware claim |
| Local daemon startup | Both retained files load; control loop answers health; all 12 command/enable RPC replies accepted | Startup health initially reports no completed cycle, then healthy |
| Continuous stand→walk→turn→stop | **0/4 phases complete**; fall at 0.903904 s | Terminal negative, not an accepted behavior |
| Fall witness | Trunk height 0.07936 m; tilt 70.22444° exceeds 70° | Still within the two-second HOME_RAMP; no actor-driven walking occurred |
| Body pacing | 0.9 simulated seconds /0.903904 wall seconds =0.995681× | Short diagnostic only; daemon achieved_hz remained unavailable |
| Cleanup | All three owned child processes reaped; TCP listener gone | No other process/service was terminated |
| New command adapter | 19,800/19,800 recorded intervals exactly reconstruct routed twist, actor-facing twist, mode and HOME+action target | Six existing course cases; no new physics or closed-loop acceptance |

Frozen protocol: [PROTOCOL.md](PROTOCOL.md). Compact receipts:
[offline actor result](offline-result.json),
[upstream diagnostic result](upstream-diagnostic-result.json),
[command adapter result](adapter-result.json), and [closure manifest](closure.json).
Raw logs, samples, acknowledged calls, source archives and build artifacts remain
under `.workspace/runtime-rehearsal-v1/` (about 1.3 GB).

## What differs from the retained stack

Runtime pin is
[`fead66bb21195971fcbb2858a19b1e290a9f2031`](https://github.com/pollen-robotics/microduck/tree/fead66bb21195971fcbb2858a19b1e290a9f2031);
RL/body pin is
[`cb70b792312d559a4da09064d92009079671815f`](https://github.com/pollen-robotics/microduck_rl/tree/cb70b792312d559a4da09064d92009079671815f).

- The normal runtime's head/leg output filters default to 0.5/0.7, walking
  action scale to 0.9, standing gain ratio to 0.8, and voltage adaptation on.
  The diagnostic explicitly uses filters off, both scales one, ratio one and
  voltage adaptation off. These are isolated simulator params, not a hardware
  configuration change.
- Runtime actor selection uses twist magnitude <=0.05 for standing; retained
  V30 selects standing at exact zero after its command ramp. Applying the
  upstream threshold to recorded routed commands changes the actor at three
  intervals per course case (18 across six cases). This is one isolated routing
  difference, not a replay of the complete upstream scheduler.
- The runtime's startup `robot.enable` acknowledgement says "driving", but
  its log and executable state machine enter a two-second HOME_RAMP before the
  policy drives. `scripts/duck-sim` commentary describing immediate policy
  handoff is stale for this binary. The failure is inside this ramp.
- The official body server defaults to `scene.xml`, which includes
  `robot_groundcontact.xml`. `robot_allcollisions.xml` is used for extra ducks.
  A "full collision" claim for the separate VelStand training task does not
  establish this runtime default's contact coverage.
- The body server runs static XML position actuators (`chosen_actuator`: kp
  0.55, kv 0, force ±0.96; joint damping 0.053, frictionloss 0.0048, armature
  0.0018). It neither imports nor updates the local dynamic BAM controller and
  does not implement our declared motor/sensor delay queues. Its documentation's
  BAM wording is not conformance evidence.
- Its current/voltage/temperature values include synthetic stand-ins. Those
  streams cannot be used for physical load, thermal or battery calibration.

The test used existing local MuJoCo 3.12.0 and ONNX Runtime 1.23.2 rather than
installing the upstream training stack. The body module directly needs MuJoCo
and NumPy; no training, CUDA, NPU, media daemon, camera renderer or hardware
driver was started. The Rust binding accepted the installed ONNX Runtime.
The systemd-nspawn `boot` path remains a Linux deployment test; it was not run.

## Adapter delivered and remaining work

`command_adapter.py` is an isolated, physics-free component that reuses the
existing CommandRamp and V30 heading implementations. It preserves exact-zero
mode selection, orientation history across transitions, and raw action values.
`verify_adapter.py` hash-checks all six recorded sources and their relevant
source freezes before reconstructing every interval. Invalid action dtype,
shape and nonfinite values are rejected. It does not open sockets or operate
the robot.

[ADAPTER_CONTRACT.md](ADAPTER_CONTRACT.md) defines the remaining integration:
actor output at the first interval, no HOME_RAMP, no post-activation pose writes,
four 5 ms BAM updates per control step, exact motor/sensor FIFO phases, continuous
state across stops, epoch/step-tagged transport, and paired physical replay.
The body bridge, Rust observation-builder comparison and complete modified
runtime scheduler are **not implemented or validated**. Protocol 1 has no step
identity and cannot by itself prove fixed-lag parity across independent loops.

The next runtime experiment should implement that explicit compatibility seam
and prove its timing against the retained world before another closed-loop
rehearsal. Substituting a TerrainWorld command wrapper would exercise our local
controller; it would not show that the official daemon now drives it correctly.

Only the one preregistered physics episode was run. Its original runner and
protocol snapshots are preserved with matching receipt hashes. Afterwards the
runner was hardened to reject denied enable/move acknowledgements and continue
owned-process cleanup after a socket-close error; those changes were syntax
checked, not re-run in physics. All actual episode acknowledgements were accepted.

No behavior was promoted, no physical calibration was established and no
carpet-generalization claim changed.
