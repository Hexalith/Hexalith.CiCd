# Review (pass 3): verification of the 2026-11-08 spine update

- **Spine:** `../ARCHITECTURE-SPINE.md` (updated 2026-11-08; `git diff` = Precedence table removed, AD-19 interim `builds-release.yml`, AD-20 end state and deletion timing, schema convention U4, `builds_tag` → `buildsTag`)
- **Decision log:** `../.memlog.md` lines 84–95 (2026-11-08 reality checks and U1–U4)
- **Prior passes:** `review-verification.md`, `review-verification-pass2.md`. Items they confirmed are not re-checked unless they may have changed.
- **Lens:** is each claim the update relies on confirmed against the web, the existing project or upstream source, or only asserted?
- **Date:** 2026-11-08
- **Method:**
  - `git fetch` + `git ls-remote` of Builds and all 17 modules. Every local checkout under `references/` equals its remote `main` today, so all `git grep origin/main` evidence is live.
  - `uvx zizmor@1.32.0 --offline` with the spine's zizmor policy, and actionlint 1.7.12, run on Builds' real `.github/workflows/`.
  - NuGetGallery source and tests at `main` (`GitHubTokenPolicyValidator.cs` last changed 2026-10-01, commit `63b66c9828`), and the Microsoft Learn Trusted Publishing page.
  - `gh api`: Builds rulesets, workflow runs and job steps, branches, immutable releases; GitHub releases and tags for every Stack row; npm, PyPI, nuget.org flat container, .NET release metadata, Node release schedule, runner-images Ubuntu 26.04 README; public DNS (`dns.google`) for the `$id` hosts.

## Verdict

The four claims in focus mostly hold:
- **Schema convention.** Builds' convention is real, the newest schemas follow it, and it lives in shipped product tooling, so it survives the legacy deletion.
- **Names are free.** Nothing reads `hexalith-ci.json` or `buildsTag`.
- **Callers.** Neither `candidate-policy.yml` nor `commitlint-caller.yml` has a caller.
- **nuget.org environment.** Confirmed by the validator's source and its unit tests.
- **Stack.** Current, apart from one patch release published today.

But the update added one claim that the code contradicts. AD-19 says the renamed `builds-release.yml` keeps "its publishing unchanged". In fact the legacy publish path fails closed unless the run's workflow file is `build-release.yml`, and its CI proof requires `ci.yml`.

Three more gaps are about running new code beside the frozen legacy in the same folder:
- zizmor fails on the frozen files.
- One workflow is unaccounted for in AD-20.
- Setup-file validation conflicts with the required `schema` property.

**Counts:** 0 critical, 1 high, 3 medium, 6 low.

---

## Critical

None.

---

## High

### H1 — AD-19 / AD-20: "renamed legacy `build-release.yml` … its publishing unchanged" is WRONG; the legacy release checks its own workflow file name

- **Spine claim (new today):**
  - AD-19: "`builds-release.yml` … first exists as the renamed legacy `build-release.yml`, with its green-CI check pointed at `builds-ci.yml` and its publishing unchanged."
  - AD-20: "`ci.yml` and `build-release.yml` become `builds-ci.yml` and `builds-release.yml` in one change, before the reusable `ci.yml` lands."
  - Backed by `stories.yaml` story 2 ("minimally adapted builds-release.yml that checks builds-ci.yml") and story 1 ("Keep Builds' NuGet publishing working across the rename").
- **Evidence (Builds `origin/main` `3c809618`):**
  - The publish path is semantic-release's exec plugin (`package.json:27-29`). It runs `Tools/prepare-g4-tool-release.ps1`, `verify-g4-tool-release.ps1` and `publish-g4-tool-packages.ps1`. All three call `Assert-CurrentReleaseSource` (`prepare:16`, `verify:52`, `publish:559`).
  - `Tools/G4PackageQualification.functions.ps1:100` throws unless `GITHUB_WORKFLOW_REF -ceq "Hexalith/Hexalith.Builds/.github/workflows/build-release.yml@$GITHUB_REF"`.
  - `:45` and `:57` throw unless the source CI run's `path` is `.github/workflows/ci.yml`.
  - `Tools/verify-g4-release-source.sh:29,45` reads `actions/workflows/ci.yml/runs` and requires `.path == ".github/workflows/ci.yml"`. This is the green-CI check the spine does mention.
  - `Tools/archive-g4-qualification-evidence.py:61-67` raises "Complete matching producer run/workflow identity is required" unless the workflow ref names `build-release.yml` (release) or `ci.yml` (CI). It runs in both workflows (`if: always()` in the release job).
  - **Tests.** About 20 files assert the text of Builds' own `ci.yml` or `build-release.yml` by path:
    - `Tools/test-self-ci.py:15,20`, `Tools/test-g4-release-contract.ps1:10`, `Tools/test-archive-g4-qualification-evidence.py`;
    - `Tools/test-domain-workflow-test-platforms.ps1:14,1019`, `Tools/test-central-package-version-validator.ps1:8`, `Tools/test-dapr-package-version-validator.ps1:8`;
    - `Tools/test-package-version-audit-*.ps1`, `Tools/test-publish-g4-tool-packages.ps1:760`;
    - `Github/commitlint/tests/test_commitlint_workflow.py:10-11`, which also reads `commitlint-caller.yml`;
    - `Github/prepare-module-build/tests/test_prepare_module_build.py:339,352`;
    - `Github/publish-containers/tests/test_publish_script_contract.py:15,507`.

    `Github/prepare-module-build` and `Github/publish-containers` are referenced by `domain-ci*.yml` and `domain-release.yml`, so AD-20 freezes them.
  - **Live baseline.** Builds' `build-release.yml` publishes today: run 42438005017 (2026-11-08, `workflow_dispatch`, `environment: production`), step "Authenticate to NuGet.org with Trusted Publishing" = success.
- **Consequence:**
  - A rename that changes only the green check makes the first `builds-release.yml` run fail closed in semantic-release's verify and prepare steps. Builds can't release again until someone edits the G4 scripts.
  - The rename also turns builds-ci red wherever it still runs the legacy suite.
  - The suite breaks again when the reusable `ci.yml` lands under the old name: tests that read `.github/workflows/ci.yml` as "Builds' own CI" will read the reusable workflow instead.
- **Fix:**
  - AD-19 replaces "its publishing unchanged" with: "its publishing logic unchanged except the workflow identities. The same change repoints every hard-coded `build-release.yml` / `ci.yml` identity in Builds-only release tooling to `builds-release.yml` / `builds-ci.yml`." List the three files in story 2:
    - `G4PackageQualification.functions.ps1`
    - `verify-g4-release-source.sh`
    - `archive-g4-qualification-evidence.py`

    All three are Builds-only (grep: only `build-release.yml`, Builds' `ci.yml` and Builds' `package.json` reach them), so the freeze doesn't block the edit.
  - AD-20 adds: "The freeze covers what module-reachable code does, not tests that assert Builds' own workflow files. The rename change repoints or retires those tests, including tests inside frozen composite folders. `builds-ci.yml` states which legacy test suites it still runs during the freeze."
  - Story 2 done-check: one real (or prerelease-branch) `builds-release.yml` run passes `Assert-CurrentReleaseSource` before story 3.

---

## Medium

### M1 — Conventions / AD-19: builds-ci's zizmor fails on the frozen legacy workflows (measured), and AD-20 forbids fixing them

- **Spine claim:**
  - `builds-ci.yml` "runs actionlint, zizmor".
  - Convention: "zizmor runs with a committed config (ref-pin `Hexalith/*`, hash-pin all others, `self-repository` audit off, never `--fix`)".
  - AD-20: `codeql.yml`, `commitlint.yml`, `dependency-review.yml` and `domain-ci*.yml` stay unchanged until the last module moves.
  - Pass 2 confirmed this config only on sample workflows, never on Builds' real folder.
- **Experiment:** `uvx zizmor@1.32.0 --offline` with exactly that policy on Builds `.github/workflows/` gives exit 14 (high).

  | File | Findings |
  | --- | --- |
  | `codeql.yml` | 3 `unpinned-uses` High (`actions/checkout@v7.0.1`, `github/codeql-action/*@v4.39.1`), 1 `artipacked` Low |
  | `commitlint.yml` | 2 `unpinned-uses` High, 1 `artipacked` Low |
  | `dependency-review.yml` | 2 `unpinned-uses` High, 1 `artipacked` Low |
  | `domain-ci.yml` / `domain-ci-v2.yml` | 3 / 1 `artipacked` Medium |
  | `ci.yml`, `build-release.yml` (renamed anyway) | 6 + 2 `cache-poisoning`; 2 `unpinned-uses` |

  The frozen files are called by 10 modules at `@main` (and more at SHAs), so they can't be pinned. An agent's natural fix (hand-pinning them) would break AD-20.
- **actionlint 1.7.12** exits 0 on the whole folder, so it needs no change.
- **Fix (verified):** add per-rule `ignore:` entries for the frozen files to Builds' committed zizmor config, and remove them in the legacy deletion:
  - `unpinned-uses`: `codeql.yml`, `commitlint.yml`, `dependency-review.yml`;
  - `artipacked`: the same three plus `domain-ci.yml` and `domain-ci-v2.yml`.

  Re-run result: "No findings to report … (14 ignored, 24 suppressed)", exit 0, over all frozen and Builds-only legacy files. State this in the convention row or in AD-20.

### M2 — AD-20: `eventstore-maintenance-publisher.yml` is in Builds' workflows folder but not in AD-20 or the 2026-11-08 reality check

- **Claim:**
  - The memlog (lines 86, 88) enumerates Builds `.github/workflows/` as of 2026-11-08 without this file.
  - AD-20 names only `ci.yml`, `build-release.yml` and `commitlint-caller.yml` as Builds-only deletions, plus `candidate-policy.yml` and `domain-*.md` in the final sweep.
- **Evidence:**
  - `git ls-tree origin/main .github/workflows/` lists 15 entries, including `eventstore-maintenance-publisher.yml` (added 2026-11-01, last touched 2026-11-05 by Dependabot `db31a60c`).
  - It triggers on push to `fix/eventstore-maintenance-publication`, a branch that no longer exists (`gh api …/branches/…` → 404), and on `workflow_dispatch`. Its last run was 2026-11-01.
  - It names a module, which conflicts with AD-2's "Builds' workflows … contain no module names".
  - Its test step runs `Github/publish-containers/tests`, which read `build-release.yml` (H1), so the rename breaks it too.
- **Coverage:** AD-20's catch-all ("everything else outside the end state") does sweep it at the end, so nothing is orphaned forever. But it is Builds-only, has no caller and needs no replacement. Under AD-20's own rule it should not wait for the last module.
- **Fix:**
  - Name it in AD-20 as a Builds-only workflow deleted in the rename change.
  - Correct memlog lines 86 and 88: 15 files, not 14.
  - Optionally have the global or Builds lint assert that the folder equals an allow-list, so the next unlisted file is caught.

### M3 — AD-3 + Schemas convention: the setup file can't validate against a schema whose `schema` property is required

- **Spine claim (new today):**
  - Conventions: "every document carries the required `schema: "hexalith.<name>.v<N>"`".
  - AD-3: "A setup file is `hexalith-ci.json` without `schema` and `buildsTag`, which the render adds. It is validated against Builds' `schemas/hexalith.ci.v1.json` …, and unknown keys fail."
- **Reality check:** the convention was taken from Builds. 14 of its 16 schemas list `schema` in top-level `required`. Validating a document that lacks a required property fails in any draft 2020-12 validator, including jsonschema 4.26.0 from the Stack. As written, every setup file fails the global checks.
- **Fix:** say which document is validated. Pick one:
  - **(a)** CiCd validates the rendered `.github/hexalith-ci.json`, which has `schema` and `buildsTag` injected. A setup file then fails only through its rendered output.
  - **(b)** CiCd validates the setup file against the schema with `required` minus `schema` and `buildsTag`.

  (a) is simpler and keeps one schema.

---

## Low

- **L1 — Schema convention: CONFIRMED and durable. The memlog counts are slightly off.**
  - **Durable.** At least 8 schemas are embedded in shipped product, so the convention survives the AD-20 legacy deletion. That deletion binds `.github/workflows/`, `Github/` and `Tools/`, not `schemas/` or `src/`.
    - `Hexalith.Builds.Tooling.csproj:29-36` embeds `check-*`, `release-records`, `module-run-evidence`, `module-manifest.v2`, `test-environment` and `test-result`.
    - That code ships in `Hexalith.Builds.Module.Cli` (`hexalith-module`) and `Hexalith.Builds.Evidence.Cli`, both on nuget.org at 4.44.13.
    - ChatBot, Conversations, Parties, Platform and EventStore consume `hexalith-module` via `.config/dotnet-tools.json`.
    - Only `g6-current-evidence`, `runtime-toolchain-evidence.v1/.v2` and `platform-identity` (no reader at all) are legacy-only.
  - **Counts.** The memlog says 15/16 carry the `schema` const. The real count is **14/16**:
    - `platform-identity.v1` uses integer `schemaVersion: 1`;
    - `release-records.v1` uses per-record URL consts (`https://schemas.hexalith.com/platform/<kind>.v1`) under `oneOf`.

    camelCase holds in 15/16; `readiness-evidence.v1` is snake_case (`generated_by`, `markdown_view`, …).
  - **`$id` hosts.** The 8 / 7 / 1 split is confirmed. Every schema added since 2026-10-02 uses `hexalith.com`, except `release-records`.
  - **Domains.** `hexalith.com` is registered (public NS `ui-dns.*`). `hexalith.dev` is **NXDOMAIN** (`dns.google` Status 3), so 7 existing `$id`s use a domain the org does not hold. That supports the choice of `hexalith.com`.
  - **Fix:** correct memlog line 89 and record the domain evidence beside U4.

- **L2 — Name collision: CONFIRMED none.**
  - Across Builds and all 17 modules, no code or workflow reads `hexalith-ci.json`, `hexalith.ci.v1`, `hexalith.perimeter`, `buildsTag` or `builds_tag`.
  - The only hits are `builds-tag` in evidence and validation JSON (148) plus one legacy tooling test (`Hexalith.Conversations/tests/tooling/test_epic16_published_artifact_qualification.py`), and `builds_tag` in one Platform evidence file and one Builds BMAD doc.
  - Upstream, `stories.yaml:68` (story 6) still says `builds_tag`, as memlog line 95 already notes.

- **L3 — nuget.org no-environment policy: CONFIRMED by source, but the memlog cites the wrong part of the doc.**
  - **Source.** `GitHubTokenPolicyValidator.cs` reads the `environment` claim only inside `if (!string.IsNullOrWhiteSpace(criteria.Environment))`.
  - **Tests.** `GitHubTokenPolicyValidatorFacts.cs` `ReturnsSuccessForValidPermanentPolicy` is parameterized with `PermanentPolicyCriteriaNoEnvironment`. Its default token carries `"environment": "production"`, and the result is `Success`. So a no-environment `builds-release.yml` policy accepts the interim job that still runs under `environment: production`.
  - **Doc citation.** The Learn sentence "Validated only if set in the policy" is in the **GitLab** "Required token claims" table. The GitHub section says only: "Enter environment if … you want to restrict this policy to that environment. Leave this empty if you do not use GitHub Actions environments."
  - **Caveats.**
    - The validator also checks `event_name` against a ban list that lives in deployment config (`BannedGitHubActionsEvents`, default empty; not public).
    - `workflow_dispatch` is proven live by run 42438005017.
    - Deployed nuget.org could lag `main`. The story-1 policy plus the first renamed release is the live test.
  - **Fix:** re-cite memlog line 90 to the validator source, its test and the live run.

- **L4 — `commitlint-caller.yml` deletion depends on the ruleset cut.**
  - **CONFIRMED:** no module can call it. It has no `workflow_call` trigger, and no module references it.
  - Builds ruleset 19196298 ("Protect main") currently requires `commitlint / commitlint`, a check only this workflow produces, plus `Codacy Static Code Analysis` and `SonarCloud Code Analysis`, with `strict_required_status_checks_policy: true`.
  - Deleting it before the AD-19 cut blocks every Builds PR.
  - `Github/commitlint/tests/test_commitlint_workflow.py:10` reads the file, so delete or repoint that test in the same change.
  - **Fix:** in AD-20 write "goes once the guard's commitlint runs in `builds-ci.yml` and the AD-19 ruleset cut is done."

- **L5 — `candidate-policy.yml`: no caller CONFIRMED; it has a product dependent.**
  - **No caller.** It is `workflow_call` only. No module workflow and no Builds workflow `uses:` it.
  - **Tenants.** It does run `Github/governed-provenance` from a Builds checkout, but pinned to `ff3b7628…` (`release.yml:21,311,432`), so deletion on `main` can't break it.
  - **Product dependent.** The shipped `hexalith-module` CLI has a candidate-gate validator enrolled against a `candidate-policy.yml` WorkflowRef at a pinned SHA:
    - `src/libraries/Hexalith.Builds.Tooling/CandidatePolicy/*`;
    - `ModuleCommandApplication.cs:111-117`, diagnostic `HXP301`.

    Deleting the file breaks no pinned enrollment, but it leaves a product command whose issuer no longer exists at later SHAs.
  - **Fix:** in the legacy-deletion story, decide deliberately whether to retire that CLI command or keep it, and don't remove it silently.

- **L6 — Stack freshness (2026-11-08).** All rows are current except the notes below.

  | Row | Spine | Latest today | Status |
  | --- | --- | --- | --- |
  | jscpd | 5.4.2 | **5.4.3** (npm and GitHub, 2026-11-08 06:54 UTC) | Newer patch. It adds a `runJscpd()` Node API and leaves detection unchanged. Bump optional. |
  | Node.js | 24 | 24 is **Maintenance LTS since 2026-10-20** (EOL 2028-04-30). 26 is Active LTS since 2026-10-28. | Still fits. The Ubuntu 26.04 image ships Node 24.22.2, and `@commitlint/cli` 21.2.4 needs ≥ 22.12. Note maintenance status. Builds' `Github/create-release` comment "24 is Active LTS" is stale. |
  | `@semantic-release/commit-analyzer` / `release-notes-generator` | 13.0.1 / 14.1.1 | stable unchanged; **14.0.0-beta.4 / 15.0.0-beta.3** in beta. semantic-release 26.0.0-beta.6 needs Node ≥ 26.13. | The pins hold. Recheck the plugin call contract at story 3 if the majors go stable. |
  | uv, setup-uv, setup-node, checkout, setup-dotnet, upload/download-artifact, create-github-app-token, codeql-action, NuGet/login, actionlint, zizmor, Jinja2, PyYAML, jsonschema, @commitlint/cli | as spine | same | current |
  | .NET SDK | 10.0.403 | 10.0.403 (10.0.14, 2026-10-25) | current; next Patch Tuesday 2026-11-10 |
  | Python | ≥ 3.12; 26.04 image 3.14.4 | Ubuntu 26.04 image 20261101.186.1: Python 3.14.4 | confirmed; `ubuntu-latest` → 26.04 rollout still open (runner-images issue) |
  | Dapr | 1.19.1 | runtime v1.19.1, CLI v1.19.1 | current |
  | Runner `$/` | ≥ 2.336.0 | v2.338.2 | satisfied |

---

## Claims checked

| # | Claim relied on today | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Builds file naming `hexalith.<name>.v<N>.json` | CONFIRMED (16/16) | `ls schemas/` |
| 2 | Required `schema` const = file stem | CONFIRMED 14/16 (memlog says 15) | L1 |
| 3 | camelCase keys | CONFIRMED 15/16 | L1 |
| 4 | `$id` host split 8/7/1; `hexalith.com` chosen | CONFIRMED; `hexalith.dev` unregistered | L1 |
| 5 | Convention is product, survives legacy deletion | CONFIRMED | `Hexalith.Builds.Tooling.csproj:29-36`; nuget.org 4.44.13; 5 module tool manifests |
| 6 | Nothing reads `hexalith-ci.json` / `buildsTag` today | CONFIRMED | L2 |
| 7 | AD-20 list of module-called workflows | CONFIRMED exact. Callers: `domain-ci.yml` (11), `domain-ci-v2.yml` (EventStore, Parties), `domain-release.yml` (Agents), `codeql`/`commitlint`/`dependency-review` (10 modules call at least one at `@main`). Direct Builds checkouts and submodule script uses are all SHA- or gitlink-pinned. | `git grep origin/main -- .github` across 17 modules |
| 8 | `commitlint-caller.yml` Builds-only | CONFIRMED | L4 |
| 9 | `candidate-policy.yml` no module caller | CONFIRMED | L5 |
| 10 | Every file in Builds `.github/workflows/` accounted for by AD-20 | Not quite: `eventstore-maintenance-publisher.yml` is caught only by the catch-all | M2 |
| 11 | Renamed `builds-release.yml` publishes unchanged | **WRONG** | H1 |
| 12 | nuget.org no-environment policy accepts an environment job | CONFIRMED (source and test); doc citation is the GitLab table | L3 |
| 13 | zizmor committed config works in Builds during the freeze | **Fails on frozen files**; per-file `ignore` verified | M1 |
| 14 | Stack versions | Current except jscpd 5.4.3 and the Node 24 status note | L6 |

**Still open from pass 2 and unchanged:** Builds immutable releases are `{"enabled":false}`, while `SPEC.md:162` says "its releases are immutable" (pass-2 L2). The `HEXALITH_CICD_APP_ID` vs `client-id` deprecation (pass-2 L3) is also still open.

**Counts:** 0 critical, 1 high, 3 medium, 6 low.
