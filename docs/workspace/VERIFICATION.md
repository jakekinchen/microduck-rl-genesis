# Workspace verification

Run the fast tooling checks after changing the workspace CLI, viewer, metadata
exchange or offline diagnostics:

```sh
./scripts/duck verify
./scripts/duck verify --list
./scripts/duck verify --json-out .workspace/verification.json
```

This runs the selected unittest modules without installing dependencies or
importing a simulator. Each module must discover at least one test. Failures,
import errors and empty discovery return a nonzero exit code; optional skipped
tests retain their reasons and produce `passed_with_skips`. A successful process
exit with skips does not establish the skipped checks. The JSON result is also
written on test failure and records the checkout, interpreter, counts and scope.
Detailed test failures and tracebacks remain in terminal output.

`scripts/verify_workspace.py` owns the shared module list. The `duck` command,
workspace CI and `tests/run_all.py` use that same runner. Add a new dependency-free
workspace test module there so local and CI coverage agree. Do not add simulator
tests to this list. Node is optional for the existing diagnostic JavaScript syntax
test; its absence is an explicit skip. Actual browser playback and interaction
still require browser QA.

## Fresh checkouts and worktrees

The launcher selects `.venv-apple/bin/python` from its own checkout when present,
otherwise `python3`. An Apple environment is unnecessary for the tooling suite;
the CI reference is Python 3.12. To select an interpreter explicitly:

```sh
python3 scripts/verify_workspace.py
```

Use the scripts from the checkout under review, including when your current
directory is elsewhere. The runner resolves source and tests from its own file:

```sh
/path/to/worktree/scripts/duck verify
python3 /path/to/worktree/scripts/verify_workspace.py
```

There is no dependency installation or shared-checkout setup hidden in these
commands. Each worktree uses its own source; an optional `--json-out` relative path
is resolved from the caller's current directory. Generated results belong under
ignored `.workspace/` when retained in a checkout.

## Choose the proof appropriate to the change

| Change or question | Verification |
|---|---|
| Workspace tooling, CLI or offline diagnostics | `./scripts/duck verify` |
| Current queue and retained development evidence | `./scripts/duck status` |
| Local packages, pinned BAM and contract readiness | `./scripts/duck doctor` |
| Frozen interface/model/actuator sources | `python3 scripts/freeze_contract.py --check` |
| Viewer JavaScript | `node --check duck_workspace/web/app.js`, then browser interaction and retained-video QA |
| Simulation or training implementation | Relevant focused tests, then the authorized runtime checks for that lane |

`tests/run_all.py` remains the broader runtime suite: it includes the workspace
checks but also starts simulator tests and needs the documented runtime/BAM setup.
Do not use it as a quick tooling check or while another experiment owns compute.
Its legacy commands run from the repository root and retain their own skip rules.

Neither workspace verification nor `doctor` establishes walking quality, task
acceptance, held-out results or physical authority. For a behavior intervention,
follow `AGENTS.md`, the current queue and the existing experiment workflow.

## External evidence and workspace inspection

The viewer and workspace inspector refuse symlinked evidence, including directory
links to external drives. `duck prepare` now reports an unreadable training record
in `active_training_record_errors` and returns not-ready, while preserving the
verified local focus and its diagnostics. It does not open the link, conceal the
inspection gap or grant launch authority.

V54 intentionally stores its bulk evidence on the UUID-checked external volume.
Its dedicated frozen verifier, `scripts/verify_recipe_v54.py`, checks the complete
two-arm artifacts and action parity through the declared archive paths after
both runs and all eight evaluation banks finish. That verification is separate
from workspace serving. A successful V54 verification does not imply that the
viewer supports external archives or that the candidate passed its behavior gates.
