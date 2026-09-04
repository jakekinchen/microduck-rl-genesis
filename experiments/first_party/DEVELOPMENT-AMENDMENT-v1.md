# First-party development amendment v1

The absence of Pollen's checkpoint history blocks claims about, and exact
repeatability of, Pollen's official `alpha_walking.onnx`. It does not block this
repository from training a new policy from scratch and debugging its own
training, normalization, export, and visible-development evaluation chain.

The first-party lane therefore admits only a clean committed repository state,
the public seed and budget frozen in `development-plan-v1.json`, `resume=null`,
and the exact checkpoint produced by that run. Before checkpoint parsing, the
export admission verifies the first-party origin, no-resume declaration, source
commit and relevant source bytes, frozen-run record, configuration pickle, and
checkpoint paths and digests. The frozen-run record also retains the dependency,
task, model, interface, BAM, command, seed, and budget hashes used by the run.
After export, evaluation admission verifies the checkpoint association and the
exact ONNX and visible-suite digests before learned-policy inference, while the
export association retains the separately attributable normalizer digest. The
evaluator independently checks its pinned model/task/BAM inputs.
There is no generic provenance bypass. Traversal, symlinks, changed bytes, a
non-first-party origin, synthetic learned-policy latency, and held-out suites
are rejected.

This amendment does not alter historical M5 inputs or receipts. It leaves open:

- exact repeatability of the official policy;
- held-out acceptance and any success claim;
- the official Apple/CUDA comparison;
- admission or promotion of official/community M6 artifacts;
- unresolved third-party licensing and publication;
- transfer, activation, and hardware authority.

The next executable local step is to use the retained first-party artifact only
on additional preregistered visible-development diagnostics, or preregister a
longer single-seed first-party training budget. Neither path may inspect or
realize held-out seeds, select a checkpoint by outcome, or imply gait success.
