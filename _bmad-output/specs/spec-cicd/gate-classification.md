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
- Works' source-identity check (`scripts/verify-source-debug.py`) and Platform R1–R11
  parity/rollback job. See [Works classification](#works-classification-story-13).

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
- The repo tests that assert workflow YAML: Folders' original 27-file estimate is superseded by the [story 17 per-method inventory](evidence/17/gate-classification.json); EventStore 13, FrontComposer 13, Tenants 12, Parties 11, Memories 11.

## Not yet classified

These gates failed in the sample but have no explicit verdict in the source. Apply the rule during migration.
- Folders: locally classified in [story 17](evidence/17/gate-classification.json). Keep actual provider smoke, pinned provider classification/redaction, source whitespace/analyzers, capacity operations, and complete product suites. Remove repeated scheduled test orchestration and CI/tooling/story-evidence assertions. The local candidate remains blocked on policy and genuine product prerequisites; this classification does not establish adoption.
- Parties: "Finalize exact CI owner", "Require the owning integration job to pass"
- FrontComposer: "Gate 2b: Infrastructure governance", "Coverage Summary", "Quarantine Summary"
- Builds: the `Props/` catalog validators in `Tools/`, about 13 PowerShell scripts (about 4,000 lines) that Builds' `ci.yml` runs today. They check the package catalog, so they are product checks (AD-11). Each is classified in the change that rewrites `builds-release.yml`. Kept ones go on running in `builds-ci.yml`, in their current language.

## EventStore release-readiness classification

Retire the `Phase 4 gate risk matrix` workflow's matrix-tool fixtures and live
story-evidence evaluation during owner-controlled EventStore migration. The
[failed run](https://github.com/Hexalith/Hexalith.EventStore/actions/runs/43981244557)
at `8d409495926a568c5e2679f726b76f7de5dd85d5` reports missing human seals and
attestations, unbound story-owned bindings and insufficient declared assurance.
These check CI/story governance under the rule above. Preserve the original
failed report; do not fabricate seals, relax its validator or edit the owned
module workflow directly. The [source-bound readiness packet](../../implementation-artifacts/evidence/eventstore-release-readiness-2026-11-17/20261116T234322Z/README.md)
records the actual failure and publication boundaries.

Keep the independent product checks: package-mode compilation, Contracts and
typed-query generator tests, Gateway behavior, published API compatibility,
payload protection, Dapr broker/runtime controls, security/dependency scans,
commitlint and package publication verification. This classification does not
remove product tests or enable release publication. EventStore registration,
complete owned-perimeter delivery and successful adoption qualification remain
the separate story 20 prerequisites for central nightly eligibility.

The local Contracts run at `3b2350e7c1fff640131f8101596c78a59e31a03f`
also reproduces `CommitMessagePolicyTests.CopilotInstructionsDelegateCommitlintContractToSharedInstructions`
failing on stale shared-instruction wording. Retire this agent-tooling class
during the same migration; its cases inspect instruction, Markdown, hook and
configuration text rather than run commitlint on history or message inputs.
The [checked proposal](../../implementation-artifacts/evidence/eventstore-release-readiness-20261117/retire-agent-policy-assertions.json)
preserves the actual pinned commitlint workflow, policy and hook. Package
boundary tests needing real candidate archives remain product checks and must
run with their documented package inventory.

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

## Works classification (story 13)

Apply the gate rule; do not invent a fourth category. Recorded during story 13 from
Works `ci.yml` jobs `platform-parity`, `scripts-lint`, and `ci`, plus the three unnamed
sampled names. This classification does not adopt the module or enable registration.

- **Lint release tooling:** delete actionlint and tests that parse workflow YAML or
  story evidence, including `scripts/tests/test_release_{builds_compatibility,hook_permissions}.py`,
  `tests/Hexalith.Works.ArchitectureTests/FitnessTests/CiCdConfigurationTests.cs`, and
  `PlanningEvidenceDocumentationTests`. Keep `scripts/verify-source-debug.py` (reviewed
  EventStore/PolymorphicSerializations source↔package identity) as a product action.
- **Preserve source identity checks:** keep. Same product action as `verify-source-debug.py`.
- **Platform R1–R11 parity and rollback:** keep as a parallel extra Linux `jobs` action
  (`timeoutMinutes: 180`, own Dapr). Shared CI submodule list stays Platform + Parties;
  the action keeps initializing the gitlinks it needs. Do not put R1–R11 on the shared
  CI job or the nightly hook.

Shared stage 3 replaces late "Fail on blocking test failures". Shared package-mode
build replaces the two failing setup steps except published Builds artifacts still
needed inside the R1–R11 action. Leave the nine allowlisted `[Fact(Explicit = true)]`
Platform-lane tests in `IntegrationTests`; do not port `allowed-not-runnable-tests`.
If adopted stage 4 still selects them, add a test-project trait/filter, not a CI skip.

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
  without rebuilding Agents or retaining receipts. The current `builds-version`
  pin `v6.4.4` contains the shared floors/fail-skips fields and central
  NU1901/NU1902 treatment. The [2026-11-21 fresh live-main scan](evidence/14/registration-20261121/README.md)
  of the prospective registry discovers six Agents hook sources with no errors
  and reports zero cross-module copies. Coverage is still incomplete: Commons,
  Conversations, McpCli, PolymorphicSerializations and Works have unresolved
  discovery expressions, which belong to their owning migrations. On 2026-11-21
  the human decided that Agents qualifies on its own scan row, no run-level
  errors and no finding involving Agents, the test nightly acceptance applies.
  No scanner exception is approved.
- The registration enables `after-unit-tests`, both C# and JavaScript/TypeScript
  CodeQL, the five floors and fail-skips. A simulated delivery onto Agents main
  at `v6.4.4` passes the guard and all five suites, then the hook fails: 11
  `eng/consumer-executable-assets.json` rows still record the pre-delivery
  catalog (EventStore 5.3.0, FrontComposer.Shell 6.0.0). Only the version
  fields differ; every SHA-256 is unchanged. A simulated version-only product
  update from delivered main passes the guard, the floors and the
  six-package/seven-consumer hook. The module agent applies it after delivery,
  because the pre-delivery pin still selects the old versions.
- After delivery, `package.json` keeps only an empty tool-only stub, and
  `package-lock.json` stays. The root npm files were restored on Agents main
  for the legacy release. Deleting both is a module-agent product step (AD-21
  step 2) once delivery has removed the legacy release.
- Delete pinned-workflow-source, npm tooling, workflow-text and story-evidence
  assertions, traceability-manifest checks and redundant full/focused runners.
  Remove the registered nested-submodule automation scan from
  `ForbiddenHostingOwnershipTests`; it checks agent tooling and workflow text.
  Retain its hosting-boundary product tests, with the existing validator-data
  exception following the validator's move to `nuget_package_validation.py`.
  Historical source-mapping runners remain outside hosted gates. Runtime tests
  with story-related names stay.
- Delivery owns legacy workflow/release/commitlint removal. Module preparation
  preserves that perimeter. The pilot checkpoint was accepted on 2026-11-19, and
  `v6.4.4` is acceptable. `setup/Hexalith.Agents.yml` and its render are prepared
  locally but not committed. Publication waits for the AD-21 maintainer
  provisioning. Authenticated App delivery follows publication.
