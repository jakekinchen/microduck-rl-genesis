# V23 native visual inspection

Viewed actual 720x480 frames extracted from retained videos, alongside trajectory data.

- Downhill start 1 at 13.54 s: standing actor, feet on sloped surface, visibly pitching after STOP. Source telemetry: transition to standing at 13.16 s; at 13.82 s both feet unload, tilt reaches 71.207 degrees and ground-relative base clearance falls to .065707 m. This is a genuine terminal fall, not a false absolute-world-height trigger on a descending floor.
- Seam start 1 at 8.02 s: narrow raised seams are visibly present beneath the actual sole. Yellow position trail shows the foot/robot spending time at the obstacle. Tracking failure is supported by the full velocity trace; a still image alone does not quantify stepping or slip.

The figures are diagnostic. All original frames, float32 actions and contacts remain in the frozen V23 receipt. No successful uphill frame is presented as broad terrain success.

- Sustained combined start 2 at 179.02 s: standing actor, bilateral support and retained stopped pose are visibly consistent with the full recorded stop metrics.
- Composition start 2 at 178.02 s: robot is upright and stopped, but the full-session heading audit rejects its accumulated orientation error. The visually plausible standing frame does not override the failed composition.
