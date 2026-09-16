# V45: two component regressions and a zero-delay interaction

All four pairs completed the frozen six-session bank. Original and joint V44
controls reproduce **27,703 actual action tensor rows byte-for-byte and numeric
poses exactly**. Both source freezes and all eight evaluation manifests verify.
No new actor was trained during this diagnosis. Original V30 remains retained.

| Pair | Selected flat gates | Downhill gates | Long-composition gates | Long-composition survival |
|---|---:|---:|---:|---:|
| Original V21 / V15 | 2/2 | 0/2 | 2/2 | 180 / 180 s |
| Joint V44 | 0/2 | 0/2 | 0/2 | 67.98 / 14.06 s |
| V44 walker / V15 | 0/2 | 0/2 | 0/2 | 180 / 180 s |
| V21 / V44 stander | 2/2 | 0/2 | 0/2 | 122.02 / 14.70 s |

Replacing only the walker reproduces the nominal forward-08 knee-occupancy
failure: 191/605 walking controls (31.57%) enter the band within 5% of the right
knee's range. Original walker pairs have 0/605; joint V44 has 192/605. Standing
controls do not enter that band in this case. This is a controlled component
replacement result on the declared cases, not a universal causal claim.

The zero-delay case is more specific: joint V44 falls at 2.66 s, while **both
mixed pairs survive the full 18 s**. The walker-only replacement still fails
persistent joint-stop occupancy, but does not reproduce that fall. The joint
zero-delay fall therefore requires the two replacements together in this bank.
Do not label every zero-delay problem as a walker-only failure.

Replacing only standing reproduces long-composition falls, despite passing both
selected flat cases. Replacing only walking preserves both 180-s durations but
fails joint-margin, yaw-tracking and occupancy gates. Survival is not walking
acceptance. One walker-only downhill session survives 36 s, but fails yaw and
final head/face posture; the other falls at 13.92 s. No mixed pair is admissible.

The resulting V46 correction starts from original V21/V15, freezes standing,
trains only walking with explicit original-policy retention and rehearsal,
includes all three timing profiles and replaces the binary absolute joint cost
with a continuous normalized margin cost. It must satisfy the original full
regression banks before any new terrain work. Its protocol and outcome are
separate from this completed diagnosis.

Evidence: `receipts/walking/20260907-v45-analysis/analysis.json`; the eight
receipts use `20260907-v45-{original,joint-v44,new-walker,new-stander}-{flat,endurance}`.
Protocol: `experiments/walking/COMPONENT-ISOLATION-v45.md`. V46 protocol:
`experiments/walking/RETENTION-CORRECTION-v46.md`. Physics, observations, controller,
action semantics and all composite gates remain unchanged; no calibrated physical
or carpet transfer claim is made.
