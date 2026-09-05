# Workspace validation — 2026-09-05

Scope: the new read-only Duck Lab viewer, workspace CLI, history scanner,
behavior drafts, documentation and repository skill. This is tooling evidence,
not a new learned behavior or physical test.

## Executed checks

| Check | Result |
|---|---|
| `.venv-apple/bin/python tests/test_duck_workspace.py` | 19 passed. Negative-result preservation, tampering, missing/unbound artifacts, parent manifests, unsupported/held-out/reserved data, paths/symlinks, timestamps, draft errors/overwrite, history formats, GET/range-only HTTP and loopback boundary. |
| `.venv-apple/bin/python tests/test_laser_task.py` | 12 passed; existing steering and perception behavior retained. |
| `.venv-apple/bin/python scripts/freeze_contract.py --check` | Contract snapshots verified. |
| `./scripts/duck doctor` | Apple runtime, all five inspected packages against the Apple lock, MPS availability, frozen contract and clean pinned BAM checkout pass. |
| Python compilation and `node --check duck_workspace/web/app.js` | Pass. |
| Skill Creator `quick_validate.py .agents/skills/microduck-experiments` | Skill is valid. |
| `git diff --check` | Pass. |
| History scanner with the two explicit linked tasks | 126 sessions, 118,803 JSONL lines, 2,777 extracted text messages; zero read/parse-discovery errors reported. |
| Initial development receipt inspection | Ten reports with verified containing manifests, no inspection errors. Later dynamic reports are discovered on refresh. |

## Actual browser inspection

- Retained baseline and v2 videos loaded with 12-second durations and playable
  media state. Playback advanced the recorded trajectory and metrics. At the
  end, the two video positions differed by approximately 0.00007 seconds in
  the inspected DOM snapshot (this observation is not a universal sync bound).
- Scrubbing target-loss to 4.00 seconds displayed the 4.02-second post-step
  sample, target unavailable, approximately 0.007 m/s robot speed, no fall.
- Case changes, comparison changes and no-video states worked. Loading a new
  selection now hides the previous report while its evidence is being read.
- The new dynamic-development schema displayed 1/6 and its actual per-case
  failures for the inspected robust/baseline pair. Its column is explicitly
  mean visible gap, not the legacy final-distance metric. No reserved results
  were opened. These are observations of another ongoing task's receipts, not
  outcomes produced by this workspace task.
- The training view displayed TensorBoard iterations, rewards and timestamps,
  including the separately running turn-correction experiment. It labels
  process liveness as unchecked and does not control that process.
- Phone-width inspection at 390×844: document width was 390 px, with no
  horizontal page overflow. Viewport override was reset after inspection.
- No browser console errors were observed during the inspected flows.

## Scope preservation

The canonical simulation, actuator, exporter and evaluator were not edited by
this workspace task. The broader simulator suite was not rerun for these
isolated tooling additions; the focused tests and frozen-contract check are
the relevant validation. The new CI job runs the workspace tests on Python 3.12
without installing Genesis or launching a GPU workload.

Concurrent L2 code, training, receipts and edits to `tests/run_all.py` and
`scripts/retain_laser_receipt.py` belong to the ongoing dynamic-laser work and
were preserved. Shared `.gitignore`, queue and status documents received only
the workspace additions. No commit or push was made by this audit task.

The exact BAM dependency was materialized at `.workspace/bam` with the existing
immutable helper and is clean at
`62bd8ce12154340be97e06f7f41a0ca8f116d967`. It is ignored local dependency state.
Private extracted conversations are also ignored. No global skills/settings,
paid resources, third-party messages, policy activation or hardware operations
were changed by this task. The local loopback viewer is the only service this
task leaves running for the user; stop it with Ctrl-C in its terminal.

## Metadata exchange follow-up

The additive `duck_workspace/exchange.py` and `exchange-export`,
`exchange-inspect`, `exchange-conformance` commands passed 17 focused tests,
including refusal of named pipes, symlinks and files changing during a read.
The shared 30-case fixture pack passed in both native readers, including an
inert shell-looking entrypoint. The fixture path, exact contract digest and
bilateral source checks are retained in `exchange/CONFORMANCE.md` and its JSON
receipt. No simulator dependency was added to the MicroDuck workspace CLI.

The existing 19 workspace tests, separately integrated 22 offline-diagnostic
tests, Python compilation and frozen-contract check passed again. The workspace
CI now includes all three tooling suites. Diagnostics guidance was linked from
the README, behavior workflow and project skill. These checks establish tooling
behavior and metadata compatibility only; policy portability is not established.
