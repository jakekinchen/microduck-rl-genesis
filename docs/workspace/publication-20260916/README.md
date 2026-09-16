# September 16 repository and evidence publication

This snapshot supports the [process review](../PROCESS_REVIEW_20260916.md).
It is research/development evidence, **not a policy release or physical
acceptance**. The repository's `origin` is
[`jakekinchen/microduck-rl-genesis`](https://github.com/jakekinchen/microduck-rl-genesis);
`Macmachi/microduck-rl-genesis` is a separate upstream remote. Publication targets
origin explicitly, including commands that would otherwise default to upstream.

## Where the data lives

- **Git:** source, configurations, protocols, readable result receipts, plots,
  current status, dated history and this publication manifest.
- **[Evidence release](https://github.com/jakekinchen/microduck-rl-genesis/releases/tag/process-evidence-20260916):**
  one gzip-compressed tar stream split into ordered 1 GiB parts. It contains
  retained experiment/receipt/output/training-log files, including dereferenced
  external-drive directories. Identical byte content/modes use tar hardlinks
  to reduce duplicated frozen source/model/checkpoint storage.
- **[archive.json](archive.json):** exact file/byte counts, ordered part names,
  SHA-256 digests and catalog digest. **[files.jsonl.gz](files.jsonl.gz)** records
  every published payload path, size, hash, mode and original mtime.
- **[external-links.json](external-links.json):** original local path mapping.
  Git preserves the historical symlinks; the archive contains their real files
  at repository-relative paths. A bare clone does not resolve local drive links.

The inventory covers `experiments/`, `receipts/`, `outputs/` and `logs/` as they
existed for this snapshot. It includes failed and interrupted experiments,
checkpoints and raw traces; a filename or a checksum does not confer acceptance.
Closed V62–V66 payloads are unchanged: see
[closed-evidence-review.json](closed-evidence-review.json). Historical closure
hashes of GOAL/queue describe their original status snapshot, not today's docs.

Private `.workspace/` session extracts, credentials, caches, environment installs,
and unrelated repositories are outside the publication. Regenerable Python
caches and the separately installed MuJoCo 3.10 runtime directory are excluded;
their source/version provenance remains in the experiment record. One captured
editor UI-state file (`outputs/laser-course-20260913/compilation-before.json`)
contained an editor boot token and is withheld in full. Its original remains
local; it is not robot experiment evidence. The exclusion list is
[excluded-generated-paths.json](excluded-generated-paths.json). No original
experiment payload was edited to redact, normalize or shrink this release.

Seventy-seven additional manifest-bound training/test log copies (2,175,711
bytes) under `receipts/.../retained/.workspace/` are published in Git. These
scoped receipt copies are distinct from the private root `.workspace/` folder;
the archive's hidden-directory exclusion does not prevent retrieving them.

## Download, verify and restore

Use Python 3.12 and GitHub CLI. Download into a directory with sufficient space:

```sh
gh release download process-evidence-20260916 \
  --repo jakekinchen/microduck-rl-genesis \
  --dir /path/to/downloads/microduck-evidence
python3 scripts/review_evidence_archive.py \
  --parts-dir /path/to/downloads/microduck-evidence
```

The verifier checks each part, the catalog, every archived regular file and
hardlink, exact coverage and the gzip trailer. It imports no simulator and
starts no training. To restore, provide an **absent or empty** destination:

```sh
python3 scripts/review_evidence_archive.py \
  --parts-dir /path/to/downloads/microduck-evidence \
  --extract-to /path/to/restored-evidence
```

Do not extract over the working repository or its external-drive symlinks.
Restored duplicate files share hardlinks; treat this directory as immutable and
copy files before changing them for another experiment. Restoration makes the
original files available under `experiments/`, `receipts/`,
`outputs/` and `logs/` in the new directory. The read-only verifier creates only
the requested output/report; it does not remap local absolute paths in frozen
XML, commands or receipts. Executable reproduction still requires the documented
runtime/BAM pins and explicit path mapping in a separate checkout. Historical
source-bound path strings remain original; their presence is not a portability
claim. The workspace viewer also refuses external symlinked evidence.

For a small review, read the Git result summaries first. Decompressing the
catalog with `gzip -dc docs/workspace/publication-20260916/files.jsonl.gz` locates
the raw file behind a disputed claim. Full extraction requires substantial disk
space; `archive.json` gives both logical and deduplicated sizes. No paid storage
or compute is required by the publication itself.

GitHub documents release assets under 2 GiB with no aggregate release size or
bandwidth limit; the 1 GiB split stays below that per-file limit.
[GitHub release documentation](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases).

## Verification scope

Workspace tooling, fresh-checkout tooling, Python syntax, archive content,
closed-receipt preservation, staged source scanning and remote publication are
recorded in the publication verification files. Secret scanning is bounded:
the history scanner checks unpublished commits, while directory scans skip
files larger than 5 MB and do not establish exhaustive absence of secrets in
binary/large numerical payloads. The discovered editor-state file is excluded.

Some unchanged source-bound reports, third-party snapshots and generated SVGs
contain original trailing whitespace or terminal blank lines. Their bytes are
preserved rather than invalidating recorded hashes for cosmetic cleanup.
Software checks and archive integrity do not replace behavior acceptance.

CI verifies all Git-resident receipt bytes and matches archive-only references
against the checksummed catalog. It reports these counts separately; it does
not download or claim to reverify the 14.9 GB archive on every push. Full payload
verification is [archive-verification.json](archive-verification.json), and can
be repeated with the command above. Seventeen formatting exemptions are bound
to exact file hashes in [immutable-formatting.json](immutable-formatting.json):
future edits fail the exemption check instead of silently bypassing whitespace
validation. The initial sync's legacy CI failure and its publication-layout
correction are part of the process record, not a failed robotics result.
