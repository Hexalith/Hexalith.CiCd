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
- **Submodules:** only Builds is checked out. Today `initialize-build` clones every declared submodule, 2–17 per module. If a package-mode build turns out to read more, a `submodules` knob is added (spine, Deferred).
- **SDK:** comes from `global.json`.

## Hook points

- The hook points are exactly `after-unit-tests`, `after-integration-tests`, and `nightly` (the last runs in the release). Each has one action, at `.github/actions/<hook>`, run only when the setup file enables it.
- There is no hook after the build, so that the local check matches CI stages 1–3 exactly.
- An action that needs browsers or Dapr is a hook with that knob on.
- An action that needs another operating system gets an extra job, rendered into the module's caller. It runs after the main job passes and repeats checkout, restore, and build through `prepare`.
- Script hooks through `run:` are not used: they are unstructured and tend to grow into a second pipeline.
- The custom-action contract is in AD-14.

## Local check

- `python3 references/Hexalith.Builds/check.py` runs stages 1–3, with the same scripts and build flags as CI.
- Agents are told to run it before they push.
- There is no pre-push hook: hooks slow every push and can be skipped with `--no-verify`.

## Nightly run

1. At 02:17 UTC, `nightly.yml` in this repository dispatches Builds' `builds-release.yml` and the `release.yml` of every adopted module, all at once. Anything beyond the Free plan's 20 concurrent jobs waits in GitHub's queue.
2. Each module's release run (AD-16, AD-17):
   1. Resolves the release SHA once and checks its owned files against the module's `delivered/<Repo>` branch. Drift fails red.
   2. Runs CodeQL (`build-mode: none`) and the `nightly` hook, whatever the kill switch says. An open high or critical alert from this analysis, or a failing hook, blocks the release.
   3. Applies the kill switch: `false` succeeds with "publishing disabled", and any value other than `true` fails.
   4. If CI on that SHA isn't green, fails red: "main is red, nothing released".
   5. If no releasable commit exists since the last tag, succeeds: "nothing to release". Otherwise creates a marked draft release with the next version.
   6. Builds and packs once with the real version. Packages with a high or critical vulnerability fail the build.
   7. The caller's `publish` job pushes the NuGet packages (Trusted Publishing, `--skip-duplicate`) and the containers (by version tag). It then publishes the draft, which creates the tag last.
3. `nightly.yml` waits for every run, for at most 5 hours. A run still going at that point, or one without a readable outcome, counts as failed. It writes a pass/fail summary with links, runs the duplicate scan, and then bumps Builds (below), whatever the results. It fails if any release, the scan, or the bump's delivery failed.

- **Reruns:** a marked draft is completed with its own version and SHA, so rerunning a failed release completes it. The release never commits to `main`.
- **What runs twice:** one compile per released module per night, plus one more for a module with a `nightly` hook.
- **CodeQL trade-off:** moving it to the nightly run removes a quarter to a third of the runs in most repositories. The cost is that a finding can take up to 24 hours to appear, but it still blocks the release.

## Builds version bump

- Modules reference Builds by an exact release tag, never by `@main` or a raw SHA. The tag appears in the callers, in `hexalith-ci.json`, and as the submodule pointer.
- After the wait and the duplicate scan, `nightly.yml` moves `builds-version` to the newest tag in the current major that isn't in `builds-skip`. It re-renders and commits `build(cicd): bump Builds to vX.Y.Z`, and delivery ships it to every module. `build(cicd)` is not releasable.
- A new major is adopted with one commit here that changes `builds-version`, `templates/`, and `setup/` together.
- A rollback sets `builds-version` to the older tag, adds the bad tag to `builds-skip`, and removes setup keys that the older schema lacks. A rollback across a major reverts that major's adoption commit.

## Release propagation

- Dependency bumps are `build(deps)` commits. They don't release; they ship with the module's next releasable change.
- To force a release, for example for a security fix, an agent commits the bump as `fix(deps): …`.
- Hexalith package versions are pinned centrally in Builds' `Props/Directory.Packages.props`. Builds releases on every commit type except `docs`, `test`, and `style`, so a change there always produces a Builds release. Modules receive it through the next bump.
- Known effect: a module's published package keeps referencing an older Hexalith version until that module changes.

## Builds' own CI and release

- `builds-ci.yml` runs `actionlint`, `zizmor`, and the Python tests on its scripts. It also runs the reusable `ci.yml` twice:
  - against Builds itself, for the build and test stages;
  - against the sample module in `Samples/`, using test-only inputs that module callers never set. Only this call runs the guard, against the sample's fixture perimeter, and its commitlint covers Builds' own commits.
- Tests that assert workflow text are dropped.
- `builds-release.yml` mirrors a module's `release.yml`, without the drift check. `nightly.yml` dispatches it, so the only unattended Builds release is the nightly one; other dispatches come from interactive CiCd sessions. For comparison, it released 44 times last month.
- The first release from the new pipeline is dispatched by hand, and its tag seeds `builds-version`.

## Dependency review

Dependency review is dropped:
- The release build turns high and critical vulnerabilities (NU1903, NU1904) into errors, overriding module settings, so they block the release like CodeQL findings.
- CI runs with NuGet audit off, so an advisory published overnight never turns CI red.
- Audit waivers exist only in Builds' `Props/`.

What is lost: the license check and the npm coverage. Today dependency review runs only on PRs, so with direct pushes to `main` it rarely runs.
