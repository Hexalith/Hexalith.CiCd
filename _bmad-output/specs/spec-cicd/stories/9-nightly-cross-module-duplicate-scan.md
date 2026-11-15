---
title: 'Nightly cross-module duplicate scan'
type: 'feature'
created: '2026-11-15'
status: 'done'
baseline_revision: '23e1c39cf387151467cac4636267c780098a388d'
baseline_commit: 'cd20395ca6e2886c5d936c7ecc608f359277caa0'
review_loop_iteration: 3
followup_review_recommended: false
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

### 2026-11-15 — Resumed review 4 loopback (review_loop_iteration 2)

**Trigger:** The coverage model is sound, but traversal loses candidate working-directory contexts, and several parsing/runner/reflection paths still certify incomplete scope. All three current review layers completed. Real-Git reproductions are in `story-9-review4-blind-probes.log` and `story-9-review4-edge-probes.log`; the latter's fixture source is `story-9-review4-edge-probes.py.log`. The YAML-scalar regression mutation is in `story-9-review4-verification-gap.log`.

**Amended:** The non-frozen Design Notes below now specify the demonstrated cases D1–D17. Every case must either include the copied helper and produce a two-module real-detector finding or give the named source coverage failure. Do not silently skip any of these regressions.

**Known-bad state avoided:** `errors: []` with executed tracked helper code omitted, including imports through a symlink; all 22 concrete review reproductions exhibit that outcome. The separate YAML-scalar test mutation makes the actual controller falsely pass.

**KEEP and restoration:**

1. The parent reverted only these seven story paths to `23e1c39cf387151467cac4636267c780098a388d`: `.github/workflows/nightly.yml`, `docs/duplicate-scan.md`, `docs/nightly.md`, `setup/README.md`, `tools/scan_discovery.py`, `tools/tests/test_nightly_workflow.py`, `tools/tests/test_scan.py`.
2. Perform the previous change log's restore-from-`23e1c39cf387151467cac4636267c780098a388d` instruction for those paths first. Then restore the same seven paths from the reviewed source `cd20395ca6e2886c5d936c7ecc608f359277caa0` with `git restore --source=cd20395ca6e2886c5d936c7ecc608f359277caa0 --worktree -- <paths>`. This restores the completed coverage model and all C1–C16 fixes before re-derivation. Do not recreate them from scratch.
3. Preserve every existing test, bounded traversal, literal/module inclusion, precise resolution, diagnostics, policy and calibration. Keep `.jscpd.json`, npm manifests/lock, `tools/scan.py` and its lock, test lock, workflow, workflow tests, nightly docs and setup README verbatim from that reviewed source. Changes in this re-derivation belong only in `tools/scan_discovery.py`, `tools/tests/test_scan.py` and discovery explanations in `docs/duplicate-scan.md`.
4. Never restore or modify submodule gitlinks, the frozen `<intent-contract>`, the frontmatter `deferred` item, deferred-work ledger or detector investigation. The concurrent `/pushall` commit updated submodule pins independently; those are outside this story's changes.
5. Keep regression fixtures quoted below, or faithful equivalents, so the demonstrated issue cannot be replaced by a nearby passing example. Ordinary quoted data must stay data; conservative failures for unmodeled execution stay explicit.

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

### 2026-11-15 — Resumed review 4

- Three required layers completed; none skipped. 24 findings: 23 high, 1 medium. Each is independently retained below; parent traced all cited functions and read the retained reproduction outputs.
- Findings:
  - `[high]` `[bad_spec]` B1: PowerShell block-comment removal is not quote-aware. A real-Git probe with `Write-Output '<#'; python -m helper; Write-Output '#>'` omits helper.py without errors; the unconditional regex deletes the command. D3.
  - `[high]` `[bad_spec]` B2: An unknown wrapper can hide a computed interpreter operand: `xvfb-run python "${{ inputs.script }}"` returns no coverage error or helper. Rule 2 requires a diagnostic for this execution indirection. D4.
  - `[high]` `[bad_spec]` B3: `import builtins; builtins.__dict__['__import__']('helper')` bypasses reflective identity checks and omits scripts/helper.py; names() strips the builtins namespace before reflective() recognizes it. D5.
  - `[high]` `[bad_spec]` B4: A literal X=1 component masks the computed output in `printf "X=1\n%s" "$CONFIG" >> "$GITHUB_ENV"`; CONFIG can set PYTHONPATH while no diagnostic is emitted. environment() validates only the literal key it finds. D7.
  - `[high]` `[patch]` B5: `npm run go --ignore-scripts` still executes the named tracked package recipe; the local execution proof prints its marker, while discovery returns no files/errors. The blanket ignore-scripts early return is wrong. D8.
  - `[high]` `[bad_spec]` B6: `uv build` executes a tracked backend selected through build-system backend-path, proven by a synthetic backend marker; uv() returns None for non-run commands and omits that code. D9.
  - `[high]` `[patch]` B7: `xvfb-run python -c "import pkg.ns"` omits pkg/__init__.py when pkg/ns is a namespace. include_modules() continues before walking ancestors unless the exact module has a py/init/main blob. D10.
  - `[high]` `[bad_spec]` B8: After `cd support`, an unknown wrapper includes scripts/start.py using the initial cwd; its subprocess Python import omits support/helper.py without errors. include() passes cwds[0] and skips already-selected files. D1.
  - `[high]` `[bad_spec]` B9: An unquoted cat heredoc executes `$(cd support; python -m helper)` during shell expansion, while logical()/commands() treat the body only as data and omit the helper without errors. D11.
  - `[high]` `[bad_spec]` B10: `read -r PATH <<<support; helper` executes tracked support/helper (synthetic Bash proof), but the read builtin is unmodeled and emits no resolution-mutation diagnostic. D12.
  - `[high]` `[bad_spec]` E1: The edge real-Git probe independently reproduces B8 with `cd work; xvfb-run ../scripts/start.sh`: child traversal loses work as a cwd and omits work/helper.py. Same context-loss defect, D1.
  - `[high]` `[bad_spec]` E2: `if false; then cd a; fi` followed by `cd b; python -m helper` establishes only a/b in precise traversal, omitting actual b/helper.py. Each later literal cd must extend every possible preceding cwd. D2.
  - `[high]` `[patch]` E3: The edge probe independently confirms B5 using `npm --ignore-scripts run lint`; the named script executes and its module is omitted. D8.
  - `[high]` `[bad_spec]` E4: The edge probe independently confirms B1: quoted PowerShell comment delimiters delete the intervening import. D3.
  - `[high]` `[bad_spec]` E5: The edge probe mixes MODE=fast with "$NAME=support" in a GITHUB_ENV write; the literal key prevents a computed-key failure. Same incomplete emitted-output validation as B4. D7.
  - `[high]` `[bad_spec]` E6: A valid inline Python operand over 4096 bytes behind xvfb-run is silently ignored by module_references()/imported(), omitting its imported helper with errors empty. A resource bound must fail visibly. D13.
  - `[high]` `[bad_spec]` E7: The edge unquoted heredoc computes its module through `$MODULE`; body expansion is ignored, giving no error. Same heredoc execution defect as B9. D11.
  - `[high]` `[bad_spec]` E8: `python -m poetry run lint` bypasses the project-runner recipe checks even with tracked pyproject.toml; only task_runner() is called for absent non-local modules. D14.
  - `[high]` `[patch]` E9: `bash --rcfile setup.rc -ic true` executes tracked startup source (local Bash proof); shell_options() discards the rcfile operand and discovery omits its helper without errors. D15.
  - `[high]` `[patch]` E10: An imported scripts/helper.py symlink is found by import_module() but silently dropped by add_module() regular() checks; no unsafe-import error reaches the module. D16.
  - `[high]` `[patch]` E11: `uv run --project tools lint` discards the project selector then searches only the caller recipe roots, omitting the tools/pyproject.toml recipe and its helper without errors. Reject this unmodeled recipe location. D17.
  - `[high]` `[bad_spec]` E12: `getattr(__import__('subprocess'), 'run')(['python', '-m', argv[1]])` bypasses reflective checks because the import result is not represented in names(). The real-Git probe omits helper.py and emits no error. D6.
  - `[high]` `[bad_spec]` E13: The edge claim-level finding aggregates its twelve no-error omissions, substantiated by the retained real-Git probes. It shares their verified causes D1–D3/D6–D8/D11/D13–D17; it is retained as its own row.
  - `[medium]` `[patch]` G1: Pre-verified regression gap: removing only action() scalar include() in memory leaves all 52 ScanTests passing. Two real Git modules with inputs.script.default naming the copied helper then falsely pass. Add input-default and step-with scalar fixtures. D18.

Grouping: B8/E1/E13 share lost child contexts; E2 is separate conditional-cd state loss; B1/E4 share quote-insensitive comment removal; B4/E5 share partial environment-output validation; B5/E3 share the npm bypass; B9/E7 share expanding heredoc handling. Other concrete rows have distinct roots. E13 also carries the verified members of its aggregate claim. G1 is an independent test gap. Context propagation and unresolved execution require nontrivial changes, so bad_spec entries trigger the loopback; patch entries are moot and carried as the D constraints. No new deferral or intent ambiguity exists.


### 2026-11-15 — Resumed review 6

All three required layers completed; none skipped. The 21 findings have individual verdicts below (20 high, one medium). The parent inspected the cited functions, callers and exact real-Git/runtime probe fixtures. Blind probes and their source are retained in `story-9-review6-blind-probes.log` and `story-9-review6-blind-probes.py.log`; edge evidence is retained in `story-9-review6-edge-*.log`; the verification mutation and pinned-detector proof are in `story-9-review6-verification-ancestor.log`.

- `[high]` `[patch]` B1: Returned process namespaces bypass execution checks. The explicit ast.Attribute exemption allows `__import__('subprocess').run(['python3', '-m', sys.argv[1]])`; names() never resolves that call, and the probe executes omitted support/helper.py with errors empty. R1.
- `[high]` `[bad_spec]` B2: An intermediate package-directory symlink is invisible to import_module(). `scripts/pkg -> ../support` with `import pkg.helper` executes support/helper.py; final-path lookups find no candidate and produce no unsafe-path diagnostic. R2.
- `[high]` `[patch]` B3: include_modules() filters unsafe leaf imports before validation. `sys.modules['subprocess'].run(['python3', '-c', 'import helper'], cwd='scripts')` through scripts/helper.py symlink omits support/helper.py with no errors; the precise add_module() fix does not cover this caller. R3.
- `[high]` `[bad_spec]` B4: uv run can build a tracked local backend before its child executes. The run exemption omits backend-path=['support']; the actual uv runtime proof prints the backend's copied content. R4.
- `[high]` `[patch]` B5: npm --prefix info run lint treats the option operand info as a safe subcommand before checking recipe-location options. The actual npm proof executes omitted info/helper.py. R5.
- `[high]` `[patch]` B6: environment() exempts an entire computed output word containing GITHUB_ENV. CONFIG can supply PYTHONPATH and the runtime proof emits a valid resolution-changing environment file while discovery has no errors. R6.
- `[high]` `[bad_spec]` B7: A harmless command-prefix MODE=fast certifies a GITHUB_ENV heredoc body the validator never examines. The runtime output contains PYTHONPATH=support, and the subsequent helper remains omitted. R7.
- `[high]` `[bad_spec]` B8: printf output escapes are checked only by source spelling. An octal-escaped P in PYTHONPATH emits the forbidden key beside harmless MODE=fast and passes without errors. R8.
- `[high]` `[bad_spec]` B9: Backslash-newline removal in an expanding heredoc creates a command substitution across physical lines. Bash executes support/helper.py, while the per-line substitution check sees no executing construct. R9.
- `[high]` `[patch]` B10: Double-quoted PowerShell here-string bodies are marked expands=False. The actual PowerShell proof executes $(Set-Location support; python3 -m helper), but discovery omits its helper without errors. R10.
- `[high]` `[patch]` E1: The edge two-module/pinned-detector probe independently confirms B1 with computed -m sys.argv[1]. Both modules and overall report pass with the copied helper omitted. R1.
- `[high]` `[patch]` E2: builtins.__dict__.get('__import__')('helper') bypasses reflection checks. The nested Attribute parent exemption hides __dict__, and the final resolved name is outside the exact namespace check. The pinned-detector probe passes with scripts/helper.py omitted. R11.
- `[high]` `[patch]` E3: The edge probe uses a computed emitted word GITHUB_ENV$CONFIG to reproduce B6's substring exemption. The output can introduce PYTHONPATH; two modules pass without the copied helper. R6.
- `[high]` `[bad_spec]` E4: printf '%b' emits hex-escaped newlines and a PYTHONPATH line that the source-spelling parser misses. The pinned-detector probe falsely passes; this shares B8's unmodeled formatted-output root cause. R8.
- `[high]` `[patch]` E5: read PATH[0] writes the same Bash resolution variable as PATH, but the exact-name guard omits indexed destinations. Discovery has no errors and the actual Bash proof changes PATH. R12.
- `[high]` `[bad_spec]` E6: An over-limit literal -c program behind sys.modules['subprocess'].run is silently dropped by module_references()/imported(). The 4,400-character program imports the copied helper, but the pinned-detector report passes with no errors or findings. R13.
- `[high]` `[patch]` E7: python -m poetry --directory tools run lint silently returns from runner() before checking its project selector. The tracked tools recipe executes omitted tools/helper.py and the pinned-detector report passes. R14.
- `[high]` `[bad_spec]` E8: A mixed-quoted heredoc delimiter E'OF' is parsed as E. The parser swallows subsequent real commands as data, including a computed interpreter target that must fail coverage. The actual shell terminates at EOF. R15.
- `[high]` `[bad_spec]` E9: The edge direct-discovery/Bash proof independently confirms B9 with a computed -m operand across the continued heredoc lines. R9.
- `[high]` `[bad_spec]` E10: Claim-level AC1 failure is demonstrated by six independent real-Git/two-module/pinned-detector probes with result=pass, findings=[] and errors=[] while executed copied helpers are absent. This aggregate carries R1/R6/R8/R11/R13/R14; it does not replace the individual findings.
- `[medium]` `[patch]` G1: Pre-verified regression gap: changing only add_module()'s ancestor condition back to regular(init) leaves all 69 tests green. A two-module actual-detector proof falsely passes when a regular child has a symlink package initializer with copied code. Add explicit unsafe ancestor-initializer assertions. R16.

Grouping retains every row above. B1/E1, B6/E3, B8/E4 and B9/E9 share their respective demonstrated causes; all other concrete findings remain separate. E10 is an aggregate of its verified members. The nontrivial unsafe import, project-build, emitted-output and heredoc parsing changes route to bad_spec and trigger a loopback. Patch entries are moot until re-derivation and carried as R constraints. No intent ambiguity and no new deferral exists. `review_loop_iteration` is now 3.


### 2026-11-15 — Review 7

All three required layers completed; none skipped. The parent inspected every cited function and its callers, all retained exact fixtures, and actual Bash/PowerShell/Python/uv/npm/Poetry runtime output. All 20 findings have individual verdicts below (19 high, one medium). Evidence: `story-9-review7-blind-hunter7-probes.py.log` / `.log`, `story-9-review7-edge-probes.py.log` / `.log`, `story-9-review7-edge-runtime.py.log` / `.log`, and `story-9-review7-verification-context.log`.

- `[high]` `[patch]` B1: sys.modules.get('subprocess') bypasses subscript-only namespace normalization. The real-Git probe reports no errors and actual Python executes support/helper.py via a computed -m target. P1.
- `[high]` `[patch]` B2: asyncio.subprocess.create_subprocess_exec and from-import aliases miss the unsupported API prefix. The actual async Python fixture executes the omitted helper; add the public qualified spelling to the existing prefix guard. P2.
- `[high]` `[patch]` B3: from pkg import ns checks final child blobs before validating its intermediate directory. A regular pkg initializer plus symlink ns executes support/__init__.py and emits no error; use the existing import_path check on this child edge. P3.
- `[high]` `[patch]` B4: printf -v PATH is treated as a data command. The actual Bash fixture mutates PATH and runs omitted support/helper; apply the existing resolution-write failure policy to this variable-writing form. P4.
- `[high]` `[patch]` B5: declare -n indirect=PATH bypasses the read destination's direct-name check. Actual Bash resolves read indirect into PATH and executes the omitted helper. Explicitly fail this unmodeled alias declaration rather than implementing alias state. P5.
- `[high]` `[patch]` B6: GITHUB_PATH output still skips every word containing the destination marker. The retained emitted file adds support and actual Bash executes its helper, while discovery reports no error. Apply the already implemented bounded output/destination checks to this producer. P6.
- `[high]` `[patch]` B7: The preparation guard requires backend-path and omits conventional setuptools setup.py execution. Actual uv/setuptools reaches the fixture's setup marker with discovery errors empty. Fail unmodeled tracked build-system preparation instead of assuming absence of backend-path means no local execution. P7.
- `[high]` `[patch]` B8: --no-project/--no-sync bypass preparation even with explicit --with . installation. Actual uv executes support/backend.py. Check the demonstrated local dependency source before applying synchronization exemptions. P8.
- `[high]` `[patch]` B9: npm audit fix is classified as the read-only audit probe. The actual offline fixture executes its local file dependency's install hook and support/helper.py. Restrict the safe audit form. P9.
- `[high]` `[patch]` B10: A tracked project recipe named python shadows the interpreter before the late recipe guard runs. Actual Poetry invokes support.helper:main, but discovery analyzes only pass. Move the existing recipe-name check before interpreter dispatch. P10.
- `[high]` `[patch]` E1: PowerShell Write-Output emits arguments as separate lines; environment_output joins them with spaces. Actual PowerShell emits MODE=fast and PYTHONPATH=support as two lines, and both real-detector modules falsely pass. Use the producer's actual line semantics. P11.
- `[high]` `[patch]` E2: npm --workspace info run lint mistakes the selector value for NODE_SAFE info. Actual npm runs omitted info/helper.py and both actual-detector modules pass. Reject unmodeled leading selector/options before classifying a safe subcommand. P12.
- `[high]` `[patch]` E3: The edge two-module/pinned-detector and actual uv fixture independently confirm B7's setuptools setup.py omission. P7.
- `[high]` `[patch]` E4: The edge real-detector and actual Bash fixture independently confirm B5's nameref PATH mutation. P5.
- `[high]` `[patch]` E5: The edge real-detector fixture independently confirms B1's computed process execution through sys.modules.get. P1.
- `[high]` `[patch]` E6: An unknown Python consumer's one long literal command string is discarded before nested -c tokenization. The copied helper is omitted with errors=[] in both real-detector modules. Report the execution-literal bound at this outer entry point. P13.
- `[high]` `[patch]` E7: subprocess.run.__call__ evades a namespace-only dunder check. Both real-detector modules pass with a computed target's helper omitted. Apply the existing reflective API check to the nested dunder member. P14.
- `[high]` `[patch]` E8: $'EOF' is parsed as literal $EOF, swallowing subsequent execution as data. Actual Bash executes the later computed interpreter target, and both detector modules falsely pass. Fail unsupported ANSI/locale-quoted delimiter syntax explicitly. P15.
- `[high]` `[patch]` E9: Claim-level AC1 failure is demonstrated by all eight edge real-Git/two-module/pinned-detector fixtures returning pass with empty findings/errors and omitted copied code. This aggregate carries P1/P5/P7/P11/P12/P13/P14/P15 without replacing their individual rows.
- `[medium]` `[patch]` G1: Pre-verified gap: deleting only Python traversal's cwds.append(directory) leaves all 84 tests green. The unknown-consumer child-cwd fixture changes from a work/helper.py finding to a false pass. Add the actual two-module transitive-child assertion. P16.

Grouping produces 16 patch entries. B1/E5, B5/E4 and B7/E3 share their respective causes; E9 retains its proven members. Other concrete findings remain separate. Each smallest fix is an existing private predicate/check at a demonstrated edge, an explicit conservative failure, a normalization/spelling correction, or a test assertion. They introduce no public interface, runtime evaluation or new resolution state and do not change the captured intent or coverage model; no loopback is required. Re-engage the original implementation agent for these patches, preserving all 84 prior tests and adding real-Git/pinned-detector regressions for every reproduced case. No finding was deferred, and no new deferral was added.


### Parent inspection after review 7

- `[high]` `[patch]` P17: The new GITHUB_PATH output validator split only on LF, but AddPathFileCommand reads records with .NET File.ReadAllLines (CRLF, CR and LF). Parent discovery and actual Bash/.NET reproduction: `printf '/usr/bin\rsupport\r' >> "$GITHUB_PATH"` returned errors=[] and omitted support/helper; ReadAllLines returned /usr/bin and support, and the helper executed. Evidence: `story-9-parent-cr-path-probe.log`; primary source: [GitHub runner AddPathFileCommand](https://github.com/actions/runner/blob/main/src/Runner.Worker/FileCommandManager.cs). Split only emitted path records with the runner's line semantics and add a real-Git/two-module pinned-detector regression. Preserve source/detector LF semantics and the Linux GITHUB_ENV reader. This is a private one-line output-splitting correction at the demonstrated state, with no new interface or resolution model.

- `[high]` `[patch]` P18 (P13 completion): Parent inspection reproduced an oversized unknown-consumer command string with 5,500 characters of `true;` padding before `python -c 'import helper'`. The prefix-only execution check returned errors=[] and omitted helper.py. Evidence: `story-9-parent-outer-limit-probe.log`. The existing literal-limit contract requires a source failure for this execution-bearing suffix; extend the bounded check and the existing P13 regression while keeping ordinary large data supported. No interface or resolution model changes.

- `[high]` `[patch]` P19 (P1 completion): A stored namespace from `sp = sys.modules.get('subprocess')` followed by `sp.run(['python', '-m', sys.argv[1]])` still bypassed direct-expression normalization and omitted helper.py with errors=[]. Evidence: `story-9-parent-stored-module-get.log`. Apply the existing returned-process-namespace reflection guard to this known lookup and extend P1's detector regression, preserving direct literal calls. The smallest fix is one additional known call spelling in the existing predicate.

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


### Resumed review 4 re-derivation constraints

The following demonstrated cases extend the existing model; they do not relax it. Implement in `tools/scan_discovery.py`, add real-Git/two-module pinned-detector regressions in `tools/tests/test_scan.py`, and update the affected discovery explanations in `docs/duplicate-scan.md`.

- **D1 — context propagation:** Traverse every included child under all candidate established working directories, even if already selected; queue/visited bounds still apply. `cd support; xvfb-run python ../scripts/start.py` with a start subprocess importing support/helper.py, and the shell-child variant `cd work; xvfb-run ../scripts/start.sh`, must cover the helper or fail explicitly.
- **D2 — successive conditional directories:** Resolve each literal cd from every possible preceding cwd, retaining before/after candidates. `if false; then cd a; fi` then `cd b; python -m helper` must include b/helper.py, even with a/b/helper.py as a decoy.
- **D3 — PowerShell quoting:** `<#` and `#>` inside quoted strings are data, never comment delimiters. Preserve physical line diagnostics and actual inline/multiline block comments.
- **D4 — hidden computed execution:** Unknown consumers must not bypass Rule 2. `xvfb-run python "${{ inputs.script }}"` must fail with a source coverage diagnostic; an unknown consumer of purely literal script/module operands stays included. Preserve ordinary quoted nonexecuting data.
- **D5 — builtins reflection:** Fail reflective builtins/__builtins__ namespace access, including `builtins.__dict__['__import__']('helper')`; plain direct supported import APIs remain followed.
- **D6 — reflected imported namespace:** Fail a process/import module namespace returned from `__import__`/`importlib.import_module` when it is reflectively used, including `getattr(__import__('subprocess'), 'run')` with a computed target.
- **D7 — whole environment writes:** A harmless literal key cannot certify other computed output in a GITHUB_ENV write. Both `printf "X=1\n%s" "$CONFIG" >> "$GITHUB_ENV"` and `printf '%s\n' MODE=fast "$NAME=support" >> "$GITHUB_ENV"` must fail coverage. A completely literal harmless write can still pass.
- **D8 — npm named scripts:** `--ignore-scripts` suppresses lifecycle hooks, not an explicitly selected script. `npm run go --ignore-scripts` and `npm --ignore-scripts run lint` with tracked package.json must fail coverage or include their recipe's executed scripts. Preserve safe nonexecuting npm probes.
- **D9 — project build backends:** uv build (and equivalent handled project runners) with a tracked local build backend must not silently pass. Conservatively fail unmodeled tracked-project execution; do not execute or import its backend.
- **D10 — namespace ancestors:** A literal -c import of a namespace package still includes every tracked regular ancestor initializer, even when that namespace has no __init__.py or __main__.py.
- **D11 — expanding heredocs:** Unquoted heredocs perform shell expansions. Diagnose their unmodeled command substitution/backtick execution, including computed -m operands, while quoted heredoc bodies remain literal-reference data. Retain interpreter-fed-heredoc failures.
- **D12 — read environment mutation:** Shell `read` assigning PATH or another resolution-affecting/computed name fails coverage, including `read -r PATH <<<support`; harmless literal variable names need no new failure.
- **D13 — literal limits:** An execution-bearing literal over MAX_LITERAL cannot be silently ignored. Valid inline Python `x=0;` repeated 1100 times then `import helper`, behind xvfb-run, must include helper.py or report a coverage-limit failure. Preserve resource bounds and distinguish ordinary data as appropriate.
- **D14 — module-form runners:** Apply the same project recipe guard to `python -m poetry run lint` and other recognized Python project-runner module forms as to direct runner commands.
- **D15 — startup sources:** Shell --rcfile/--init-file cannot discard a tracked executing source; fail explicit coverage for unmodeled startup options, or include and traverse it.
- **D16 — unsafe imports:** A recognized imported blob that is a symlink/gitlink must fail as unsafe, never disappear through regular() filtering. Regular modules and namespace ancestor traversal remain supported.
- **D17 — project selectors:** Reject unmodeled uv --project recipe-root changes (or resolve them completely). `uv run --project tools lint` must not silently skip tools/pyproject.toml and its helper.
- **D18 — YAML scalar tests:** Test action input-default and step-with scalars that are the sole references to substantial copied tracked helper scripts. Both module manifests and actual cross-module findings must prove inclusion. Keep all existing 52 tests.

## Verification

**Commands:**

- `run-with-temp uv run --locked --script tools/tests/test_scan.py -v` — every detector/discovery/report matrix test passes, including real jscpd integration.
- `run-with-temp uv run --locked --script tools/tests/test_nightly_workflow.py -v` — existing workflow behaviors and new scan continuation tests pass.
- `run-with-temp uv run --locked --script --python 3.12 tools/tests/test_scan.py -v` — supported Python floor passes the same enabled cases.
- `run-with-temp uv run --locked --script tools/check_global.py --project-root .` — unchanged global gate passes all suites, render/schema/tag/bootstrap checks, actionlint and online zizmor. Supply the configured CiCd-agent job token privately if required; never print it or use the maintainer profile.
- `git diff --check` — no whitespace errors.

**Pre-review results:** Parent scanner checks passed 22 tests on the current interpreter and 22 on Python 3.12. Behavioral nightly workflow checks passed 25 tests. The unchanged global gate passed all 14 suites / 308 tests plus committed render/input, immutable bootstrap, reproducibility, schemas/caller interfaces, acceptable Builds publication, actionlint 1.7.12 and online zizmor 1.32.0 checks. All 10 matrix rows have enabled passing coverage. Parent inspection additionally reproduced and repaired subprocess cwd resolution, function-local aliases and import search-path mutation gaps; regressions exercise real Git and the pinned detector. `git diff --check` passed. Useful logs are `story-9-parent-*.log` under implementation-artifacts (Git-ignored).

## Review 5 verification and handoff (historical)

D1–D18 are implemented in `tools/scan_discovery.py`, with 17 added regression methods in `tools/tests/test_scan.py` (all original 52 retained) and matching discovery documentation in `docs/duplicate-scan.md`. The parent inspected the complete code/docs diff at `story-9-review5.diff.log` and audited all ten acceptance-matrix rows against enabled passing tests (`story-9-rederive3-matrix-audit.log`).

Final focused runs passed: 69 scanner tests on the current Python, 69 on Python 3.12, and 27 nightly workflow tests. Logs: `story-9-rederive3-scan.log`, `story-9-rederive3-scan-py312.log`, `story-9-rederive3-workflow.log`. The earlier parent global gate passed, including online actionlint/zizmor and 69 scanner tests, before the last D4/D3/D12 scanner refinements (`story-9-resumed-global.log`). A final global rerun remains pending; do not represent the earlier gate as verification of those final refinements.

All three required final reviewers were launched against `story-9-review5.diff.log`; each failed before reviewing with: “Your access token could not be refreshed because you have since logged out or signed in to another account. Please sign in again.” Retrying the blind reviewer produced the same error. No final-review findings or clean verdict were produced. The step-04 unavailable-subagent fallback requires a halt and standalone review prompts.

Standalone prompts, with their referenced diff, claims and reviewer instructions inlined, are retained as `story-9-review5-blind-hunter-prompt.log`, `story-9-review5-edge-case-hunter-prompt.log` and `story-9-review5-verification-gap-prompt.log` in implementation-artifacts. Resume this `in-review` story after restoring agent authentication, or run the three prompts in separate sessions and return all findings. Then triage, fix any surviving findings, run final verification and follow step 5. No new deferral was added. Concurrent submodule/gitlink changes belong to another workspace operation and were not modified by this story.


## Resumed review 6 re-derivation constraints

### 2026-11-15 — Review 6 loopback (review_loop_iteration 3)

**Trigger:** Review 6 demonstrates incomplete coverage through unsafe intermediate imports, runner preparation, formatted environment output and heredoc parsing. The known-bad state is result=pass with errors=[] while executed copied helper/backend code is absent. The frozen intent and original acceptance criteria remain unchanged.

**Amended model:** Safety validation covers every import-path component and every literal-module fallback. An execution coverage bound must fail visibly at every execution-bearing literal-sequence entry point. Environment-write validation examines the complete emitted output, including heredoc bodies and printf formatting, or fails as unmodeled; input source spelling and unrelated assignments cannot certify the output. Shell/heredoc parsing applies quote removal and continuation semantics before determining boundaries or executable expansion. Project-runner preparation can execute module code before the visible child and is part of scope.

**Restoration and KEEP:** Before re-derivation the parent restores only tools/scan_discovery.py, tools/tests/test_scan.py and docs/duplicate-scan.md to baseline_commit cd20395ca6e2886c5d936c7ecc608f359277caa0. Restore the completed D1–D18 implementation first with `git apply --include=tools/scan_discovery.py --include=tools/tests/test_scan.py --include=docs/duplicate-scan.md _bmad-output/implementation-artifacts/story-9-review6.diff.log`, then implement the R constraints. This reviewed snapshot preserves every existing test (69), positive literal/candidate-context traversal, source diagnostics, safe nonexecuting probes, conservative failures and resource bounds. Do not recreate it from scratch. Preserve the scanner controller, policy, package/lock files, workflow and its tests, nightly/setup docs, frozen intent, frontmatter deferred item, deferred ledger, detector investigation and every submodule/gitlink. Scope changes to discovery, its focused tests and discovery documentation.

- **R1 — returned namespaces:** A process/import namespace returned by __import__ or importlib.import_module cannot exempt attribute-based execution from reflection coverage. The exact computed-target reproduction above must fail explicitly or be fully resolved; direct supported local imports stay supported. Parent implementation inspection also reproduced `sys.modules['subprocess'].run(['python', '-m', sys.argv[1]])` with errors=[] and its helper omitted. The same execution-position rule must cover this known process namespace: resolve it or fail computed targets, while preserving literal targets and direct imports.
- **R2 — intermediate unsafe imports:** Inspect tracked package-path components, not just final module filenames. Importing pkg.helper through a symlink/gitlink pkg must fail explicitly; do not follow the link or treat it as an installed non-local module.
- **R3 — unsafe literal-module fallback:** Apply the same unsafe-leaf and unsafe-ancestor checks in include_modules(), including literal -c imports behind unrecognized consumers. Never silently filter an unsafe known candidate with regular().
- **R4 — project preparation:** uv run with a tracked local build backend must not pass merely because its visible child is harmless. Diagnose unmodeled local project preparation before the child; do not execute or import the backend. Preserve the existing nonexecuting/version probes and fully supported runner forms.
- **R5 — runner option order:** npm --prefix info run lint (and analogous recipe-location selectors) must fail for the unmodeled location before an option value can be classified as a safe subcommand. Keep plain nonexecuting npm info/version/audit probes supported.
- **R6 — environment destinations:** A computed emitted word is never exempt merely because it contains the GITHUB_ENV marker. Both $CONFIG$GITHUB_ENV and GITHUB_ENV$CONFIG must fail; only an actual, understood destination is exempt.
- **R7 — heredoc output:** MODE=fast cat >> "$GITHUB_ENV" <<EOF with body PYTHONPATH=support must fail coverage. A harmless command-prefix assignment cannot certify body output. Validate all output or fail the producer conservatively.
- **R8 — formatted output:** Octal/hex escape expansion and printf %b must not hide environment keys or newlines. The two exact review fixtures must fail; completely understood harmless literal echo/printf writes can pass. Do not execute shell/module code to evaluate output.
- **R9 — heredoc continuation:** Fold unquoted heredoc backslash-newline continuations before checking command substitutions, retaining physical source diagnostics. A dollar followed by backslash-newline then (python -m "$MODULE") must fail explicitly. Quoted bodies stay literal-reference data.
- **R10 — PowerShell here-strings:** Double-quoted here-strings expand subexpressions; fail their unmodeled execution. Single-quoted here-strings remain data. Preserve line positions and existing comment/quote handling.
- **R11 — nested builtins reflection:** Detect builtins.__dict__.get('__import__')('helper') and equivalent namespace reflection. Existing direct supported import calls and ordinary data remain supported.
- **R12 — indexed read destinations:** read PATH[0] and indexed resolution-variable destinations fail as resolution-affecting writes, along with computed variable names. Preserve harmless literal destination names.
- **R13 — literal fallback bounds:** Behind an unrecognized Python process consumer, the valid literal -c program `x=0;` repeated 1100 times followed by import helper must either include the copied helper or fail with a source coverage-limit diagnostic. Retain bounds and avoid silently discarding execution-bearing literals; ordinary large data need not fail.
- **R14 — project selectors in module runners:** python -m poetry --directory tools run lint must fail for the unmodeled project location. Apply equivalent guarding to direct and module-form recognized project runners, including options before run.
- **R15 — whole heredoc delimiter:** Parse the complete quoted/unquoted delimiter word, including E'OF', and stop at its quote-removed EOF boundary. Preserve subsequent execution diagnostics instead of swallowing the rest of the source as data. Unsupported delimiter syntax must fail visibly.
- **R16 — unsafe initializer test:** Extend the real-Git/two-module pinned-detector tests with a regular imported child beneath symlink and gitlink __init__.py ancestors. Assert source coverage errors for both modules; mutation back to regular(init) must fail this regression.

Every concrete reproduction above needs an enabled regression through real Git and the actual pinned detector, asserting either the copied target's finding or its named source diagnostic. Keep all prior 69 scanner tests and all 27 workflow tests. After implementation run focused current/Python-3.12 verification, inspect the complete diff, audit all ten matrix rows, then run the three review layers again. The earlier final-global run started before this loopback and must not be described as final verification unless it actually exercised the final implementation.


## Review 7 handoff

R1–R16 and the parent-discovered positional-uv and computed sys.modules cases are implemented. All 69 prior scanner tests remain, with 15 new methods (84 total). The parent read the complete 1,346-line implementation diff, checked the exact final implementation snapshot, and audited all ten matrix rows against enabled passing tests. The final original-offset, four-language, partial-failure, policy, empty-scope, live-main and nightly-continuation checks remain intact.

Focused verification passed: 84 current-Python scanner tests (`story-9-rederive4-scan.log`), all 84 tests on Python 3.12 after the final fixture corrections (`story-9-final-r6-scan-py312.log`), and 27 workflow tests (`story-9-rederive4-workflow.log`). The R16 mutation was rejected by both symlink/gitlink initializer subtests (`story-9-rederive4-ancestor-mutation.log`). `git diff --check` passed. The earlier global gate passed 14 suites / 357 tests and online audits before R1–R16 (`story-9-pre-review6-global.log`); final global verification remains pending.

A concurrent operation committed only builds-version at 95d74ced9fc9707ca6dd6961faf786d6d93ef6f5, advancing HEAD from baseline_commit. This story did not create that commit or edit builds-version or any gitlink. The review diff covers all story changes since the preserved baseline_commit and excludes that independently committed version bump and unrelated submodule work. Final global verification uses the current repository state. No new deferral was added.


## Final verification and completion

Story 9 is done. All three review layers completed in reviews 6 and 7; all verified findings and parent inspection variants were fixed. R1–R16 preserve the prior discovery model and its original 69 tests; P1–P19 add the remaining private guards and regressions. Final scanner coverage is 101 enabled methods, retaining all prior cases, including two-module real-Git/pinned-detector findings and named conservative failures.

Final current-Python and Python 3.12 scanner runs each passed all 101 tests without skips (`story-9-verified-scan-current.log`, `story-9-verified-scan-py312.log`). All 27 workflow tests passed (`story-9-final-workflow.log`). The unchanged global gate exited 0: all eight gates, 14 suites / 389 tests, committed render/input/bootstrap, reproducibility, schemas/caller interfaces, acceptable Builds publication, actionlint and online zizmor passed (`story-9-final-global.log`). `git diff --check` passed. The parent verified every matrix row against enabled passing tests (`story-9-verified-matrix-audit.log`).

The initial verification wrapper's source-fingerprint guard detected the known P18/P19 corrections made while unrelated integration suites were running. Both scanner suites were rerun after those corrections and passed with unchanged final source hashes; the global scanner suite ran afterward and also passed all 101 tests. That wrapper metadata check was the only nonzero exit; check_global.py itself exited 0. Final hashes and results are recorded in `story-9-final-verification.json.log`. Verification HEAD was 95d74ced9fc9707ca6dd6961faf786d6d93ef6f5; the original baseline_commit remains unchanged.

No new work was deferred. The original unverified eligible-source accounting follow-up remains in frontmatter; no substantive detector omission was reproduced. The deferred-work ledger, detector investigation, policy/locks, workflow/controller/setup/nightly files and all submodule/gitlink work remain outside this completion commit.
