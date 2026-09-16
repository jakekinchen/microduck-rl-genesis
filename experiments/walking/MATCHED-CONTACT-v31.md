# V31 matched-support numerical diagnosis

Freeze before execution. Reuse all five V1 exposed initial-standing action
prefixes, maximum one second, truncating at their original terminal record.
Replay every float32 action unchanged in three lanes: original native plane,
native four fixed boxes matching Genesis V25, and unchanged Genesis CPU V25.
Native box geometry, positions, friction and solver parameters match the
authored Genesis panels. Translate the initial Y coordinate to the panel center;
subtract only this translation when comparing poses. Robot geometry, masses,
inertias, BAM parameters, 5-ms physics and four-tick action hold stay fixed.

Require original native-plane reproduction within 1e-10 in all qpos values.
Check original Genesis reproduction within 1e-7 after adding read-only observers.
Capture poses, delayed targets, torques and actual applied contact records at
200 Hz without extra integration or forwarding physical data. Do not compare
contact force sums as if different manifolds had identical point identities.
Retain original 2-mm maximum base and 5-degree joint discrepancy diagnostic
limits, scored at the original 50-Hz times for all five cases, and additionally
report 200-Hz discrepancies. Missing traces and altered actions reject a run.

First change only support representation. A remaining discrepancy requires
another separately frozen diagnosis of the first divergent property; no broad
PPO extension is justified by this probe. Passing is numerical conformance of
these short exposed prefixes, not a gait, calibrated material or physical pass.
Retain compressed raw telemetry and per-case results including all failures.
