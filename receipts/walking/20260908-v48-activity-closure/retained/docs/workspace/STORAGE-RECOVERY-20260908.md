# Storage recovery for V47/V48

The user authorized external storage use and retiring the Time Machine backup.
The measured starting internal free space was 0.23 GiB. Time Machine was set
to manual and its sole `cerebro-old` destination forgotten through System
Settings. All nine verified backup snapshots on volume UUID
`ABDDF5AF-D90F-4F8C-9A5B-4056ECEF58B4` were removed with `diskutil`.
This recovered 790.08 GiB externally before the subsequent archival copy.

The separate external `CodexOffload` tree and latest raw backup directory
`/Volumes/cerebro-old/2026-09-06-041739.previous` remain. No disk or volume was
erased. `cerebro` remains unchanged at about 40.24 GiB free. Removing external
snapshots does not itself free internal storage.

An earlier, inactive 500-step exploratory checkpoint was archived from
`/Users/kelly/Documents/Codex/sim2claw-groot-n17-physical-bg-exploratory-20260719/checkpoint-500`
to
`/Volumes/cerebro-old/CodexOffload/DailyMaintenance/20260908T031400Z/sim2claw-groot-n17-physical-bg-20260719-checkpoint-500`.
Its newer 5,000-step representative remains local. All seven files (9,464,940,983
bytes), SHA-256 values, sizes, nanosecond modification times, modes and xattrs
match. Checksum rsync found no differences; no file was open. The local source
was removed only after verification, then replaced with a compatibility symlink.

Internal free space at the closing maintenance audit was 8.97 GiB and external
free space was 900.50 GiB. Values will change as experiments continue. Active
repositories, current checkpoint representatives, the newest three CodexBackups
snapshots and the active uv cache were preserved. The latest raw backup copy
still occupies space; no claim of a completely empty former backup volume.

Receipts and exact restoration instructions:
`/Users/kelly/.codex/maintenance-receipts/20260908T031400Z/ACTIONS.md`.
Source/destination manifests and failed pre-copy attempts are retained there.
To restore the checkpoint, remove only its compatibility symlink, copy the
verified external directory to its former source, and compare with
`checkpoint-source-manifest.json` before changing the external copy.

The supported snapshot operation is documented by
[Apple](https://support.apple.com/guide/disk-utility/view-apfs-snapshots-dskuf82354dc/mac).
