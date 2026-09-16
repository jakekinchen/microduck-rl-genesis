# V23 terrain, endurance and physical calibration results

The fixed V21 walking / V15 standing pair is still a development candidate.
New terrain and long compositions failed required checks. Four uninterrupted
three-minute walks passed the complete simulated endurance audit.

## Outcomes

| Bank | Independent sessions passing | What happened |
|---|---:|---|
| Flat terrain control | 2/2 | Both continuous 36-second sessions pass. |
| New 3-degree uphill | 2/2 | Both continuous 36-second sessions pass. |
| New 3-degree downhill | 0/2 | Both fall at 13.82 s after STOP. |
| New 3-degree cross-slope | 0/2 | Lateral tracking fails; three windows also fail final head posture. |
| New 3-mm seams | 0/2 | Tracking failures; one fall at 13.92 s. |
| New 2/4/6-mm tiles | 0/2 | Tracking failures; one of four windows passes, neither full session does. |
| New tiles + .6 friction / 1.1 mass/inertia | 0/2 | Tracking/joint/interference failures and two terminal falls. |
| 180-s sustained walking, nominal | 2/2 | Every gate, including whole-session heading, passes. |
| 180-s sustained walking, combined factors | 2/2 | Every gate, including whole-session heading, passes. |
| 180-s walking/turning/stopping compositions | 0/2 after full audit | Each of 20 short windows passes, but heading error accumulates across stops. |
| Measured physical calibration | Blocked inputs | No Ducky-specific raw measurements found in the inspected repositories. |

Terrain totals: 4/14 sessions including controls, **2/12 on new terrain**, and
9/28 windows pass. Five sessions fall. Four later windows remain explicit unrun
failures; no resets or omitted failure denominators. All raised surfaces were
actually loaded, with materialized collider poses/sizes/masks, mass/inertia and
contact friction retained. This is a bounded deterministic development bank,
not a population success-rate estimate or a protected final evaluation.

Endurance totals: all six 180-second worlds complete without falls, excessive
body penetration or failed internal-load gates. Original V23 window scores are
24/24 and its original session aggregation is 6/6. During review, a scoring gap
was identified: heading origins reset between scoring windows even though the
controller and simulation histories remained continuous. A separately retained
whole-session audit uses the same 15-degree endpoint / 20-degree maximum limits
with one heading origin across every transition. **Both compositions fail**, with
endpoint errors 64.0364 and 86.4354 degrees and maximum errors 66.7590 and 89.6160.
The four sustained walks pass this audit. Complete-audit endurance is **4/6**.
Original scores were not rewritten, and the additive audit is exposed evidence.

The drift is visible during STOP: every composition window rotates an additional
5.27–20.27 degrees during its five-second STOP interval. This is a measured
association in the simulator, not a causal controller experiment. The controller
currently drops the heading reference at zero command. The first downhill failure
switches to the standing actor at 13.16 s, then reaches 71.207-degree tilt and
.065707-m ground-relative base clearance at 13.82 s; this is not an absolute-height
false fall on descending terrain.

## Verification and retained artifacts

- Native terrain: 20,301 control rows, 81,204 applied physics-rate load samples,
  24 actual videos and all 28 action files (including empty unrun windows).
- Native endurance: 54,000 control rows, 216,000 applied load samples, 24 videos
  and action arrays. Six continuous worlds total 1,080 simulated seconds.
- Raw float32 action files match the recorded endurance actions exactly. Real
  observation ONNX/Torch error <=1.78814e-6 rad; all 73 frozen source bindings match.
- Endurance worst window yaw MAE .159457 rad/s (<.20), minimum actual joint margin
  .057651 rad (>.02), maximum self-penetration zero. These do not override the
  failed whole-session heading requirement.
- 16 focused tests pass: terrain/ray/clearance/isolation, long-horizon missing-data
  and drift rejection, calibration uncertainty/split validation, and accumulation
  across scoring windows. Workspace verification passes 132 tests.
- The full legacy simulation suite was not repeated: original simulator, policies
  and training sources were preserved; new adapters received focused tests and
  the actual new banks. The earlier 61-group result retains its existing scope.

Receipts (repository-relative):

- `receipts/walking/20260906-v23-terrain/probe.json`
- `receipts/walking/20260906-v23-endurance/probe.json`
- `receipts/walking/20260906-v23-verification/whole-session-heading.json`
- `receipts/walking/20260906-v23-verification/terrain-review.json`
- `receipts/walking/20260906-v23-verification/endurance-review.json`
- `receipts/walking/20260906-physical-calibration-intake/input-audit.json`

Full, actual-speed examples:

- `receipts/walking/20260906-v23-endurance/sustained-combined-start-2--window-1.mp4`
- `receipts/walking/20260906-v23-terrain/downhill-3deg-start-1--window-1.mp4`

## Calibration work and next intervention

The new offline tool `scripts/calibrate_walking_physics.py` prepares and checks
real mass, HOME planar COM and kinetic-friction measurements. It requires raw
hashes, exact assembly/surface/instrument identity, uncertainty, five fit and
three validation readings per quantity, and disjoint acquisition sessions.
It fits only training readings and rejects any excessive held-out residual.
Its six synthetic tests prove intake behavior only. The real empty bundle returns
`blocked_inputs`; no physical value was estimated or replaced. See
`PHYSICAL-CALIBRATION-v1.md` for collection fields and the separate actuator,
full-inertia, sensor/timing and contact-response stages. A connected serial-device
name is not verified robot identity. No hardware was contacted or actuated.

Next local intervention: isolate heading preservation and standing behavior
through STOP, including downhill state transitions, with a fresh versioned
controller/training protocol and the whole-session heading gate frozen up front.
Do not extend PPO blindly, tune on a protected bank or weaken terrain limits.
Broader randomized terrain learning, cross-engine/timestep checks and measured
physical calibration remain required before generalized locomotion or transfer.
No policy activation, publication, paid compute or library admission occurred.
