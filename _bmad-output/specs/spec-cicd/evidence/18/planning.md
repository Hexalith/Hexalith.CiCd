# Story 18 planning evidence

Observed 2026-11-16. This is planning, not migration acceptance. No GitHub,
NuGet or registry setting, module product file or owned module portion changed.

## Isolation and source identity

The human authorized an isolated worktree after the skill's dirty-tree stop.
`/home/administrator/projects/hexalith/cicd-story-18` is on
`story/18-migrate-projects`, created after `git fetch origin main`, from
`d04c9ab7a8fa43dc6dac1f15d34135aba8e79551`. Existing changes in the original
workspace remain untouched. Its rendered skill snapshot remains the instruction
source; it was rendered once, before isolation.

Direct root submodules Projects, Builds and AI.Tools were initialized without
recursion. No nested submodule was initialized. Projects' recorded pin is
`fc58cefde69d72d7d3daa574b5022f73f830a85e`; fetched live `origin/main` is
`981ceef13a1abc88219925e73c51a23eb9ac50c2`, twenty commits newer. Prepare a
product branch from freshly fetched current main, not the old gitlink. Builds
pin `v6.0.6` peels to `fdda17c0a4538b0f7c99f813c20ca24b49006530`.

The module AGENTS.md and direct AI.Tools `hexalith-llm-instructions.md` and
`hexalith-git-instructions.md` were loaded. Their general maintainer-push
fallback does not supersede this migration's explicit module-agent requirement.

## Maintainer metadata and real failures

`planning-preflight.py` and its JSON record read-only GETs with timestamps and
permission headers. Inherited profile is
`/home/administrator/.config/gh-cicd-agent`; neither GH_TOKEN nor GITHUB_TOKEN
override is present. Default-profile read-only user/repo checks succeeded.
Administration checks use only command-local
`/home/administrator/.config/gh`, account `jpiquot` / `6775094`, target
`Hexalith/Hexalith.Projects` / `871087402`. Account admin metadata is not token
permission evidence.

The intended maintainer profile's installation-repository GET returns HTTP 403:
“You must authenticate with an access token authorized to a GitHub App, a
personal access token, or basic auth in order to list repositories for an
installation.” No token change was attempted. The existing attended browser
provided an alternative read-only observation: `app-selection-readback.json`
identifies the exact installation URL and an unchanged saved selection of
Builds, CiCd, Commons and PolymorphicSerializations. Projects is not selected.
Recheck after any additive selection; preserve every existing selected repo.

Other successful reads establish: no rulesets; only the legacy `production`
environment; immutable releases off; publish switch exactly `true`; retention
90 days; default CodeQL `not-configured`; security updates disabled; secret
scanning push protection enabled. Six returned published releases have no
drafts. Returned tags include `v1.1.0` without a corresponding returned release;
authenticate its complete legacy state before any cleanup. CodeQL analysis
cleanup, full orphan-tag reconciliation, scoped NuGet
policy, per-module Zot identity, org grants and legacy scopes remain to be
verified/provisioned in AD-21 order. They are not assumed absent or satisfied.

`run-with-temp python3 references/Hexalith.Builds/check.py`, executed from the
isolated Projects root, exits 2: its nested Builds script is absent. Exact
stderr is retained in `pre-adoption-checker.log`. Released `local_check.run`
also requires an adopted CI document, matching committed Builds gitlink/tag,
clean checkout and accepted delivered perimeter. Initializing or bootstrapping
owned files would not establish the ordinary pre-adoption prerequisite.
The pilot preparation exception does not authorize Projects. A new scoped
human decision is required before a product push; no push has occurred.

Story 11's saved scheduled-night checkpoint is still pending. The live nightly
inventory has no newer successful post-repair scheduled pilot checkpoint.
Planning can continue; adoption must wait for the accepted pilot gate.

## Product inventory and classification

Read-only investigation used current Projects origin/main, not its stale
checkout. `Hexalith.Projects.CI.slnx` contains sixteen product projects, seven
unit suites and `tests/Hexalith.Projects.Integration.Tests`. Preserve all C#
test sources and the module's SDK `11.0.100` / MTP selection. No C# workflow
YAML assertion was found. Package IDs are `Hexalith.Projects`, `.Contracts`,
`.Client`, `.Testing`, `.ServiceDefaults`; no explicit container opt-in was
found. Root npm manifest/lock serve only semantic-release/commitlint; no
tracked `.husky/` exists. No production NuGet audit waiver was found;
UI.Contracts' `ASP0006` suppression is unrelated and stays.

- Preserve FrontComposer generated-artifact inspection in
  `tests/tools/run-frontcomposer-inspect-gate.ps1`. It presently rebuilds
  UI.Contracts and the sibling inspector, then uses `inspect --build`.
  Adapt it to inspect retained generator outputs from the shared build and a
  prepared inspector; generic installation/build work belongs in Builds.
- `run-openapi-fingerprint-gate.ps1` repeats ClientGenerationTests already
  executed by Client.Tests. Preserve those assertions, eliminate the duplicate
  invocation. Preserve actual package/consumer assertions from
  `run-package-dependency-gate.ps1` and
  `scripts/{pack-release-packages,validate-nuget-packages,validate-consumer-package-references}.py`,
  reusing Release outputs. Old publishing authentication/evidence machinery
  is replaced by shared release behavior.
- Retire workflow-policy, agent-tooling and historical P1R artifact/run/tag
  evidence gates. Workflow-reading Python tests include
  `tests/tools/test_{bmad_loop_hook,g6_mapper_build,production_authority_guard,release_workflow,render_skill,run_ci_workflow_gates,run_g6_candidate_gate,run_g6_ci_gate,run_g6_current}.py`.
  Delete workflow-asserting portions; preserve any mixed product assertions.
  Retain unrelated local tooling and historical evidence unless their removal
  is required by the owned perimeter.
- G-6 is mixed: retire Projects' tuple/source/workflow evidence governance and
  repeated cross-module compilation. Its genuine EventStore PostgreSQL
  stop/restart and deterministic support assertions must remain in owning
  product suites; trace coverage rather than deleting by story label.

`current-ci-jobs.json` and `current-ci-failed.log` record run `43881420098` at
the exact live source above. Shared legacy build/test and Projects generated
artifact jobs succeeded; G-6 failed restoring its effective package graph.
Scheduled E2E was skipped on this push. This is not proof that shared v6.0.6
or the scheduled browser path works on Projects.

## Browser prerequisite and proposed choices

The real browser gate is `tests/e2e/run-live-apphost.sh` and its full Playwright
suite. It sets up explicit live fixtures and tears down its exact AppHost. Its
scheduled path requires `PROJECTS_E2E_TEST_USER_PASSWORD`, runs `aspire start`
without reusing the shared Release build, and unconditionally follows with
`tools/qualification/run_supported_project_reads.py`, a Debug/source path.
Keep the actual browser and persisted-state product assertions.

An existing ephemeral credential/backend path is
`tools/qualification/run_live_project_fixtures.py`; it provisions private
fixtures but builds a Debug/source graph.
`src/Hexalith.Projects.AppHost/IsolatedLiveE2EFixtureProfile.cs` rejects
Release/package use. Do not remove that safeguard to make CI pass. A distinct
qualified Release/package fixture lane can reuse the provisioning concept and
shared outputs while preserving current source/production separation.

Shared `Github/lib/ci_environment.py` supports Dapr and built .NET Playwright
tooling, not this npm workspace's browser installation or Aspire CLI. Generic
support must be released in Builds with explicit optional configuration and
no module-name conditions. Hook secret support was deferred to story 20;
providing a named secret alone would not fix the source/rebuild limitations.

Proposed choice: include a separate Release/package ephemeral-fixture path and
the generic runtime support in this migration (no persistent browser password
input), or hold adoption until these prerequisites are delivered separately.
Neither choice may drop or skip product checks. After the choice, complete
the exact API/file design before spec approval.

Baseline knobs: solution above; Dapr needed. Extra direct submodules include
EventStore and Tenants (unconditional executable AppHost references), Platform
(package-mode linked helpers), FrontComposer (inspection tooling). Browser,
registry and additional runtime dependencies must be finalized through the
chosen package-mode fixture qualification, not guessed from all gitlinks.

## Approval facts

Intent gaps: whether fixture/runtime prerequisites belong in this migration,
and whether to authorize the narrow pre-adoption checking substitute.
External effects after approval: App selection, AD-21 settings and scoped
credentials/policies, product pushes, delivery-triggering CiCd push, immediate
legacy credential cleanup and normal nightly publication. No such effect has
been performed. Footprint includes Projects product tooling/hooks, optional
Builds runtime/schema support and a released pin, CiCd setup/render/gitlink and
evidence. Keep this one migration goal; do not claim adoption while prerequisites
or the authentic scheduled-night outcome are missing.

## Human decisions and current design — 2026-11-16

The human answered `*apply recommended`: both numbered recommendations are
accepted. Include the distinct Release/package ephemeral browser-fixture lane
and generic Builds preparation in this migration. The Projects-only preparation
exception consists of released commitlint/audit, unchanged owned-tree proof,
complete Release/package build/tests and retained product-hook qualification,
with exact source/results. It expires at adoption and covers no other module.
These answers supersede the proposed-choice and pending-authorization statements
above; do not ask again for these decisions.

The isolated CiCd branch was fast-forwarded after fetching current main to
`d3f3ef864c08cd89e390246d1a5d1dedffc4a92b`. Its recorded Projects pointer now
already equals `981ceef13a1abc88219925e73c51a23eb9ac50c2`.
Clean direct Projects/AI.Tools checkouts were synchronized to those recorded
gitlinks without recursive initialization. Original workspaces remain untouched.

The exact shared/tool/scanner and module-fixture tasks are captured in adjacent
`design.md` and distilled into the spec. No module implementation, remote
administration, push, publication or adoption has been performed. The actual
scheduled-night pilot checkpoint remains a prerequisite for adoption.
