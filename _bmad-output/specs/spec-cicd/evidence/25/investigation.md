# Story 25 investigation

## Repository context

Work is isolated in `/home/administrator/projects/hexalith/cicd-story-25`, branch
`story/25-migrate-timesheets`, created from freshly fetched CiCd main
`66e3a5a3a0e9bb01dd161c19349953594e01a22f` after the human approved an isolated
worktree. Existing work in the original checkout was left in place.

Timesheets main and the CiCd gitlink both resolve to
`bbb91319ee209333d29f07e53bd9b5e4adc40267`. The original story's stale-checkout
assumption is no longer true. GitHub contents were read before relying on the
checkout. Timesheets' own Builds pin is
`39973bfccb26ae98a3d25856a8f85950fecdf02a`; selected CiCd Builds is `v6.0.6` at
`fdda17c0a4538b0f7c99f813c20ca24b49006530`.

Only CiCd-root-declared Builds, Timesheets and AI.Tools were initialized. The
module baseline was read from the declared AI.Tools checkout, together with
Timesheets AGENTS.md, editorconfig, attributes, props, projects and boundary
documentation. No nested submodule was initialized and no remote mutation ran.

Two investigation agents examined module gates and shared runtime contracts.
Their findings were cross-checked against sources, current hosted job results,
a real checker run and independent discovery probes. No product code was changed.

## Administrative preflight

`preflight.json` records read-only maintainer metadata, identity, override
presence and canonical revisions. Account `admin: true` is not treated as token
permission proof. No secret values or credential file contents were read.

- No repository/inherited rulesets were returned: create the exact AD-21 main
  and version-tag rulesets in sequence.
- Only `production` exists, with manual review; `hexalith-release` and its
  module-specific Zot pair remain to be established. Never copy a generic push
  identity into it.
- `HEXALITH_RELEASE_PUBLISH_ENABLED=true` already exists; preserve its value.
- Retention is 90 days; secret-scanning push protection is enabled; default
  CodeQL setup is not configured; Dependabot security updates are disabled.
- Immutable releases are disabled; enable immediately after actual adoption.
- Four public releases were returned, no drafts. Refresh tags/orphan checks
  before changing release settings; do not delete published releases.
- Required Actions/Dependabot pull-secret selections and `HEXALITH_NUGET_USER`
  variable selections do not include Timesheets.
- The org `hexalith-cicd` App installation exists, selected-repository mode.
  Its Timesheets selection remains **unverified**. Under the intended maintainer
  profile, `GET user/installations/179966090/repositories?per_page=100` returned
  HTTP 403: `You must authenticate with an access token authorized to a GitHub
  App, a personal access token, or basic auth in order to list repositories for
  an installation.` The CLI also reported the endpoint needs `read:user`.
  Verify selection through the authorized installation settings or an adequate
  read interface; no broader credential was requested or substituted.
- The new scoped NuGet trusted-publishing policy and legacy policy/key package
  scopes were not inspected here. Record them at onboarding; unknown is not
  absent. The selected legacy NUGET_API_KEY/Zot username/SONAR secret lists
  returned no Timesheets membership; guessed legacy password/Azure names
  returned 404 and cannot certify global absence. Inventory real legacy names
  before post-adoption cleanup.

Only maintainer/CiCd gh profile directories were discovered locally. Availability
of a correctly scoped module-agent write credential remains to be verified
before a product push; do not use the CiCd or maintainer profile as a substitute.

## Current hosted failure

See `hosted-job-status.json` and the concise `hosted-diagnostics.json` excerpts.
CI run 43741211405 on the exact current main failed:

- `ci / build-and-test` failed while fetching unused Conversations pin
  `1d7d2d6b31381c5dc80699ee8be273424ccd36cb`. The new explicit dependency list
  should avoid this unrelated checkout rather than retarget its gitlink.
- The separate compiled AppHost job failed with missing EventStore namespaces,
  `IEventPayload`, `SharedProjectionScope` and other ReadModels types. It did
  not execute the retained configuration checks. Package references already
  exist. Assess framework/catalog compatibility, not duplicate references.

## Product execution and registration

`global.json` selects SDK 11.0.100 and Microsoft.Testing.Platform.
`Directory.Build.props` targets net10.0 and defaults Release/package mode.
The solution has 16 owned projects and six test suites. Default shared routing
puts five suites in stage 3 and IntegrationTests in stage 4.

Package-mode source edges are gated. Extra direct dependencies are EventStore
(AppHost metadata/fixture assets) and Works (the retained Works root-resolution
product tests evaluate its checkout). Omit unused siblings. Proposed setup:

```yaml
solution: Hexalith.Timesheets.slnx
hooks: [after-unit-tests]
submodules: [references/Hexalith.EventStore, references/Hexalith.Works]
```

Leave Dapr/browsers/registry false. Existing hosted probes run configuration,
model and construction/disposal paths without Start/Run or live services.
Existing live-Dapr/performance facts remain opt-in; default skips prove no
runtime acceptance. Preserve the AppHost and ServiceDefaults projects.

## Gate inventory and product preparation

| Existing surface | Migration treatment |
|---|---|
| Legacy shared compilation and six .NET suites | Keep via shared stages; fail at first failed project |
| `apphost-configuration` compiled fixture refusal/default/model/security checks | Keep in enabled product action, reusing shared build |
| `verify-test-evidence` and `scripts/validate-test-results.py` | Remove CI-result/evidence gate; actual test exits remain authoritative |
| `release-tooling` npm/BMAD/release-tool tests | Remove tooling gates; retain selected-index/fixture/privacy product coverage mixed into this job |
| `run-consumer-validation: true` and three package scripts | Keep six package+symbol/payload/dependency/isolated-consumer contracts; shared support required |
| Legacy CodeQL, dependency-review, commitlint and release jobs | Replace through owned delivery; nightly security/shared commit format/release remain |
| `scripts/tests/test_bmad_tooling.py`, `test_bmad_loop_hook.py` | Remove agent tooling gates |
| `scripts/tests/test_bundle_repair.py` | Remove obsolete npm machinery including YAML-asserting `ReleaseToolingWorkflowTests` |
| `scripts/tests/test_release_tooling.py` | Remove SourceGateTests/PrePublicationTests/TestEvidenceTests; split and retain InventoryTests/ConsumerRestoreTests/RestoreBackedValidatorTests product assertions |
| Architecture `FitnessTests/LaunchReadinessTests.cs` | Remove story/doc/evidence/agent gates; keep extracted AppHost SDK dependency invariant and no-UI-project assertion |
| Architecture `FitnessTests/PerformanceEvidenceTests.cs` | Remove doc/test-existence/skip governance; preserve actual functional/statistical/performance tests elsewhere |
| `ScaffoldGovernanceTests.CiCdGuideNamesThePinnedDotnetSdk` | Remove CI-document assertion; keep source/dependency/privacy assertions |
| Root `package.json`, `package-lock.json` | Product preparation deletes tool-only manifests; no `.husky/` found |
| Semantic-release/commitlint config and `bmad-testarch-ci` | Delivery removes must-be-absent owned paths; do not manually rewrite owned portions |
| NuGet audit waivers | None found. Existing NoWarn 1591/ASPIRE010 are unrelated |

Retained action commands are the Release configuration-only AppHost guard,
`scripts/test_magic_link_index_selection.py`, isolated fixture/privacy tests and
the package-consumer checks. `discovery-probe.json` demonstrates why wiring the
old scripts unchanged cannot pass the current scanner. The shared prerequisite
document carries the required bounded support and compatibility work.

## Workflow state and next decision

The human approved the Timesheets-only pre-adoption verification procedure on
2026-11-16. That decision is recorded in `pre-adoption-decision.md` and the
spec's intent block; the pilot exception is not inherited. The human subsequently
approved the overall migration spec and requested stopping before implementation,
then pushing the planning changes. The spec is marked `ready-for-dev`; its
implementation tasks remain open.
`pre-adoption-check.json` retains the original blocker evidence from the real
committed checker in a disposable standalone clone. Qualify/release shared
support before production registration. No product tests, full candidate
validation or adoption were claimed complete during investigation.
