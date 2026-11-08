---
reviewer: adversary
pass: 3
lens: construct two units one level down (stories in spec-cicd/stories.yaml, built independently by agents reading the spine and their story) that each obey every AD to the letter yet build incompatibly
target: ../ARCHITECTURE-SPINE.md (update U1–U4, updated 2026-11-08)
scope: today's diff only (Precedence rule, AD-19 interim builds-release.yml, AD-20 conditions and end state, schema convention, builds_tag -> buildsTag)
previous: review-adversary.md, review-adversary-pass2.md
date: 2026-11-08
---

# Adversarial review, pass 3: Hexalith.CiCd architecture spine (update U1–U4)

## Verdict

**Pass with fixes. No Critical.** Restating the ADs as conditions holds up: no AD now depends on story order to make sense. The holes are in what the new rules leave unsaid:

- **The schema rules.** They fix the `schema` value but not three things:
  - which Builds versions read which value;
  - which readers may stop on an unknown value before the repair step runs;
  - how a setup file that lacks two required keys gets validated.
- **The AD-20 end state.** It defines `.github/workflows/` only. "Legacy", "moved" and "the guard's commitlint runs in builds-ci.yml" have no checkable meaning outside that directory, and inside it they meet Builds' own self-calls.

There are three High holes:

| ID | Hole |
| --- | --- |
| H1 | An unknown `schema` stops the readers that would repair it. |
| H2 | Setup-file validation cannot be built as written, and it leaves a per-module `buildsTag` pin open. |
| H3 | Builds' own CI and release run the guard against Builds. Builds has no perimeter, and AD-10 puts every NuGet audit waiver in Builds. |

## Grounding checks (run against `references/Hexalith.Builds` @ `3c809618` and the GitHub org)

- **The interim green check exists twice.**
  - `Tools/verify-g4-release-source.sh` (lines 29 and 45) hard-codes `actions/workflows/ci.yml/runs` and `.path == ".github/workflows/ci.yml"`.
  - The second copy is `Get-VerifiedSourceCiRun` in `Tools/G4PackageQualification.functions.ps1` (lines 45 and 57), which hard-codes the same path. It runs when semantic-release's `verifyReleaseCmd` (`Tools/verify-g4-tool-release.ps1`) receives `HEXALITH_G4_SOURCE_CI_RUN_ID`, and `build-release.yml` passes that variable.
- **Tests that read the renamed files by name:**
  - `Tools/test-self-ci.py:21` (`WORKFLOW.with_name("build-release.yml")`);
  - `Github/commitlint/tests/test_commitlint_workflow.py`;
  - `Github/publish-containers/tests/test_publish_script_contract.py`;
  - `Github/prepare-module-build/tests/test_prepare_module_build.py:352`.

  The last three sit inside composites that module-called workflows reference, so AD-20 freezes them.
- **`build-release.yml` itself:**
  - runs under `environment: production`, which has required reviewers (pass-2 grounding);
  - reads `vars.NUGET_USER`;
  - uploads no `hexalith-release-outcome`;
  - runs semantic-release core with `@semantic-release/exec` and `@semantic-release/github`, so the tag is pushed before `publishCmd`.
- **Frozen workflows pin third-party actions by tag:**
  - `codeql.yml` ×3, `commitlint.yml` ×2, `dependency-review.yml` ×2, for example `actions/checkout@v7.0.1`;
  - the spine's zizmor config hash-pins every action outside `Hexalith/*`.
- **Unmanaged org callers.**
  - 14 non-archived Hexalith repos outside the managed 18 reference `Hexalith/Hexalith.Builds/` in workflows: Applications, ChatClient, Documents, Domains, EventStores, GitStorage, IdentityStores, KeyValueStorages, MyNewModule, MyNewPackage, NetAspire, Security, Security_OLD, Streams.
  - All 8 sampled call `Github/package-release@main`. Security also calls `Github/publish-container-to-registry@main`.
  - No managed module and no module-called workflow references either composite.
- **Builds keeps old schema versions next to new ones.**
  - `schemas/` ships `module-manifest` v1 and v2, and `runtime-toolchain-evidence` v1 and v2.
  - That is the "existing convention" the new Schemas row adopts.
- **`job.workflow_ref` is available.** Builds' `.github/actionlint.yaml` records that GitHub exposes `job.workflow_repository/sha/ref/file_path` at run time.
- **Builds has no audit waivers yet.** No Builds MSBuild file has `NuGetAuditSuppress` or a `NoWarn` for NU1903/NU1904; `Hexalith.Build.props:33` uses `WarningsNotAsErrors`. The first waiver arrives with the pilot (AD-21 step 2).

## Prior items that today's change reopened or left open

| Item | Status | Here |
| --- | --- | --- |
| pass-2 L6 (`builds_tag` vs setup validation) and H6 (Builds' own file, `builds_tag` optional) | Reopened and widened: now two keys, and the convention makes `schema` required | H2 |
| pass-2 C1 fix (versioned perimeter) | Landed as `schema`, but nothing bounds pinned guards reading newer perimeters | M1 |
| pass-2 H7 (freeze scope: composites that modules call directly at `@main`) | Still open in today's rewording; now also covers unmanaged repos | M3 |
| pass-1 M11 and pass-2 M8 (self-test vs guard) | New angle through AD-20's commitlint condition and AD-10's waivers | H3 |

## Pairs tried

| Requested shape | Result |
| --- | --- |
| Stories 4, 5 and 6 on how `schema` is checked across a Builds minor and major | H1, M1, M6 |
| Stories 2, 1, 3 and 8 on the interim | M2, L5, L7. The nuget.org policy holds: a no-environment policy accepts the interim, verified in memlog 2026-11-08. The ruleset holds because the cut comes before the rename. Ownership of `builds-release.yml` holds: created at the rename, rewritten later, both in AD-19. |
| Stories 2 and 5 vs story 27 on Builds `.github/workflows/` | H3, M3, M4, M5, L1, L6. These hold: `ci.yml` and `build-release.yml` go in one change; `candidate-policy.yml` and `eventstore-maintenance-publisher.yml` have no replacement and go in the final deletion, as story 27 also says. |
| Validating a setup file that lacks `schema` and `buildsTag` | H2 |

## Tier counts

| Tier | Count |
| --- | --- |
| Critical | 0 |
| High | 3 |
| Medium | 6 |
| Low | 7 |

---

## High

### H1. An unknown `schema` stops the readers that would repair it

- **Units:**
  - **Story 2:** the reusable `ci.yml` loads `hexalith-ci.json` at job start for `solution`, the knobs and the hook `if:` conditions.
  - **Story 5:** the guard, and the restore job that runs after a guard failure on `main`.
  - **Story 7:** delivery.
  - **Story 6:** `check.py`.
- **Each obeys:**
  - AD-1: CI reads `hexalith-ci.json` from the checkout.
  - AD-4 (today): "Every reader (guard, restore, delivery, `check.py`) fails with a fixed message on an unknown `schema` value in the perimeter or `hexalith-ci.json`."
  - Each story implements that rule as written:
    - Story 2 loads the config first and stops with "unsupported schema …".
    - Story 5's restore checks the module file's `schema` before it applies the perimeter.
    - Story 7 checks the live copy before it applies.
  - AD-15: `check.py` "first checks" the gitlink against `buildsTag`, but it reads `buildsTag` from the same JSON.
- **Clash:**
  - **Agents can write the file.** `.github/hexalith-ci.json` sits outside `.github/workflows/`, so a module-agent token (Contents write) or any App-based agent can write it.
  - **Two ways to break it.**
    - Set `schema` to any other value.
    - Leave a merge-conflict marker in it. A branch that edited the file conflicts with every bump, because each bump changes `buildsTag`.
  - **Nobody repairs it.**
    - CI stops at config load, before the guard, so no drift is reported.
    - If restore runs anyway, AD-4 makes it fail on the file it has to overwrite.
    - If delivery checks the live copy, it fails every hour.
    - The module stays red with no automated repair. This is the one kind of drift the reconcile loop cannot fix.
  - **The fixed message invites the edit.** "this Builds version reads `hexalith.ci.v1`" tells an agent which value to type into an owned file.
  - **`check.py` variant.**
    - After a major, a developer merges `main` but doesn't run `git submodule update`. `check.py` then runs the old Builds code from the checked-out submodule.
    - It meets the new `schema` before it can compare the gitlink.
    - The agent "fixes" the owned file instead of updating the submodule.
  - **Lockstep risk.** AD-8's "running workflow's tag" has no named source. The easiest one to reach is `buildsTag` in the module's file, which an agent can edit. Using it would let restore split the lockstep set again (pass-2 M1).
- **Severity:** High.
- **Closing rule (AD-4: replace the reader sentence; AD-8, AD-15):**

  > Readers that configure from a document (CI, release, `check.py`) stop with the fixed message on an unknown `schema` or entry kind, but only after the step that repairs or explains it:
  > - in CI, after the guard's perimeter comparison;
  > - in `check.py`, after comparing the `HEAD` gitlink with the checked-out submodule commit, which needs no JSON.
  >
  > Restore and delivery never parse the module's copy of an owned file; they compare blobs and overwrite.
  >
  > A module `hexalith-ci.json` that cannot be read is drift: the ownership message, then restore.
  >
  > The running tag comes from the workflow's own ref (`job.workflow_ref`), never from the module's `hexalith-ci.json`.

### H2. Setup files cannot be validated as written, and a setup-level `buildsTag` escapes lockstep

- **Units:**
  - **Story 2:** writes `schemas/hexalith.ci.v1.json` and Builds' hand-written `.github/hexalith-ci.json`.
  - **Story 4:** setup handling, render and validate.
  - **Story 6:** `check.py`.
- **Each obeys:**
  - The Schemas row says "every document carries the required `schema`", so story 2 puts `schema` in `required`. AD-1 lists `buildsTag` as part of the config, and AD-9 and AD-15 read it, so story 2 requires it as well.
  - AD-3: "A setup file is `hexalith-ci.json` without `schema` and `buildsTag`, which the render adds. It is validated against … `hexalith.ci.v1.json` …, and unknown keys fail."
- **Clash:**
  - **Day one.** Validated as written, every setup file fails with "'schema' is a required property". Story 4 has to invent a method, and the three obvious ones behave differently:
    1. inject both keys, then validate;
    2. drop them from `required` in memory;
    3. validate only the rendered file.
  - **A setup file can pin its own tag.**
    - With methods 1 and 2, a setup file carrying `buildsTag: v5.3.0` passes. The key is known to the schema, so "unknown keys fail" never fires, and no rule says a setup file must not carry it.
    - **If the render keeps the setup value:**
      - one module is pinned to its own tag;
      - the gitlink and `hexalith-ci.json` sit at v5.3.0, through the AD-4 gitlink entry;
      - the callers sit at `builds-version`, from the templates.
    - That puts two Builds versions in one module and breaks AD-9 and AD-10. `check.py` still passes, because the gitlink equals `buildsTag`.
    - **If the render overwrites it,** the override silently never applies, which AD-3's own Prevents rules out.
    - The same applies to a setup-level `schema`.
  - **Builds' own file.** It is "in the same schema". If `buildsTag` is required, Builds must commit a tag for itself. That tag can only be stale, since Builds' own tag is created after the commit, and the AD-9 fallback would check it out in the self-test (pass-2 L9).
  - **No source for the `schema` value.** It could be a `render.py` constant, a template, or the schema file's `const`. AD-10's major ("changes `builds-version` and the templates together") updates only the template case.
- **Severity:** High.
- **Closing rule (AD-3):**

  > Validate composes each module's `hexalith-ci.json` (the setup values verbatim, plus `schema` and `buildsTag`) and validates that document against the schema at `builds-version`.
  >
  > A setup file that contains `schema` or `buildsTag` fails validate.
  >
  > The render takes `buildsTag` only from `builds-version`, and `schema` from the schema file's `const` at `builds-version` (M1).
  >
  > The schema requires `schema`. `buildsTag` is:
  > - optional in the schema;
  > - written by every render;
  > - required by every module-side reader (guard, restore, `check.py`);
  > - absent from Builds' own file.

### H3. Builds' own CI and release run the guard against Builds, which has no perimeter and holds every audit waiver

- **Units:**
  - **Story 2:** `builds-ci.yml` calls the reusable `ci.yml` against Builds itself and against `Samples/`.
  - **Story 3:** rewrites `builds-release.yml` "to mirror the module `release.yml`".
  - **Story 5:**
    - the guard, including the NU1903/NU1904 waiver ban;
    - the release's drift check (AD-17 step 1);
    - the AD-20 deletion of `commitlint-caller.yml`.
  - **Story 11:** moves the pilot's NuGet audit waivers into Builds' `Props/`.
- **Each obeys:**
  - AD-8: "The guard is stage 1 of every CI run", and it fails on `NuGetAuditSuppress` in module MSBuild files.
  - AD-17 step 1: the reusable release re-runs the guard check on the release SHA against `delivered`.
  - AD-19:
    - Builds is "never … guarded";
    - `builds-ci.yml` calls `ci.yml` against Builds itself;
    - `builds-release.yml` mirrors the module caller.
  - AD-10: waivers exist only in Builds' `Props/`.
  - AD-20 (today): `commitlint-caller.yml` goes "once the guard's commitlint runs in `builds-ci.yml`".
- **Clash:**
  - **No Builds perimeter.** `delivered` has no `rendered/Hexalith.Builds.perimeter.json`. Story 5's guard and release drift check can do one of two things:
    - **Fail.** The first Builds release after story 5 goes red, so no tag ever ships story 5's own guard.
    - **Skip on a missing perimeter.** The guard then fails open for any module whose perimeter is absent: after a rename, a case mismatch, or an offboarding race.
  - **A Builds fixture turns red later.**
    - AD-19 reads as if both calls take the test-only inputs. If story 2 gives the Builds-self call a fixture through `expected-source`, the full guard runs over Builds' MSBuild files.
    - That stays green until story 11 moves the first waiver into `Props/`, as AD-21 step 2 orders.
    - From then on, `builds-ci.yml` is red. The green check fails every Builds release, including the one that carries the waiver the pilot's release audit needs.
    - `builds-release.yml`'s drift check fails the same way.
  - **No defined place for "the guard's commitlint runs in `builds-ci.yml`".** If the Builds-self call skips the guard, story 5 might call the condition unmet and keep `commitlint-caller.yml`, so commitlint runs twice. Or it might call the condition met and delete it.
- **Severity:** High.
- **Closing rule (AD-19):**

  > In Builds' own repository (`github.repository` is `Hexalith/Hexalith.Builds`), the guard and the release's drift check run only when `module-root` is set: that is, in `builds-ci.yml`'s `Samples/` call, against the fixture perimeter. That call's commitlint over Builds' commit range is "the guard's commitlint in `builds-ci.yml`".
  >
  > In any other repository, `module-root` and `expected-source` are rejected, and a missing perimeter on `delivered` fails the guard.
  >
  > This rule names Builds itself, not a module, so AD-2 holds.

---

## Medium

### M1. The `schema` value does not say which Builds versions read a document

- **Units:**
  - **Story 4:** the perimeter schema and library, the render, validate.
  - **Story 5:** the guard and restore, pinned at the module's tag.
  - **Story 6:** `check.py`.
  - **A future story** that ships `hexalith.ci.v2` or extends the perimeter.
- **Each obeys:**
  - AD-4: "A new schema version is a Builds major."
  - AD-3: "Adding a knob is a minor Builds release."
  - The Schemas row adopts "Builds' existing convention".
  - AD-8's restore rule ("only when the perimeter's tag equals the running workflow's tag") shows that pinned guards read perimeters rendered for a newer `builds-version` by design.
- **Clash:**
  - **Minor.**
    - Every minor shares `hexalith.perimeter.v1`, so the `schema` check can't tell a T1 guard that a T2 perimeter holds a kind it doesn't know.
    - Story 4 adds an entry kind in a minor, since a new kind is "not a new version".
    - T1 readers then fail with "unknown entry kind": guards in skipped modules, guards on non-`main` branches, and local `check.py` runs.
    - Or a T1 reader ignores a new optional field and judges drift differently from T2 delivery (the pass-2 M9 pattern).
  - **Major.**
    - The existing convention keeps old schema files next to new ones, so the story that ships `hexalith.ci.v2` keeps `v1.json`.
    - CiCd validate follows AD-3's literal `schemas/hexalith.ci.v1.json` and stays green at T3, and `render.py` still writes `hexalith.ci.v1`.
    - After delivery, every module's CI stops with "unsupported schema `hexalith.ci.v1`, this Builds version reads `hexalith.ci.v2`". Validate approved an org-wide outage.
  - **Readers diverge.** The fixed message reads one `<schema>`, yet a reader that follows the convention might accept both versions. Four readers can each choose differently.
  - **Rollback.** A rollback across a major (AD-10) leaves v2 templates and the v2 `schema` value on a v1 tag.
- **Severity:** Medium. The major case is rare and deliberate. The minor case only hits stragglers: skipped modules, stale branches, local runs.
- **Closing rule (AD-4 and AD-10; Schemas row):**

  > Each Builds tag ships exactly one `hexalith.ci.v<N>.json` and one `hexalith.perimeter.v<N>.json`. Every Builds reader accepts exactly the `const` of the file at its own commit.
  >
  > The perimeter schema is closed per version: a new entry kind or field is `v<N+1>` and a Builds major.
  >
  > `hexalith.ci.v<N>` may gain optional knobs in a minor.
  >
  > The render and validate take the schema file name and the `schema` value from `builds-version`.
  >
  > A rollback across a major reverts that major's adoption commit.

### M2. The interim `builds-release.yml` cannot pass its own green check, and nothing stops nightly from waiting on it

- **Units:**
  - **Story 1:** preconditions, and "keep Builds' NuGet publishing working across the rename".
  - **Story 2:** the rename and the interim.
  - **Story 3:** the rewrite.
  - **Story 8:** nightly.
- **Each obeys:**
  - AD-19: the interim is the renamed legacy file, "with its green-CI check pointed at `builds-ci.yml` and its publishing unchanged", and it is rewritten "before `nightly.yml` dispatches it".
  - AD-18: nightly dispatches `builds-release.yml`, "polls every 60 seconds until all runs complete", and reads `hexalith-release-outcome`.
- **Clash:**
  - **The repointed check is overruled downstream.**
    - Story 2 repoints `Tools/verify-g4-release-source.sh`, the check visible in the workflow.
    - "Publishing unchanged" then runs semantic-release, whose `verifyReleaseCmd` re-verifies the CI run through `Get-VerifiedSourceCiRun`. That function rejects any run whose path is not `.github/workflows/ci.yml`.
    - The interim fails at `verifyRelease`. Builds has no release path until story 3.
  - **Tests break at the rename.**
    - Tests that read `build-release.yml` or `ci.yml` by name break.
    - Three of them sit in composite directories that AD-20 freezes, so a story 2 that follows AD-20 literally cannot edit them.
  - **Nightly can wait forever.**
    - Story 8 cannot check the condition "before `nightly.yml` dispatches it".
    - If the rewrite slips (story 3 carries two spikes), nightly dispatches a run under `environment: production`, which has required reviewers.
    - The run waits for approval, never completes and uploads no outcome.
    - Nightly polls until the 6-hour job limit, and the bump never runs.
- **Severity:** Medium.
- **Closing rule (AD-19 and AD-18):**

  > The rename repoints every check of the CI workflow path on the interim's publish path: `verify-g4-release-source.sh`, and `Get-VerifiedSourceCiRun` in `G4PackageQualification.functions.ps1`. It also retargets or deletes the tests that read the renamed files. Tests and docs of frozen files are not frozen.
  >
  > Nightly counts a dispatched run as `failed` if it is incomplete after 5 hours, or complete without `hexalith-release-outcome`, and the bump still runs.

### M3. "Until the last module has moved" leaves callers outside the 17 unprotected and deletable

- **Units:**
  - **Stories 2–5:** change Builds' `Github/` under the freeze.
  - **Story 27:** the legacy deletion, which its story calls "the legacy actions".
  - **Against:** 14 non-archived org repos outside the managed set.
- **Each obeys:**
  - AD-20 freezes "every Builds workflow that modules call today, and every composite, action and script those workflows reference … until the last module has moved".
  - "Modules" means `setup/*.yml` (AD-3). The AD title says "caller", but the rule says "module".
- **Clash:**
  - **Two composites are unfrozen but in use.** No managed module and no module-called workflow references `Github/package-release` or `Github/publish-container-to-registry`, so neither is frozen. All eight sampled unmanaged repos call `package-release@main`.
  - **What can happen to them:**
    - Any story can change them, and those repos' releases break at once.
    - Story 27's "legacy actions" deletes them.
  - **The pass-2 H7 gap is still open.** Composites that managed modules call directly also stay outside the freeze: `initialize-dotnet` ×21, `prepare-domain-release` ×7, `verify`, `create-release`.
  - **"Moved" is undefined.** It could mean adopted (AD-18) or done (AD-21 step 4).
- **Severity:** Medium. Out-of-scope repos break. For managed modules, see pass-2 H7.
- **Closing rule (AD-20):**

  > The freeze covers every file under `.github/workflows/` and `Github/` that a non-archived Hexalith repo references today, directly or through another frozen file.
  >
  > It ends when an org-wide code search for `Hexalith/Hexalith.Builds/` finds only exact-tag references to end-state files, or when the maintainer has archived or explicitly dropped each remaining caller.
  >
  > The title and the rule both say "caller".

### M4. `builds-ci.yml`'s linters fail on the frozen workflows for the whole migration

- **Units:**
  - **Story 2:** `builds-ci.yml` runs actionlint and zizmor with the committed config.
  - **Against:** the AD-20 freeze and story 27.
- **Each obeys:**
  - The Action references convention: zizmor "ref-pin `Hexalith/*`, hash-pin all others".
  - AD-20: `codeql.yml`, `commitlint.yml` and `dependency-review.yml` stay unchanged until the last caller moves.
- **Clash:**
  - **The frozen files fail the scan.** They pin `actions/*` by tag (7 references), so zizmor's `unpinned-uses` audit fails whenever it scans `.github/workflows/`.
  - **Every Builds release is blocked.** `builds-ci.yml` stays red from the rename until story 27, and the green check fails every Builds release.
  - **Exclusions have no owner.** Story 2 will add exclusions ad hoc, but nothing says which files, or who removes the exclusions later.
  - **The interim must pass too.** The interim `builds-release.yml` is also tag-pinned, and as an end-state file it has to pass.
- **Severity:** Medium. It is visible at once, but the exemption has no owner.
- **Closing rule (AD-19):**

  > Until the legacy deletion, actionlint and zizmor in `builds-ci.yml` lint exactly the AD-20 end-state workflow files and `Samples/`. The rename hash-pins the interim `builds-release.yml`.

### M5. "Legacy" has no end state outside `.github/workflows/`

- **Units:**
  - **Stories 2, 3 and 5:** may reuse an existing composite or script unchanged, which AD-20 allows.
  - **Story 27:** deletes "the legacy actions".
- **Each obeys:** AD-20's Binds now include `Github/` and `Tools/`, but the end state and "everything else" are defined only for `.github/workflows/`.
- **Clash:**
  - **Reuse, then deletion.**
    - Story 2's `prepare` reuses `Github/initialize-dotnet` unchanged. That is allowed, because frozen means unchanged, not unused.
    - Story 27 deletes it as a legacy action.
    - The next Builds tag breaks `prepare`, on the Windows `jobs` path that `builds-ci.yml` may not cover.
  - **Or story 27 keeps every composite,** and these outlive the migration — the very outcome AD-20 now lists under Prevents:
    - the G4 scripts that only the interim used;
    - the semantic-release core/exec/github config in Builds' root `package.json`;
    - `Github/package-release` and dozens of other legacy composites.
- **Severity:** Medium.
- **Closing rule (AD-20):**

  > The legacy deletion also covers `Github/`, `Tools/` and Builds' root npm release config:
  > - it removes what only legacy workflows, the interim release or external `@main` callers reach;
  > - it keeps what an end-state workflow reaches.
  >
  > The new pipeline may reuse an existing composite only unchanged, and the deletion then keeps it.

### M6. Six readers, no shared loader, and nobody named to apply the defaults

- **Units:**
  - **Story 2:** CI reads `dapr`, `browsers`, `registry`, `tests` and `hooks`.
  - **Story 3:** the release reads `codeql` and `solution`.
  - **Story 5:** the guard reads `hooks` and `jobs`.
  - **Story 6:** `check.py`.
  - **Story 4:** validate, with jsonschema in CiCd.
- **Each obeys:**
  - AD-4 (today) makes the guard, restore, delivery and `check.py` each check `schema`. AD-1 adds CI and the release as readers, but AD-4's list leaves them out.
  - AD-11: the Builds runtime is stdlib-only, so Builds readers cannot run the JSON Schema. CiCd validates with jsonschema.
  - AD-3: `codeql` defaults to `[csharp]`, or `[]` with `solution: none`. The render adds only `schema` and `buildsTag`, so nobody materializes the defaults.
- **Clash:**
  - **Missing defaults.** Story 3 reads `config["codeql"]`, assuming the render filled it in. AI.Tools has `solution: none` and no `codeql` key, so the release either:
    - raises a `KeyError`; or
    - applies a `[csharp]` default that ignores the `none` rule, so CodeQL fails every night (pass-2 M7 again, through where the default lives).
  - **Different acceptance.** Story 5 checks `schema` by prefix, story 6 by exact match. `check.py` and CI then accept different documents (CAP-3).
  - **Validate and runtime disagree.** jsonschema accepts what a hand-written stdlib reader rejects, so validate is green while modules go red.
- **Severity:** Medium.
- **Closing rule (AD-1 and AD-4):**

  > Builds' `Github/lib/` holds one stdlib loader per document type:
  > - CI, release, guard, restore and `check.py` use it, and delivery uses it from the Builds clone;
  > - it checks `schema` (M1), rejects unknown keys and applies the AD-3 defaults.
  >
  > `builds-ci.yml` runs the loader and the JSON Schema over the same valid and invalid fixtures.

---

## Low

- **L1. Stage 1 "Guard and commitlint" has two owners.**
  - **Units:** Story 2 implements AD-12 stage 1 and may ship a commitlint step. Story 5 builds commitlint into the guard (AD-8).
  - **Clash:**
    - Commitlint runs twice on every module push, possibly with two configs.
    - Either story could claim to be "the change that ships" `commitlint-caller.yml`'s replacement.
  - **Rule (AD-12):** "commitlint is part of the guard composite; the reusable `ci.yml` has no other commitlint step."
- **L2. Story 6 still says `builds_tag`.** Memlog 95's upstream edit is still pending.
  - **Units:** Story 6 against stories 2 and 4 (`buildsTag`).
  - **Clash:** A story-6 agent's `.get("builds_tag")` returns `None`. A lenient implementation then skips the pointer check and fails open.
  - **Rule (AD-15):** "`check.py` fails when `buildsTag` is missing; no reader defaults a required key." Land the `stories.yaml` edit before story 6.
- **L3. "JSON keys in camelCase" vs maps keyed by data.**
  - **Units:** Story 2 (schema) against story 4 (render).
  - **Clash:**
    - `jobs` keys are kebab-case job names, and `tests.exclude` keys are `.csproj` paths.
    - Story 2 may enforce camelCase `propertyNames`, or reshape both as lists of objects, while story 4 renders AD-3's maps.
    - Validate catches the mismatch, but one story has to redo its work.
  - **Rule (Schemas row):** "camelCase applies to property names the schema defines; map keys that are identifiers keep their own convention (kebab-case names, `/` paths)."
- **L4. The release outcome is a cross-repo document outside the convention and the public API.**
  - **Units:** Story 3 (writes it) against story 8 (reads it).
  - **Clash:** Builds code writes the outcome at two versions on the same night:
    - modules write it at their `buildsTag`;
    - `builds-release.yml` writes it at Builds `main` (local `./`, AD-9).

    Any Builds commit can change the format, and nightly would then misread one side.
  - **Rule (AD-17 and AD-10):** "`hexalith-release-outcome` holds one `outcome.json` with `schema: "hexalith.release-outcome.v1"`, `outcome` and `version`, validated by `schemas/hexalith.release-outcome.v1.json` (public API)."
- **L5. The interim can leave an orphan tag.**
  - **Units:** Story 2's interim against story 3's state machine.
  - **Clash:**
    - The interim keeps semantic-release core, which pushes the tag before `publishCmd`.
    - A failed interim publish leaves an orphan `v*` tag, and the rewritten release counts it as released.
    - AD-19's preconditions lack AD-21's "delete any draft or tag left by an incomplete legacy release".
  - **Rule (AD-19):** "Before the first release from the rewritten `builds-release.yml`, every Builds `v*` tag has a published release, or the tag is deleted."
- **L6. "Everything else outside the end state" also catches legitimate additions.**
  - **Units:** Any story that adds a Builds workflow (for example, a fallback from a story-3 spike) against story 27.
  - **Clash:** Story 27 deletes the added workflow.
  - **Rule (AD-20):** "The end state is the state right after the legacy deletion. A reusable workflow added later is a Builds API change (AD-10) and extends this list."
- **L7. The interim's legacy settings can be tidied away.**
  - **Units:** Story 1 against story 2's interim.
  - **Clash:**
    - The interim reads `vars.NUGET_USER` and environment `production`.
    - While meeting AD-19's preconditions, story 1 may tidy `NUGET_USER` into the org's `HEXALITH_NUGET_USER`, as the conventions suggest.
    - The interim's `NuGet/login` then fails.
  - **Rule (AD-19):** "The Builds preconditions leave the legacy release settings (`NUGET_USER`, environment `production`) in place until the rewrite."
