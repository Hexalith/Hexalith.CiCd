---
title: 'Shared execution support for ordered module adoption'
type: feature
created: 2026-11-16
status: done
route: dispatch
baseline_commit: 0f25d19ba712eee9aae59d118251b854bbffd120
context: []
---

<frozen-after-approval reason="User supplied the adoption inventory and explicitly requested implementation">

## Intent

Implement the shared Builds runtime and CiCd configuration/rendering capabilities
needed to adopt EventStore, FrontComposer and Tenants in that order. Adoption
and its qualification are separate from product releases. The current shared
caller cannot express retained Linux browser/authentication matrices, long
mutation workers, private/manual qualification or existing coverage gates.

## Boundaries & Constraints

Preserve complete-project test execution, count/skip policy, release audits,
package-only Release builds, and the local checker's stages 1–3 alignment.
Exclusions delegate to enabled actions; they never silently skip product tests.
Shared installation, results, coverage and consumer mechanics belong in Builds;
product fixtures, hosts, API/archive assertions and runtime eligibility decisions
remain in module actions. Preserve existing workspace changes. Do not commit,
push, change module registrations/pins, release products, publish packages/images,
or enable publication. A needed Builds release is a separate infrastructure
operation. Existing released contract bytes remain authoritative for delivery.

## I/O & Edge-Case Matrix

| Scenario | Input | Required behavior |
| --- | --- | --- |
| Existing registrations | Existing released Builds pin | Identical generated caller/configuration |
| Isolated jobs | Linux matrix, duration, dependencies and resource profile | Independent workers, bounded lifetime and unique result identity |
| Restricted qualification | Manual protected runner/environment and explicit secrets | Main-only dispatch; secrets reach only the product action |
| Test reporting | MTP/VSTest and multi-target projects | Native switches, distinct paths, truthful reports, full project execution |
| Missing report | Required TRX/coverage absent, empty or invalid | Fail with a diagnostic; preserve the product failure |
| Coverage | Declared source scopes and comparisons | Preserve Tenants' strict line >80 and branch >=100; reporting alone adds no threshold |
| Additional tests | Explicit product test outside the solution | Restore/build/discover with the same Release properties; reject unknown/non-test entries |
| Preparation | Enabled exact tool inputs, browser/TLS/Dapr prerequisites | Shared installation, integrity/path validation and fresh-job evidence |

</frozen-after-approval>

## Code Map

- Builds `schemas/hexalith.ci.v1.json`, `Github/lib/ci_config.py`: additive schema and strict unchanged-value reader.
- Builds `Github/lib/ci_pipeline.py`, `local_check.py`: shared stage implementations; preserve stop-on-project-failure and complete xUnit projects.
- Builds `Github/lib/ci_environment.py`, `Github/prepare/prepare_linux.py`: shared environment and independent job preparation.
- Builds `Github/product-validation`, `Github/lib/product_validation.py`: existing candidate pack/metadata/signature/audited isolated consumers; reuse through enabled actions.
- Builds `.github/workflows/{ci,release}.yml`, `Github/prepare/action.yml`: workflow interface and resource preparation.
- CiCd `tools/render.py`, `check_global.py`, `validate.py`, `templates/.github/`: selected-tag rendering, interface/live-input validation and owned perimeter.
- CiCd `setup/README.md`, `docs/`: document supported configuration, ordered cutover and separate qualification.

## Tasks & Acceptance

- [x] Extend schema, strict reader, renderer and caller for isolated Linux jobs/matrices, duration, resource profiles, scheduling and restricted manual execution.
- [x] Implement native result/coverage collection and validation, preserving exact scopes/comparisons and local stage alignment.
- [x] Admit and build explicit additional product test projects outside the solution.
- [x] Extend shared browser/tool/APT/TLS preparation and per-job configuration without copying installation into module actions.
- [x] Reuse and qualify the existing shared package consumer validator; document the module action contract.
- [x] Run focused contracts, repository Python suites, workflow/security/API checks and render/global checks where prerequisites permit; retain exact evidence and blockers.

Given an existing released pin, when rendering after these changes, its output
remains unchanged. Given a candidate contract supporting the extensions, when a
retained job is configured, schema/reader/render/runtime agree on its execution
and secret boundaries. Given the same committed source and tools, local stages
1–3 use the same build/unit functions and report rules as CI. Given missing
required reports or failed product commands, qualification fails without weakening
audits, test completeness or coverage. Given adoption preparation, no product
release or package/image publication occurs.

## Implementation Notes

The invocation explicitly authorizes implementation of the supplied inventory.
Unrelated CiCd changes are present and remain outside this work. File ownership
is divided among implementation agents to prevent overlapping edits. Current
Builds already supplies `ciTimeoutMinutes`, npm/tool preparation and authenticated
candidate consumer validation; extend these capabilities rather than duplicate
them. Historical Dapr tuples, actual runtime eligibility and hosted success must
be recorded as limitations unless fresh evidence establishes them.

## Verification

Use `run-with-temp` for disposable workspaces. Run the owning Python test groups,
CiCd locked renderer and validation tests, exact-tag production render checks,
and pinned workflow/security/public API checks. Full live-main/global validation
requires acceptable released metadata and committed clean delivery inputs; local
candidate fixture evidence is identified separately.

## Review Triage Log

All three review layers completed against the saved candidate diff. Findings are
kept separately even when they share a correction.

| Finding | Verdict | Evidence and disposition |
| --- | --- | --- |
| Blind 1: unit-only local coverage | high | Unit aggregation used `enforce=False`; fix unit-only enforcement and caller regression. |
| Blind 2: complementary branch union | false | The retained Tenants validator explicitly uses maximum covered counts per source line. Preserve that exact conservative policy and document the limitation. |
| Blind 3: later product failure masked | medium | An earlier TFM report error occupied the first-failure slot; prioritize product command failures while completing frameworks. |
| Blind 4: TRX changed after collection | high | Only coverage paths were rehashed; validate every required report at stage transitions, including TRX-only policies. |
| Blind 5: additional Playwright project | medium | Tool discovery enumerated solution projects only; include admitted additional projects through shared setup. |
| Blind 6: APT mirror list | medium | Actual runner sources use `apt-mirrors.txt`; include it in shared HTTPS normalization. |
| Blind 7: platform additional projects | medium | PowerShell preparation built only the solution; preserve stage-2 admitted projects on independent Windows/macOS workers. |
| Blind 8: nonexistent source scope | high | Filename matching could satisfy nonexistent checkout paths; validate source directories/files and contained paths. |
| Verification 1: no failing hosted threshold caller test | medium | A mutation of final enforcement passed existing full-coverage fixtures; add below-threshold integration entry-point cases. |
| Verification 2: composite job-name forwarding | medium | Helper-only tests bypassed input forwarding; exercise the actual prepare composite with observable per-job overrides. |
| Verification other 1: nested fake SDK fixture | medium | Additional-project filtering changed the replacement target; update the existing nested-solution control. |
| Verification other 2: local enforcement claim | high | Same demonstrated unit-only enforcement defect as Blind 1; retain its correction and caller evidence. |
| Edge 1: local enforcement | high | Same unit-only defect; fixed with Blind 1. |
| Edge 2: product exit precedence | medium | Same cross-framework error ordering as Blind 3; preserve original product exit. |
| Edge 3: missing or modified TRX | high | Same report-boundary defect as Blind 4; validate all report digests. |
| Edge 4: project-relative PDB source path | high | Missing `src/` prefix excluded uncovered retained package lines; normalize using declared scopes before unioning, matching the retained gate. |

Concurrent workspace Git operations advanced Builds to newer infrastructure
commits and resolved an external stash-pop. Preserve the incoming managed module
preparation, protected Windows checkout and source-authorized private request
contracts while integrating this change. Re-run affected checks on the combined
result; evidence from the earlier source snapshot is labelled separately.

The final historical Dapr initialization and TLS trust-export delta received an
additional independent edge/security check with no new actionable findings.
Both supported Python versions pass the final 74 environment/tool cases. See
[the validation report](../../docs/shared-adoption-validation.md) for source-bound
full-suite results, native MTP/VSTest checks, API/workflow/render evidence and the
failed .NET/global checks. Implementation and review are complete; infrastructure
delivery and hosted adoption qualification remain blocked as recorded there.
No owning-workspace commit/push occurred during implementation. Subsequent source
publication is separate from infrastructure delivery; no product publication was
performed by this work.
