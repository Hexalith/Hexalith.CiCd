---
title: 'Nightly cross-module duplicate scan'
type: 'feature'
created: '2026-11-15'
status: 'done'
baseline_revision: '93e3d33b6436d9e8f215a7556b0beb0368107b56'
review_loop_iteration: 0
followup_review_recommended: true
context:
  - /home/administrator/projects/hexalith/cicd/_bmad-output/specs/spec-cicd/enforcement.md
  - /home/administrator/projects/hexalith/cicd/_bmad-output/planning-artifacts/architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md
warnings: [oversized]
deferred:
  - summary: >-
      Verify eligible-source accounting can distinguish legitimate token-floor filtering from unexpectedly missing substantial detector inputs.
    evidence: |-
      The report validator accepts coherent all-zero counters. Actual pinned jscpd 5.4.3 reports zero sources for two comment-heavy 100-line files below the token floor, while substantial 100-line copies report two sources and one clone.
      No engine failure on an eligible substantive corpus was reproduced. Establish the pinned engine's eligible-source counting contract and reproduce an unexpectedly omitted eligible input before introducing a coverage invariant.
      Evidence: _bmad-output/implementation-artifacts/story-9-parent-counter-check.log. This is review finding B10, unverified, rather than an observed production defect.
    location: >-
      tools/scan.py:findings
    severity: high (unverified)
---

<intent-contract>

## Intent

**Problem:** Nightly does not detect generic code copied between modules' custom actions and their called scripts (CAP-9). Such code belongs in Builds.

**Approach:** Add a secretless jscpd scan after publish-ready. Scan each registered module's live main using CiCd's committed detector policy, report actionable cross-module fragments, and fail the night without suppressing the Builds bump.

## Boundaries & Constraints

**Always:** The registry is committed `setup/*.yml`, including dormant action directories and modules not yet adopted; exclude Builds and reject invalid/colliding registrations or capacity above 17. Fetch module main anonymously through hardened git, recording full canonical revisions. Cover YAML, shell, PowerShell and Python under `.github/actions/**` and recursively called local scripts, including local Python imports. Resolve ordinary workspace/action-relative literal paths and report unresolved local-script calls explicitly rather than silently claiming complete coverage. Treat module files as data; isolate each module's failure and continue healthy siblings. Use central committed config and integrity-pinned jscpd 5.4.3, npm lock, `npm ci --ignore-scripts` then `npm audit signatures`, and a locked PEP 723 Python entry point (Python >=3.12). Detector/config/report/clone/discovery failures fail visibly. Preserve main-only, qualification bypass and cancellation behavior. Use `run-with-temp` for disposable builds/tests/verification, with scratch beneath its TMPDIR and retained logs outside it.

**Never:** Execute module code, initialize submodules, read pinned module checkouts as the scan source, consume module detector configuration/ignores, give scan App/publish credentials, hide duplicates through module/language exclusions, fail merely for repetition within one module, or block bump/keepalive on an ordinary upstream failure. Do not adopt modules, change Builds, delivered refs or credentials, or hoist/delete module code in this story.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
| --- | --- | --- | --- |
| Cross-module fragment | Substantial identical action/called-script code in two or three modules | Fail; name each implicated module, original file and line ranges plus code to move | Report survives and bump remains eligible |
| Same-module repetition | Multiple copies within only one module | Pass unless another error occurs | Never use total duplication percentage as the gate |
| Language and reachability | YAML/bash/PowerShell/Python; dormant actions, nested calls and local Python imports | All reachable supported files enter detection with original paths | Missing/unresolvable local calls fail with source diagnostics |
| Current remote authority | Live main differs from pinned checkout; unregistered repository has copies | Inspect only registered remote main at recorded full SHAs | Never fall back to a stale checkout |
| Policy dominance | Module supplies jscpd config, ignore files or suppression directives | Central policy determines detection; module policy cannot hide the clone | Unsupported/incomplete detector output fails |
| Empty scope | Empty registry or registered module with no actions | Explicit successful zero-scope report | Distinguish from failed fetch/discovery |
| Partial failure | One remote unreadable, invalid action, unsafe path/symlink/gitlink or oversized input | Failed module reported; healthy siblings still scanned and their findings retained | Whole scan exits nonzero |
| Tool/report failure | Install/signature/version/detector failure or malformed/outside-root report paths | No false clean result; failed report and diagnostic | Nonzero with durable conservative job output |
| Threshold calibration | Short shared boilerplate versus substantial clones in all four languages; Memories/Tenants tooling | Committed tuned thresholds reject substantial copies and avoid trivial boilerplate; document measured scope and noise | Do not claim empty live action corpora prove absence of future noise |
| Nightly continuation | Publication or scan failed; cancellation or qualify-bump dispatch | Ordinary failures remain red while scan/bump/keepalive progress in order; cancellation/qualification skip production scan | Missing scan controller still leaves failure evidence |

</intent-contract>

## Code Map

- `.github/workflows/nightly.yml:1446` — explicit story-9 boundary. Add scan after publish-ready; bump needs both publish-ready and scan while retaining explicit `!cancelled()` eligibility. Keepalive remains independent of ordinary failures. Use canonical nonhidden sibling artifact paths, pinned actions, no checkout credential persistence or caches.
- `tools/delivery_runtime.py:103`, `:148`, `:355`, `:458` — stdlib hardened anonymous environment, `Git` trees/blobs, `Transport.module` shallow live-main fetch and committed `registry`. Reuse these without importing the renderer or privileged controllers. `Git.blob` enforces regular blobs and 2 MiB; use bounded aggregate/export/report limits too. Existing transport has fixed GitHub origins; test injection stays at the Python boundary.
- `tools/validate.py:43` — alternative anonymous clone pattern, but importing it loads global/render dependencies; prefer the stdlib boundary above.
- `tools/check_global.py:383` — automatically executes every locked `tools/tests/test_*.py`; no registration change needed. Shared global gate must remain unchanged.
- `tools/tests/test_nightly_workflow.py:454` — `PostReleaseWorkflow` executes parsed real job/step conditions and substituted controller I/O; extend it for scan command, permissions, setup-node/setup-uv and artifacts. Do not write source-text workflow assertions.
- `tools/tests/delivery_support.py`, `nightly_support.py`, `bump_support.py` — real disposable Git remotes and workflow fixture patterns; support data injection without production remote configurability.
- No existing superproject npm package or detector config. Add a dedicated npm tool directory, its package/lock, and CiCd config. jscpd 5.4.3 is Rust distributed via npm optional platform packages; install works with scripts disabled. Formats: `yaml`, `bash`, `powershell`, `python`. JSON has `duplicates[]` with `fragment`, `lines`, `tokens`, `format`, `firstFile`/`secondFile` each with name/start/end locations. Explicit config, `absolute`, `skipLocal`, `noGitignore` are available. Independently validate that each reported endpoint is a staged known file from a distinct module; do not trust detector percentages or arbitrary paths. Disable source directives if detector supports them, otherwise neutralize their ignore effect without losing source locations.
- `docs/nightly.md`, `setup/README.md` — document actual chain, scan policy/call discovery, failure reports and tuning. Existing 24 stories all done; production setup registry intentionally empty. Relevant continuity: original jobs 55/330/55 minutes; bump/push/observation/keepalive 55/55/105/15; qualified GITHUB_TOKEN bump transport stays unchanged.
- Anonymous investigation: Memories main `2c2e9b58990638ededf22e8e67ff5c12de75b434`, Tenants main `d89f234c4f020373aaabe0e3699ecdb5097b1079` have no action entries. Their unrelated Python tooling must not be pulled into scope to manufacture noise. Detector reference: https://jscpd.dev/reference/config-file and https://jscpd.dev/reference/reporters/json .

- `_bmad-output/implementation-artifacts/story-9-detector-investigation.md` — retained primary-tool investigation and empirical calibration. Start with weak mode, minLines 10/minTokens 50; 100 tokens misses substantial shell/PowerShell copies. Actual 97-file broader Python diagnostic found no cross-module copies at captured revisions; no module exclusions are justified. Read this evidence before final tuning.

## Tasks & Acceptance

**Execution:**

- [x] `tools/jscpd/package.json`, `tools/jscpd/package-lock.json`, `.jscpd.json` — add exact detector/dependency integrity pins and central format/threshold policy; validate actual signature verification and version before detection. Keep installation and outputs in private disposable scratch.
- [x] `tools/scan.py`, `tools/scan.py.lock` (and a focused helper if needed) — implement committed registry, anonymous current-main snapshots, bounded nonexecuting action/call discovery and isolated staging; run central jscpd over module roots; independently validate report endpoints; emit deterministic token-free report, full source SHAs and actionable code/location diagnostics. Fail closed while retaining healthy observations and an explicit empty-scope result.
- [x] `tools/tests/test_scan.py`, adjacent `.py.lock`, fixture helper if useful — test every matrix row through real temporary Git repositories and actual pinned detector integration. Include all four formats, transitive calls/imports, same-module repetition beside cross-module copies, module config/ignores/directives, invalid outputs, bad paths and empty scope. Every matrix-covering test must run without skips.
- [x] `.github/workflows/nightly.yml`, `tools/tests/test_nightly_workflow.py` — insert scan as a secretless read-only job, with conservative failure seed, persistent summary/report and always-upload; use setup-node 24 and locked uv with caches off and pinned actions. Add scan to bump dependencies and retain failed-prerequisite continuation, qualification and cancellation. Verify failures through execution of the workflow model, including unavailable checkout/tooling. Choose a bounded scan timeout below six hours.
- [x] `docs/nightly.md`, `docs/duplicate-scan.md`, `setup/README.md` — document scope, supported/static and unresolved/dynamic calls, thresholds, reporting, failure continuation and retuning procedure. Retain reproducible real-detector calibration results and full live Memories/Tenants identities, distinguishing empty action scope from optional broader tooling diagnostics.

**Acceptance Criteria:**

- Given two registered live-main modules containing a copied fragment above the committed threshold in custom actions or called scripts, when the production scan entry point runs, then it exits nonzero and its report/summary identifies the original module files, line ranges and fragment.
- Given a nightly whose publication or scan fails, when its remaining ordinary jobs evaluate eligibility, then bump and keepalive still run as appropriate and the overall nightly conclusion remains failed.
- Given unchanged inputs and detector policy, when scan runs again, then its selected scope and findings are reproducible except for freshly recorded remote revisions/observation metadata.

## Spec Change Log

## Review Triage Log

### 2026-11-15 — Review pass
- verdicts: 30 findings — high 22, medium 1, low 0, false 6, maybe-false 1
- All four layers completed. The blind layer's arithmetic and the intent auditor's reading enumeration are metadata; its six descriptive divergences are logged individually below. Rows follow layer completion order: blind hunter, verification gap, intent alignment, edge-case hunter.
- findings:
  - `[high]` `[patch]` B1: Shell substitutions omit invoked scripts — Parent tracked-blob reproduction omitted scripts/helper.py for echo and assignment substitutions with no diagnostic. Applied: Added an explicit source coverage error for unquoted command substitutions before shell tokenization.
  - `[high]` `[patch]` B2: Compact shell functions and PowerShell blocks omit literal calls — Parent reproduced both f() { python ...; } and & { python ... } returning no errors while omitting the helper. Applied: Added explicit coverage errors for unsupported shell function/compound and PowerShell script-block execution.
  - `[high]` `[patch]` B3: pushd and Set-Location select a root decoy — Parent reproduced both directory commands selecting helper.py instead of scripts/helper.py. Applied: Directory stack/location commands, including case-insensitive PowerShell CD and canonical Push-Location/Pop-Location forms and aliases, now fail coverage explicitly without changing path casing.
  - `[high]` `[patch]` B4: Subshell cwd leaks into later parent commands — Parent reproduced (cd scripts; python helper.py); python other.py omitting root other.py with no diagnostic. Applied: Unsupported subshell syntax now fails coverage before cwd state can leak into parent commands.
  - `[high]` `[patch]` B5: env, command and exec options conceal child calls — Parent reproduced env -i/-u, command -- and exec -a forms omitting helper.py without coverage errors. Applied: Wrapper option forms are explicitly rejected before option operands can hide the child executable.
  - `[high]` `[patch]` B6: Namespace from-import omits a tracked helper — Parent reproduced from pkg import helper without __init__.py omitting scripts/pkg/helper.py. Applied: Tracked namespace-package directories and their imported children are included.
  - `[high]` `[patch]` B7: Python -m/-c import context prefers source-directory decoys — Parent reproduced -m scripts.start selecting scripts/helper.py instead of actual root helper.py; source roots need invocation context. Applied: Private queue traversal preserves invocation-specific Python import roots through recursive imports; -m/-c use cwd roots.
  - `[high]` `[patch]` B8: Subprocess env changes import resolution silently — Parent reproduced env={'PYTHONPATH':'support'} selecting a clean decoy and omitting support/helper.py. Applied: Computed or resolution-affecting subprocess environment overrides now produce source coverage errors.
  - `[high]` `[patch]` B9: PowerShell Start-Process hides supported script calls — Parent reproduced Start-Process python -ArgumentList scripts/helper.py -Wait with helper omitted and no errors. Applied: Unsupported PowerShell process invocation now produces an explicit coverage error.
  - `[maybe-false]` `[defer]` B10: A zero-source detector report might mask incomplete analysis — findings() accepts coherent all-zero counters, verified directly. With actual pinned jscpd, two comment-heavy 100-line Python sources legitimately report sources=0/clones=0 below the token floor; a substantial 100-line copy reports sources=2/clones=1 (story-9-parent-counter-check.log). No engine failure on eligible substantive input was reproduced. Settle the eligible-source counting contract and reproduce an unexpectedly omitted eligible input before adding an invariant.
  - `[medium]` `[patch]` G1: Tests do not assert exact mapped original line ranges — Pre-verified regression gap: reviewer changed mapped endpoints by +1 in disposable source and all 22 actual-detector tests passed. Add different-offset source blocks, exact slices and summary-location assertions. Applied: Added actual-detector offsets (3–20)/(6–23), exact original-source slice/fragment assertions and summary locations; the +1 mutation now fails.
  - `[high]` `[patch]` G2: uv --directory is discarded rather than applied — Parent reproduced uv run --directory scripts python helper.py selecting root decoy; official uv CLI reference confirms cwd changes before execution. Applied: UV --directory/-C forms now fail coverage explicitly rather than selecting an executable from the caller cwd.
  - `[false]` `[reject]` I1: Hosted nightly behavior is not directly observed — Auditor describes a verification limit, not a demonstrated defect. The job targets GitHub Actions and the workflow model executes actual conditions/steps; no hosted qualification is claimed or required by this detection story.
  - `[false]` `[reject]` I2: Tests use injected Git remotes instead of GitHub modules — Production Transport.module uses the fixed anonymous GitHub main origin; tests use real current commits and prove stale checkout exclusion. Current empty registry authorizes no production module scan.
  - `[false]` `[reject]` I3: Static discovery does not demonstrate general runtime call discovery — The implementation and docs explicitly avoid module execution, matching the story's jscpd static analysis. This general limit does not itself prove a defect; concrete silent omissions from other layers are retained as separate patches.
  - `[false]` `[reject]` I4: Synthetic threshold tuning does not establish production noise rates — The docs correctly distinguish measured four-format calibration, empty live action corpora and the optional 97-file tooling survey. The story asks for tuning, not an invented populated live corpus.
  - `[false]` `[reject]` I5: Production scanning is currently zero scope — AD-3 defines every module as setup/*.yml, currently empty. The scanner covers every registration including unadopted ones; adding module registrations is later onboarding work.
  - `[false]` `[reject]` I6: Detection does not eliminate all shared code — Resolved story 9 expressly adds the scanner and tunes thresholds; code hoisting is separate migration work. No module cleanup outcome is claimed.
  - `[high]` `[patch]` E1: python -m package omits __main__.py — Parent reproduced package/__init__.py selected while copied executable package/__main__.py was omitted without errors. Applied: Regular and namespace package execution includes __main__.py and applicable initializers.
  - `[high]` `[patch]` E2: Transitive imports lose the original interpreter search roots — Parent reproduced scripts/start.py -> package.worker -> helper omitting scripts/helper.py because imported-module parents replaced entrypoint roots. Applied: Private queue traversal preserves invocation-specific Python import roots through recursive imports; -m/-c use cwd roots.
  - `[high]` `[patch]` E3: -m/-c execution resolves an action-directory decoy — Same verified invocation-context defect as B7: module/inline execution must use cwd-rooted interpreter search paths. Applied: Private queue traversal preserves invocation-specific Python import roots through recursive imports; -m/-c use cwd roots.
  - `[high]` `[patch]` E4: Namespace imported child modules are omitted — Same verified namespace defect as B6; tracked directory plus child exists despite missing __init__.py. Applied: Tracked namespace-package directories and their imported children are included.
  - `[high]` `[patch]` E5: env -u treats an option as the executable — Parent reproduced env -u MODE python scripts/helper.py with helper omitted; same wrapper-option root cause as B5. Applied: Wrapper option forms are explicitly rejected before option operands can hide the child executable.
  - `[high]` `[patch]` E6: uv --directory keeps the caller cwd — Same verified uv-directory defect as G2, including python helper.py child form and root decoy. Applied: UV --directory/-C forms now fail coverage explicitly rather than selecting an executable from the caller cwd.
  - `[high]` `[patch]` E7: while/until/elif condition scripts are omitted — Parent reproduced while ./scripts/helper.sh; do true; done with the condition helper omitted and no errors. Applied: Shell while/until/elif prefixes now expose literal condition calls to discovery.
  - `[high]` `[patch]` E8: Subshell directory state is not restored — Same verified subshell-state defect as B4; later parent commands can resolve against a decoy directory. Applied: Unsupported subshell syntax now fails coverage before cwd state can leak into parent commands.
  - `[high]` `[patch]` E9: A sourced script's cwd effect is ignored by its caller — Parent reproduced source scripts/change.sh (cd scripts), then python helper.py selecting a stale root decoy. Applied: Sourced traversal carries an explicit context flag and rejects caller cwd mutation instead of assuming stale state.
  - `[high]` `[patch]` E10: Import-Module -Name hides a local PowerShell module — Parent reproduced Import-Module -Name ./scripts/helper.psm1 with no errors and no selected module. Applied: PowerShell Import-Module resolves a literal local -Name argument.
  - `[high]` `[patch]` E11: Subprocess PYTHONPATH override is not validated — Same verified subprocess-env defect as B8; child module roots differ from the assumed inherited roots. Applied: Computed or resolution-affecting subprocess environment overrides now produce source coverage errors.
  - `[high]` `[patch]` E12: Claim-level package entrypoint copies can pass — Same verified package-main defect as E1; substantial code in executed __main__.py is outside selected scope. Applied: Regular and namespace package execution includes __main__.py and applicable initializers.

Grouping produced 15 patched entries (14 high, 1 medium), one unverified deferral and six rejected descriptive observations. Every duplicated observation retains its own row. All patches are private discovery/validation corrections or assertions for demonstrated states; they add no public interface. No intent-contract or planning amendment was required.

## Design Notes

One supplied root per module plus `skipLocal` reduces same-module noise, but the wrapper remains authoritative for cross-module policy and validates every finding against its own manifest. Materialize only selected regular blobs into private scratch; neither module Git attributes nor action/script text is executed. Discovery can conservatively include ambiguous candidate files, but cannot report clean when a local-script call remains uncovered.

Calibrate minimum lines/tokens with the real pinned binary before finalizing policy; document the measured tradeoff without blanket suppression. This is an implementation decision within the explicit tuning requirement, not a new product requirement. Current empty live action corpora provide source/scope evidence only. Useful logs and calibration evidence stay outside disposable scratch.

## Verification

**Commands:**

- `run-with-temp uv run --locked --script tools/tests/test_scan.py -v` — every detector/discovery/report matrix test passes, including real jscpd integration.
- `run-with-temp uv run --locked --script tools/tests/test_nightly_workflow.py -v` — existing workflow behaviors and new scan continuation tests pass.
- `run-with-temp uv run --locked --script --python 3.12 tools/tests/test_scan.py -v` — supported Python floor passes the same enabled cases.
- `run-with-temp uv run --locked --script tools/check_global.py --project-root .` — unchanged global gate passes all suites, render/schema/tag/bootstrap checks, actionlint and online zizmor. Supply the configured CiCd-agent job token privately if required; never print it or use the maintainer profile.
- `git diff --check` — no whitespace errors.

**Pre-review results:** Parent scanner checks passed 22 tests on the current interpreter and 22 on Python 3.12. Behavioral nightly workflow checks passed 25 tests. The unchanged global gate passed all 14 suites / 308 tests plus committed render/input, immutable bootstrap, reproducibility, schemas/caller interfaces, acceptable Builds publication, actionlint 1.7.12 and online zizmor 1.32.0 checks. All 10 matrix rows have enabled passing coverage. Parent inspection additionally reproduced and repaired subprocess cwd resolution, function-local aliases and import search-path mutation gaps; regressions exercise real Git and the pinned detector. `git diff --check` passed. Useful logs are `story-9-parent-*.log` under implementation-artifacts (Git-ignored).

## Auto Run Result

Status: done

Added the secretless nightly cross-module duplicate scan after publish-ready, with bump/keepalive continuation after ordinary failure. It uses committed registry and policy data, anonymous live-main snapshots, bounded nonexecuting discovery, verified jscpd 5.4.3, original-source locations/code, durable failure reports and explicit zero-scope outcomes. The intent contract is preserved verbatim.

**Files changed:**

- `.github/workflows/nightly.yml` — read-only scan job, failure seeds, summary/artifact and bump ordering.
- `.jscpd.json` — central weak-mode 10-line/50-token policy for YAML, Bash, PowerShell and Python.
- `tools/jscpd/package.json`, `tools/jscpd/package-lock.json` — exact detector version and dependency integrity pins.
- `tools/scan.py`, `tools/scan.py.lock` — locked controller, signature/version checks, snapshots, validated reports and CLI verdict.
- `tools/scan_discovery.py` — bounded action/script/import discovery and explicit unsupported-coverage diagnostics.
- `tools/tests/test_scan.py`, `tools/tests/test_scan.py.lock` — 28 enabled real-Git/pinned-detector tests, including exact source ranges.
- `tools/tests/test_nightly_workflow.py` — 25 behavioral workflow tests, including failure continuation and qualification/cancellation.
- `docs/duplicate-scan.md`, `docs/nightly.md`, `setup/README.md` — scope, supported/rejected forms, thresholds, reporting and operations.
- `_bmad-output/implementation-artifacts/story-9-detector-investigation.md` — live Memories/Tenants identities, detector evidence and empirical calibration.
- This story spec — plan, completed checklist, per-finding review triage, deferred item and verification results.

**Review:** Four independent layers reported 30 observations. Twenty-three observations were patched in 15 entries (14 high, 1 medium); B10 remains one unverified deferral. The six rejected auditor observations and their individual reasons are recorded in the triage log: hosted qualification was not claimed, local Git fixtures exercise the production boundary, static analysis is intentionally nonexecuting, calibration distinguishes synthetic and live scope, setup defines registration, and hoisting belongs to later migration. All concrete discovery defects from the other layers were retained and repaired.

**Follow-up review recommendation:** true. This first pass patched 14 high entries and one medium entry. The specific remaining unverified risk is whether other scripting forms outside the exercised wrapper/import matrix can still differ from the bounded static model; eligible-source accounting also remains unverified as B10. Further review should inspect those boundaries rather than repeat already-covered examples.

**Verification performed:**

- `run-with-temp uv run --locked --script tools/tests/test_scan.py -v` — 28 tests passed after final repairs.
- `run-with-temp uv run --locked --script --python 3.12 tools/tests/test_scan.py -v` — 28 tests passed after final repairs.
- `run-with-temp uv run --locked --script tools/tests/test_nightly_workflow.py -v` — 25 tests passed.
- `run-with-temp uv run --locked --script tools/check_global.py --project-root .` — final exit 0; 14 suites / 314 tests passed, plus committed render/input, immutable delivery bootstrap, reproducibility, schema/caller interface, acceptable Builds publication, actionlint 1.7.12 and online zizmor 1.32.0 checks.
- Matrix audit — all 10 rows covered by enabled passing cases; 53 distinct scanner/workflow methods, with no skips.
- Original-range regression — exact 3–20 and 6–23 offsets, both original source slices, fragment and summary locations are asserted; the endpoint +1 mutation now fails.
- `git diff --check` — passed.
- One parallel interpreter run encountered uv's shared script-environment recreation race (`ModuleNotFoundError: yaml`). Its failed log is preserved; sequential current/floor reruns passed, as did the final global gate.
- Useful logs: `_bmad-output/implementation-artifacts/story-9-parent-postreview-*.log`, plus the counter-check log. All disposable jobs used private wrapper scratch.

**Residual risks:** Production setup is currently empty, so a hosted nonempty nightly scan has not been observed. Future adopted modules exercise actual Actions timing and source patterns beyond the fixtures. Recognized unsupported constructs fail coverage explicitly; static detection cannot prove semantic equivalence or model arbitrary runtime behavior. The observed Memories/Tenants action corpora are empty at their recorded revisions; the separate 97-file tooling diagnostic and synthetic calibration do not establish future production noise rates. No module, Builds, credential or delivered-ref changes were made.

The reviewed files are finalized as a local commit; the finalization check verifies the working copy is clean.
