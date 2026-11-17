# Epic 14 Context: Migrate Agents

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Move Hexalith.Agents onto the one shared CI pipeline and one shared release pipeline so this repository owns its generated callers, delivery adopts it, and remaining CI failures point at the product rather than local policy. Agents currently fails most sampled CI runs on a pinned-source gate, a package test-floor gate and late aggregate test reporting; adopting it is a required step toward every module using the same pattern and toward deleting legacy Builds CI/CD.

## Stories

- Story 14: Migrate Agents

## Requirements & Constraints

- Adopt Agents through the standard onboarding sequence: maintainer repo preconditions first, then product preparation that never touches owned files, then one CiCd commit of submodule plus setup plus render. Delivery is the only writer that adopts the module.
- Delete the pinned-source gate; it checks the Builds workflow pin, not the product. Classify "Enforce package test floors" with the product-only rule; keep it only if it checks the product. Architecture requires preserving the original five floors as product policy, along with SDK 11 / net11 / C# 15, existing product checks and owned bytes. CI/CD never rewrites `global.json`.
- Keep gates that check compilation, tests, security and dependency scans, commit format or package publishing. Delete gates that check CI itself, agent tooling, story evidence or workflow YAML, including tests that assert workflow YAML. Module-specific product checks that remain become custom actions at fixed hook points.
- Product preparation must prove full package-mode verification, real package consumers, released audit and commit checks, and exact fresh-main base and head before each push. After delivery, the normal standalone module checker is mandatory. Do not infer a release, a provisioned state or a nightly outcome from local preparation. AI.Tools and EventStore preparation substitutes do not apply.
- A failed hook-source scan blocks registration. Local snapshot qualification found every Agents hook source but is incomplete on the local Commons snapshot; keep registration blocked until complete fresh live-main discovery and duplication qualification pass. No scanner exception is approved.
- After adoption, immediately turn on immutable releases, delete every other nuget.org policy for the repo, and remove it from legacy org secrets, the legacy NuGet API key scope and the legacy Zot push identity.
- Done when Agents' CI is green and the next nightly release succeeds or reports nothing to release.
- Program success still applies: one CI pattern and one release pattern, main CI success at least 95% in every repo, only generated callers in the module, and no lasting CI/CD change from outside this repository.

## Technical Decisions

- Desired state lives in this repo's setup file. Render materializes a complete CI document and the owned perimeter; Agents runs through generated `ci.yml` and `release.yml` at an exact Builds tag, with the gitlink on the same tag. CI is one job: guard (including commitlint), package-mode Release build without audit, unit tests project by project stopping at the first failing project, then one environment setup, hooks and integration tests. CodeQL runs only at night. Only the Builds submodule is cloned. Fail-fast replaces the late "fail on blocking test failures" aggregate.
- Shared test policy maps discovered, non-excluded test projects to positive integer floors and can reject skips. Renderer defaults are empty floors and do-not-fail-skips; tagged readers require both fields. The shared executor supports this on Microsoft.Testing.Platform with xUnit and refuses unsupported runners before any tests run. Each project's tests finish before a failure stops its successor; no suite runs twice. This is the shared home for kept floor enforcement.
- Custom actions stay in the module, composite-only, at `.github/actions/`. Hooks are `after-unit-tests`, `after-integration-tests` and `nightly`. They reuse the job's restored Release build and never call Builds or rebuild the solution. An extra job is only for a different runner. Delivery's per-module checks require every named hook or job action to exist on live `main`.
- Owned in the module: workflows, `dependabot.yml`, the Builds gitlink and its `.gitmodules` section, instruction blocks and deny entries. Custom actions are module-owned, linted and scanned, never restored. Module agents use a contents-only token with no Workflows permission. A CiCd agent moves NuGet audit waivers into Builds `Props/`; adoption waits until `builds-version` names a tag that contains them. Delete a tool-only root `package.json`, lockfile and `.husky/` when they exist only for semantic-release or commitlint.
- Maintainer preconditions for this repo: add it to the App installation; delete unmarked drafts and incomplete-release leftovers; set the `main` and `v*` tag rulesets; create `hexalith-release` with this module's own Zot push pair and add a nuget.org policy for `release.yml` scoped to its package-ID glob, beside any existing policy; set the publish kill switch to exactly `true` or `false`; 90-day artifact and log retention; grant org secrets and variables; turn off code-scanning default setup and Dependabot security updates. The App key never enters a module or an agent session.
- Delivery adopts in one `build(cicd)` commit that replaces the perimeter and deletes legacy workflows. A module with no delivered ref yet receives nothing. Frozen Builds files stay unchanged until every managed module has moved.

## Cross-Story Dependencies

- Shared CI, release, perimeter, delivery, guard, nightly scheduler, module-agent qualification and delivered agent instructions must already exist (stories 1–10). The pilot (story 11) pauses for one real night before later migrations; AI.Tools (story 12) and Works (story 13) precede Agents in the sequence.
- Registration and adoption wait on live-main hook discovery plus duplication qualification, and on a Builds tag that contains any Agents waivers moved to `Props/`.
- Story 27's legacy Builds deletion waits until all 17 modules, including Agents, are adopted.
