# Workspace metadata conformance — 2026-09-05

Scope: independent native readers of `robotics.workspace_exchange.v1`.
This is inspection evidence, with no shared training runtime or robot policy.

Schema SHA-256:
`7f6115335dac03c0493940ed9f63d1aba0c741ba55defd434b5208acedf52bf0`.
Shared fixture SHA-256:
`7ea788e0ddce6ce77a99ae18fb1c87589ec5437806ed68ed6d2b8efde0f6eaa4`.

The schema and shared fixture files are byte-identical to the Sim2Claw copies
under `configs/operations/`. Both readers accept all three positive fixtures
and reject all 27 negative fixtures. The shell-looking capability entrypoint
remains inert; every inspection retains false execution and portability flags.

The retained `receipts/20260905/interop.json` records both readers checking
both native exports with explicit producer roots. It binds the exact packet,
reader, schema and fixture hashes used. The exports contain source hashes and
repository identity at that moment, including a dirty-worktree flag. Later
edits or commits can make a source-bound recheck fail; that is expected drift,
not permission to ignore a mismatch. Regenerate both exports for a new check.

MicroDuck reader:

```sh
./scripts/duck exchange-conformance
./scripts/duck exchange-inspect <export.json> --source-root <producer-repository>
```

Sim2Claw reader, run from its own repository/runtime:

```sh
uv run --locked sim2claw ops --json adapter conformance
uv run --locked sim2claw ops --json adapter check <export.json> --source-root <producer-repository>
uv run --locked sim2claw ops --json adapter compare <microduck-export.json> --peer-root <microduck-repository>
```

The recorded local check used the existing Sim2Claw `.venv/bin/python` and
`PYTHONPATH=.../sim2claw/src`, without installing dependencies. MicroDuck used
its existing `.venv-apple/bin/python`; its validator is stdlib-only.

The validation implementations intentionally have different local limits.
MicroDuck accepts packets up to 2 MiB and sources up to 8 MiB; Sim2Claw limits
them to 1 MiB and 4 MiB. Keep portable packets within the smaller limits.
MicroDuck additionally checks branch identity and canonical unique source
paths; the initial Sim2Claw reader checks source hashes and HEAD. Passing this
finite fixture corpus does not assert identical handling of all possible JSON.

Native tests executed here: 17 exchange tests, 19 Duck Lab/workspace tests and
22 offline-diagnostic tests. Frozen contract snapshots and compilation pass.
No paid compute, training, policy activation or hardware was used. The native
Sim2Claw gate result remains its own observation; MicroDuck does not reinterpret
it as a MicroDuck gate. Every profile comparison retains `policy_portable=false`.
