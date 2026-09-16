# Incomplete diagnostic setup — no alternate-model result

The first attempt stopped before stepping the full model: it compared BAM-
configured reference armature against raw XML armature and correctly rejected
the mismatch. The raw full and reduced XML variants must be compared before
either is configured, then both BAM-configured armatures compared afterward.
The corrected attempt is `20260905-v5-full-collision-replay-r2`.
This partial reference trace is not a completed collision or walking result.
