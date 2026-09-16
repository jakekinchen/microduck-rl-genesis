# V28 course establishment after initial settling

V24 passes two long compositions but regresses one original repeated-window
case: motor-25ms-sensor-20ms, turn-left-738, repeat 1 ends 18.182 degrees short
against the unchanged 15-degree limit. Its initial STOP already holds an old
heading despite no prior motion command. V19 follows settling orientation.

Change only this state transition: use exact V19 heading behavior until the
first nonzero routed motion command. Thereafter preserve the desired course
through STOP using exact V24 behavior. New-session reset clears this latch.
STOP commands remain exactly zero. No gain, filter, timing, actor, motor action,
physics, threshold, reward or trajectory assistance changes.

Before candidate inspection, freeze and rerun the original 21 plus repeated 42
flat cases, and V24's two 180-second compositions and two downhill sessions.
Preserve all V24 results. Require all 63 flat gates plus both whole-session
compositions to accept that limited improvement. Downhill and public surface
acceptance remain independent and cannot be averaged into a pass. This is
exposed development without physical or library admission, and needs no training.

Verify original first-window action arrays match V21 on each fresh session;
later restart actions may differ because their course reference now persists.
