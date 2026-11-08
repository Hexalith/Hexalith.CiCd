---
review: reconcile-spec
target: ../ARCHITECTURE-SPINE.md
against: [SPEC.md (+ companions), baseline-and-targets.md, stories.yaml]
decision_log: ../.memlog.md
date: 2026-11-07
---

# Reconcile review: spine vs SPEC-cicd

**Verdict: PASS WITH FIXES.** All 9 spec Open Questions are closed by an AD or listed under Deferred. One is only partly closed (F-16). The spine contradicts no fixed message, tone or non-goal, apart from the deliberate amendments below. One real binding gap remains: Builds' own status (F-01). Most other findings are stale stories (F-02, F-03, F-04, F-08, F-09, F-11), and the spec still needs 15 amendments propagated back to it.

Types: **CONTRADICTION (unlogged)**: spine differs from the spec and the memlog has no decision for it. **BINDING GAP**: spine is silent where two stories could build incompatibly. **STORY MISMATCH**: the story's scope no longer matches the architecture. **OPEN QUESTION**: a spec OQ that is not fully closed. **ORPHAN**: a spec requirement that no story or AD owns. Amendments are listed separately (section 2).

## 1. Findings (ranked)

### F-01: Builds' status as a managed repo is undefined, and the counts disagree. HIGH
- **Type:** BINDING GAP / CONTRADICTION (unlogged)
- **Spec:** Non-goals and module-inventory: 18 managed repos *including* Builds. CAP-1 says "All 18 modules call the same Builds CI workflow". CAP-16 says "All 18 repositories are managed from here". CAP-14 and CAP-15 cover Builds' nightly release.
- **Spine:** frontmatter scope ("18 managed repos") vs Structural Seed ("18 module repos" + "Hexalith.Builds (public, managed)") and the sequence diagram ("Module release.yml (x18)" + Builds). AD-3 says registry = `setup/*.yml`. AD-7 installs the App on "the managed modules and CiCd". AD-4 owns the whole `.github/workflows/`. AD-16 reads the repo's `ci.yml` runs. AD-10 gives Builds its own release rules.
- **Issue:** It is never stated whether `setup/Hexalith.Builds.yml` exists.
  - **If it does:** AD-4 whole-directory ownership would overwrite Builds' hand-written reusable `ci.yml`/`release.yml` (and `ci-cd-standards.md`, which lives there). The guard and delivery would also manage a gitlink from Builds to itself.
  - **If it doesn't:** AD-7 does not put the App on Builds, yet `nightly.yml` must dispatch Builds' release and poll it with the App.
  - **Either way:**
    - AD-16 has no defined CI workflow for Builds. Its `ci.yml` is reusable, so it may have no push runs and the release would always say "main is red".
    - Builds' non-default release rules have no defined path under AD-2.
- **Fix:** Add one rule for Builds:
  - It has no setup file and is not delivered or guarded by AD-4.
  - The App is installed on it.
  - `nightly.py` dispatches it as the one named non-module.
  - Its own CI workflow name, which AD-16 reads, is fixed.
  - Its release rules arrive as an input.
  - Correct the counts to "17 modules + Builds".

### F-02: Migration stories push "with the delivery credential", which AD-6 and AD-7 forbid. HIGH
- **Type:** STORY MISMATCH
- **Spec:** stories.yaml 11–26 `invoke_dev_with`: "push with the delivery credential decided in story 1". Story 11 also says "delete their local workflow YAML".
- **Spine:** AD-7 says the App key "never enters a module or an agent session". AD-6 says only `deliver.yml` writes owned files. AD-4 makes unrendered workflow files drift, so delivery deletes them.
- **Issue:** A migration agent cannot hold the App credential. Under the spine a migration has three parts:
  1. Product, test and `.github/actions/**` changes, pushed with the module-agent token.
  2. A CiCd setup-file commit. AD-3 makes CiCd CI fail if the setup file names an action the module doesn't have yet, so this comes after step 1.
  3. Delivery, which replaces and deletes the workflows and removes the release config.
- **Fix:** Rewrite `invoke_dev_with` for stories 11–26 as: "product and custom-action changes with the module-agent token. Owned files only via the setup file in CiCd and `deliver.yml`. Order: actions first, then setup."

### F-03: Story 7 is a separate bumper, merged into delivery by AD-6, and delivery has no story. HIGH
- **Type:** STORY MISMATCH
- **Spec:** story 7, "Builds version lockstep bumper"
- **Spine:** AD-6 says "A Builds bump is a delivery of a changed version value, not a separate writer". AD-5, AD-10 and AD-18 cover the bump.
- **Issue:** No story owns `deliver.yml`. Its unowned scope:
  - sparse clone, diff, no-op when nothing changed, and push with an App token;
  - rebase and retry, never force-push;
  - the four triggers, including the hourly run at minute 17;
  - the `deliver` concurrency group;
  - the within-major bump with its `build(cicd): bump Builds to vX.Y.Z` commit.
- **Fix:** Retitle story 7 "Delivery: the single write path into modules (`deliver.yml`, incl. the Builds bump)" and move the bump wording under it.

### F-04: Story 4 renders commitlint and semantic-release config that AD-4 requires to be absent. HIGH
- **Type:** STORY MISMATCH (paired with amendment A-02)
- **Spec:** story 4: "render … commitlint and semantic-release config"
- **Spine:** AD-4 says these files "must be absent"; the config exists only in Builds composites.
- **Fix:** Story 4 should render:
  - both callers (`ci.yml`, `release.yml`), with any extra-runner and nightly jobs;
  - `.github/dependabot.yml`;
  - the Builds gitlink value;
  - the deny fragment.

  It should drop the release and commitlint config. Story 4 should also own CiCd's `ci.yml`: re-render diff, schema, submodule and App-installation check, action-exists check, and actionlint/zizmor.

### F-05: Delivery's handling of the perimeter is unbound (merge, delete, gitlink). MEDIUM
- **Type:** BINDING GAP
- **Spec:** CAP-11 says each module "keeps its own allow list" (enforcement.md: the entries are "merged in").
- **Spine:** AD-4 says "restore merges them". AD-6 says delivery just "writes the render".
- **Issue:** AD-4 says the restore merges, but says nothing for delivery. If delivery overwrites `.claude/settings.json`, it erases each module's allow list. If delivery never deletes the must-be-absent paths (`.releaserc*`, the `package.json` keys, the `.husky` hook), the guard fails on every run after onboarding. "No diff means no push" also needs a defined merge result to compare against.
- **Fix:** In AD-6, add: "delivery and restore apply the same AD-4 semantics through one Builds or CiCd function. That covers replacing the whole workflows directory, replacing whole files, setting the gitlink, merging the deny entries, and deleting must-be-absent paths and keys."

### F-06: Where the release workflow's jobs live is ambiguous. MEDIUM
- **Type:** BINDING GAP
- **Spec:** CAP-14 ("CodeQL before the release"), CAP-12, CAP-13
- **Spine:** AD-18 says "Each module's `release.yml` has these jobs: codeql, nightly-hook, release". The capability map puts CAP-14 in "Builds `release.yml` `codeql` job". The nightly hook is "Builds `prepare`, then `./.github/actions/nightly`", which is ambiguous between caller-rendered `@tag` and `$/` inside Builds.
- **Issue:** Story 3 (Builds release) and story 4 (templates) could each build the codeql and nightly-hook jobs. The caller must also grant `id-token: write` for Trusted Publishing.
- **Fix:** State that all three jobs are inside Builds' reusable `release.yml`. The nightly hook is a literal `./.github/actions/nightly` guarded by an input, like the CI hooks. The caller is one `uses:` job that grants `contents`, `security-events`, `actions: read` and `id-token: write`. Alternatively, choose the caller-rendered pattern explicitly.

### F-07: The duplicate scan is not placed, and neither the scan nor the action-exists check has a source. MEDIUM
- **Type:** BINDING GAP
- **Spec:** CAP-9 ("the nightly scan fails, and names the code"). enforcement.md: the scan "fails this repository's nightly run" and covers "custom actions and the scripts they call".
- **Spine:** The capability map points to `tools/scan.py` only. The AD-18 nightly rule does not mention the scan. AD-3 says CiCd CI fails if the setup file "names an action the module lacks".
- **Issue:** Stories 8 and 9 could disagree on whether the scan is a `nightly.yml` job and whether it turns the nightly run red. Neither the scan nor AD-3 says which module content it reads. CiCd's `references/` pointers go stale (Timesheets and Platform already are), so scanning them misses current code.
- **Fix:**
  - Add the scan to AD-18 as a `nightly.yml` job whose failure fails the nightly run.
  - State that CiCd tools read module content by shallow clone of each module's `main` head, never from the `references/` pointers. Alternatively, state that CiCd keeps its pointers current.

### F-08: Story 8 asks for staggered starts and is missing the scope AD-18 now assigns. MEDIUM
- **Type:** STORY MISMATCH (paired with amendment A-11)
- **Spec:** story 8: "with staggered start times"
- **Spine:** AD-18 dispatches everything at once at 02:17 UTC and lets GitHub queue the rest (memlog 5.6).
- **Fix:** Drop "staggered". Add the rest of AD-18's scope to story 8:
  - App-token dispatch, polling and the job-summary table;
  - failing the nightly run if any run failed;
  - delivery after Builds' release;
  - the keepalive, plus the deferred bot-activity check;
  - the duplicate-scan job (F-07).

### F-09: Story 1's spike is mostly answered, and creating the App has no owner. MEDIUM
- **Type:** STORY MISMATCH
- **Spec:** story 1: "Determine which credential can push and restore owned files … notifications, 60-day disable, concurrent-job limit, package-mode submodules, NuGet audit"
- **Spine:** AD-7 and AD-8 decide the credentials. memlog verified the notification behavior, the 60-day disable, the 20-job limit and NuGet audit. The Deferred list moves the remaining checks (`$/`, bot activity, the nuget.org claim) to other stories.
- **Issue:** No story creates the org GitHub App, installs it on the selected repos, or stores `HEXALITH_CICD_APP_PRIVATE_KEY`.
- **Fix:** Rescope story 1 to:
  - create and install the App, and store its key;
  - check whether package-mode builds read only the Builds submodule;
  - write the verified facts back into SPEC.

### F-10: Builds' own CI run against `Samples/` conflicts with "the guard is stage 1 of every CI run". MEDIUM-LOW
- **Type:** BINDING GAP
- **Spec:** CAP-15: "runs the reusable CI against its sample module"
- **Spine:** AD-8 says the guard is stage 1 and clones CiCd `rendered/<Repo>/`. AD-15 and AD-8 check the pointer against the caller tag. AD-2 forbids module-specific conditions.
- **Issue:** The sample has no rendered entry and no caller tag. When story 5 adds the guard, story 2's sample run breaks, or gains an ad-hoc skip.
- **Fix:** State how the sample satisfies the guard. Either CiCd keeps a fixture `rendered/` entry for it, or there is a generic `expected-source` input that Builds' own CI points at a fixture inside `Samples/`. Rendered callers can never set it.

### F-11: Story 5's credential and restore scope are stale. LOW
- **Type:** STORY MISMATCH
- **Spec:** story 5: "restores files on main … using the credential decided in story 1"
- **Spine:** AD-8 defines the restore:
  - it is a separate job using `GITHUB_TOKEN` with `contents` and `actions` write;
  - it restores only agent-reachable files, then dispatches `ci.yml`;
  - it leaves workflow drift to delivery.

  The guard also checks the must-be-absent paths and that the pointer equals the tag.
- **Fix:** Replace "credential decided in story 1" with the AD-8 restore job, and add the absence and pointer checks to story 5.

### F-12: The AD-16 "green" rule is ambiguous for several runs, and its order against draft completion is unset. LOW
- **Type:** BINDING GAP
- **Spec:** CAP-12: "On a red main, the release fails with 'main is red, nothing released'"
- **Spine:** AD-16 reads the push or `workflow_dispatch` runs for the head SHA. AD-17 step 1 completes an existing draft first.
- **Issue:** The rule doesn't say which run decides when a red push run and a green dispatch or re-run exist for the same SHA. If step 1 publishes an old draft while main is red, the release prints "nothing released" even though something was published.
- **Fix:** Add "the most recent run (by `run_started_at`, last attempt) decides", and either "the green check runs before step 1" or "step 1 is exempt and logs it".

### F-13: The allowed-dependency diagram has no caller-to-composite arrow. LOW
- **Type:** CONTRADICTION (spine-internal)
- **Spine:** "Allowed dependencies are the arrows above, and nothing else" vs AD-12 and AD-18: `uses: Hexalith/Builds/Github/prepare@<same tag>` in the caller.
- **Fix:** Add the arrow `CALLER -- "uses prepare @exact tag" --> COMP`.

### F-14: "At most once a night" vs builds-version commits at any time. LOW
- **Type:** CONTRADICTION (unlogged)
- **Spec:** Constraints and pipeline-stages: the workflow reference and the submodule move "at most once a night"
- **Spine:** AD-6 triggers on any push touching the Builds version. AD-10 adopts a major and rolls back through a CiCd commit at any time. AD-5's "render and commit together" rule names `setup/` and `templates/` but not `builds-version`.
- **Fix:** Amend the spec: "the *automatic* bump runs at most once a night, while a rollback or major adoption is a CiCd commit at any time". Add `builds-version` to AD-5's rule.

### F-15: Nothing stops a manual release dispatch. LOW
- **Type:** BINDING GAP
- **Spec:** Constraints: "A release starts only from the scheduler's `workflow_dispatch`". CAP-15: Builds releases "at most once a night".
- **Spine:** AD-7 doesn't say whether the module-agent token has the Actions permission. Nothing restricts who dispatches `release.yml`.
- **Fix:** In AD-7, state that the module-agent token has no Actions write. Alternatively, amend the spec to say that a manual dispatch by the maintainer is allowed.

### F-16: OQ4 is only partly closed: module-agent token expiry. LOW
- **Type:** OPEN QUESTION
- **Spec:** OQ4: "How are the fine-grained agent and scheduler tokens rotated before they expire?"
- **Spine:** AD-7 and Operations cover the App (no expiry) and the CiCd-agent token (renewed at expiry). They don't cover the module-agent token, which also has a 366-day maximum.
- **Fix:** Add to Operations: "the module-agent token is renewed at expiry, noticed in the next session (interactive only)". Alternatively, list it under Deferred.

### F-17: Spec deliverables with no story. LOW
- **Type:** ORPHAN
- **Spec:**
  - Assumptions: "The standard [`ci-cd-standards.md`] is rewritten to match this spec". The file lives at `Hexalith.Builds/.github/workflows/ci-cd-standards.md`.
  - gate-classification: "The rule is written into this repository's `AGENTS.md`".
- **Spine:** none
- **Fix:** Add both to story 10 or story 27. Move `ci-cd-standards.md` out of `.github/workflows/`, which matters if F-01 makes that directory generated.

### F-18: Story 15's "Aspire integration hook" vs AD-13. LOW
- **Type:** STORY MISMATCH
- **Spec:** story 15 says McpCli is "the first repo with an Aspire integration hook".
- **Spine:** AD-13 sends `AppHost.Tests` to shared stage 4. The Builds-owned environment setup lists only Dapr and Playwright.
- **Fix:** Reword story 15: "Aspire AppHost tests run in shared stage 4. Use an `after-unit-tests` hook only for McpCli-specific tier preparation."

### F-19: Python coverage in Memories and Tenants will trip the duplicate scan. LOW
- **Type:** BINDING GAP (watch)
- **Spec:** stories 22 and 23: "Python code needs to be covered by a shared stage or a custom action". CAP-9 allows zero shared fragments.
- **Spine:** AD-3's closed knob list has no Python stage.
- **Fix:** Decide in story 22 whether Python tests become a Builds stage plus a `python` knob (schema change plus a minor Builds release) before story 23 copies the same custom action.

## 2. Deliberate amendments to propagate back to the spec

Each spine–spec difference below is backed by the memlog. "Logged as amendment" means the memlog itself says it amends the spec. "Implicit" means the decision is logged but its effect on the spec is not.

| ID | Status | Spec location | Spine location | Memlog | Change to propagate |
| --- | --- | --- | --- | --- | --- |
| A-01 | AMENDMENT (deliberate, logged as amendment) | CAP-8 success 2 and 3; baseline row "CI/CD changes … persist"; enforcement.md Layer 2 step 4 | AD-8 | l.30–31 | The restore commit covers only agent-reachable owned files. Workflow drift is repaired by the next delivery, within 1 h: "No such change persists beyond the next CI run, or beyond the next delivery run (≤1 h) for `.github/workflows/**`". |
| A-02 | AMENDMENT (deliberate) | Constraints, owned perimeter ("the commitlint and semantic-release config") | AD-4 | l.33 (3.1 B) | In modules this config must be absent. It and its npm pins live only in Builds composites. Ownership means a guard absence check. |
| A-03 | AMENDMENT (deliberate, logged as refinement) | Non-goals: "Central failure reporting"; CAP-13 | AD-18; Operations | l.46 (5.1 B) | CiCd `nightly.yml` aggregates pass or fail with links and fails, and its failure email is the signal. The details stay in each module's run. |
| A-04 | AMENDMENT (deliberate, logged as amendment) | CAP-4 success 3 (onboarding) | AD-3 | l.50 (5.5 B) | Onboarding is submodule + setup file + adding the repo to the App installation + a nuget.org Trusted Publishing policy. |
| A-05 | AMENDMENT (deliberate; closes OQ1) | OQ1; pipeline-stages "Release propagation" ("as `fix(deps)` in Builds") | AD-10 | l.41 (4.3 B) | Builds releases on every commit type except `docs`, `test`, `chore`, `style`, not by `fix(deps)` discipline. |
| A-06 | AMENDMENT (deliberate, implicit) | CAP-6 success 2; baseline row "Builds version spread … within one night" | AD-10 | l.41 (4.3 B) | Modules are auto-bumped within one night only inside the current major. A new major needs a CiCd commit that also changes the templates. |
| A-07 | AMENDMENT (deliberate, implicit) | Constraints: "A separate job is allowed only for … different runner … slow, independent suite" | AD-8, AD-12 | l.30, l.54 (6.3) | Add a third exception, the restore job (permission isolation). The slow-suite exception is effectively removed: extra jobs are `needs: ci`, and parallel extra jobs were rejected. |
| A-08 | AMENDMENT (deliberate, logged as removing a known effect) | enforcement.md Known effects: "GITHUB_TOKEN commits don't start a new CI run …" | AD-8, AD-12 | l.39 (4.1 A) | The restore job dispatches `ci.yml` on `main`, so restored files are tested right away. The caller has a `workflow_dispatch` trigger. |
| A-09 | AMENDMENT (deliberate; closes OQ2 and OQ4) | Constraints, Credentials: "The scheduler's token … stored here as a secret" | AD-7 | l.27 | An org GitHub App, whose private key is a CiCd secret, both dispatches and delivers. Each job mints a scoped token. No unattended path uses a PAT. |
| A-10 | AMENDMENT (deliberate; closes OQ3) | CAP-13 success 1; Success signal; Constraints ("runs only when main is green and there are releasable commits") | AD-18 | l.43 (4.5 B), l.53 (6.2) | That night's release is also blocked by open high or critical CodeQL alerts on the default branch and by a failing `nightly` hook. |
| A-11 | AMENDMENT (deliberate) | pipeline-stages Nightly step 1 ("Start times can be staggered") | AD-18 | l.51 (5.6) | Everything is dispatched at once at 02:17 UTC, and GitHub queues anything beyond the 20-job limit. |
| A-12 | AMENDMENT (deliberate) | pipeline-stages Hook points ("such as after the build or after unit tests") | AD-14, AD-15 | l.52–53 (6.1, 6.2) | The only hooks are `after-unit-tests`, `after-integration-tests` and `nightly`. An after-build hook was rejected to keep CAP-3. |
| A-13 | AMENDMENT (deliberate) | pipeline-stages release step 3.3 (version → pack → publish → tag → GitHub release) | AD-17 | l.42 (4.4 C) | The release is a draft-release state machine. semantic-release computes only the version and notes, the tag is created last, and the release never commits to `main`. New fixed message: "publishing disabled". |
| A-14 | AMENDMENT (deliberate; closes OQ9) | Constraints and pipeline-stages "Dependency review is dropped if …" | AD-12 | l.18, l.60 | Dependency review is dropped, which is now a fact. Restore runs with `-warnaserror`. Known effect: NU1900 (feed unreachable) fails CI. |
| A-15 | AMENDMENT (deliberate, implicit) | pipeline-stages: "The only work done twice is one compile per released module per night" | AD-18 nightly-hook job (`prepare`) | l.53 (6.2) | A module with a `nightly` hook enabled compiles twice a night. |

## 3. Open Questions: closure check

| Spec OQ | Closed by | Status |
| --- | --- | --- |
| 1. Which Builds changes are releasable | AD-10 | Closed (A-05) |
| 2. Which credential delivers and restores | AD-6, AD-7, AD-8 | Closed (A-09) |
| 3. Does CodeQL block the release | AD-18 | Closed (A-10) |
| 4. How tokens are rotated | AD-7, Operations | **Partial**: module-agent token not covered (F-16) |
| 5. Who receives failure notifications | AD-18, Operations | Closed (A-03) |
| 6. 60-day schedule disable | AD-18 keepalive; Deferred (bot activity) | Closed / Deferred |
| 7. Free-plan concurrent-job limit | AD-18 ("GitHub queues") | Closed (the limit, 20, is in the memlog only) |
| 8. Which submodules a package-mode build reads | AD-12; Deferred | Deferred |
| 9. Does NuGet audit replace dependency review | AD-12 | Closed (A-14) |

## 4. Checked with no finding

- **CAP-1 through CAP-3, CAP-5, CAP-7, CAP-9 (guard part), CAP-10 and CAP-11** match AD-1, AD-4, AD-8 and AD-12 through AD-15, apart from the items above.
- **Fixed messages:** the guard, "main is red, nothing released" and "nothing to release" are quoted verbatim.
- **Commit types match:** bumps are `build:` (refined to `build(cicd):`), dependency bumps are `build(deps)` and `fix(deps)` forces a release.
- **Rules that hold:**
  - never `secrets: inherit`;
  - SDK from `global.json`;
  - tests per project;
  - no CodeQL on push or PR;
  - no Dependabot for `github-actions` or `gitsubmodule`;
  - the deny rules stay out of machine-wide managed settings, which the spine never proposes.
- **Non-goals:** the plan upgrade, deployment, malicious agents, review-based enforcement, automatic stage reordering, the release cascade and repacking are all respected. The spine's "no pre-push hook" is stricter than the spec's "no *mandatory* pre-push hook" and does not conflict with it.
- **Actions limits:** `pull_request_target` is not used. Nesting stays at one level of `workflow_call`.
- **baseline-and-targets.md:** the Operations section requires the same measurement method. The rows affected by amendments are A-01 and A-06.
- **Stories with no other mismatch:** 2, 3 (once F-06 is settled), 6, 9 (once F-07 is settled), 10 (with F-15 and F-17) and 27 are compatible. So are 12–14, 16, 17, 19–21 and 24–26, apart from the `invoke_dev_with` change in F-02. Folders' `nightly-drift` uses no secrets, so the deferred decision on hook secrets doesn't land before the EventStore migration.
