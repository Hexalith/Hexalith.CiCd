# Epic 13 Context: Migrate Works

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Adopt Hexalith.Works onto the shared CI and release pipelines so this repository generates, delivers and enforces its CI/CD. Works is the second module in the approved plain-CI cohort. The baseline sample recorded 56 CI runs with no successes; most failures were local policy or evidence gates and two setup steps, with real test failures reported only at the end. The epic is done when one delivery commit adopts the module, its CI is green, and the next nightly release succeeds or reports nothing to release.

## Stories

- Story 13: Migrate Works

## Requirements & Constraints

Follow the onboarding sequence in order. The maintainer first meets per-repo preconditions: App installation, stale CodeQL configs and leftover drafts or tags removed, exactly the `main` (no delete or force-push) and `v*` (no update or delete) rulesets, a main-only `hexalith-release` environment holding this module's own registry push identity, a nuget.org Trusted Publishing policy for `release.yml` naming that environment and scoped to Works package IDs added beside any existing policy, default code scanning and Dependabot security updates off, `HEXALITH_RELEASE_PUBLISH_ENABLED` exactly `true` or `false`, 90-day retention, and org secret and variable grants.

Module-agent sessions then prepare product-side work in `references/Hexalith.Works`: keep genuine product checks (and turn module-specific ones into custom actions), delete gates and workflow-YAML tests the gate rule removes, delete module NuGet audit waivers, and delete a tool-only root `package.json`, lockfile and `.husky/` used only for semantic-release or commitlint. Never edit owned files there. A CiCd agent adds any waivers to Builds `Props/`; adoption waits for a `builds-version` tag that contains them. Then one CiCd commit adds the submodule, setup file and render; delivery adopts. Immediately after adoption the maintainer turns on immutable releases, deletes every other nuget.org policy for the repo, and removes it from legacy org secrets, the `NUGET_API_KEY` scope and the legacy Zot push.

A gate stays only if it checks the product: compilation, tests, security and dependency scans, commit format or package publishing. Delete jobs or steps that check CI itself, agent tooling, story evidence or workflow YAML. Works is grouped with the workflow-policy, pinned-source and evidence gates, but the inventory does not name which of its sampled gates belong there. Classify these during migration; do not invent verdicts:

- Lint release tooling
- Preserve source identity checks
- Platform R1–R11 parity and rollback

The shared pipeline replaces the failing setup steps "Prepare package dependencies" and "Prepare verified published Builds artifacts". Fail-fast unit tests replace the late aggregate "Fail on blocking test failures". Custom actions are enabled only from this repository's setup file. Test projects cannot be skipped. Module files cannot waive the release vulnerability gate.

Works has no approved pre-adoption checker substitute. The AI.Tools and EventStore exceptions do not extend here. Require a successful standalone `python3 references/Hexalith.Builds/check.py` with Builds as a direct dependency before adopted-module pushes; without an approved substitute, stop before pushing. Product writes use the restricted module credential; CiCd and Builds use the CiCd-agent token; never the maintainer's personal login. Start product branches from freshly fetched current `main`. Do not import owned CI/CD through PR Update branch; reapply only product changes. Do not revoke legacy publishing until delivery actually adopts. Adoption is not a product release.

Must be absent from the module after delivery: semantic-release and commitlint config and dependencies, the commitlint Husky hook line, `Directory.Build.rsp`, and `bmad-testarch-ci`.

## Technical Decisions

Delivery is the only writer of owned files into modules (restore is the one exception). The setup file turns on shared stages and enables custom actions. Shared CI is one job, cheapest and most likely to fail first: guard and commitlint; a Release package-mode build with warnings as errors and NuGet audit off; unit tests project by project, stopping at the first failing project; then one environment setup and integration or hooks. Local `check.py` is stages 1–3 of that job. CodeQL runs only in the nightly release. CI checks out Builds plus only the submodules listed on the setup knob. Works' package-mode tests read Platform and Parties, so those belong on that list. Dependabot is rendered and never covers `github-actions` or `gitsubmodule`. The SDK pin stays in module-owned `global.json`. Shared workflow linting lives in Builds; do not keep a module-local CI-linting-CI job.

Test projects with names ending in `IntegrationTests` or `Integration.Tests` or `AppHost.Tests`, or containing `E2E`, go to stage 4. Everything else, including Works' `UnitTests`, `PropertyTests` and `ArchitectureTests`, goes to stage 3. The setup file may only move a project to stage 4 or hand it to an enabled hook or job. If the classifier misroutes a project, fix it in the setup file.

Custom actions live in the module at the named hook points (`after-unit-tests`, `after-integration-tests`, `nightly`) and reuse the job's build and environment. They contain no generic building blocks and no code shared with another module. An extra job is only for another operating system. This cohort is plain CI: no Aspire stage-4 first, no extra-runner first, and no first kept product-check custom actions unless classification keeps a Works-specific product gate.

Builds' package catalog already carries Works-specific conditions. Those are product build data; do not strip them as a module-name leak. After adoption the publish job runs in `hexalith-release` from `main` only. An adopted module with drifted callers, a failed adoption push or immutable releases off is not released and turns the nightly run red.

## Cross-Story Dependencies

This epic follows the approved order: after the Commons and PolymorphicSerializations pilot and after AI.Tools, before Agents. It consumes the shared pipelines, delivery, module-agent token, and ownership instructions from earlier stories. Waiver moves must land in an acceptable Builds release before adoption. Gate verdicts recorded here must not be recreated later. Legacy Builds CI is deleted only after all 17 modules are adopted.
