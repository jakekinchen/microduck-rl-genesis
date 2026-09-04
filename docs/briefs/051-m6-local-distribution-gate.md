# Brief 051 - M6 local provenance distribution gate

**Date:** 2026-09-04

## Objective

Advance the accepted 65 / 0 / 5 file inventory to the smallest safe local
distribution unit. Include only complete, license-bound, byte-identical source
records; quarantine the five terminal negatives without deleting them; and
prove deterministic byte-only validation plus library staging.

## Required Changes

- Derive an exact allowlist from accepted inventory revision `c9a610b...`.
- Bind all 65 included paths, sizes, digests, licenses, license evidence, source
  revisions/paths/digests, and the five excluded records and blockers.
- Retain a deterministic archive containing the allowlist, inventory, two
  license texts, and only the 65 complete files.
- Fail closed on missing/partial inclusion, coverage removal, digest/license/
  source drift, lifecycle promotion, archive corruption, or required-role
  promotion/removal.
- Validate and stage from an isolated exact-commit checkout using Python
  standard-library byte handling only.

## Acceptance

- Two independent generations are byte-identical to the retained archive.
- Receipt and archive manifests/digests verify exactly.
- Isolated exact-commit retrieval validates and reaches
  `staged_not_imported`; all five quarantined paths stay absent.
- Focused/adversarial/full suites, hygiene/workflow/diff gates, and empty Brev
  inventory pass; independent Reviewer accepts a scoped Executor commit.

## Stop Conditions

No publication or push. Do not import, parse, load, execute, evaluate, approve,
or activate policy bytes. Do not relabel local/smoke material as an official or
community artifact. Stop at the still-open ten-role policy manifests and the
human-owned publication boundary.
