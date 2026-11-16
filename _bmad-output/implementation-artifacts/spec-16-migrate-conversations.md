---
title: '16 — Migrate Conversations'
type: 'chore'
created: '2026-11-16'
status: 'ready-for-dev'
baseline_commit: 'd04c9ab7a8fa43dc6dac1f15d34135aba8e79551'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/specs/spec-cicd/evidence/16/planning.md'
  - '{project-root}/_bmad-output/specs/spec-cicd/evidence/16/gate-inventory.md'
  - '{project-root}/_bmad-output/specs/spec-cicd/evidence/16/shared-preparation-design.md'
  - '{project-root}/_bmad-output/specs/spec-cicd/evidence/16/windows-and-fixture-design.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Conversations' legacy pipelines include .NET 11 product checks
requiring producer-selected imports, browser/Dapr setup, an isolated fixture
and protected Windows checkout.

**Approach:** Follow AD-21 to preserve product coverage, prepare module actions,
register/render the module and let App delivery adopt it. Completion requires
green Linux/Windows CI and the next genuine scheduled nightly outcome.

**Human decisions, 2026-11-16:** Include generic shared producer preparation,
protected Windows checkout, qualification and a Builds release in story 16.
For Conversations preparation pushes before adoption only, require exact-input
package-mode builds/tests and applicable product checks, policy/commit
validation and owned byte/mode/gitlink preservation. Normal check.py remains
mandatory after adoption. This grants no owned-file edits or weaker tests/audits.

## Boundaries & Constraints

**Always:** Preserve SDK/runtime selections, product assertions and foreign
instructions/settings. Use module-agent credentials for product writes,
CiCd-agent for CiCd/Builds and command-local maintainer access for administration.
Keep Linux TestSupport coverage alongside Windows. Use run-with-temp for jobs;
retain logs outside scratch. Apply the product-only gate rule and centralize
justified waivers in a released Builds pin. Preserve concurrent onboarding.

**Never:** Directly edit module owned-perimeter files, initialize nested
submodules, manufacture producer metadata, suppress tests/audits, disable Windows
path protections, give custom actions checkout/build/environment setup, obtain
the App key, or claim adoption/nightly results from fixtures. Only delivery or
restore writes owned files. Remove legacy publication access after adoption.

## I/O & Edge-Case Matrix

| State | Expected behavior |
| --- | --- |
| Missing prerequisite or denied administrative read | Record exact failure; do not infer absence or adopt. |
| Producer imports unavailable before project evaluation | Fail; never invent an enrollment identity or defer setup to a late hook. |
| Unsafe Windows archive paths | Preserve bytes and protected checkout; module action cannot repair an earlier checkout failure. |
| Fixture catalog/lock mismatch | Deliberately qualify successor locks; retain seven product assertions. |
| Failed delivery or no releasable change | Retain authenticated per-module result; no forced release or completion claim. |

</frozen-after-approval>

## Code Map

- Context companions supply exact identities, administration, resolved gate
  dispositions, source files, APIs and failure tests. Builds/module paths below
  are relative to their respective `references/Hexalith.*` checkouts.

## Design Notes

Add nullable `moduleManifest`/`windowsCheckout`. Managed preparation binds the
accepted central catalog and truthful Platform provenance; legacy modes/hashes
stay unchanged. Separate candidate qualification binds exact product inputs,
committed render and external released Builds; production rejects its authority.
Windows uses validated outputs and protected cone sparse-index checkout with
immutable excluded-tree IDs; ordinary index expansion is unsafe.

## Tasks & Acceptance

**Execution:**

- [x] `evidence/16/` — record human decisions, source/preflight investigation,
  gate inventory, shared design and native Windows feasibility probes.
- [ ] `evidence/16/` — verify/provision AD-21 preconditions in order, preserving
  existing access until adoption and recording exact readbacks/access failures.
- [ ] Builds `schemas/`, `Github/lib/module_preparation.py`, producer/CLI,
  orchestration and `Github/prepare/` — implement companion contracts and tests
  for managed/candidate authority, one preparation lifetime and protected checkout.
- [ ] Architecture spine, `setup/README.md`, `templates/.github/workflows/ci.yml.j2`
  — document/export validated inputs and active catalog authority. Qualify defaults,
  CI/local/Windows/release parity; publish an acceptable Builds/CLI release.
- [ ] Module `.config/dotnet-tools.json`, Platform gitlink, inventory-listed tests,
  root npm files and `.githooks/commit-msg` — update released prerequisites,
  extract product assertions and retire forbidden tooling.
  Remove active waivers; externally clear fixture demotions while preserving its
  historical source. Justified waivers belong only in released Builds `Props/`.
- [ ] Module `.github/actions/{after-unit-tests,testsupport-windows}/action.yml`,
  `tests/compatibility/MinimalModule/`, package scripts and root `.slnx` — wire
  fixture adapter/seven tests, five-package payload/symbol/consumer checks and
  built Windows tests. Qualify package locks and protected product-preparation pushes.
- [ ] `builds-version`, `setup/Hexalith.Conversations.yml`, `rendered/` and
  Conversations gitlink — commit released prerequisites and registration/render
  together. Enable browsers, Dapr, Admin.Web.Tests in stage 4, the fixture hook,
  Windows job, C# analysis and the direct Platform identity dependency.
- [ ] `evidence/16/` — authenticate adoption/preservation; immediately enable
  immutable releases and retire verified legacy access. Observe green CI,
  normal checker and scheduled night.

**Acceptance Criteria:**

- Given prerequisites and live actions, when delivery adopts Conversations, then
  its owned tree matches the perimeter and retained product checks execute.
- Given missing, stale or candidate-only authority, when a production entry point
  prepares a build, then it fails before evaluation; accepted central catalog bumps
  remain compatible with separately verified Platform provenance.
- Given validated CI outputs, when Windows runs, then shared prepare builds
  safely without environment setup and descendant-cleanup tests pass;
  Linux-specific tests also remain covered.
- Given the selected catalog, when the adapter builds, then isolated locks and
  all seven assertions pass; frozen fixture projects stay outside root .slnx.
- Given green adopted CI, when its next scheduled nightly completes, then CodeQL
  and publication or a valid nothing-to-release outcome establish CAP-16.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Verification

- Companion-defined .NET/CLI and Python 3.12/runner regressions; actual package
  builds, classified tests, five-package consumers, browser/Dapr/AppHost, seven-test
  fixture and native Windows execution without added skips or root rebuilds.
- `run-with-temp uv run --locked --script tools/render.py --check` — no diff.
- `run-with-temp uv run --locked --script tools/validate.py` — committed candidate
  passes global and live-module checks before the delivery-triggering push.
- Normal `python3 references/Hexalith.Builds/check.py` from an adopted, correctly
  initialized module workspace; authenticated delivery/CI/nightly observations.
