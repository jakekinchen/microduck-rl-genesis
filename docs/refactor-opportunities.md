# Refactor and Optimization Opportunities

Generated: 2026-09-05
Repository scope: workspace inspection, offline diagnostics, browser reports, test entrypoints and CI.
Rubric: Refactor Score v1

## Executive summary

Three explicitly requested sub-agents completed separate cleanup, performance and agent-DX passes. The parent reviewed all changes, ran the integrated suite independently, exercised the browser, and corrected a benchmark metadata defect before accepting the measurements. Six improvements are implemented; five tempting changes are explicitly declined. These 11 findings are bounded tooling coverage, not an exhaustive audit of the simulator, training algorithms or historical provenance code.

The main improvements are selected-run receipt verification, fewer redundant filesystem checks, and `./scripts/duck verify`: one fast test inventory for local use, the full runner and workspace CI. Cleanup removes a recursive JSON validation pass and redundant browser state. Existing adversarial tests protect distinct behavior and were retained.

The [verification guide](workspace/VERIFICATION.md) explains the command and worktree use. [Retained review evidence](workspace/REPO_IMPROVEMENTS_20260905.json) contains exact source hashes, timings, results and preservation checks. Detailed raw profiles, baseline copies, logs and agent-only patches remain under ignored `.workspace/repo-improvements-20260905/`.

## Measured performance

Seven alternating baseline/candidate trials used 31 retained development evaluations with zero inspection errors. Every timed result matched, and one full-inventory digest was checked before warmup, across both cache groups and after timing. Cold means a fresh Inspector hash cache; filesystem caches were not cleared. These timings measure reader calls, not HTTP transfer, video decoding, full Studio startup or training speed.

| Operation | Baseline median | Candidate median | Speedup |
|---|---:|---:|---:|
| Full evaluation inventory, cold | 886.4 ms | 807.6 ms | 1.10x |
| Full evaluation inventory, warm | 276.2 ms | 201.1 ms | 1.37x |
| Selected run detail, cold | 910.3 ms | 43.7 ms | 20.82x |
| Selected run detail, warm | 300.1 ms | 42.1 ms | 7.13x |
| Selected artifact lookup, cold | 885.8 ms | 22.9 ms | 38.63x |
| Selected artifact lookup, warm | 275.6 ms | 25.5 ms | 10.82x |

The separate synthetic JSON decoder comparison measured 31.80 → 20.73 ms for 5,000 rows (1.53x). Its 1,008 valid inputs preserve exact decoded types and float bits. Sixteen malformed inputs retain exact errors; four compound-malformed inputs still reject but report numeric overflow earlier. This minor diagnostic change is disclosed rather than called fully identical behavior.

## Parent review and acceptance

- **Cleanup accepted:** inspected only the new `strict_json` hunk and point-state deletion; the pre-existing `load_trace(max_bytes=...)` changes are unchanged. Rejection of invalid numbers, exact actions, missing telemetry and HTML escaping remains covered.
- **Performance accepted after a measurement correction:** selected requests reuse the existing discovery/admission checks and still validate the entire applicable manifest, including covered siblings. The first benchmark counted inventory before timing; an independently added receipt made that metadata stale. The reviewed benchmark now rejects inventory drift and derives counts from timed results. `performance/benchmark-reviewed.json` supersedes the original `benchmark.json`.
- **DX accepted after a summary improvement:** reviewed discovery/import failure paths and requested explicit expected-failure/unexpected-success counters. All 50 original full-suite entries remain in order; the shared tooling runner is one additional entry. A source copy without a virtualenv, in a path containing spaces, passes from `/tmp`.
- **Preservation accepted:** the Git index is byte-identical to task start, pre-existing staged work remains staged, all 25 running v6 source bindings match, and the frozen contract passes. No policy, simulator, actuator, model, evaluation threshold or retained receipt was edited by this pass. The parent added only tooling support notes to the current queue/status and verification links to README/AGENTS.

## Ranked findings

| Rank | Score | Priority | Confidence | Type | Title | Recommended next step |
|---:|---:|---|---|---|---|---|
| 1 | 89 | P1 | High | Performance | R-performance-1: Verify only the requested run on individual viewer routes | Implemented and reviewed |
| 2 | 87 | P1 | High | Testability | R-dx-1: Use one fast workspace test inventory locally and in CI | Implemented and reviewed |
| 3 | 82 | P1 | High | Simplification / Performance | R-performance-2: Remove duplicate filesystem path validation work | Implemented and reviewed |
| 4 | 79 | P2 | High | Reliability | R-dx-2: Make empty discovery and skipped checks visible to agents | Implemented and reviewed |
| 5 | 77 | P2 | High | Simplification | R-slop-1: Validate finite floats while decoding | Implemented and reviewed |
| 6 | 65 | P2 | High | Simplification | R-slop-2: Read report points from the selected case | Implemented and reviewed |
| 7 | 42 | Do not prioritize | High | Architecture / Performance | R-performance-3: Do not add persistent verified-manifest caching | Retain current design |
| 8 | 38 | Do not prioritize | High | Architecture | R-dx-3: Do not replace the full simulator suite with global discovery | Retain current design |
| 9 | 30 | Do not prioritize | High | Simplification | R-slop-3: Retain small boundary and DOM helpers | Retain current design |
| 10 | 26 | Do not prioritize | High | Architecture | R-slop-4: Keep independent JSON reader boundaries | Retain current design |
| 11 | 20 | Do not prioritize | High | Testability | R-slop-5: Preserve adversarial trace tests | Retain current design |

## Top opportunities

### R-performance-1: Verify only the requested run on individual viewer routes
- **Priority:** P1
- **Score:** 89
- **Confidence:** High
- **Type:** Performance
- **Scope:** `duck_workspace/core.py:156` (`Inspector.evaluations`), `:296` (`detail`), `:325` (`artifact`); new benchmark and boundary-test files
- **Current problem:** Every detail request and every video byte-range lookup reparsed and verified all development runs. Unrelated manifests made a single retained video lookup cost approximately 0.90 seconds with a fresh Inspector.
- **Proposed change:** Implemented an optional exact run-ID filter before report parsing and verification, used by the individual detail/artifact routes. The unfiltered snapshot retains its full evaluation inventory.
- **Why this is valuable:** Selected artifact lookup fell to 22.9 ms cold/25.5 ms warm; selected detail fell to 43.7 ms cold/42.1 ms warm. Browser video range requests stop incurring unrelated integrity work.
- **Why this is simpler:** It removes unrelated work from requests without introducing persistent result caches, invalidation rules, indexes, threads, or a second admission implementation.
- **Evidence:** Seven-trial equality-checked benchmark and profiles under `.workspace/repo-improvements-20260905/performance/`; actual 31-report development inventory. The existing directory scan remains O(discovered paths), but report parsing/hash verification is limited to the requested manifest rather than all run manifests.
- **Safety plan:** Seven new boundary tests cover same-size tampering with restored mtime, deleted files/reports, changed manifests, parent-manifest sibling tampering, new runs, held-out/reserved/unindexed/traversal admission, and symlink replacement. All 31 existing workspace tests also pass, including HTTP routing/byte ranges and proof-class admission. Roll back via the saved incremental source patch; no schema or artifact migration is required.
- **Forward option-value:** Retained evidence can grow without making every individual video lookup hash the whole inventory; the benchmark remains reusable for future changes.
- **Senior judgment notes:** Discovery, visibility/schema checks, artifact allowlisting, and selected manifest validation remain shared with snapshots. Parent manifests still verify every covered sibling file. Invalid integrity remains displayable as invalid, matching baseline behavior. No performance claim is made for large trajectory decoding or training.
- **Score breakdown:**
  - Real impact: 19
  - Simplification leverage: 14
  - Safety and behavior preservation: 15
  - Evidence and confidence: 15
  - Forward option-value: 8
  - Effort-adjusted ROI: 9
  - Senior judgment bonus: 9
  - Applied caps: none
- **Recommended next step:** Implemented and reviewed.

### R-dx-1: Use one fast workspace test inventory locally and in CI
- **Priority:** P1
- **Score:** 87
- **Confidence:** High
- **Type:** Testability
- **Scope:** `scripts/verify_workspace.py:15`, `scripts/duck_workspace.py:18`, `tests/run_all.py:15`, `.github/workflows/workspace.yml`, `docs/workspace/VERIFICATION.md`
- **Current problem:** The full runner omitted all four existing workspace/diagnostic suites. CI maintained a separate four-command list, including a special discovery invocation for `test_experiment_ops.py`, whose direct invocation fails to resolve `experiment_ops`. Agents had no one-command fast suite and could reach for simulator-heavy `run_all.py` during active training.
- **Proposed change:** Implemented one explicit six-module stdlib-only inventory, exposed as `duck verify`, consumed by CI and registered once in the full runner. Added the performance agent's new seven-test module. Resolve source/tests from the script's own checkout and normalize legacy subprocess cwd to the repository root. Document the appropriate verification lanes.
- **Why this is valuable:** Existing boundary tests and new performance regressions now run together without simulator startup, package installation or environment provisioning. Local and CI workspace coverage share the same list.
- **Why this is simpler:** Four CI commands and their special-case invocation are replaced by one runner. Agents no longer need to reconstruct different invocation modes or infer which tests are cheap.
- **Evidence:** Baseline direct `tests/test_experiment_ops.py` import failure independently observed by parent; workspace suite absent from baseline `run_all.py`. Actual final runner with Python 3.12 and `-S` ran 94 tests with zero failures/errors/skips in 2.895 seconds, retained under `.workspace/repo-improvements-20260905/dx/verification-final.json` and `.log`. Both CLI entrypoints list the same suite from an unrelated temporary cwd.
- **Safety plan:** Six isolated runner regressions plus all existing tooling tests; preserve every prior `run_all.py` entry and dirty training registration. Parent independently checks baseline registration equality and a source mirror with no virtualenv. The full simulator suite was not launched.
- **Forward option-value:** New workspace suites need one registration to participate in local and CI verification.
- **Senior judgment notes:** This is a tooling coverage bug fix and small feature, not a behavior-preserving refactor. The explicit allowlist avoids importing training/simulator tests through broad discovery. No worktree manager, environment installer or agent role framework was introduced.
- **Score breakdown:**
  - Real impact: 17
  - Simplification leverage: 16
  - Safety and behavior preservation: 14
  - Evidence and confidence: 14
  - Forward option-value: 8
  - Effort-adjusted ROI: 9
  - Senior judgment bonus: 9
  - Applied caps: none
- **Recommended next step:** Implemented and reviewed.

### R-performance-2: Remove duplicate filesystem path validation work
- **Priority:** P1
- **Score:** 82
- **Confidence:** High
- **Type:** Simplification / Performance
- **Scope:** `duck_workspace/core.py:22` (`safe_path`), `:121` (`Inspector.integrity`)
- **Current problem:** `safe_path` resolved the same root twice per call. Integrity validation also called `safe_path` immediately before `digest`, which independently rechecks the path and every symlink before its hash-cache lookup. Warm profiling showed path validation dominating evaluation inspection.
- **Proposed change:** Implemented one resolved root per `safe_path` call and removed the intermediate duplicate check; manifest parsing still validates every name, and `digest` still validates every workspace path before accessing cached hashes.
- **Why this is valuable:** Warm full evaluation inspection improved from 276.2 to 201.1 ms. Matched 31-report profiling shows 33.4% fewer stat calls and 53.1% fewer path resolutions.
- **Why this is simpler:** Removes redundant resolution/validation work while keeping both the initial manifest-name boundary and the digest access boundary; no additional cache or bypass API is added.
- **Evidence:** `.workspace/repo-improvements-20260905/performance/matched-profile-counts.json`, matched warm profiles, and full-evaluation benchmark equality. Incremental source patch preserves every pre-existing dirty schema/training-counter/trajectory change.
- **Safety plan:** All existing workspace tests and seven new selected-request boundary tests pass. `digest`'s size/mtime/ctime cache key is unchanged; symlink and same-size/restored-mtime tampering are explicitly exercised.
- **Forward option-value:** Retains one clear secure digest boundary for future receipt readers.
- **Senior judgment notes:** The remaining manifest validation is intentionally retained, including duplicate-entry, malformed-line, traversal, and symlink rejection. Path safety was not replaced by string-prefix checks or a stale filesystem cache.
- **Score breakdown:**
  - Real impact: 12
  - Simplification leverage: 17
  - Safety and behavior preservation: 14
  - Evidence and confidence: 15
  - Forward option-value: 6
  - Effort-adjusted ROI: 9
  - Senior judgment bonus: 9
  - Applied caps: none
- **Recommended next step:** Implemented and reviewed.


## Good batch candidates

### R-dx-2: Make empty discovery and skipped checks visible to agents
- **Priority:** P2
- **Score:** 79
- **Confidence:** High
- **Type:** Reliability
- **Scope:** `scripts/verify_workspace.py:25`, `tests/test_verification_runner.py`, `.github/workflows/workspace.yml`
- **Current problem:** A unittest discovery command can exit successfully with zero tests. Generic successful-process summaries also hide optional missing coverage unless agents inspect the underlying unittest output. Existing tests have an optional Node syntax check, so this is a real current distinction.
- **Proposed change:** Implemented required nonzero discovery per registered module, summary counters including expected failures/unexpected successes, explicit `passed_with_skips` status and retained skip reasons, and optional JSON on both success and test failure. CI retains that small result as an artifact. Standard unittest expected-failure semantics are preserved.
- **Why this is valuable:** Automated callers can distinguish a passing exercised suite, a partial suite, discovery drift and actual failures while retaining interpreter/checkout context. Missing test coverage cannot silently become a pass.
- **Why this is simpler:** One result shape and conventional nonzero exits replace manual terminal-output interpretation; standard unittest remains the execution engine.
- **Evidence:** Regression fixtures exercise success, test failure, import error, missing/empty modules, skips and unexpected successes in isolated subprocesses. Running the real five-module pre-performance inventory from `/tmp`, with site packages disabled and Node absent, produced 87 executed tests and `passed_with_skips`, preserving the exact optional-Node reason in `.workspace/repo-improvements-20260905/dx/verification-no-node.json`; ordinary execution produced zero skips.
- **Safety plan:** The six new test methods use tiny temporary suites and never recursively invoke the complete workspace suite. Failure and import-error fixtures must produce nonzero exit plus valid JSON, not only a printed traceback. No arbitrary suite CLI or execution plugin mechanism was added.
- **Forward option-value:** Future agent and CI consumers can assess proof scope without parsing localized test logs.
- **Senior judgment notes:** This is a reliability feature. JSON contains aggregate failure/error counts and skip details; full failure tracebacks remain in the terminal/CI log. No claim of individual pass counts is inferred from subtest failure counts.
- **Score breakdown:**
  - Real impact: 15
  - Simplification leverage: 11
  - Safety and behavior preservation: 14
  - Evidence and confidence: 14
  - Forward option-value: 8
  - Effort-adjusted ROI: 8
  - Senior judgment bonus: 9
  - Applied caps: none
- **Recommended next step:** Implemented and reviewed.

### R-slop-1: Validate finite floats while decoding
- **Priority:** P2
- **Score:** 77
- **Confidence:** High
- **Type:** Simplification
- **Scope:** `experiment_ops/compare.py:21`, `strict_json()`
- **Current problem:** The decoder walked every decoded dictionary, list, and scalar a second time solely to reject exponent-overflow floats such as `1e999`. The standard decoder already exposes a callback for each floating-point token.
- **Proposed change:** Use `json.loads(parse_float=finite_float)` and remove the recursive `finite()` traversal. Keep the existing duplicate-key and nonfinite-constant callbacks.
- **Why this is valuable:** Trace rows include many numeric values and optional nested telemetry. Their finite-float rule now lives at the moment values enter the decoded object. A small synthetic decode benchmark also measured a benefit.
- **Why this is simpler:** Removes one recursive traversal, its dict/list branches, and five net source lines. No shared parser framework or cache was added.
- **Evidence:** `.workspace/repo-improvements-20260905/slop/json-differential.json` records 1,008 valid inputs with identical decoded types and float64 bits, 16 invalid inputs with identical errors, and four compound-malformed inputs still rejected with earlier overflow diagnostics. The existing 23-test trace/activity suite passes. Seven alternating rounds of 5,000 representative synthetic rows measured median baseline 31.80 ms versus candidate 20.73 ms (1.53x decode speedup).
- **Safety plan:** Existing overflow, duplicate-key, signed-zero, action-equality, missing-telemetry, report-escaping and bounded-output tests pass. Differential checks cover nested containers, underflow, large finite values, arbitrary integers, UTF-8/16/32, invalid encoding, malformed JSON, and excessive nesting. The retained baseline and standalone patch provide a scoped rollback.
- **Forward option-value:** New telemetry fields no longer require a second recursive validation walk. The guard remains local to the trace reader.
- **Senior judgment notes:** This is behavior preserving for valid values and the reject/accept boundary tested here; invalid diagnostic precedence is an explicit small behavior change. `{"x":1e999,"x":0}` reports `nonfinite numeric value` instead of `duplicate JSON key: x`; analogous nonfinite-constant, malformed-syntax, and nested-duplicate examples also reject earlier. Preserving the old error ordering would require extra state solely for doubly malformed input and was rejected by the parent. The benchmark is a synthetic decoder microbenchmark, not an end-to-end training or Studio claim. `load_trace()` and all comparison code remain byte-identical to the entry copy, including pre-existing user changes.
- **Score breakdown:**
  - Real impact: 11/20
  - Simplification leverage: 15/20
  - Safety and behavior preservation: 14/15
  - Evidence and confidence: 14/15
  - Forward option-value: 5/10
  - Effort-adjusted ROI: 9/10
  - Senior judgment bonus: 9/10
  - Applied caps: none; the diagnostic precedence change is disclosed
- **Recommended next step:** Implemented and reviewed.

### R-slop-2: Read report points from the selected case
- **Priority:** P2
- **Score:** 65
- **Confidence:** High
- **Type:** Simplification
- **Scope:** `experiment_ops/report.js:10`, `drawPath()` at line 17
- **Current problem:** `plotPoints` was mutable global state assigned from `current.points` on every draw, read only inside that same draw, and otherwise redundant with the selected case.
- **Proposed change:** Delete the global alias and use `current.points` directly for bounds and SVG paths.
- **Why this is valuable:** Small cleanup prevents a second retained variable from suggesting that point selection has an independent lifetime or source.
- **Why this is simpler:** One global and its synchronization assignment disappear; no new helper or state is introduced.
- **Evidence:** Static call-site inspection found exactly one assignment and two reads inside `drawPath()`. Existing JavaScript syntax check passes. Parent independently exercised the actual report in a browser: two SVG paths/cursors, first-difference jump to 0.060 s/0.005 m, End scrub to 0.100 s, missing-position case with unknown telemetry/disabled jump, and restored paths on switching back. Parent reported no browser errors or warnings.
- **Safety plan:** Tiny diff plus existing syntax check and the parent's browser interaction verification. The retained original `report-baseline.js` and scoped patch support rollback.
- **Forward option-value:** Case selection remains the single owner of point data.
- **Senior judgment notes:** This is a modest batch cleanup, not a material performance claim or justification for reformatting the whole viewer. SVG rendering, missing-telemetry gaps, transforms, and scrubbing behavior were preserved.
- **Score breakdown:**
  - Real impact: 4/20
  - Simplification leverage: 13/20
  - Safety and behavior preservation: 15/15
  - Evidence and confidence: 14/15
  - Forward option-value: 2/10
  - Effort-adjusted ROI: 8/10
  - Senior judgment bonus: 9/10
  - Applied caps: none; removes state rather than changing formatting
- **Recommended next step:** Implemented and reviewed.

## Research-first candidates

No unmeasured simulator or training optimization was implemented. Walking v6 was running at task entry and binds 25 source files; all remain unchanged. Its own run record reached completed during this review. Broader runtime work needs its own baseline, suitable idle compute and lane-specific verification. No task-quality or physical-transfer improvement is claimed here.

## Do not refactor yet

### R-performance-3: Do not add persistent verified-manifest caching
- **Priority:** Do not prioritize
- **Score:** 42
- **Confidence:** High
- **Type:** Architecture / Performance
- **Scope:** `duck_workspace/core.py` (`Inspector.integrity`, `Inspector.evaluations`)
- **Current problem:** Cold hashing remains the largest cost when intentionally inspecting every retained evaluation; caching whole verified results might appear to remove it.
- **Proposed change:** Defer. Keep the existing per-file size/mtime/ctime hash cache and re-read manifests/admission state on each request.
- **Why this is valuable:** Protects immediate detection of added/deleted reports, manifest changes, parent-manifest sibling tampering, and symlink replacement while the repository is actively changing.
- **Why this is simpler:** Avoids a new cache, dependency graph, invalidation policy, or filesystem watcher. Selected-run inspection already removes the high-impact redundant work.
- **Evidence:** Boundary tests demonstrate state changes between calls. An independent task added a 31st receipt during this work; the matched profile immediately discovered it. The measured selected-route wins do not need stale state.
- **Safety plan:** Any future proposal must show invalidation correctness and measured benefit beyond the current implementation before adding retained verified state.
- **Forward option-value:** Preserves an understandable inspection boundary while receipt formats and experiment workflows continue evolving.
- **Senior judgment notes:** Do not sacrifice corruption visibility for UI speed. Live TensorBoard curves and running simulator sources were outside this scoped change; no unmeasured optimization is claimed there.
- **Score breakdown:**
  - Real impact: 12
  - Simplification leverage: 0
  - Safety and behavior preservation: 3
  - Evidence and confidence: 8
  - Forward option-value: 4
  - Effort-adjusted ROI: 7
  - Senior judgment bonus: 8
  - Applied caps: none (raw score already below applicable caps)
- **Recommended next step:** Retain current design.

### R-dx-3: Do not replace the full simulator suite with global discovery
- **Priority:** Do not prioritize
- **Score:** 38
- **Confidence:** High
- **Type:** Architecture
- **Scope:** `tests/run_all.py`, simulator tests, setup scripts
- **Current problem:** The full runner has a long manual list and mixed legacy skip rules, which invites replacing it with one generic discovery or environment-management framework.
- **Proposed change:** Defer the rewrite. Preserve its explicit subprocess isolation and all existing registrations. Keep the new fast tooling lane bounded and additive.
- **Why this is valuable:** Avoids repeated Genesis initialization in one process, unapproved simulator activity and changes to frozen-source/evaluator behavior while walking-v6 training is active.
- **Why this is simpler:** Does not add a profile registry, dependency probing framework, generic worktree provisioner or role loop to solve a small workspace-test coverage gap.
- **Evidence:** `tests/run_all.py:1` explicitly documents Genesis's process-initialization restriction. Current `TRAINING_ACTUALIZATION.md` retains the active v6 run and source-preservation requirements. Read-only `duck doctor` reported runtime/contract/BAM readiness, not permission to run broader simulation.
- **Safety plan:** Any later broader runner change should inventory exact startup, dependency and skip contracts first, and run real runtime verification only when compute is available and authorized.
- **Forward option-value:** Retains a clear boundary for a future separately scoped runtime cleanup.
- **Senior judgment notes:** There is no observed worktree-setup failure justifying a new setup workflow. The current script-location root resolution and explicit interpreter command are sufficient for the requested fast tests.
- **Score breakdown:**
  - Real impact: 5
  - Simplification leverage: 4
  - Safety and behavior preservation: 4
  - Evidence and confidence: 5
  - Forward option-value: 4
  - Effort-adjusted ROI: 6
  - Senior judgment bonus: 10
  - Applied caps: none
- **Recommended next step:** Retain current design.

### R-slop-3: Retain small boundary and DOM helpers
- **Priority:** Do not prioritize
- **Score:** 30
- **Confidence:** High
- **Type:** Simplification
- **Scope:** `experiment_ops/compare.py:number/exact_vector`, `experiment_ops/report.js:node/textCell`, `duck_workspace/server.py:send_content_headers/reply`
- **Current problem:** The tempting proposal is to classify short functions as unnecessary wrappers. No concrete defect supports that removal here.
- **Proposed change:** Retain the helpers.
- **Why this is valuable:** `number()` distinguishes booleans from finite numeric telemetry, `exact_vector()` deliberately preserves signed zero, report node helpers use safe text insertion, and shared response headers consistently apply security controls.
- **Why this is simpler:** Inlining would duplicate the same domain rules at multiple call sites and scatter security headers.
- **Evidence:** `tests/test_experiment_ops.py:60` and `:66` protect exact actions and signed zero; `:138` and `:146` protect HTML embedding. `tests/test_duck_workspace.py:test_http_range_and_read_only_boundary` exercises range serving and host restrictions.
- **Safety plan:** Preserve helpers and their existing behavioral tests.
- **Forward option-value:** Domain rules remain small and localized.
- **Senior judgment notes:** Line count alone is not complexity. Short helpers with shared semantics are useful here.
- **Score breakdown:**
  - Real impact: 0/20
  - Simplification leverage: 0/20
  - Safety and behavior preservation: 3/15
  - Evidence and confidence: 5/15
  - Forward option-value: 2/10
  - Effort-adjusted ROI: 10/10
  - Senior judgment bonus: 10/10
  - Applied caps: 40 for aesthetic-only removal; raw score is lower
- **Recommended next step:** Retain current design.

### R-slop-4: Keep independent JSON reader boundaries
- **Priority:** Do not prioritize
- **Score:** 26
- **Confidence:** High
- **Type:** Architecture
- **Scope:** `experiment_ops/compare.py:strict_json`, `duck_workspace/exchange.py:_json`, `duck_workspace/core.py:read_json`
- **Current problem:** Similar JSON helpers invite a cross-package utility. Their semantics and authority boundaries differ.
- **Proposed change:** Retain local readers; reuse the simple decoder-hook idiom without introducing a shared import dependency.
- **Why this is valuable:** Exchange ingestion has separate encoding/nesting normalization and bounded-regular-file requirements; the core reader is an independent evidence projection. A generic utility would need configuration flags to preserve those distinctions.
- **Why this is simpler:** Avoids a new package or configurable parsing layer for a few short helpers.
- **Evidence:** `_json()` in exchange already uses a finite-float decoder and translates Unicode/recursion failures; trace validation has its own error messages and load constraints. `read_json()` currently has a different size/inspection contract.
- **Safety plan:** Keep existing focused suites and package boundaries. Consider consolidation only if a shared contract is deliberately established.
- **Forward option-value:** Each boundary can harden without changing unrelated consumers.
- **Senior judgment notes:** Shared syntax does not establish a shared contract. No production code outside assigned files was changed.
- **Score breakdown:**
  - Real impact: 1/20
  - Simplification leverage: 1/20
  - Safety and behavior preservation: 2/15
  - Evidence and confidence: 5/15
  - Forward option-value: 1/10
  - Effort-adjusted ROI: 6/10
  - Senior judgment bonus: 10/10
  - Applied caps: 60 for adding abstraction without sufficient deleted complexity; raw score is lower
- **Recommended next step:** Retain current design.

### R-slop-5: Preserve adversarial trace tests
- **Priority:** Do not prioritize
- **Score:** 20
- **Confidence:** High
- **Type:** Testability
- **Scope:** `tests/test_experiment_ops.py`
- **Current problem:** Similar tiny trace fixtures may look repetitive, but the tests enforce distinct failure boundaries rather than mirroring implementation steps.
- **Proposed change:** Keep them. Do not replace separate signed-zero, missing-action, mismatched-time, malformed-input, and safe-embedding checks with a smaller happy-path test.
- **Why this is valuable:** These cases prevent incomplete or different evidence from acquiring a false identical-action classification.
- **Why this is simpler:** Existing fixture helpers already remove setup duplication; further consolidation would hide the rule each test protects.
- **Evidence:** All 23 tests finish in roughly 0.2 seconds locally and require no simulator/GPU. The assertions cover observable classifications, preserved raw values, rejected inputs, and filesystem outcomes.
- **Safety plan:** Retain the current suite. Additional one-off differential evidence lives under ignored `.workspace/`, avoiding a new permanent test solely for the small alias cleanup.
- **Forward option-value:** Regression failures remain named after the evidence rule that failed.
- **Senior judgment notes:** No useless tests were substantiated in this assigned scope. This is not a repo-wide claim about every training/provenance test.
- **Score breakdown:**
  - Real impact: 0/20
  - Simplification leverage: 0/20
  - Safety and behavior preservation: 1/15
  - Evidence and confidence: 4/15
  - Forward option-value: 0/10
  - Effort-adjusted ROI: 5/10
  - Senior judgment bonus: 10/10
  - Applied caps: 40 for aesthetic-only test reduction; raw score is lower
- **Recommended next step:** Retain current design.

## Cross-cutting themes

Remove work and duplicate state before adding caches or frameworks. Keep evidence admission shared across routes. Treat missing telemetry, skipped checks and zero discovered tests as different outcomes. Preserve short helpers when they own an actual boundary. A visually repetitive test is useful when it rejects a distinct false claim.

## Verification strategy and executed results

| Verification | Observed result |
|---|---|
| Parent `./scripts/duck verify` | 94 tests; zero failures, errors, skips or discovery errors; 2.902 s |
| Parent no-venv source copy, path with spaces, invoked from `/tmp` | 94 tests passed; no skips |
| Agent Python 3.12 with site packages disabled (`-S`) | 94 tests passed; no skips |
| Optional Node unavailable, from `/tmp` before performance-suite registration | 87 tests; explicit one-check skip, `passed_with_skips` |
| Runner negative fixtures | Import errors, assertion failure, missing/empty discovery and unexpected success return failure and retain JSON; skipped reason remains explicit |
| Parent frozen-contract check | Passed |
| Python compilation, both viewer JS syntax checks, `git diff --check` | Passed |
| Full-suite registration comparison against reconstructed task-start source | All 50 existing entries preserved; one new tooling entry |
| Active walking v6 sources | 25/25 hashes match |
| Browser comparison report | Two paths/cursors, jump to 0.060 s/0.005 m, End scrub to 0.100 s, missing-data case and return switch pass |
| Browser Duck Lab | Selected walking report loads; 12-second retained video reaches playable state and advances; case switching and missing comparison-video message work; no observed console errors/warnings |

Future tooling changes should run `./scripts/duck verify`; JSON is optional through `--json-out .workspace/verification.json`. Browser-affecting changes still need browser interaction and retained-video checks. Benchmark the current source against an explicitly saved baseline using `scripts/benchmark_workspace.py`; the command refuses changed evidence instead of publishing inconsistent measurements.

The broad simulator suite was not run while another task owns active training. No remote CI run was dispatched, no commit or push was made, and no paid compute, hardware or third-party contact was used. Temporary browser QA tabs and the two local QA servers were closed. Walking v6 completed independently during this review, with all 25 source bindings still matching. Its task owns subsequent behavioral evaluation. Concurrent changes outside this audit were observed in `duck_workspace/web/index.html`, `scripts/evaluate_walking_heading.py`, `scripts/probe_walking_backend.py` and `tests/test_walking_heading.py`; they were preserved and are not attributed to these agents.

## Appendix: subagent coverage

| Subagent scope | Areas inspected | Findings returned | Gaps |
|---|---|---:|---|
| Slop audit | Offline JSON comparison, report renderer/JS, HTTP helpers, adversarial tests | 5 | No exhaustive training or historical provenance audit |
| Performance | Receipt inventory, detail/artifact admission, path/digest checks, profiles and benchmarks | 3 | No training throughput, TensorBoard or video-decoding measurement |
| Agent DX | Test inventory, CLI integration, CI, fresh checkout/cwd behavior, truthful result reporting | 3 | No new worktree provisioner or simulator-wide runner rewrite |

Parent-owned integration: README/AGENTS entry points, support notes in GOAL/TRAINING_ACTUALIZATION, the ranked report and durable evidence JSON. The three agent reports and incremental patches remain under the ignored task evidence directory for review against the pre-existing dirty checkout.
