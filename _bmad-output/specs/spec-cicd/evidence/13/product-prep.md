# Works product prep — 2026-11-17

Standalone clone `/home/administrator/projects/hexalith/works-story-13` at freshly
fetched origin/main `e63d857f0b75023b3b8ca9d786e5d5254e23b4b2`. Branch
`ci/shared-cicd-product-prep` pushed as
`18853d2af196c02ca80d0b40a46418f9866797d1` (tree
`494745dee30899da656987ebf5f1534280653931`). Owned workflows, Dependabot, Builds
gitlink, instruction files, deny entries, `commitlint.config.mjs` and
`global.json` are unchanged. Setup/render/gitlink remain held.

## Custom actions

- `.github/actions/after-unit-tests/action.yml` — initialize EventStore and
  PolymorphicSerializations gitlinks (no nested recurse), then
  `scripts/verify-source-debug.py --check-only`.
- `.github/actions/platform-parity/action.yml` — initialize the ten root
  gitlinks the current R1–R11 job uses, `scripts/prepare-platform-builds.sh`,
  then `scripts/verify-platform-parity-ci.sh`. Shared prepare already supplies
  Dapr for the independently prepared job; the action does not call Builds.

## Deleted (gate rule)

- `scripts/tests/test_release_{builds_compatibility,hook_permissions}.py`
- `tests/Hexalith.Works.ArchitectureTests/FitnessTests/CiCdConfigurationTests.cs`
- `tests/Hexalith.Works.ArchitectureTests/FitnessTests/PlanningEvidenceDocumentationTests.cs`
- tool-only `package.json`, `package-lock.json`, `.releaserc.json`

Nine `[Fact(Explicit = true)]` Platform-lane facts stay in IntegrationTests.
`allowed-not-runnable-tests` is not ported. R1–R11 is not part of the
preparation proof.

## Reviewed source pair

Origin `main` gitlinks are EventStore `05e4f6d40d4731f7acf435f3c678959efc672269`
and PolymorphicSerializations `f1e2b45b161627bc2d204e128ffeda086eb413b8`.
The current-source markers and `tools/source-debug-dependencies.json` were
stale (`3b2350e7…` / `2cbec6a6…`). Product prep rebinds those files to the
gitlinks. Release versions stay EventStore `5.2.0` and PolymorphicSerializations
`2.0.0`. ArchitectureTests Debug evaluation also needs the root Commons
checkout so EventStore.Contracts can resolve UniqueIds; nested EventStore
Commons is not initialized. Shared adopted submodules remain Platform +
Parties in the in-memory document; extra proof checkouts are not registration.

## Preparation proof

`prepare-proof.json` result `pass` on candidate tree
`494745dee30899da656987ebf5f1534280653931`. Package-mode Release build, stage 3
(ArchitectureTests 385, PropertyTests 3, UnitTests 597), stage 4 IntegrationTests
without Explicit request, consumer validation, released commitlint/audit/action
lint, owned-byte/mode/Builds gitlink preservation, and
`verify-source-debug.py --check-only` all passed. R1–R11 was not run. One earlier
attempt failed on MSB3026 file-lock retry for Hexalith.Builds.Tooling and was
retried without product changes.
