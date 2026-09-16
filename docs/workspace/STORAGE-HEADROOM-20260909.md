# V54 storage headroom

September 9, 2026 local time (September 10 UTC). The existing preservation-first
maintenance workflow moved one eligible older Codex backup to the second drive.
No training receipt, model, source tree, active cache, Time Machine directory or
running process was removed.

- Source: `/Users/kelly/Library/Application Support/CodexBackups/snapshots/2026-09-06T03-15-05`.
- Destination: `/Volumes/cerebro-old/CodexOffload/DailyMaintenance/20260910T024300Z-v54-headroom/2026-09-06T03-15-05`.
- Receipts: `/Users/kelly/.codex/maintenance-receipts/20260910T024300Z-v54-headroom/`.
- Verified: 13,267,905,512 copied bytes, 2,044 objects, clean checksum rsync and
  equal SHA-256/metadata manifests before exact-source removal.
- `/System/Volumes/Data` free space: **3.18 → 15.54 GiB**. Observed free-space
  movement was 13,275,594,752 bytes; it is reported separately from logical copy
  size because concurrent APFS activity can change the total.
- Destination free space after the move: **888.09 GiB**. Its root remains
  protected; the existing owner-writable `CodexOffload` directory was verified
  on volume UUID `ABDDF5AF-D90F-4F8C-9A5B-4056ECEF58B4`.
- `latest` and the newest three local dated snapshots (September 7, 8 and 9)
  remain. No backup job or source open file was found. No further archive was
  positively classified for this maintenance pass; active uv/pnpm work was left.

The initial root-level audit correctly reports that the volume root is not
writable. A second audit of the actual `CodexOffload` destination verifies its
writability and mount point before the move. No permissions were weakened.

To restore the archived snapshot locally, first ensure sufficient internal
space, then copy it back and verify against the retained destination manifest:

```sh
rsync -a -- '/Volumes/cerebro-old/CodexOffload/DailyMaintenance/20260910T024300Z-v54-headroom/2026-09-06T03-15-05/' '/Users/kelly/Library/Application Support/CodexBackups/snapshots/2026-09-06T03-15-05/'
```

V54's new experiment data separately uses
`/Volumes/cerebro-old/CodexOffload/MicroDuck/20260909-recipe-v54/`, with stable
repository directory links. Moving the backup creates headroom; it establishes
no physics, policy-quality or carpet-transfer result.
