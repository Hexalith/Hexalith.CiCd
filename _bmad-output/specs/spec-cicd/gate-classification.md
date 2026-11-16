# Gate classification

The gate rule and the first keep/delete classification. Serves CAP-10. The whole classification is *verify during migration*.

## Rule

- **Keep** a job or step if it checks the product: compilation, tests, security and dependency scans, commit format, or package publishing.
- **Delete** it if it checks the CI itself, agent tooling, story evidence, or workflow YAML text.
- Product checks specific to one module are kept and become custom actions.
- Repo tests that assert workflow YAML are deleted.

The risk is small, because all product tests stay. A deleted gate may once have caught something real.

## First classification

**Keep, as custom actions:**
- Folders' accessibility and end-to-end gates, and FrontComposer's browser regression tests.
- Folders' contract-spine gates, which check API contracts and generated artifacts. Today they fail 74% of the time.
- Folders' provider smoke test (`nightly-drift`), moved into the `nightly` hook.
- EventStore's payload-protection tests and Dapr broker tests.

**Delete:**
- FrontComposer's flaky-test governance (901 lines of Python), its quarantine nightly run, and its IDE parity check ("Story 9-3").
- Parties' `rc-gate` and startup diagnostics.
- Tenants' `story-guards`, which tests BMAD tooling in CI.
- The story- and BMAD-named jobs in `ci.yml` of Memories, Parties, Projects, and ChatBot.
- McpCli's `agent-instructions-sync`. It is agent tooling and belongs in AI.Tools' own sync.
- The three `recover-partial-release.yml` copies, replaced by a release that is safe to rerun.
- The workflow-policy, pinned-source, and "evidence" gates in Agents, Projects, Works, ChatBot, and Builds. Sampled examples:
  - Agents: "Require the pinned Builds workflow source"
  - Projects: "Validate workflow policy / production-authority scheduling guard"
  - ChatBot: "story-evidence-integrity" and the "release evidence gate"
  - Builds: "Require every validation job to pass", the `build-and-test` aggregator. It leaves `builds-ci.yml` with the G-4/G-6 qualification jobs and tests, in the change that rewrites `builds-release.yml` (AD-20).
  - Works belongs to this group, but the source doesn't say which of its sampled gates are in it (see Not yet classified).
- The repo tests that assert workflow YAML: Folders' original 27-file estimate is superseded by the [story 17 per-method inventory](evidence/17/gate-classification.json); EventStore 13, FrontComposer 13, Tenants 12, Parties 11, Memories 11.

## Not yet classified

These gates failed in the sample but have no explicit verdict in the source. Apply the rule during migration.
- Folders: locally classified in [story 17](evidence/17/gate-classification.json). Keep actual provider smoke, pinned provider classification/redaction, source whitespace/analyzers, capacity operations, and complete product suites. Remove repeated scheduled test orchestration and CI/tooling/story-evidence assertions. The local candidate remains blocked on policy and genuine product prerequisites; this classification does not establish adoption.
- Works:
  - "Lint release tooling"
  - "Preserve source identity checks"
  - "Platform R1–R11 parity and rollback"
- Parties: "Finalize exact CI owner", "Require the owning integration job to pass"
- FrontComposer: "Gate 2b: Infrastructure governance", "Coverage Summary", "Quarantine Summary"
- Builds: the `Props/` catalog validators in `Tools/`, about 13 PowerShell scripts (about 4,000 lines) that Builds' `ci.yml` runs today. They check the package catalog, so they are product checks (AD-11). Each is classified in the change that rewrites `builds-release.yml`. Kept ones go on running in `builds-ci.yml`, in their current language.

## ChatBot runtime classification during story 19

Keep the genuine runtime checks and preserve their roles with whole test projects:

- `Hexalith.ChatBot.Live.IntegrationTests` retains the authenticated refusal smoke,
  production-browser matrix and correction-propagation runtime health checks in CI.
  Run the whole project with runner-enforced `failSkips`. Ordinary integration retains
  its in-process topology, recovery harness and cleanup contracts in CI.
- `CommittedGovernedStateShouldPassM2StopShipSweepsInRealDaprTopology` and
  `GovernedNoteShouldProjectIdenticalDurableEndStateRegardlessOfDeclaredOrigin`
  require accepted canonical commits and durable state. Retain their complete scenario bodies
  in a dedicated `Hexalith.ChatBot.Release.Tests` project, assigned to the enabled nightly hook
  with `tests.exclude`. Run that whole project on every release. A real failure blocks publication.
- The complete destructive recovery sweep stays in `Hexalith.ChatBot.Recovery.Tests`, separately
  assigned to nightly and run on Sunday UTC. A failed release-only gate must not suppress a due
  recovery after successful runtime preparation unless the run was canceled.

The legacy ordinary test job did not opt into Tier3. Its separate live CI job selected only
the refusal smoke and browser matrix; the release workflow selected M2 as an additional gate.
The origin-parity positive-state test was not selected by either live job. Whole-project nightly
routing retains that product check as an effective release gate instead of dropping it or
changing its expected committed state to match the current refusal implementation.

The ordinary integration project's existing manual independent-observer producer remains
unchanged and visibly optional. It requires independently enrolled trust and signed native
observations; neither the legacy CI nor release workflow selected it. Report that exact case
as unexecuted when its operator prerequisites are absent, and reject any other unexpected
skip. The required live, release and recovery projects reject every skip. This preserves
the legacy required-live guarantee without inventing observer enrollment or claiming native
mutation/atomic acceptance from the manual producer.

The current production admission validator unconditionally refuses atomic participation.
That product-contract gap must remain visible in release results until an accepted owner
implementation exists. It is independent of removable story evidence, workflow-text assertions
and artifact bookkeeping. The private catalog fixture must use a genuinely new owned business
backend and the pinned SDK's explicit owner-custody contract; model-only keys or invented
observations are not acceptable runtime evidence.

## Why gates can't come back

- Module agents can't add workflows (token scoping, the guard, and delivery).
- Custom actions can only be enabled from this repository, through the setup file. That change is also where the gate rule and the common-code check are applied.
- Test projects can't be skipped. The setup file can only move one to stage 4 or hand it to an enabled hook or job (AD-13). The guard rejects module test-filter properties (`TestingPlatformCommandLineArguments`, `VSTestTestCaseFilter`), and commitlint rejects `[skip ci]`-family markers.
- Module files can't waive the release's vulnerability gate. The guard rejects them, and waivers live only in Builds' `Props/` (AD-8, AD-10).
- The rule is written into this repository's `AGENTS.md`. The delivered instruction block forbids tests that assert workflow YAML. It is the only lasting control for that rule.

## Agents classification (story 14, local preparation)

- Keep original Release test floors (Contracts 529, Client 6, Agents 787,
  Server 549, UI 1073), fail-skips and all five suites in stage 3. Builds owns
  count/skip execution for both CI and local checking; no second suite runner.
- Keep whole-repository package authority with the existing exclusions and the
  six exact frozen Platform evidence paths approved by the human on 2026-11-16,
  dependency-mode rejection targets, and stable EventStore capability floor as
  product tests. The floor script has a neutral product name.
- Keep six-package inventory, archive integrity, UI static assets and isolated
  consumers. The prepared hook uses existing Release output and cleaned scratch,
  without rebuilding Agents or retaining receipts. Hook enablement is pending
  complete cross-module duplication qualification. Agents source discovery passes
  the unchanged scanner. The [local three-module qualification](evidence/14/local-readiness-20261116/README.md)
  remains incomplete because the local Commons snapshot has four unresolved
  discovery expressions; zero reported copies does not establish clean coverage.
- Delete pinned-workflow-source, npm tooling, workflow-text and story-evidence
  assertions, traceability-manifest checks and redundant full/focused runners.
  Remove the registered nested-submodule automation scan from
  `ForbiddenHostingOwnershipTests`; it checks agent tooling and workflow text.
  Retain its hosting-boundary product tests, with the existing validator-data
  exception following the validator's move to `nuget_package_validation.py`.
  Historical source-mapping runners remain outside hosted gates. Runtime tests
  with story-related names stay.
- Delivery owns legacy workflow/release/commitlint removal. Module preparation
  preserves that perimeter. Production registration awaits the accepted pilot,
  an acceptable Builds release, provisioning and authenticated App delivery.
