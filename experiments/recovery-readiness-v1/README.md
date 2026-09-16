# Recovery and handoff readiness v1

**The handoff preview is implemented and tested. No recovery actor is admitted.**
The default readiness input blocks recovery before it can request an actor.
The code never produces actuator actions, opens a transport or operates hardware.
It is an offline protocol component for future integration, not a physical safety
controller or a verified robot recovery capability.

## Source assessment

The official policy set's `v5` tag resolves to
[`1b56c396825c052a4e26e95cf2b8d8298af9e9b4`](https://huggingface.co/pollen-robotics/microduck-policies/tree/1b56c396825c052a4e26e95cf2b8d8298af9e9b4).
The immutable manifest matches the retrieved tag bytes. Both responses and their
receipt are retained here; no weights were downloaded or loaded.

| Source | Useful result | Missing admission evidence |
|---|---|---|
| `alpha_sitstand.onnx` manifest | Scripted posture flag: twist.vx 1=sit, 0=stand; ramp 2 s, unwind 1 s | No training source commit/run/checkpoint, model binding, or independent acceptance report |
| `velstand.onnx` manifest | One perpetual walk/stand policy; training branch `protective_fall`, export named `velstand_best.onnx` | Branch name/export time does not bind training commit, chosen checkpoint, full physical model or evaluator evidence |
| Pinned standup/sitstand task sources | Defined reset/pose/command curricula, fixed 61D/14D shape, randomized dynamics and contact sensors | Current source does not prove the published artifact used this source; simulated contact sensors do not establish deployable sensing |
| Pinned current VelStand source | Selects the all-collision configuration and adds servo/head/trunk ground-impact costs | These are training costs; contact coverage and internal loading still need independent checks on the reconciled model |

Sources use RL revision
[`cb70b792312d559a4da09064d92009079671815f`](https://github.com/pollen-robotics/microduck_rl/tree/cb70b792312d559a4da09064d92009079671815f).
The standup/sitstand tasks select `MICRODUCK_STANDUP_ROBOT_CFG`; the current
VelStand task selects `MICRODUCK_ALLCOLLISIONS_ROBOT_CFG`. Treat those distinct
models as separate comparisons. The upstream runtime manifest format permits
absent metadata; its shape/encoding acceptance is less strict than this repo's
behavior acceptance standard.

The local V49/V51 results are **braking diagnoses**, not general get-up training:
V49 used exact serialized simulator states and time-indexed searched actions;
three clean first-stop witnesses still failed full downhill sessions. V51
retargeted those witnesses before braking learning. They do not supply a
source-bound actor for arbitrary fallen states. V52 subsequently regressed
flat/endurance/surface performance; none of these facts licenses a recovery
handoff. Historical receipts remain unchanged.

## Component contract

`handoff.py` accepts timestamped projected gravity, angular rates and joint
positions/velocities. HOME comes from the existing observation contract rather
than a second pose table. It uses no simulator position, height, privileged
velocity, episode progress, reward or target coordinates.

The preview follows:

`walking → stopping → recovery_entry → recovering → stabilizing → ready_walk → walking`

- `recover` requests zero twist through the retained command controller, then
  requires 0.5 s of fresh IMU/joint quiescence before entering recovery.
- Recovery entry requires six already-verified provenance/model/evaluator
  digest inputs. They are absent by default. `RecoveryReadiness` is a typed
  **preview input**, not a verifier: arbitrary hash strings do not establish
  admission. Only synthetic tests supply positive fixtures here. Actual receipt
  loading, content/hash binding and evaluator integration remain unimplemented.
- Recovery exit requires tilt <=10°, every joint within 0.12 rad of HOME,
  gyro <=0.20 rad/s, joint velocity <=0.25 rad/s for 0.75 s, followed by another
  0.75 s standing dwell. A later explicit `walk` request is required to resume.
- Samples older than 60 ms, future timestamps, missing/duplicate/reordered
  frames, invalid dimensions/values/gravity, and phase timeouts latch a fault.
  Stopping has a 4 s timeout, recovery entry 1 s, recovery 8 s, stabilization 3 s.
  Dwell counts sample timestamps and cannot span missing observations.
- A `stop` during a recovery transition latches inhibition; it never blindly
  hands a possibly fallen body to V15. `cancel` latches inhibition in every
  active state. The physical emergency behavior must be validated separately.
- Optional contact regions are consumed only from an explicitly declared
  deployable source. The current profile declares none. Simulator ground-truth
  contacts are rejected, and absence remains **unavailable**, never a pass.
  Locomotion allows only feet. The candidate recovery envelope additionally
  names trunk/head shell contact, but shell support cannot satisfy the standing
  exit predicate. Servo-housing contact is never allowed by this preview.
  These are candidate contact categories, not measured load/impact permissions.

IMU/joint quiescence is **not proof of zero translational speed or ground
support**. The nominal envelope and dwell numbers are provisional protocol
thresholds, not calibrated physical thresholds. They need a preregistered
behavior experiment and deployable-sensor validation before control integration.
No actual safety decisions should be taken from this preview.

## Verification

Run the standard-library-only test suite:

```sh
python3 experiments/recovery-readiness-v1/test_handoff.py
```

Sixteen synthetic tests cover a full ordered handoff, unknown actor and missing
model/source evidence, interrupted dwell, stale/future/duplicate/reordered/gapped
samples, malformed data, transition timeouts, forbidden/privileged contacts,
shell-support exit rejection, explicit resume and cancellation in every recovery
phase. Every decision has `actuator_actions=None` and `physical_authority=False`.
These tests validate protocol behavior, not a robot or a recovery policy.

## Next experiment and exact blockers

1. Finish reconciling the full-CAD physical model, including actual-surface
   collision/penetration and applied internal-load audits. The eleven-collider
   V11 reference can support legacy comparison; it is not full-CAD coverage.
2. Bind a recovery candidate to exact weights, training/export source, model,
   actuator and observation contracts. The public v5 manifest alone is
   insufficient. Do not reinterpret a metadata import as training validation.
3. Freeze a **seated-to-stand flat-floor canary first**, using continuous states
   from an admitted sitting endpoint. Compare the candidate with unchanged V15
   and a no-op baseline. Require full-CAD body contact, applied loads measured
   after every 5 ms physics step, joint/torque/impact limits and final stopping.
   Evaluate shell contact separately during recovery and feet-only support at
   the locomotion handoff. No reset between recovery, stand dwell and restart.
4. Then test disjoint seated/prone/supine/side families, phase/timing variations,
   repeated handoffs, unseen combined environments and endurance. Restrict
   the scheduler to sensor-observable entry/exit inputs; simulator truth belongs
   only to the independent evaluator. Contact sensing is still unavailable in
   the present deployable input profile.

No recovery physics was run in this activity. Physical calibration and the
mandatory BEHAVIOR_VALIDATION gates remain outstanding.
