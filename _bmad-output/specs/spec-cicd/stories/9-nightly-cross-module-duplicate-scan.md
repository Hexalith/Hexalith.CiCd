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

### 2026-11-15 — Review pass
- verdicts: 62 findings — high 14, medium 9, low 28, false 8, maybe-false 3
- Follow-up pass on the `done` spec. All four layers completed and none were skipped. Rows follow layer completion order: blind hunter (B1–B18), edge-case hunter (E1–E28), verification gap (G1–G7, where G6–G7 are its other findings) and intent alignment (I1–I9, one row per described divergence). Before/after reproductions are in `story-9-followup-probes.log` (Git-ignored), which also holds a read-only run over the 18 `references/` module checkouts: 17 have no custom actions, and Builds' two composite actions discover cleanly. Its pinned-jscpd measurements are in the same log. Patch entries P1–P19 are named in the rows.
- findings:
  - `[medium]` `[patch]` B1: Summary fragment indented after list items renders as live Markdown — CommonMark treats the 4-space text after a `- ` item as a list-item paragraph, so module HTML and links render and lines join. Applied (P8): each fragment is a top-level fence longer than any backtick run, tagged with its format. Regressions assert the fenced copy and an HTML/backtick fragment.
  - `[low]` `[reject]` B2: Module paths and errors enter the summary unescaped — Real but cosmetic. GitHub sanitizes summary HTML, and only registered organization modules supply paths. An escaping helper is more than a direct correction for a rare file-name shape.
  - `[low]` `[reject]` B3: Summary can exceed GitHub's 1 MiB step-summary limit — This needs on the order of a thousand fragments. The job stays red and the full summary and report are still uploaded. Truncation would add a guard for an unlikely volume.
  - `[high]` `[patch]` B4: Common shell wrappers silently drop the called script — Parent probe: timeout, nohup, sudo, xargs, find -exec, time, eval, trap and nice each selected nothing with no error. Applied (P1):
    - Wrappers are unwrapped with fixed positional operands; their option forms fail.
    - eval/Invoke-Expression text, trap handlers and find -exec commands are rediscovered.
    - find -execdir, find -exec {} and Invoke-Command fail.
  - `[high]` `[patch]` B5: Python process/import APIs outside the allowlist are ignored — Parent probe: os.popen, subprocess.getoutput, os.execv, a star import, spec_from_file_location, exec(open()) and asyncio subprocess calls each omitted the helper silently. Applied (P1):
    - os.popen, getoutput and getstatusoutput literal commands are followed.
    - These fail coverage: exec/spawn/posix_spawn/asyncio/pty APIs, file-location loaders, exec/compile, partial application and star imports of process modules.
  - `[low]` `[reject]` B6: Ordinary shell constructs such as `$(date)`, `case` and heredocs fail coverage — This is the loud, conservative failure the matrix prescribes for unresolvable forms. No module reaches it before onboarding: the referenced module checkouts have no custom actions, and Builds' two composite actions discover cleanly. Parsing substitutions, case patterns and heredocs is beyond a direct correction. The docs now state this limitation.
  - `[low]` `[reject]` B7: Non-composite and tag-pinned actions always fail, undocumented, at line 1 — The failure matches `enforcement.md:29`: custom actions are composite, and third-party `uses:` are full-SHA pinned. What remains is cosmetic line-1 anchoring, and the diagnostic names the target. Threading step line numbers is more than a direct correction.
  - `[low]` `[reject]` B8: Production blob:none fetch lazily fetches each selected blob — This is the existing delivery_runtime transport pattern. Realistic action scopes are a few files, each Git call is bounded (≤120 s), and a slow module fails visibly. Batch prefetching is beyond a direct correction.
  - `[low]` `[patch]` B9: Empty registry with a tooling failure says "Registry unavailable." — The production registry is empty today, so every tooling failure was mislabelled; the real cause appeared only on the next ERROR line. Applied (P15): the message is now "No registered module was scanned.", and a regression asserts it beside the real error.
  - `[low]` `[patch]` B10: Endpoint validation uses str.splitlines and never compares content — Pinned-jscpd probe: form feed, U+2028 and lone CR are not detector line breaks, so splitlines shifted the reported source slice. Applied (P14): source is split on LF only, and the original-offset regression now contains a form feed.
  - `[low]` `[reject]` B11: Central policy validation is a denylist — The policy is CiCd's committed, reviewed file and never module input. Exact key/value validation would add guards against an unlikely internal edit.
  - `[low]` `[reject]` B12: Finding and report caps discard actionable findings — The failure is visible and fail-closed. More than 1,000 raw clones, or a report over 16 MiB, is unlikely for composite-action corpora. Partial truncation changes report semantics beyond a direct correction.
  - `[false]` `[reject]` B13: A thin Bash calibration margin may miss substantial copies — Pinned-jscpd probe: a realistic 13-line Bash script measured 72 tokens and was detected, and a 16-line cp sequence measured 128 tokens and was detected. Only 2-token echo lines fall under the floor, and those are trivial boilerplate.
  - `[low]` `[reject]` B14: The investigation cites Git-ignored logs — The project convention keeps logs outside version control (run-with-temp), and the key measurements are inlined in the investigation and docs.
  - `[low]` `[reject]` B15: The Python interpreter is not pinned — The intent prescribes a Python >=3.12 entry point, verified on 3.12 and on the current interpreter. Version-specific module syntax yields a loud invalid-source diagnostic. Pinning or recording runtimes is outside a direct correction.
  - `[maybe-false]` `[reject]` B16: The reused detector result directory could expose a stale report — Production builds a fresh detector root per scan; only the shared test detector reuses it, and pinned jscpd rewrites the report on every successful run. It would be settled by showing jscpd exit 0 without writing a report. If true, it is low and test-only.
  - `[low]` `[reject]` B17: read_json duplicates rt.json_read — This is developer-only duplication with no diverging caller named. Adding a limit parameter changes the shared runtime API.
  - `[low]` `[patch]` B18: The seed report lacks the documented v1 shape — `docs/duplicate-scan.md` documents modules, findings, detector and policy, but the seed declared v1 without them. Applied (P16): the seed carries empty observation fields, and a workflow regression asserts the shape.
  - `[high]` `[patch]` E1: An unquoted `#` inside a word discards the rest of the line — Parent probe: `if [ $# -lt 1 ]; then ./scripts/helper.sh; fi` omitted the helper silently. Applied (P2): a comment starts only at a word boundary, and shlex comment handling is disabled after the cut.
  - `[high]` `[patch]` E2: -m/-c are found among the script's own arguments — Parent probe: these omitted the script:
    - `python helper.py -c cfg`
    - `bash helper.sh -c Release`
    - `pwsh -File b.ps1 -config x`
    - lowercase `-executionpolicy`

    `-m fast` failed spuriously. Applied (P3): interpreter options are parsed positionally, and pwsh -WorkingDirectory, -EncodedCommand and -CommandWithArgs fail.
  - `[high]` `[patch]` E3: python3.11, python3.15, pypy3, python.exe and pwsh.exe are not recognized — Parent probe: each omitted its script silently. Applied (P1): versioned and `.exe` interpreter spellings are recognized.
  - `[high]` `[patch]` E4: A shell PYTHONPATH prefix, env assignment, export or step `env:` silently changes import roots — Parent probe: all four forms omitted `support/helper.py`. Applied (P4): these assignments, exports, declarations and composite step env entries fail coverage.
  - `[high]` `[patch]` E5: os.environ writes, os.putenv and contextlib.chdir are ignored — Parent probe reproduced the omission for an os.environ write, and the decoy selection for contextlib.chdir. Applied (P4): writes of resolution or computed keys through subscript, update, setdefault or putenv fail, and contextlib.chdir is a working-directory mutation.
  - `[high]` `[patch]` E6: eval, time, timeout, sudo, xargs, trap, Invoke-Expression and `using module` hide calls — Same unrecognized-invocation root cause as B4, reproduced by the parent probe. Applied (P1), including PowerShell `using module` paths.
  - `[high]` `[patch]` E7: os.popen, getoutput, exec*/spawn*, exec(open()), partial and star imports launch silently — Same root cause as B5, reproduced by the parent probe. Applied (P1).
  - `[medium]` `[patch]` E8: A UTF-8 BOM hides first-line calls and invalidates Python — Parent probe: a BOM dot-source was omitted, and a BOM Python file reported invalid source. Applied (P6): a leading BOM is ignored for parsing only.
  - `[medium]` `[patch]` E9: `python -m pip` and other installed tools fail coverage — Parent probe: "missing local Python module: pip". Applied (P5): a required module fails only when its top-level package exists locally.
  - `[low]` `[reject]` E10: `from . import name` for an `__init__` attribute fails spuriously — The failure is loud and rare in action helper packages. Supporting it needs an initializer branch, beyond a direct correction.
  - `[low]` `[patch]` E11: `from os import path` selects an unrelated local `path.py` — Verified: the else branch imported a non-local module's attribute names as top-level modules. Applied (P18): only module-less relative imports name modules, and a regression excludes `path.py`.
  - `[medium]` `[patch]` E12: PowerShell block comments and heredoc bodies are parsed as commands — Parent probe: comment-based help containing an apostrophe failed with "No closing quotation". Applied (P7): `<# … #>` regions that start a line are blanked, preserving line numbers. Heredoc bodies keep the conservative explicit failure rejected under B6.
  - `[low]` `[reject]` E13: An empty composite `shell:` raises IndexError — Reproduced. The module still fails visibly while its siblings continue, GitHub rejects the same invalid shape, and the fix would be an added guard.
  - `[false]` `[reject]` E14: JS, Docker and tag-pinned actions keep modules permanently red — `enforcement.md:29` makes these invalid custom actions for every module, so failing them is the matrix's invalid-action row.
  - `[low]` `[reject]` E15: Overflowing the 128 MiB aggregate staging cap fails later siblings — This needs more than 128 MiB of selected action sources across modules that are each capped at 32 MiB. It fails closed, and rebalancing would add accounting branches.
  - `[low]` `[reject]` E16: Discovery errors beyond 16 MiB break the fallback persist — This needs about 10^5 failing lines. The initialization stub then remains a conservative failure, and capping would add guards.
  - `[low]` `[patch]` E17: splitlines also splits on \f, \v, \x85,   and lone CR — Same root cause as B10, confirmed by the pinned-jscpd probe. Applied (P14).
  - `[medium]` `[patch]` E18: Fragment indentation after list items renders as Markdown — Same root cause as B1. Applied (P8).
  - `[low]` `[reject]` E19: summary.md can exceed GitHub's 1 MiB limit — Same claim as B3, rejected for the same reason.
  - `[maybe-false]` `[defer]` E20: The detector could silently skip a staged file, so sources should equal the staged count — carried: same location and claim as the logged B10 deferral (eligible-source accounting in `tools/scan.py:findings`). The code is unchanged, so it is not deferred again.
  - `[false]` `[reject]` E21: Prefix-sharing module roots could be skipped under skipLocal — Pinned-jscpd probe: roots `Hexalith.Tenants` and `Hexalith.TenantsAdmin` reported the cross-root clone exactly like the control pair.
  - `[low]` `[reject]` E22: Fresh 36-minute budgets per module can outlast the 55-minute job — Each Git call is ≤120 s, so only pathological network delay reaches this. A killed job leaves the conservative failure report. A shared budget would add plumbing.
  - `[low]` `[reject]` E23: A timed-out npm or jscpd can orphan grandchild processes — The timeout fails closed and runner teardown removes strays. Process-group handling adds complexity for an unlikely 600 s hang.
  - `[maybe-false]` `[reject]` E24: The reused detector could validate a stale report — Same claim as B16, settled the same way. If true, it is low.
  - `[low]` `[patch]` E25: An empty SCAN_DIRECTORY writes reports into the current directory — argparse converts "" to `Path(".")`. The workflow always sets the variable, but local runs could leave it empty. Applied (P17): an empty value counts as missing, and a regression asserts exit 2.
  - `[low]` `[reject]` E26: The aggregate total keeps the overflowing module's bytes — Same claim as E15.
  - `[high]` `[patch]` E27: commands() treats calls after `$#`, after a script's `-c`, under env prefixes and inside unlisted wrappers as data — Aggregate of E1, E2, E4 and E6, each reproduced. Applied by P1–P4.
  - `[low]` `[reject]` E28: Unbounded per-line errors can crash report generation — Same claim as E16.
  - `[high]` `[patch]` G1: The workflow model ignores job-level needs status, so removing `!cancelled()` goes undetected — Pre-verified by the reviewer's mutation probe. Applied (P9): `PostReleaseWorkflow.job_condition` applies GitHub's implicit success() and transitive needs results. A new test removes `!cancelled()` from scan and from bump and observes each skip.
  - `[medium]` `[patch]` G2: A real Detector.run nonzero exit is never exercised — Pre-verified. Applied (P10): a real child exiting 3 raises exactly "npm signature verification failed (exit 3)", without its stderr.
  - `[medium]` `[patch]` G3: Composite `uses:` steps are never exercised — Pre-verified. Applied (P11): a local `uses:` plus a SHA-pinned remote passes with findings; `@v4`, a missing local action and a target outside `.github/actions` fail at the action.
  - `[medium]` `[patch]` G4: Inline `shell: python` steps are never exercised — Pre-verified. Applied (P12): imports from the root and from `working-directory` select the actual helper, not the decoy.
  - `[medium]` `[patch]` G5: summary.md diagnostics and copied code are never asserted — Pre-verified. Applied (P13): module diagnostics and the fenced copied fragment are now asserted.
  - `[high]` `[patch]` G6: Interpreter flags are matched anywhere in the arguments — Same root cause as E2, confirmed by the reviewer's probe. Applied (P3).
  - `[high]` `[patch]` G7: Wrappers other than env/exec/command drop the inner call — Same root cause as B4. Applied (P1).
  - `[low]` `[reject]` I1: Discovery over-rejects realistic shell and PowerShell code — Same claim as B6, rejected for the same reason. The docs now state the limitation.
  - `[high]` `[patch]` I2: timeout, python3.11, node and os.popen calls cause silent under-coverage — Same unrecognized-invocation root cause, reproduced. Applied (P1): node, deno, bun, ruby, perl and php calls of tracked local scripts now fail as unsupported languages.
  - `[false]` `[reject]` I3: The production partial-clone transport is never executed by the tests — carried: same claim as logged I2. Production uses the fixed anonymous transport and is unchanged.
  - `[false]` `[reject]` I4: A simulator stands in for the hosted job graph — carried: same claim as logged I1. The concrete model defect behind it is G1, patched separately.
  - `[false]` `[reject]` I5: Production detects nothing yet, so all evidence is synthetic — carried: same claim as logged I5 and I4.
  - `[false]` `[reject]` I6: Three-module copies are reported pairwise, not grouped — The intent requires naming each implicated module with its locations. Pairwise findings do that, and the three-module test asserts that their union names all three.
  - `[low]` `[reject]` I7: One oversized clone volume or malformed endpoint empties the findings — Same claim as B12; this fails closed, per the tool/report failure row.
  - `[low]` `[patch]` I8: `docs/nightly.md` says scan "receives no credentials" — Its pinned checkout and setup actions use the Contents-read job token by default; only the controller step is token-free. Applied (P19): the wording is corrected.
  - `[false]` `[reject]` I9: The SHA-pinning and composite-only rules were never stated — `enforcement.md:29` states both rules for every module's custom actions.

Grouping produced 19 patched entries: 5 high (P1–P4, P9), 8 medium (P5–P8, P10–P13) and 6 low (P14–P19). E20 carries the existing deferral, so there is no new one. Thirty-one rows are rejected or carried as false. Every patch is private: discovery or validation behavior, report rendering, the workflow model, documentation, or a regression for a demonstrated state. None adds a public interface or amends the intent contract or plan. The original step-03 implementation subagent belongs to an earlier session and could not be re-engaged, so this session applied the patches directly.

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

**Implemented change:** Nightly now runs a secretless cross-module duplicate scan after publish-ready and before the Builds bump.

- It fetches each registered module's anonymous live main, recording full revisions.
- It discovers custom-action sources and the local scripts they call, statically and without executing module code.
- It runs integrity-pinned, signature-verified jscpd 5.4.3 under CiCd's central policy.
- Cross-module fragments and incomplete coverage fail the night. Bump and keepalive still continue.
- The intent contract is preserved verbatim.

This follow-up review pass hardened discovery, reporting and the workflow model:

- Wrappers and evaluators are unwrapped or rediscovered: timeout, nohup, sudo, eval, trap, find -exec and others.
- Interpreter options are read only before the script operand. Versioned and `.exe` interpreter spellings are recognized.
- Tracked scripts in unsupported languages fail coverage.
- os.popen and getoutput are followed; unsupported process/import APIs fail.
- Import-path environment overrides fail, whether set in shell, step `env` or Python.
- Word-internal `#`, byte-order marks and PowerShell comment help no longer hide or invent calls.
- `python -m` of an installed tool is treated as non-local.
- Copied fragments render in inert fences and use the detector's LF-only line numbering.
- The summary, seed and CLI edge cases are corrected.
- The workflow model now enforces GitHub's job-level needs semantics.

**Files changed** (story total; † = changed in this follow-up pass):

- `.github/workflows/nightly.yml` † — read-only scan job, failure seeds, summary/artifact and bump ordering. This pass: the seed carries the documented v1 report shape.
- `.jscpd.json` — central weak-mode 10-line/50-token policy for YAML, Bash, PowerShell and Python.
- `tools/jscpd/package.json`, `tools/jscpd/package-lock.json` — exact detector version and dependency integrity pins.
- `tools/scan.py` † — locked controller, signature/version checks, snapshots, validated reports and CLI verdict. This pass: LF-only slicing, fenced fragments, zero-registry failure message, empty `SCAN_DIRECTORY` rejection.
- `tools/scan_discovery.py` † — bounded static action/script/import discovery. This pass: wrappers and evaluators, positional options, interpreter spellings, environment and process-API coverage failures, comment/BOM handling, non-local `-m` and from-import fixes.
- `tools/tests/test_scan.py`, `tools/tests/test_scan.py.lock` † — 33 enabled real-Git/pinned-detector tests, 5 of them new this pass.
- `tools/tests/test_nightly_workflow.py` † — 26 behavioral workflow tests. This pass: job-level implicit success() and transitive needs, a `!cancelled()` mutation test, the seed shape.
- `docs/duplicate-scan.md` †, `docs/nightly.md` †, `setup/README.md` — scope, supported and failing forms, the conservative over-rejection limit, thresholds, reporting, job-token wording.
- `_bmad-output/implementation-artifacts/story-9-detector-investigation.md` — live Memories/Tenants identities, detector evidence and calibration.
- This story spec † — plan, checklist, both triage logs, the existing deferral and this result.

**Review findings breakdown (this pass):** 62 findings — high 14, medium 9, low 28, false 8, maybe-false 3.

Patches applied (19 entries):

- **5 high:**
  - P1: unrecognized invocation forms silently treated as data
  - P2: word-internal `#` treated as a comment
  - P3: interpreter options matched anywhere in the arguments
  - P4: import-path environment overrides
  - P9: workflow model missing needs semantics
- **8 medium:**
  - P5: `-m` of installed tools
  - P6: byte-order mark
  - P7: PowerShell comment help
  - P8: inert fragments
  - P10–P13: verification gaps G2–G5
- **6 low:**
  - P14: LF slicing
  - P15: zero-registry message
  - P16: seed shape
  - P17: empty `SCAN_DIRECTORY`
  - P18: non-local from-import
  - P19: job-token wording

Deferred: nothing new. E20 carries the existing eligible-source deferral (the earlier B10).

Rejected rows, with the recorded reasons:

- **Cosmetic, rare or fail-closed lows whose fix exceeds a direct correction:**
  - B2: Markdown in paths
  - B3/E19: 1 MiB summary limit
  - B7: line-1 anchoring; the action rules come from enforcement policy
  - B8: lazy blob fetch
  - B11: policy denylist
  - B12/I7: caps discard findings
  - B14: Git-ignored logs, by convention
  - B15: the intent prescribes Python >=3.12
  - B17: shared-runtime API change
  - E10: relative attribute import
  - E13: empty shell
  - E15/E26: aggregate staging
  - E16/E28: unbounded errors
  - E22: per-module budgets
  - E23: orphaned grandchildren
- **Conservative over-rejection of `$(...)`, case, heredocs and PowerShell blocks** (B6/I1): matrix-prescribed loud failure, no current module reaches it, and the limit is now documented.
- **Refuted:**
  - B13: realistic Bash measured 72 and 128 tokens and was detected
  - E14, I9: rules come from `enforcement.md:29`
  - E21: prefix-sharing roots were detected
  - I6: pairwise findings name every module
- **Carried as false:** I3, I4, I5.
- **Maybe-false:** B16/E24, a stale test-only report; if true it is low.

**Follow-up review recommendation:** true. This follow-up pass patched 5 high, 8 medium and 6 low entries. The specific unverified risk is that discovery remains an allowlist recognizer. An unlisted command, alias or API whose operand is a local script is still treated as data, which is fail-open by construction. This pass closed 33 reproduced omissions, and unreviewed classes remain:

- `$GITHUB_ENV`/`$GITHUB_PATH` writes that affect later steps
- shell aliases
- PowerShell invocation forms outside the handled set

A further pass should examine that unknown-command default rather than enumerate more examples.

**Verification performed:**

- `run-with-temp uv run --locked --script tools/tests/test_scan.py -v` — 33 tests passed.
- `run-with-temp uv run --locked --script --python 3.12 tools/tests/test_scan.py -v` — 33 tests passed.
- `run-with-temp uv run --locked --script tools/tests/test_nightly_workflow.py -v` — 26 tests passed.
- `run-with-temp uv run --locked --script tools/check_global.py --project-root .`:
  - The first attempt hit the 10-minute tool limit and was rerun detached.
  - A tokenless run failed only the three online checks that require a read-only token.
  - With the CiCd-agent profile token supplied privately, it exited 0: 14 suites / 320 tests, plus committed render/input, immutable delivery bootstrap, reproducibility, schemas/caller interfaces, acceptable Builds publication, actionlint 1.7.12 and online zizmor 1.32.0. No token appears in the log.
- Probes: 33 silent omissions at HEAD and 0 in the patched tree, plus the module-corpus scan and pinned-jscpd measurements described in the triage log.
- `git diff --check` — passed.
- Logs: `_bmad-output/implementation-artifacts/story-9-followup-*.log` (Git-ignored). Disposable jobs used wrapper scratch.

**Residual risks:**

- The allowlist recognizer risk described above.
- The conservative failure on common shell and PowerShell constructs will turn realistic modules red until central discovery is extended. Measure it at onboarding.
- Eligible-source accounting remains the carried deferral.
- The production registry is empty, so no hosted nonempty nightly scan has been observed.
- Extreme clone volume can still empty findings or overflow the step summary. Both fail closed.

No module, Builds, credential or delivered-ref changes were made.

The reviewed files are finalized as a local commit; the finalization check verifies the working copy is clean.
