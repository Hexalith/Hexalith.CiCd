---
review: reconcile-validate
target: ../ARCHITECTURE-SPINE.md (status final, 21 ADs, 2026-11-08 12:39)
against: [SPEC.md, pipeline-stages.md, enforcement.md, gate-classification.md, module-inventory.md, baseline-and-targets.md, stories.yaml]
spec_state: refreshed spec as committed in 4666c3d "fix: spec" (2026-11-08 13:07). The brief said "uncommitted", but the working tree is clean, so the refresh diff was read with `git show 4666c3d -- _bmad-output/specs`.
decision_logs: [../.memlog.md, ../../../../specs/spec-cicd/.memlog.md]
date: 2026-11-08
---

# Reconcile validation: the final spine against the refreshed SPEC-cicd

## Verdict

**PASS WITH FIXES.** The refresh brought the spec into line with the spine on every cited AD and name, and every item in the spine's "Upstream for bmad-spec" direction landed. Story order satisfies every AD ordering condition as written. One high finding remains: CAP-15's "no Builds test asserts workflow text" has no owner, and AD-20 lets those tests be repointed instead. Seven medium findings are partial landings or ordering preconditions that can lapse.

**Counts:** 0 critical, 1 high, 7 medium, 9 low.

---

## Coverage

Status values:
- **landed:** carried by an AD, a convention, the seed or a Deferred item.
- **partial:** carried, but a quiet part is missing.
- **dropped:** carried by nothing.
- **contradicted:** an AD says otherwise.

### Capabilities (SPEC.md)

| Spec item | Carried by | Status |
| --- | --- | --- |
| CAP-1: rendered `ci.yml` + `hexalith-ci.json` in all 17; v1/v2 deleted; workflows dir rendered only; Builds runs it from `builds-ci.yml` | AD-1, AD-4 (`whole-dir`), AD-12, AD-19, AD-20 | landed |
| CAP-2: stop at the failing project, every test in it runs, p90 ≤ 10 min | AD-12 stage 3, AD-13; target in baseline | landed ("every test inside still runs" is in the spec only, and no AD contradicts it) |
| CAP-3: one command matches CI stages 1–3 | AD-15, AD-13 (one classifier) | landed |
| CAP-4: re-render gives no diff; enabling an action is a setup-only change; one `build(cicd)` commit only on a diff; restore is the exception | AD-3, AD-5, AD-6, AD-8 | landed |
| CAP-4: a skipped module keeps enforcing its last accepted render | AD-6 step 1 (`delivered/<Repo>` not advanced) | landed |
| CAP-4: onboarding, then delivery, guard, scheduler, scan | AD-21, AD-18 ("adopted"), AD-3 | landed |
| CAP-5: three hook points; no re-setup; browsers/Dapr in the main job; Windows job after the main job | AD-12, AD-14 | landed |
| CAP-6: no two versions; rollback holds; a bump never releases | AD-9, AD-10, AD-17 (dispatch-only) | landed |
| CAP-6: all modules on the new tag "within one night" | AD-10, AD-18 | partial (S-9) |
| CAP-7: token pushes to workflows and dispatches refused | AD-7 | landed |
| CAP-8: PR fails with diff + message; restore + skip set; release drift check | AD-8, AD-17 step 1, Conventions (fixed message) | landed |
| CAP-8: what restore skips is gone "within 1 h" | AD-6, AD-8 l.214 | partial (S-4) |
| CAP-9: deny list; nightly scan names code; zero fragments | AD-8, AD-18, AD-3, AD-14, Deferred (story 9) | landed |
| CAP-10: module gates and YAML tests removed; kept checks become custom actions | AD-21 step 2, AD-14 | landed |
| CAP-10: applied to Builds' own CI jobs | AD-11, AD-20 l.429 | partial (S-2) |
| CAP-11: marker block in the three instruction files | AD-4 `marker-block` | partial (S-13: file absent) |
| CAP-11: `.claude/settings.json` deny entries, module keeps its allow list | AD-4 `json-superset` l.150 | contradicted by a literal reading of AD-4 l.141 (S-3) |
| CAP-11: AI.Tools guide; `bmad-testarch-ci` absent | story 10; AD-4 `absent-glob` | landed |
| CAP-12: all six success criteria (red main, nothing, kill switch, rerun, tag last, legacy patterns gone) | AD-16, AD-17, AD-4/AD-21 (adoption deletes legacy workflows) | landed |
| CAP-13: release in each module's own tab; failure turns nightly red; kill switch | AD-17, AD-18, Deferred story-3 spike | landed with assumption (S-8, S-14) |
| CAP-14: no push/PR CodeQL; release alerts block; NU1903/4 block; guard rejects waivers | AD-12, AD-17 step 6, AD-18, AD-8 | landed |
| CAP-15: a broken sample fails Builds CI | AD-19 | landed |
| CAP-15: no Builds test asserts workflow text | AD-20 l.423 ("repoints or deletes") | contradicted / no owner (S-1) |
| CAP-15: the only unattended Builds release is nightly; other dispatches are interactive | AD-7 (CiCd token interactive only), AD-18, AD-19 (the legacy `build-release.yml` is already `workflow_dispatch`-only, l.2–3; the rewrite mirrors AD-17) | landed |
| CAP-16: one adoption commit, done condition, all 17, AD-20 end state | AD-20, AD-21 | landed |

### Constraints, non-goals, success signal, assumptions (SPEC.md)

| Spec item | Carried by | Status |
| --- | --- | --- |
| Builds is the runtime; guarded only against the fixture | AD-19, AD-2 | landed |
| "Everything a module's CI and release depend on is committed in the module" | AD-1 l.93 (guard exception) | partial wording (S-12) |
| Delivery is the one writer, restore the exception | AD-6, AD-8 | landed |
| Ownership list, absent list, `.github/actions/**` module-owned | AD-4 table | landed |
| GitHub Free enforcement; org Apps covered by guard, drift check, delivery | AD-7, AD-8, AD-17, AD-6 | landed |
| Direct pushes; careless, not malicious | Paradigm | landed |
| `uses:` is not an expression | AD-12, AD-14 | landed |
| One CI job + two exceptions | AD-12, AD-8 | landed |
| Nothing runs twice (6 bullets) | AD-12, AD-8, AD-16, AD-17, AD-18, AD-20 (rename drops dependency-review) | landed |
| Gate rule | AD-21 step 2, AD-11 | landed |
| Exact tags; `v*` tags can't move ("the AD-21 tag ruleset, applied to Builds by AD-19"); bump and rollback | AD-10, AD-19 l.412, AD-21 l.446 | partial (S-5) |
| Builds release rules; module release rules | AD-10 | landed |
| Dispatch-only, rerun-safe, exact kill switch | AD-17, AD-7 | landed |
| Legacy freeze, unmanaged callers not waited for, Builds-only workflow deleted with its replacement | AD-20 | landed |
| Deny rules per module, never machine-wide | AD-4 (machine-wide is spec-only and not contradicted) | landed |
| Credentials (5 bullets) | AD-7 | landed |
| Actions limits; `pull_request_target` | AD-12, AD-19 (nesting ≤ 2); not used | landed |
| Non-goals 1–11 | AD-20 (unmanaged repos), Deferred (SDK), Seed (no deployment), AD-15 (no pre-push hook), AD-18 (no cascade, summary only), AD-17 (no repack) | landed |
| Success signal 1 ("undone within an hour") | AD-6, AD-8, AD-18 | partial (S-4) |
| Success signal 2 (targets) | Seed re-measurement; story 27 | landed |
| Assumption: standards carry over | Conventions, AD-13, AD-20 end state, story 27 | landed |
| Assumption: "standard module"; re-measurement | baseline; Seed | landed |
| Assumption: CAP-13 own-tab release depends on the story-3 spike | Deferred l.582 | partial (S-8, S-14) |

### Companion rules

| Spec item | Carried by | Status |
| --- | --- | --- |
| pipeline-stages: what Builds keeps; edge-case knobs | AD-20 end state, AD-3, AD-12, AD-13 | landed |
| pipeline-stages: CI table, test stages, `solution: none`, submodules, SDK | AD-12, AD-13, Deferred, Conventions (the order-review rule is a process, spec-only) | landed |
| pipeline-stages: hook points; local check | AD-14, AD-12, AD-15 | landed |
| pipeline-stages: nightly run steps 1–3, 5 h bound, bump whatever the results | AD-16, AD-17, AD-18 | landed |
| pipeline-stages: bump, major adoption includes `setup/`, rollback removes keys | AD-10 | landed |
| pipeline-stages: release propagation; dependency review dropped | AD-10, AD-12, AD-17 | landed |
| pipeline-stages: Builds' own CI (guard only in the `Samples/` call), release without drift check, bootstrap | AD-19 | landed |
| pipeline-stages l.83: "Tests that assert workflow text are dropped" | AD-20 l.423 | contradicted / no owner (S-1) |
| enforcement: Layer 1 | AD-7, AD-21 | landed |
| enforcement: Layer 2 steps 1–5, ruleset on `delivered/**`, known effects | AD-8, AD-6, AD-21, AD-17 | landed |
| enforcement: Layer 3 "each run re-applies the full expected state" | AD-6 l.178 (passing modules only) | partial (S-4) |
| enforcement: "Not used": rulesets "cut back" | AD-21 l.446 | partial (S-5) |
| enforcement: deny list; scan; hoisting; instruction block (incl. the `check.py` bullet) | AD-8, AD-3, AD-18, AD-4, story 10 | landed |
| enforcement l.101: deny entries merged, allow list kept | AD-4 l.150 vs l.141 | contradicted under the literal reading (S-3) |
| gate-classification: rule, keep list, module delete list, "why gates can't come back" | AD-21 step 2, AD-14, AD-13, AD-8, AD-10, stories | landed |
| gate-classification l.33: delete Builds' "Require every validation job to pass" | nothing | dropped (S-2) |
| gate-classification: unclassified module gates | AD-21 step 2; stories 13, 14, 21 name theirs; 17 and 24 don't | partial (S-17) |
| gate-classification l.48: Builds `Props/` validators | AD-11, AD-20 l.429, story 3 | landed |
| module-inventory: managed repos, migration order, AD-21 per migration | AD-19, AD-21, stories 11–26 (order matches exactly) | landed |
| module-inventory: Builds-today rows | AD-19, AD-20, AD-11, Deferred (HXP301) | landed, except l.41 and l.43 (S-11, S-10) |
| module-inventory: drift, release patterns, `production` env, blocking settings, audit bypass wording, 14 unmanaged callers | AD-10, AD-12, AD-17, AD-21, AD-7, AD-8, AD-20 | landed |
| module-inventory l.121: `.claude/settings.json` in 15 of 17 modules | AD-4 | partial (S-13) |
| module-inventory: baseline gaps, toolchain drift, test naming, technical surface, current standard | AD-4 (Dependabot), AD-3, AD-13, AD-14, Conventions, Deferred | landed |
| baseline-and-targets: method, targets, persist row, Releases row | Seed, AD-8, AD-18 | landed; version-spread row partial (S-9) |

### AD ordering conditions against `stories.yaml`

| Ordering condition | Story order | Status |
| --- | --- | --- |
| AD-19 l.412: ruleset cut + nuget.org policy before any CiCd-agent change to Builds | 1 → 2 | satisfied (tag ruleset creation: S-5) |
| AD-19 l.413: App, exact kill switch, org access, no orphan `v*` tag before the first rewritten release | 1 → 3 | can lapse between 1 and 3 (S-6) |
| AD-20 l.427: rename before the reusable `ci.yml` | inside story 2 ("First … Then") | satisfied |
| AD-20 l.428: `commitlint-caller.yml` deleted after the ruleset cut, when the guard's commitlint runs in `builds-ci.yml` | 1 → 5 (story 5 description + invoke) | satisfied |
| AD-20 l.429: legacy jobs and `codeql.yml` call leave, and `Props/` validators are classified, at the `builds-release.yml` rewrite | story 3 | satisfied (aggregator missing: S-2) |
| AD-19 l.410: rewrite before `nightly.yml` dispatches it | 3 → 8 | satisfied |
| AD-19 l.414: bootstrap tag seeds `builds-version` | 3 → 4 | satisfied; that tag lacks the perimeter schema (S-7) |
| AD-21 l.456: CiCd App, key, `main` and `delivered/**` rulesets before delivery | 1 → 7 | satisfied |
| AD-6 l.176: `deliver` after `validate` | 4 → 7 | satisfied |
| AD-6 l.184: 26 h check only once `nightly.yml` has run | 7 (conditional) → 8 | satisfied |
| AD-18: bump waits for delivery; scan before bump, never blocking it | 7 → 8 → 9 | satisfied |
| AD-21 steps 1–4 per module | stories 11–26 `invoke_dev_with` | satisfied (waiver hand-off: S-15) |
| AD-20 l.430: final deletion after all 17 are adopted | 11–26 → 27 | satisfied |
| Story 4 invoke: library released before delivery uses it | 4 → 7 | satisfied for story 7, not for story 4's own validate job (S-7) |

### Deferred items that name a story

| Deferred item | Story text | Status |
| --- | --- | --- |
| Story 3 spike: `GITHUB_TOKEN` publishing a draft behind `main` | story 3 runs it; story 8 has the nightly half | partial (S-8) |
| Story 3 spike: OCI containers, `NuGet/login` in the remote composite | story 3 | landed |
| Story 1: package-mode submodules, then a `submodules` knob | story 1 checks; nobody owns the knob | partial (S-16) |
| Story 2: `$/` failure → AD-9 fallback; story 2 names the Dapr pin file | story 2 is silent on both | partial (S-16) |
| Story 4 Dependabot; stories 2/3/5 composite names; story 8 bot commits; story 9 threshold; story 15 Aspire; story 20 hook secrets; story 27 HXP301 | each in its story | landed |

### Spine memlog "Upstream for bmad-spec" direction (l.108)

| Item | Landed at | Status |
| --- | --- | --- |
| Story 2: ci schema + loader, Builds' file without `buildsTag`, rename repoints identities + tests, drop dependency-review, delete eventstore publisher, frozen composites untouched | stories.yaml l.16–29 | landed (`buildsTag` optional only implied) |
| Story 3: G-4 jobs + `codeql.yml` call out, `Props/` classification, release-outcome schema | l.32–41 | landed |
| Story 4: perimeter schema, loader, complete rendered `hexalith-ci.json` | l.47–53 | landed (ci loader stays with story 2, as the spec memlog notes) |
| Story 5: guard only in the `Samples/` call; `commitlint-caller.yml` after the cut; missing ref/perimeter fails | l.61–75 | landed |
| Story 6: `buildsTag`, gitlink first | l.78–82 | landed |
| Story 7: `delivered/<Repo>`, 26 h conditional | l.87–94 | landed |
| Story 8: 5 h, scan never blocks, conditional ready-draft fallback | l.101–110 (+ story 9 l.118) | landed |
| Story 27: end state, HXP301, 14 unmanaged repos | l.332–344 | landed |
| SPEC.md: CAP-8 tag exception, "never guarded against a delivered ref", per-module delivered | SPEC l.74, l.136, l.49 | landed |
| enforcement.md: `delivered/<Repo>` + ruleset, Layer 2 step 4, `check.py` bullet | l.18–21, l.30–33, l.94 | landed |
| module-inventory.md: Builds rows, 14 callers, audit wording | l.25–46, l.74, l.76–79 | landed (one stale cell: S-10) |
| baseline-and-targets.md: persist row | l.77 | landed |

---

## Findings

### Critical

None.

### High

#### S-1 (high): CAP-15's "no Builds test asserts workflow text" has no owner, and AD-20 permits keeping such tests

- **Spec:**
  - SPEC.md:122 (CAP-15): "No Builds test asserts workflow text."
  - pipeline-stages.md:83: "Tests that assert workflow text are dropped."
  - stories.yaml:18–19 (story 2): "repoint their hard-coded identities and the tests that read them".
- **Spine:**
  - ARCHITECTURE-SPINE.md:423 (AD-20): "A change that renames or deletes a Builds-only workflow also repoints or deletes every test that reads it by name".
  - ARCHITECTURE-SPINE.md:433 (AD-20 end state): "`Github/` and `Tools/` hold only what those workflows and `check.py` use".
- **Evidence:**
  - `references/Hexalith.Builds/Tools/test-self-ci.py:15,20` reads `ci.yml` and `build-release.yml` and asserts their text with `assertIn` and `assertNotIn`.
  - Builds' `ci.yml:290` runs that test.
  - The test sits in `Tools/`, outside the frozen set.
- **Issue:**
  - Story 2 is told to repoint these tests, and AD-20 allows that.
  - No later AD or story deletes Builds' workflow-text tests.
  - The final deletion keeps whatever `builds-ci.yml` still runs, so the end-state rule is circular: a repointed test is "used" and survives.
  - So CAP-15 success 2 never becomes true. Rubric-pass3 H2 raised this, and the spine's resolution ("repoints or deletes") did not close it.
- **Side:** spine (Update), then the story text follows (bmad-spec).
- **Smallest fix:**
  - **AD-20 l.423:** "… also deletes every test that asserts that workflow's text (CAP-15), including tests inside frozen directories, and repoints any other test that reads it by name."
  - **Story 2:** "delete the tests that assert their text and repoint the rest".

### Medium

#### S-2 (medium): Builds' "Require every validation job to pass" delete verdict is scheduled nowhere, and AD-20's list of legacy jobs is too narrow

- **Spec:**
  - gate-classification.md:33: delete Builds' "Require every validation job to pass".
  - SPEC.md:86 (CAP-10): "no job or step checks the CI itself".
  - module-inventory.md:40: G4/G6 scripts go in the final deletion.
- **Spine:**
  - ARCHITECTURE-SPINE.md:429 (AD-20): "The legacy jobs in `builds-ci.yml` (the G-4 qualification jobs and the `codeql.yml` call) leave it in the change that rewrites `builds-release.yml`".
  - stories.yaml:36 (story 3) repeats the same list.
- **Evidence:**
  - The verdict targets the aggregator job `build-and-test`, which holds the step "Require every validation job to pass" (`references/Hexalith.Builds/.github/workflows/ci.yml:23–38`). It `needs` `catalog`, `contracts`, `dotnet` and `python-tests`.
  - The `python-tests` job also runs G-4 and G-6 evidence tests (ci.yml:292–300).
  - `builds-ci.yml` is kept in the end state, so the aggregator survives the final deletion, and so does every legacy test step it still runs (the circularity from S-1).
- **Side:** spine (Update); story 3 follows.
- **Smallest fix:**
  - **AD-20 l.429:** "Every legacy job and step in `builds-ci.yml`, meaning the G-4/G-6 qualification jobs and tests, the `Require every validation job to pass` aggregator (gate-classification.md) and the `codeql.yml` call, leaves it in the change that rewrites `builds-release.yml`."
  - **Story 3:** the same words.

#### S-3 (medium): AD-4's "never parse the module's copy of an owned file" contradicts partial entries and CAP-11's allow-list rule

- **Spec:**
  - SPEC.md:94 (CAP-11): every `.claude/settings.json` "keeps its own allow list".
  - enforcement.md:101: "The entries are merged in, and every other key, including the allow list, stays module-owned."
- **Spine:**
  - ARCHITECTURE-SPINE.md:141 (AD-4): "Restore and delivery never parse the module's copy of an owned file. They compare blobs and overwrite."
  - ARCHITECTURE-SPINE.md:150 and :158: the `json-superset` entry, and "Partial entries are judged semantically and edited minimally".
- **Issue:**
  - The l.141 sentence came from adversary-pass3 H1, which was about `hexalith-ci.json`, a whole-file entry. Its literal scope is now "an owned file", which includes `.claude/settings.json`, the marker-block files and `package.json` (`absent-json`).
  - Stories 4, 5 and 7 build the perimeter library, restore and delivery. A builder who follows l.141 literally overwrites the settings file and erases the module's allow list.
  - The spine contradicts itself here, and one of its two readings breaks CAP-11.
- **Side:** spine (Update).
- **Smallest fix (AD-4 l.141):** "Restore and delivery never parse the module's copy of a whole-file entry. They compare blobs and overwrite. Partial entries are edited as below. A partial file that can't be parsed is drift, and is rewritten from the expected part alone."

#### S-4 (medium): The "within 1 h" bound fails for a skipped module, and for any hour in which the global checks fail

- **Spec:**
  - SPEC.md:75 (CAP-8): "What restore skips doesn't persist beyond the next delivery, within 1 h."
  - SPEC.md:191 (Success signal): "… is undone within an hour".
  - baseline-and-targets.md:77.
  - enforcement.md:33, :41, :48: "Each run re-applies the full expected state".
- **Spine:**
  - ARCHITECTURE-SPINE.md:176 (AD-6): `deliver` runs only after the global checks pass.
  - ARCHITECTURE-SPINE.md:178–183: steps 2 and 3 (apply and push) run only "for each module that passes its own checks". A skipped module gets nothing.
- **Issue:**
  - Take a module skipped because, say, a newly enabled hook's action is not on its `main` yet. Its last accepted render stays in `delivered/<Repo>`, but no one re-applies it.
  - A workflow-file edit by an org agent App therefore persists for as long as the module stays skipped, which can be days.
  - Likewise, a broken commit on CiCd `main` stops all drift repair in every module until it is fixed. Here the red hourly run is at least a signal.
  - CAP-4's new sentence ("keep enforcing its last accepted render") holds for the guard, but the 1 h repair bound does not.
- **Options:**
  - **A (recommended).**
    - **How:** spine AD-6. Step 1 stays conditional on the module's checks. Steps 2–4 apply every module's current `delivered/<Repo>`, so a skipped module is repaired back to its last accepted render. Optionally, on a global-check failure, the `deliver` job still re-applies the existing refs without advancing any.
    - **Pros:** keeps the spec's bound unchanged. The refs are already validated.
    - **Cons:** one more case in `deliver.py`. Applying under a failing CiCd `main` needs the perimeter library from the `builds-version` at that ref.
  - **B.**
    - **How:** bmad-spec qualifies CAP-8 success 3, the Success signal, the baseline row and enforcement l.48: "for a module that delivery reaches. A skipped module stays red until its checks pass."
    - **Pros:** no design change.
    - **Cons:** it weakens a headline guarantee for the commonest skip cause.
- **Side:** spine (option A) for skipped modules. For the global-failure case, apply A's optional clause or add a one-line spec qualifier.

#### S-5 (medium): Nothing creates the `v*` tag ruleset that the refreshed constraint relies on

- **Spec:**
  - SPEC.md:161: "its `v*` tags can't be moved or deleted (the AD-21 tag ruleset, applied to Builds by AD-19)".
  - SPEC.md:102 (CAP-12): "A version is never republished from different content."
  - enforcement.md:53–55: "Existing ones are cut back during onboarding".
  - module-inventory.md:46: Builds has only a `main` ruleset.
- **Spine:**
  - ARCHITECTURE-SPINE.md:412 (AD-19): "the ruleset is cut as in AD-21" (singular).
  - ARCHITECTURE-SPINE.md:446 (AD-21): "cut rulesets to: … `v*` tags block update and deletion".
- **Issue:**
  - "Cut" reduces an existing ruleset. It never creates one.
  - Builds has no `v*` tag ruleset, which rubric-pass2 M15 checked live. Most modules have none either.
  - Read literally, AD-19, AD-21 and enforcement.md never create the protection that the spec's lockstep constraint now cites.
  - There is also an ordering trap: AD-21 l.451 (and AD-19 l.413) delete leftover tags, but a tag ruleset set before that deletion blocks it.
- **Side:** both.
- **Smallest fix:**
  - **AD-21 l.446:** "set rulesets to exactly these, creating missing ones: …". Move the deletion of leftover drafts and tags before it.
  - **AD-19 l.412:** "the AD-21 rulesets, `main` and `v*` tags".
  - **enforcement.md:53:** "Rulesets are set to exactly these during onboarding, created where missing and cut back where stricter."

#### S-6 (medium): AD-19's "no orphan `v*` tag before the first rewritten release" is checked in story 1, but the interim legacy release can create orphan tags before story 3

- **Spec:**
  - stories.yaml:4–8 (story 1) meets "Builds' preconditions (AD-19)".
  - stories.yaml:40–41 (story 3) dispatches the bootstrap by hand.
  - baseline-and-targets.md:99: Builds' `Release` fails 30% of runs.
  - module-inventory.md:43: 44 tags in the last month.
- **Spine:**
  - ARCHITECTURE-SPINE.md:413 (AD-19): before the first rewritten release, "every Builds `v*` tag has a published release, or the tag is deleted".
  - ARCHITECTURE-SPINE.md:409: the interim `builds-release.yml` keeps its legacy publishing.
- **Issue:**
  - The interim legacy release keeps running through stories 2 and 3, and it fails about 30% of the time. A partial run can leave a tag with no published release after story 1 has checked.
  - The new release computes from "the last `v*` tag reachable from the SHA" (AD-17 l.348), so an orphan tag misleads the bootstrap.
  - The condition holds when story 1 ends, but story 3 does not re-check it. With S-5's tag ruleset in place, deleting the orphan also needs a maintainer bypass.
- **Side:** spec (stories.yaml).
- **Smallest fix (story 3):** "…then re-check AD-19's release preconditions (no orphan `v*` tag, exact kill switch) and dispatch the first Builds release by hand to seed builds-version."

#### S-7 (medium): The bootstrap tag ships without the perimeter schema, yet story 4's own validate job needs it at `builds-version`

- **Spec:**
  - stories.yaml:40–41: the story 3 bootstrap seeds `builds-version`.
  - stories.yaml:51–52: story 4 writes `schemas/hexalith.perimeter.v1.json`.
  - stories.yaml:58 (story 4 invoke): "Ship the library in a Builds release before story 7 uses it."
- **Spine:**
  - ARCHITECTURE-SPINE.md:241 (AD-10): "Each Builds tag ships exactly one version of each of those three schemas."
  - ARCHITECTURE-SPINE.md:239 and :109 (AD-3): the global checks validate perimeters against Builds at `builds-version`.
- **Issue:**
  - The story order makes AD-10's literal "exactly one of each" false for the bootstrap tag, and for any tag cut before story 4's Builds release. Neither contains a perimeter schema.
  - The real consequence is inside story 4. Its validate job can't check perimeters until a Builds release containing the schema exists and `builds-version` has been moved to it by hand (an AD-5 commit). The invoke note places that release "before story 7", which is too late.
- **Options:**
  - **A (recommended).**
    - **How:** story 4 invoke: "Ship the perimeter schema, loader and library in a Builds release, and move `builds-version` to it, before the validate job checks perimeters." AD-10 l.241: "at most one version of each".
    - **Pros:** two short edits, and no story moves.
    - **Cons:** story 4 needs one hand dispatch.
  - **B.**
    - **How:** move the perimeter schema and loader into story 2 or 3.
    - **Pros:** the bootstrap tag is complete.
    - **Cons:** it splits story 4's perimeter work, and the library still lands later.
- **Side:** both (spine wording, story text).

#### S-8 (medium): Story 3 doesn't carry the release-side half of the Deferred fallback

- **Spec:**
  - stories.yaml:38–41 (story 3) only runs the spike.
  - stories.yaml:108–110 (story 8) publishes ready drafts with the App.
  - SPEC.md:199: the assumption.
- **Spine:**
  - ARCHITECTURE-SPINE.md:582 (Deferred): "If the spike confirms that, the run ends `ready`, and `nightly.yml` publishes ready drafts".
  - ARCHITECTURE-SPINE.md:356 (AD-17 `publish` step 4): "Publish the draft".
  - ARCHITECTURE-SPINE.md:360: the `ready` outcome.
- **Issue:**
  - If the refusal is confirmed, the reusable release or the `publish` composite must stop before step 4 and report `ready`. Without that, the module's run fails red at step 4 before `nightly.yml` ever sees a ready draft.
  - That change is in Builds (stories 3 and 5 territory), but only story 8's nightly half is written down.
- **Side:** spec (stories.yaml).
- **Smallest fix (story 3):** "If the spike confirms the refusal, the release stops before publishing the draft and reports `ready` (spine Deferred)."

### Low

#### S-9 (low): CAP-6's "within one night" omits the skipped-module exception
- **Location:** SPEC.md:62 and baseline-and-targets.md:74 vs ARCHITECTURE-SPINE.md:179 and :183 (AD-6: a skipped module keeps its previous ref, so it also keeps its previous Builds tag).
- **Issue:** a module that fails its own checks at bump time stays on the old tag. The delivery run is red, but CAP-6 success 2 and the baseline row list only "a new major or a tag in `builds-skip`" as exceptions.
- **Side:** spec.
- **Fix:** add "or a module skipped by its own checks, which the red delivery run reports".

#### S-10 (low): module-inventory still says Builds releases "at most one release a night"
- **Location:** module-inventory.md:43 vs SPEC.md:123 (amended CAP-15) and pipeline-stages.md:84; spine AD-7 l.194 (the CiCd-agent token has Actions write).
- **Side:** spec.
- **Fix:** "Exact-tag references; the only unattended release is the nightly one."

#### S-11 (low): "Final deletion removes it" could mean the root `package.json` itself
- **Location:** module-inventory.md:41 vs ARCHITECTURE-SPINE.md:434 (AD-20: the file "carries no legacy release configuration"), SPEC.md:132 and stories.yaml:336–337.
- **Issue:** Builds' npm pins (AD-4 l.159; the Stack's commit-analyzer, release-notes-generator and commitlint) may live in that file, so deleting it would break them.
- **Side:** spec.
- **Fix:** "Final deletion removes that configuration."

#### S-12 (low): "Everything a module's CI and release depend on is committed in the module" ignores the guard's run-time read
- **Location:** SPEC.md:137 vs ARCHITECTURE-SPINE.md:93 (AD-1: "At run time Builds reads CiCd only for the guard's comparison"), :203 (AD-8) and :344 (AD-17 step 1).
- **Side:** spec.
- **Fix:** append "except the guard's expected state, read from this repository's `delivered/<Repo>` (AD-8)".

#### S-13 (low): AD-4 doesn't say what a partial entry does when its file is absent
- **Location:**
  - **Spec:** module-inventory.md:121 (`.claude/settings.json` exists in only 15 of 17 modules); SPEC.md:92 (CAP-11: "Every module's `AGENTS.md`, `CLAUDE.md`, and `.github/copilot-instructions.md` carry the … block").
  - **Spine:** ARCHITECTURE-SPINE.md:150–151.
- **Issue:** for the deny rules and the blocks to exist in every module, `json-superset` and `marker-block` must create the file when it is missing. The perimeter library (story 4) has no rule for this.
- **Side:** spine.
- **Fix:** add to AD-4: "A partial entry on a missing file creates it holding only the owned part."

#### S-14 (low): The CAP-13 assumption is broader than the spine's refusal condition
- **Location:** SPEC.md:199 ("can publish a draft behind `main`") vs ARCHITECTURE-SPINE.md:582 (refused only "when that commit's workflows differ from the default branch"; "the run ends `ready`").
- **Issue:** neither text says whether the fallback applies to every release or only to refused ones. That decides how much of CAP-13 success 1 and 2 changes.
- **Side:** both.
- **Fix:**
  - **Spine:** "a run whose draft publication is refused ends `ready`".
  - **Spec:** "a draft behind `main` whose workflows differ from `main`'s".

#### S-15 (low): AD-21 gives module agents a Builds change that they can't make, and the waiver timing is unstated
- **Location:**
  - **Spine:** ARCHITECTURE-SPINE.md:452 (AD-21 step 2: module agents move "module NuGet audit waivers to Builds") vs :252 (AD-10: only CiCd agents change waivers) and :193 (AD-7: the module-agent token covers module repos only).
  - **Stories:** stories 11–26 `invoke_dev_with` (e.g. stories.yaml:139–144) split the work correctly.
- **Issue:**
  - The AD text gives module agents work their token can't do.
  - The waiver has to be in the Builds tag at `builds-version` before the adopted module's first nightly release, because that release is AD-21's done condition. Nothing says so.
- **Side:** spine.
- **Fix (AD-21 step 2):** "module agents remove module waivers; a CiCd agent adds them to Builds `Props/`, and they reach `builds-version` before adoption."

#### S-16 (low): Stories 1 and 2 don't name their Deferred follow-ups, and story 2's freeze note omits the test carve-out
- **Location:**
  - **Spine:** ARCHITECTURE-SPINE.md:584 (a `submodules` knob if story 1 finds more submodules), :587 (`$/` → AD-9 fallback in story 2), :589 (story 2 names the Dapr pin file) and :423 (tests inside frozen directories are repointed or deleted).
  - **Stories:** stories.yaml:7–8, :16–25, :26–29 ("Frozen files stay unchanged").
- **Issue:**
  - Nobody owns the knob if story 1's answer is yes.
  - Story 2 mentions neither the `$/` check nor the Dapr pin.
  - Its invoke note would forbid the test edits that AD-20 (and S-1) require inside frozen `Github/prepare-module-build/tests` and `Github/publish-containers/tests`.
- **Side:** spec.
- **Fix (story 2):**
  - Add "verify `$/` (AD-9 fallback if it fails), name the Dapr pin file, and add a `submodules` knob if story 1 found one".
  - In the invoke note: "Frozen files stay unchanged, except tests (AD-20)".

#### S-17 (low): Stories 17 and 24 omit some gates that are not yet classified
- **Location:**
  - **Spec:** gate-classification.md:41 (Folders' drift and policy lanes) and :47 (FrontComposer's "Gate 2b: Infrastructure governance" and "Coverage Summary").
  - **Stories:** stories.yaml:207–211 and :293–298. Stories 13, 14 and 21 do name theirs.
  - **Spine:** AD-21 step 2 carries the rule generically.
- **Side:** spec.
- **Fix:** add "and classify its drift and policy lanes" to story 17, and "and classify Gate 2b and Coverage Summary" to story 24.

---

## Checked with no finding

- **AD numbers and names:**
  - Every `AD-n` citation in the refreshed spec means what the spec uses it for, including AD-17 step 1, the AD-4 loader, AD-11 and AD-19's fixture-only guard. S-5 is the one exception (AD-19's "ruleset" wording).
  - `delivered/<Repo>` is used everywhere, and no bare `delivered` branch remains.
  - `buildsTag`, `schemas/hexalith.ci.v1.json` and `schemas/hexalith.perimeter.v1.json` match.
  - No `builds_tag`, `hexalith-ci.v1`, `hexalith-perimeter` or `format: 1` remains.
- **Restore skip rule:** SPEC.md:74, enforcement.md:30 and baseline:77 match AD-8 l.212 exactly (the perimeter tag against the running workflow's `job.workflow_ref` tag).
- **CAP-15 dispatch wording:** the legacy `build-release.yml` is already `workflow_dispatch`-only (l.2–3), and the rewrite mirrors AD-17's dispatch-only caller. AD-7 confines CiCd-agent dispatches to interactive sessions.
- **Builds' release has no drift check:** pipeline-stages.md:84 matches AD-19 l.407 and l.410. `builds-release.yml` passes no `module-root`.
- **G-4 identity tooling** (`G4PackageQualification.functions.ps1`, `verify-g4-release-source.sh`, `archive-g4-qualification-evidence.py`) is used only by Builds' own workflows and `Tools/`, not by `domain-*` or composite `action.yml` files. Story 2's repointing therefore touches nothing frozen.
- **No module** calls Builds' `ci.yml` or `build-release.yml` by `uses:`, so the rename breaks no caller.
- **Fixed messages, times and bounds** match: the guard message, the four release messages, 02:17, minute 47, 60 s, 5 h, 26 h (spine-only, conditional) and "within one night".
- **Migration order** in stories 11–26 matches module-inventory.md:11–18 exactly.
- **Non-goals:** the spine builds none of them.
