# Gait-v4 reader compatibility — 2026-09-05

The completed gait-v4 baseline and candidate receipts initially produced two
inspection errors: the workspace reader supported composite schema v3 only.
The reader now recognizes the explicit v3 and v4 schemas, preserving the same
visible-only admission and target-AND-gait consistency checks. Unknown schemas
are not granted gait semantics. No evaluator or historical receipt was changed.

Validation: `tests/test_duck_workspace.py` passed all 23 tests, including a new
v4 negative-result test that also rejects contradictory target/gait claims and
reserved-bank reports. Retained stdout: `gait-v4-reader-tests.txt`.
`./scripts/duck status` reports 22 development evaluations and zero inspection
errors; both final v4-format comparison receipts show 0/4 combined passes with
verified manifests. This is reader compatibility, not walking acceptance.

This addendum follows the immutable `receipts/laser-gait/SHA256SUMS` package;
it does not rewrite that diagnosis, its bound source snapshot, or its results.
An already-running Duck Lab process must be restarted by its owner to load the
new reader. The direct CLI was tested; no unrelated viewer process was stopped.
