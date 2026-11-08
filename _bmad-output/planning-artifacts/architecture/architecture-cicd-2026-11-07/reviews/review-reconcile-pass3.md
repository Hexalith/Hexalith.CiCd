---
review: reconcile-pass3
target: ../ARCHITECTURE-SPINE.md (working copy 2026-11-08, decisions U1–U4)
against: [SPEC.md, pipeline-stages.md, enforcement.md, gate-classification.md, module-inventory.md, baseline-and-targets.md, stories.yaml]
decision_logs: [../.memlog.md, ../../../../specs/spec-cicd/.memlog.md]
excludes: items already in review-reconcile-spec.md and review-reconcile-companions.md, unless still unresolved
date: 2026-11-08
---

# Reconcile review, pass 3: spine (U1–U4) against the refreshed SPEC-cicd

## Verdict

**PASS WITH FIXES.** Nothing in the spec is contradicted head-on, and the Precedence deletion lost nothing: all 19 rows landed in SPEC.md, a companion or `stories.yaml` (section 3). Today's edits (U2 story-number removal, U3 AD-20 end state, U4 schema convention) are consistent with the spec.

Three spine gaps remain where the spec states a requirement that no AD delivers:
- **AD-20's freeze is narrower than the spec's.** The spec freezes "every Builds file that modules call today". The spine freezes only the files reached through Builds workflows. That leaves `Github/initialize-dotnet@main`, which 18 references in FrontComposer and Memories call, unprotected, and story 2 edits the only Builds workflows that use it.
- **The per-module skip doesn't work.** `delivered` advances for every module, including one that failed its own checks. That module's guard, restore and release drift check therefore enforce the render that validation rejected.
- **Builds' release has no perimeter.** The reusable release's drift check (AD-17 step 1) has nothing to compare for Builds, and "Builds is never guarded" is at odds with the U3 trigger "once the guard's commitlint runs in `builds-ci.yml`".

There are also 4 medium findings, 10 low ones and 9 upstream story edits.

Severity: **Critical**: blocks a build or a CAP everywhere. **High**: two stories will build incompatible things, or a CAP or success criterion fails. **Medium**: a quiet spec requirement or consequence is unrecorded, or the outcome is conditional. **Low**: wording, a single-story detail, or an upstream-only edit.

---

## 1. Findings

### Critical

None.

### High

#### H1. AD-20 freezes less than the spec's "every Builds file that modules call today" (still unresolved from pass 2)

- **Spec:**
  - SPEC.md l.166: "Every Builds file that modules call today stays unchanged until the last caller has moved."
  - module-inventory.md l.32: composites "Frozen while legacy callers remain".
- **Spine:** AD-20 l.397: "Every Builds workflow that modules call today, and every composite, action and script **those workflows** reference…"
- **Evidence (checked 2026-11-08 in `references/*/.github/workflows`):**
  - Modules call Builds composites **directly**:
    - `Github/initialize-dotnet` 21 times, 18 of them at `@main` (FrontComposer, Memories);
    - `Github/initialize-build` 30 times, 21 at `@main`;
    - `Github/verify@main` once;
    - `prepare-domain-release` 7 times, `dapr-init` 6 times, `create-release` and `prepare-module-build` once each.
  - Among Builds workflows, `initialize-dotnet` is referenced only by Builds' own `ci.yml` (4 times) and `build-release.yml`. No `domain-*` workflow references it, and no Builds workflow references `verify` or `prepare-domain-release`. The literal AD-20 text therefore does not freeze them.
  - Story 2 adapts exactly those two workflows (the rename, and the "minimally adapted" `builds-release.yml`). The AD-19 interim keeps "publishing unchanged", and that release runs `./Github/initialize-dotnet` and `./Github/create-release`.
  - rubric-pass2 M8 and adversary-pass2 H7 raised this. Spine memlog l.80 records "freeze covers every Builds file modules call today", but the spine text kept the transitive-only wording.
- **Fix (spine, AD-20 bullet 1):** "Every Builds file that a module uses today, directly (a `uses:` of a Builds workflow or composite at `@main` or a SHA) or through a Builds workflow, stays unchanged until the last module has moved. That includes `domain-ci.yml`, …, `Github/initialize-build`, `Github/initialize-dotnet`, `Github/verify`. Builds' own workflows may stop using a frozen file but never change it."

#### H2. A module that fails its own checks is not really skipped: `delivered` carries its rejected render to the guard, restore and release

- **Spec:**
  - SPEC.md l.49 (CAP-4): "A module that fails its own checks is skipped and reported, and the other modules are still delivered."
  - Success signal l.192: "A red CI run in any module means the product is broken."
  - enforcement.md l.18: `delivered` "holds only renders that passed validation".
- **Spine:**
  - AD-6 l.168: on a passing run (global checks), "Advance branch `delivered` to the validated commit" for all modules.
  - AD-6 l.172: a module that fails its checks is skipped.
  - AD-6 *Prevents*: "unvalidated renders reaching modules or the guard".
  - AD-8 l.192: the guard reads `delivered`. AD-8 l.200: restore applies it. AD-17 step 1: the release drift-checks against it.
- **Evidence:** Walk the most likely per-module failure, a hook enabled in `setup/` before the module's action reaches its live `main` (AD-3 l.116):
  1. The global checks pass, so `delivered` now holds the new `hexalith-ci.json` with the hook enabled. The module is skipped.
  2. The module's next CI run fails the guard on `hexalith-ci.json` drift.
  3. On `main`, restore writes that file, because the tags are equal, and dispatches CI.
  4. The guard then fails "enabled action missing", every run, until the action lands.
  5. The nightly release fails its drift check.

  So the per-module check is bypassed by restore: the module is red for a CiCd mistake and gets a partial write of a render that was rejected for it. The same happens for any template change while a module fails a precondition check.
- **Fix (spine, AD-6 step 1):** "The `deliver` job builds `delivered` with the App: global files from the validated commit, and each module's `rendered/<Repo>/` and `<Repo>.perimeter.json` from the validated commit if that module passed its checks, otherwise carried over from the previous `delivered`." The alternative, keeping the fast-forward and amending CAP-4 and the Success signal ("a skipped module is red until its checks pass"), is not recommended.

#### H3. Builds' release has no perimeter for its drift check, and "Builds is never guarded" conflicts with the guard running on Builds

- **Spec:**
  - SPEC.md l.137: Builds "is never rendered, delivered to, **guarded**, bumped, or duplicate-scanned".
  - CAP-12 intent: the release publishes only a commit "whose owned files match the delivered state".
  - CAP-15: Builds releases through the same nightly run.
- **Spine:**
  - AD-19 l.384: "never … guarded".
  - AD-19 l.386: the test-only inputs `module-root` and `expected-source` exist only on `ci.yml`.
  - AD-19 l.387: `builds-release.yml` passes only `ci-workflow` and `release-rules`.
  - AD-17 l.326: the reusable release "re-run[s] the guard check … against `delivered`".
  - AD-20 l.401 (new today, U3): `commitlint-caller.yml` goes "once the guard's commitlint runs in `builds-ci.yml`".
- **Evidence:** `delivered` has no `Hexalith.Builds.perimeter.json` (no setup file, AD-3). When story 5 adds the drift check to the release that story 3 wired to `builds-release.yml`, one of two things happens:
  - Builds' nightly release fails, so CAP-15 fails.
  - A "missing perimeter = pass" path gets built, which is a silent bypass for any module.

  Meanwhile U3 relies on the guard running against Builds itself, using the fixture perimeter, which contradicts the literal "never guarded".
- **Fix:**
  - **Spine, AD-19:** "`builds-ci.yml` and `builds-release.yml` pass `expected-source` (Builds' fixture perimeter), so the guard and the release drift check run against the fixture. Builds is never guarded against `delivered`. A missing perimeter fails the guard."
  - **Upstream, SPEC.md l.137:** "never guarded against the delivered state".

### Medium

#### M1. Restore's lockstep condition narrows CAP-8, and the spec doesn't say so

- **Spec:**
  - SPEC.md l.74: "A restore commit repairs everything except `.github/workflows/**`".
  - l.75: "No such change persists beyond the next CI run."
  - Success signal l.192.
  - enforcement.md l.26: restore "writes the expected state … skipping `.github/workflows/**`".
  - baseline-and-targets.md l.21.
- **Spine:** AD-8 l.200: restore writes the gitlink, the `.gitmodules` section and `hexalith-ci.json` "only when the perimeter's tag equals the running workflow's tag". l.202: "What restore skips waits for the next delivery, at most one hour later."
- **Evidence:** If the tags differ (between a bump commit and its delivery, or after an App-based agent re-pins the caller), an edit to `hexalith-ci.json` or the gitlink persists past the next CI run, for up to 1 h. Under the Precedence rule, a story builds to the spine and the CAP-8 test fails.
- **Fix (upstream):**
  - CAP-8 success 2 and 3, enforcement.md Layer 2 step 4, the baseline "persist" row and the Success signal: "everything except `.github/workflows/**` and, when the delivered Builds tag differs from the running one, the Builds tag, its `.gitmodules` section and `hexalith-ci.json`. These are repaired by the next delivery, within 1 h."

#### M2. AD-20 binds `Github/` and `Tools/` but defines an end state only for `.github/workflows/`, so legacy composites and scripts have no fate

- **Spec:**
  - CAP-16 l.129–133 deletes `prepare-domain-release` and "the legacy actions".
  - module-inventory.md l.32 lists 8 composites as "Frozen while legacy callers remain", with no fate after that except `prepare-domain-release`.
  - Story 27 enumerates only that list.
- **Spine:** AD-20 *Binds* "Builds `.github/workflows/`, `Github/`, `Tools/`". l.402: "removes everything else outside the end state". l.403: the end state names only `.github/workflows/`.
- **Evidence:**
  - Builds `Github/` today: `commitlint`, `create-release`, `dapr-init`, `governed-provenance`, `initialize-build`, `initialize-dotnet`, `package-release`, `prepare-domain-release`, `prepare-module-build`, `publish-azure-container-app`, `publish-container-to-registry`, `publish-containers`, `run-module-integration`, `scripts`, `split-publication`, `unit-tests`, `verify`.
  - Four of these (`commitlint`, `run-module-integration`, `scripts`, `split-publication`) appear nowhere in the spec.
  - `Tools/` holds about 50 legacy G4/G6 and package-audit scripts.
  - "Everything else outside the end state" can't be applied to directories that have no end state. This is the same orphan pattern that U3 fixed for workflows.
- **Fix:**
  - **Spine, AD-20 end state:** "`Github/` and `Tools/` hold only what `ci.yml`, `release.yml`, `builds-ci.yml`, `builds-release.yml` and `check.py` use. Everything else goes in the final legacy deletion." Since bullet 2 puts all new code in new files, nothing legacy survives.
  - **Upstream:**
    - module-inventory.md Builds-today table: add the four missing composites, `candidate-policy.yml`, `commitlint-caller.yml`, the `domain-*.md` docs and `Tools/` with their AD-20 fates.
    - Story 27: see section 2.

#### M3. Unmanaged repos call legacy Builds actions at `@main`, so "until the last caller has moved" never literally happens

- **Spec:**
  - SPEC.md l.166 and module-inventory l.27: "until the last caller has moved".
  - Non-goal l.178: the other ~43 repos are out of scope.
  - CAP-16 and module-inventory l.33 delete `package-release` and `publish-container-to-registry`.
- **Spine:** the AD-20 title says "until the last caller has moved", and its body says "until the last module has moved".
- **Evidence (checked live, 2026-11-08):**
  - 13 unmanaged public repos (Applications, ChatClient, Documents, Domains, EventStores, GitStorage, IdentityStores, KeyValueStorages, MyNewModule, MyNewPackage, NetAspire, Security, Streams) run `Hexalith/Hexalith.Builds/Github/package-release@main` on push. Security_OLD runs it too, so 14 repos in all.
  - One of those repos also runs `Github/publish-container-to-registry@main`.
  - None of these repos is archived. Their last pushes were between January and April 2026.
  - The final legacy deletion breaks their next push build, and neither document records this.
- **Fix (decision):**
  - **Recommended:** accept it and record it.
    - **Spine, AD-20:** "Callers outside the 17 modules are not waited for."
    - **Upstream:** add the same sentence as a known effect to CAP-16 or module-inventory, listing the 14 repos.
  - **Alternatives:** archive the 14 repos first, or keep `package-release` and `publish-container-to-registry` until they are archived.

#### M4. The Deferred story-3 fallback would break CAP-13 "made by a run in its own Actions tab"

- **Spec:**
  - SPEC.md l.108: a new release is "made by a run in its own Actions tab".
  - l.109: "A failure shows as a failed run in that repository".
  - baseline-and-targets.md l.22: the same wording.
- **Spine:** Deferred l.549: if the spike confirms the `GITHUB_TOKEN` refusal, "the run ends `ready`, and `nightly.yml` publishes ready drafts with the App before the bump".
- **Evidence:** Under the fallback, a module's release finishes in CiCd's run, and a failure to publish shows only in CiCd. Neither the spine nor the spec marks this as a spec change.
- **Fix:**
  - **Spine, Deferred:** "Taking the fallback amends CAP-13 success 1 and 2 and the baseline Releases row; raise it as a spec update."
  - **Upstream:** story 8 notes the conditional task.

### Low

#### L1. AD-18 doesn't say that the duplicate scan never blocks the bump
- **Spec:** enforcement.md l.70 ("It never blocks the Builds bump"); story 9.
- **Spine:** AD-18 l.352 says "whatever their result", which covers the release runs only.
- **Fix (spine):** "When all runs are complete and the scan has run, whatever their results, it bumps."

#### L2. The rule against the maintainer's personal `gh` login isn't in any AD
- **Spec:** SPEC.md Credentials ("Agent sessions never run with the maintainer's personal `gh` login, which has the `workflow` scope"); enforcement.md l.9.
- **Spine:** AD-7 covers the App and the agent tokens only.
- **Fix (spine, AD-7):** add a bullet: "Agent sessions never use the maintainer's personal `gh` login."

#### L3. Nothing protects `delivered`, though the spec relies on it holding only validated renders
- **Spec:** enforcement.md l.18: "holds only renders that passed validation … module agents can't change it".
- **Spine:** the AD-21 tail gives CiCd a ruleset on `main` only. Adversary-pass2 H1's fix said "A ruleset lets only the App move it", but that part was dropped without a logged decision. CiCd agents and the org agent Apps can push to `delivered`.
- **Fix (spine, AD-21 CiCd preconditions):** "A ruleset on `delivered` blocks deletion and force-push, and restricts updates to the App." If H2 is adopted, the force-push rule must allow the App-built commits.

#### L4. The 26-hour nightly freshness check would make hourly delivery red until `nightly.yml` exists
- **Spine:** AD-6 l.173.
- **Stories:** story 7 (delivery) comes before story 8 (nightly), and neither mentions the check.
- **Fix:** In AD-6, add "once `nightly.yml` has run". Upstream, assign the check to story 8.

#### L5. U4 schema requiredness is unstated for setup files and for Builds' own file
- **Spine:**
  - AD-3 l.106 validates a setup file, which has no `schema` or `buildsTag`, against `hexalith.ci.v1.json`.
  - The Schemas convention says `schema` is required.
  - AD-19 l.385 says Builds' hand-written file is "in the same schema", yet Builds has no `buildsTag` to carry (AD-9 and AD-15 read it).
- **Fix (spine):**
  - AD-3: "the render adds `schema` and `buildsTag`, then validates the result".
  - AD-19: "`buildsTag` is optional in the schema; Builds' file omits it; the guard and `check.py` require it for modules".

#### L6. Builds' own calls to the legacy `codeql.yml` and `dependency-review.yml` have no removal trigger
- **Spec:**
  - SPEC.md "Nothing runs twice: CodeQL runs only in the nightly release".
  - Assumptions l.200.
- **Spine:** AD-20's new rule covers Builds-only workflows (`commitlint-caller.yml`). It does not cover the calls that `builds-ci.yml` (renamed from `ci.yml`, which today calls `codeql.yml` at l.346 and `dependency-review.yml` at l.358) keeps making to those shared, frozen workflows.
- **Evidence:** After story 3, Builds would run CodeQL on every push and again nightly. The final deletion would also break `builds-ci.yml` if the calls remain.
- **Fix (spine, AD-20):** "`builds-ci.yml` stops calling `codeql.yml` in the change that adds `builds-release.yml`'s `codeql` job, and stops calling `dependency-review.yml` at the rename."

#### L7. AD-19 preconditions omit Builds' access to the org secrets and variables
- **Spine:** AD-21 step 1 grants this access for modules. AD-19 l.388 does not, yet `$/Github/publish` needs `HEXALITH_NUGET_USER`.
- **Fix (spine, AD-19):** add "access to the org secrets and variables". Story 1 inherits it through its AD-19 reference.

#### L8. CiCd agents can dispatch `builds-release.yml` at any time (the Builds half of reconcile-spec F-15)
- **Spec:** CAP-15 l.123: "Builds releases at most once a night".
- **Spine:** AD-7 l.183 gives the CiCd-agent token Actions write on Builds. The legacy release (44 per month) shows agents do dispatch it.
- **Fix:** Either remove Actions write on Builds from the CiCd-agent token, or, upstream, amend CAP-15 to "apart from the bootstrap and maintainer-directed dispatches".

#### L9. Upstream: module-inventory says the guard rejects `NuGetAuditLevel=critical`
- **Spec:** module-inventory.md l.67.
- **Spine:** the AD-8 guard rejects `NoWarn` and `NuGetAuditSuppress`. AD-17 neutralizes the audit level with `-p:NuGetAuditLevel=low` (measured, verification-pass2).
- **Fix (upstream):** "The guard rejects `NoWarn` and `NuGetAuditSuppress`; the release build's `-p:NuGetAuditLevel=low` overrides a module's level."

#### L10. Upstream: the instruction block doesn't tell agents to run the local check
- **Spec:** pipeline-stages.md l.44 says "Agents are told to run it before they push", but the block contents in enforcement.md l.83–87 omit it.
- **Spine:** AD-4 sets only the marker-block mechanics.
- **Fix (upstream, enforcement.md):** add the bullet "Run `python3 references/Hexalith.Builds/check.py` before you push." Story 10 writes the text.

---

## 2. Upstream edits needed (stories.yaml; not spine defects)

| Story | Current text | Conflict with today's spine | Edit |
| --- | --- | --- | --- |
| 2 | "the hexalith-ci.json schema"; "minimally adapted builds-release.yml … (AD-20)" | U4 file name and discriminator; the interim release is now described in AD-19; H1 | Name `schemas/hexalith.ci.v1.json` (required `schema`, camelCase `buildsTag`). Add Builds' hand-written `.github/hexalith-ci.json` (AD-19). Cite AD-19 and AD-20. "Don't modify `Github/initialize-dotnet` or `create-release`, which modules call at `@main`." Drop the `dependency-review.yml` call at the rename (L6). |
| 3 | rewrite `builds-release.yml` onto the reusable release | H3, L6 | `builds-release.yml` passes `expected-source` (Builds' fixture). `builds-ci.yml` stops calling `codeql.yml` in the same change. |
| 4 | "the perimeter schema and library" | U4 | Name `schemas/hexalith.perimeter.v1.json`, with `schema: "hexalith.perimeter.v1"` replacing `format: 1`. Every reader fails with the fixed unsupported-schema message. |
| 5 | guard, restore, drift check | U3 (AD-20 l.401), H3 | Add: "Delete `commitlint-caller.yml` in the change where `builds-ci.yml`'s run of the reusable CI against Builds runs the guard's commitlint." The drift check fails on a missing perimeter. Builds runs against its fixture. |
| 6 | "checks that the Builds pointer equals builds_tag" | U4 rename | `builds_tag` → `buildsTag`. `check.py` fails with the fixed unsupported-schema message. |
| 7 | deliver job | H2, L4 | If H2 is adopted: "build `delivered` per module (passed → new render, skipped → previous)". The 26-hour freshness check is conditional or belongs to story 8. |
| 8 | nightly scheduler | M4, L1, L4 | Add the hourly 26-hour freshness check. Add the conditional fallback: publish `ready` drafts with the App before the bump if story 3's spike confirms. The scan never blocks the bump. |
| 27 | enumerated deletion list | U3 end state; M2; M3 | "Delete until Builds' `.github/workflows/` holds only `ci.yml`, `release.yml`, `builds-ci.yml`, `builds-release.yml`, `ci-cd-standards.md` (this removes `candidate-policy.yml`, `commitlint-caller.yml` if still present, `domain-*.md` and `eventstore-maintenance-publisher.yml`), and `Github/` and `Tools/` hold only what the new pipeline uses." Record the 14 unmanaged `package-release@main` callers. |
| 1 | AD-19 preconditions | L7 | Inherits Builds' access to the org variables and secrets once AD-19 lists it. No text change is needed if the AD is fixed. |

Other upstream edits in the spec documents themselves:
- **SPEC.md:**
  - CAP-8 success 2 and 3, and the Success signal (M1);
  - Constraint l.137, "never guarded against the delivered state" (H3);
  - CAP-13 and CAP-15 only if M4 or L8 are taken as amendments.
- **enforcement.md:**
  - Layer 2 step 4 (M1);
  - the instruction-block bullet (L10).
- **module-inventory.md:**
  - the Builds-today rows (M2);
  - the unmanaged-callers known effect (M3);
  - the audit-bypasses wording (L9).
- **baseline-and-targets.md:** the "persist" row (M1).

---

## 3. Spot-check: did every deleted Precedence row land?

The spec memlog's self-validate pass 2 claims that all 19 rows landed. **Confirmed.**

| Deleted row | Landed at |
| --- | --- |
| CAP-1/16 Builds not a spoke | SPEC Constraint l.137; CAP-1 and CAP-16 say "17 modules"; module-inventory l.8 |
| CAP-8 workflows ≤ 1 h | CAP-8 l.75; baseline l.21; enforcement known effects |
| CAP-4 maintainer preconditions | CAP-4 l.50 |
| CAP-6 current major and `builds-skip` | CAP-6 l.62; Constraint l.162; baseline l.18 |
| CAP-5 browsers and Dapr in the main job | CAP-5 l.56; pipeline-stages l.13, l.36 |
| Perimeter: absent config, plus `hexalith-ci.json`, `.gitmodules`, blocks | Constraints l.140–147 |
| Non-goal central failure reporting | Non-goal l.188 |
| CAP-13 no stagger | CAP-13 intent; pipeline-stages l.49 |
| Story 7 separate bumper / story 4 owns `deliver.yml` | Stories 4 (validate), 7 (deliver), 8 (bump). The spine no longer names stories in ADs. |
| Builds releases on all types except `docs`, `test`, `style` | Constraint l.163; pipeline-stages l.75 |
| Restore dispatches CI | CAP-8 l.74; enforcement l.27 |
| Draft-marker release state machine | CAP-12; pipeline-stages l.50–60 |
| CodeQL, nightly hook and NU1903/4 block the release | CAP-14; pipeline-stages l.52, l.56 |
| Dependency review dropped, audit only in release, waivers in Builds | Constraint l.159; pipeline-stages l.85–92; gate-classification l.54 |
| Stories 11–26: no delivery credential | `invoke_dev_with` of stories 11–26 |
| Three hook points only | CAP-5 l.54; pipeline-stages l.34 |
| No slow-suite job | Constraint l.151–153 |
| CAP-11 marker block | CAP-11 l.92; enforcement l.83 |
| Story 1 spike scope | Story 1. Every Deferred owner (1, 2, 3, 4, 8, 9, 15, 20) matches `stories.yaml`. |

Also confirmed:
- No AD body names a story. Story numbers appear only in Deferred, as U2 intends.
- No `builds_tag`, `hexalith-ci.v1`, `hexalith-perimeter` or `format: 1` remains in the spine or the spec companions. The only remnant is story 6.
- Every `AD-n` the spec cites still means what the spec uses it for, including "AD-17 step 1" in story 5.

## 4. Checked with no finding

- **CAP-1, CAP-2, CAP-3, CAP-5, CAP-7, CAP-9 (guard), CAP-10, CAP-11, CAP-12 and CAP-14** each map to an AD with matching success criteria. CAP-2's "every test inside the failing project still runs" is carried by the spec only, and no AD contradicts it.
- **Constraints:** the perimeter; one write path; GitHub Free enforcement; the one-job shape with its two exceptions; nothing runs twice; the gate rule; exact-tag lockstep; release rules; independent releases; dispatch-only releases with an exact kill switch; deny rules per module; credentials (apart from L2); Actions limits.
- **Non-goals:** all 11 respected. The spine adds no deployment, no cascade, no repacking and no pre-push hook, and keeps SDK unification module-owned.
- **Today's U3 end state** matches pipeline-stages "What Builds keeps" plus `ci-cd-standards.md`, which spec Assumption l.197 and story 27 rewrite in place.
- **Today's U4 convention** is consistent with the spec. The spec names no schema file or key, and module-inventory's "`HEXALITH_` prefix" points to the Conventions row.
- **AD-19's interim `builds-release.yml`** keeps environment `production` while the nuget.org policy has none; spine memlog l.90 verified that this works. Story 1's "keep Builds' NuGet publishing working across the rename" matches.
