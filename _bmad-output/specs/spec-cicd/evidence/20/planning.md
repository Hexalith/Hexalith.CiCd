# Story 20 investigation

Recorded 2026-11-16. Planning only; no source changes, configuration writes,
pushes, dispatches, adoption or Azure operations have occurred.

## Accepted decisions, 2026-11-16 15:15 UTC

The human instructed “apply recommendation” after the option analysis. Both
choices are resolved in the implementation spec's approved intent: preserve
live Azure qualification as a narrowly scoped rendered manual job, and use the
EventStore-only pre-adoption verifier with the exact safeguards described below.
The job requires green CI at the same commit, the designated private runner,
approval environment, explicit authority/custody secrets and per-run digest.
Ordinary CI retains offline coverage and receives no Azure secrets. A separate
runner may build once; there is no cross-run binary-transfer mechanism.
The authorization does not supply Azure authority, establish private-runner
readiness, or authorize a live fault-injection run. Earlier open-choice text in
this investigation is historical; the implementation spec governs.

The worktree was fast-forwarded to freshly fetched CiCd main
`d3f3ef864c08cd89e390246d1a5d1dedffc4a92b` before implementation. Direct AI.Tools
and EventStore checkouts were synchronized to its gitlinks without initializing
nested submodules. The original workspace remains untouched.

## Isolation and source identities

- The human authorized an isolated worktree because the original workspace
  contains unrelated changes. Worktree: `/home/administrator/projects/hexalith/cicd-story-20`;
  branch: `story/20-migrate-eventstore`.
- Freshly fetched CiCd `origin/main` and worktree base:
  `d04c9ab7a8fa43dc6dac1f15d34135aba8e79551`.
- EventStore's committed CiCd gitlink:
  `fdb59895975e86a1e234325a01237f259cdbd53b`.
- Freshly fetched EventStore `origin/main`, used for the investigation:
  `f85419d501f279e9a813435aa73538185ad26ada`.
- CiCd's committed Builds gitlink:
  `fdda17c0a4538b0f7c99f813c20ca24b49006530`.
- `builds-version`: `v6.0.6`. Rendering reads exact tag objects, not newer
  working-tree code. Release/fetch a compatible minor API before changing the pin.
- Initialized only CiCd's directly declared Builds, EventStore and AI.Tools.
  EventStore's nested submodules remain uninitialized.

## Material changes from the historical story

Current EventStore `ci.yml` calls frozen `domain-ci.yml`, not v2. It also has
folded-snapshot compatibility, checkpointed-process package proof, contracts,
semantic-release governance and source-mode jobs. Current workflow count and
gate classification must drive migration, not the historical inventory.

Preserve genuine package/API/consumer, folded-snapshot, process, browser,
payload-protection, Dapr runtime and broker tests. Delete CI/source-mode wiring,
agent/story/evidence governance and workflow-text assertions. A mixed test file
must keep its independent product assertions.

### Product implementation map

All paths in this subsection are relative to EventStore.

- `Hexalith.EventStore.slnx`: Azure unit/live projects are included; retained
  `PayloadProtection.Tests` and `PayloadProtection.LiveSidecar.Tests` are not.
  Include retained projects so shared CI builds them once.
- `tools/folded-snapshot-compatibility/run.sh`,
  `scripts/verify-process-packages.py`, `scripts/pack-release-packages.py`,
  `scripts/validate-consumer-package-references.py`: preserve package and
  consumer assertions; change current-module packing to use existing Release
  output. Isolated compatibility-consumer builds test the product and remain.
- Explicitly classify `Server.LiveSidecar.Tests`, `PublishedCompatibility.Tests`
  and Azure live tests: their names would default to the unit stage. Excluded
  projects must map to enabled custom actions/jobs, never plain skips.
- `tools/qualify-dapr-brokers.py` and related qualification helpers own real
  broker/OpenBao/container fixtures. Kubernetes crypto needs kind 0.31.0,
  a pinned node image and Dapr 1.19.1. Treat these as product-fixture requirements,
  not evidence-governance gates.
- No `NuGetAuditSuppress`/NU190x waivers were found in tracked MSBuild files.
  Review audit properties in root props, Admin UI E2E and consumer helpers
  against the guard before adopting. Do not invent centralized waivers.
- Root `package.json`, its lockfile and `.husky` serve semantic-release/commitlint
  only and should be retired. Delivery removes owned legacy configuration.
- `docs/ci.md` is stale. Update it and
  `docs/concepts/dapr-infrastructure-boundary.md` with the approved routing;
  the latter requires retaining fixtures until an approved Platform replacement.

### Workflow-coupled test inventory

There are at least 20 workflow-coupled files in the fetched main, rather than
the historical 13. Remove workflow assertions, preserving product methods in
mixed files. Re-scan at implementation to catch subsequent main changes.

Under `tests/Hexalith.EventStore.Contracts.Tests/Packaging/`:

- `ContainerPublishingGovernanceTests.cs`
- `CorrectiveOciProvenanceReleaseTests.cs`
- `PostgreSqlImageGovernanceTests.cs`
- `ProcessPackageContractTests.cs`
- `ReleasePackageManifestTests.cs`
- `TrustedPublishingReleaseTests.cs`

Under `tools/tests/`:

- `test_check_committed_files.py`
- `test_dapr_runtime_qualification.py`
- `test_oq8_governing_design.py`
- `test_phase_4_gate_decision.py`
- `test_phase_4_gate_risk_matrix.py`
- `test_phase_4_story_completion.py`
- `test_phase_4_transition.py`
- `test_published_compatibility_workflow.py`
- `test_published_runner_exit.py`
- `test_published_workflow_context.py`
- `test_release_api_compatibility.py`
- `test_release_candidate.py`
- `test_release_publication_authority.py`
- `test_route_catalog_ci_tools.py`

Also classify `PackageOwnershipGovernanceTests.cs` (Dependabot policy),
`CommitMessagePolicyTests.cs` (legacy tool configuration), and the
`DeferredWorkGovernance.Tests` project under the same rule.

## Azure is a contract decision, not just secret forwarding

Current `.github/workflows/payload-protection-azure.yml` separates offline
adapter/schema tests from real Azure conformance. The latter requires:

- Manual dispatch with `run_live=true` and exact `authority_sha256`.
- Environment `payload-protection-azure-conformance` and private ephemeral
  self-hosted runner group `payload-protection-azure-private-ephemeral`.
- Explicit environment secrets `PAYLOAD_AZURE_AUTHORITY_JSON` and
  `PAYLOAD_AZURE_CUSTODY_JSON`.
- `tests/Hexalith.EventStore.PayloadProtection.AzureKeyVault.LiveTests/AzureLiveAuthority.cs`
  validates source-bound owner authority, expiry within 24 hours, exact resource,
  identity and network bindings, custody receipt and real fault windows.
  Defaults fail before Azure calls.
- `AzureDaprFixture.cs` in that project pins Dapr 1.18.7 and executable SHA.
  Substituting shared 1.19.1 is a behavior change, not routine setup.

Ordinary CI secret exposure or a generic GitHub-hosted Linux job cannot preserve
this behavior. The human must choose whether to amend the contract for rendered,
separately authorized qualification jobs, or renegotiate the story to retain
specialized live qualification outside shared CI. Do not auto-run cloud faults,
synthesize authority, change private networking, or silently retire product tests.

## Shared code map

- Builds `schemas/hexalith.ci.v1.json`, `Github/lib/ci_config.py`: closed objects,
  complete validated config, Windows-only job definitions. Extend additively
  for the human-selected model; keep shared code module-agnostic.
- Builds `.github/workflows/ci.yml`, `Github/lib/ci_pipeline.py`: fixed hook
  calls, stage classification and fail-fast execution.
- Builds `Github/prepare/action.yml`, `Github/lib/prepare_linux.py`: reusable
  preparation; do not assume it preserves Azure's private preprovisioned runtime.
- Builds `Github/lib/tests/test_ci_config.py`, `test_ci_pipeline.py`,
  `test_local_check.py`, and `Tools/ci/check_public_api.py`: compatibility and
  behavior verification. Do not add workflow-text assertion tests in Builds.
- CiCd `templates/.github/workflows/ci.yml.j2`: literal named secret mappings
  and rendered job contract. Release template changes only if the approved model
  requires them; do not expose Azure authority to unattended nightly jobs.
- CiCd `tools/render.py:pinned_contract,desired_tree`: tagged contract loading
  and schema validation before YAML rendering.
- CiCd `tools/check_global.py:check_interfaces`: reuse exact declaration and
  permission validation. `tools/validate.py:check_module` checks enabled actions
  on anonymous live module main, so product preparation must be pushed first.
- CiCd `tools/tests/test_render.py`, `test_validate.py`: synthetic tagged API
  fixtures and meaningful renderer/interface tests are permitted here.

## Read-only onboarding preflight

See `planning-preflight.json` for exact endpoint outcomes. Default profile is
`/home/administrator/.config/gh-cicd-agent`; no inherited token overrides were
present. Administrative GETs used the existing maintainer profile through a
command-local override; no default authentication configuration was changed.

Observed requirements not yet met: main rules require PR/status checks; no v*
tag ruleset is listed; an additional finite-release-branch ruleset exists;
`hexalith-release` is absent; managed pull-secret and NuGet-variable selections
do not include EventStore. The private Azure conformance environment is also
absent from the successful environment inventory. Retention is 90 days, default
CodeQL is not configured, Dependabot security updates are disabled, push
protection is enabled, and the publish switch is exactly true. Immutable
releases are disabled, to be enabled immediately after adoption as specified.
NuGet policies and module Zot identity remain to be verified/provisioned.

Installation membership remains **unverified**: authenticated GET
`user/installations/179966090/repositories?per_page=100` returned HTTP 403:
“You must authenticate with an access token authorized to a GitHub App, a
personal access token, or basic auth in order to list repositories for an
installation.” Org installation metadata was readable; this refusal does not
establish whether EventStore is selected. Use intended installation settings
readback or an authorized UI session; do not obtain the App key or switch push
credentials.

## Pre-adoption checker dependency

`run-with-temp python3 references/Hexalith.Builds/check.py`, from the EventStore
checkout, exits 2 because that nested file is absent; see
`pre-adoption-check.log`. Current fetched main also has no
`.github/hexalith-ci.json`, and pins legacy Builds commit
`e2bbbd0893f586e4d447ef8358ff747ea3d34435`.

Shared `local_check.run` requires an exact initialized Builds checkout, clean
committed module, CI JSON matching its tag/gitlink, full history and an accepted
`delivered/<Repo>` before it runs product stages. It has no pre-adoption mode.
Delivery requires custom actions already on live main. The human-approved
story 11 exception applies only to its pilots, so EventStore needs an explicit
bootstrap decision before any preparation push.

Proposed narrow exception: for EventStore product preparation before its actual
App adoption only, require package-mode Release build and every applicable
ordinary product unit/package/consumer check, commit/action/audit-policy
validation, and byte/mode/gitlink comparisons showing every owned portion
unchanged from freshly fetched main. Record intentionally owner-authorized
live-suite prerequisites separately; never claim an unexecuted lane passed.
This exception allows no owned-file edits, authority bypass, nested-submodule
initialization, skip markers or alternate push credentials. After adoption,
the ordinary shared checker is mandatory. If this exception is declined, stop
before preparation pushes until an approved bootstrap mechanism exists.
