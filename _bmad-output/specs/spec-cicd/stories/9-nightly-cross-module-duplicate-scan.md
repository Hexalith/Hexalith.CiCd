---
title: 'Nightly cross-module duplicate scan'
type: 'feature'
created: '2026-11-15'
status: 'in-review'
baseline_revision: '23e1c39cf387151467cac4636267c780098a388d'
review_loop_iteration: 1
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
- [x] `tools/scan.py`, `tools/scan.py.lock` (and a focused helper if needed) — implement committed registry, anonymous current-main snapshots, bounded nonexecuting action/call discovery following the Design Notes discovery coverage model, and isolated staging; run central jscpd over module roots; independently validate report endpoints; emit deterministic token-free report, full source SHAs and actionable code/location diagnostics. Fail closed while retaining healthy observations and an explicit empty-scope result.
- [x] `tools/tests/test_scan.py`, adjacent `.py.lock`, fixture helper if useful — test every matrix row through real temporary Git repositories and actual pinned detector integration. Include all four formats, transitive calls/imports, same-module repetition beside cross-module copies, module config/ignores/directives, invalid outputs, bad paths and empty scope, plus both coverage-model rules and the Spec Change Log re-derivation constraints. Every matrix-covering test must run without skips.
- [x] `.github/workflows/nightly.yml`, `tools/tests/test_nightly_workflow.py` — insert scan as a secretless read-only job, with conservative failure seed, persistent summary/report and always-upload; use setup-node 24 and locked uv with caches off and pinned actions. Add scan to bump dependencies and retain failed-prerequisite continuation, qualification and cancellation. Verify failures through execution of the workflow model, including unavailable checkout/tooling. Choose a bounded scan timeout below six hours.
- [x] `docs/nightly.md`, `docs/duplicate-scan.md`, `setup/README.md` — document scope, the discovery coverage model (included literal references and failing indirection), thresholds, reporting, failure continuation and retuning procedure. Retain reproducible real-detector calibration results and full live Memories/Tenants identities, distinguishing empty action scope from optional broader tooling diagnostics.

**Acceptance Criteria:**

- Given two registered live-main modules containing a copied fragment above the committed threshold in custom actions or called scripts, when the production scan entry point runs, then it exits nonzero and its report/summary identifies the original module files, line ranges and fragment.
- Given a nightly whose publication or scan fails, when its remaining ordinary jobs evaluate eligibility, then bump and keepalive still run as appropriate and the overall nightly conclusion remains failed.
- Given unchanged inputs and detector policy, when scan runs again, then its selected scope and findings are reproducible except for freshly recorded remote revisions/observation metadata.

## Spec Change Log

### 2026-11-15 — Review pass 3 loopback (review_loop_iteration 1)

**Triggering finding: A1.** Discovery recognizes a fixed set of invocation forms. Anything it does not recognize is treated as data: commands, syntax and APIs outside the set, and any resolution state it does not model.

- At `23e1c39cf387151467cac4636267c780098a388d`, triage rows B2, E1–E11, E14, E15 and E23 reproduced 30 silent omissions, each with `errors: []` (`_bmad-output/implementation-artifacts/story-9-review3-probes.log`).
- This is the third review pass to find omissions of this class. The previous pass recommended examining the unknown-form default instead of enumerating more examples.

**Amended:**

- Design Notes now carry the **Discovery coverage model**. Recognized calls refine resolution only; literal references to tracked scripts are included from every candidate base, whatever consumes them; unmodeled indirection fails.
- The Tasks checklist is unchecked, and its discovery, test and docs lines reference the model.
- Code was reverted in the working tree to `93e3d33b6436d9e8f215a7556b0beb0368107b56` for re-derivation. Three paths were not reverted: this spec, the orchestrator-owned `_bmad-output/implementation-artifacts/deferred-work.md` and the evidence artifact `story-9-detector-investigation.md`.

**Known-bad state avoided:** a module produces `result: pass` while its copied action or called-script code sits outside the scanned scope. The copied code is reached through any of:

- an unrecognized wrapper, runner, block, redirection, option or assignment;
- an environment or `PATH` write;
- a conditional directory change;
- a piped interpreter;
- a reflective Python API.

**Re-derivation constraints.** Each item was verified in this pass and is patch-level: moot until re-derivation, then mandatory in the re-derived code.

| Item | Source | Required behavior |
| --- | --- | --- |
| C1 | B1/E12/I2 | A dormant file's action context is its nearest ancestor holding `action.yml`/`action.yaml`. Add a test with a script in an action subfolder that uses `$GITHUB_ACTION_PATH`. |
| C2 | B4/E17 | The continuation characters are `\` in shell and the backtick in PowerShell, and nothing else. Diagnostics keep physical line numbers. |
| C3 | B5 | Each composite step is discovered independently. A step's error is anchored at that step's line, and later steps are still discovered. |
| C4 | B6 | The bump job sets up the same pinned Node 24 as the scan job before its producer step, because its shared global gate runs `tools/tests/test_scan.py` with the real detector. The workflow model asserts the step. `setup/README.md` lists Node/npm and `registry.npmjs.org` among the validation prerequisites. |
| C5 | B8 | Heredoc-fed interpreters fail. A heredoc body fed to any other command is scanned for literal references as data. `docs/duplicate-scan.md` describes the actual behavior. |
| C6 | E13 | An import through a namespace package nested in a regular package includes every ancestor `__init__.py`. |
| C7 | E16 | Shell and PowerShell discovery split only on LF and drop a trailing CR. |
| C8 | E18 | PowerShell `<# … #>` comments are removed wherever they occur, preserving the line count. |
| C9 | E20 | `command -v`/`-V` is a non-executing probe and passes. |
| C10 | E22 | `sys.executable`, and any alias of it, as argv[0] is the Python interpreter. |
| C11 | G1 | Tests pin the followed `xargs`, `flock <lock>`, `bash -c`, `pwsh -Command` and `uv run --with` forms. |
| C12 | G2 | Tests pin following `os.system`, `subprocess.Popen`/`call`/`check_output`/`getstatusoutput`, `runpy.run_module` and `__import__`. |
| C13 | G3 | Tests pin these failures: `os.chdir`, `os.putenv`, `os.environ.setdefault`, `os.spawn*`/`posix_spawn`, `SourceFileLoader`/`compile`, and a missing local `-m` child. |
| C14 | G4 | Tests pin an extensionless shebang file directly under `.github/actions/**`. |
| C15 | G5 | Tests assert a Python finding at `scripts/helper`, next to a distinct `scripts/helper.py`, in both modules. |
| C16 | G6 | Tests have one single-violation subtest per central-policy rule. |

Every A1 reproduction in the probe log becomes a two-module real-detector regression that produces either the cross-module finding or the named coverage failure.

**KEEP:**

1. **Restore first.** Begin by restoring every reverted path from `23e1c39cf387151467cac4636267c780098a388d`, using `git restore --source=23e1c39cf387151467cac4636267c780098a388d --worktree -- <path>`. Do not re-implement from scratch.
2. **Keep these verbatim, except as C4 requires:**
   - `.jscpd.json`;
   - `tools/jscpd/package.json` and `tools/jscpd/package-lock.json`;
   - `tools/scan.py` and `tools/scan.py.lock`;
   - `tools/tests/test_scan.py.lock`;
   - the nightly scan job, its seed, summary and artifact upload, and the bump/keepalive ordering;
   - `tools/tests/test_nightly_workflow.py`;
   - `docs/nightly.md`.
3. **In `tools/scan.py`, keep:**
   - the detector install, signature and version checks;
   - central-policy validation;
   - endpoint validation with LF-only slicing;
   - unique flat staged names;
   - same-length directive neutralization;
   - persist with its bounded fallback;
   - the fenced summary;
   - the CLI.
4. **In `tools/scan_discovery.py`, keep the proven recognized-call layer as the precise-resolution path:**
   - hardened `safe_path`/`resolve`;
   - the duplicate-key action loader;
   - composite-only, SHA-pinned `uses:`;
   - wrapper unwrapping and its option failures;
   - positional interpreter options and interpreter spellings;
   - invocation-specific Python roots;
   - the `-m` package `__main__`, namespace packages and non-local `-m` handling;
   - BOM handling, comment-help blanking and the word-boundary `#`;
   - the process, environment, search-path and working-directory failures;
   - every resource bound.

   Add the coverage model around this layer rather than replacing it.
5. **Keep existing tests.** Every existing test stays unless the amended model reverses one of its assertions. One known case: a data argument that names a tracked script is now included.
6. **`docs/duplicate-scan.md`:** keep its scope, threshold, reporting and retuning sections, and rewrite its discovery section for the model.
7. **Do not modify:** `_bmad-output/implementation-artifacts/deferred-work.md`, the investigation artifact, `<intent-contract>`, or the frontmatter `deferred` item.

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

### 2026-11-15 — Review pass
- verdicts: 53 findings — high 17, medium 12, low 10, false 13, maybe-false 1
- This is the second follow-up pass on the `done` spec, reviewing `93e3d33..23e1c39`. All four layers completed and none were skipped.
- Rows follow layer completion order: blind hunter (B1–B12), edge-case hunter (E1–E23), verification gap (G1–G6) and intent alignment (I1–I12, one row per described divergence).
- Parent reproductions are in `story-9-review3-probes.log` (Git-ignored), with their probe sources alongside.
- Entry A1 routes to bad_spec, and the cascade makes this pass's patch entries moot. Each patch row names the Spec Change Log constraint (C1–C16) that carries it into re-derivation.
- findings:
  - `[medium]` `[patch]` B1: dormant files in action subfolders use their own folder as `$GITHUB_ACTION_PATH`. Parent probe: `.github/actions/a/scripts/run.sh` sources `$GITHUB_ACTION_PATH/scripts/lib.sh`. The pass from `action.yml` resolves it, but the dormant-seed pass fails with `.../scripts/scripts/lib.sh` and turns a correct module red. Moot; constraint C1.
  - `[high]` `[bad_spec]` B2: `$GITHUB_ENV`/`$GITHUB_PATH` writes and shell `PATH` changes silently redirect resolution. Parent probe: a `PYTHONPATH=support` write to `$GITHUB_ENV` followed by `python -m helper` omitted `support/helper.py` with no error, and so did `export PATH="$PWD/scripts:$PATH"; helper.sh` for `scripts/helper.sh`. Amendment A1 (Design Notes coverage model, rule 2).
  - `[false]` `[reject]` B3: `python -I`/`-P` keep the script directory as an import root. Under `-I`/`-P`, Python imports from no local directory, so keeping the script directory only over-includes; the parent probe selected `scripts/lp.py`. The Design Notes permit conservative inclusion, and no file that runs is omitted.
  - `[low]` `[patch]` B4: line continuations shift later diagnostics and join on the wrong character per shell. Parent probe: `python missing.py` on physical line 5, after two `\` continuations, was reported at line 3. Continuations are everyday shell. Moot; constraint C2.
  - `[low]` `[patch]` B5: one bad composite step stops discovery of later steps and anchors at line 1. Parent probe: `uses: actions/checkout@v4` followed by `python scripts/later.py` reported `action.yml:1` and never selected `scripts/later.py`. The module stays red, so scope and diagnostics are truncated rather than passed. Moot; constraint C3.
  - `[medium]` `[patch]` B6: the bump's shared gate now needs npm and registry.npmjs.org, and neither is declared. `tools/bump.py:97` runs `check_global.py`, whose `run_tool_tests` runs `test_scan.py` with a real `npm ci` and `npm audit signatures`. The bump job has no setup-node step and relies on the runner image's unpinned npm, and `setup/README.md` lists no npm prerequisite. The spec deliberately runs every suite in the shared gate, so the coupling itself stays; the smallest fix pins Node and documents the prerequisite. Moot; constraint C4.
  - `[false]` `[reject]` B7: the detector's fragment is never compared with the source. Staging preserves every line (directive neutralization keeps the same length), and the actual-detector offset test asserts the published fragment equals the exact copied source (`tools/tests/test_scan.py:656`). A wrong range would need a defect in the pinned engine, which no probe has shown.
  - `[low]` `[patch]` B8: the docs say heredoc bodies fail coverage, but discovery parses them as commands. Parent probe: a `cat > notes.md <<EOF` body passed with no error, and `bash <<EOF` followed the body and also reported a bogus missing `<<EOF`. Moot; constraint C5, and A1 rule 2 makes heredoc-fed interpreters fail.
  - `[low]` `[reject]` B9: the spec metadata and pre-review results are stale. The pre-review counts are stale. `review_loop_iteration: 0` was correct, because no bad_spec loopback had happened before this pass. The fix would edit this build's spec.
  - `[low]` `[reject]` B10: scan reads the triggering CiCd commit while bump fetches current main. Confirmed: the scan checkout has no `ref`, and `docs/nightly.md:134` describes the bump fetch. A module registered during that same night's window is scanned the following night. Aligning the revisions needs fetch plumbing beyond a direct correction, for an unlikely race.
  - `[false]` `[reject]` B11: the summary lacks permalinks, numbering and the policy digest. For each finding, the summary already gives the module main revision, `module/path:start-end` for both endpoints and the fenced fragment, which is everything the intent's actionable-report row asks for. Reproducibility metadata is in the `report.json` uploaded with it.
  - `[false]` `[reject]` B12: jscpd's `maxSize: 2mb` may silently skip files that the 2 MiB blob cap admits. Pinned-jscpd probe: copies of 1,990,000, 2,050,000 and 2,097,152 bytes each reported 2 sources and 1 clone, so `2mb` covers the full cap.
  - `[high]` `[bad_spec]` E1: wrappers and uv invoked by absolute path hide the script. Parent probe: `/usr/bin/env python3 scripts/helper.py`, `/usr/bin/timeout 60 ./scripts/helper.sh` and `/home/runner/.local/bin/uv run scripts/helper.py` each selected nothing, with no error. A1 rule 1.
  - `[high]` `[bad_spec]` E2: brace groups after then/do/else, a mid-line `function` and PowerShell `try`/`else` blocks hide calls. Parent probe reproduced the omission for `then { ./scripts/helper.sh; }`, `do { …; }`, `function f { …; }`, `try { ./scripts/helper.ps1 } catch {…}` and `} else { … }`. A1 rule 1.
  - `[high]` `[bad_spec]` E3: `builtin`, `coproc` and leading redirections hide calls. Parent probe: `builtin source`, `coproc` and `>out.log ./scripts/helper.sh` each omitted the helper silently. A1 rule 1.
  - `[high]` `[bad_spec]` E4: `trap -- 'handler' EXIT` drops the handler. Parent probe: the handler was omitted silently, because the trap branch treats `--` as an option and skips. A1 rule 1.
  - `[high]` `[bad_spec]` E5: unlisted `uv run` value options become the command. Parent probe: `-p 3.12`, `--extra dev` and `--env-file .env` each omitted the target silently. A1 rules 1–2.
  - `[high]` `[bad_spec]` E6: `NAME+=value` prefixes and `export PYTHONPATH+=` are not recognized as assignments. Parent probe: `MODE+=x ./scripts/helper.sh`, `env MODE+=x …` and `export PYTHONPATH+=:support` each omitted the target silently. A1 rules 1–2.
  - `[high]` `[bad_spec]` E7: `$GITHUB_ENV` writes and a non-mapping step `env` bypass the resolution check. Same reproduction as B2. A non-mapping `env:` expression also skips the `isinstance(dict)` check (`tools/scan_discovery.py:199`). A1 rule 2.
  - `[high]` `[bad_spec]` E8: a `PATH` prepend followed by a slashless call selects a decoy. Same reproduction as B2 (`path-export`). A1 rule 2.
  - `[high]` `[bad_spec]` E9: a conditional `cd` is applied unconditionally. Parent probe: after `if [ -n "$X" ]; then cd scripts; fi`, `python helper.py` selected only `scripts/helper.py` and omitted the root `helper.py`. A1 rule 1 keeps every established working directory as a base.
  - `[high]` `[bad_spec]` E10: Python `eval` of an import or process call is ignored. Parent probe: `eval("__import__('helper')")` omitted `scripts/helper.py`. A1 rule 2.
  - `[high]` `[bad_spec]` E11: process APIs that are stored, passed, unpacked, defaulted or fetched with `getattr` launch silently. Parent probe reproduced the omission for attribute-store, argument, `getattr(subprocess, 'run')`, tuple-unpack, walrus and default-argument forms. A1 rules 1–2.
  - `[medium]` `[patch]` E12: a dormant script under `.github/actions/x/scripts` resolves `$GITHUB_ACTION_PATH` against its own folder. Same defect and reproduction as B1. Moot; constraint C1.
  - `[high]` `[patch]` E13: `from pkg.ns import helper` omits the regular parent package's initializer. Parent probe: `scripts/pkg/__init__.py` was not selected, although Python executes it. The smallest fix walks ancestors from the namespace stem. Moot; constraint C6.
  - `[high]` `[bad_spec]` E14: `pwsh -Command -` fed from a pipe hides the piped script. Parent probe: `Get-Content scripts/x.ps1 | pwsh -Command -` omitted `scripts/x.ps1` silently. A1 rule 1 makes the operand a literal reference, and rule 2 fails stdin-fed interpreters.
  - `[high]` `[bad_spec]` E15: scripts launched through runners (`poetry`/`pipenv`/`pdm`/`hatch run`, `make`/`just`) are omitted. Code path: an unrecognized command word leaves every operand as data, as in E1, and recipe files are never examined. A1 rules 1–2.
  - `[low]` `[patch]` E16: shell discovery splits lines on U+2028, `\x85`, form feed and lone CR. Parent probe: `echo x  # ; ./scripts/helper.sh` hid the call. Only crafted separators reach it, but the fix is the direct LF-only split that `scan.py` already uses. Moot; constraint C7.
  - `[low]` `[patch]` E17: backslash continuations shift later diagnostics. Same defect and reproduction as B4. Moot; constraint C2.
  - `[high]` `[patch]` E18: an inline PowerShell `<# … #>` comment discards the rest of the line. Parent probe: `Write-Output x <# note #> ; ./scripts/helper.ps1` omitted the helper silently, because only line-leading comment help is blanked. Moot; constraint C8.
  - `[false]` `[reject]` E19: a symlinked TMPDIR would make every endpoint unknown. The supported runtime is Linux x86_64. The GitHub runner's `/tmp` is a real directory, and `run-with-temp` gives a real `/tmp/hexalith-job.*` (`readlink -f` returns it unchanged). Reaching this would fail closed with an explicit endpoint error.
  - `[medium]` `[patch]` E20: `command -v tool` fails as a wrapper option. Parent probe: `if command -v jq >/dev/null; then …` raised "unsupported shell wrapper options". This common, non-executing probe turns healthy modules red. Moot; constraint C9.
  - `[low]` `[reject]` E21: sourcing or calling an absolute system path fails coverage. Reproduced with `/etc/os-release` and `/usr/local/bin/tool.sh`. An absolute target can be a module script copied at runtime, so the loud failure is the conservative outcome. Exempting system paths needs a path policy, which is beyond a direct correction for an uncommon idiom.
  - `[medium]` `[patch]` E22: `subprocess.run([sys.executable, 'scripts/helper.py'])` fails as computed. Parent probe: "unresolved computed Python script invocation" for the standard interpreter idiom, and the helper was not staged. Moot; constraint C10.
  - `[high]` `[bad_spec]` E23: claim-level for AC1 — copied called-script code reached through these forms yields a pass. This aggregates E1–E6 and E15, each reproduced with `errors: []`. A1.
  - `[medium]` `[patch]` G1: no test pins the xargs/flock wrappers, the `bash -c`/`pwsh -Command` recursion or `uv run --with`. Pre-verified: each mutant passed all 33 tests. Moot; constraint C11.
  - `[medium]` `[patch]` G2: following `os.system`, `Popen`, `runpy.run_module` and `__import__` is untested. Pre-verified by mutation. Moot; constraint C12.
  - `[medium]` `[patch]` G3: the `os.chdir`, `os.putenv`, `os.environ.setdefault`, `os.spawn*` and missing-local-`-m`-child failures are untested. Pre-verified by mutation. Moot; constraint C13.
  - `[medium]` `[patch]` G4: extensionless shebang files directly under `.github/actions/**` are untested. Pre-verified by mutation. Moot; constraint C14.
  - `[medium]` `[patch]` G5: the staged-name collision fixture cannot observe a collision. Pre-verified: with path-based staging, all tests passed while the copied Python was overwritten. Moot; constraint C15.
  - `[medium]` `[patch]` G6: the central-policy test violates two rules at once. Pre-verified: removing `ignore` from the denylist still passed all tests. Moot; constraint C16.
  - `[low]` `[reject]` I1: discovery over-rejects realistic shell and PowerShell code — carried: same claim as logged B6/I1. `$(...)`, `case` and computed PowerShell values still fail as described.
  - `[medium]` `[patch]` I2: scripts in action subdirectories fail spuriously. Same defect and reproduction as B1. Moot; constraint C1.
  - `[false]` `[reject]` I3: one invalid registration aborts the scan for every module. The intent says to "reject invalid/colliding registrations or capacity above 17". The isolation clause and the partial-failure row concern module-level fetch, action and path failures. A Builds, colliding or over-capacity registry is invalid system-wide (`render.registry`, `rt.registry`), and the scan rejects it loudly instead of certifying partial scope.
  - `[false]` `[reject]` I4: tests use injected local remotes, not the production partial-clone transport — carried: same claim as logged I2/I3. The transport is unchanged.
  - `[false]` `[reject]` I5: neither suite runs the real controller inside the real job — carried: same claim as logged I1/I4.
  - `[maybe-false]` `[defer]` I6: detector source counts are checked structurally, not for semantic completeness — carried: same location and claim as the logged B10/E20 deferral (`tools/scan.py:findings`). The code is unchanged, so it is not deferred again.
  - `[false]` `[reject]` I7: calibration is synthetic and the Bash margin is thin — carried: same claims as logged I4 and B13.
  - `[false]` `[reject]` I8: the scan job's Contents-read token reaches the checkout and setup actions. The intent forbids App and publish credentials, and the default Contents-read job token is neither. The controller step receives no token, and the docs state this (P19).
  - `[false]` `[reject]` I9: non-composite and tag-pinned actions fail their module — carried: same claim as logged E14/B7, on the authority of `enforcement.md:29`.
  - `[false]` `[reject]` I10: three-module copies are reported pairwise — carried: same claim as logged I6.
  - `[low]` `[reject]` I11: the global staging budget and finding caps can discard sibling observations — carried: same claims as logged I7/E15/B12, all fail-closed.
  - `[false]` `[reject]` I12: compliance with `run-with-temp` and retained logs cannot be checked from the diff. This is a descriptive limitation, not a defect. The retained logs exist as `_bmad-output/implementation-artifacts/story-9-*.log` (Git-ignored), and every recorded command ran under `run-with-temp`.

Grouping produced these entries:

- **A1 (bad_spec, high, 15 rows):** discovery treats unrecognized invocation forms and unmodeled resolution state as data. It triggered the Design Notes coverage-model amendment and the unchecked Tasks.
- **16 patch entries (19 rows):** 2 high (C6, C8), 10 medium (C1, C4, C9–C16) and 4 low (C2, C3, C5, C7). The bad_spec cascade makes them moot, and the Spec Change Log carries them as re-derivation constraints.
- **One carried deferral.**
- **18 rejected or carried rows.**

`review_loop_iteration` is now 1. Code was reverted for re-derivation through step 3.

## Design Notes

One supplied root per module plus `skipLocal` reduces same-module noise, but the wrapper remains authoritative for cross-module policy and validates every finding against its own manifest. Materialize only selected regular blobs into private scratch; neither module Git attributes nor action/script text is executed. Discovery can conservatively include ambiguous candidate files, but cannot report clean when a local-script call remains uncovered.

Calibrate minimum lines/tokens with the real pinned binary before finalizing policy; document the measured tradeoff without blanket suppression. This is an implementation decision within the explicit tuning requirement, not a new product requirement. Current empty live action corpora provide source/scope evidence only. Useful logs and calibration evidence stay outside disposable scratch.

**Discovery coverage model** (amended in review pass 3). Recognized calls refine resolution; they never bound coverage. Discovery keeps recognized semantics for interpreters, wrappers, `source`/dot-source, imports and process APIs, because they supply the exact working directory, import roots and language. Two fail-safe rules cover everything else:

1. **Literal references are included.**
   - **What counts as a reference.** The sources are every reachable action `run`, shell, PowerShell and Python file. A literal is a shell word after quote removal, or a Python string constant, including list and tuple elements. It is a reference when it names a tracked regular blob that is a shell, PowerShell or Python script, either by suffix or as an extensionless file with a supported shebang. This holds whatever consumes the literal: any command, wrapper, runner, block, pipeline, redirection, heredoc body or API.
   - **Resolution.** Resolve each reference against every candidate base:
     - the workspace root;
     - the owning action directory;
     - the referencing file's directory;
     - every literal working directory that the source has established, both before and after each change.
   - **Inclusion.** Include and traverse every match. Over-inclusion is acceptable, and a reference never fails merely because its consumer is unrecognized. A literal never pulls in YAML outside `.github/actions`.
   - **Execution positions.** From an execution position, a literal fails coverage when it names a tracked file in another script language, or when it resolves against no base.
   - **Python imports.** Imports resolve against every candidate root: the invocation roots, the importing file's directory, the working directory and the workspace root. Every match is included.
2. **Unmodeled indirection fails** with a source diagnostic. This covers:
   - a computed value in an execution position: a command word, interpreter operand, sourced path, import or process-API target, or working directory;
   - an interpreter fed from stdin or a heredoc, such as `bash <<EOF`, `pwsh -Command -` or `python -`;
   - a `PYTHONPATH`, `PYTHONHOME` or `PYTHONSAFEPATH` value set by any means: assignment including `+=`, export/declare, step `env` (including a non-mapping `env`), `$env:`, `os.environ`, `os.putenv`, subprocess `env`, an env file, or a `$GITHUB_ENV` write;
   - a `PATH` value or `$GITHUB_PATH` write that adds a relative, workspace or action-path directory, or any computed component other than `$PATH` and `$HOME`;
   - a `$GITHUB_ENV` write with a computed key;
   - Python code that opens `GITHUB_ENV` or `GITHUB_PATH`;
   - reflective use of a process or import API: one that is stored, passed, unpacked, defaulted, returned, fetched with `getattr`, or run through `eval`, `exec` or `compile`;
   - a task runner whose recipes are tracked module files, for example `make`/`just` with a tracked Makefile/justfile, or `npm`/`pnpm`/`yarn run` with a tracked `package.json`.

Existing explicit failures stay conservative, for example substitutions, subshells, `pushd`/`Set-Location`, `uv --directory` and `Start-Process`. This model is what "cannot report clean when a local-script call remains uncovered" means for discovery.

## Verification

**Commands:**

- `run-with-temp uv run --locked --script tools/tests/test_scan.py -v` — every detector/discovery/report matrix test passes, including real jscpd integration.
- `run-with-temp uv run --locked --script tools/tests/test_nightly_workflow.py -v` — existing workflow behaviors and new scan continuation tests pass.
- `run-with-temp uv run --locked --script --python 3.12 tools/tests/test_scan.py -v` — supported Python floor passes the same enabled cases.
- `run-with-temp uv run --locked --script tools/check_global.py --project-root .` — unchanged global gate passes all suites, render/schema/tag/bootstrap checks, actionlint and online zizmor. Supply the configured CiCd-agent job token privately if required; never print it or use the maintainer profile.
- `git diff --check` — no whitespace errors.

**Pre-review results:** Parent scanner checks passed 22 tests on the current interpreter and 22 on Python 3.12. Behavioral nightly workflow checks passed 25 tests. The unchanged global gate passed all 14 suites / 308 tests plus committed render/input, immutable bootstrap, reproducibility, schemas/caller interfaces, acceptable Builds publication, actionlint 1.7.12 and online zizmor 1.32.0 checks. All 10 matrix rows have enabled passing coverage. Parent inspection additionally reproduced and repaired subprocess cwd resolution, function-local aliases and import search-path mutation gaps; regressions exercise real Git and the pinned detector. `git diff --check` passed. Useful logs are `story-9-parent-*.log` under implementation-artifacts (Git-ignored).
