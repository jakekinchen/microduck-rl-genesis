# V50 downhill yaw correction complete; retain V30

V50 makes a measured walking improvement while retaining the old passing
behaviors, but fails full acceptance. Downhill mean absolute yaw error falls
by 16–17% to .202639/.202257 rad/s, still above the unchanged .20 limit.
Both downhill sessions fall at the first stop (13.98/13.84 s). **Reject V50
for promotion and keep original V21/V15 with V30.** FINAL749 is a retained
development artifact; no policy was activated.

## Complete exposed evaluation

| Required bank | Original V30 | V50 FINAL749 | Decision |
|---|---:|---:|---|
| Original flat cases | 21/21 | 21/21 | Retained |
| Repeated flat cases | 42/42 | 42/42 | Retained |
| Whole 180-second compositions | 2/2 | 2/2 | Retained |
| Whole downhill sessions | 0/2 | 0/2 | Failed |
| Whole exposed surface sessions | 5/14 | 5/14 | Same five retained |
| Exposed surface windows | 12/28 | 13/28 | One new window; no new whole session |

The five retained sessions are `rigid-control-start-{1,2}`,
`soft-low-traction-start-{1,2}` and `unseen-low-medium-start-1`. The historical
“unseen” names are now exposed development data. The newly passing
`unseen-high-mild-start-1--window-1` does not admit its session: whole-session
heading error is 20.18397 degrees (endpoint limit 15, maximum limit 20).
No previously passing surface window or session is lost.

All original task, sustained bilateral gait, loaded slip, joint/torque,
posture, non-foot support, heading, body interference, applied 200-Hz internal
load and full-duration gates remain. Both later downhill windows are unrun
after terminal falls and fail closed. Start 1 also records non-foot support
and sustained internal bracing during the failed stop. Start 2 lacks full-stop
evidence; absence of its bracing failure is not a complete safe-stop pass.

## Downhill walking prefix, separate from full acceptance

Exactly the same 551 controls at 2–13 seconds are compared before braking.
Yaw is actual body yaw rate minus requested yaw rate; absolute errors are
averaged without cancellation. Signed mean yaw cannot replace this test.

| Start | V30 absolute yaw | V50 absolute yaw | Limit | V30 forward error | V50 forward error |
|---|---:|---:|---:|---:|---:|
| 1 | 0.244186 | 0.202639 | .200000 rad/s | 0.047197 | 0.040680 m/s |
| 2 | 0.240999 | 0.202257 | .200000 rad/s | 0.047718 | 0.041488 m/s |

Forward error also improves and stays below .05 m/s. This does not certify
a complete walking window: the yaw threshold and subsequent stop still fail.
Plots and source data: `outputs/walking-retention-v50/`. Recorded-pose video:
`outputs/walking-retention-v50-video/downhill-start-1.mp4` (699 source rows,
350 frames at 25 fps; no new physics integration or repaired motion).

## Bounded learning and verification

- One 2,880-transition smoke, 15.537 s; one 864,000-transition full run,
  1004.000 s. Seed 26090850, FINAL749 only; no extension or checkpoint search.
- Original V21 walking initialization; original V15 standing and V21 teacher
  frozen, parent normalizers unchanged. Only walking weights learn.
- Targeted absolute downhill-yaw reward, flat-only online retention, and
  56,655 original walking replay rows from passing flat/long/surface sessions.
  All replay action labels reproduce original ONNX tensor bytes exactly.
- 24 compiled terrain/timing/yaw cells; 341,008 paired control continuations
  and repeated HOME resets match exactly. Actual floor quaternions, collision
  masks, nominal physical arrays, yaw starts and delay settings verify.
- 180-second continuous candidate-state training episodes: 40 flat and 20
  uphill completions; zero downhill completions. Training records 9 flat,
  124 downhill and 4 uphill falls. These are changing-policy training counts,
  not final policy evaluation scores.
- All 864,000 observation/action rows, reward components and actor-routing
  masks verify. 1,988 switch histories and 9,638 finite learning scalars verify.
  Maximum reward reconstruction residual is 5.96e-8. Privileged terrain labels
  remain excluded from actor and critic inputs.
- Exact joint/component checkpoint splits and fixed component tensors verify;
  main training freeze binds 213 sources. All five V50 source freezes pass,
  and previously frozen V44–V49 sources remain unchanged.
- 140 workspace tests and three focused tests pass. ONNX export parity and
  every actual evaluation observation/action parity check pass.

## Artifact identities

- Joint FINAL749 SHA-256: `65f6c7d38043908c2a89ed733fb5ffb7e504e04410bb8c48b32995a8b0bbb162`.
- Walking component SHA-256: `352a349603992ead2a43ab1f35714dda9f73e416697809a318d45ebc24eb0fac`.
- Original standing parent SHA-256: `acab8402e262dbb6af5a3fab9b67fa4ce5e34a4d23cadb127fe6dfa475a70e46`.

Receipts under `receipts/walking/`:
`20260908-v50-retention-conformance`, `20260908-v50-replay-parity`,
`20260908-v50-retention-flat`, `20260908-v50-retention-repeated`,
`20260908-v50-retention-endurance`, `20260908-v50-retention-surfaces`,
`20260908-v50-retention-verification` and the closing activity receipt.
All failed cases and original evaluator scores remain retained.

## Next activity

Freeze a bounded state-conditioned braking correction using the three clean
V49 stopping witnesses. First revalidate or retarget those demonstrations on
V50 incoming states: the original-walker search does not prove the same actions
will work after this walking change. Preserve original V15 steady standing.
Use V50 only as a development starting point, keep the .20 yaw gate and close
its remaining margin, then require successive stops/restarts and full flat,
180-second and surface retention before any admission.

The walking correction activity is complete; walking acceptance is not.
Fresh sequence and protected terrain banks remain unrun. Measurement-based
physical calibration, broad terrain generalization and carpet transfer remain
unmet. No paid compute, publication, policy activation or hardware was used.
