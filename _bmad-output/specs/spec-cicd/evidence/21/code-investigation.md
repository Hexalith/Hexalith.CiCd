# Story 21: Parties investigation, 2026-11-16

Planning only. The user selected an isolated worktree after the source workspace
was found to contain unrelated work. No product file, registry entry, render,
remote ref, setting or credential has been changed. Two read-only research
agents inspected product gates and build/release compatibility.

## Source identities and isolation

- Worktree: `/home/administrator/projects/hexalith/cicd-story-21`.
- Branch: `story/21-migrate-parties`, created from freshly fetched `origin/main`.
- CiCd: `66e3a5a3a0e9bb01dd161c19349953594e01a22f`.
- Parties: `a575021fc97a8eda664711089270b60f5e570ded`, equal to its freshly
  fetched `origin/main`.
- Selected Builds: `v6.0.6`, source
  `fdda17c0a4538b0f7c99f813c20ca24b49006530`. Its release API reports published,
  stable and immutable. Implementation must revalidate the selected release.
- AI.Tools baseline: `736687b79c1e4fa8beabdab75c4675bb76c466b9`.

Only these three top-level direct submodules were initialized. No nested
submodule was initialized. Root CiCd instructions take precedence over older
shared guidance about checker applicability, Update branch and credentials.

## Live maintainer prerequisites

`planning-preflight.py` made GET requests only. `planning-preflight.json`
preserves sanitized metadata, timestamps, effective profiles, token-override
presence, permission response headers and exact failures. Release bodies and
bulk release assets are omitted. Both the configured CiCd profile and the
command-local maintainer profile identify `jpiquot`; account permissions do not
establish token API permissions.

- Parties rulesets: successful empty inventory. AD-21 main and v-tag rulesets
  need provisioning.
- Environments: successful inventory contains only `production`.
  `hexalith-release` is absent; its branch-policy and secret inventories return
  404. Provision a main-only environment with a Parties-only Zot push identity
  and add the `release.yml`/`hexalith-release` NuGet policy for
  `Hexalith.Parties*` beside the existing policy.
- The publish switch is exactly `true`; retention is 90 days; default CodeQL
  setup is not configured; automated Dependabot security fixes are disabled.
  Push protection is enabled in repository security metadata.
- Immutable releases are disabled. Enable immediately after adoption, together
  with scoped legacy-policy/credential cleanup, not before product preparation.
- No draft releases were returned. Of 16 tags, `v1.2.0` and
  `evidence/story-8-3-final` have no matching release in the complete 14-release
  inventory. The unmatched v-tag needs a fresh legacy-state assessment before
  deletion; do not classify the evidence tag as an orphan release or delete it.
  Preserve published package/image source identity when assessing any cleanup.
- App installation selection is **unverified**, not absent. The intended
  maintainer profile's GET of
  `user/installations/179966090/repositories?per_page=100` returns 403:
  “You must authenticate with an access token authorized to a GitHub App, a
  personal access token, or basic auth in order to list repositories for an
  installation.” The CLI also names `read:user`. Use the existing maintainer
  settings UI/readback; do not switch credentials after a refusal or broaden
  tokens. NuGet policy, Zot grants/principal mapping, org selected-repository
  grants and stale CodeQL configurations still require verification.
- Pilot story 11 remains pending its genuine scheduled-night acceptance at
  2026-11-17 02:17 UTC, allowing scheduling delay. The latest observed scheduled
  nightly, run `43842471669`, failed before pilot adoption; no future outcome is
  inferred. Preserve migration ordering and do not duplicate its observer or
  substitute a manual dispatch.

## Gate disposition against the current source

Eight legacy workflows exist: `ci.yml`, `release.yml`, `codeql.yml`,
`commitlint.yml`, `dependency-review.yml`, `rc-gate.yml`,
`current-owner-startup-diagnostics.yml`, and `ci-lifecycle-qualification.yml`.
App delivery replaces this owned perimeter; product preparation never edits it.

“Finalize exact CI owner” is already absent. “Require the owning integration
job to pass” at `ci.yml:59` only aggregates `needs.ci.result` and is deleted.
The following native persistence/authentication and cleanup verification is
product behavior and must survive through an enabled hook. Remove BMAD config,
gitlink controls and CI lifecycle/controller qualification gates and tooling.
Do not conflate them with product `.Platform.LifecycleTests` suites.

The historical count of eleven YAML-asserting tests is stale. Current direct
C# workflow readers under `tests/Hexalith.Parties.Ci.Tests/` are:

- `CiGitHistoryPreparationTests.cs`
- `GitlinkGateWorkflowTests.cs`
- `AccessibilityWorkflowTests.cs`
- `ReleaseRegistryFloorTests.cs`
- `ReleaseArtifactVerificationTests.cs`
- `ReleasePublicationVerificationTests.cs`
- `PartiesContainerPublishWorkflowTests.cs`
- `ReleaseSourcePreflightTests.cs`

Delete workflow/CI orchestration assertions. Narrow mixed files to preserve
independent package, runtime, browser and container-product assertions.
`AssistantCommitMessageInstructionsTests.cs` checks agent tooling and also goes.
`gitlink_gate_cases.py` and workflow assertions in
`tests/ci-lifecycle/{test_review_fixes,test_startup_observer,test_workflow_boundaries,test_loop2_fixes}.py`
are obsolete; assess the remaining controller-only harness as a group.

Do not delete the entire `Ci.Tests` project: its remaining product checks cover
runtime images, asset staging, dependency routing and compiled compatibility.
Keep `scripts/test_verify_eventstore_publish.py` product manifest validation,
module/ACL declarations, catalog concurrency and isolation, actual native
authentication/persistence/cleanup, and Playwright accessibility/portal checks.
Classify receipt checks individually: product provenance remains; old CI job,
run ownership and story bookkeeping do not.

## Build, native runtime and test routing

Use `Hexalith.Parties.Standalone.slnx`; the main solution includes sibling
library projects. Preserve SDK `11.0.100` and Microsoft.Testing.Platform.
Builds already selects MTP `--project` and the appropriate options. Legacy jobs
add SDK `10.0.404`; determine whether retained net10 targets need that runtime
with the real package-mode build rather than changing the SDK pin.

The standalone solution disables building three declared projects:
`Hexalith.Parties.Platform.IntegrationTests`,
`Hexalith.Parties.Platform.LifecycleTests`, and
`Hexalith.Parties.Platform.AttachedLifecycleTests`. The comment alleging a
missing published fixture API is **not current evidence**. Released package
inspection through `dotnet-inspect` found the APIs used by
`PlatformEnvironmentFixture.cs` and `AttachedLifecycleQualificationTests` in
`Hexalith.EventStore.Testing.Integration`/`Testing` **5.1.1**: topology fixture
resources/clients/descriptor, endpoint construction/authentication/Dapr,
stored-stream readers, attachment expiry/identity/cancellation and clients.
This establishes API presence, not successful compilation/runtime execution.
The selected Builds catalog defaults to EventStore 5.1.1 and Parties 3.1.1;
Parties' fallback 5.1.0 applies only without that catalog.

The successful package-inspection commands, all run from the isolated CiCd
root, were:

```bash
run-with-temp dnx dotnet-inspect -y -- type 'AspireTopologyFixtureBase' --package Hexalith.EventStore.Testing.Integration@5.1.1 -n 35
run-with-temp dnx dotnet-inspect -y -- type 'AspireTopologyFixtureBase' --package Hexalith.EventStore.Testing.Integration@5.1.1 --all -n 55
run-with-temp dnx dotnet-inspect -y -- type 'TestEnvironmentStreamReader' --package Hexalith.EventStore.Testing.Integration@5.1.1 -n 35
run-with-temp dnx dotnet-inspect -y -- type 'TestEnvironmentEndpoint' --package Hexalith.EventStore.Testing.Integration@5.1.1 -n 45
run-with-temp dnx dotnet-inspect -y -- type 'TestEnvironmentDescriptor' --package Hexalith.EventStore.Testing@5.1.1 -n 65
```

The tool version was not captured. Its initial documented `--oneline` option
was rejected; `type --help` supplied the supported syntax above. Post-inspection
Parties `git status --short` exited 0 with no output.

Remove obsolete build exclusions after qualifying the graph. Explicitly route
both lifecycle projects to integration, since their names otherwise classify
as unit. Inspect/split environment-dependent cases inside the general
`Hexalith.Parties.Tests` project; never turn failure into a filter/skip. Native
suite execution requires live environment/control channels as well as built
assemblies.

`scripts/prepare-aspire-runtime-hosts.sh` rebuilds local gateway/sample hosts
and pinned EventStore, Tenants and Memories executable sources. The Admin UI
test host also invokes a nested native-source build for asset staging. A
build-reusing hook cannot retain these rebuild paths. Subject to the human's
narrow source-host decision, explicitly include runtime executable owners in
the solution graph, keep library references in package mode, and make runtime
preparation consume the single Release build. Declare required direct
submodules in setup; do not discover or update nested ones.

`scripts/prepare-ci-package-dependencies.sh` restores an additional temporary
Aspire 13.6.5 project. Put required orchestration/dashboard dependencies into
the declared project graph instead of adding another restore inside a hook.
`scripts/verify-catalog-runtime.py` similarly owns another scratch build,
preparation and filtered run: retain catalog behavior while replacing its CI
invocation with build reuse. Qualify the selected dependency cohort before
extending exact-version capability declarations in `Directory.Build.targets`.

`scripts/verify-public-package-integration.py` hardcodes old Builds/Platform
identities, `jobId=build-and-test` and `g4-workspaces` paths. Retire obsolete CI
receipt orchestration, preserve the native/public-package effects it checks,
and never merely repin old receipt constants to claim equivalent coverage.
Use Dapr/browsers/registry setup from Builds and module actions at the existing
hook points. Assign every retained suite exactly once to a shared stage or
enabled hook; preserve dependency compatibility cohorts as product tests.

## Release compatibility and cleanup

`Directory.Build.targets` owns strict container provenance validation. Enroll
the three existing `parties`, `parties-mcp`, `parties-ui` hosts using
`HexalithPublishContainer` alongside `EnableContainer`. Map shared
`SourceRevisionId` and `Version` to the existing provenance properties without
weakening validation or repurposing an unrelated property.

The shared `Github/lib/release_build.py:release_flags` supplies source/version,
but neither it nor `Github/release-build/action.yml` supplies a created-time
authority. Parties requires one publisher-owned RFC3339 UTC second across all
images/RIDs. Per-project `UtcNow` is invalid. Recommend separately shipping
generic frozen-created support in Builds before adoption; the alternative is
an explicitly approved change to commit-time provenance semantics. Existing
checks and OCI archives must preserve exact source, version, time and identity.

No module audit waiver was found; no Builds waiver transfer is needed unless
new evidence establishes one. Preserve unrelated analyzer suppressions. Remove
tool-only root `package.json`/`package-lock.json`; `.husky/` is absent. Keep
the real product Playwright manifest under `tests/e2e`. Update active
`docs/ci.md`, `docs/development-guide.md`, `docs/index.md` and
`RELEASE-CHECKLIST.md` references while retaining historical evidence.

## Pre-adoption verification decision

`pre-adoption-check.json` records the exact required command, wrapped with
`run-with-temp`, from the Parties root. It exits 2 because
`references/Hexalith.Builds/check.py` is absent. There is no adopted
`.github/hexalith-ci.json`, and initializing an umbrella's nested dependency is
prohibited. Existing pilot and ChatBot exceptions do not authorize Parties.

Recommend a Parties-only exception for exact preparation pushes: fresh-main
standalone source, package-mode build and all applicable retained product
tests, released guard audit/action lint and pinned exact-message commitlint,
and byte/mode/gitlink comparisons proving every owned portion unchanged.
Preserve exact-input proof for every pushed revision. The exception ends at
App adoption; afterward the normal successful checker is mandatory. Without
the human's decision, preparation pushes remain blocked. No push, build or
product test was performed during planning.

## Planning verification

- Draft spec: 1,565 tokens using `tiktoken`'s `o200k_base`, within the workflow's
  target. Token counting used a disposable `run-with-temp uv run --no-cache`
  environment.
- Planning Python syntax and both saved JSON documents parse successfully.
- Standard pre-adoption checker: blocked with the exact exit-2 result saved
  separately; it did not pass and no push followed.
- Product builds/tests, full candidate validation, delivery, publication and
  acceptance remain unexecuted. Three human decisions keep the spec in draft.

## Human decisions, 2026-11-16

The human selected “apply recommendations” for all three questions. The spec
now records the Parties-only pre-adoption verification substitute, the narrow
gitlink-pinned runtime executable/composition source exception with ordinary
libraries packaged, and separate shared frozen publisher-created support as
an adoption prerequisite. The latter is recorded in
`../../../../implementation-artifacts/prerequisite-21-frozen-release-timestamp.md`.
No question remains open; the overall spec approval checkpoint is next.
The prior pending-decision and token-count observations above describe the
initial draft, not an implementation or acceptance outcome.

At this checkpoint, the isolated branch's base remains the recorded
`66e3a5a3a0e9bb01dd161c19349953594e01a22f`. The shared `origin/main` tracking
ref has advanced by four commits, most recently to
`771cfd0f01416d9adb2bdb3ff8cf8d1437d385e1`, obtained with
`git rev-parse origin/main`. No merge, reset or other session's work was
changed. Fetch and inspect the then-current main before implementation; these
planning observations do not authorize product branching from a stale main.

The revised spec measures 1,549 `o200k_base` tokens. All three decisions are
present, the Open Questions section is removed, the separate prerequisite
exists, and planning Python/JSON checks pass. The spec remains `draft` until
Checkpoint 1 approval. No product or remote operation accompanied these edits.

The human subsequently selected “approve and stop.” The spec was re-read from
disk and marked `ready-for-dev`, preserving its approved intent. Implementation
has not started; the isolated worktree and planning files remain available for
resumption. The timestamp prerequisite is still unshipped.
