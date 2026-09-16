# V47: downhill arrives faster at the standing handoff

Both original V30 and V46 pairs pass the two matched flat sessions and fail both
original downhill sessions. All 2,763 downhill controls reproduce retained
action tensor bytes and numeric poses exactly. Sixteen complete captured states
reproduce 25 subsequent controls each (400 controls total), including actual
observation/action bytes, qpos and qvel after storage round-trip.

| Pair / terrain | Speed just before handoff, starts 1 / 2 | Yaw at 13.30 s, starts 1 / 2 | Session result |
|---|---:|---:|---:|
| Original / flat | .038 / .077 m/s | .564 / .320 rad/s | 2/2 |
| Original / downhill | .136 / .141 m/s | 3.278 / 2.844 rad/s | 0/2 |
| V46 / flat | .055 / .064 m/s | .899 / .813 rad/s | 2/2 |
| V46 / downhill | .137 / .136 m/s | 3.285 / 3.092 rad/s | 0/2 |

Trunk tilt is still below five degrees just before each handoff. First standing
action jumps are .965–1.316 rad on the passing flat cases and 1.072–1.437 rad on
the failed downhill cases (largest joint deviation). A large action jump alone
does not separate passes from failures. The incoming velocity and motor-history
differences matter; no individual feature is proven to cause the fall.

Choose a standing correction with the original walker fixed, starting from V15.
Rehearse original flat and long-composition standing behavior while learning
recovery from complete pre-brake states and continuing through restart. Include
both start orientations, the three original timing profiles and uphill controls.
Online imitation should apply to the passing flat domain, not force imitation
of the failed downhill stander. Full original gates still decide acceptance.
This is a targeted next experiment, not a claim that standing-only learning must
solve the failure. Do not expand terrain or open protected banks yet.

Evidence: `receipts/walking/20260908-v47-{original,v46}-handoff` and
`receipts/walking/20260908-v47-handoff-verification`. Sources and unchanged gate
receipts are retained; 139 workspace tests pass. The full state includes native
MjData, BAM state, delay/sensor histories, command ramp and heading controller.
No calibrated physical or carpet-generalization claim is established.
