# Story 23 investigation

This is planning evidence, not implementation or adoption evidence. Read-only
investigation ran on 2026-11-16. No remote setting, product file, workflow,
credential grant, delivery ref or release was changed. The original CiCd
workspace and its staged changes were not edited.

## Revisions and workspace

- Isolated CiCd worktree: `/home/administrator/projects/hexalith/cicd-story-23`,
  branch `story/23-migrate-tenants`, based on freshly fetched origin/main
  `66e3a5a3a0e9bb01dd161c19349953594e01a22f`.
- Tenants checkout and freshly fetched origin/main:
  `292dbf164f26bcf376ef86d749b149b075f8b502`.
- Tenants' committed Builds gitlink and CiCd's current `v6.0.6` source:
  `fdda17c0a4538b0f7c99f813c20ca24b49006530`.
- Tenants SDK: `11.0.100`, `latestPatch`, Microsoft.Testing.Platform. Preserve it.
- No nested submodule was initialized. Later disposable verification must use
  `run-with-temp`; keep package feeds, repository copies and outputs in its
  private TMPDIR and save useful logs here.
- The existing Builds working copy has unrelated uncommitted shared-preparation
  changes. Released-contract conclusions were checked against `git show
  v6.0.6:<path>`. Use an isolated Builds worktree from fresh main for any later
  shared edits, and reconcile published overlapping capabilities before adding
  another API; never overwrite that working copy.

## Read-only authentication and preconditions

`read-preflight.py` records exact requests, statuses and relevant permission
headers in `preflight.json` and `maintainer-preflight.json`. Its API snapshots
are initial pages, not a complete historical or mutation-ready inventory.
Paginate and recheck immediately before any cleanup or configuration change.

The default CiCd profile stayed `/home/administrator/.config/gh-cicd-agent`,
with neither GH_TOKEN nor GITHUB_TOKEN inherited. The default and protected
module credential both identified account `jpiquot`, id `6775094`. Account
`admin:true` does not establish token scope. Module credential storage is the
existing current-user-owned, nonsymlink mode-0600
`/home/administrator/.config/gh-module-agent/token`. It was read only into
child-process GH_TOKEN, without printing its value. Future product writes use
that credential; CiCd/Builds operations use CiCd-agent. Administrative reads
used command-local `/home/administrator/.config/gh`; it made no writes and did
not replace the default profile.

Verified current state:

- Ruleset inventory is empty; `hexalith-release` environment is absent. The
  existing `production` environment and its reviewer policy remain untouched.
- Publish switch `HEXALITH_RELEASE_PUBLISH_ENABLED` is absent; the repository
  variable list contains only legacy `NUGET_USER`.
- Retention is 90 days. Push protection is enabled. CodeQL default setup and
  Dependabot automated security updates are disabled. Immutable releases are off.
- Tenants lacks all four shared Actions/Dependabot registry-pull grants and
  the shared `HEXALITH_NUGET_USER` variable grant.
- The App installation exists with selected repository access, but its exact
  repository list returned 403 even with the intended maintainer profile.
  App selection remains unverified. Access to the installation's selected
  repository settings, or the appropriate App-authorized read, is required;
  do not infer exclusion or mint the private App key in this session.
- NuGet Trusted Publishing policies and a Tenants-scoped Zot identity have
  not been inspected through their authenticated management surfaces.
- Legacy CodeQL analyses exist under `.github/workflows/codeql.yml:analyze`.
  Reinventory every page and delete only superseded configurations at the
  prescribed migration stage, preserving unrelated findings/configurations.
- Tenants is selected for legacy `HEXALITH_ZOT_USERNAME`; it is not selected
  for org `NUGET_API_KEY`. The actual paired org secret is `HEXALITH_ZOT_API_KEY`,
  not the nonexistent `HEXALITH_ZOT_PASSWORD` queried by the initial snapshot.
  Inventory every legacy secret and its grants before cleanup; these reads
  do not establish a complete legacy-credential no-op.

Before product preparation, follow architecture AD-21 in order: confirm App
selection; inspect incomplete release drafts/tags and stale CodeQL state;
create exactly the main deletion/force-push and v* update/deletion protections;
create main-only release environment with Tenants-only Zot push pair; add the
NuGet policy for `Hexalith.Tenants`, `release.yml`, `hexalith-release`, scoped
to `Hexalith.Tenants*`, beside existing policies; retain disabled redundant
security automation; set the exact publish switch and grants. After actual
adoption, immediately enable immutable releases and revoke only superseded
NuGet/org-secret/API-key/Zot access. A permission refusal leaves state unverified.

## Pre-adoption check boundary

The exact wrapped standard command from the current module checkout returned 2:

```text
python3 references/Hexalith.Builds/check.py
python3: can't open file '.../Hexalith.Tenants/references/Hexalith.Builds/check.py': [Errno 2] No such file or directory
```

The nested Builds checkout is intentionally uninitialized. The committed pin
does contain the checker, but `Github/lib/local_check.py` additionally requires
the committed `.github/hexalith-ci.json` and authentic delivered state. Tenants
has no committed configuration, no CiCd setup, and delivered-ref GET returns
404 under both profiles. Initial failure is not a product build/test failure.
Initializing a standalone Builds checkout alone cannot satisfy adoption inputs.

Pilot and ChatBot exceptions are module-specific. A human decision is required
for Tenants: before adoption only, verify each exact prospective product push
with the released package-mode build and classified tests, applicable product
checks, audit/custom-action policy and pinned commitlint, plus owned
byte/mode/gitlink preservation. No fake delivery/configuration or checker bypass
is authorized. After adoption the standard command is mandatory.

## Product gate inventory and retention

The historical count of twelve YAML-asserting tests is a starting inventory,
not a deletion target. Enumerate current methods and indirect/parsed YAML
reads before editing. Keep all module/sample product test projects.

| Existing source | Migration treatment |
| --- | --- |
| `ci.yml` server-profile-boundaries | Retain owner transport, readiness budget and v2 runtime assertions for every existing profile. |
| `ci.yml` published-catalog-http | Retain compiled catalog enrollment, generated HTTP cases, archive provenance/refusal, real pack and consumer checks across existing profiles. |
| `ci.yml` authenticated-routes | Retain REST, persisted state, anonymous UI, authenticated responsive UI, private diagnostics, no-skips checks and real Dapr retry qualification. |
| `ci.yml` http-contracts | Retain ETags, command status/UI proof, protected project contracts, replay integrity and audit persistence. Avoid repeating the same tests in the shared integration stage. |
| `source-reference.yml` | Retain production source registration, authority, bootstrap/cohort and persisted-effect behavior, migrating ordinary dependencies to Release package mode. Rebind `SourceCatalogOwnerProfileTests.cs` to the existing COHORT capability and package producer identity where equivalent. |
| `story-guards.yml` remove-focus-browser-guard | Keep `tests/Hexalith.Tenants.UI.Tests/Browser/validate-tenants-focus-browser.sh` as a product hook using central browser setup. |
| Shared legacy coverage gate | Preserve 80% line coverage and 100% named isolation branch coverage, including its original scopes; do not silently replace thresholds with passing test counts. |
| Scheduled tenant-audit performance | Retain its cadence, assertions and functional `tests/performance/tenant-audit/package.json`/lock; run scheduled work through the nightly hook with cadence selection, without rerunning ordinary CI suites. |

`tests/Hexalith.Tenants.Contracts.Tests/PackageGovernanceTests.cs` mixes workflow
policing with package metadata, consumer and publishing assertions; edit at
method level. `CiQualityGateScriptTests.cs` also keeps real archive and coverage
validator behavior; delete its workflow assertions including
`FrozenBootstrapJobsBind...`, `AspireLaneRequires...`,
`AspireResultGateRequires...`, and `AspireResultGateRejects...`.
`SourceReferenceWorkflowGovernanceTests.cs` is workflow policing.
`tests/Hexalith.Tenants.UI.Tests/TenantsUiCompositionTests.cs` contains a
workflow assertion alongside product checks; preserve the latter.

Delete the story gitlink/pushall/BMAD customization/elicitation/TEA CI gates and
workflow-governance assertions. Classify legacy release/replay/provenance suites
by what they actually test: remove agent/story/evidence or obsolete pipeline
proof; retain tests of real packages, consumer behavior and shipped tooling.

Product Python suites include `tests/scripts/test_{catalog_artifact_guards,
catalog_package_consumer,hosted_package_profile,nuget_dependency_ranges,
bootstrap_handoff}.py`, plus `scripts/tests/test_{platform_source_root,
source_catalog_profile}.py`. Do not replace inspection with blanket deletion of
Python tooling. Classify all 28 currently tracked Python files under tests/.

The existing `scripts/run-aspire-integration-tier.sh` omits five live classes
and Category=Performance because separate lanes own them; copying it alone
loses coverage. Explicitly route every test project/category exactly once.
AppHost/IntegrationTests classify into stage 4 automatically; Server.Tests
requires explicit integration classification or hook ownership. Hooks that own
a complete project must use `tests.exclude` pointing to that enabled hook.
Keep test results and failure diagnostics with their existing confidentiality.

## Package/source boundary and proposed human decision

Root `Hexalith.Tenants.slnx` explicitly lists ordinary Commons, EventStore,
FrontComposer and Memories library projects. Remove those entries from the CI
solution graph; ordinary cross-module references already have package-mode
alternatives. Preserve module projects and tests.

Actual live topology still requires source inputs:

- AppHost unconditionally links Platform `DaprSelfHostedMtls.cs` and
  `DaprSelfHostedMtlsSubscriber.cs`, and references Builds.Tooling source.
- `AddHexalithEventStorePlatformProjects` launches nonpackable EventStore
  command host, Admin.Server.Host and Admin.UI executable projects. At Tenants'
  pinned EventStore `f85419d501f279e9a813435aa73538185ad26ada`, the command host
  still unconditionally references EventStore.Gateway source. Its current
  executable closure additionally includes Admin.Abstractions, Admin.Server,
  Server, Client, Contracts, DomainService, ServiceDefaults and SignalR, with
  Gateway linking command-host source and Server linking PayloadProtection
  files. The proposed exception covers this upstream executable closure only;
  ordinary Tenants library references still use packages.
- AppHost can compose the Memories search-index host. Inventory its active
  profile and executable closure before minimizing direct checkouts; do not
  remove a live product resource merely to avoid declaring a dependency.
  Existing live fixtures set `EnableMemories=false`; model tests still need
  direct-checkout path metadata. `scripts/run-tenant-audit-performance.sh` is
  not currently invoked by workflows; do not introduce it as an additional
  migration gate. Preserve the actual scheduled Category=Performance tier in
  pinned legacy `domain-ci.yml`, with its opt-in flags and nonzero execution
  validation. If a later chosen profile executes Memories.Server, its direct
  gitlink is `898f451111740ccf489d56f7c20cd47edc2fcdf6`; scope the published-host
  switch to that upstream server, never globally to Tenants under test.

Platform's direct pin is `c2236a9f95c37d4d2ef8dee3fe2cbfe5e9ab41d2`.
Builds.Tooling is nonpackable and must retain
`GlobalPropertiesToRemove="HexalithEventStoreVersion"` so it selects its own
authoritative catalog. FrontComposer currently auto-selects source for UI and
UI.Tests even with standard package flags; explicitly correct that CI mode to
use published Contracts, Shell, Testing and SourceTools.

Human choice: retain a named, gitlink-pinned exception for indispensable
executable/composition source and helpers, with ordinary library packages;
or require package/container-backed topology refactoring before adoption.
Neither route authorizes Debug CI, broad source-mode switches, nested
initialization, or suppressing source/profile refusal tests.

## Shared capability prerequisites

Extend Builds in the owning repository; never copy generic environment setup
into Tenants actions. Wait for a published acceptable release containing changes
and an updated CiCd builds-version before registering Tenants.

1. `Github/lib/ci_environment.py:setup_dapr` should record an exclusive generic
   receipt under RUNNER_TEMP immediately before its existing single `dapr init`:
   UTC start, preexisting volume names and run/job/attempt identity, followed by
   actual created container/mount identities and creation times. Expose its path via
   a documented `HEXALITH_DAPR_INITIALIZATION_RECEIPT` only after successful init.
   Keep initialization central. Cover old/reused/malformed receipts and failed
   initialization in `Github/lib/tests/test_ci_environment.py`.
2. Adapt Tenants `scripts/prepare-source-catalog-profile.py` and
   `scripts/tests/test_source_catalog_profile.py` to consume the receipt and
   supported shared job identity. Preserve checks for exact gitlinks, newly
   created running Redis, local fresh volumes, no bind mounts, correct localhost
   port, empty DB, private material custody and refusal to overwrite evidence.
   Separate worker-response profile selection from legacy job names.
   All cold profiles can reuse the once-created job-owned Redis with distinct,
   validated nonzero logical databases and private custody directories; reserve
   DB0 for the ordinary suite. Copy the complete Dapr component set privately
   using the AppHost's existing state/pubsub component overrides and set the
   same redisDB on both components. The authority clone preserves state-store
   backend metadata. Replace direct Redis reads in
   `SourceCatalogBootstrapEvidence`, `SourceCatalogOwnerProfileTests`,
   `AuthenticatedTenantsRouteTests` and `AspireTopologyTests` with one
   validated database-aware helper. Bind receipt/container/port/DB identity,
   prove that exact database empty before minting material, prevent profile
   database reuse, and test conflicting/invalid/substituted databases. Never
   reset a populated shared database to make freshness pass. This preserves
   one Dapr initialization without reusing another profile's business state.
   Keep each consumed database, receipt and private custody separate until
   cleanup; stop and await every topology before starting the next. Refuse
   occupied/reserved DBs, duplicate/noncanonical redisDB, disagreement between
   state/pubsub/authority/direct readers, changed component hashes and incomplete
   shutdown. Bind component hashes and exact producer revision in each private
   provisioning receipt. Official component documentation confirms redisDB for
   [state.redis](https://docs.dapr.io/reference/components-reference/supported-state-stores/setup-redis/)
   and [pubsub.redis](https://v1-19.docs.dapr.io/reference/components-reference/supported-pubsub/setup-redis-pubsub/).
3. Shared `ci.yml` already has `job-timeout-minutes`, default 30, but the schema,
   strict loader and production template have no corresponding registry knob.
   Add bounded `ciTimeoutMinutes` with unchanged default 30 in Builds schema and
   loader, plus fixtures/tests; render into the existing workflow input through
   `templates/.github/workflows/ci.yml.j2`, `tools/render.py` and contract tests.
   Measure the serialized preserved workload to select a sufficient explicit
   Tenants allowance. Existing parallel lanes allow 35–60 minutes each.
4. Remove module `Directory.Build.props:127` NU1901–NU1904 error demotion. Do not
   recreate blanket high/critical suppression centrally. Diagnose audited restore,
   fix vulnerable dependencies and centralize only policy-compatible justified
   exceptions in Builds Props/. Await their shared release if any is required.

Custom actions may run explicit project-level product variants and checks;
`Github/lib/guard_actions.py` rejects duplicated checkout/SDK/cache/Dapr setup,
solution-wide builds/tests and publishing/login building blocks. Keep the one
shared solution build and environment. Stage 4 hooks must reuse those assets;
retain indispensable profile-specific project builds rather than copying
legacy full-solution lanes.

## Registration and completion

Register solution, Dapr/browsers, appropriate registry pull, explicit test/hook
ownership and only genuine direct source inputs after the approved graph is
verified. Add `setup/Hexalith.Tenants.yml`, remotely reachable product gitlink,
`rendered/Hexalith.Tenants/` and perimeter in one CiCd candidate. Render and
validate from the released contracts, including live-main action availability.

Publishing inventory from `tools/release-packages.json`: Contracts, Client,
Server, Testing, Aspire packages, plus containers `tenants` and `tenants-api`.
Preserve this inventory while moving publication to central nightly scheduling.

Authenticate actual App delivery report/artifact and exact accepted source,
perimeter changes and foreign-content preservation; perform immediate legacy
cleanup. Require green adopted-main CI and the next genuinely scheduled central
release outcome. Local fixtures or manual dispatch do not establish completion.
