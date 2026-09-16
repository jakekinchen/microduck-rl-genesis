# V30 preserve float32 command semantics outside saturation

V29 passes all 63 flat cases but falls in composition-start-1 window 2.
Those compositions request at most .35 rad/s, so their requested yaw plus
maximum .25 correction cannot reach the original .75 limit. Expanding that
limit should therefore change no action in these cases.

Inspection found an unintended arithmetic change: V29 subtracts the requested
yaw from a float64 constrained sum. The original heading controller first
stores that sum in its float32 command vector and then subtracts two float32
values. Restore this rounding order exactly while keeping the same .80 cap.
This is an implementation correction, not another cap/gain search. Preserve
V29's failed result, including fall and body-interference evidence.

Before simulation, verify 1,000 arbitrary nonsaturating command/orientation
steps byte-identically against V28, including stops and complete-session reset.
Then freeze and repeat the same original 21+42 cases, both 180-second
compositions and both downhill diagnostics. Require every 63 flat case and
both whole compositions to pass for the limited heading improvement. Compare
all V30 composition actions and qpos with V28 exactly. If these gates pass,
execute the unchanged public-surface bank with original V21/V15 actors plus
V30. No thresholds, actors, physics or action assistance change. Physical
acceptance and actor-command extrapolation remain explicitly unvalidated.
