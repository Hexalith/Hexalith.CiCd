# Module inventory (2026-11-07; Builds and org settings re-checked 2026-11-08 and, by story 1, 2026-11-09)

Current state of Builds and of the 17 modules, as input to migration (CAP-16). Facts marked *checked* were confirmed during architecture on 2026-11-07 or 2026-11-08, or by story 1's re-check on 2026-11-09.

## Managed repositories

The 18 repositories in `references/`, all prefixed `Hexalith.`, are public, with `main` as the default branch (*checked*):
- **Builds:** the shared runtime, not a managed module (AD-19).
- **The 17 modules:** AI.Tools, Agents, ChatBot, Commons, Conversations, EventStore, Folders, FrontComposer, McpCli, Memories, Parties, Platform, PolymorphicSerializations, Projects, Tenants, Timesheets, and Works.

- **Migration order** (user-approved):
  1. Pilot: Commons and PolymorphicSerializations.
  2. Plain CI: AI.Tools, Works, Agents.
  3. McpCli: the first Aspire AppHost tests in shared stage 4.
  4. Conversations: the first job on another runner (Windows).
  5. Folders: the first kept product checks (browser end-to-end and accessibility) turned into custom actions.
  6. Then by local workflow YAML size: Projects, ChatBot, EventStore, Parties, Memories, Tenants, FrontComposer.
  7. Last, because their checkouts here are stale: Timesheets and Platform.
- **Each migration** follows the onboarding sequence in AD-21: maintainer preconditions, then product-side changes by module agents, then the setup file here, then one delivery commit that adopts the module.
- **Custom actions today:** no module has a `.github/actions/**` action yet. Kept product checks become the first ones.
- **Org:** GitHub Free, 2 members, 61 public and 6 private non-archived repositories.

## Hexalith.Builds today

"Final deletion" is the AD-20 legacy deletion, run after all 17 modules are adopted. It leaves only the end state in CAP-16.

| Item | State | Fate |
|---|---|---|
| `domain-ci.yml` (v1) | 1,507 lines, legacy, many caller hooks | Frozen, then final deletion (AD-20) |
| `domain-ci-v2.yml` (v2) | 762 lines, strict, manifest-driven. Used by EventStore and Parties only. Rejects caller hooks; needs the module CLI tool pin and registry secrets everywhere. | Frozen, then final deletion |
| `domain-release.yml` | 2,058 lines | Frozen, then final deletion; replaced by the one release workflow |
| Thin gates: `codeql`, `dependency-review`, `commitlint` | Builds' own `ci.yml` calls `codeql.yml` and `dependency-review.yml` (*checked*) | Frozen, then final deletion. `builds-ci.yml` drops the `dependency-review.yml` call at the rename and the `codeql.yml` call at the `builds-release.yml` rewrite. CodeQL moves into the release, commitlint into the guard, and dependency review is dropped. |
| Builds' own `ci.yml` and `build-release.yml` | Legacy release tooling hard-codes their names: `Tools/G4PackageQualification.functions.ps1`, `verify-g4-release-source.sh`, `archive-g4-qualification-evidence.py`. About 20 tests read them by name, some inside frozen composites. `Tools/test-self-ci.py` asserts their text, as do tests in the frozen `Github/prepare-module-build/tests` and `Github/publish-containers/tests` (*checked*). `ci.yml`'s `build-and-test` aggregator ("Require every validation job to pass") needs the catalog, contracts, .NET, and Python jobs; the Python job also runs G-4 and G-6 evidence tests. | Renamed to `builds-ci.yml` and `builds-release.yml` before the reusable `ci.yml` lands. The rename deletes the tests that assert their text and repoints the rest. The G-4/G-6 jobs and tests and the aggregator leave `builds-ci.yml` at the `builds-release.yml` rewrite. |
| `commitlint-caller.yml` | Builds-only push and PR commitlint. It calls the frozen `commitlint.yml`, and its check is required by Builds' ruleset until the story-1 cut (*checked*). | Deleted in the change that makes the guard's commitlint run in `builds-ci.yml` |
| `candidate-policy.yml` | Legacy governed-provenance workflow; no managed module calls it. The `hexalith-module` CLI's candidate gate (HXP301) is enrolled against it at a pinned SHA (*checked*). | Final deletion. Story 27-1 decides whether HXP301 retires with it. |
| `eventstore-maintenance-publisher.yml` | One-off with no caller; its trigger branch `fix/eventstore-maintenance-publication` is deleted, and it names a module (*checked*) | Deleted at the rename |
| `domain-ci.md`, `domain-ci-v2.md`, `domain-release.md` | Docs in `.github/workflows/` | Final deletion |
| `ci-cd-standards.md` | Lives in `.github/workflows/` | Kept, and rewritten to match this spec once the legacy files are gone (story 27-2) |
| `Github/` | 17 entries: `commitlint`, `create-release`, `dapr-init`, `governed-provenance`, `initialize-build`, `initialize-dotnet`, `package-release`, `prepare-domain-release`, `prepare-module-build`, `publish-azure-container-app`, `publish-container-to-registry`, `publish-containers`, `run-module-integration`, `scripts`, `split-publication`, `unit-tests`, `verify`. Modules call some directly: `initialize-build` 30 times (21 at `@main`), `initialize-dotnet` 21 (18 at `@main`), `prepare-domain-release` 7, `dapr-init` 6, `create-release` and `prepare-module-build` once each, `verify@main` once (*checked*). | Frozen until all 17 modules are adopted, including direct uses. Then final deletion of everything the new pipeline doesn't use. New code goes in new composites. |
| `Tools/` | About 50 legacy G4/G6 and package-audit scripts, plus about 13 PowerShell `Props/` catalog validators (about 4,000 lines) that Builds' `ci.yml` runs (*checked*) | Legacy scripts: final deletion. Catalog validators: classified with the gate rule at the `builds-release.yml` rewrite (`gate-classification.md`). |
| Root `package.json` | Carries the legacy release configuration | Final deletion removes that configuration |
| `schemas/` | 16 files named `hexalith.<name>.v<N>.json`; several ship in product CLIs (`hexalith-module`, Evidence.Cli) (*checked*) | Kept. New schemas follow the convention (spine, Consistency Conventions). |
| Release cadence | semantic-release, exact tags only. Latest v4.44.11. 44 tags in the last month, no floating major tag. No consumer references a tag; they use `@main` or raw SHAs. | Exact-tag references; the only unattended release is the nightly one |
| Audit settings | `Hexalith.Build.props` line 33 sets `WarningsNotAsErrors` for NU1901–1904, so vulnerable packages don't fail builds today (*checked*) | The release build overrides it for NU1900, NU1903, NU1904, and NU1905 |
| Commitlint config | `commitlint.config.mjs`: header and body lines at most 200, footer lines at most 100 (config-conventional), merge commits linted (`defaultIgnores: false`) (*checked*) | Kept as is, plus one rule rejecting skip markers |
| `dependabot.yml` | Covers Builds' own paths | Excludes the frozen paths until the final deletion; CiCd agents close Dependabot PRs that touch frozen files |
| Dapr pins | `HexalithDaprRuntimeVersion` 1.18.7 and `HexalithDaprCliVersion` 1.18.2 in `Props/Directory.Packages.props` (*checked*) | The one pin each, bumped to 1.19.1 in story 2-5 |
| Package catalog | `Props/Directory.Packages.props` has Works- and Folders-specific conditions (*checked*) | Product build data, outside the module-agnostic rule (AD-2) |
| Rulesets | Since story 1 (2026-11-09): `Protect main` blocks only deletion and force-push, with no bypass. `v tags` blocks update and deletion of `v*`. The 15 `v*` tags without a release are deleted (*checked*). Before that, `main` required a pull request and status checks, and there was no `v*` ruleset. | Done: exactly the AD-21 rulesets, `main` and `v*` tags. `v*` creation stays open (`enforcement.md`, Accepted residuals). |
| Immutable releases | Off (*checked*) | On before the first rewritten release |

## Versioning drift

- Builds pins range from 7 to 946 commits behind HEAD. Ten repositories pin `domain-ci` to a SHA.
- Every `Directory.Packages.props` imports from the `references/Hexalith.Builds` submodule. In every repository, that submodule's commit differs from the workflow pin.
- Stale submodule pointers: Timesheets and Platform run workflows on GitHub, but their checkouts in this repository have none.
- One switch selects package mode: `UseHexalithProjectReferences`, with 736 uses (*checked*). CI and the local check always build in package mode.

## Release patterns (to unify into one)

| Pattern | Repos |
|---|---|
| Reusable `domain-release` | 2 |
| `prepare-domain-release` composite | 6 |
| Bespoke `.hexalith/builds-execution` checkout | 4 |
| Fully bespoke | ChatBot, McpCli |

- ChatBot runs its full release on every push: 88 runs, 100% failed.
- Recovery workflows: three copies of `recover-partial-release.yml`.
- 14 module releases use the `production` GitHub environment (*checked*). The new publish job runs in each repo's `hexalith-release` environment. At onboarding, a nuget.org policy naming it and scoped to the module's package IDs is added beside the existing one. Right after adoption, every other policy is deleted (AD-21).
- Legacy releases are mostly authored by `github-actions[bot]`, some by the maintainer: Parties 2 of 13 recent, Agents 1 of 3 (*checked*).
- NuGet authentication is split between an API key and OIDC. Every module moves to Trusted Publishing.

## Settings that block onboarding (*checked*)

- **Rulesets:** EventStore and Platform require a pull request and status checks on `main`. Builds did too, until story 1 cut it back (2026-11-09). Platform also has tag rulesets, including tag-creation authorization. Delivery and the release can't push until these are cut back (AD-21).
- **Org-wide Apps:** before story 1, `claude`, `chatgpt-codex-connector`, `cursor`, and `semgrep-app` were installed on all repositories, with Contents, Workflows, and Actions write. Since 2026-11-09, `claude`, `cursor` and `semgrep-app` are uninstalled, and `chatgpt-codex-connector` is installed on EventStore only. The CiCd App `hexalith-cicd` is installed on Builds and CiCd only (*checked*). Branch evidence (2026-11-08):
  - `codex/*`: 42 PRs on 9 repos, the last on EventStore on 2026-10-09.
  - `claude/*`: last on 2026-01-10. Builds has 4 Claude-on-the-web PRs, the last on 2026-01-04. CiCd has none from any App.
  - `cursor/*`: one PR, on 2026-02-26.
  - Semgrep: no PRs, and no Semgrep check on Builds' `main`.

  Hence the SPEC's installation scope. Since story 1 (2026-11-09), local Claude Code sessions in CiCd use the CiCd-agent token, through `GH_CONFIG_DIR`. The token expires on 2027-11-08 and must be renewed before then. Elsewhere they use the maintainer's tokens. None of them uses the App.
- **Org settings:** before story 1, the default workflow permission was `read`, fork-PR approval applied only to first-time contributors, all actions were allowed, artifact and log retention was 30 days, and the legacy org secrets `NUGET_API_KEY`, `HEXALITH_ZOT_*`, `AZURE_*`, and `SONAR_TOKEN` were visible to all repositories. Since 2026-11-09:
  - fork-PR approval covers all external contributors, and retention is 90 days;
  - each legacy secret is restricted to the public repos that read it (story 1, step 8 table), never CiCd or Builds;
  - `HEXALITH_NUGET_USER` exists, selected: Builds. The Actions and Dependabot secrets `HEXALITH_REGISTRY_PULL_USERNAME` and `_PASSWORD` exist, selected: Builds. They hold the pull-only Zot principal `hexalith-registry-pull`;
  - push protection is on for CiCd, Builds and all 17 modules (*checked*).
- **Rulesets and immutable releases elsewhere:** since 2026-11-09, CiCd has exactly `main` (deletion and force-push) and `delivered` (`delivered/**`, with the App as the only bypass), plus the `cicd-app` environment (*checked*). Immutable releases are off on Builds, CiCd, and Parties.
- **Audit already failing:** ChatBot, Platform, Parties, FrontComposer, and McpCli set `TreatWarningsAsErrors` without exempting NU190x, so vulnerable packages already fail their CI. CI's audit-off flag removes that. Waivers move to Builds during migration.
- **Audit bypasses** (reproduced with SDK 10.0.403):
  - A module `NoWarn` for NU1903, `NuGetAuditLevel=critical`, or `NuGetAuditSuppress` each defeat the release audit gate. So do `MSBuildWarningsAsMessages`, `TreatAsLocalProperty` on `NuGetAudit`, a `NoWarn` attribute on a `PackageReference`, `-nowarn` in a `Directory.Build.rsp`, `auditSources` in a `nuget.config`, an obfuscated `NoWarn`, and `NuGetAuditSuppress` in an imported `build.xml`.
  - The release's `-noAutoResponse` and Builds' nuget.org-only restore config remove the `rsp` and `nuget.config` paths.
  - The release's `-p:NuGetAuditLevel=low` overrides a module's audit level.
  - The guard's audit lint rejects the rest, except the obfuscated `NoWarn`, which is accepted (`enforcement.md`).
- **Files the perimeter adds to the must-be-absent list:** no module tracks a `Directory.Build.rsp` or a `.commitlintrc*` today.

## Callers outside the managed modules (*checked*)

- 14 unmanaged public repos run `Github/package-release@main` on push: Applications, ChatClient, Documents, Domains, EventStores, GitStorage, IdentityStores, KeyValueStorages, MyNewModule, MyNewPackage, NetAspire, Security, Streams, and Security_OLD. One of them also runs `Github/publish-container-to-registry@main`. None is archived; their last pushes were between January and April 2026.
- They are not waited for. The final deletion breaks their next push. The maintainer may archive them at any time (AD-20).

## Baseline gaps

- **ChatBot:** no CodeQL, dependency review, commitlint, or Dependabot.
- **McpCli:** no CodeQL, dependency review, or Dependabot.
- **Projects:** no Dependabot.
- **Workflow linting:** only Works runs `actionlint`.
- **CodeQL today:** runs on every push, every PR, and weekly in 12 repositories, taking 6–24 minutes per run. It already uses `build-mode: none`. Stale configurations and default setup are removed during onboarding.

## Setup and toolchain drift

The shared pipeline replaces all of these, except the SDK version, which stays module-owned.
- **Workflow volume:** 2 to 13 workflow files per repository, 218 to 3,116 lines in total.
- **SDK:** FrontComposer hard-codes the SDK version in 10 places. `global.json` pins are split between 10.0.401, .402, and .403.
- **Dapr:** runtime pins vary from 1.18.2 to 1.18.7, even within one repository. Builds' props pin the Dapr .NET SDK 1.19.0. The new pipeline uses one runtime pin and one CLI pin in Builds' `Props/`, both 1.19.1 (Builds table).
- **Variables:** names differ from repository to repository. The new ones are all prefixed `HEXALITH_` (spine, Consistency Conventions).

Setup and import steps that fail in the sample are replaced by the shared pipeline:
- Conversations: "Prepare package build imports", in 4 jobs
- Works: "Prepare package dependencies" and "Prepare verified published Builds artifacts"
- Parties: "Initialize root-declared submodules"
- McpCli: "Prepare Aspire tier" and "Run Aspire hook"

Late failures: "Fail on blocking test failures", an aggregate step at the end of the run, appears in Agents, Conversations, Folders, McpCli, Parties, Tenants, Timesheets, and Works.

## Test projects (*checked*)

Naming is mixed across modules: `*.Tests`, `IntegrationTests`, `Integration.Tests`, `AppHost.Tests`, `UI.E2E.Tests`, `LoadTests`, `Benchmarks`, and Works' `UnitTests`, `PropertyTests`, and `ArchitectureTests`. The stage rule in `pipeline-stages.md` sorts them; anything it misroutes is fixed through the setup file.

16 of the 17 .NET repositories, and Builds, select Microsoft.Testing.Platform in `global.json`, so tests run with `dotnet test --project`.

## Dependency graph

- Modules reference each other as submodules, 2–17 each, in a dense mesh with cycles: EventStore with Tenants, and Memories with EventStore.
- McpCli, Platform, and ChatBot reference nearly every other repository.
- Hexalith package versions are pinned centrally in Builds' `Props/Directory.Packages.props`.

## Agent and governance footprint

- **Agent-written "fix CI" specs:** FrontComposer 26, EventStore 25, Memories 8, Parties 7, Projects 4.
- **Workflow commits since 2026-10-01:** Tenants 84, EventStore 76, Parties 60.
- **Instruction files:** `AGENTS.md`, `CLAUDE.md`, and `copilot-instructions.md` are identical in each repository, and all derive from `Hexalith.AI.Tools/hexalith-llm-instructions.md`. None of them says "don't edit workflows" or "use Builds". They say releases happen on merge, which contradicts the standard.
- **`bmad-testarch-ci`:** installed in 14 repositories.
- **`.claude/settings.json`:** present in 15 modules, in 12 different versions.

## Technical surface

Shared stages or custom actions must cover all of these:
- **Non-.NET code:**
  - Python: Memories 122 files, Tenants 71. It is tooling under `tests/tooling` and `tests/scripts`, not product (*checked*), so the gate rule decides its fate.
  - PowerShell.
  - Node, for commitlint and semantic-release. Both now run only inside Builds.
- **Runtime:** Dapr 1.18 and Aspire.
- **Images and registry:**
  - A Postgres image pinned by digest.
  - The Zot registry (`registry.hexalith.com`).
- **Secrets:** Azure secrets (EventStore). Hook secrets arrive with its migration, passed explicitly by name.
- **Runners:** a Windows runner (Conversations).

## Current standard (`ci-cd-standards.md`)

| Rule | Status under this spec |
|---|---|
| Shared logic lives in Builds | Kept |
| Routine Builds refs use `@main`; release is pinned to a reviewed SHA | Replaced by exact release tags |
| SDK comes from `global.json`; Release builds use `-warnaserror` | Kept |
| Tests run per project | Kept |
| Releases run by `workflow_dispatch` only, behind a publish-gate variable | Kept, but dispatched nightly by the scheduler; the variable must be exactly `true` or `false` |
| Secrets are explicit, never `secrets: inherit` | Kept |
| Every module has CodeQL, dependency review, commitlint, and Dependabot | CodeQL runs inside the nightly release. Commitlint runs inside the guard. Dependency review is dropped; the release audit gate replaces it. Dependabot is rendered, never for `github-actions` or `gitsubmodule`. |
