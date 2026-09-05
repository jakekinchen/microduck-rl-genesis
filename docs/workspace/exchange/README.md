# Read-only workspace exchange

`robotics.workspace_exchange.v1` is a small metadata envelope shared with the
Sim2Claw operations workspace. The exact schema bytes are mirrored in
`workspace_adapter.v1.schema.json`; their SHA-256 is carried in every packet.
Neither repository imports the other's Python package or runtime environment.

```sh
./scripts/duck exchange-export --owner-task '<current-task-id>' > /tmp/microduck-workspace.json
./scripts/duck exchange-inspect /tmp/microduck-workspace.json
./scripts/duck exchange-inspect /tmp/microduck-workspace.json --source-root .
./scripts/duck exchange-conformance
```

Export reads current file bytes and Git identity, derives the 14D action,
61D observation and 50 Hz / 5 ms timing profile from the native interface
files, then verifies those source hashes again before emitting JSON. It does
not import training code or run physics. `owner_task` identifies the exporting
workspace task, not an exclusive owner of concurrently running experiments.

The native source ordering is AGENTS, ordered task list, concise GOAL, then
the action/observation/control contracts. Current user authority remains
outside this metadata packet. Historical lessons are separately identified;
they cannot override the task list. A queue/status disagreement is retained
through separate source hashes rather than converted to a completion claim.

Inspection without a root checks structure, exact contract digest, IDs and
references, canonical relative paths, action dimensions and permission
constants. An explicit `--source-root` additionally checks each source's
bytes, rejects symlinks, and checks repository HEAD and branch. It never
follows a path outside that supplied root, imports a source or executes an
entrypoint. A stale or wrong root fails; regenerate a snapshot after changes.
The worktree's dirty flag and native-gate field remain producer observations.

The stdlib validator supports only the vocabulary used by this exact schema;
it is not a general JSON Schema implementation. Packets are bounded to 2 MiB;
individual source files to 8 MiB. Duplicate JSON keys, nonfinite numbers,
symlinks, non-regular files (including pipes), files changing during a read,
unknown versions or fields, privilege escalation, traversal, duplicate IDs,
unresolved references and dimension/unit-count disagreements are rejected.
An unfamiliar native schema, frame description or unit may still be valid
metadata; it is never permission to execute or convert a robot policy.

## Claim boundaries

- All execution, source mutation, training, hardware, promotion and paid
  compute permissions are false. Entrypoints describe native capabilities.
- `native_gate.status=source_only`: exporting did not run an evaluator or
  recheck current process liveness, runtime readiness or external authority.
- Source-byte verification is not evaluator acceptance, physics conformance,
  provenance certification or authentication of a publisher.
- No trace records, media, checkpoints, hidden suites or physical evidence
  are exported. Native proof classes and schemas are descriptive metadata.
- Matching dimensions, units or control rate do not establish policy
  portability. MicroDuck's deltas from HOME are not Sim2Claw absolute targets.

## Fixtures and versioning

`fixtures/microduck.source-snapshot.json` is a retained native export for
portable structure tests. Its source hashes and Git identity describe the
time it was generated; it is not asserted to match a later checkout.
`fixtures/negative-cases.json` lists path/value mutations applied to that
snapshot. Each must be rejected. Tests also verify changed and symlinked
sources against temporary Git repositories.

`workspace_adapter.v1.fixtures.json` is the byte-identical shared pack of
30 synthetic cases: three valid metadata packets and 27 required rejections.
Both native readers can consume this data without reading a producer root.
It includes an untrusted shell-looking entrypoint that must remain inert.

The Sim2Claw schema is initially mirrored from
`configs/operations/workspace_adapter.v1.schema.json`. The exporter and reader
in each repository remain independently owned. Before changing this format,
compare the schema bytes, update fixtures, and exercise both readers against
both native exports. A unilateral successful parser is not bilateral
conformance. Breaking changes require a new version and migration guidance.

See `CONFORMANCE.md` for the checks actually completed on this revision.
