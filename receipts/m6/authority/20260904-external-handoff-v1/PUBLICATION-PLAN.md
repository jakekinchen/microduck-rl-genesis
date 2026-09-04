# Preregistered publication plan - not authorized or executed

## Frozen inputs

- Source repository: `https://github.com/jakekinchen/microduck-rl-genesis.git`
- Exact accepted source revision:
  `f22c799a6fc81375588f899da15468087731219d`
- Expected pre-publication `origin/main`:
  `3257775beeeb8b1df646dd295bf84e34967e42ec`
- Archive: `microduck-complete-assets-v2.tar.gz`
- Archive SHA-256:
  `0c92aa28888754d9b6c07a6d92f45f06fae8e7564ad76482ec1aa06a385300d9`
- Archive size: `9272643`
- Source tag/revision name: `m6-complete-assets-v2-0c92aa28`
- Hugging Face revision/tag name: `m6-complete-assets-v2-0c92aa28`
- Hugging Face repository id: **human must supply and confirm before action**

## Authority and credentials required

Execution requires a new explicit human authorization that names both the
GitHub repository/tag action and exact Hugging Face repository. It also requires
authenticated GitHub write/tag/release access and a Hugging Face token with
write access to that exact repository. Credentials remain user-controlled and
must not be copied into receipts, logs, environment dumps, or commits.

## Preregistered sequence

1. Re-read `GOAL.md`, the Reviewer 052 acceptance, and this packet. Stop if the
   exact authorization, destination, or credentials are absent.
2. Require a clean checkout at exact `f22c799...`; verify the archive SHA/size,
   v2 receipt manifest, 65-file allowlist, five-file quarantine, full tests,
   and empty Brev inventory.
3. Fetch GitHub without mutation. Require `origin/main` to remain exactly
   `3257775...`, require it to be an ancestor of `f22c799...`, and require the
   destination tag not to exist. Any drift stops the plan for review.
4. With explicit authority only, publish the exact source revision and create
   immutable tag `m6-complete-assets-v2-0c92aa28`. Do not add or rewrite files,
   force-push, move an existing tag, or publish the five quarantined files as
   part of the distribution artifact.
5. With separately confirmed Hugging Face destination and authority, upload
   only the v2 archive, its `SHA256SUMS`, `SEARCH_RESULT.json`,
   `EVIDENCE_BOUNDARY.txt`, and canonical allowlist under revision/tag
   `m6-complete-assets-v2-0c92aa28`.
6. Re-fetch the Git tag into a fresh clone and require its peeled commit to be
   exact `f22c799...`. Re-download every Hugging Face file by immutable revision
   into a fresh directory, verify exact digests/size/manifest coverage, and run
   byte-only validation to `staged_not_imported` with no `demo/` or `policies/`.
7. Only after successful re-fetch may a human-authorized release page or model
   card link to the immutable objects. This does not create policy approval,
   activation, official/community policy-manifest completeness, or task proof.

## Stop and rollback conditions

Stop before mutation on remote-head/tag drift, missing authority, missing
credentials, destination ambiguity, digest/size mismatch, quarantine leakage,
test failure, or any attempt to promote lifecycle state. Never overwrite or
move an immutable tag. If an upload is incomplete or re-fetch fails, do not
announce/promote it; preserve local and remote receipts, mark the revision
quarantined, and obtain human direction before any deletion or retraction.
