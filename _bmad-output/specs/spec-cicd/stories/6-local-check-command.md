---
title: Local check command
type: feature
created: '2026-11-14'
status: done
baseline_revision: 5fab90e7dd140493842dfc43b84d0e846d06d5b2
implementation_repository: references/Hexalith.Builds
implementation_revision: 14f87f2dc5dfce9832154b9fd3aa8159fe3ab73c
implementation_baseline_revision: 0b6400457ca646d63a0c21bdad471f9c861e0c5b
review_loop_iteration: 0
followup_review_recommended: false
context: []
warnings: [oversized]
deferred: []
---

<intent-contract>

## Intent

**Problem:** Modules lack the Builds-provided local command that checks the same commit with CI stages 1–3 before a push (CAP-3; AD-15).

**Approach:** Provide `python3 references/Hexalith.Builds/check.py`. Verify Builds Git identities before JSON, require the AD-4-loaded exact `buildsTag`, then reuse the guard with `origin/main..HEAD` and existing build/unit executors.

## Boundaries & Constraints

**Always:** Python ≥3.12 standard library runtime; full canonical Git commit identities; inspect HEAD gitlink before reading JSON, then ensure checkout/gitlink/tag equality; strict shared loader; guard before product commands; CI Release/package-mode/analyzer/warnings-as-errors/audit-off flags; evaluated project classification and first-failing-project semantics. Operate on a committed clean module and required submodule checkouts to avoid testing content different from HEAD. Derive trusted module identity from GitHub origin, never JSON or inherited Actions variables. Inspect declared direct dependencies without changing their checkout. Preserve guard ownership message, module SDK selection and process failures.

**Never:** Hooks, integration execution, environment setup, restore writes, recursive initialization, checkout retargeting, pre-push hook, live module adoption, copied policy/classification/flags, changed frozen legacy runtime.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|---------------|---------------------------|----------------|
| Aligned module | HEAD gitlink = separate initialized Builds HEAD = peeled buildsTag | Guard over origin/main..HEAD, restore/build once, classified unit projects | Success only when all stages pass |
| Checkout mismatch | Missing/wrong-mode gitlink, uninitialized or different Builds checkout | Reject before malformed JSON or SDK work | Clear nonzero ownership/pin diagnostic |
| Config/tag mismatch | Missing buildsTag, invalid/schema-mismatched JSON, unavailable/different exact tag | Shared loader/tag validation rejects before product execution | Nonzero diagnostic |
| Uncommitted inputs/dependency mismatch | Dirty/staged/untracked inputs or required direct dependency absent/misaligned | Require committed inputs or initialization without writing caller state | Nonzero actionable diagnostic |
| Non-build module | Valid solution:none | Run guard only | Never invoke SDK |
| Failure | Guard/build/unit failure | No successor stages/projects; unit project completes internally | Nonzero, preserve product exit status |
| Commit range | Valid empty/nonempty origin/main..HEAD, or absent base | Reuse explicit full endpoints, ignore inherited event payloads | Missing base fails; empty range lints no commits |

</intent-contract>

## Code Map

All implementation paths below are relative to `references/Hexalith.Builds/`.

- `Github/lib/ci_config.py::load_config` — sole strict loader; ordinary modules require buildsTag; schema beside code.
- `Github/lib/guard.py::run` — existing HEAD ownership/action/audit/commit guard; pass frozen ref, explicit commit_range, and no-op output emitter.
- `Github/lib/guard_commitlint.py::select` — explicit endpoints already support empty ranges independently of inherited event files.
- `Github/lib/expected_state.py::Git`, `validate_context` — sanitized read-only Git/context and fixed anonymous delivered transport.
- `Github/lib/ci_pipeline.py::prepare_config`, `restore_and_build`, `run_unit_tests` — shared stage 2–3 APIs; `initialize_submodules` retargets checkouts and must not be called locally.
- `Github/lib/tests/test_ci_pipeline.py` — fake SDK/real SDK behavioral fixtures and independent mandatory-flag assertions.
- `Github/lib/tests/test_guard.py`, `test_expected_state.py` — real Git/transport fixtures for ownership and explicit local range tests.
- `Tools/ci/run_python_tests.py` — automatically discovers `Github/lib/tests`; no registration needed.
- `Tools/ci/README.md`, `README.md` — prerequisites and command documentation.
- Canonical companions: architecture AD-4/15 and `pipeline-stages.md`. All 20 prior stories are done with no unchecked tasks. No delivered production refs exist; use temporary fixtures. Warm local NuGet caches need a documented parity policy rather than weakened restore flags.

## Tasks & Acceptance

**Execution:**
- [x] `check.py` and `Github/lib/local_check.py` — add narrow local CLI/orchestrator, Git identity/cleanliness/direct-dependency checks and shared stages; avoid mutation and inherited Actions context.
- [x] `Github/lib/tests/test_local_check.py` — behavioral CLI and real Git coverage for matrix, guard-to-SDK sequencing, classification/failure propagation and nonmutation; include SDK-backed validation where practical.
- [x] `README.md`, `Tools/ci/README.md` — document command, committed-clean scope, SDK/Node/network/origin/tag prerequisites, local cache behavior and failure recovery.

**Acceptance Criteria:**
- Given a committed module with aligned Builds and available dependencies, when the documented command runs from its repository, then the same guard/build/unit implementation determines stages 1–3 and no hook or integration command executes.
- Given mismatched Builds and malformed module JSON, when the CLI runs, then the Git identity failure is reported before any JSON failure or product command.
- Given a failing unit project, when the CLI runs, then all its tests execute and later projects do not run.
- Given any invocation, when it finishes, then the caller index, source files, Git refs and submodule checkouts remain unchanged apart from normal ignored build outputs/tool caches.

## Spec Change Log

## Review Triage Log

### 2026-11-14 — Review pass

- verdicts: 17 findings — high 0, medium 10, low 2, false 5, maybe-false 0
- findings:
  - `[medium]` `[patch]` V1: successful public CLI path is unverified — Pre-verified gap: successful tests bypass main, so return 0 -> return 1 survives. Add successful and product-failure subprocess tests with actual guard orchestration and controlled external tools. Correction applied; covered by the 29-test focused suite passing on Python 3.12 and 3.14.
  - `[medium]` `[patch]` E1: configured fsmonitor executes during cleanliness checks — Parent reproduced caller marker creation; disable fsmonitor for every local Git handle and test that the helper cannot run. Correction applied; covered by the 29-test focused suite passing on Python 3.12 and 3.14.
  - `[medium]` `[patch]` E2: executable clean/process filters run during status — Parent reproduced caller marker creation; refuse effective executable filters before worktree comparisons and test nonexecution. Correction applied; covered by the 29-test focused suite passing on Python 3.12 and 3.14.
  - `[medium]` `[patch]` E3: rejected checks can mutate caller state through configured Git helpers — Same reproduced fsmonitor/filter roots as E1/E2; the shared Git-handle override and filter rejection address the composite claim. Correction applied; covered by the 29-test focused suite passing on Python 3.12 and 3.14.
  - `[false]` `[reject]` A1: no new local-versus-hosted same-commit comparison — No divergent outcome identified: the implementation delegates to the same CI APIs, and retained behavioral workflow plus real SDK tests exercise their stages. Production delivered refs do not exist yet; adoption remains separate.
  - `[false]` `[reject]` A2: new failing-project test uses SDK completion markers — Existing test_ci_pipeline.RealSdkTests exercises real failing xUnit projects under both runners, proves all tests complete and later projects stop, and passed in both full suites. The local command delegates directly to that tested executor.
  - `[medium]` `[patch]` A3: successful entrypoint subprocess path is absent — Same regression gap as V1; add public CLI success and failing-product exit assertions. Correction applied; covered by the 29-test focused suite passing on Python 3.12 and 3.14.
  - `[false]` `[reject]` A4: local readiness failures differ from hosted environment setup — Installed SDKs, available base/tag objects and aligned committed checkouts are prerequisites to checking a commit. Rejecting unavailable local inputs does not demonstrate a different guard/build/unit verdict for that commit.
  - `[false]` `[reject]` A5: dependency snapshots are less comprehensive than module/Builds snapshots — No dependency mutation outcome identified. Dependencies receive the same read-only checkout/cleanliness validation; E1/E2 repair its demonstrated helper side effects for every handle. Tests explicitly prove checkout preservation and no nested initialization.
  - `[false]` `[reject]` A6: diff alone cannot prove commit/push completion — Commit and remote verification are finalization operations after review, not a defect in the reviewed source. Record full revision and remote availability at finalization.
  - `[medium]` `[patch]` B1: fsmonitor remains enabled for diff and ls-files — Parent reproduced the exact behavior; same fix and coverage as E1. Correction applied; covered by the 29-test focused suite passing on Python 3.12 and 3.14.
  - `[medium]` `[patch]` B2: status invokes executable filters — Parent reproduced the exact behavior; same fix and coverage as E2. Correction applied; covered by the 29-test focused suite passing on Python 3.12 and 3.14.
  - `[medium]` `[patch]` B3: shallow history silently truncates the explicit range — Parent reproduced two unpushed commits with only HEAD linted despite both endpoints resolving. Refuse shallow module history before guard with unshallow guidance and a regression. Correction applied; covered by the 29-test focused suite passing on Python 3.12 and 3.14.
  - `[medium]` `[patch]` B4: sources can change during the guard and still pass — Parent reproduced a guard tool factory changing a tracked project while the command returned success. Revalidate frozen HEAD/tag/checkout identities and cleanliness before product work and success, with mutation regressions; retain caller edits. Correction applied; covered by the 29-test focused suite passing on Python 3.12 and 3.14.
  - `[low]` `[patch]` B5: strip removes valid root-path whitespace — Both toplevel resolutions use strip(), so a trailing-space root changes identity. Remove only Git's output delimiter and test a whitespace-containing root. Correction applied; covered by the 29-test focused suite passing on Python 3.12 and 3.14.
  - `[low]` `[patch]` B6: origin spelling must match case-sensitive delivered branches — The existing delivered selector uses the repository basename verbatim. Clarify the canonical spelling/case prerequisite in both READMEs; avoid introducing a new network identity service. Correction applied; covered by the 29-test focused suite passing on Python 3.12 and 3.14.
  - `[medium]` `[patch]` B7: production entrypoint/tool composition is not exercised successfully — Same root as V1/A3. Copy guard assets into the committed miniature Builds checkout and run successful and failing-product public CLI subprocesses with controlled Git/npm/Node processes. Correction applied; covered by the 29-test focused suite passing on Python 3.12 and 3.14.

Seven shared-root correction entries were applied: five medium (CLI coverage, fsmonitor, executable filters, shallow history, state revalidation) and two low (path whitespace, canonical origin documentation). No findings deferred. Three reviewers launched together; the fourth launched when the three-reviewer capacity limit freed a slot. All four completed before triage. The claims document was excluded from the code diff and supplied separately to the edge-case layer to preserve review independence.


### 2026-11-14 — Review pass

- verdicts: 39 findings — high 0, medium 9, low 21, false 9, maybe-false 0
- findings:
  - `[low]` `[patch]` BH1: local setup failures carry the guard prefix and ownership trailer — ExpectedStateError always prefixes `guard:` and appends OWNERSHIP_MESSAGE (expected_state.py:48), so missing-base, shallow-history, origin, declaration and mid-run HEAD refusals told users to fix product code. Patched: those local prerequisites raise PipelineError with only their recovery action; Builds/dependency checkout and tag pin mismatches keep the matrix's ownership/pin diagnostic; tests updated.
  - `[low]` `[patch]` BH2: Builds-own-CI refusal is unreachable from a real Builds checkout — run() checked the module Builds gitlink before origin identity, and Builds has no such gitlink. Patched: origin identity and the Builds-origin refusal precede module pin checks; new `test_builds_origin_is_refused_before_module_gitlink_checks` errors under the old order.
  - `[low]` `[patch]` BH3: fsmonitor still runs in the shared xUnit VSTest `git ls-files` — ci_pipeline.py:325 runs Git with the caller environment, contradicting the README's all-operations claim; harm is limited to the caller's own helper during product stages that already run module code. Patched: Tools/ci/README.md limits the guarantee to the command's own Git inspections.
  - `[medium]` `[patch]` BH4: ignored files and initialized unselected submodules reach the local build — require_clean allows ignored files and uses `--ignore-submodules=all` while product stages run in the caller worktree. Grouped with BH5/EC2/EC3. Patched: both READMEs document the warm build-state parity policy (fresh clone with only Builds and selected dependencies), matching the spec's documented warm-cache approach rather than changed shared flags.
  - `[medium]` `[patch]` BH5: incremental local build can hide warnings CI rejects — Reproduced with SDK 11.0.100: a plain `dotnet build -c Release` followed by the CI-flag `--no-restore -warnaserror` build succeeded, while fresh outputs failed with CS0219. Same root and documentation fix as BH4.
  - `[low]` `[reject]` BH6: documented command omits `python -I` — The intent fixes the command as `python3 references/Hexalith.Builds/check.py`; only a caller Python environment that shadows standard-library modules is affected.
  - `[low]` `[reject]` BH7: product stages inherit the caller environment — Real only for unusual MSBuild-property variables; a fix needs an environment whitelist parameter on shared run_command that would also drop documented NUGET_* cache and SDK-selection variables, contrary to "Never: environment setup".
  - `[low]` `[patch]` BH8: cleanliness refusals do not name offending paths — Verified at local_check.py:86. Patched: refusals list up to ten staged, modified, untracked or hidden paths (`status --no-renames` keeps every record as `XY path`); the dirty-input test asserts the named path.
  - `[false]` `[reject]` BH9: successful run ends silently — Exit status 0 without failure output is the success signal; the guard prints "guard policy passed" and product tools print their own summaries, so no wrong conclusion follows.
  - `[low]` `[reject]` BH10: base and remote are hard-coded; forks — The intent mandates `origin/main..HEAD` and origin-derived identity; a fork main ahead of upstream is rare, and a `--base` option adds public surface.
  - `[low]` `[reject]` BH11: another Builds copy's check.py is not detected — Module developers run the documented pinned path; launching another copy is a deliberate Builds-development workflow, and detection adds a guard branch.
  - `[false]` `[reject]` BH12: recovery messages give no commands — Each diagnostic names the exact path or tag and action, the shallow refusal names its command, and Tools/ci/README.md documents recovery; no unrecoverable case was shown.
  - `[false]` `[reject]` BH13: `sys.dont_write_bytecode` in local_check's `__main__` is ineffective — Only an undocumented entry is affected; its bytecode is ignored by Builds .gitignore:341 so it never trips cleanliness, and check.py sets the flag before imports.
  - `[low]` `[patch]` BH14: dead invoke branch and missing origin cases in tests — The `self.invoke()` branch after rmtree was unreachable, and missing, multi-valued and dot-segment origins were untested. Patched: direct subprocess launch; the origin test covers those cases with exact messages. Gitfile submodule layouts need no test: production code resolves checkouts only through Git commands.
  - `[low]` `[patch]` BH15: local command platform scope is unstated — Node 24+ was already stated; the platform was not. Patched: Tools/ci/README.md states the command is validated on Linux and other platforms are untested.
  - `[low]` `[reject]` BH16: READMEs overlap and wrapping is uneven — Both files were required by the story's documentation task, no current contradiction was found, and consolidation is a restructure rather than a direct correction.
  - `[medium]` `[patch]` EC1: cleanliness ignores the caller's global excludes and autocrlf — expected_state.Git sets HOME, XDG_CONFIG_HOME and GIT_CONFIG_GLOBAL to the null device with GIT_CONFIG_NOSYSTEM=1, so a globally ignored file is untracked to status and refuses although the caller's `git status` is clean. Grouped with IA5. Patched: both READMEs document repository-local-only cleanliness with the `.git/info/exclude` and repository-config remedy; with BH8 the refusal names the file.
  - `[low]` `[patch]` EC2: initialized unselected submodule is hidden by `--ignore-submodules=all` — Verified; it matters only when a solution consumes an unselected submodule, which package-mode flags normally prevent. Grouped with BH4; documentation patched.
  - `[medium]` `[patch]` EC3: ignored MSBuild inputs and stale obj state reach the build — Verified by BH5's reproduction. Grouped with BH4; documentation patched.
  - `[low]` `[patch]` EC4: xUnit VSTest `git ls-files` runs the caller's fsmonitor — Same defect as BH3; README patched.
  - `[low]` `[patch]` EC5: Builds-own message is unreachable — Same defect as BH2; order patched and tested.
  - `[low]` `[reject]` EC6: edit-then-revert between revalidations reports success — Requires editing and reverting a tracked input while a stage runs; closing it needs a private export or content hashing.
  - `[low]` `[reject]` EC7: full caller environment reaches dotnet — Same as BH7.
  - `[medium]` `[patch]` EC8: origin-rejection subtests run after origin/main was deleted — Same defect as VG1; patched.
  - `[low]` `[reject]` EC9: tool-written tracked files refuse after build and differ from CI — Requires lock files that restore rewrites (a stale committed lock file that committing fixes) or unignored test outputs; preventing writes would change shared restore flags, which the intent forbids. With BH8 the refusal names the file.
  - `[medium]` `[patch]` VG1: origin-rejection subtests pass on the missing base, not the origin check — Pre-verified gap. Patched: the base is restored before the loop and every refusal asserts its message; a mutation accepting the Builds origin now fails the test.
  - `[medium]` `[patch]` VG2: mid-run Builds and dependency checkout changes are untested — Pre-verified gap. Patched: guard-time Builds edit plus build-time dependency edit/retarget tests; limiting revalidation to Builds without per-checkout cleanliness now fails all three cases.
  - `[medium]` `[patch]` VG3: index preservation never observes GIT_OPTIONAL_LOCKS — Pre-verified gap. Patched: stat-dirty tracked-input test; dropping `GIT_OPTIONAL_LOCKS=0` now fails it.
  - `[low]` `[patch]` VG4: duplicate committed `.gitmodules` path rejection is untested — Pre-verified gap. Patched: duplicate-section test; removing the check now fails it.
  - `[low]` `[patch]` VG5: fsmonitor helper runs during the unit stage — Same defect as BH3; README patched.
  - `[low]` `[patch]` IA1: local precondition failures carry OWNERSHIP_MESSAGE — Same defect as BH1; patched.
  - `[false]` `[reject]` IA2: tests use in-process runs, a fixture transport and shimmed git/npm/node — The shims replace only external transports and tools while the real guard, loader and pipeline code run; no production delivered refs exist (Code Map mandates temporary fixtures), and no divergent behavior was identified.
  - `[false]` `[reject]` IA3: no local-versus-hosted verdict comparison (merge ref, event range, additional SDK, cold cache) — carried from A1: the intent fixes `origin/main..HEAD` on HEAD and excludes environment setup, and the cache policy is documented.
  - `[false]` `[reject]` IA4: failing-project completion is simulated by the fake SDK — carried from A2: test_ci_pipeline.RealSdkTests exercises real failing xUnit projects and the command delegates to that executor.
  - `[medium]` `[patch]` IA5: cleanliness is judged without global excludes and post-stage refusals are untested on real layouts — Grouped with EC1; documentation patched.
  - `[false]` `[reject]` IA6: require_declarations duplicates CI's declaration check with different includes — CI's `git config --file .gitmodules` defaults to no includes exactly like `--blob`; clean committed inputs make the HEAD blob equal the worktree file; initialize_submodules cannot be reused because it retargets checkouts.
  - `[false]` `[reject]` IA7: SHA accepts only 40-hex identities — GitHub-hosted modules use SHA-1; a SHA-256 repository fails loudly; the same shared SHA serves the guard.
  - `[false]` `[reject]` IA8: the command never fetches its base — The AC requires unchanged refs, and both READMEs require fetching origin/main first; a missing base fails with that instruction.
  - `[low]` `[patch]` IA9: origin case sensitivity is documented rather than resolved — carried from B6: documentation already applied; no further change.

Twelve patch entries were applied this follow-up pass: five medium (warm build state, repository-local cleanliness configuration, origin-rejection test, mid-run dependency coverage, index-lock coverage) and seven low (local prerequisite diagnostics, Builds-origin order, fsmonitor scope, duplicate declarations coverage, named refusal paths, test cleanups, platform scope); one carried low patch entry needed no change. No intent_gap, bad_spec or defer entries. All four reviewers launched together and completed before triage; the claims document went only to the edge-case layer.


### 2026-11-14 — Review pass

- verdicts: 36 findings — high 0, medium 2, low 24, false 10, maybe-false 0
- findings:
  - `[low]` `[patch]` BH1: Git older than 2.31 ignores `GIT_CONFIG_COUNT`, so git_at's fsmonitor and untrackedCache overrides lapse silently — The `GIT_CONFIG_KEY_n`/`GIT_CONFIG_VALUE_n` environment arrived in Git 2.31, and neither README stated a minimum. Patched: both READMEs require Git 2.31 or later.
  - `[medium]` `[patch]` BH2: `safe.directory` is never applied — expected_state.Git nulls global and system config and git_at overwrites `GIT_CONFIG_COUNT`. A checkout owned by another user therefore fails at the first rev-parse with the ownership trailer, and there is no workaround. Patched: both READMEs require the module and its checkouts to be owned by the invoking user. The outside-work-tree refusal (BH4 group) also names ownership.
  - `[low]` `[patch]` BH3: proxy and CA settings are dropped without documentation — expected_state.Git and guard_tools.tool_environment whitelist an environment with no proxy variables and null the global Git/npm config. The READMEs said only "network access". Patched: both READMEs require direct connections and state that proxy settings are not applied.
  - `[low]` `[patch]` BH4: local setup and tool failures still carry the ownership trailer — Verified: outside a work tree, run()'s checked rev-parse raised ExpectedStateError. npm/Node failures come from the shared guard_tools diagnostics. Grouped with EC6/VG5. Patched:
    - rev-parse runs with `check=False` and refuses with PipelineError "run the command inside the module's Git work tree, owned by the current user";
    - new `test_outside_work_tree_refuses_without_guard_ownership_message`;
    - Tools/ci/README.md explains `trusted guard tool failed` and `commitlint tool failed` as Node/npm/network prerequisite failures.

    Probing prerequisites before the guard was not added, because it would add new branches.
  - `[low]` `[patch]` BH5: MinVer modules' `git status` can refresh the caller index — Works and Timesheets reference MinVer from Directory.Build.props, and MinVer runs `git status` under ci_pipeline.run_command's caller environment without `GIT_OPTIONAL_LOCKS`. Only the stat cache is rewritten, but the README claimed no index writes. Patched: Tools/ci/README.md says module build tools such as MinVer may refresh the stat cache as a manual `git status` does, with staged content unchanged.
  - `[low]` `[patch]` BH6: pull request title commitlint has no local equivalent — guard_commitlint.select lints `pull_request` titles (guard_commitlint.py:38-46), and the local command passes only `commit_range`. Patched: Tools/ci/README.md says CI also lints the pull request title, which has no local equivalent.
  - `[low]` `[reject]` BH7: running from inside a submodule checks that repository — This happens only when the command is deliberately started inside a dependency or Builds checkout, and Builds gets its explicit own-CI refusal. A superproject guard would add a branch and block intentionally checking a dependency module from its own checkout.
  - `[low]` `[patch]` BH8: in-process recorders are asserted after subprocess CLI runs — Verified at test_local_check.py:292 and :320: invoke() never touches `self.installations` or `self.transport`. Grouped with VG6. Patched: both tests install cli_controls() and assert that the new external_calls() ledger is empty. A mutation that moves the shallow refusal after the guard now fails on that assertion.
  - `[false]` `[reject]` BH9: "no SDK" assertions on `solution: "none"` fixtures cannot catch restore/build moved ahead of refusals — Any SDK work moved before the refusals also precedes the guard, which `test_guard_precedes_sdk_and_shared_flags_and_classification_apply` rejects. The refusal tests' `installations == []` or stderr assertions pin them before the guard, so no such regression ships unnoticed.
  - `[low]` `[patch]` BH10: the empty-filter-override test cannot observe helper execution — No attribute mapped a path to the filter and no file was stat-dirty, so Git never consulted the clean filter. Patched: the test adds `.gitignore filter=fixture` attributes and a stat-dirty `.gitignore`. With the override removed and the filter refusal disabled, the helper now runs and the test fails.
  - `[false]` `[reject]` BH11: the git shim skips the environment-leak assertion — The guard's Git receives only expected_state.Git's whitelisted environment, which test_expected_state.py:380-387 already checks against GH_TOKEN/GITHUB_TOKEN poison. git_at adds only fixed Git config keys.
  - `[low]` `[reject]` BH12: exit codes do not separate setup failures from product failures — The intent requires only nonzero failures and a preserved product status, and both are implemented. A distinct exit-code contract would be new public surface, and the diagnostic text already names the failing prerequisite.
  - `[low]` `[reject]` EC1: `.git/info/grafts` can truncate the range while `--is-shallow-repository` reports false — Grafts are a deprecated Git feature that must be created by hand. Refusing them would add a guard branch for a state that everyday clones never have.
  - `[low]` `[reject]` EC2: a commit that lands between revalidate's HEAD check and its status check passes — This needs the caller to commit within the milliseconds between two Git subprocesses. Closing the window for every checkout would need a second identity pass. It is the same concurrency risk class as the logged EC6 rejection.
  - `[low]` `[reject]` EC3: carried EC9 — Tool-written tracked or unignored files refuse after a stage with the uncommitted-input message. require_clean still reads as logged, and the refusal names the files.
  - `[low]` `[reject]` EC4: carried BH11 (follow-up pass) — Running check.py from another Builds tree is a deliberate Builds-development workflow, and detecting it adds a guard branch.
  - `[low]` `[patch]` EC5: a case-variant Builds origin skips the own-CI refusal — Verified: the exact comparison let `hexalith/hexalith.builds` fall through to the gitlink ownership error. Patched: the comparison is case-insensitive, because GitHub repository names are, and the origin test adds `git@github.com:hexalith/hexalith.builds`. Restoring the exact comparison now fails that test.
  - `[low]` `[patch]` EC6: outside a work tree, the generic rev-parse failure blames product code — Same root as BH4; patched there.
  - `[low]` `[patch]` VG1: an undeclared Builds entry in committed `.gitmodules` was untested — Pre-verified gap: narrowing require_declarations to the configured submodules passed every test, although CI's prepare stage refuses that module. Patched: new `test_undeclared_builds_gitlink_refuses_before_guard`; the mutation now fails.
  - `[low]` `[patch]` VG2: dependency refusals were not pinned before the guard — Pre-verified gap. Patched: the dependency test asserts no installations or transport calls after the undeclared, uninitialized, dirty and retargeted refusals. Replacing the pre-guard loop with `pass` now fails.
  - `[medium]` `[patch]` VG3: running from a subdirectory was unverified — Pre-verified gap on the everyday entry path: replacing the resolved root with `git = initial` passed every test. Patched: new `test_subdirectory_workspace_checks_the_module_root` runs from `.github`; the mutation now fails with the pin diagnostic.
  - `[low]` `[patch]` VG4: the staged-gitlink refusal never exercised `--ignore-submodules=none` — Pre-verified gap. Patched: a subTest commits `ignore = all` for Builds and stages a different gitlink. Removing the flag now fails.
  - `[low]` `[patch]` VG5: misleading ownership message outside a repository — Same root as BH4; patched there.
  - `[low]` `[patch]` VG6: two in-process assertions after CLI subprocesses are vacuous — Same root as BH8; patched there.
  - `[false]` `[reject]` IA1: carried A1/IA3 — There is no hosted-versus-local verdict comparison. The implementation delegates to the same shared stages, the intent fixes the local range, and it excludes environment setup.
  - `[low]` `[reject]` IA2: carried BH11 (follow-up pass) — Reading R2b: nothing proves the running check.py comes from the verified checkout.
  - `[false]` `[reject]` IA3: CI runs the Builds commit named by the workflow call, not the gitlink — The guard compares the module's rendered caller workflow, including its Builds workflow ref, with the accepted delivered branch. Its gitlink perimeter entry binds the gitlink to the trusted peeled buildsTag (expected_state.py:177). local_check also requires the tag to equal the gitlink, so both name the same commit.
  - `[false]` `[reject]` IA4: carried IA6 — require_declarations reimplements CI's declaration rule without retargeting checkouts, and reads the same inputs for clean committed modules.
  - `[false]` `[reject]` IA5: the staged gitlink c8c3473 does not contain the reviewed content — The reviewed working-tree patches were waiting for finalization. They are now committed and pushed as 14f87f2dc5dfce9832154b9fd3aa8159fe3ab73c, and the superproject gitlink is restaged to that commit, as the Verification section prescribes.
  - `[false]` `[reject]` IA6: carried IA2 (follow-up pass) — The shims replace only external transports and tools; the real guard, loader and pipeline code run.
  - `[false]` `[reject]` IA7: carried IA4/A2 — test_ci_pipeline.RealSdkTests exercises real failing xUnit projects, through the executor the command delegates to.
  - `[false]` `[reject]` IA8: carried IA3 (follow-up pass) — The hosted additional-SDK input is environment setup, which the intent excludes.
  - `[low]` `[patch]` IA9: product stages inherit IDE terminal variables, and this was undocumented — Verified: Props/Environment.Build.props sets `IDEBuild` from `TERM_PROGRAM=vscode`/`cursor` or `VSCODE_PID`/`VSCODE_CWD`, and Hexalith.Package.props then leaves `IsPackable` false, unlike CI. This is the common IDE case, not the unusual-property case logged for BH7. Patched: Tools/ci/README.md documents it and recommends a plain terminal. The environment is not rewritten, so the logged BH7 whitelist rejection stands.
  - `[low]` `[patch]` IA10: carried BH4 (follow-up pass) — Local stages see ignored files and unselected submodules. The documentation was already applied, so no further change.
  - `[false]` `[reject]` IA11: carried A1/IA3 — The event range and the pull request merge ref differ from the intent-fixed `origin/main..HEAD` on HEAD.
  - `[low]` `[reject]` IA12: carried BH6 (follow-up pass) — The documented command omits `python -I`, as the intent fixes it.

This resumed follow-up pass applied fourteen patch entries:
- Two medium: ownership/`safe.directory` documentation and subdirectory coverage.
- Twelve low: Git minimum, direct network, outside-work-tree diagnostics, MinVer index refresh, PR title, CLI ledger assertions, effective filter override, case-insensitive Builds origin, undeclared Builds coverage, pre-guard dependency assertions, `ignore = all` staged gitlink and IDE build properties.

One carried low patch entry needed no change. There were no intent_gap, bad_spec or defer entries. All four reviewers launched together in one message and completed before triage; only the edge-case layer received the claims document. The follow-up implementation subagent could not be re-engaged from a new session, so the parent applied the patches.


## Design Notes

Reject uncommitted inputs because the guard reads committed objects while builds read disk. Local dependency validation replaces CI checkout mutation. Accept standard GitHub HTTPS/SSH origins for repository context; reject unsupported origins explicitly. The command serves modules; Builds root has no Builds gitlink and is validated by its existing own CI instead.

## Verification

- Focused `Github/lib/tests/test_local_check.py` plus shared pipeline/guard tests — meaningful Git/SDK behavior and error precedence pass.
- Locked `Tools/ci/run_python_tests.py` under Python 3.12 and runner Python — all retained groups pass.
- Pinned workflow lint, public API check and exact-message commitlint — pass without changing policies.
- Commit and push implementation in Builds; record full pushed revision, then stage superproject gitlink with this story.


### Matrix test audit

All names below belong to `Github/lib/tests/test_local_check.py::LocalCheckTests` and ran without skips in the focused Python 3.12/3.14 suites.

| Matrix row | Passing coverage |
|---|---|
| Aligned module | `test_cli_success_and_product_failure_run_real_guard_and_preserve_status`;  `test_guard_precedes_sdk_and_shared_flags_and_classification_apply`; `test_actual_module_sdk_restore_build_and_evaluation` |
| Checkout mismatch | `test_cli_mismatched_checkout_wins_over_malformed_json_and_inherited_git`; `test_missing_wrong_mode_or_uninitialized_builds_precedes_json` |
| Config/tag mismatch | `test_invalid_config_and_missing_mismatched_or_unavailable_tag_fail_before_tools` |
| Uncommitted inputs/dependency mismatch | `test_dirty_staged_untracked_and_hidden_module_inputs_fail_without_mutation`; `test_direct_dependencies_must_be_declared_aligned_and_clean_without_initialization`; `test_dirty_builds_and_staged_gitlink_refuse_without_changing_inputs` |
| Non-build module | `test_cli_none_success_uses_real_guard_without_sdk`;  `test_none_runs_real_guard_and_empty_range_without_sdk_or_actions_outputs` |
| Failure | `test_cli_success_and_product_failure_run_real_guard_and_preserve_status`;  `test_guard_and_build_failures_stop_successors`; `test_failing_project_completes_and_preserves_status_without_later_projects`; `test_main_preserves_product_exit_status` |
| Commit range | `test_explicit_range_lints_all_messages_and_ignores_event_payload`; `test_none_runs_real_guard_and_empty_range_without_sdk_or_actions_outputs`; `test_missing_base_and_unsupported_origin_do_not_start_guard_or_sdk` |


## Auto Run Result

Status: done

Implemented the Builds-provided local command for CI stages 1–3:
- It verifies the committed Builds gitlink and its separate checkout before reading JSON.
- It validates their exact release tag through the shared loader, then validates committed local inputs and complete history.
- It runs the unchanged guard with explicit `origin/main..HEAD` endpoints, then reuses the shared restore/build and classified unit executors.
- Input or pin changes made during execution fail without undoing the caller's changes.

This resumed follow-up review pass hardened diagnostics, coverage and documentation without changing the stage composition.

Files changed (relative to implementation repository):
- `check.py`: the public module command, with trusted sibling imports and no bytecode writes.
- `Github/lib/local_check.py`: read-only identity and input checks, plus orchestration of the shared stages.
  - This pass: a local refusal outside a work tree, and a case-insensitive check for Builds' own origin.
- `Github/lib/tests/test_local_check.py`: 37 behavioral tests covering real Git, a real SDK smoke run, public subprocess CLI/tool composition, nonmutation and failure controls.
  - This pass added three tests (undeclared Builds, subdirectory invocation, outside work tree).
  - It also strengthened the CLI ledger, filter override, dependency ordering, `ignore = all` and origin-case assertions.
- `README.md`: the command and its prerequisites, now including Git 2.31+, direct network access and checkout ownership.
- `Tools/ci/README.md`: detailed stage behavior, prerequisites, recovery and NuGet cache policy.
  - This pass added: PR title scope, IDE terminal build properties, the MinVer index stat refresh and guard tool diagnostics.

Review findings, this pass (36):
- **Patched (14 entries; 2 medium, 12 low):**
  - medium: BH2 (ownership/`safe.directory`), VG3 (subdirectory coverage);
  - low: BH1, BH3, BH4+EC6+VG5, BH5, BH6, BH8+VG6, BH10, EC5, VG1, VG2, VG4, IA9.
- **Carried patch, no change:** IA10.
- **Deferred:** none.
- **Rejected, false:** BH9 (guard-before-SDK test plus pre-guard refusal assertions cover the ordering), BH11 (the Git environment whitelist is tested in test_expected_state), IA3 (the guard binds the caller workflow and gitlink to the trusted buildsTag), IA5 (finalization commits and pushes the reviewed patches). Carried: IA1, IA4, IA6, IA7, IA8, IA11.
- **Rejected, low:** BH7 (superproject guard would block legitimate dependency checks), BH12 (exit-code contract is new public surface), EC1 (deprecated grafts), EC2 (millisecond concurrent-commit race). Carried: EC3, EC4, IA2, IA12.

Each row in the Review Triage Log above records its reason. Earlier passes (17 and 39 findings) are logged there as well.

Follow-up review recommended: false. This dispatch resumed the follow-up pass of the completed first run. The staged story carried `status: done` and the first Auto Run Result, and the second review was logged as a follow-up pass but was never finalized. On a follow-up pass, only a patched high finding recommends another review, and none was found.
- Patched counts by verdict: high 0, medium 2, low 12.
- Both medium fixes were verified: VG3 by its mutation probe, and BH2 as a documented prerequisite. No unverified code risk remains.

Verification:
- Focused `Github/lib/tests/test_local_check.py`: 37 tests passed on Python 3.14.
- Mutation probes on a scratch copy: each new or strengthened test fails under the matching regression:
  - narrowed declarations, removed pre-guard dependency loop, `git = initial`, dropped `--ignore-submodules=none`, exact Builds-origin comparison, checked outside-tree rev-parse;
  - helper execution once the filter override and refusal are removed;
  - shallow refusal moved after the guard.
- Locked `Tools/ci/run_python_tests.py` under Python 3.12.13 and runner Python 3.14: 961 tests each, all 14 groups passed, with all 37 local-command tests and no local skips. `pwsh` from `~/.dotnet/tools` was on PATH, and a read-only GitHub token was supplied via `gh auth token`.
  - A first 3.12 attempt without those failed only on environment prerequisites: the Windows composite harness lacked `pwsh`, and the online zizmor test lacked a token.
- `python3 Tools/ci/lint_workflows.py` with read-only GitHub authentication: passed, 10 exact frozen composite findings and 0 new findings.
- Locked `Tools/ci/check_public_api.py` at 14f87f2dc5dfce9832154b9fd3aa8159fe3ab73c: compatible, 2590 entries, no removals against v5.2.2.
- `git diff --check`: passed.
- The exact full commit message `fix(cicd): harden local check diagnostics and coverage` was validated with the owning repository's pinned `@commitlint/cli` 21.2.4 (exit 0) before committing.

Residual risks:
- The command assumes installed SDK/tools, accepted delivered ownership data, a canonical origin, direct network access and checkouts owned by the caller.
- It validates the host's stages 1–3 only. Warm NuGet caches, existing ignored outputs and IDE terminal variables can make local results differ from CI; the documented parity runs cover this.
- No adopted production delivered branch exists yet for a real end-to-end remote check; confirm that at first module adoption.
- Live module adoption and stage 4 remain separate work.

Repository finalization:
- Builds `main` was pushed from c8c3473cc205ef811bd9fb3ee23fe7d375f9c566 to 14f87f2dc5dfce9832154b9fd3aa8159fe3ab73c, the verified origin/main.
- In CiCd, the updated submodule pointer and this canonical story are staged for the caller, per the superproject submodule procedure.
- The deferred-work ledger was not modified.
