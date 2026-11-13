---
title: "4-3 Delivery's validate job"
type: feature
created: '2026-11-13'
status: done
story_id: '4-3'
review_loop_iteration: 0
followup_review_recommended: false
baseline_revision: 76096c764335ade1e93e949e1aa18151770ff36d
builds_contract_tag: v5.1.0
builds_contract_revision: 9ebc31f606bc02f8a0ec2f1ec344127e2468c6b4
context:
  - '{project-root}/_bmad-output/specs/spec-cicd/SPEC.md'
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md'
warnings: [oversized]
deferred: []
---

<intent-contract>

## Intent

**Problem:** CiCd can render owned files but has no delivery validation entry point. CAP-4 needs a global verdict and independent module verdicts before later delivery can advance accepted renders safely.

**Approach:** Add `deliver.yml` with its secret-free `validate` job only, backed by one reusable global-check script and an anonymous module-check orchestrator (AD-3/6). Emit one JSON verdict even when checks fail. Work exclusively in this superproject; this invocation halts after planning.

## Boundaries & Constraints

**Always:** Enumerate exactly `setup/*.yml` through the existing registry; reject Builds. Run global checks through the same `tools/check_global.py` entry point that the future nightly bump will invoke. Check render reproducibility, committed render, selected schemas/readers and caller interfaces, tool tests, actionlint, online zizmor, and acceptable Builds publication. Consume Builds code/schemas only from Git objects at `builds-version`, independently of its checkout HEAD. Perimeter checks start only once that pin names a release containing story 4-1's schema/library; current `v5.1.0` satisfies this prerequisite. An older/incomplete pin fails the global verdict explicitly, without a HEAD fallback or silent perimeter-check skip. Read module content from anonymous shallow clones of live `main`; never execute it. Module failures remain independent, including when global checks fail. Python >=3.12; PEP 723 dependencies/adjacent committed locks and `uv run --locked`. The only workflow credential is its read-only `GITHUB_TOKEN`.

**Never:** Add the deliver job, App checks, `cicd-app`, secret references, writes to modules or delivered refs, nightly/bump implementation, guard/restore, duplicate scanning, onboarding, or workflow-text assertion tests. Do not compare live module owned state against the proposed perimeter: validate judges the candidate render and enabled action availability, while later delivery repairs owned drift. Do not modify Builds, `builds-version`, submodule pointers, production setup registrations, templates or the interim story 10-2 policy. No dispatch, publication, push or live configuration mutation belongs to this story's validation.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
| --- | --- | --- | --- |
| Empty registry | Existing README and `rendered/.gitkeep` only; valid pin/global checks | `{"global":true,"modules":[]}` | Exit 0; still exercise nonempty synthetic fixtures |
| Passing modules | Registered direct submodules with valid rendered CI and every enabled action on live main | Global boolean plus sorted, unique passing repository stems | Exit 0 when all checks pass |
| Independent failure | One module lacks an action, is not a direct submodule, has conflicting hook/job names, a disabled exclusion target, or a failed clone | Omit only that module; retain all other passing names and the independently computed global verdict | Diagnose repo/check on stderr; exit 1 after output |
| Global failure | Render/schema/interface/test/lint/tag check fails, while some module checks pass | `global:false`; still list independently passing modules | Exit 1 after output; no ref could advance from this verdict |
| Invalid module document | Malformed/missing rendered CI, unsupported schema or invalid semantic configuration | That module fails; others are still checked | Schema/render failure also fails the global verdict |
| Unusable registry/contract | Registry cannot be safely enumerated, or selected contract is unavailable | `global:false`; no unvalidated module name passes | Emit conservative verdict and contextual diagnostic; no guessed defaults/contracts |
| Pin prerequisite | Pre-4-1 tag or tag lacking perimeter schema/library | Explicit failed global prerequisite before perimeter loading/checking | No import from mutable Builds HEAD and no accepted run with checks omitted |
| Unacceptable tag/API | Draft/missing/nonimmutable/wrong-author release, tag-object mismatch, nonancestor commit, unavailable/malformed API response | Failed global verdict | Fail closed; an authorization error means unverified, never absent |
| Source isolation | Local module checkout disagrees with live main; Builds HEAD differs from tag | Live module Git tree and exact tagged Builds bytes determine checks | No module checkout fallback; never initialize nested submodules |
| Output on failure | Normal check failure; stdout otherwise receives tool logs | Exactly one compact JSON object on stdout and `verdict=<same JSON>` in `GITHUB_OUTPUT` when set | Route logs to stderr; write output before nonzero exit |

</intent-contract>

## Code Map

Paths are relative to the superproject. Builds paths are read-only evidence; execute trusted exports of the selected tag, not their mutable worktree copies.

- `tools/render.py:188` (`Contract.validate`), `:213` (`pinned_contract`), `:326` (`registry`), `:390` (`desired_tree`), `:504` (`render`) provide strict serialized schema/loader validation, tagged export, registry/default handling and read-only render comparison. The export already includes schemas, `Github/lib`, callable manifests and the pinned linter installer/configuration. Reuse these APIs rather than duplicating their policies.
- `tools/render.py:61` (`diagnostic`) escapes unsafe log characters. Renderer Git reads scrub inherited Git context, disable replace refs/lazy fetch and prevent an uninitialized Builds path from resolving to the superproject. Preserve those boundaries.
- `tools/tests/test_render.py:30`, `:71` provide module loading and synthetic Git workspaces; `:752` checks callable inputs/secrets in both directions, CI output references and release permission union; `:834` supplies negative required-input cases. These tests currently qualify representative generated callers. Extract reusable interface checks into the global checker as needed, retaining the existing fixture assertions.
- `tools/tests/test_render.py:941` (`lint_fixtures`) demonstrates private temporary, integrity-verified installation and explicit-path online linting with complete JSON-result validation. `tools/actionlint.yaml`, `tools/zizmor.yml` hold the narrow current policies. Do not transfer Builds' frozen legacy exceptions or invoke its Builds-specific `run_linters` enumeration.
- Tagged `references/Hexalith.Builds/Tools/ci/lint_workflows.py:37` (`install_tool`) and `Tools/ci/tools.json` provide actionlint 1.7.12, zizmor 1.32.0 and integrity hashes. Tagged `Github/lib/ci_config.py:117` validates enabled exclusions/reserved job names; `Github/lib/perimeter_config.py:174` validates perimeter bytes. Use the sole existing readers, not a new schema implementation.
- `.gitmodules` declares 18 direct submodules at `references/<Repo>`; verify each selected module's declaration and mode-160000 Git entry, without reading its checkout. Clone canonical public `https://github.com/Hexalith/<Repo>.git` at live `main`, independently of the gitlink's pinned commit.
- `.github/workflows/` has no tracked workflow yet. `setup/README.md` documents render prerequisites and intentionally empty production registry; `rendered/` has only `.gitkeep`. An empty registry is legitimate.
- `ARCHITECTURE-SPINE.md:112`, `:186`, `:259`, `:290`, `:584` (path in context) define registry/check separation, verdict/triggers, acceptable tag/interfaces, locked scripts and workflow conventions. App-only checks belong to the later deliver job.
- Prior story continuity: all 16 earlier specs are `done`, with complete execution lists. 4-2's final 31-test renderer suite is the reuse baseline; it compares worktree bytes, leaving committed-render comparison to this global checker. 4-1's published release `443617691`, `v5.1.0`, peels to `9ebc31f606bc02f8a0ec2f1ec344127e2468c6b4`. Read-only verification on 2026-11-13 confirmed published/immutable, author `github-actions[bot]`, and ancestry of Builds main. Builds checkout HEAD is later documentation revision `7917c50e21ec5bae15677c9ac3559623e432756e`. Historical bootstrap blockers are closed; older-Git perimeter qualification and other adoption follow-ups remain with their existing stories.

## Tasks & Acceptance

**Execution:**

- [x] `tools/check_global.py`, `tools/check_global.py.lock` — add locked CLI `--project-root PATH`, defaulting from script location. Reuse the renderer's pinned contract; check the perimeter capability prerequisite, render with no writes/diff, generated CI/perimeter schemas and strict readers, actual generated caller interfaces/permissions/output references/consistent tag, and committed generated paths/bytes/modes against candidate `HEAD`. Run CiCd tool suites once without recursive orchestration, then integrity-pinned actionlint and online zizmor over explicit CiCd and rendered workflow paths. Verify release publication, immutability, bot author, exact remote/local peeled tag commit and ancestry of live Builds main through read-only API reads. Collect contextual failures; return nonzero for any failed/incomplete check. This is the complete global entry point for both validate and future nightly bump.
- [x] `tools/validate.py`, `tools/validate.py.lock` — add locked CLI with the same project-root convention. Invoke the global checker once and independently inspect all safely enumerated modules. Validate each candidate CI document through the selected strict reader, verify direct-submodule registration/gitlink, disjoint hook/job sets and enabled exclusion targets, then inspect the anonymous shallow clone's committed `.github/actions/<name>/action.yml` for every named enabled hook, job and exclusion target. Use bounded network/subprocess operations, no credentials/helpers/extraheaders for module clones, no checkout execution, hooks or recursive submodules. Emit the exact verdict protocol below before returning the aggregate exit status.
- [x] `tools/tests/test_validate.py`, `tools/tests/test_validate.py.lock`, `tools/tests/fixtures/validate/` — add CLI/Git/HTTP-boundary fixtures covering every matrix row, all tag-acceptance predicates including annotated-tag peeling and remote/local mismatch, old/incomplete pin, API/clone errors, missing/invalid configuration, and committed/uncommitted render drift. Prove checks remain independent in mixed global/module failure, output survives exit 1, a passing no-hook module is checked, and empty production registry is valid. Use real temporary Git remotes/index trees and test doubles only at external I/O boundaries; no production success-bypass flags. Tests of the global runner must stub child test execution to prevent self-recursion.
- [x] `tools/tests/test_render.py`, `tools/actionlint.yaml`, `tools/zizmor.yml` — reuse/extract interface and lint helpers where that removes duplication; preserve all existing renderer coverage and narrow lint policy. Global tests run without `--lint`; production lint runs once over the actual explicit paths. Keep representative fixture online lint as a separate qualification command, outside the shared global runner.
- [x] `.github/workflows/deliver.yml` — add the four triggers and concurrency below, top-level `permissions: {}`, `cache-mode: none`, and exactly one Ubuntu `validate` job with contents read. SHA-pin checkout v7.0.1 and setup-uv v10.3.3, with version comments. Checkout CiCd with persisted credentials off and no recursive submodules; separately checkout only Builds at main with tags available (`fetch-depth: 0`, no submodules, persisted credentials off). Its worktree is never the contract source. Disable setup-uv caching and pin uv 0.13.7. Invoke the locked validator; supply the job token through `env`, no expressions in `run:`. Map job output `verdict` from the validator step. Allow that step to attempt a conservative verdict after a Builds-checkout failure when CiCd/uv are available; keep actual check failures red.
- [x] `setup/README.md` — document both CLI commands, required checkout/tag/network/token availability, the JSON/exit contract, global-check reuse by nightly, and the satisfied v5.1.0 perimeter prerequisite. Preserve the empty production registry and intentional 10-2 partials.

**Acceptance Criteria:**

- Given a push to main, pull request, hourly minute-47 schedule or manual dispatch, when `deliver.yml` runs, then only its validate job runs with read permission and exposes one `verdict` JSON job output; main uses noncancelling group `deliver`, and other refs use cancelling group `deliver-validate-<ref>`.
- Given the same candidate checkout and read-only token, when the shared global command runs directly or through validate, then the same render/schema/interface/test/lint/tag checks decide its verdict, including actual rendered workflow paths rather than merely fixture workflows.
- Given two valid registered modules and one failed module, when the locked validator CLI completes, then its stdout and GitHub step output contain the same object with only the passing names, its exit status is nonzero, and diagnostics identify the failed module. Given a failed global check as well, when it completes, then those independently passing names remain and `global` is false.
- Given a module's local reference checkout contains an action absent on live main, when validation runs, then that module fails; given the inverse state, when it runs, then action existence passes. Module-owned commands are never executed, and no module checkout or nested submodule is initialized or changed by those reads.
- Given current `builds-version` v5.1.0, when perimeter validation runs, then it uses the released schema/reader bytes at `9ebc31f606bc02f8a0ec2f1ec344127e2468c6b4`; given an older pin without story 4-1, when validation runs, then the global prerequisite fails explicitly before perimeter checks and no newer HEAD bytes are substituted.
- Given valid fixture registries and the real empty production registry, when implementation qualification runs, then meaningful passing/failing module and global paths are exercised, all existing renderer tests remain green, and the real locked global/validate commands succeed without changing tracked inputs, rendered output, module state or live settings.

## Spec Change Log

- 2026-11-13: The user invoked build-auto again for implementation in this repository. This resumes the ready-for-development spec. The planning-only invocation mentioned in the original intent and result is historical; all implementation boundaries and acceptance criteria remain in force.

## Review Triage Log

### 2026-11-13 — Review pass

- verdicts: 20 findings — high 0, medium 15, low 0, false 5, maybe-false 0
- findings:
  - `[medium]` `[patch]` VG1: Valid custom-job action availability lacked a verdict regression. — The review mutation removed jobs from the union while all original 30 tests passed. Added present/missing Windows-action fixtures with independent Alpha and both global outcomes.
  - `[medium]` `[patch]` EC1: A tag named main could be cloned in place of a live main branch. — A real tag-only Git clone succeeded with detached HEAD. Require symbolic HEAD refs/heads/main and equality with fetched origin/main; real-Git regressions cover tag-only and mismatched refs.
  - `[medium]` `[patch]` EC2: Permission union could downgrade read to none. — The parent reproduced contents read followed by none returning none. Compute maxima using none < read < write; focused order regressions pass.
  - `[medium]` `[patch]` EC3: Callable validation accepted a boolean for a declared string input. — The parent reproduced boolean delivered-sha acceptance. Check declared literal string/boolean/number types while preserving expressions and untyped composite arguments.
  - `[medium]` `[patch]` EC4: Bracket-form output references bypassed declaration checks. — The parent reproduced needs['release'].outputs['not-declared'] acceptance. Normalize bracket access over actual string values and check both output declarations and producer dependencies.
  - `[false]` `[reject]` IA1: Broad prerequisite gating differs from perimeter-only conditional activation. — The existing ready-for-development contract explicitly requires an incomplete pin to fail globally with no contract fallback. The current v5.1.0 pin satisfies the user’s prerequisite; no precondition is silently skipped.
  - `[false]` `[reject]` IA2: Capability detection does not require exactly the first story 4-1 tag. — The supplied story and AD-10 permit later compatible accepted releases. Current builds-version still names the verified v5.1.0 release; tagged capability checks preserve the milestone without preventing future accepted bumps.
  - `[false]` `[reject]` IA3: Candidate-perimeter validation differs from live owned-state comparison. — The referenced story expressly defines candidate contract validation and live action availability; later delivery repairs drift. Live owned-state comparison would obstruct that intended repair path.
  - `[false]` `[reject]` IA4: Local qualification does not execute actual hosted triggers/concurrency/output propagation. — The workflow provides and passes online lint for the requested Actions surface; manual wiring inspection and real CLI step-output checks pass. No observed workflow defect was reported. Hosted execution requires a future authorized push and is recorded as unverified.
  - `[false]` `[reject]` IA5: Production is empty while nonempty behavior uses synthetic registries. — An empty production registry is intentional and valid. Real temporary Git repositories and CLI fixtures cover passing/failing nonempty modules; no production registration was requested.
  - `[medium]` `[patch]` BH1: Permission union could downgrade read to none. — Same verified defect as EC2; fixed with ranked maxima and order regressions.
  - `[medium]` `[patch]` BH2: A job without an explicit permissions mapping raised KeyError. — The parent reproduced failure for a valid no-token job inheriting top-level permissions: {}. Use the effective job mapping or top-level mapping; inheritance regressions cover empty and explicit mappings.
  - `[medium]` `[patch]` BH3: Callable validation omitted declared literal types. — Same demonstrated literal mismatch as EC3; fixed typed literals. Arbitrary dynamic expression inference is not added: the reported concrete literal mismatch is covered.
  - `[medium]` `[patch]` BH4: Bracket-form needs output access escaped validation. — Same reproduced defect as EC4; normalization handles single/double quoted bracket names, mixed access and whitespace, with unknown-output and missing-needs regressions.
  - `[medium]` `[patch]` BH5: Working-tree submodule metadata could certify an absent HEAD declaration. — The parent committed removal of a declaration, restored only the working-tree file and reproduced acceptance. Read metadata through git config --blob HEAD:.gitmodules, consistent with the HEAD gitlink; real-Git regression covers both directions.
  - `[medium]` `[patch]` BH6: A declared submodule without any URL passed. — The parent reproduced acceptance without url. Require a nonempty committed URL; preserve URL spelling flexibility and continue cloning the canonical public module URL anonymously.
  - `[medium]` `[patch]` BH7: Clone --branch=main could select a same-named tag. — Same real-Git defect as EC1; branch identity and fetched-ref agreement now gate module action checks, including no-hook modules.
  - `[medium]` `[patch]` BH8: The tool suite assumed production must remain empty forever. — The production renderer.registry(ROOT)==[] assertion would fail on the first legitimate onboarding. Removed that assertion and retained the synthetic empty-registry test; production is still unchanged.
  - `[medium]` `[patch]` BH9: The 30-minute job budget could expire before bounded module failures emitted a verdict. — The parent confirmed a 30-minute global child plus 18 conservative 3-minute clone deadlines can total 84 minutes. Increased the workflow limit to 120 minutes, retaining child limits and headroom for output; no overall-deadline public surface was added.
  - `[medium]` `[patch]` BH10: Committed rendered output could be certified with uncommitted render causes. — The parent reproduced a committed render whose removed setup cause was restored as an untracked file. Compare pin, direct registry and used template bytes/modes/path sets with HEAD, while allowing unrelated tools/planning/evidence changes; focused positive/negative regressions cover this.

The 15 patch findings group into 11 distinct entries (11 medium; four duplicate reports). The original implementation agent applied the fixes in one re-engagement. No findings were deferred and no intent/spec repair loop was required.

### 2026-11-13 — Review pass

- verdicts: 53 findings — high 0, medium 12, low 21, false 20, maybe-false 0
- findings:
  - `[medium]` `[patch]` BH1: The validate step used `always()`, so it kept running after cancellation. — GitHub re-evaluates step conditions on cancel, and `always()` keeps the step running; a superseded PR run could hold its concurrency group for up to 120 minutes. Changed to `!cancelled()`, which still runs after a failed Builds checkout.
  - `[low]` `[patch]` BH2: Multi-line child output became one escaped line. — `diagnostic()` escapes LF, so every captured stderr blob (global child, unittest, linters) was logged as one line. `log()` now escapes each line separately, and other control characters stay escaped. Real runs now emit one stderr line per message. A mutation test pins it.
  - `[low]` `[reject]` BH3: A timeout drops partial output and can orphan grandchildren. — Real, but only when a bounded check hangs. The verdict still fails closed, and hosted runners reap orphans at job end. The complete fix needs process-group management, which adds new branches.
  - `[low]` `[patch]` BH4: `test_render.py` kept a divergent permission-union copy. — Its loop let a later `none` overwrite `read` (the defect fixed only in the global checker). The renderer suite now asserts against `check_global.permission_union`. Its assertion-style argument fixtures stay, as the Code Map requires.
  - `[false]` `[reject]` BH5: Global checks read tools and workflows from the working tree but certify HEAD. — Verdicts are consumed only from a fresh Actions checkout (and from the future nightly's committed candidate), where the tree equals HEAD. A local dirty run advances no ref. Testing working-tree tools locally is the intended developer loop.
  - `[medium]` `[patch]` BH6: An unpaginated compare response can exceed the 2 MiB bound. — Measured real bodies: about 1.5 MB from v4.48.0 and about 2.1 MB from v4.0.0 to live main. A rollback or hold pin would therefore fail closed permanently. Ancestry is now read from `compare/...?per_page=1&page=2`, which omits file lists and keeps status and merge base: about 13 KB measured for a 1580-commit gap and for identical refs. The real run passes.
  - `[medium]` `[patch]` BH7: The API double ignored request paths and only modelled the identical case. — A reversed or self-comparison would have passed silently. The double now answers only the exact endpoints and argument order, and live main defaults to a distinct `ahead` commit. Identical refs are covered separately. The reversed-compare and no-ahead mutations are now caught.
  - `[low]` `[patch]` BH8: `http.client.HTTPException` (e.g. `IncompleteRead`) escaped `check()`. — Such an exception would abort `run()` with a traceback and skip the lint and tool-suite checks. Added to `FAILURES`. A regression test proves the later checks still run.
  - `[low]` `[patch]` BH9: Module clones downloaded every blob at the tip. — A real anonymous Tenants clone took 52 MB and 5.5 s. With `--filter=blob:none` it took 0.2 MB and 0.6 s, and the branch, origin/main and ls-tree reads still succeeded. The flag is added and asserted.
  - `[low]` `[reject]` BH10: The story's Verification wording and `deferred` list omit hosted qualification. — Fixing this would mean editing this build's spec. Hosted execution stays recorded as a residual risk.
  - `[medium]` `[patch]` BH11: Several fail-closed guards lacked regression tests. — Added CI and perimeter `buildsTag` mismatch tests for `check_documents`, the CLI internal-failure fallback verdict, and the unwritable `GITHUB_OUTPUT` exit 1. The module `buildsTag`, zizmor guards and `NoRedirect` are covered by VG3–VG5. Mutations are caught.
  - `[low]` `[reject]` BH12: Reproducibility renders twice in one process. — Hash-seed-dependent nondeterminism is still caught as a mismatch against the committed render, which a separate process produced. A subprocess re-render with a different seed would add a new execution path for a rare case.
  - `[false]` `[reject]` BH13: Runner image and Python version are unpinned. — Templates use the same `ubuntu-latest` convention. uv selects an interpreter that satisfies the locked `>=3.12`, and the suites qualify both 3.12 and 3.14. No concrete failure was shown.
  - `[low]` `[patch]` BH14: The README omitted the `check_global.py` stdout and exit contract. — The future nightly relies on it. Documented: no stdout, stderr logs, exit 0 only when every check passes. A real run confirmed 0 stdout bytes.
  - `[low]` `[patch]` BH15: Output references to plain-job outputs were falsely rejected. — Only `uses:` jobs registered outputs. Plain jobs now register their declared `outputs` mapping. A declared/undeclared regression covers both directions.
  - `[medium]` `[patch]` EC1: The `always()` step survives cancellation. — Same defect as BH1; fixed with `!cancelled()`.
  - `[false]` `[reject]` EC2: The job output is empty when the validate step is skipped. — Design Notes define missing output after a startup or runner failure as fail-closed, with no fabricated verdict. The job is red, and no consumer exists in this story.
  - `[false]` `[reject]` EC3: A newer queued main run cancels a pending one despite `cancel-in-progress: false`. — ARCHITECTURE-SPINE lines 196 and 597 mandate the `deliver` group and allow a pending run to be superseded. The nightly design treats a cancelled run as "not a result", and the newer run validates a descendant.
  - `[low]` `[patch]` EC4: `FAILURES` was too narrow for HTTP exceptions. — Same defect as BH8; fixed.
  - `[medium]` `[patch]` EC5: The compare response can exceed 2 MiB when main is far ahead. — Same defect as BH6; fixed with paginated metadata.
  - `[low]` `[reject]` EC6: Mixed-case `needs` expressions bypass the reference check. — Templates emit only lowercase `needs.` literals, and setup data cannot inject expressions. Case-folding every producer, needs and output comparison changes matching semantics for an unreachable input.
  - `[low]` `[patch]` EC7: Plain-job outputs were unregistered. — Same defect as BH15; fixed.
  - `[low]` `[reject]` EC8: Builds `uses:` with different casing or root form skips the interface checks. — Templates use the exact `Hexalith/Hexalith.Builds/` prefix, and a job-level mismatch already fails. Handling step casing variants needs a new rejection branch for template mistakes that don't occur.
  - `[low]` `[reject]` EC9: String, absent or `none` permission forms are not normalized. — Tagged v5.1.0 manifests use explicit scope mappings, and templates always set top-level `permissions: {}`. Unexpected forms fail loudly. Normalization adds policy branches for unobserved inputs.
  - `[low]` `[reject]` EC10: The module CI document is read from the working tree while `.gitmodules` comes from HEAD. — The two differ only locally. There, the committed-render global check fails any rendered drift, so `global` is false and nothing can advance. A HEAD-based registry and document read is more than a direct correction.
  - `[low]` `[patch]` EC11: Clones download blobs that are never needed. — Same defect as BH9; fixed.
  - `[low]` `[reject]` EC12: A global-child timeout leaves orphaned processes. — Same claim and rationale as BH3.
  - `[false]` `[reject]` EC13: A stdout write failure prevents the `GITHUB_OUTPUT` record. — The runner's stdout pipe is never shown to close. The path fails loudly (`verdict output` diagnostic, exit 1), which the fail-closed protocol accepts.
  - `[low]` `[patch]` EC14: The lint test failed on non-Linux or non-x86_64 hosts. — The platform guard ran before the mocks. The test now patches the platform detection.
  - `[false]` `[reject]` EC15: The `-I` CLI harness writes `tools/__pycache__` bytecode. — `**/__pycache__/` and `*.pyc` are gitignored, and no committed-input, render or status check observes them. `git status` stays clean.
  - `[medium]` `[patch]` VG1: Runner wiring for the render, committed-render and interface checks was unpinned. — Pre-verified. Added a `run()`-level test where each check fails alone and the other three report passed. Deleting any of the three lines is now caught.
  - `[medium]` `[patch]` VG2: The validate → check_global process boundary was never exercised. — Pre-verified. Added subprocess runs of `check_global.main()` (exit 0 and 1, empty stdout). The child command is asserted to be the locked `check_global.py` with `--project-root` and `cwd` set to a non-default project. The `main-always-0` and dropped `--project-root` mutations are now caught.
  - `[low]` `[patch]` VG3: The module-level `buildsTag` check was untested. — Pre-verified. Only informational module listing under an already-false `global` was affected. Added a `stale-builds-tag` case; the mutation is caught.
  - `[medium]` `[patch]` VG4: The online-zizmor guards were untested. — Pre-verified. Added offline, no-online and no-token subtests asserting a ValueError and no installer or zizmor call. Both guard mutations are caught.
  - `[medium]` `[patch]` VG5: `NoRedirect` was mocked away. — Pre-verified. The test now asserts the opener receives a `NoRedirect` handler and that a redirect raises "redirected ... unverified". Dropping the handler is caught.
  - `[false]` `[reject]` IA1: Implementation happened despite "this invocation halts after planning". — The Spec Change Log records the user's later implementation invocation, and the halt clause described the planning run.
  - `[false]` `[reject]` IA2: Broad prerequisite gating (reading B2) instead of perimeter-only. — carried: the same reading was rejected as IA1 in the earlier pass, and `selected_contract`/`validate` still read as described.
  - `[false]` `[reject]` IA3: Capability detection instead of identity with the first 4-1 tag. — carried: the same claim was rejected as IA2 in the earlier pass, and the code is unchanged.
  - `[false]` `[reject]` IA4: Hook/job conflicts and disabled exclusions also fail `global`. — Matrix row "Invalid module document" says schema or semantic failure also fails `global`. Such input fails the strict reader inside render and `check_documents`, so `false` is the independently computed global result.
  - `[false]` `[reject]` IA5: Module checks read only `hexalith-ci.json`, so a broken perimeter or workflow lets the module pass. — The spec task defines the module check over the CI document. `check_documents` fails `global` for every broken perimeter or workflow, so no advancement could occur.
  - `[low]` `[reject]` IA6: Candidate sources mix working tree and HEAD. — Same claim and rationale as EC10.
  - `[false]` `[reject]` IA7: The committed-cause check excludes renderer and tool code. — Same claim and refutation as BH5.
  - `[false]` `[reject]` IA8: Online zizmor is enforced by preconditions, not observed. — The pinned zizmor 1.32.0 `--help` shows it reads `GH_TOKEN`, `GITHUB_TOKEN` or `ZIZMOR_GITHUB_TOKEN`. The gate rejects every offline selector, and real runs logged completed online audits.
  - `[false]` `[reject]` IA9: An import or startup failure emits no verdict. — Design Notes define missing output after a startup or runner failure as fail-closed, and the job stays red.
  - `[medium]` `[patch]` IA10: The step condition uses `always()`, which survives cancellation. — Same defect as BH1; fixed. Hosted execution itself remains unverified, as the carried earlier IA4 rejection records.
  - `[medium]` `[patch]` IA11: Tests never prove the child is `check_global.py`. — Same gap as VG2; fixed.
  - `[false]` `[reject]` IA12: Global and module verdicts are never composed in one test, and D-type cases are single-module. — Per-module isolation is the same `contract.validate` exception path that the multi-module missing-configuration and clone-failure tests exercise. Global is merged as a boolean for both values, and VG2 now covers the real child.
  - `[false]` `[reject]` IA13: The verdict-level prerequisite failure is tested only with a missing tag. — Both failures raise `CheckError` inside `selected_contract` before yield and reach the same `validate`/`run` handler. The incomplete case is tested at that raise.
  - `[false]` `[reject]` IA14: Production anonymous HTTPS clones were never exercised. — Real `clone_module` runs against Commons, EventStore, FrontComposer and Tenants passed the branch, origin/main and ls-tree reads, both with and without `--filter=blob:none`.
  - `[false]` `[reject]` IA15: API, linters and test suites are replaced by doubles. — The spec requires doubles only at external I/O boundaries. The real locked `check_global.py` passed release/API, online lint and both suites (79 tests).
  - `[false]` `[reject]` IA16: The empty production registry is tested synthetically. — carried: the same claim was rejected as IA5 in the earlier pass. The real validator again emitted `{"global":true,"modules":[]}`.
  - `[false]` `[reject]` IA17: Stdout purity is tested only with mocked globals. — A real locked validator run wrote exactly the JSON plus LF to stdout. Its real child logs all went to stderr.
  - `[low]` `[patch]` IA18: Task 4 is ticked but `test_render.py` was unchanged. — Same root cause as BH4: the renderer suite now delegates the union rule to the shared checker.

The 24 patch findings group into 16 distinct patched entries: 8 medium and 8 low, with eight duplicate reports folded in. Nothing was deferred, and no intent-gap or spec-repair loop was required. The original implementation agent was not available to this follow-up session, so the review orchestrator applied the patches.


## Design Notes

The single verdict is `{"global":true,"modules":["Hexalith.Example"]}`: exactly a boolean and a sorted array of repository stems from this run's registry. Stdout is machine-readable; check/test/linter progress goes to stderr. When `GITHUB_OUTPUT` exists, append one `verdict=` record containing the identical compact JSON before exiting. Exit 0 requires the global verdict and every registered module to pass; otherwise exit 1. Missing output after a startup/runner failure remains fail-closed for the future deliver consumer; do not fabricate success or add `continue-on-error` to hide a failed job.

Preserve independence: run the global subprocess without letting its exit stop the orchestrator; validate modules individually from candidate CI JSON, never by reusing one failing all-modules render as their sole result. A missing selected contract cannot certify a module; a mere lint/test/tag-acceptance failure does not erase module checks that can still be evaluated with the selected contract. An unreadable registry produces no trusted names. Perimeter validation concerns the rendered contract, not the module's current owned state.

The committed-render check compares `rendered/` to candidate `HEAD` as well as to a fresh read-only render, including additions/deletions and executable/symlink modes. It must not require a globally clean tree: the Builds checkout can differ from its superproject gitlink and planning/evidence files may be present. The future nightly bump prepares its local candidate commit, with render committed alongside the pin, before invoking this identical command; nothing is pushed unless it passes. No nightly code is added here.

The workflow triggers are `push: branches: [main]`, `pull_request`, `schedule: cron: '47 * * * *'`, and `workflow_dispatch`. Concurrency uses `github.ref == 'refs/heads/main'` to select `deliver`/false versus `deliver-validate-<ref>`/true. PR merge refs stay in validation concurrency even when targeting main. No path filter suppresses a required run. Action pins can be taken from the released Builds workflow and verified upstream during implementation; do not invent SHAs.

## Verification

- `uv lock --script tools/check_global.py`, `uv lock --script tools/validate.py`, `uv lock --script tools/tests/test_validate.py` — create committed adjacent locks; dependency declarations reuse the renderer's exact pins where imported.
- `uv run --locked --script --python 3.12 tools/tests/test_validate.py` and the same command with `--python 3.14` — fixture/CLI/Git/API-boundary matrix passes sequentially on the Python floor and current available interpreter.
- `uv run --locked --script --python 3.12 tools/tests/test_render.py` — existing renderer suite passes after any shared-helper extraction.
- `uv run --locked --script --python 3.14 tools/tests/test_render.py --lint` — representative nonempty callers pass pinned online audits separately from production global checks.
- `uv run --locked --script tools/check_global.py` and `uv run --locked --script tools/validate.py` — with a read-only token supplied privately through the environment, current empty-registry candidate passes real release/API checks and actual workflow lints; validator emits `{"global":true,"modules":[]}`. Validate invokes the global command itself; the direct invocation separately qualifies reuse.
- `git diff --check` and `git status --short` — only the planned root implementation files and this canonical story change; no pin, gitlink, production registration or Builds changes.
- Inspect `deliver.yml` with pinned actionlint/online zizmor and manually verify trigger/concurrency/permission/output wiring against the first acceptance criterion; qualify the actual hosted job/output handoff at the next authorized push, without adding workflow-text tests or dispatching from this planning invocation.

## Auto Run Result

Status: done

### Follow-up review result — 2026-11-13

Story 4-3 remains implemented: `deliver.yml` has only the read-only `validate` job. It runs the shared
`tools/check_global.py` entry point once and checks every registered module independently against an
anonymous clone of its live `main`. It emits one compact JSON verdict, including on ordinary failures. This
follow-up pass ran the four review layers again on the complete change since
`76096c764335ade1e93e949e1aa18151770ff36d` and repaired the verified defects without changing the intent
contract or scope.

Files changed by this pass (repository-relative):

- `.github/workflows/deliver.yml`: the validate step condition is `!cancelled()`, not `always()`, so a superseded or cancelled run stops. The step still runs after a failed Builds checkout.
- `tools/check_global.py`: logs one escaped line per message; adds `http.client.HTTPException` to the collected failures; registers declared outputs of plain (non-`uses`) jobs; reads ancestry from paginated compare metadata (`?per_page=1&page=2`), which omits the file lists, so a large pin-to-main gap stays within the 2 MiB bound.
- `tools/validate.py`: module clones add `--filter=blob:none` (trees only; no blob download).
- `tools/tests/test_validate.py`: 48 tests (was 40). New coverage:
  - `run()`-level wiring for each render or interface check failing alone;
  - the real `check_global.main()` exit status and stdout, and the locked child command, `--project-root` and `cwd`;
  - the CI and perimeter tag checks in `check_documents`, and the module `buildsTag` check;
  - the online-zizmor guards and the `NoRedirect` handler;
  - the CLI fallback verdict and an unwritable `GITHUB_OUTPUT`;
  - per-line log escaping, collection of `IncompleteRead`, and plain-job outputs.

  The API double now answers only exact endpoints and argument order, and live main defaults to an `ahead` commit. The lint test patches platform detection.
- `tools/tests/test_render.py`: the caller permission assertion delegates to the shared `check_global.permission_union`, which removes the copy that had drifted.
- `setup/README.md`: documents the `check_global.py` contract: no stdout, stderr logs, exit 0 only when every check passes, otherwise 1.
- This canonical story: status, follow-up triage log and this result. An orchestrator had already removed the earlier `## Auto Run Result` text before dispatch. That removal is kept, and this section replaces it.

Review findings breakdown (53 findings; high 0, medium 12, low 21, false 20, maybe-false 0):

- 24 patch findings grouped into 16 patched entries: 8 medium (cancellation condition, compare size bound, exact-path API double, fail-closed regression tests, runner wiring, process boundary, zizmor guards, redirect handler) and 8 low (per-line logs, shared permission union, HTTP exception collection, blob-less clones, README contract, plain-job outputs, platform-independent lint test, module `buildsTag` test). No high finding.
- Deferred: none. No intent-gap or spec-repair loop.
- Rejected, with reasons recorded per row in the triage log:
  - low, because the input is rare or unreachable and the fix would add branches: BH3/EC12 timeout orphans, BH12 in-process reproducibility, EC6 mixed-case `needs`, EC8 `uses:` casing, EC9 permission forms, EC10/IA6 working-tree module document;
  - low, because the fix would edit this spec: BH10;
  - false: BH5/IA7, BH13, EC2, EC3, EC13, EC15, IA1, IA4, IA5, IA8, IA9, IA12–IA15 and IA17;
  - carried false from the earlier pass: IA2, IA3, IA16.
- The step-03 implementation agent from the earlier session could not be re-engaged, so the review orchestrator applied the patches directly.

Follow-up review recommendation: `false`. This is a follow-up pass and no `high` entry was patched. Patched counts by entry verdict: high 0, medium 8, low 8.

Verification performed after the patches:

- `uv lock --script` for `tools/check_global.py`, `tools/validate.py` and `tools/tests/test_validate.py`: all resolved, with no lock changes.
- `uv run --locked --script --python 3.12 tools/tests/test_validate.py`: 48 tests OK. The same with `--python 3.14`: 48 tests OK.
- `uv run --locked --script --python 3.12 tools/tests/test_render.py`: 31 tests OK.
- `uv run --locked --script --python 3.14 tools/tests/test_render.py --lint`: 31 tests OK, and 8 representative workflows passed pinned actionlint 1.7.12 and online zizmor 1.32.0.
- Mutation qualification in a scratch copy: all 16 targeted regressions were caught. They were removing each of the three render or interface checks, `main()` always returning 0, dropping `--project-root`, removing the module `buildsTag` check, removing either zizmor guard, dropping `NoRedirect`, reversing the compare, dropping `ahead`, dropping the blob filter, narrowing `FAILURES`, ignoring plain-job outputs, single-line logging, and removing the output-failure fallback.
- Real locked `tools/check_global.py`, with a read-only token from the CiCd-agent gh profile supplied privately through the environment: exit 0 and 0 stdout bytes. All seven global checks passed, including the real release, tag and paginated-compare ancestry, online lint of the actual `deliver.yml`, and both suites (79 tests). Stderr is now one line per message.
- Real locked `tools/validate.py`: exit 0, stdout exactly `{"global":true,"modules":[]}` plus LF, and the identical single `verdict=` record in a temporary `GITHUB_OUTPUT`.
- Real anonymous `clone_module` runs against the public Commons, EventStore, FrontComposer and Tenants `main` branches passed the branch identity, origin/main and ls-tree reads. `--filter=blob:none` cut the Tenants clone from 52 MB in 5.5 s to 0.2 MB in 0.6 s.
- Real compare measurements: about 2.1 MB unpaginated from v4.0.0 versus about 13 KB paginated. Identical refs also work with the paginated request.
- `git diff --check` passed for the code changes. No Builds, pin, gitlink, template, lock or production registration changed. Nothing was dispatched, published or pushed.

Residual risks:

- Hosted Actions behavior is still unexercised: `!cancelled()` semantics, step and job output propagation after a Builds checkout failure, and the 120-minute budget. These are inspected and linted only, and qualify at the next authorized push.
- Ancestry relies on GitHub's documented rule that compare file lists appear only on the first page.
- A hung bounded check still loses its partial output and can orphan grandchild processes until the job ends (rejected low, BH3/EC12).
- Diagnostics from multi-line child output are now line-split. Each line is still control-character escaped, but a line from candidate-owned tools that starts with `::` is no longer folded into a single escaped line. Candidate code already runs in the same job and inherits `GITHUB_OUTPUT`, so this adds no new trust boundary.
