---
reviewer: confirmation (narrow)
pass: update gate, second amendment
target: ../ARCHITECTURE-SPINE.md (draft, updated 2026-11-08, 21 ADs; working tree, uncommitted)
closes: review-rubric-update.md (U-R*), review-adversary-update.md (U-A*), review-security-update.md (U-X*), review-verification-update.md (U-V*)
date: 2026-11-08
---

# Confirmation review, update gate: Hexalith.CiCd architecture spine

## Verdict

**Does not pass yet. One high finding remains, and the fix is small.**

The second amendment closes every finding in scope. The critical U-A1 / U-V1 mechanism is now correct:
- create mode refuses a draft whose workflows differ from `main`'s;
- `publish` ends `ready` instead of sending a request GitHub would refuse;
- the App publishes the draft before the bump.

The remaining problem is in the order of the nightly jobs (U-C1):
- `wait` is the only job that applies the verdicts, yet it runs before the job those verdicts depend on.
- `publish-ready` runs "after `wait`", and GitHub skips a dependent job when the job it needs fails.

So a `ready` draft is never published on a night when any other run fails. Read literally, it is never published at all. Three medium findings sit where the new `ready` path meets AD-16 and AD-3. Seven low findings are edge cases with one-line fixes.

| Severity | Count | IDs |
| --- | --- | --- |
| Critical | 0 | — |
| High | 1 | U-C1 |
| Medium | 3 | U-C2, U-C3, U-C4 |
| Low | 7 | U-C5 to U-C11 |

`L<n>` refers to `ARCHITECTURE-SPINE.md` as it stands in the working tree.

### Method

- **Read:**
  - the spine, end to end;
  - the four update reviews;
  - the memlog. It has no entry for this second amendment: the last entry is from the first update run.
- **Checked with `gh`, read-only:**
  - `github/docs` `src/github-apps/data/fpt-2026-03-10/server-to-server-permissions.json`, for the permission behind every App call;
  - `github/rest-api-description` `api.github.com.2022-11-28.json`, for the release create and update notes, the draft listing, and ruleset `bypass_actors` visibility;
  - the docs reusable `data/reusables/actions/jobs/section-using-jobs-in-a-workflow-needs.md`;
  - live tags and drafts on the 18 repos;
  - release authors on `release-drafter/release-drafter` and `actions/runner`, to see whether publishing a draft keeps its author.
- **Brownfield:** grep of `references/*/.github/workflows`, for how Zot authenticates pulls.

---

## Closure of the scoped findings

| Finding | Status | Rule that closes it (quoted) | What remains |
| --- | --- | --- | --- |
| **U-A1** (critical) and **U-V1** (high): `GITHUB_TOKEN` can't publish a draft whose `.github/workflows/` differs from `main`'s | **Closed (mechanism).** Nightly sequencing is open (U-C1). | L405 (create mode): "if the release SHA's `.github/workflows/` differs from `main`'s, creates nothing and fails with 'workflows changed on main during the release, nothing released'". L417 (`publish` step 5): "If the release SHA's `.github/workflows/` equals `main`'s, publish the draft … Otherwise end `ready`: `GITHUB_TOKEN` can't publish it, and nightly's `publish-ready` does". L445: "`publish-ready` (App, stdlib only), after `wait` … with an App token holding Contents and Workflows write on that repo". L443: "`ready` passes only once `publish-ready` has published that draft". L712: the "behind main" spike is retired. | 1. `publish-ready` is skipped whenever `wait` fails, and `wait` applies a verdict it can't know yet (U-C1). 2. `publish-ready`'s inputs and checks aren't buildable as written (U-C2). 3. No path ships mixed content: completion always uses the one artifact named by the trailer. A partly pushed version can still be silently abandoned (U-C3). 4. Create mode is not starved by nightly workflow changes (see "Checked and holding"). |
| **U-A2** (high): `resolve` can't see drafts | **Closed** | L392: "`resolve` (stdlib only; `contents: write`, which listing drafts needs, and `actions: read`)". L391: "the caller's `release` job grants their union". Confirmed in OpenAPI `repos/list-releases`: "Only users with push access will receive listings for draft releases." | none |
| **U-A11** (low): duplicate marked drafts; re-runs | **Closed** | L369: "more than one marked draft fails the run". L404: "it reuses a marked draft whose `hexalith-release-run:` names this run, and fails if any other marked draft exists". "Re-run all jobs" re-resolves into complete mode for the same run and its artifact, so it converges. | none |
| **U-A3** (medium): the missing-artifact path | **Closed** | L406: the trailers `hexalith-release-packages: <ids>` and `hexalith-release-containers: <names>`. L410: "deleted only when none of its listed packages exists at its version on nuget.org and none of its listed container tags exists in the registry; the run then ends `nothing`". | The registry read has no stated credential. Zot needs one even to pull, so an "unauthorized" answer can be misread as "absent" (U-C8). |
| **U-A4** (medium): Builds' workflow-path check | **Closed** | L408: "that that run's workflow path equals the running caller's (`github.workflow_ref`: `release.yml` in modules, `builds-release.yml` in Builds) … A run that no longer exists or fails this check counts as having no artifact". In a called workflow, `github.workflow_ref` is the caller's. | none |
| **U-X1** (high): the `bump-push` substitution check | **Closed** | L449–451: "its parent is the tip `bump` used, and that tip is still `main`; its own API reads confirm that the new `builds-version` is the newest acceptable tag …; each changed file under `rendered/` equals its parent copy with the old tag and its commit replaced by the new tag and its commit. The one exception: a `hexalith-ci.json` may also gain keys whose values equal the `default` …". An added file has no parent copy, so it fails, which is correct. | none |
| **U-R5** (medium): `bump` renders on a stale tree | **Closed** | L447: "It fetches the current tip of CiCd `main`, never the run's `github.sha`. On that tip it moves `builds-version` …". The race window shrinks from hours to the gap between `bump` and `bump-push`. | none |
| **U-X2** (high): the artifact trailer and the one-step version bound | **Closed** | L402: "accepts `version` only if it is the last reachable `v*` tag with exactly one of major, minor or patch incremented". L403: "checks through the API that the artifact ID belongs to this run, is named `release` and has the digest `build` output". L408: "takes exactly the artifact named by `hexalith-release-artifact:` … an artifact whose API digest differs fails the run". | The bound is undefined when no `v*` tag is reachable. AI.Tools has none today (U-C9). |
| **U-V4** (medium): stray tags | **Closed for the publish binding** | L413: "that no tag `v<version>` exists or that it points at `sha`". L417: "check the returned release and that `v<version>` resolves to `sha`, or fail with 'tag vX.Y.Z does not point at the built commit'". L592: the fixed message. | The clause "or that it points at `sha`" can never be reached: a tag at `sha` makes AD-16 unmark the draft first (U-C3). |
| **U-R1** (high), **U-A6** (medium), **U-V11** (low): the `delivered/**` ruleset and refs that aren't ancestors of `main` | **Closed** | L579: "a ruleset on `delivered/**` that restricts creation, updates and deletion and blocks force-push, with the App as its only bypass actor". L205: "A ref whose commit is not an ancestor of CiCd `main` fails the run, naming it." | Step 3 still applies such a ref, and L203 can take `tools/` from it (U-C6). The ref advance needs Workflows write in its token (U-C5). |
| **U-X5** (medium): tools from the last delivered commit | **Closed for steps 3–5** | L203: "When the run's global checks failed, steps 3–5 run with `tools/` taken from the newest commit that a `delivered/*` ref points to, never from the run's commit." | Step 1 still runs the failing commit's tools, and a crash there can stop steps 3–5 (U-C7). |

**Tally:** all 15 scoped IDs (11 rows) are closed. U-V4 and U-X5 are closed only partly, as noted. The residuals are new findings U-C1 to U-C11.

---

## New findings

### U-C1 (high): `wait` applies a verdict that depends on `publish-ready`, which runs after it; `publish-ready` and `scan` are skipped whenever `wait` fails

- **Location:**
  - AD-18 `wait` (L440–444), `publish-ready` (L445), `scan` (L446);
  - "The night fails when any job fails" (L460);
  - AD-17 Prevents, "a stale draft blocking a module's releases" (L386).
- **Rule as written:**
  - L440 has `wait` write "the verdict per run", including "`ready` passes only once `publish-ready` has published that draft" (L443).
  - `publish-ready` runs "after `wait`" (L445), with no "whatever its result". `bump`, by contrast, runs "whatever their results" (L447).
  - `scan` runs "after `publish-ready`" (L446), also with no "whatever".
- **Platform:** GitHub docs, `jobs.<job_id>.needs`: "If a job fails or is skipped, all jobs that need it are skipped unless the jobs use a conditional expression that causes the job to continue."
- **Scenario:**
  1. Night N: module X completes a stuck draft after a bump, so it ends `ready` as designed (L417).
  2. Module Y fails its release: for example a CodeQL high alert (AD-18 L462), which stays red for days.
  3. `wait` applies the verdict table and fails, because L460 needs some job to fail the night and only `wait` evaluates verdicts.
  4. `publish-ready` is skipped, and `scan` is skipped with it. `bump` runs.
  5. Night N+1: X is again in complete mode and ends `ready` again. While Y is red, X can never publish, and it creates no new release, because its marked draft forces complete mode.
- **The literal reading is worse.** At `wait` time no `ready` run "has been published", so `wait` fails on every `ready` run. `publish-ready` is then never reached, even on an all-green night. That is U-A1's deadlock again.
- **The opposite reading is no better.** If story 8 keeps `wait` green, no job applies the verdict table at all, and failed releases pass silently. That contradicts AD-18's Prevents, "silent nightly failures".
- **It also covers Builds.** A Builds draft left `ready` is not published, so tonight's bump can't move to it.
- **Smallest fix (AD-18):**
  > 2. **`wait`** (App). Polls every 60 seconds until all runs complete, for at most 5 hours, and outputs each run's conclusion and outcome. It fails only when it can't list the runs.
  > 3. **`publish-ready`** (App, stdlib only), after `wait` whatever its result: for each run whose conclusion is `success` and outcome `ready`, it publishes the marked draft (checks in U-C2). It then writes the summary and the verdict per run: a conclusion other than `success` is failed, whatever the outcome; `success` with `published`, `nothing` or `disabled` passes; `ready` passes only if this job published that draft; no readable outcome, or still running after 5 hours, is failed. It fails if any verdict is failed.
  > 4. **`scan`** (no secrets), after `publish-ready` whatever its result.

### U-C2 (medium): `publish-ready`'s inputs and checks can't be built as written; AD-16 has nightly read `draft`'s outputs, which no cross-repo job can

- **Location:**
  - AD-16 (L376): "`publish` and nightly take it from `draft`'s outputs and re-check only ancestry";
  - AD-17 `draft` outputs (L411);
  - Outcome (L421);
  - `publish` steps 1 and 5 (L413, L417);
  - AD-18 `publish-ready` (L445);
  - AD-7 token rule (L217).
- **The problems:**
  1. **The last reachable tag is passed nowhere.**
     - `draft`'s outputs (L411) are `publish`, `version`, `sha`, `draft-id`, `artifact-id`, `artifact-digest` and `artifact-run`. They don't include it, so even `publish` can't "take it from `draft`'s outputs".
     - Nightly runs in CiCd. It reads only the `hexalith-release-outcome` artifact, which holds `schema`, `sha`, `version` and `outcome`. Job outputs of a module run aren't exposed through REST.
     - Story 3 (which owns the outcome schema, AD-10 public API) and story 8 (`publish-ready`) therefore have no common contract for "still marked".
  2. **"The `publish` checks (AD-17 `publish` steps 1 and 5) other than the download" is ambiguous.**
     - Step 5's first check is the condition "If the release SHA's `.github/workflows/` equals `main`'s". `publish-ready` runs exactly when that condition is false. A literal implementation ends `ready` again and never publishes.
     - Step 1's digest and `.nupkg` checks run on the downloaded files. With the download excluded, it's unclear whether the API digest is compared with the trailer.
  3. **The token permissions are incomplete.**
     - The token "holding Contents and Workflows write" (L445) is minted with exactly those `permission-*` inputs (L217), and any `permission-*` input limits the token to the ones listed (memlog constraint).
     - An API digest check (`GET …/actions/artifacts/{id}`) needs `actions: read`, which that token then lacks.
- **Smallest fix (AD-16, AD-17, AD-18):**
  > - AD-17: `draft` also outputs `last-tag`. When the outcome is `ready`, `outcome.json` also holds `draftId` and `lastTag`; the release-outcome schema has these from its first tag.
  > - AD-16: "`publish` takes it from `draft`'s outputs, and nightly from `outcome.json`; both re-check only ancestry."
  > - AD-18 `publish-ready`: "It reads the draft by `draftId` and checks that it is still marked (against `lastTag`). It checks that the API digest of the artifact named by `hexalith-release-artifact:`, in the run named by `hexalith-release-run:`, equals the trailer, and that no tag `v<version>` exists or that it points at `sha`. It then sends step 5's publishing request, without step 5's tree comparison, and checks the returned release and that `v<version>` resolves to `sha`. Its tokens hold Contents and Workflows write, and Actions read, on that repo."

### U-C3 (medium): A tag at the draft's own SHA unmarks the draft, so step 1's "or that it points at `sha`" can't be reached, and a partly pushed version is silently abandoned

- **Location:**
  - AD-16, marked draft (L373): "its `tag_name` is `v<semver>`, above the last `v*` tag reachable from that SHA";
  - L376: "among the tags whose commit is an ancestor of that SHA";
  - AD-17 `publish` step 1 (L413).
- **The clash:**
  - A commit is its own ancestor (`git merge-base --is-ancestor S S` succeeds).
  - When `v<version>` exists at `sha`, the last reachable tag is `v<version>` itself. The draft's `tag_name` is then not above it, so the draft is unmarked and "never touched".
  - Step 1 explicitly accepts that state. The two rules disagree.
- **Scenario (careless module agent, in model; module-agent tokens hold Contents write, and `v*` creation is not restricted):**
  1. Draft v1.2.0 at S0 is stuck after 2 of 5 packages were pushed.
  2. An agent "fixes" the missing tag by creating `v1.2.0` at S0.
  3. The next night, `resolve` sees no marked draft, so it picks create mode at `github.sha`.
  4. `version` starts from v1.2.0 and ships v1.2.1. The night is green.
  5. v1.2.0 stays on nuget.org with 2 of 5 packages and no release. Its draft sits unmarked for good.
  6. A stray *higher* tag on an ancestor of S0 has the same effect.
- **Smallest fix (AD-16):**
  > - … "its `tag_name` is `v<semver>`, above the last `v*` tag other than its own `tag_name` reachable from that SHA."
  > - "A draft authored by `github-actions[bot]` whose body carries a `hexalith-release:` trailer but fails the marked test fails `resolve`, naming it."
  >
  > Step 1 then reaches both branches. A same-version tag elsewhere fails red with the existing message "tag vX.Y.Z does not point at the built commit".

### U-C4 (medium): The App can't read ruleset bypass actors, so "its rulesets are exactly the AD-21 ones" is either blind or fails every module

- **Location:**
  - AD-3, App per-module checks (L131);
  - AD-7, App permissions (L214);
  - AD-21 step 1, rulesets (L558);
  - Deferred, the story-1 `v*`-creation rule with bypass actors (L714).
- **Evidence:**
  - Reading a ruleset needs only `metadata:read` (`server-to-server-permissions.json`).
  - But OpenAPI, `GET /repos/{owner}/{repo}/rulesets/{ruleset_id}`: "To prevent leaking sensitive information, the `bypass_actors` property is only returned if the user making the API request has write access to the ruleset."
  - The App holds Administration *read*.
- **Two stories' readings:**
  - **Story 7, strict.** It compares the whole ruleset, including `bypass_actors: []`. The field is absent, so every module fails its App checks, no `delivered/<Repo>` ref is ever created, and nothing is adopted.
  - **Story 7, lax.** It ignores the missing field. A bypass actor added to `v*` (for example an agent App) then goes unseen.
  - **The Deferred story-1 rule** names exactly two bypass actors (GitHub Actions and the CiCd App), which the App can never verify.
- **Smallest fix (AD-3):**
  > … "its rulesets' targets, conditions and rules are exactly the AD-21 ones. Their bypass actors, which the App can't read, are checked by hand at onboarding."

### U-C5 (low): Advancing `delivered/<Repo>` needs Workflows write in the token whenever CiCd's own workflows changed

- **Location:** AD-6 step 2 (L199); AD-7 token rule (L217).
- **Evidence:** `server-to-server-permissions.json` lists `workflows:write` as an additional permission for `POST /git/refs` and `PATCH /git/refs/{ref}`. A git push that changes `.github/workflows/` on the updated ref is refused without it.
- **Scenario:**
  1. A CiCd commit edits `nightly.yml`.
  2. Story 7 mints the advance token with `permission-contents: write` only, which is a valid reading of "passing `permission-*` for each use".
  3. Every module's advance across that commit is refused, so every module fails its push and no ref moves until the token is fixed.
- **Smallest fix (AD-6 step 2):**
  > … "advance CiCd branch `delivered/<Repo>` … with an App token holding Contents and Workflows write on CiCd".

### U-C6 (low): A ref that isn't an ancestor of `main` fails the run, but is still applied and can become the tools source

- **Location:** AD-6, L200 (step 3), L203, L205.
- **The clash:**
  - Step 3 applies "every module that has a `delivered/<Repo>` ref, passing or not".
  - L203 takes `tools/` from "the newest commit that a `delivered/*` ref points to".
  - Neither excludes the non-ancestor ref that L205 names.
  - With the U-R1 ruleset, only App code can create such a ref. But if one exists, its unvalidated render is still written hourly, and its unvalidated `tools/` can run with the key.
- **Smallest fix (AD-6, L205):**
  > "A ref whose commit is not an ancestor of CiCd `main` fails the run, naming it. It is not applied, and its commit is never the `tools/` source."

### U-C7 (low): With the global checks failed, step 1 still runs the failing commit's tools

- **Location:** AD-6, L198 (step 1) and L203.
- **The issue:**
  - L203 moves only steps 3–5 to the last delivered `tools/`.
  - Step 1 (the App checks) still runs the run's own, failing `tools/`. Its result is unused, because step 2 doesn't advance anything when the global checks failed.
  - If step 1 crashes, the job's later steps are skipped. The one-hour repair bound that U-X5 kept is then lost while `main` is red.
- **Smallest fix (AD-6, L203):**
  > "When the run's global checks failed, steps 1 and 2 are skipped, and steps 3–5 run with `tools/` taken from …".

### U-C8 (low): The missing-artifact container check has no registry credential, and failing open republishes containers

- **Location:** AD-17 complete mode (L410); permissions of the reusable release's jobs (L391).
- **Evidence:**
  - Zot needs authentication even to pull. CI logs in with the pull-only pair (`references/Hexalith.Builds/.github/workflows/domain-ci-v2.yml:655`; `Hexalith.Parties/.github/workflows/current-owner-startup-diagnostics.yml:99`).
  - The security review describes that pair as limited to test images.
  - `draft` is given no registry secret.
- **Scenario:**
  1. A stuck draft's artifact has expired.
  2. The module ships containers only, so the package check is vacuous.
  3. The tag query returns 401, and `draft` reads it as "absent".
  4. The draft is deleted.
  5. The next run rebuilds the same version at a newer SHA and pushes `:vX.Y.Z` again.
- **Smallest fix (AD-17 complete mode):**
  > … "none of its listed container tags exists in the registry (read with the pull pair; any answer other than a definite not-found counts as existing)".

### U-C9 (low): The version bound and the `version` range are undefined when no `v*` tag is reachable

- **Location:** AD-16 (L373, L376); AD-17 `version` (L399), `draft` (L402).
- **Evidence:** `gh api repos/Hexalith/Hexalith.AI.Tools/git/matching-refs/tags/v` returns 0 refs. Every other repo has `v*` tags.
- **The issue:**
  - semantic-release core is not run (L399), so nothing supplies its first-release rule.
  - "The last reachable `v*` tag with exactly one part incremented" has no base. `version` and `draft` (both in story 3) can each pick a different one: 0.0.1, 0.1.0 or 1.0.0.
- **Smallest fix (AD-16):**
  > "With no reachable `v*` tag, `version` ranges over the whole history, and the only accepted version is `1.0.0`."

### U-C10 (low): The 90-day retention is App-checked per module, but it is not in any per-repo step, and Builds is never checked

- **Location:**
  - AD-3 (L131): "its artifact and log retention is 90 days";
  - AD-21, once-only list (L552) and per-repo step 1 (L555–562);
  - AD-19 preconditions (L509–517).
- **The issue:**
  - Today every repo reports `{"days":30,"maximum_allowed_days":30}` (update-verification U-V2). Setting the org to 90 need not change a repo whose own value was set to 30.
  - Step 1 doesn't say to set the repo value, so the App check simply fails adoption until someone notices.
  - Builds' complete mode needs the same 90 days for its `release` artifact and its creating run. No precondition sets or checks it.
- **Smallest fix:**
  > - AD-21 step 1: add "set the repo's Actions artifact and log retention to 90 days".
  > - AD-19 "Before the first rewritten release": add "Builds' artifact and log retention is 90 days".

### U-C11 (low): A `ready` draft from a run outside nightly has no publisher until the next night, or none at all before nightly exists

- **Location:** AD-17 step 5 (L417); AD-19 Bootstrap (L518); AD-10 acceptable tag (L280).
- **The issue:**
  - `ready` is published only by nightly's `publish-ready`.
  - An interactive dispatch (CAP-15 allows CiCd-agent Builds releases) that ends `ready` leaves pushed packages with no tag until 02:17. It is published there only if U-C1 is fixed.
  - The **Builds bootstrap** runs before `nightly.yml` exists. If it ends `ready`, which needs a Builds workflow commit between `draft` and `publish`, no tag ever seeds `builds-version`.
  - The manual or App publication also assumes the release keeps `author` `github-actions[bot]`. AD-10's acceptable-tag test depends on that. The evidence is good but indirect: on `release-drafter/release-drafter` and `actions/runner`, drafts created by `github-actions[bot]` and published later still show that author. The REST update body has no author field.
- **Smallest fix:**
  > - AD-19 Bootstrap: "If it ends `ready`, the maintainer publishes that draft as it is."
  > - Deferred: "Story 8 check: a draft created by `github-actions[bot]` and published by the App keeps `author` `github-actions[bot]`. If not, AD-10's acceptable-tag test also accepts a release published by the CiCd App."

---

## Checked and holding

- **Create mode is not starved by nightly workflow changes.**
  - The bump's delivery lands after that night's `wait` (L447–457), and the next night's `github.sha` already contains it.
  - `dispatch` first waits for in-flight deliveries (L436).
  - Inside the release window, workflow files change only in these cases:
    - a CiCd render change, delivered by a push-triggered or `:47` run;
    - a Builds workflow commit (Builds only);
    - a `chatgpt-codex-connector` edit and its `:47` repair.
  - Each fails one night, visibly. No module is starved unless one of these recurs every night inside the window.
  - One case remains: when `wait` times out, the bump's delivery can land under a still-running release. That run fails or ends `ready` after `publish-ready` has run, and the next night's complete mode publishes it. It converges.
  - The comparison is on `.github/workflows/` only, so ordinary product pushes during the night don't trigger it.
- **App permissions cover every App call** (`server-to-server-permissions.json`):

  | Call | Needs | The App has it? |
  | --- | --- | --- |
  | artifact and log retention | `administration:read` | yes |
  | immutable releases | `administration:read` | yes |
  | `automated-security-fixes` | `administration:read` | yes |
  | `code-scanning/default-setup` | `administration:read` | yes |
  | rulesets | `metadata:read` | yes, except `bypass_actors` (U-C4) |
  | draft listing, update and delete | `contents` | yes |
  | update of a release whose target differs in workflows | `contents:write` + `workflows:write` | yes |
  | dispatch | `actions:write` | yes |
  | runs and artifacts | `actions:read` | yes |

  - Code scanning alerts read is held but no App job uses it: the release's `codeql` job reads alerts with its own `GITHUB_TOKEN`. This is a least-privilege nit, not a defect.
- **The marked-draft definition fits every creation path.**
  - Only create-mode `draft`, with `GITHUB_TOKEN`, creates marked drafts.
  - The App never creates one now, because create mode fails instead of leaving the draft to the App.
  - Drafts by agents, by the maintainer's token or by `chatgpt-codex-connector[bot]` are unmarked.
  - The live legacy drafts (Agents v1.2.1 and v1.2.2, by `github-actions[bot]`) carry no trailers, so they are unmarked and on the AD-21 step-1 deletion list.
- **Outcome values and nightly's verdict table agree.**
  - `publish` writes `published`, `ready` or `failed`; the final job writes `nothing`, `disabled` or `failed`.
  - The final job no longer writes `ready`, which is consistent with create mode failing.
  - Every value has a verdict row. Only the job that applies the table is wrong (U-C1).
- **Job limits.** Every nightly job stays under 6 hours. The longest is `wait`, at 5 hours plus the mint steps. The whole run is about 8 hours, against a 35-day workflow limit and the 24-hour cron cycle.
- **The race between step 5's comparison and its request converges.** If `main`'s workflows change between the comparison and the request, GitHub returns 404 (OpenAPI note on update-release). The run fails, and the next night's complete mode ends `ready` and is published by `publish-ready`.
- **The bump substitution is safe against unrelated version strings.** Rendered callers name only Builds actions and local actions (AD-1), so the old tag string appears only where the render puts it.

## Spec handoff items (not spine defects)

- **`SPEC.md:199`:** the conditional "assumes that story 3's spike shows `GITHUB_TOKEN` can publish a draft behind `main`". The refusal is documented and the App path is now unconditional. Amend CAP-13 success 1 and 2 ("made by a run in its own Actions tab") and the baseline Releases row.
- **`stories.yaml:39`:** story 3 still lists the "publishing a draft behind main" spike.
- **`stories.yaml:108`:** story 8's `publish-ready` is still conditional ("if story 3's spike confirmed").
- **Story 3:** the outcome schema fields from U-C2, if adopted.
