# V43 handoff diagnosis — September 7

The diagnosis is complete. V30 remains the retained development baseline;
no new policy was trained or promoted. The next recommended experiment is
continuous walk–stand–walk learning that covers braking and restarting, with
the existing regression and physical-quality gates preserved.

## What was measured

All eight exposed V30/V42 downhill/composition sessions reproduce across
**36,622 control steps**. Actual generated float32 action and observation bytes
match the originals, including signed zero; all generalized coordinates match
exactly. The command controller stays closed loop. Forced-action overrides were
rejected in the first attempt, which is retained as an incomplete diagnostic.

Captured **65 complete reset/handoff states**: 16 original training reset states,
26 from V30 sessions and 23 from V42 sessions. These are captured samples, not
65 independent environmental conditions; some reset states repeat. Each state
preserves complete native MjData, joint damping/friction, BAM targets, previous
torque/timestamp, motor FIFO, sensor history and last action. Disk round-trip and
cross-world continuation match exactly for every state. The original actor's
49 source branches additionally reproduce **9,987 controls** with exact action
and observation bytes and zero pose discrepancy.

Both standing actors were tested for five seconds from every shared state:
**130 paired branch trials**. They retain separate falls, posture, joint/torque,
non-foot support, body interference and 200-Hz internal-loading results. Loaded
foot slip is separately reported. Branch scores do not replace full locomotion,
continuous-session or physical acceptance.

| Starting states | V15 standing from V30 baseline | V42 standing |
|---|---:|---:|
| Original training HOME/handoff resets | 15/16 | 14/16 |
| States reached by the V30 pair | 23/26 | 25/26 |
| States reached by the V42 pair | 20/23 | 22/23 |

The diagnostic initially counted torque saturation at 99% of the limit; the
original contract uses 98%. A separately retained additive analysis reapplies
the stricter original occupancy and absolute torque limits. **No branch outcome
changes.** Original reports remain intact; the table uses the additive result.

## Findings that determine the next step

1. **The training bank contains a failure.** V42 falls from the known uphill
   HOME state at .80 seconds and the known uphill handoff at 1.10 seconds.
   V15 completes both five-second branches. These starts were already present
   in V42 training; adding unfamiliar reset examples alone does not address
   every observed failure.
2. **One downhill handoff improves.** From the first V30 downhill handoff, V15
   falls at .68 seconds and V42 passes five seconds. At the second yaw/start,
   V15 falls at .68 and V42 at .84 seconds. Keep both outcomes.
3. **The late composition state defeats both tested standers.** At the V42
   eighth-window handoff (139.12 seconds), V15 falls after .94 seconds and V42
   after 1.04 seconds, reproducing the original 140.16-second fall. This is not
   proof that no controller could recover; it motivates improving the state
   delivered by the braking phase as well as standing recovery.
4. **History differs materially from the reset bank.** At that late handoff,
   the nearest matching flat handoff motor FIFO differs by a maximum .592 rad;
   BAM's previous torque differs by .207 N·m. Sensor-history maximum difference
   is 2.118 across mixed observation units. Per-feature distances are retained
   separately; they have no invented pass/fail threshold. The old PPO runs did
   not retain every observation, so this measures reset-bank distance, not
   full stochastic training-distribution coverage.
5. **The three-second horizon does not truncate the observed falls.** No branch
   survives three seconds and then falls before five. The V42 second downhill
   session instead fails at 4.12 seconds while walking, before a stopping
   handoff. This also motivates testing the reverse standing-to-walking
   transition and the effect of the new standing posture on the walker.

[Paired clearance traces](../../outputs/walking-handoff-v43/paired-handoffs.png)
show the known uphill failure, the improved downhill handoff and the late
composition failure. [PDF](../../outputs/walking-handoff-v43/paired-handoffs.pdf)
and plotted data are retained alongside the image. The curves use actual
recorded branch poses and surface-relative clearance, without repaired motion.

## Recommended next experiment

Train complete command sequences in native MuJoCo/BAM, beginning from the
retained V21/V15 motor pair with V30 command control. Include braking, a settled
stand, restart and repeated turns in the same episode. Train for compatible
states in both directions, rather than assuming an isolated standing score
guarantees that walking will resume successfully.

The frozen V43 bank provides known uphill controls and difficult incoming
states for diagnosis/rehearsal. Keep a separate fresh sequence bank with command
orders, stop durations and initial orientations fixed before candidate
evaluation. Declare one bounded budget and final checkpoint; retain actual
training observation/history coverage so future distribution claims are
measurable. First require the original 63 flat gates, both complete 180-second
compositions and improved downhill stopping, with no regression against the
existing exposed surface baseline. Keep all posture, stepping, slip, joint,
torque, body interference and internal-load rejection gates. Only then proceed
to new terrain families under `BEHAVIOR_VALIDATION.md`.

This is the recommended next work item, not an executed training run. The
cross-engine soft-contact discrepancy and missing Ducky-specific calibration
remain explicit. Public priors do not establish carpet or hardware readiness.

## Verification and storage

- `receipts/walking/20260907-v43-handoff-coverage-r3`: complete replay, 65 states,
  130 branch traces and source freeze.
- `receipts/walking/20260907-v43-handoff-analysis`: complete-history distances,
  source-branch reproduction and additive original torque checks.
- `receipts/walking/20260907-v43-byte-verification`: separately rerun full
  closed-loop byte verification and source-branch byte checks.
- Earlier V43 and r2 attempts remain incomplete and retained. R2 exhausted disk
  while serializing the final snapshot; its empty partial payload is preserved.
  Snapshot compression and deduplication verified original bytes before removing
  their redundant representations. Maps and original manifest are retained.
- Each full pickle repeats most of the robot model. Content-addressed 64-KiB
  blocks retain every serialized byte: about 5.64 GB of logical snapshots use
  about 37.5 MB of shared compressed blocks plus 5.9 MB of indices. Three
  focused tests cover exact reconstruction, sharing and tamper/budget rejection.
  Only trusted, hash-bound local snapshots may be deserialized. MuJoCo copy/state
  semantics were checked against its [Python documentation](https://mujoco.readthedocs.io/en/stable/python.html)
  and [state documentation](https://mujoco.readthedocs.io/en/stable/computation/index.html#the-state),
  then verified in the installed runtime.
- **138/138 workspace tests pass**, including snapshot storage tests. Original
  frozen sources remain unchanged. All diagnostic jobs from this activity are
  complete. No hardware, paid compute, policy activation or library admission.
