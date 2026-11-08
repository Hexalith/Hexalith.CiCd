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
- The repo tests that assert workflow YAML: Folders 27 files, EventStore 13, FrontComposer 13, Tenants 12, Parties 11, Memories 11.

## Not yet classified

These gates failed in the sample but have no explicit verdict in the source. Apply the rule during migration.
- Agents: "Enforce package test floors"
- Folders: the drift and policy lanes, apart from the provider smoke test (`nightly-drift`), which is kept
- Works:
  - "Lint release tooling"
  - "Preserve source identity checks"
  - "Platform R1–R11 parity and rollback"
- Parties: "Finalize exact CI owner", "Require the owning integration job to pass"
- FrontComposer: "Gate 2b: Infrastructure governance", "Coverage Summary", "Quarantine Summary"
- Builds: the `Props/` catalog validators in `Tools/`, about 13 PowerShell scripts (about 4,000 lines) that Builds' `ci.yml` runs today. They check the package catalog, so they are product checks (AD-11). Each is classified in the change that rewrites `builds-release.yml`. Kept ones go on running in `builds-ci.yml`, in their current language.

## Why gates can't come back

- Module agents can't add workflows (token scoping, the guard, and delivery).
- Custom actions can only be enabled from this repository, through the setup file. That change is also where the gate rule and the common-code check are applied.
- Test projects can't be skipped. The setup file can only move one to stage 4 or hand it to an enabled hook or job (AD-13). The guard rejects module test-filter properties (`TestingPlatformCommandLineArguments`, `VSTestTestCaseFilter`), and commitlint rejects `[skip ci]`-family markers.
- Module files can't waive the release's vulnerability gate. The guard rejects them, and waivers live only in Builds' `Props/` (AD-8, AD-10).
- The rule is written into this repository's `AGENTS.md`. The delivered instruction block forbids tests that assert workflow YAML. It is the only lasting control for that rule.
