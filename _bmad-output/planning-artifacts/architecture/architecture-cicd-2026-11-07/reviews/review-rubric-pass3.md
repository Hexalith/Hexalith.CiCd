# Rubric review, pass 3: ARCHITECTURE-SPINE.md (Hexalith.CiCd), 2026-11-08 update

- **Reviewed:** `../ARCHITECTURE-SPINE.md` (562 lines) with its uncommitted diff against the finalized 2026-11-07 version, and the memlog entries after "spine finalized" (U1–U4 and the 2026-11-08 reality checks).
- **Checked against:**
  - `specs/spec-cicd/` after its refresh: `SPEC.md`, `pipeline-stages.md`, `enforcement.md`, `module-inventory.md`, `stories.yaml`;
  - brownfield `references/Hexalith.Builds` at `3c80961`: `schemas/` (all 16 files parsed), `.github/workflows/` (all 15 files), `Github/` (17 directories), `Tools/` (68 entries), and the legacy tests that read workflow files;
  - module references to Builds (`references/*/.github/workflows`, counted by grep);
  - prior reviews, especially `review-rubric-pass2.md`, which this pass does not repeat.
- **Scope:** today's changes and what they break elsewhere. Pass-2 findings appear only where today's change resolved, worsened or reopened them (closure table).

## Verdict

The update does what it set out to do, and the mechanical part is clean:
- `format`, `builds_tag`, `hexalith-ci.v1` and `hexalith-perimeter` are gone from the spine.
- No AD names a story number. Story numbers appear only under Deferred.
- Every Deferred owner matches the refreshed `stories.yaml`, apart from L8.
- The schema file names match all 16 files in Builds' `schemas/`.
- The interim `builds-release.yml` can be built: its green-CI check lives in `Tools/verify-g4-release-source.sh` and `Tools/G4PackageQualification.functions.ps1`. Both are Builds-only and are not frozen.

Two changes introduce contract defects that the stories below will hit early:
1. **The schema convention contradicts AD-3.** Setup files have no `schema`, yet they are validated against a schema that now requires one. Which keys of `hexalith.ci.v1` are required is not decided.
2. **The rename sequence collides with the freeze.** The rename (AD-19/AD-20) breaks legacy tests inside frozen composite directories, and `builds-ci.yml` has no defined interim, so Builds' green check, the interim release and the bootstrap stall.

The new end-state rule closes the orphan problem for `.github/workflows/` only. The new Precedence rule no longer says what happens when `stories.yaml` conflicts with the spine, and it conflicts today in three places.

**Counts: 0 critical, 2 high, 6 medium, 8 low.**

## Pass-2 closure (items touched by today's change only)

| Pass-2 item | Status after today | Note |
| --- | --- | --- |
| M1 Precedence table missing rows | Closed (superseded) | Table deleted. The deltas are in the refreshed spec: CAP-1, CAP-5, CAP-6, CAP-8 and CAP-16 all match. |
| L3 "Story 1 spike scope" row | Closed | Row deleted. Deferred owners match `stories.yaml`. |
| M8 freeze scope and orphans | Partly closed | The workflow orphans (`commitlint-caller.yml`, `candidate-policy.yml`, `build-release.yml`, `domain-*.md`) are closed by the end state. **Still open, not re-scored:** the freeze wording covers composites that frozen workflows reference, but not composites that modules call directly. Today's grep: `Github/initialize-build@main` ×21, `Github/initialize-dotnet@main` ×18, plus SHA pins of `prepare-domain-release`, `dapr-init`, `verify`, `create-release` and `prepare-module-build`. The AD-20 rewrite kept the narrow wording. |
| M15 Builds/CiCd preconditions | Partly closed, new gap | The preconditions are listed (AD-19, AD-21), but now that ADs name conditions, they say nothing about *when* (M6). |
| M9 hook secrets | Worse | "arrive at story 20" became "arrive later" (L4). |
| L2 map vs Binds | Worse | AD-20 now binds CAP-1 and CAP-15, but neither map row lists AD-20 (L7). |
| H1 Builds' own payload | Partly addressed | The interim release keeps G-4 publishing. The end-state fate of `Tools/*g4*` and the root `package.json` `release` block now depends on M2. |

## Rubric scorecard

| # | Criterion | Result |
| --- | --- | --- |
| 1 | Fixes the real divergence points for the 27 stories | Mostly. New open points: H1 (stories 2/4/6 vs the schema), H2 (stories 2/3/5 vs the freeze), M3 (schema shape), M4 (stories 3/8 outcome format). |
| 2 | Every Rule is enforceable and prevents its divergence | AD-3 is unsatisfiable as written (H1). AD-20's freeze blocks AD-19's rename (H2). AD-20's "Prevents: commitlint running twice" does not hold inside `builds-ci.yml` (L5). |
| 3 | Nothing under Deferred lets units diverge | Holds, except the composite-name owners (L8). |
| 4 | Ratifies the brownfield code | The schema file naming and the `schema` const are ratified correctly. The `$id` host and camelCase are a plurality, not the existing convention (L2). The rename breaks 4 brownfield tests (H2). |
| 5 | Covers CAP-1..16 | All mapped. CAP-15 ("no Builds test asserts workflow text") has no transition rule (H2). |
| 6 | Every owned dimension is decided, deferred or open, including operations | Gaps: end state of `Github/` and `Tools/` (M2); timing of the Builds preconditions (M6); the outcome artifact as an interface (M4). |
| 7 | Internal consistency after the update | No leftover `format`, `builds_tag`, hyphenated schema names or story numbers in ADs. Remaining issues: the AD-20 title says "caller" while the body says "module" (M5); the AD-4 reader list differs from "every schema reader" (L1); "later" in AD-14 (L4). |

---

## Critical

None.

---

## High

### H1: AD-3's setup-file validation contradicts the new required `schema`, and the required key set of `hexalith.ci.v1` is undecided
**Location:**
- AD-3, line 106: "A setup file is `hexalith-ci.json` without `schema` and `buildsTag` … validated against Builds' `schemas/hexalith.ci.v1.json` … unknown keys fail";
- Conventions "Schemas", line 432: "every document carries the required `schema`";
- AD-19, line 385: Builds' hand-written file "in the same schema";
- AD-9 fallback, line 213.

**Evidence:**
- **The setup file cannot pass.** Under the ratified convention, `hexalith.ci.v1.json` has `required: ["schema", …]` with a `const`. Every brownfield schema that has a root `schema` property is built this way: 14 of 16, all draft 2020-12 with `additionalProperties: false`. A setup file has no `schema`, so a literal AD-3 check fails on every one of the 17 files. Story 2 writes the schema and story 4 validates against it, and each must improvise a workaround:
  - inject the two keys before validating;
  - add a `$defs/setup` sub-schema;
  - make the keys optional, which breaks the convention.

  Each choice puts the knowledge in a different repo. Any later fix is a Builds major (AD-4, AD-10).
- **`buildsTag` has no answer for Builds itself.** If `buildsTag` is required, Builds' own hand-written `.github/hexalith-ci.json` (AD-19) must carry a Builds tag that means nothing for a repo that calls `./.github/workflows/ci.yml` locally. If the AD-9 fallback ever fires there, it checks out that stale tag and Builds' self-test tests old code. Adversary pass 2 raised this for `builds_tag` (H6, L6, L9). Today's change made the requirement explicit for `schema` and left `buildsTag` undecided.

**Fix:**
- **AD-3:** "Validate checks the rendered `hexalith-ci.json`, which is the setup file plus the injected `schema` and `buildsTag`, against the schema. It never checks the raw setup file."
- **Schemas row or AD-1:** "`schema` is required. `buildsTag` is optional in the schema, and the guard, restore and `check.py` require it in modules. Builds' own file omits it."
- **AD-9:** "Under `module-root`, the fallback uses `github.workflow_sha`, never `buildsTag`."

### H2: The rename breaks legacy tests inside frozen composites, and `builds-ci.yml` has no interim, so Builds' green check stalls
**Location:**
- AD-20, line 397: "every composite, action and script those workflows reference, stays unchanged";
- AD-20, lines 400–401: the rename and the deletion of `commitlint-caller.yml`;
- AD-19, lines 386–387: `builds-ci.yml` is described only in its end state, and the interim release's green check points at it;
- CAP-15: "No Builds test asserts workflow text";
- `pipeline-stages.md`: "Tests that assert workflow text are dropped".

**Evidence:** These tests read the Builds-only workflows by file name and assert their text:

| Test | Reads | Frozen? |
| --- | --- | --- |
| `Github/prepare-module-build/tests/test_prepare_module_build.py:352` | `build-release.yml`, `ci.yml` | yes (composite referenced by `domain-ci*.yml`) |
| `Github/publish-containers/tests/test_publish_script_contract.py:15,507` | `build-release.yml`, `ci.yml` | yes (referenced by `domain-release.yml`) |
| `Github/commitlint/tests/test_commitlint_workflow.py:11,111,115` | `build-release.yml`, `ci.yml`, `commitlint-caller.yml` | in a `Github/` legacy directory |
| `Tools/test-self-ci.py:15,19` | `build-release.yml`, `ci.yml` | no |

What the rename does:
- **The renamed CI goes red.** At the rename, `ci.yml` becomes `builds-ci.yml` and later turns into the reusable workflow. The renamed CI is today's `ci.yml`, which runs these tests (lines 290–342), so it goes red at once.
- **The interim release stalls.** The interim `builds-release.yml` needs a green `builds-ci.yml`, and so does the hand-dispatched bootstrap (AD-16, AD-19). Every module story waits on `builds-version`.
- **Every way out breaks a rule:**
  - editing or deleting the frozen tests breaks AD-20's "unchanged";
  - leaving them out of `builds-ci.yml` is not stated anywhere, because AD-19 says it runs "the Python tests";
  - keeping them breaks CAP-15.
- **Deleting `commitlint-caller.yml` breaks another test.** `test_commitlint_workflow.py` asserts that file's text, so the deletion breaks it in the same way.
- **The interim has no exit.** Today's `ci.yml` also calls the frozen `codeql.yml` and `dependency-review.yml`, and runs the G-4 qualification jobs that the interim release consumes. No condition says when those leave `builds-ci.yml`. The final legacy deletion would break `builds-ci.yml` if they are still there.

**Fix:** Add to AD-20, beside the rename bullet:
- "`builds-ci.yml` first exists as the renamed legacy `ci.yml`. In that change, every test that reads a Builds-only workflow file by name is deleted, frozen directories included. The freeze protects what callers execute, not tests."
- "The legacy jobs (G-4 qualification, catalog validators, the `codeql.yml` and `dependency-review.yml` calls) leave `builds-ci.yml` in the change that rewrites `builds-release.yml`, their only consumer. After that, `builds-ci.yml` has the AD-19 shape."

---

## Medium

### M1: The Precedence rule no longer resolves conflicts with `stories.yaml`, and three are live
**Location:** Precedence, line 28; memlog "(direction) Upstream after close: offer bmad-spec edits".

**Evidence:**
- **What the old rule covered.** The deleted text said the spine wins over "SPEC-cicd, its companions, or `stories.yaml`".
- **What the new rule covers.** The new text names only "a conflict between the spec and the spine". It gives `stories.yaml` "who and in what order", but says nothing when a story's text states a *how*.
- **The live conflicts.** The upstream edits are only "offered", so `stories.yaml` disagrees with the spine today:
  - story 6: "checks that the Builds pointer equals `builds_tag`";
  - story 27: its deletion list omits `candidate-policy.yml`, `commitlint-caller.yml`, the `domain-*.md` docs and four `Github/` directories (M2);
  - story 5: says nothing about deleting `commitlint-caller.yml`, which AD-20 ties to the guard's commitlint.

  A story agent that reads only its story builds the wrong thing.
- **Ordering.** The ADs now carry ordering conditions ("before the reusable `ci.yml` lands", "before `nightly.yml` dispatches it"), but the rule does not say that the story order must satisfy them.

**Fix:**
- Extend the rule: "Where a story's text states how something is built and conflicts with an AD, the AD wins. `stories.yaml` is authoritative only for ownership and order, and its order must satisfy the ordering conditions in the ADs. Story numbers appear only under Deferred, as owners."
- Apply the three `stories.yaml` edits now rather than offering them.

### M2: AD-20's end state covers only `.github/workflows/`, although AD-20 binds `Github/` and `Tools/`
**Location:**
- AD-20, Binds (line 394): "Builds `.github/workflows/`, `Github/`, `Tools/`";
- line 402: "removes everything else outside the end state";
- line 403: the end state lists workflows only;
- `module-inventory.md` lines 32–33.

**Evidence:**
- **`Github/` has no end state.** It holds 17 directories:
  - The spec marks 5 legacy actions plus `prepare-domain-release` for deletion.
  - It keeps 7 composites "frozen while legacy callers remain" and gives no final fate: `initialize-build`, `initialize-dotnet`, `dapr-init`, `prepare-module-build`, `create-release`, `publish-containers`, `governed-provenance`.
  - It never mentions 4: `commitlint` (tests only), `run-module-integration`, `split-publication` and `scripts`.
- **`Tools/` is a mix.** It holds 68 entries: G-4 release tooling (`*g4*`), domain-workflow tests, and the `Props/` catalog validators (`validate-*.ps1`). The validators guard product build data, which AD-2 excludes from the module-agnostic rule.
- **The root release config has no fate.** That is the `package.json` `release` block with its `@semantic-release/exec` hooks. Once `builds-release.yml` is rewritten, it is dead.
- **The result.** "Everything else outside the end state" has nothing to compare against for these paths. That is the same orphan pattern U3 fixed for workflows. Story 27 decides alone, and it could delete the catalog validators or keep dead G-4 tooling.

**Fix:** Extend the end state:
- "`Github/` holds only the composites the new pipeline references (`prepare`, `publish`, guard, restore, `lib/`, …)."
- "`Tools/` holds only scripts that `builds-ci.yml` or `builds-release.yml` invoke."
- "The root `package.json` keeps only the commitlint and release-analysis dependencies that AD-4 places in Builds."
- Decide the `Props/` catalog validators: port them to Python tests in `builds-ci.yml` (AD-11), or drop them. Recommended: port, because a catalog error breaks every module's package-mode build.

### M3: "JSON keys in camelCase" collides with data-keyed maps in `hexalith-ci.json` and the perimeter
**Location:** Conventions "Schemas" (line 432); AD-13 (`tests.exclude`: "project → enabled hook or job"); AD-3 and AD-12 (`hooks`, `jobs` by kebab-case name); Conventions "Identifiers" (line 431).

**Evidence:**
- **The natural shapes break the rule.** The natural JSON shape for `tests.exclude` is an object keyed by repo-relative `.csproj` path. For `jobs` and `hooks`, it is objects keyed by kebab-case names (`after-unit-tests`, `<job-name>`). Read literally, "JSON keys in camelCase" forbids all three.
- **The perimeter has the same problem.** Its `json-superset` and `absent-json` entries carry keys that belong to other tools (`permissions.deny`, `@commitlint/*`).
- **Two readings.** Story 2 (schema) may follow the rule and use arrays of objects, while stories 4, 5 and 6 and the 17 setup files assume maps. Or the reverse. The schema is public API, so a later fix is a major.

**Fix:** In the Schemas row: "Property names the schema defines are camelCase. Keys that are data (project paths, hook and job names, foreign JSON keys) keep their own identifier convention." Also fix the shapes: `tests.exclude` is an object of path → hook-or-job name; `hooks` is an array of hook names; `jobs` is an object of job name → `{ "os": … }`.

### M4: The `hexalith-release-outcome` artifact is a Builds→CiCd interface with no format and no public-API status
**Location:** AD-17 "Outcome" (line 342); AD-18 "Wait and report" (line 351); AD-10 "Public API" (lines 220–225); Conventions "Schemas" ("every document").

**Evidence:**
- **The values are fixed, the format is not.** The artifact name and its five values are fixed, but nothing fixes the file inside: its name, JSON or text, and fields such as the version and SHA.
- **It crosses Builds versions.** `nightly.py` (CiCd, story 8) reads artifacts produced on the same night by two Builds versions:
  - Builds' own run, from `builds-release.yml` at Builds `main`;
  - module runs, at `builds-version`.
- **A minor can break nightly.** AD-10's public API lists `workflow_call` outputs but not this artifact, so a Builds minor can change it.
- **The convention makes it ambiguous.** Today's "every document carries the required `schema`" raises a question nobody has answered: is this artifact a schema'd document?

**Fix:**
- In AD-17: "The artifact holds `outcome.json`, schema `hexalith.release-outcome.v1`: `schema`, `outcome`, `version` (optional) and `sha`."
- Add the schema to AD-10's public API.
- In AD-18: "A run without a readable outcome counts as `failed`."

### M5: AD-20's new conditions are not yet checkable predicates
**Location:** AD-20 title (line 392: "until the last **caller** has moved"); lines 397 and 402 ("until/after the last **module** has moved"); line 401 ("goes once the guard's commitlint runs in `builds-ci.yml`").

**Evidence:**
- **"Moved" has no test.** Story 27's agent needs a test for it. AD-21 defines "adopted" (step 3) and "done" (step 4), and AD-20 uses neither.
- **"Caller" and "module" differ.** "Caller" would include any of the about 43 unmanaged Hexalith repos. Today's org code search found none calling Builds, but the code-search index is partial. A file that a module SHA-pins is not broken by deletion from `main`, so only `@main` references matter.
- **`commitlint-caller.yml` has a hidden dependency.** Its condition omits that Builds' `Protect main` ruleset requires the `commitlint / commitlint` check, which comes from this file (memlog 2026-11-08, adversary pass 2). Deleting the file before the ruleset cut means no Builds PR can merge.
- **"Goes once" reads as "any time after".** The parent bullet says "in the change that ships its replacement". "Once" allows a window where commitlint runs twice, which is the outcome AD-20's Prevents line rules out.

**Fix:**
- Title: "until the last module has moved".
- Define it: "Moved = every `setup/*.yml` module is adopted (AD-21 step 3), and a grep of every managed module's `main` finds no `Hexalith/Hexalith.Builds/…@main`."
- `commitlint-caller.yml` "is deleted in the change that makes the guard's commitlint run in `builds-ci.yml`. That change requires that Builds' ruleset no longer lists `commitlint / commitlint`."

### M6: AD-19's preconditions have no condition, and two of them must precede the rename
**Location:** AD-19 "Preconditions" (line 388); AD-7 (the CiCd-agent token has no Pull requests write); AD-20 rename (line 400).

**Evidence:** With story numbers removed, the AD carries no "before X" for its preconditions. Three are time-critical:
- **The nuget.org policy for `builds-release.yml`.** The interim keeps `NuGet/login` in a job whose `job_workflow_ref` becomes `builds-release.yml` at the rename. Without the new policy, Builds' only publishing path breaks at the rename. The memlog verified that a no-environment policy accepts the interim `production` job, so the precondition is sufficient, but only if it comes first.
- **The ruleset cut.** `Protect main` requires a PR and 3 status checks, and the CiCd-agent token cannot open PRs (AD-7). No agent change to Builds can land before the cut, the rename included.
- **The kill switch.** `HEXALITH_RELEASE_PUBLISH_ENABLED` is needed before `nightly.yml` dispatches the rewritten release. AD-19 says only "is set", while AD-21 requires "exactly `true` or `false`".

Story 1 currently orders these correctly, but under M1 the spine, not the story, must state the invariant.

**Fix:** In AD-19: "Before the first CiCd-agent change to Builds (the rename): the ruleset is cut as in AD-21, and the nuget.org policy names `builds-release.yml` with no environment. Before `nightly.yml` dispatches Builds: the App is installed, and `HEXALITH_RELEASE_PUBLISH_ENABLED` is exactly `true` or `false`."

---

## Low

- **L1. AD-4's reader list is narrower than the Conventions row, and one promised message is missing.**
  - AD-4 (line 130) names "guard, restore, delivery, `check.py`".
  - The Fixed messages row says "every schema reader". AD-1 adds Builds' CI and release, including `prepare` on Windows, as readers of `hexalith-ci.json`.
  - AD-4 also promises a fixed message for an unknown entry kind, but Conventions defines none.
  - Fix: "The first reader in each path checks `schema`: the guard in CI, the drift check in the release, `check.py` locally, and the perimeter library in delivery." Add "unsupported perimeter entry kind `<kind>`" to Fixed messages.
- **L2. The Schemas row says "existing convention" for two things that are only a plurality, and omits two things that are universal.**
  - `$id` hosts today: `hexalith.com/schemas` ×8, `hexalith.dev/schemas` ×7, `schemas.hexalith.com` ×1.
  - `hexalith.readiness-evidence.v1.json` uses snake_case (`generated_by`, `source_of_truth`), and `platform-identity` uses `schemaVersion`.
  - All 16 use draft 2020-12, and 15 close the root with `additionalProperties: false`, which AD-3's "unknown keys fail" needs.
  - Fix: "New schemas use…". Add "draft 2020-12; objects closed with `additionalProperties: false`".
- **L3. Schema versioning is stated one way only, and the render's source for `schema` is unstated.**
  - AD-4 says a new schema version is a major. It does not say the converse: additive changes stay in `v<N>`, and removals or meaning changes require `v<N+1>`.
  - AD-3 hard-codes the file name `hexalith.ci.v1.json`, and AD-10 line 230 says a major is adopted by changing `builds-version` and the templates "together". A `v2` would also change `setup/`, and would change render.py if the `schema` value were hard-coded there.
  - Fix: "The render takes `schema` and the schema file from Builds at `builds-version` (the `const`). A major-adoption commit changes `builds-version`, `templates/` and `setup/` together."
- **L4. AD-14 (line 291): "Hook secrets … arrive later" is not a condition.** It replaced "at story 20" with no trigger. Fix: "when the first hook that needs a secret is enabled (Deferred)".
- **L5. AD-19 says Builds is "never … guarded", but AD-20's condition depends on the guard running in `builds-ci.yml`.**
  - `builds-ci.yml` calls the reusable `ci.yml` twice, for Builds and for `Samples/`. Both calls run stage 1, so commitlint runs twice over the same Builds commits, against AD-20's "Prevents: commitlint running twice".
  - Fix: "Builds is never guarded against `delivered`. Its self-test runs the guard on the fixture perimeter. Commitlint runs only in the Builds-itself call."
- **L6. "Before `nightly.yml` dispatches it" is not self-enforcing.**
  - If the order slips, nightly dispatches the interim release. That release runs under Builds' `production` environment, which has required reviewers (adversary pass 2, live check), so it waits for approval.
  - AD-18 polls "until all runs complete" with no bound. The nightly job dies at the 6-hour job limit, and there is no bump that night.
  - Fix: nightly counts a Builds run without a readable outcome as `failed` (see M4), and polls for at most a fixed time, for example 5 hours.
- **L7. The map and the seed lag the new AD-20.**
  - The CAP-1 and CAP-15 rows omit AD-20, which now binds both. This is pass-2 L2, worse.
  - The Structural Seed's Builds `.github/workflows/` line omits `ci-cd-standards.md`, which is in the end state.
  - Fix: add AD-20 to both rows and the file to the seed.
- **L8. The Deferred "Builds composite names" owners (line 559) predate the refreshed stories.**
  - The refreshed `stories.yaml` gives the guard, restore and the release drift check to story 5, and the perimeter library to story 4. Deferred says "stories 2 and 3" and treats the guard and restore names as fixed, but they appear only in a seed comment.
  - Story 2's stage-1 call and story 5's composite must agree on the name.
  - Fix: name `guard`, `restore` and `drift-check` (if it is a composite) in the Conventions "Workflow files" row, and make the owners "stories 2, 3 and 5".

---

## What holds and should be kept

- **U1 Precedence.** The what/how/who split is the right shape. It only needs the stories clause (M1).
- **U2 Conditions instead of story numbers.** "Before the reusable `ci.yml` lands" is a git-history check. AD-9 and AD-21 read cleanly without numbers.
- **U3 End state for workflows, and deletion with the replacement.** It closes pass-2 M8's orphans and ratifies `ci-cd-standards.md` living in `.github/workflows/`.
- **U4 Schema convention.** Choosing it before it becomes public API avoids a later major. The file naming and the `schema` const match the brownfield. The unsupported-schema message gives every reader one failure text.
- **The AD-19 interim.** It keeps Builds' only publishing path alive across the rename. The memlog's nuget.org check shows that a no-environment policy covers it.
