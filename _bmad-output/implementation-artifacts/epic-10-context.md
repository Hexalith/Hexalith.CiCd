# Epic 10 Context: Module-agent permissions and instructions

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Give module agents a verified permission boundary and clear instructions that keep CI/CD policy in Hexalith.CiCd while allowing ordinary product development. GitHub must refuse workflow changes and workflow dispatches made with the restricted module credential. Delivered instructions and local Claude Code denies explain the same ownership boundary, direct agents to fix product failures, and preserve each module's unrelated settings and instructions.

## Stories

- Story 10.1: Module-agent token
- Story 10.2: Agent instructions and deny entries

## Requirements & Constraints

Module credentials are fine-grained tokens limited to module repositories, with Contents and Pull requests write access and no Workflows, Administration, Actions, Variables or Secrets write access. CiCd and Builds use a separate credential. Agent sessions never substitute the maintainer's personal login. Keep token values, App keys and publishing credentials out of source, logs and module workspaces. Preserve the configured default profile when selecting a dedicated qualification credential.

Qualification requires actual GitHub responses. A refused workflow-changing push and a refused valid dispatch establish the token-level block; a dry run, mock, public metadata read or successful login cannot establish these outcomes. Successful ordinary product writes distinguish a workflow-specific restriction from a repository-wide refusal. Account administration rights describe the account rather than the token's API grants. An unreadable settings inventory leaves configuration unverified. Keep exact revisions, server responses, positive controls, unchanged ref state and cleanup evidence together.

Branches begin from fresh current main. Use disposable refs and PRs for qualification, never merge probes or change a module main ref, and preserve owned content. Existing real module history can establish pre-adoption GitHub behavior without prior CiCd delivery. Distinguish those findings from proof following an actual delivery. Never manufacture an adoption, broaden a credential or edit owned files to make a probe possible.

Agent instructions identify CiCd as the owner of workflows, CI configuration, Dependabot configuration, the Builds gitlink and its submodule section, delivered instruction blocks and required Claude deny entries. Agents run the shared Builds check before pushing, fix product failures, and report pipeline defects and permission refusals without weakening audits, tests or credentials. Instructions prohibit skip markers and skip-checks trailers. Releases use the central nightly process rather than merge-triggered publishing.

Keep gates that check compilation, tests, security, dependencies, commit format or publishing. Product checks specific to a module become custom actions enabled through the central registry. Remove gates that check CI itself, agent tooling, story evidence or workflow YAML, including repository tests that assert workflow text. Resolve unclear classifications during migration. This policy remains in the instructions so subsequent agents do not recreate removed gates.

## Technical Decisions

Token scoping is the first enforcement layer. The shared guard compares the module's owned perimeter against its delivered state and rejects drift; restore and delivery repair it. Instructions and Claude Code denies supplement those mechanisms. The design assumes careless agents, permits direct product pushes, and does not rely on human review, CODEOWNERS or required-status-check rulesets as enforcement.

Delivery manages one marked ownership block in AGENTS.md, CLAUDE.md and Copilot instructions, preserving surrounding foreign content. Required Claude deny entries are merged into each module's project-local settings while preserving its allow list, unrelated deny entries and other keys. Launch Claude Code from the module root so rooted Edit patterns apply correctly. Reads remain available. Never install these denies in machine-wide settings, where they would prevent authorized work in Builds. File-level patterns cannot isolate owned JSON entries, instruction blocks or individual submodule sections; instructions and the shared guard protect those portions.

The shared AI.Tools guide links to the canonical ownership block and drops release-on-merge guidance. The pipeline-scaffolding skill is absent from managed modules. Shared policy is authored centrally rather than patched into module-owned checkouts.

## Cross-Story Dependencies

Story 10.2 consumes 10.1's verified workflow-push refusal, dispatch refusal and product-only branch result. The human's 2026-11-15 sequencing decision accepts those three results plus cleanup for the handoff. Meaningful PR Update branch and Pull requests write remain explicitly unverified after GitHub refused the historical-workflow head fixture before a PR could exist. Instructions temporarily prohibit Update branch pending the pilot test; a fixture-creation refusal must not be presented as that operation's result.

Story 11 creates a disposable product-only branch and PR from current main before real pilot delivery. After delivery introduces workflow changes, it attempts that PR's meaningful Update branch with the same restricted credential and repeats product branching from fresh post-delivery main. Record actual pre-delivery base/head, delivery and post-delivery revisions, server outcomes and cleanup. Confirm or correct the instruction restrictions before accepting the pilot checkpoint. Missing fixture creation or an update that cannot exercise the delivery's workflow difference remains a pilot blocker.
