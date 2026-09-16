# Aborted evaluator initialization

No behavioral result exists in this directory. The first attempted dynamic
evaluation failed before control step one because the display-world helper
used `trunk` instead of the locked body's actual name `trunk_base`. A following
render smoke also found a requested framebuffer wider than the locked default.
Both initialization defects were fixed in the separate helper, without editing
the model, BAM, old training sources, or learned policy. The successful rerun
is `../20260905-baseline-dev-r2/`. Preserve this partial attempt as a negative
infrastructure receipt; do not count it as a failed behavioral trial.
