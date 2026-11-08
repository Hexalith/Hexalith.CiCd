# Review: reconcile the spine with the spec companions

- **Spine:** `../ARCHITECTURE-SPINE.md` (418 lines)
- **Decision log:** `../.memlog.md`
- **Companions checked:** `specs/spec-cicd/pipeline-stages.md`, `enforcement.md`, `gate-classification.md`, `module-inventory.md`
- **Date:** 2026-11-07
- **Method:** I read every companion rule against the spine, then against the memlog to tell deliberate amendments from unlogged drift. Where a gap rests on a fact about a module, I checked it in `references/` (evidence is cited in the finding). A missing restatement is not a finding when the detail belongs to a story and nothing in the spine conflicts with it.

## Verdict

**Needs revision before stories 2–5 start.** The spine keeps the companions' core: the stage order, the hook semantics, the deny list, the guard's PR/main behaviour, the release steps, propagation and the gate rule. Every change the memlog logged is a coherent amendment. But 3 high and 10 medium gaps remain. In each, two stories (usually Builds stories 2/3/5 vs generator story 4, or two migration stories) can now build incompatible things. Most are technical-surface or toolchain-drift items from `module-inventory.md` that no AD, convention, stack row or Deferred entry covers. 13 deliberate amendments and 2 unlogged deviations need to go back into the companions.

Severity: **H** = stories will collide or a CAP fails, **M** = likely divergence between repos or stories, **L** = wording, naming or a single-story detail worth pinning.

---

## 1. Gaps and contradictions (ranked)

### F1 (H): Builds' own status as a managed repo is undefined
- **Type:** silent, so stories can build incompatibly (type 1 and 4)
- **Companion:** `module-inventory.md` §Managed repositories, line 8 (Builds is one of the 18). `pipeline-stages.md` §Builds' own CI, lines 68–73 (Builds releases through the same nightly pipeline).
- **Spine:**
  - AD-3: the managed set is `setup/*.yml`.
  - AD-4: the whole `.github/workflows/` directory equals the render, and the Builds gitlink equals the caller tag.
  - AD-7: the App is installed on "the managed modules and CiCd".
  - AD-10: Builds has its own releaseRules.
  - AD-16: the green check reads "the module's `ci.yml`".
  - AD-18: dispatches "Builds and every module", and the diagram shows modules x18 *plus* Builds, which makes 19.
  - Convention row "Workflow file names": the reusable workflow is named `ci.yml`.
- **Problem:**
  - If story 4 writes `setup/Hexalith.Builds.yml`, delivery treats Builds' reusable `ci.yml` and `release.yml` as unrendered drift and deletes them. Builds also can't hold a pointer to itself, and Builds' `.claude` deny entries would block the CiCd agents that edit it.
  - If there is no setup file, the App installation (AD-7) and the nightly dispatch (AD-18) have no rule that includes Builds.
  - Builds already has its *own* push/PR `ci.yml` (`references/Hexalith.Builds/.github/workflows/ci.yml`), which collides with the reusable `ci.yml` name. The reusable `release.yml` would also need a `workflow_dispatch` trigger.
  - Builds' non-default releaseRules (AD-10) need a selector. A `github.repository` condition would break AD-2.
- **Fix:** Add a rule that Builds is managed as the runtime, not as a spoke. It should say:
  - whether Builds has a setup file, and its reduced perimeter (no workflow-directory ownership, no self-pointer, no deny entries);
  - that the App installation includes Builds;
  - the file name of Builds' own CI, and which file AD-16 reads for Builds;
  - Builds' release trigger;
  - that the releaseRules set is a `workflow_call` input.
  
  Fix the diagram count (17 modules + Builds).

### F2 (H): Where CodeQL and the nightly hook live is contradictory
- **Type:** contradiction inside the spine, plus a companion item (type 1)
- **Companion:** `pipeline-stages.md` lines 9 ("Builds keeps … The CodeQL workflow") and 42. `module-inventory.md` line 28 ("CodeQL stays (nightly)").
- **Spine:** AD-18 says "Each module's `release.yml` has these jobs: `codeql`, `nightly-hook`, `release` (needs both)", which reads as rendered caller jobs. The CAP map row for CAP-14 says "Builds `release.yml` `codeql` job". The convention lists only `ci.yml` and `release.yml` as Builds reusable workflows, so the fate of the existing thin `codeql.yml` is silent.
- **Problem:** Story 3 (Builds release) and story 4 (caller template) can put `codeql` and `nightly-hook` on opposite sides of the `workflow_call` boundary. `release` can't `needs:` a job across that boundary, and the Trusted-Publishing claim and the caller permissions differ depending on the choice.
- **Fix:** Pick one placement. The simplest is all three jobs inside Builds `release.yml`, with the hook as a literal `./.github/actions/nightly` guarded by an input. State it in AD-18, align the CAP map, and say that Builds' thin `codeql.yml` is deleted.

### F3 (H): Package-mode build with only the Builds submodule is undecided, so CI and the local check diverge
- **Type:** silent, so stories can build incompatibly (type 1 and 4)
- **Companion:**
  - `pipeline-stages.md` line 24: clone only the submodules the build reads; "package-mode build may need only Builds (*verify*)".
  - `module-inventory.md` lines 37, 72, 79: submodule mesh; "Parties: Initialize root-declared submodules".
- **Spine:** AD-12 says "The job checks out only the Builds submodule". AD-15 says the local check runs "the same stage 1–3 scripts". AD-2 forbids module-specific conditions, and the knob list is closed. The rule is in the spine, but no memlog decision backs it (see A8).
- **Evidence:** The modules choose source or package mode with different properties and defaults:
  - `UseNuGetDeps` / `UseHexalithProjectReferences` in Commons, EventStore, Tenants and others;
  - ChatBot keys it on `$(CI)` and `Configuration`;
  - Folders, Tenants and Parties' workflows pass `-p:UseNuGetDeps=true` explicitly;
  - Conversations has 14 source references into `references/`.
- **Problem:** The CI build (story 2) and the local check (story 6) run where different submodules are present (only Builds in CI; often all of them locally). Unless the shared build script forces one mode, the local check can pass in source mode while CI fails in package mode, which breaks CAP-3. Each migration story would also patch module props differently.
- **Fix:** Add to AD-12/AD-15: "The Builds build script always passes `-c Release -p:<one Builds-defined package-mode property>=true`. Builds Props defines it, and migration makes module props honour it." Log the "only Builds" narrowing in the memlog.

### F4 (M-H): Environment setup is missing outside the main CI job, and the trigger for browser setup doesn't match the kept browser gates
- **Type:** silent, so stories can build incompatibly (type 1 and 4)
- **Companion:**
  - `pipeline-stages.md` line 30: extra-job examples "a Windows runner, a browser, a Dapr topology".
  - `enforcement.md` lines 40–44: the deny list forbids `dapr init`, `actions/setup-dotnet` and `actions/cache` in custom actions.
  - `gate-classification.md` line 17: Folders' a11y/E2E checks and FrontComposer's browser tests are kept as custom actions.
- **Spine:**
  - AD-12 step 4: Builds-owned env setup is "Dapr when `dapr: true`, Playwright browsers for E2E projects", and it runs *after* the `after-unit-tests` hook.
  - AD-12 last bullet: the extra-runner job is `prepare` + action.
  - AD-18: the nightly hook is `prepare` + action.
- **Evidence:** FrontComposer's browser lane is npm Playwright (`npx playwright install --with-deps chromium`, `quality.yml:674`) and has no `E2E` `.csproj`. Folders has a .NET `Hexalith.Folders.UI.E2E.Tests`.
- **Problem:**
  - `prepare` sets up neither Dapr nor browsers, and the action may not run `dapr init`. So the companion's "Dapr topology" extra job can't be built, and neither can a nightly hook that needs Dapr.
  - A browser-based custom action gets browsers only if some E2E-named test project happens to exist. Story 24 (FrontComposer) would install Node and browsers inside its action, while story 17 (Folders) relies on Builds. That puts env setup in a custom action, which AD-12 says it prevents, and the duplicate scan may flag it.
  - The `after-unit-tests` hook can't use Dapr or browsers at all.
- **Fix:**
  - Make env setup one Builds-owned set of inputs (`dapr`, `browsers`, …) driven by setup knobs, applied identically by the CI job and by `prepare` (extra-runner and nightly jobs).
  - Decouple the browser install from the E2E-name heuristic (for example a `browsers: true` knob).
  - State which hooks see the environment.

### F5 (M): Aspire isn't covered
- **Type:** technical surface item not covered (type 4); changes a companion expectation (type 3)
- **Companion:**
  - `pipeline-stages.md` lines 12, 21: Dapr, Aspire and Windows become shared optional stages or custom actions; stage 4 is "(Dapr, Aspire)".
  - `module-inventory.md` lines 13, 73, 98: "McpCli: the first Aspire integration hook"; "Prepare Aspire tier" / "Run Aspire hook"; "Runtime: Dapr 1.18 and Aspire".
- **Spine:** Aspire appears nowhere. AD-13 sends `AppHost.Tests` to stage 4, so the Aspire tests run as shared integration tests without any hook.
- **Evidence:** Legacy Builds installs the Aspire workload (`Github/initialize-dotnet/action.yml`). `domain-ci.yml` has an `aspire-prepare-script` input that runs "after Dapr initialization".
- **Problem:** Story 15 (McpCli) must decide ad hoc whether Aspire is Builds env setup, a hook, or nothing. AD-12's order has no slot between env setup and integration tests, which is exactly where the legacy Aspire preparation ran. The "first Aspire integration hook" may no longer exist.
- **Fix:** State in AD-12 that Aspire needs no setup beyond Docker on the runner (no workload) and runs via the classifier, with `dapr: true` where needed. Say whether a `before-integration-tests` hook exists. Update migration-order item 3.

### F6 (M): Registry and image pulls in CI have no credential rule
- **Type:** technical surface item not covered (type 4)
- **Companion:**
  - `module-inventory.md` lines 26 ("needs … registry secrets everywhere"), 100–101 (Postgres image pinned by digest; Zot `registry.hexalith.com`).
  - `enforcement.md` line 46 (a registry login is denied in actions).
- **Spine:** Zot appears only in the Structural Seed diagram ("MODS → org secrets → ZOT"). AD-14 gives actions no secrets. The Deferred entry covers *hook and job* secrets only.
- **Evidence:**
  - EventStore and Parties CI log in to Zot with a pull-reader pair, `HEXALITH_CI_REGISTRY_USERNAME/PASSWORD` (e.g. `Hexalith.Parties/.github/workflows/ci.yml:49`).
  - Memories CI pre-pulls `docker.io/library/postgres@sha256:…` (`ci.yml:660`), and its tests pin the digest.
- **Problem:** Stories 20 and 21 must invent a CI-time pull credential path ad hoc: a secret on the Builds `ci.yml` API, an env-setup login, or dropping the pulls. Dependabot PR runs won't have Actions secrets either.
- **Fix:** Add either "CI never pulls from Zot" or a Builds-owned optional registry-pull env-setup step with an explicit secret pair in Builds `ci.yml`'s `workflow_call` API, plus a rule for digest-pinned public images (pulled lazily by tests; no pre-pull step).

### F7 (M): The restore dispatch cancels the run that should fail
- **Type:** the spine breaks a companion rule (type 1)
- **Companion:** `enforcement.md` line 22: on a push to `main`, the guard "restores … then fails the run with the same message".
- **Spine:** AD-8: the restore job dispatches `ci.yml` on `main`. The concurrency convention is "CI per ref, cancel superseded".
- **Problem:** The dispatched run lands in the same `ci-<ref>` group while the originating run is still in progress (its restore job is finishing). With `cancel-in-progress` it cancels the originating run, which then ends *cancelled*, not *failed*. That loses the ownership message signal and confuses the AD-16 history.
- **Fix:** Concurrency convention: cancel superseded runs only for `pull_request`, or key the group on the event. State this in the Conventions row.

### F8 (M): Caller-granted permissions aren't part of the Builds interface
- **Type:** silent, so stories can build incompatibly (type 1)
- **Companion:** `enforcement.md` §Layer 2 (restore on main), `pipeline-stages.md` §Nightly run (publish, tag, CodeQL).
- **Spine:**
  - AD-8: the restore job needs `contents: write` and `actions: write`.
  - AD-17: `id-token: write`, plus draft-release writes.
  - AD-18: CodeQL needs `security-events`.
  - AD-10: the public API is "inputs and secrets".
- **Problem:** A called workflow can only narrow the caller's permissions (memlog line 16). The rendered callers (story 4) must grant exactly the union that the Builds jobs (stories 2, 3, 5) need. Nothing fixes that contract, and zizmor's default `excessive-permissions` audit will push the two sides apart.
- **Fix:** Add "required caller permissions per Builds workflow" to the AD-10 public API, and render them per job.

### F9 (M): No canonical names for variables and secrets, and the kill-switch default fails silently
- **Type:** toolchain drift item not covered (type 4)
- **Companion:**
  - `module-inventory.md` line 67: variable names differ per repository.
  - `pipeline-stages.md` line 50: the kill switch.
- **Spine:**
  - Convention: only the `HEXALITH_` prefix rule.
  - AD-17: "not `true`" means "publishing disabled" and the run succeeds.
  - The memlog 5.5 onboarding list omits setting the variable.
- **Evidence:**
  - `vars.NUGET_USER` ×18 vs `vars.NUGET_TRUSTED_PUBLISHING_USER` ×4. `NuGet/login` needs a `user` input.
  - `HEXALITH_ZOT_*` vs `ZOT_REGISTRY_*` vs `HEXALITH_CI_REGISTRY_*`.
- **Problem:** Each migration story will name variables its own way. A missing or misnamed kill-switch variable turns into a nightly green "publishing disabled" that the nightly summary reports as success, so CAP-13 fails silently.
- **Fix:**
  - Add a Conventions row listing the canonical names and their level (org or repo): `HEXALITH_RELEASE_PUBLISH_ENABLED`, `HEXALITH_NUGET_USER`, `HEXALITH_ZOT_USERNAME`/`_API_KEY`, and any CI pull pair.
  - Add "set the kill switch" to onboarding.
  - Have the nightly summary flag "publishing disabled" distinctly.

### F10 (M): How the SDK pin is unified isn't decided
- **Type:** toolchain drift item not covered (type 4)
- **Companion:** `module-inventory.md` line 64: `global.json` split across 10.0.401/.402/.403; FrontComposer hard-codes the SDK in 10 places; "Architecture unifies all of these".
- **Spine:** The Stack row says ".NET SDK 10.0.403 (from each `global.json`)", and the convention says "SDK from the module's `global.json`". `global.json` is not in the AD-4 perimeter.
- **Problem:** The row states one version while the mechanism is per module. Nothing says who aligns or bumps the 18 `global.json` files, or whether a module may lag Builds' `Samples/` SDK. Migration stories will diverge: exact pin vs `rollForward`, aligned vs left as is.
- **Fix:** Either render the `global.json` `sdk` block from one CiCd value (add it to the AD-4 perimeter, like `builds-version`), or state that it is module-owned with a Dependabot `dotnet-sdk` ecosystem and a guard floor check.

### F11 (M): Dependabot ecosystems are undecided while the knob list is closed
- **Type:** silent, so stories can build incompatibly (type 4)
- **Companion:**
  - `module-inventory.md` lines 54–56: ChatBot, McpCli and Projects have no Dependabot.
  - Technical surface: Python, Node, images.
  - `pipeline-stages.md` line 63: bumps are `build(deps)`.
- **Spine:** AD-4 renders `dependabot.yml` as a whole file. AD-10 forbids only the `github-actions` and `gitsubmodule` ecosystems. AD-3's knobs can't vary ecosystems per module.
- **Problem:** Story 4 must decide alone whether every module gets `nuget` only, or also `npm` (FrontComposer), `pip` (Memories, Tenants), `docker` or `dotnet-sdk`, and with which commit prefix.
- **Fix:** State the render rule: a fixed set, or derived from a new knob. Fix the commit message (prefix `build`, scope `deps`) so AD-10's non-release rule holds.

### F12 (M): Python, PowerShell and Node product code has no shared stage or env rule
- **Type:** technical surface item not covered (type 4)
- **Companion:**
  - `module-inventory.md` lines 94–97: Python in Memories (122 files) and Tenants (71), PowerShell, Node.
  - `enforcement.md` line 53: the scan covers YAML, shell, PowerShell and Python.
- **Spine:** AD-13 classifies only MSBuild `IsTestProject` projects. AD-12 says Builds owns env setup "to prevent duplication", but provides none for Python or Node.
- **Evidence:** Memories and Tenants run `python3 -m unittest discover …` in about 15 steps. Folders' nightly runs `pwsh` scripts.
- **Problem:** Stories 22 and 23 will each build their own Python env and test runner in a custom action. The duplicate scan then forces a hoist and a new knob mid-migration.
- **Fix:** Decide now. Either custom actions may use the runner's `python3`, `pwsh` and `node` as-is with no `setup-*` actions (and say so in AD-14), or add a `python` shared-stage knob to AD-3 up front.

### F13 (M): The Windows runner breaks the `python3` assumption (verify)
- **Type:** technical surface item not covered (type 4)
- **Companion:** `module-inventory.md` line 103 (a Windows runner for Conversations), `pipeline-stages.md` line 30.
- **Spine:**
  - AD-11: "run with `python3`".
  - Stack row: "Python ≥ 3.12 (runner system 3.12.3)", which is the Ubuntu runner's system Python.
  - AD-12: `prepare` runs in the extra-runner job on `windows-latest`.
- **Evidence:** Conversations' Windows job calls `python`, while its Linux job calls `python3` (`ci.yml:141` vs `:195`).
- **Problem:** `prepare`'s scripts may fail on Windows, or story 16 adds an OS branch ad hoc. The Python version on the Windows image isn't verified.
- **Fix:** AD-11: Builds composites resolve the interpreter portably (`shell: bash` + `python3 || python`, or a pinned `actions/setup-python`). Add a Windows Python row to the Stack.

### F14 (L-M): Node provisioning isn't pinned
- **Type:** toolchain item not covered (type 4)
- **Companion:** `module-inventory.md` line 97 (Node for commitlint and semantic-release), `enforcement.md` line 53 (jscpd).
- **Spine:** The Stack says "Node.js ≥ 24.10" but has no `actions/setup-node` row. Memlog 5.4 says not to depend on image specifics. AD-15's local check runs commitlint, so it needs Node locally.
- **Evidence:** Builds today pins `actions/setup-node@v7.1.0` with Node 24.
- **Problem:** The guard, release and CiCd scan stories pick Node setup independently.
- **Fix:** Add a `setup-node` row and the rule "Node is installed by the Builds and CiCd steps that run Node tools". State the local check's Node prerequisite.

### F15 (M): The premise for dropping dependency review doesn't cover netstandard2.0 (verify)
- **Type:** a companion conditional resolved on a partial premise (type 1)
- **Companion:** `pipeline-stages.md` lines 75–77 (drop dependency review only if NuGet audit fails on vulnerable packages), `module-inventory.md` line 28.
- **Spine:** AD-12 step 2. Memlog line 18 verified transitive audit "for net10.0".
- **Evidence:** There are netstandard2.0 projects in EventStore (`RestApi.Generators`), PolymorphicSerializations (`CodeGenerators`, a pilot), McpCli (`Analyzers`) and FrontComposer (`SourceTools`, `Contracts`, `Schema`).
- **Problem:** If `NuGetAuditMode` defaults to `direct` for non-net10 TFMs, transitive vulnerabilities in packable netstandard libraries are no longer gated anywhere.
- **Fix:** Builds Props sets `NuGetAuditMode=all` (and `NuGetAuditLevel=low`, matching NU1901–1904). Cite it in AD-12.

### F16 (L-M): zizmor's default policy vs tag pins (verify)
- **Type:** possible contradiction inside the spine, involving a companion rule (type 1)
- **Companion:** `pipeline-stages.md` line 70 (actionlint and zizmor on Builds' workflows), `module-inventory.md` line 110 (exact release tags replace SHAs).
- **Spine:** The convention says "pass `actionlint` and `zizmor` with default policy". AD-10 requires exact tags for Builds. The Stack lists tag versions for `NuGet/login` and `astral-sh/setup-uv`.
- **Problem:** zizmor's default `unpinned-uses` policy is believed to require hash pins outside `actions/*` and `github/*`. If so, Builds and CiCd workflows fail their own lint, as would the rendered callers if CiCd CI lints them.
- **Fix:** Ship a zizmor config that allows ref pins for the Hexalith Builds repo and either hash-pins third-party actions (with tag comments) or ref-pins them. Say whether rendered callers are linted.

### F17 (L): The Builds repo slug is wrong
- **Type:** contradiction with the facts (type 1)
- **Companion:** `module-inventory.md` line 8 (all names prefixed `Hexalith.`).
- **Spine:** AD-12 says `uses: Hexalith/Builds/Github/prepare@<same tag>`. The real slug is `Hexalith/Hexalith.Builds`, per `.gitmodules` and today's callers.
- **Fix:** Correct the slug, and use it in the Structural Seed too.

### F18 (L): The fate of the remaining Builds workflows is unassigned
- **Type:** module-inventory item not covered (type 4)
- **Companion:** `module-inventory.md` lines 28–29 (the thin gates `codeql`, `dependency-review` and `commitlint`; "the rest are reviewed against the new workflows").
- **Spine:** The conventions list only `ci.yml` and `release.yml`. The Deferred entry for composites covers composite names only.
- **Evidence:** Builds also has `build-release.yml`, `candidate-policy.yml` and `commitlint-caller.yml`. These are in neither the CAP-16 deletion list nor any AD.
- **Fix:** Add them to the story 27 deletion list, or state the rule "everything in Builds `.github/workflows/` other than `ci.yml`, `release.yml` and Builds' own CI is deleted".

### F19 (L): Dapr pins on the module side, and the CLI pin
- **Type:** toolchain drift item partly covered (type 4)
- **Companion:** `module-inventory.md` lines 65 and 98: Dapr runtime pins 1.18.2–1.18.7 "even within one repository"; "Dapr 1.18".
- **Spine:** The Stack row "Dapr runtime (one pin in Builds) 1.19.1" covers only the CI runtime. The memlog also pins the CLI, but the Stack doesn't.
- **Evidence:** Memories' test and qualification code pins `daprd:1.18.1`.
- **Problem:** A run can mix the CI runtime from Builds (1.19.1) with test-container images that module code pins to 1.18.x. Migration stories will align them or not, ad hoc. The 1.18→1.19 move is recorded only as a version note.
- **Fix:** Add the CLI pin. State whether migrations align module-side Dapr pins to Builds' pin or leave them as product code. Log the minor-version move as a decision.

### F20 (L): Coverage and test-floor gates have nothing to consume
- **Type:** a gate-classification item the spine can't host (type 1)
- **Companion:** `gate-classification.md` lines 40, 46 (Agents "Enforce package test floors"; FrontComposer "Coverage Summary" are still unclassified).
- **Spine:** AD-14: actions never rebuild and write no result files. The shared test stages emit no results.
- **Problem:** If a migration story keeps such a gate, it must rerun the tests, which breaks "nothing runs twice".
- **Fix:** Either state that coverage and test-floor gates are classified *delete*, or have stage 3/4 leave TRX and coverage output at a fixed path that hooks may read.

---

## 2. Amendments to propagate back

| ID | Companion location | Spine location | Status | Propagate as |
| --- | --- | --- | --- | --- |
| A1 | `pipeline-stages.md` l.29: hook points "such as after the build or after unit tests" | AD-14, AD-15; memlog 6.2 | AMENDMENT (deliberate) | Hooks are only `after-unit-tests`, `after-integration-tests` and `nightly`. There is no after-build hook (CAP-3). |
| A2 | `pipeline-stages.md` l.30: the extra job "repeats checkout, restore, and build" | AD-12 last bullet; memlog 6.3 | AMENDMENT (deliberate) | The extra job is `prepare` + action with `needs: ci`, so it runs after CI and never in parallel. This also retires the SPEC constraint's "slow independent suite" split. |
| A3 | `pipeline-stages.md` l.41: "Start times can be staggered" | AD-18; memlog 5.6 | AMENDMENT (deliberate) | All runs are dispatched at once at 02:17 UTC and GitHub queues them. Story 8's text says "staggered" too. |
| A4 | `pipeline-stages.md` l.46: "sets the version, packs, publishes …, tags the commit, and creates the GitHub release" | AD-17; memlog 4.4 C | AMENDMENT (deliberate) | A draft release is the in-progress marker, the tag is created last by publishing the draft, and nothing is committed to `main` (no CHANGELOG commit). |
| A5 | `pipeline-stages.md` l.44 | AD-16; memlog 4.1 A | AMENDMENT (deliberate) | "Green" means the Actions API run of `ci.yml` (push or `workflow_dispatch`) for the head SHA; the release waits ≤ 30 min while it is in progress. |
| A6 | `pipeline-stages.md` l.65: a Props change releases Builds "as `fix(deps)` (*verify*)" | AD-10; memlog 4.3 B | AMENDMENT (deliberate) | Builds releases on every commit type except `docs`, `test`, `chore` and `style`. This closes OQ1. |
| A7 | `pipeline-stages.md` ll.55–58: the bump "in one commit per module; at most once a night; as a `build:` commit" | AD-6, AD-10, AD-18; memlog 4.2 B, 4.3 B | AMENDMENT (deliberate) | The bump is a delivery of a changed value, as `build(cicd): …`. It runs nightly *after* releases. A rollback or a major adoption is a CiCd commit, delivered on push at any time. |
| A8 | `pipeline-stages.md` l.24: clone "only those the build reads … (*verify*)" | AD-12 ("only the Builds submodule"); Deferred | **CONTRADICTION (unlogged)**: a narrowing made before story 1 verified it, with a fallback knob | Log it in the memlog. Companion: "only Builds; any other submodule needs a `submodules` knob". See F3. |
| A9 | `pipeline-stages.md` l.77: dependency review dropped "if" NuGet audit covers it | AD-12 step 2; memlog l.60 | AMENDMENT (deliberate) | Dropped. Restore runs with `-warnaserror`. See F15 for the netstandard caveat. |
| A10 | `enforcement.md` l.16: "downloads the module's expected owned files" | AD-8; memlog 3.3 B | AMENDMENT (deliberate, a refinement) | Shallow sparse git clone of CiCd `main` `rendered/<Repo>/`, never raw or REST (CDN staleness). |
| A11 | `enforcement.md` l.22: "restores the expected files in one commit, then fails" | AD-8; memlog ll.30–31 | AMENDMENT (deliberate) | A separate `restore` job (`GITHUB_TOKEN`, `contents`+`actions` write) restores the *agent-reachable* files and dispatches `ci.yml`. `.github/workflows/**` drift stays red until the next delivery (≤ 1 h). CAP-8 wording is amended too. |
| A12 | `gate-classification.md` l.17 and `module-inventory.md` l.15: Folders' E2E/a11y gates and FrontComposer's browser tests "kept as custom actions" | AD-12 step 4, AD-13; memlog 6.2, classifier option C | AMENDMENT (deliberate, implied) | .NET test projects named `*E2E*` run as shared stage-4 tests with Builds-installed browsers. Only non-test-project checks become actions. See F4 for npm Playwright. |
| A13 | `module-inventory.md` l.28 and `pipeline-stages.md` l.42: CodeQL "stays (nightly)" and reports | AD-18; memlog 4.5 B | AMENDMENT (deliberate) | The `codeql` job *blocks* the release when the default branch has open high or critical alerts. This closes OQ3. |
| A14 | `module-inventory.md` l.66: NuGet auth split between API key and OIDC | AD-17; memlog 5.3 A | AMENDMENT (deliberate) | Trusted Publishing everywhere. Both workflow files are named `release.yml`, with one nuget.org policy per repo. |
| A15 | `module-inventory.md` ll.65, 98: Dapr 1.18 | Stack: Dapr 1.19.1 | **CONTRADICTION (unlogged)**: memlog l.59 records the version only, with no decision | Log the minor-version move. See F19. |
| A16 | `enforcement.md` l.8: the CiCd-agent token "scoped to Builds and this repository" | AD-7; memlog 5.1 | AMENDMENT (deliberate) | Interactive sessions only. It also owns the cron edits, so the maintainer receives the nightly failure email. |

## 3. Known effects the architecture removed, changed or created

| ID | Companion | Effect | Change | Source |
| --- | --- | --- | --- | --- |
| K1 | `enforcement.md` l.28 | "`GITHUB_TOKEN` commits don't start CI; restored files are tested only on the next push" | **Removed.** The restore job dispatches `ci.yml`. | memlog 4.1 A |
| K2 | `enforcement.md` l.27 | The restore commit races the agent's next push | **Extended.** It also races delivery, which rebases and retries and never force-pushes. | AD-6 |
| K3 | none | Drift under `.github/workflows/**` on `main` stays red for up to 1 h, until the next hourly delivery | **Created** | memlog ll.30–31 |
| K4 | none | For about 1 min after each CiCd change, module CI sees drift. Restore moves agent-reachable files (including the Builds pointer) to the new render before delivery updates the callers, so the caller tag and the pointer briefly mismatch. | **Created** | memlog 3.3 B |
| K5 | `pipeline-stages.md` l.77 | NU1900 (feed unreachable) fails CI. NU1901 (low) advisories fail CI. A newly published advisory turns `main` red with no commit. | **Created** | memlog l.60, AD-12 |
| K6 | `pipeline-stages.md` l.46 | "The only work done twice is one compile per released module per night" | **Changed.** A module with a nightly hook compiles again in `prepare` every night, even when there is nothing to release. | AD-18 |
| K7 | `pipeline-stages.md` l.42 | A CodeQL finding appears within 24 h | **Changed.** An open high or critical alert now blocks that module's release, and pre-existing alerts block the first night after migration. | memlog 4.5 B |
| K8 | none | A move of the `ubuntu-latest`/`windows-latest` image can break every module without a Builds release | **Created** | memlog 5.4 |
| K9 | none | No CHANGELOG commits; release notes exist only in GitHub releases | **Created** | memlog 4.4 C |
| K10 | `pipeline-stages.md` l.66 | A module's package keeps referencing an older Hexalith version until the module changes | **Kept, but longer.** Modules release on the Builds tag their head referenced the previous night, and the bump runs after releases. | memlog 4.2 B |
| K11 | `pipeline-stages.md` l.77 | Dropping dependency review costs the license check and npm coverage | **Extended.** Pip coverage (Memories, Tenants) is also lost, and transitive netstandard coverage unless F15 is fixed. | AD-12 |
| K12 | none | A release can wait up to 30 min on CI that is still in progress | **Created** | AD-16 |

## 4. Outside the four companions (for completeness)

**SPEC.md**
- CAP-8 success: "beyond the next CI run, or the next delivery (≤ 1 h) for `.github/workflows/**`" (memlog l.31).
- CAP-4 onboarding: also add the repo to the App installation and create the nuget.org policy (memlog 5.5).
- Non-goal "central failure reporting" is refined: CiCd aggregates pass and fail (memlog 5.1).
- Constraint: "this repository owns … the commitlint and semantic-release config" becomes "those live only in Builds; modules must not carry them" (memlog 3.1 B).
- Constraint: "scheduler's token stored as a secret" becomes the App private key (memlog 5.1).
- Constraint: the "slow independent suite" separate job conflicts with `needs: ci` (A2).
- OQ1–OQ5 are closed by the memlog. OQ8 is narrowed (A8). OQ9 is applied (A9).

**stories.yaml**
- Story 4: "render … commitlint and semantic-release config" contradicts AD-4.
- Story 5: "credential decided in story 1" is already decided (`GITHUB_TOKEN` restore, App delivery).
- Story 7: the bumper is a delivery of a changed value, not a separate writer (AD-6).
- Story 8: "staggered start times" (A3).
- Stories 11–26: "push with the delivery credential" contradicts AD-7, under which the App key never enters an agent session. The migration's product-side changes need the module-agent token, and owned files go through setup + delivery.

## 5. Other observations (not companion-derived)
- **Pending runs get cancelled anyway.** "Never cancelled" (`deliver`, `release`) holds only for the running job. GitHub keeps one *pending* run per group and cancels the older pending one. The hourly delivery at :17 coincides with the 02:17 nightly start. If nightly's delivery is a job in the `deliver` group, it can be cancelled as pending, and nightly goes red. Have nightly dispatch `deliver.yml` (idempotent) rather than join the group, or accept this explicitly.
- **AD-16 vs AD-17 order is unstated.** The release could complete an existing draft whose SHA is green while the head is red, or refuse it. This is a single-story choice (story 3), but worth one sentence.

## 6. Checked and consistent (no finding)
- **Stage order:** stages 1–4, stopping at the first failing test project, hooks after unit tests.
- **Rules carried through:** SDK from `global.json`; no `run:` script hooks; the local check runs stages 1–3 with no mandatory pre-push hook; the guard runs first and fails PRs with the diff and fixed message; restore instead of revert.
- **Fully covered:** the deny list (AD-8 binds it); the `.claude/settings.json` merge that keeps each module's allow list; the Layer 1 token split; the duplicate scan's tool and scope; hoisting; the agent-instruction items (CAP-11 map).
- **Release:** red `main` fails and nothing-to-release succeeds; rerun-safe pushes; the kill switch; `build(deps)`/`fix(deps)` propagation; no cascade; exact tags with lockstep and reverse-bump rollback; Builds' own CI lints and runs `Samples/`.
- **Migration inventory:** the gate keep/delete lists; the legacy Builds deletions; unifying the release patterns; filling the baseline gaps (CodeQL in the nightly run, rendered Dependabot, commitlint in the guard).
