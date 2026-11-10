# Pipeline stages

The stage order and step sequence of each pipeline. Serves CAP-2, 3, 5, 6, 12, 13, 14, and 15. The mechanics are in the architecture spine (AD-12 to AD-19).

## What Builds keeps

- One reusable CI workflow (`ci.yml`): new and minimal, modeled on Commons' 1.6-minute CI.
- One reusable release workflow (`release.yml`), which holds the nightly `codeql` and `nightly-hook` jobs.
- A few composite actions, including `prepare` and `publish`, which callers reference.
- Builds' own `builds-ci.yml` and `builds-release.yml`.

Edge cases become knobs in the setup file or custom actions:
- Dapr, browsers, and a registry login: the `dapr`, `browsers`, and `registry` knobs.
- Aspire AppHost tests: shared stage 4.
- Windows: an extra job.

## CI job (one job, fixed order)

| # | Stage | Typical cost |
|---|---|---|
| 1 | Guard (`enforcement.md`) plus the commit-format check (commitlint) | seconds |
| 2 | Restore, then a Release build in package mode with `-warnaserror`, analyzers included, and NuGet audit off | minutes |
| 3 | Unit tests, project by project. Stops at the first failing project; all tests inside that project still run. | — |
| 4 | Environment setup, run once (Dapr, browsers, registry pull login, as enabled). Then the `after-unit-tests` hook, integration tests project by project, and the `after-integration-tests` hook. | — |

- **Order rule:** cheapest and most likely to fail first. Whenever a stage is added, review the order with the run-history method in `baseline-and-targets.md`.
- **Test stages:** test projects are the solution's projects with `IsTestProject=true`. A name ending in `IntegrationTests`, `Integration.Tests`, or `AppHost.Tests`, or containing `E2E`, goes to stage 4. Everything else goes to stage 3. The setup file can only move a project to stage 4 or hand it to an enabled hook or job. There is never a plain skip (AD-13).
- **`solution: none`:** stage 1 only.
- **Submodules:** CI checks out Builds plus the submodules listed in the module's `submodules` knob, which story 2-3 adds (spine, Deferred). Today `initialize-build` clones every declared submodule, 2–17 per module.
  - Story 1 found, by static reading on 2026-11-08, that a package-mode build or its tests read sibling submodules in 8 modules. They do it through ungated AppHost or test-host references, sibling sources compiled with no condition, root `.slnx` files that list sibling projects, or tests that read sibling files:
    - ChatBot: EventStore, Platform, Tenants, Parties, Projects, Memories, Commons, FrontComposer, Timesheets.
    - Commons: PolymorphicSerializations (root `.slnx`; `Commons.Standalone.slnx` is clean).
    - Folders: Platform (`AppHost.csproj:33-34`), plus Commons, EventStore, FrontComposer, Memories and Tenants in the root `Hexalith.Folders.slnx` (`Hexalith.Folders.CI.slnx` lists none).
    - Parties: EventStore (test hosts, tests).
    - Platform (stale checkout): EventStore, Memories.
    - Projects: EventStore, Tenants.
    - Tenants: Platform (`AppHost.csproj:34-35`), EventStore (tests), plus Commons, EventStore, FrontComposer and Memories besides Builds in the root `Hexalith.Tenants.slnx` (`Hexalith.Tenants.Standalone.slnx` lists none).
    - Works: Platform, Parties (`IntegrationTests.csproj:37-63`).
  - The other 9 (AI.Tools, Agents, Conversations, EventStore, FrontComposer, McpCli, Memories, PolymorphicSerializations, Timesheets) are clean: their sibling references are gated by `'$(UseHexalithProjectReferences)' == 'true'` or by per-dependency `*FromSource` switches.
- **SDK:** comes from `global.json`.

## Hook points

- The hook points are exactly `after-unit-tests`, `after-integration-tests`, and `nightly` (the last runs in the release). Each has one action, at `.github/actions/<hook>`, run only when the setup file enables it.
- There is no hook after the build, so that the local check matches CI stages 1–3 exactly.
- An action that needs browsers or Dapr is a hook with that knob on.
- An action that needs another operating system gets an extra job, rendered into the module's caller. It runs after the main job passes and repeats checkout, restore, and build through `prepare`. It takes `solution` and the other knobs it needs from the main job's outputs, reads no JSON, and sets up no environment. Its action can assume only a restored, Release-built workspace.
- Script hooks through `run:` are not used: they are unstructured and tend to grow into a second pipeline.
- The custom-action contract is in AD-14.

## Local check

- `python3 references/Hexalith.Builds/check.py` runs stages 1–3, with the same scripts and build flags as CI.
- Agents are told to run it before they push.
- There is no pre-push hook: hooks slow every push and can be skipped with `--no-verify`.

## Nightly run

`nightly.yml` in this repository runs at 02:17 UTC as a chain of jobs (AD-18). Jobs that use the App run in `cicd-app` and mint their own tokens.

1. **Dispatch.** It first waits, for at most 30 minutes, until no delivery run on `main` is in progress. A module is adopted when its `delivered/<Repo>` branch exists and its live `main` has `.github/hexalith-ci.json`. Each adopted module whose live `ci.yml` and `release.yml` equal those on its branch gets its `release.yml` dispatched, along with the branch's commit. A drifted module is not dispatched, and fails the night. So do a branch without the file (a failed adoption push) and an adopted module with immutable releases off. Builds' `builds-release.yml` is dispatched too. Anything beyond the Free plan's 20 concurrent jobs waits in GitHub's queue.
2. **Each release run** (AD-16, AD-17). It runs on `main` only:
   1. Resolves the release SHA once. The SHA is that of a marked draft if one exists (complete mode), otherwise the dispatched commit (create mode).
   2. Create mode: checks the owned files against the dispatched `delivered/<Repo>` commit. Drift fails red.
   3. Applies the kill switch: `false` succeeds with "publishing disabled", and any value other than `true` fails.
   4. Create mode: if CI on that SHA isn't green, fails red: "main is red, nothing released".
   5. Runs CodeQL (`build-mode: none`, one job per language) and the `nightly` hook, whatever the kill switch says. An open high or critical alert from this analysis, or a failing hook, blocks the release.
   6. Create mode: if no releasable commit exists since the last tag, succeeds: "nothing to release". Otherwise it builds and packs once with the next version, which is one step above the last tag, or `1.0.0` when there is no tag. Packages with a high or critical vulnerability, or an audit that can't run, fail the build. The packages and uncompressed OCI archives (`packages/*.nupkg`, `containers/*.tar`) are kept as the run's `release` artifact for 90 days. With SDK 10.0.403, it publishes each platform once via single-RID SDK publication and assembles the platform index without changing child/config/layer bytes, avoiding multi-RID source-label truncation.
   7. Create mode: only after the artifact exists, creates a marked draft release naming the SHA, the run, and the artifact. If `main`'s workflows changed during the run, it creates nothing: "workflows changed on main during the release, nothing released".
   8. The caller's `publish` job runs in `hexalith-release`. Its remote `publish` composite validates the original artifact without checkout or building, performs SHA-pinned NuGet/login v1.2.0 inside the composite (no caller-key input), then pushes the NuGet packages (`--skip-duplicate`) and the original OCI archives by version tag with pinned official Skopeo 1.22.3, `copy --all --preserve-digests`. A conflicting registry root fails before any NuGet or registry write and is rechecked before copy; the complete remote graph must match the archive afterward. Signed build provenance is excluded because default publisher identity cannot establish the earlier build on completion/replay; no `attestations: write` permission is added. If the release SHA's workflows equal `main`'s, it publishes the draft, which creates the tag last. Otherwise it ends `ready`, because GitHub refuses that token.
3. **Wait.** It waits for every run, for at most 5 hours.
4. **Publish-ready.** With the App, it publishes each draft whose run ended `ready`, after the same checks. It then writes the pass/fail summary with links. A run passes only when it succeeded with `published`, `nothing`, or `disabled`, or ended `ready` and was published here. A run still going after 5 hours, or one without a readable outcome, counts as failed.
5. **Scan.** It runs the duplicate scan.
6. **Bump.** It bumps Builds (below), whatever the earlier results, then waits up to 90 minutes for the bump's delivery and for each delivered module's CI on that commit.
7. **Keepalive.** It calls GitHub's enable API for `nightly.yml` and `deliver.yml`, and commits `build(cicd): keepalive` after 50 idle days.

The night fails if any release, the publishing of a ready draft, the scan, the bump, its delivery, or the module CI it triggers fails.

- **Reruns:** a rerun completes a marked draft from the `release` artifact of the run that created it, without rebuilding. If that artifact is gone, the draft is deleted when none of its packages or images was published. Otherwise the run fails: "draft vX.Y.Z cannot be completed: its build artifact is gone". The release never commits to `main`.
- **What runs twice:** one compile per released module per night, plus one more for a module with a `nightly` hook.
- **CodeQL trade-off:** moving it to the nightly run removes a quarter to a third of the runs in most repositories. The cost is that a finding can take up to 24 hours to appear, but it still blocks the release.

## Builds version bump

- Modules reference Builds by an exact release tag, never by `@main` or a raw SHA. The tag appears in the callers, in `hexalith-ci.json`, and as the submodule pointer.
- After publish-ready and the duplicate scan, `nightly.yml` moves `builds-version` to the newest acceptable tag (SPEC Constraints) in the current major that isn't in `builds-skip`. It does this on the current tip of this repository's `main`, re-renders, and runs the global checks, with no secret. A failed check pushes nothing and fails the night.
- A separate job pushes `build(cicd): bump Builds to vX.Y.Z` with `GITHUB_TOKEN`, and only when every changed file is `builds-version` or a rendered file whose only change is the old tag replaced by the new one. The one exception is new `hexalith-ci.json` keys set to their schema defaults. That job then dispatches delivery, which ships the bump to every module. A non-fast-forward fails the night, and the next night retries. `build(cicd)` is not releasable.
- A new major is adopted with one commit here that changes `builds-version`, `templates/`, and `setup/` together.
- A rollback sets `builds-version` to the older tag, adds the bad tag to `builds-skip`, and removes setup keys that the older schema lacks. A rollback across a major reverts that major's adoption commit.

## Release propagation

- Dependency bumps are `build(deps)` commits. They don't release; they ship with the module's next releasable change.
- To force a release, for example for a security fix, an agent commits the bump as `fix(deps): …`.
- Hexalith package versions are pinned centrally in Builds' `Props/Directory.Packages.props`. Builds releases on every commit type except `docs`, `test`, and `style`, so a change there always produces a Builds release. Modules receive it through the next bump.
- Known effect: a module's published package keeps referencing an older Hexalith version until that module changes.

## Builds' own CI and release

- `builds-ci.yml` runs `actionlint`, `zizmor`, and the Python tests on its scripts. It checks Builds' public API against the last release tag. It also runs the reusable `ci.yml` twice:
  - against Builds itself, for the build and test stages;
  - against the sample module in `Samples/Hexalith.Sample/`, using test-only inputs that module callers never set. Only this call runs the guard, against the sample's fixture perimeter, and its commitlint covers Builds' own commits. One Windows job, shaped like a rendered one, runs `prepare` on this call's outputs.
- Tests that assert workflow text are deleted in the change that renames or deletes the workflow they read.
- `builds-release.yml` mirrors a module's `release.yml`, without the drift check. `nightly.yml` dispatches it, so the only unattended Builds release is the nightly one; other dispatches come from interactive CiCd sessions. For comparison, it released 44 times last month.
- The first release from the new pipeline is dispatched by hand, and its tag seeds `builds-version`. Builds' release preconditions are re-checked right before that dispatch. If the run ends `ready`, the maintainer publishes the draft by hand after publish-ready's checks. Any other dispatch outside nightly that ends `ready` waits for the next night.

## Dependency review

Dependency review is dropped:
- The release build turns high and critical vulnerabilities (NU1903, NU1904), and an audit that can't run (NU1900, NU1905), into errors. It overrides module settings, so these block the release like CodeQL findings.
- CI runs with NuGet audit off, so an advisory published overnight never turns CI red.
- Audit waivers exist only in Builds' `Props/`. When a module is onboarded, a CiCd agent adds its waivers there, and adoption waits for a `builds-version` that contains them.

What is lost: the license check and the npm coverage. Today dependency review runs only on PRs, so with direct pushes to `main` it rarely runs.
