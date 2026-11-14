---
title: 'Restore job'
type: feature
created: '2026-11-14'
status: done
story_id: '5-3'
review_loop_iteration: 0
followup_review_recommended: false
baseline_revision: 06a3998be613e31affac5b69a755840e6a4bbcf3
implementation_repository: references/Hexalith.Builds
implementation_baseline_revision: 2f4f1cf9ae4889f8d96b4af3ceb01442163d1215
planning_repository_revision: 2f4f1cf9ae4889f8d96b4af3ceb01442163d1215
context:
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md'
  - '{project-root}/_bmad-output/specs/spec-cicd/enforcement.md'
warnings: [oversized]
deferred:
  - summary: >-
      Pre-existing caller permission-union validation does not support GitHub read-all/write-all shorthand.
    evidence: |-
      Parent probes of the baseline global checker at 06a3998be613e31affac5b69a755840e6a4bbcf3 and the current shared calculation both raise AttributeError for each shorthand. All current selected and restore-enabled workflows use explicit mappings. Future shorthand support must preserve exact least-permission validation.
    location: >-
      tools/render.py:390; inherited from tools/check_global.py
    severity: medium
  - summary: >-
      Qualification of very large module repositories remains unverified; an unfiltered shallow module fetch might exceed runner resources.
    evidence: |-
      No eligible managed-module capacity failure was demonstrated. Resolve with a large committed-main fixture, actual runner disk/network limits and a qualifying drift event; ordinary CI already performs a broader checkout before authorizing restore. The writer remains bounded by its ten-minute job timeout.
    location: >-
      references/Hexalith.Builds/Github/lib/restore.py:141
    severity: medium (unverified)
---

# Story 5-3 — Restore job

<intent-contract>

## Intent

**Problem:** The guard reports committed CI/CD ownership drift, but no isolated writer repairs it on a push to `main`. Leaving those edits in place defeats CAP-8 until delivery runs.

**Approach:** Add the AD-8 restore job to Builds' reusable CI. It independently obtains current module `main` and the latest accepted `delivered/<Repo>` state, applies the permitted perimeter entries in one `build(cicd)` commit, pushes once and explicitly dispatches `ci.yml` on `main`.

## Boundaries & Constraints

**Always:** Follow CAP-8 and AD-4/7/8/9/11/19/20. The only CI-job datum the writer accepts is its exact `drift == 'true'` flag. Recompute all source content, tag selection, eligibility and differences in the restore job. Run only trusted Builds code from the reusable workflow's commit, using native `$/Github/restore`, scripts located through `GITHUB_ACTION_PATH`, and `python3 -I`. Keep `ci` and all module build/test/hook jobs read-only; only restore gets `contents: write` and `actions: write`. Use the existing strict perimeter loader and index application engine. Preserve product content and parseable foreign partial-entry data; an unparseable partial-entry file is rewritten holding only the owned part, per AD-4. Read committed trees, never a module worktree or the failed CI job's artifacts, checkout, paths, config or repair plan.

**Never:** Restore on PR, dispatch, non-main push, missing/false drift, cancellation, Builds itself, or any nonempty `module-root`. Never modify `.github/workflows/**`, including unrendered files, modes, ancestor replacements and indirect glob deletions. Never execute module code, hooks, filters, submodules, configuration plugins, npm or downloaded validation/build tools in the write job. Never revert an agent commit, persist a token, use a PAT/App key, force-push, rebase or retry a rejected push. Delivery, actual module adoption, release changes, local `check.py`, schema redesign and frozen legacy runtime are outside scope.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
| --- | --- | --- | --- |
| Ordinary repair | Authorized main push; current accepted and module trees differ in writable entries | One commit parented by fetched live main; only eligible owned changes; push then dispatch `ci.yml` with `ref: main` | No error |
| Mixed product and ownership edit | Product edits plus malformed/missing whole or partial owned content | Preserve product and foreign keys/text; repair whole blobs without parsing module config; partial repair follows existing engine semantics | Unsafe structural conflicts fail before publication |
| Workflow drift | Missing/extra/changed workflow blobs or modes | Workflows stay byte/mode identical to fetched module main; other eligible entries may be repaired; CI config stays untouched | Remaining drift waits for delivery |
| Different Builds tag | Perimeter tag differs from reusable workflow's own tag, including a rollback | Skip Builds gitlink, its `.gitmodules` section and CI config; repair independent entries | Never infer running tag from module config/gitlink |
| Matching Builds tag | Perimeter tag equals the exact running tag | Gitlink/section are eligible; CI config additionally requires the entire committed workflow directory to match the accepted render | Workflow identity/tag-object mismatch fails closed |
| No eligible changes | Already repaired main, or only excluded drift | No empty commit or push; already-clean main may be dispatched to recover an earlier dispatch failure; excluded-only drift causes no futile dispatch | Report skipped/unchanged paths clearly |
| Sources unavailable | Missing delivered ref/perimeter/tag, invalid accepted data, oversized JSON, fetch/transport/authentication failure | No commit, push or dispatch | Fail visibly; never treat unavailable state as absence or use CiCd main as fallback |
| Concurrent module push | Live main moves after the restore snapshot | Normal push is rejected; newer main remains intact | Stop immediately, fail visibly, no retry/rebase/force or dispatch |
| Dispatch failure | Repair push succeeded but Actions dispatch is refused or unavailable | Keep the successful repair; fail with the dispatch error | Rerunning can dispatch already-clean current main without another commit |
| Forbidden invocation | PR/dispatch/non-main/no drift/sample/Builds root | Workflow job is skipped; direct script invocation also rejects ineligible context before network/write | Lint-only failures never authorize repair |

</intent-contract>

## Code Map

All unprefixed runtime paths below are relative to `references/Hexalith.Builds`.

- `.github/workflows/ci.yml:35` — one existing `ci` job, `contents: read`; internal output `drift` at line 51 comes from `steps.guard.outputs.drift`. No public workflow output or restore job exists. Guard already uses `$/Github/guard` before prepare. Preserve stage order, outputs, root/sample hooks and Windows handoff.
- `Github/lib/guard.py:29` — `run` freezes the committed revision and initializes drift false; only actual perimeter differences set true. Missing accepted state and action/audit/commitlint failures remain false. Preserve this authorization distinction.
- `Github/lib/expected_state.py:53` — hardened read-only `Git`; environment whitelist, no credential helpers/config overrides, hooks, recursion or executable transport. It intentionally rejects `run(environment=...)`; it cannot serve as the index writer.
- `Github/lib/expected_state.py:86` — `AnonymousTransport.clone/deepen/builds` uses fixed CiCd/Builds HTTPS remotes, shallow sparse no-checkout delivered clones and exact tag objects. Production offers no remote/path override; tests inject Python transport objects.
- `Github/lib/expected_state.py:191` — `compare_repository` loads `rendered/<Repo>.perimeter.json` and `rendered/<Repo>/…`, peels gitlink tags, and returns a materialized `Comparison` after its temporary expected clones are deleted. Factor acquisition into a shared context manager that keeps snapshots/tag handles alive for restore; preserve existing guard/release API, pinning, diagnostics and cleanup.
- `Github/lib/perimeter_config.py` — sole perimeter validator; use its schema and path/entry validation. `Github/lib/perimeter.py:696` `compare` and `:721` `apply` accept zero-based entry indices through `selected`. The engine owns all nine entry semantics, minimal partial edits, atomic index changes and attribute normalization; it does not own orchestration policy.
- `Github/lib/perimeter.py:61` — `Git(index_file=...)`; `apply` passes a candidate environment and later constructs another `Git` for validation. Audit every internal Git call when preserving the restore writer's sanitized environment. `hash-object --path` applies committed attributes: use a fresh private bare repository with no module-supplied filter definitions, not the module checkout/config.
- `Github/lib/perimeter.py:665` — repair preflight may add ancestor/descendant removals. The canonical absent pattern `**/bmad-testarch-ci/**` can intersect workflow paths. Omitting the workflow `whole-dir` entry alone does not guarantee workflow preservation.
- `Github/lib/release_state.py:125` — stdlib HTTP/error and token-redaction precedent; its existing read client does not implement the restore dispatch POST. Keep a bounded, fixed-endpoint dispatch adapter in the restore runtime rather than widening release behavior unnecessarily.
- `Github/lib/tests/test_expected_state.py`, `test_perimeter.py`, `test_guard.py`, `test_guard_adapter.py` — real-Git fixtures, injectable anonymous transports, selected-index and guard drift controls. `test_ci_environment.py:83` `CompositeHarness` and `tests/actions_expressions.py` execute action/job conditions and mappings; extend behavior rather than asserting workflow text.
- `.github/workflows/builds-ci.yml:24` — both reusable callers (`dotnet`, `sample`) currently grant only `contents: read`. Grant the called workflow's permission union, while the callee's CI job and standalone Windows job remain read-only and both Builds restore paths stay disabled.
- CiCd `templates/.github/workflows/ci.yml.j2:13` — module reusable caller also grants only `contents: read`; update its permission union with the runtime change. Windows jobs remain read-only. No managed modules or accepted refs currently exist; fixtures must supply delivered branches during behavioral qualification.
- `Tools/ci/run_python_tests.py:21` discovers new `Github/lib/tests/test_*.py` automatically; `Tools/ci/README.md` documents pinned lint/API/dual-interpreter commands. `docs/cicd-5-3-restore-job-plan.md` records this planning delivery in Builds.

Implemented surfaces:

- `Github/lib/restore.py:41` validates trusted invocation/source identity; `:82` supplies the private writer; `:155` implements bounded fixed-endpoint dispatch; `:201` selects eligible ownership; `:254` orchestrates fresh acquisition, candidate checks, one push and recovery.
- `Github/lib/expected_state.py:219` retains accepted snapshots inside `acquire_expected`; `compare_repository` keeps its existing external contract. `Github/lib/perimeter.py` retains the caller's hardened Git adapter when reading a candidate index.
- `Github/restore/action.yml` and `.github/workflows/ci.yml` expose the isolated writer without a checkout or module execution. Caller permission changes live in `.github/workflows/builds-ci.yml`.
- CiCd `tools/render.py:390` computes the selected tagged workflow's effective permission union; `tools/check_global.py:176` uses the same calculation for exact caller checks. The template consumes that union. Real old/new tag fixtures live in `tools/tests/test_render.py` and `tools/tests/test_validate.py`.

## Tasks & Acceptance

**Execution:**

- [x] `Github/lib/expected_state.py` and `Github/lib/tests/test_expected_state.py` — expose context-managed accepted-state acquisition shared by comparison and restore; retain live accepted/tag snapshots only within that context. Preserve anonymous fixed remotes, strict schema handling, pinned delivered commit, existing requested-ancestor release semantics, Builds/sample behavior, sanitized errors and deterministic cleanup on all failures.
- [x] `Github/lib/restore.py` — add stdlib restore orchestration and a small sanitized writable Git adapter using a fresh private bare `--template=` repository, private index and no checkout. Independently validate trusted event/ref/repository/fixture controls, fetch current module main anonymously, freeze its full commit, and acquire the current delivered branch anew. Initialize the index from that main tree. Do not consume expected SHA, module paths, JSON, tag or repair data from CI outputs. Validate required regular expected blobs before writes. Bound in-memory JSON/blob acquisition before loading (4 MiB per JSON document/HTTP response); fail oversized input without extracting it.
- [x] `Github/lib/restore.py` and, only where needed for environment propagation, `Github/lib/perimeter.py` — select entries under AD-8: skip workflow ownership; permit Builds gitlink/section only when the perimeter tag equals the exact reusable workflow tag; additionally require a clean workflow-directory comparison before selecting CI config. Obtain source identity from step-level `job.workflow_ref`, `job.workflow_sha` and `job.workflow_repository`; validate Builds CI identity, normalize exact stable tag spelling and verify its peeled object against the running SHA. Valid branch/SHA refs authorize no lockstep/config repair. Preserve protected files even through broad absence patterns and file/directory conflicts: omit an entry with a protected footprint where possible, otherwise fail preflight. Before committing, compare candidate to parent and enforce unchanged workflows, skipped gitlink/config and the owned `.gitmodules` section; independently recompare selected ownership. No generic ownership engine default changes.
- [x] `Github/lib/restore.py` — write a tree and one `build(cicd): restore owned CI/CD files` commit with fetched main as its sole parent and fixed bot identity. Use `commit-tree` so no module hook/signing configuration executes. Push once to the fixed trusted module HTTPS URL, ordinary fast-forward only. Add the token solely to the authenticated push subprocess as a header scoped to `https://github.com/`, never argv, URLs, config files or anonymous clone/fetch environments. Disable helpers, prompts, hooks, LFS smudge and submodule recursion; sanitize inherited Git/Python/credential configuration for every subprocess, including engine-created candidate readers. Dispatch only fixed `repos/<repository>/actions/workflows/ci.yml/dispatches` with `ref: main`, using bounded stdlib HTTP, no credential-bearing redirects and redacted failures. No empty commits; a fully clean recomputation supports dispatch-only recovery, while excluded-only drift does nothing. Preserve a successfully pushed repair if dispatch fails.
- [x] `Github/restore/action.yml` and `.github/workflows/ci.yml` — add trusted composite invocation and `restore` job with `needs: ci`, explicit failure-aware/noncancelled condition, push/main/true-drift/empty-module-root/non-Builds checks, timeout and only Contents/Actions write. No checkout/build/npm/module action in this job. Pass native workflow identity at step scope, event/repository/ref and token through environment, not interpolated shell code. The only value sourced from `needs.ci` is drift. Repeat eligibility checks inside the script. Keep failure of original guard visible after successful restoration; PR/dispatch never repair.
- [x] `.github/workflows/builds-ci.yml` and CiCd `templates/.github/workflows/ci.yml.j2`, `tools/render.py`, `tools/check_global.py`, `tools/tests/test_render.py`, `tools/tests/test_validate.py` — grant the restore-enabled workflow’s `contents: write` and `actions: write` union on Builds reusable caller jobs; derive module caller permissions from the selected trusted tagged workflow using one shared union calculation, and test old/new tags plus insufficient/excess permission rejection. Keep inner `ci`, module custom actions and standalone Windows jobs at `contents: read`. Treat this as an AD-10 caller-permission API change. Render in CiCd and commit any resulting render with its template cause; with the current empty registry no module render/adoption is expected. Keep frozen module-consumed workflows untouched.
- [x] `Github/lib/tests/test_restore.py`, `test_restore_adapter.py`, `test_expected_state.py`, `test_perimeter.py`, `test_guard_adapter.py`, `test_ci_environment.py` and `tests/actions_expressions.py` — exercise the matrix with real temporary Git module/Builds/CiCd remotes and delivered branches through Python injection, plus fixed-endpoint HTTP doubles. Cover both tag-transition directions, tag/source spoofing, failed-CI outputs, malformed whole/partial files, preserved foreign content, extra/missing/mode-changing workflows, indirect protected-path matches, private-index atomic failure, poisoned attributes/hooks/env and no executed marker scripts. Race a second writer to prove no lost product commit or retry. Test post-push dispatch failure followed by a clean rerun, and excluded-only no-op. Execute actual composite/job conditions and env mappings after CI failure; use hosted Builds CI for real runner syntax/permission/root/sample/Windows checks, distinguishing that from local fixture proof of actual module writes.
- [x] `Tools/ci/README.md`, `docs/cicd-5-3-restore-job-results.md` and this story — document behavior, caller permissions, skip/delivery boundaries, verification and full source/run identities. Run focused suites, complete locked dual-Python checks, pinned online workflow lint and public API checks, then normal Builds CI for the exact implementation commit. Record both repository deltas for later review. No release or real module adoption is required.

**Acceptance Criteria:**

- Given a main push whose guard fails with owned drift and mixed product changes, when reusable CI completes its restore job, then remote main contains at most one repair commit retaining those product changes, and Actions receives a `ci.yml` dispatch on `main` after the successful push; the original CI run remains failed.
- Given a PR, manual dispatch, non-main push, unavailable/false drift, lint-only failure, cancelled run, Builds root or any sample `module-root`, when workflow conditions and direct script guards are exercised, then no restore fetch/write/dispatch occurs and all module-executing jobs remain read-only.
- Given module workflows differing by content, missing/extra paths or modes, when restoration commits any other eligible repair, then the remote workflow subtree remains identical to fetched main and CI config is unchanged, including when absence patterns or path conflicts intersect workflows.
- Given delivered and running Builds tags differing in either direction, when restoration runs, then its remote commit preserves the Builds gitlink, owned `.gitmodules` section and CI config; given equal verified tags and matching workflows, when those entries drift, then their eligible repairs reach remote main without reading module config to authorize them.
- Given unavailable/oversized/invalid expected data, poisoned module execution surfaces, unsafe candidate changes or a concurrent push, when restoration attempts its transaction, then no unauthorized commit reaches remote main, no module code executes and no CI dispatch follows the failure.
- Given a successfully pushed repair followed by dispatch failure, when the original restore is rerun against already-clean main, then CI is dispatched without a second repair commit; given only excluded drift, when it reruns, then neither an empty commit nor a dispatch loop is produced.
- Given the implemented caller permission union and standard Builds CI, when the exact implementation revision is tested, then the actual root/sample/Windows topology, both Python lanes, product checks, pinned lint and API checks pass, with module write/race behavior proven separately by executable fixtures rather than workflow-text assertions.

## Spec Change Log

- 2026-11-14: Resumed the completed planning handoff for implementation. The superproject baseline remains `06a3998be613e31affac5b69a755840e6a4bbcf3`; the implementation baseline is the pushed planning commit `2f4f1cf9ae4889f8d96b4af3ceb01442163d1215`.
- 2026-11-14: Caller permissions must be derived from the selected trusted tagged workflow, rather than hard-coded to the new runtime union. The existing `builds-version` stays at `v5.1.0`; old tags retain their read-only union and restore-enabled tags receive Contents/Actions write. This requires the renderer and its contract tests in addition to the caller template. Exact union validation and Windows read-only permissions remain required. No intent-contract change.

## Review Triage Log

### 2026-11-14 — Review pass
- verdicts: 18 findings/intent observations — high 0, medium 5, low 3, false 9, maybe-false 1
- findings:
  - `[medium]` `[patch]` V1 The default dispatch opener’s redirect protection is not exercised by existing tests. — The verification reviewer mutation-tested removal of the handler and all 22 runtime tests still passed; the isolated handler assertion and replacement-openers cannot detect that regression. Applied a real default-opener loopback transport regression that checks both the fixed GitHub request and absence of any request/authorization at the redirect target.
  - `[medium]` `[defer]` E1 Permission-union calculation rejects valid GitHub read-all/write-all shorthand. — Both the pre-existing global checker at 06a3998be613e31affac5b69a755840e6a4bbcf3 and the current shared calculation raise AttributeError for either shorthand in a parent probe. This is an inherited end-to-end validation limitation; all current pinned and restore-enabled declarations use explicit mappings.
  - `[false]` `[reject]` B1 A full comparison prevents independent repairs when a regular .github file replaces the directory. — The parent reproduced both comparisons: full comparison refuses the workflow ancestor, and eligible-only comparison independently refuses .github/dependabot.yml because removing the same unowned .github ancestor is unsafe. The intent matrix explicitly permits structural conflicts to fail before publication.
  - `[medium]` `[patch]` B2 HTTP protocol exceptions bypass dispatch sanitization. — A parent opener raising BadStatusLine left the raw marker in the escaping HTTPException; Dispatch and main did not catch this exception family. Applied a standard HTTPException catch with fixed transport diagnostics; opening/body-read protocol controls and a successful-push preservation regression pass.
  - `[medium]` `[defer]` B3 The moved permission union does not normalize shorthand declarations. — The parent confirmed the identical failure in the baseline global checker and current renderer. Grouped with E1 as the same pre-existing unsupported input form; current tags and new restore declarations use mappings.
  - `[medium]` `[patch]` B4 Injected-opener tests do not verify production redirect-handler installation. — Source inspection confirms both dispatch tests replace the opener and the adapter replaces Dispatch; the separately filed verification mutation demonstrates the gap. Grouped with V1. Applied a real default-opener loopback transport regression that checks both the fixed GitHub request and absence of any request/authorization at the redirect target.
  - `[maybe-false]` `[defer]` B5 An unfiltered shallow module fetch may exceed runner resources for a very large repository. — No eligible managed module or runner-capacity failure was demonstrated. Establishing this requires a large committed-main fixture, actual runner disk/network limits, and a qualifying drift event (ordinary CI first performs a broader checkout); retain as medium if true, unverified.
  - `[low]` `[reject]` B6 Individual Git subprocesses have no timeout below the job timeout. — The writer has an explicit ten-minute job bound and no retry; a stalled operation fails visibly at that bound. Per-operation controls would add timeout branches and policy for uncommon prolonged transport stalls rather than correct an everyday defect.
  - `[false]` `[reject]` B7 Skip logs allegedly prevent identification of the delivery action and mix clean paths with drift. — The log identifies policy-skipped entry indices and paths without asserting those paths drift; excluded-only output explicitly says remaining drift requires delivery. Every excluded category has the same required delivery action, so omission of optional per-condition wording does not produce the claimed action ambiguity.
  - `[low]` `[reject]` B8 Sanitized Git failures do not distinguish every push-rejection cause. — The operation and failure remain visible, and race rejection deliberately stops without retry. Safe cause classification would require new remote-stderr/porcelain parsing branches for uncommon failure diagnosis; raw stderr remains intentionally excluded.
  - `[false]` `[reject]` B9 Native workflow identity must have an additional hosted read-only probe. — Current GitHub documentation explicitly supplies all three job.workflow_* properties on GitHub.com and their ref/commit formats match the parser; authenticated workflow lint and the real mappings pass. No missing/different native value was demonstrated, and the contract expressly separates fixture write proof from hosted self/sample skips.
  - `[low]` `[reject]` B10 Local qualification logs should additionally be archived outside temporary storage. — Exact-source hosted jobs, links, full revisions and retained job IDs supply durable CI evidence for the complete Builds checks; local logs are supplemental and commands are reproducible. Extra artifact storage/workflow machinery is disproportionate to rare inspection of redundant local raw output.
  - `[false]` `[reject]` I1 The Git transaction is exercised through controlled remotes rather than a production module. — The contract explicitly excludes actual adoption and requires executable Git fixtures for module writes/races. Tests inspect remote main and its repair parent; the results do not claim production module writes.
  - `[false]` `[reject]` I2 The orchestration harness supplies native identity values and doubles dispatch. — The adapter executes real conditions/environment mappings and production Git transport, while separate HTTP tests exercise dispatch. Official native identity formats match the boundary; this acknowledged evidence surface supplies no demonstrated behavioral divergence.
  - `[false]` `[reject]` I3 Hosted Builds/sample evidence skips the restore writer. — Both contexts are explicitly forbidden restore invocations and correctly skip. Eligible-module hosted adoption is explicitly outside the intent, and the qualification document distinguishes these skips from real-Git transaction controls.
  - `[false]` `[reject]` I4 A literal reading would forbid write declarations on reusable caller jobs named ci. — Reusable callers declare a permission ceiling, not an executable module step; actual ci/hooks and Windows jobs retain contents read, while only restore receives Contents/Actions write. This is the single reading consistent with GitHub permission propagation and the required isolated writer.
  - `[false]` `[reject]` I5 Whole-entry glob skipping and whole-file .gitmodules protection are more conservative than per-path repair. — The existing engine selects perimeter entry indices; a glob intersecting protected workflows is ineligible as an entire entry. The canonical manifest has one owned Builds section, so preserving its complete file during a tag mismatch also preserves foreign product sections without withholding another eligible owned section.
  - `[false]` `[reject]` I6 Immediate production repair is not demonstrated because release/adoption remain unchanged. — The intent explicitly excludes release changes and actual module adoption. The diff provides reusable capability and future caller plumbing, with no claim that an unadopted production repository is already repaired.


### 2026-11-14 — Resumed review

- verdicts: 12 findings — high 0, medium 4, low 3, false 4, maybe-false 1
- findings:
  - `[medium]` `[defer]` R2-E1 Permission shorthand fails in the shared union calculation. — Carried from E1/B3: the same location, claim and unchanged calculation remain an inherited validation limitation. No second deferral is created.
  - `[medium]` `[defer]` R2-B1 Permission shorthand also fails during rendering. — Carried from E1/B3: moving the existing exact-union calculation into the renderer exposes the same unsupported declarations; all current selected declarations use mappings. No second deferral is created.
  - `[low]` `[reject]` R2-B2 Branch identity validation accepts a narrower alphabet than Git, including rejecting feature+safe. — The restriction is real, but module callers use exact stable release tags under AD-10; current branch/SHA callers are Builds self-tests, where restore is forbidden. Generalizing the accepted branch grammar adds validation policy for an uncommon development-only invocation, beyond a direct correction for routine callers.
  - `[false]` `[reject]` R2-B3 An oversized protected workflow should not prevent independent repair. — The demonstrated input exceeds the explicit bounded-blob/fail-oversized-input rule. Full comparison uses the bounded private Git adapter and fails before publication as required; the ordinary workflow-drift row does not override the oversized-input failure rule.
  - `[false]` `[reject]` R2-B4 cat-file size checking does not impose a Git download or disk limit. — The 4 MiB guarantee bounds in-memory document/blob reads, not Git pack transfer or disk allocation. cat-file -s returns only the size before Python materializes the blob. No violation of that guarantee was demonstrated; separate repository capacity qualification remains deferred.
  - `[maybe-false]` `[defer]` R2-B5 Fetching unrelated product blobs may exceed future runner capacity. — Carried from B5: the same unfiltered module fetch and hypothetical capacity failure are unchanged. The existing medium/unverified entry requires an eligible large-module fixture and runner limits; no second deferral is created.
  - `[low]` `[reject]` R2-B6 Git subprocesses should have deadlines below the job timeout. — Carried from B6: the ten-minute job bound remains enforced, with no retries. Per-operation timeout policy and cleanup branches remain disproportionate for the uncommon stall described.
  - `[false]` `[reject]` R2-B7 A hypothetical engine regression could modify product.txt beyond the additional protected-path invariant. — The actual engine limits its plan to selected ownership and refuses unselected ancestor/descendant removal at perimeter.py:610-687. Real repair tests independently assert preserved product and foreign partial content. No current path writes product.txt; the extra invariant specifically enforces restore's policy exclusions.
  - `[low]` `[reject]` R2-B8 Authentication qualification should add an HTTP Git server. — The adapter already executes the production subprocess and asserts the exact GitHub-scoped key, basic header bytes, push-only credential environment and credential-free readers. A second Git transport server would chiefly qualify Git's standard HTTP configuration handling; no production mismatch was shown, and the additional fixture complexity is disproportionate.
  - `[medium]` `[patch]` R2-B9 main's final token redaction and diagnostic escaping lack a hostile-error control. — The adapter's existing failure case uses a fixed identity error, and the lower-level protocol tests do not execute main's final sanitizer with hostile text. Added a direct main failure regression asserting exit 1 and the exact single escaped/redacted diagnostic.
  - `[false]` `[reject]` R2-B10 An accepted push followed by a client transport error needs a new combined recovery control. — A transport exception exits before dispatch with no retry; existing race controls cover that branch. A subsequent invocation independently recomputes current main; existing post-push failure/clean-rerun controls prove no second commit and dispatch-only recovery. No distinct uncovered decision or incorrect transition was identified.
  - `[medium]` `[patch]` R2-V1 The required returned HTTP 204 acknowledgment is unverified. — The verification reviewer removed only the explicit status rejection in an isolated copy and all 29 tests still passed; a returned 200 then reached dispatched=True. Added returned-200/202 regressions requiring the fixed HTTP error and response cleanup, while retaining the successful-204 control.

The two new patch entries change tests only. Existing carried findings retain their earlier routes and are not deferred again. Focused discovery passes all 31 restore tests. Independent in-memory mutations confirm that the new controls detect removal of HTTP-status rejection (including permitting only 202), token redaction and diagnostic escaping. Both entries are closed with no specific unverified risk. The regression commit was validated with pinned commitlint, pushed to Builds main as `fe5d7a6c0b68584131f5dce42f366e77b3e915fc`, and confirmed through git ls-remote. Complete qualification passed, including the focused prerequisite retry documented below.

## Design Notes

The accepted clone lifetime and writer environment are implementation seams, not new ownership formats. Keep comparison's existing external contract while retaining expected snapshots inside restore's acquisition scope. A fresh bare repository prevents module Git configuration and clean-filter commands from running while allowing the engine to honor committed text attributes. Candidate validation must preserve that sanitization too.

The source tag is the called workflow's identity. GitHub documents that `job.workflow_ref` and `job.workflow_sha` identify the reusable workflow and are available within execution steps; the `github` workflow identity describes its caller. Pass the native values in the restore composite step; no OIDC permission or identity-discovery service is needed. See [GitHub job context](https://docs.github.com/en/actions/reference/workflows-and-actions/contexts#job-context). Native `$/` already has hosted evidence in stories 2-4 and 5-1.

A stale true drift flag authorizes independent recomputation, never replay of stale changes. Current main is the repair parent, and the delivered branch is pinned once during that fresh acquisition. Subsequent pushes are handled by fast-forward rejection and the newer commit's CI. A concurrent delivered advance is reconciled by subsequent CI/delivery, not by retrying this writer.

All 19 earlier story specs were loaded for continuity through the two context investigations. They are done with completed execution tasks. Story 5-2's final hosted qualification covers current Builds source; its former catalog blockers and story 5-1's unused exception do not carry forward. Production registry/delivery writing remain future work, so a real module adoption must not be invented just to qualify restore.

## Verification

Implementation commands run from Builds unless marked CiCd:

- `python3 -m unittest discover -s Github/lib/tests -p 'test_restore*.py' -v` — real repair, race, failure and adapter tests pass.
- `python3 -m unittest discover -s Github/lib/tests -p 'test_expected_state.py' -v` and equivalent discoveries for `test_perimeter.py`, `test_guard.py`, `test_guard_adapter.py`, `test_ci_environment.py` — acquisition, ownership and existing guard/pipeline regressions pass.
- `uv run --no-cache --locked --script --python 3.12 Tools/ci/run_python_tests.py` and the same command with the captured runner Python executable — complete retained suites pass under both interpreters.
- `python3 Tools/ci/lint_workflows.py` — pinned actionlint/zizmor with authenticated online audits pass; no new blanket exception or frozen baseline regeneration.
- `uv run --no-cache --locked --script --python 3.12 Tools/ci/check_public_api.py` — committed implementation public API passes; record the caller permission change explicitly because the removal checker alone does not assess it.
- CiCd: `uv run --locked --script tools/render.py --check` — template and committed output remain synchronized; no module adoption.
- CiCd: `uv run --locked --script tools/tests/test_render.py --lint` and `uv run --locked --script tools/tests/test_validate.py` — old/new tagged caller permissions, exact-union rejection and generated workflow online audits pass.
- `git diff --check` in both repositories; inspect the Builds diff against `implementation_baseline_revision` and the CiCd diff against `baseline_revision` — scope, frozen paths and whitespace pass. Validate every commit message with the owning pinned commitlint before commit.
- Observe exact-source normal `builds-ci.yml` completion and retain full commit IDs/run links for both Python lanes, root/sample/Linux/Windows and quality/product checks. No restore success is claimed from the deliberately skipped Builds/sample write jobs.

Historical planning validation covered the contract, existing code and Git identities, native source-identity documentation, document metadata/acceptance checks, whitespace and exact-message pinned commitlint. That earlier planning-only delivery stopped before implementation. The current invocation resumes implementation and executes the verification commands above.

## Auto Run Result

Status: done

Story 5.3 is implemented, reviewed and verified. The approved intent contract is unchanged; all eight execution tasks are complete. The implementation baseline is `2f4f1cf9ae4889f8d96b4af3ceb01442163d1215`, and the CiCd baseline remains `06a3998be613e31affac5b69a755840e6a4bbcf3`.

Builds implementation `5f8ae823fb74e116c7dec5289fb0c91805f092e6` introduced the isolated writer. Review correction `522a5dda67756af5f7b1c04e0c7a6d3f39b555e2` sanitized dispatch protocol failures and strengthened default-opener coverage. Resumed-review regression commit `fe5d7a6c0b68584131f5dce42f366e77b3e915fc` adds returned-status and final-diagnostic controls without changing runtime behavior. Qualification documentation is committed and pushed as `0b6400457ca646d63a0c21bdad471f9c861e0c5b`; git ls-remote independently confirmed the complete revision. Builds is clean.

Normal exact-source [run 43542954431](https://github.com/Hexalith/Hexalith.Builds/actions/runs/43542954431) passed all seven retained jobs at `fe5d7a6c0b68584131f5dce42f366e77b3e915fc`. Both hosted Python lanes passed 14/14 groups and 925 tests each, including 509 library tests and all 31 restore tests. Root .NET, catalog contracts, sample, Windows, workflow lint and public API passed. Both self/sample restore jobs correctly skipped; actual eligible writes and races are proven by executable Git fixtures. The earlier full post-review run at `522a5dda67756af5f7b1c04e0c7a6d3f39b555e2` also passed.

Current local qualification covers all 14 groups and 925 tests per interpreter. The initial repeat ended with exit 120 under near-full workspace filesystem conditions. RAM-backed TMPDIR repeats passed 13/14 groups, and the remaining Tools/ci group passed all 46 tests under both interpreters after its verified linter inputs and read-audit authentication were restored at the new temporary location. No product or gate change was needed. Full-run, focused-retry and aggregate manifests are retained beneath `/dev/shm/bmad-5-3-qualification-0g2b9gv3/{312,runner}/`; the original attempts remain under `/tmp/bmad-5-3-final-{312,runner}.{log,json}`. Focused restore discovery independently passed 31/31.

Pinned authenticated workflow lint and public API checks passed at the regression revision, retaining 2,590 API entries with no removals. CiCd render/check, 32 renderer tests, eight generated-workflow online audits and 49 validator tests passed. The empty production registry produced no generated changes or adoption; builds-version remains v5.1.0. Both repository diffs passed whitespace checks, and pinned commitlint validated every new exact commit message before use.

The original review and three resumed-review layers retain individual verdicts for all 30 findings/intent observations. Four medium patch groups are closed, including independent mutations that detect removal of their safeguards; no specific unverified risk remains in those groups and followup_review_recommended remains false. Two grouped limitations remain deferred: inherited permission shorthand support and unverified very-large-module capacity. Carried findings retain their earlier routes without duplicate deferrals.

Builds content and its qualification record are pushed. The CiCd companion changes, this canonical story and the verified Builds pointer are included in the workflow's local completion commit; the superproject is not pushed. No release or real module adoption is part of this story.
