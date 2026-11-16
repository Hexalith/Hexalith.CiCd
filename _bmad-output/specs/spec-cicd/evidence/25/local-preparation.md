# Timesheets local preparation — 2026-11-16

Local implementation and checks are complete to the unsigned-consumer boundary;
adoption and preparation-push qualification remain open. This agent performed no
commit, push, fetch, maintainer setup, App delivery, credential cleanup or release
operation. Shared repositories advanced through external commits during the run;
those changes were preserved. Initial Timesheets `origin/main` was
`bbb91319ee209333d29f07e53bd9b5e4adc40267` and was not refreshed by this agent.

## Final local result

`verification-summary.json` records tested inputs and observed external heads.
Complete local .NET results: Architecture 95, Contracts 108, Projections 792,
Server 746, Works 76 and Integration 1,057 passed with its five existing skips.
Package-validator and selected-index tests passed 30 each. Compiled AppHost
configuration, model, construction/disposal and security checks passed without
Start/Run. The final fixture/privacy suite passed all 270 tests; the final shared
runner passed 27 behavioral cases. Six expanded catalog metadata cases passed,
including package/source selection, unrelated and Works-owner defaults, explicit
overrides, Tenants, Memories, Mcp and OpenAPI.

The streamed-bootstrap fix retains sequential selected reads and revalidates its
reserved epoch/operation/generation/offboarding state before emitting mutations.
All five concurrency regressions pass. Unchanged deadline assertions measure
3.484s/552 metadata reads after the fix versus 6.107s/1,062 before it. The fixture
fix ignores only vanished `/proc` entries (`ProcessLookupError`); the old helper
fails the injected ESRCH regression, and fixed timeout/interruption cleanup kills
and reaps descendants while genuine permission/malformed-stat failures remain
refusals. The initial cleanup log did not preserve its swallowed OSError, so its
exact original cause is not asserted.

The original 80ms Server polling-count failure (two reads in a 353ms run) is kept
in evidence. An earlier unchanged-binary focused diagnostic passed. The fresh
source-complete Server run at `b325a0b47d642f1711f49e589509ca89ac585bca` includes
the concurrent deterministic-clock change documented in `polling-deadline-fix.json`;
all 746 tests pass. This agent did not author that clock change. The original
wall-clock count was scheduling-sensitive. Aborted stale tests and
relocated-output/source-path/cache harness failures are recorded separately and
do not establish product acceptance.

The complete .NET run used the recorded frozen preparation on Timesheets
`bbb91319ee209333d29f07e53bd9b5e4adc40267`; source-complete follow-up used a fresh
build of `b325a0b47d642f1711f49e589509ca89ac585bca`. Its six generated compiled
informational-version inputs are `2.1.1-preview.0.3+b325a0b47d642f1711f49e589509ca89ac585bca`.
The latest runner packed all six package/symbol pairs at `2.1.1-preview.0.3` and
passed payload/dependency checks before required signatures refused the first
unsigned consumer with `NU3004`. No isolated-consumer runtime success is claimed.
Actual runner SHA256 was
`bfd12c3daf7dfa6258c1b274ccca0c71da0fbf859964c47d6394b9449bae61d1`, matching the
current source observed at handoff.

The tested Builds base was `1e4f68d3f7e5925d33acffdadbf224e186711b5b` plus recorded
catalog/runner inputs. The corrected catalog proposal SHA256 is
`e87d7a01991f41e5fe693f3f4f945019038c6c3e73d0ef12e9740f52a8188e23`, which matched
the live catalog when the metadata matrix ran. The live catalog later advanced
to SHA256 `a5bbe3e7bfd78903ba3b7282885c087fc5cfda09e70dd53ca9ec0583066e2ccd`;
that later delta is outside this qualification. The negative Tenants-default correction
changes an unconsumed value: none of the sixteen frozen restored graphs consumes
Tenants/Memories/Mcp. See `catalog-consumed-graph.json` and
`catalog-metadata-final.json`. No live catalog content was overwritten by this
agent. External Builds/CiCd commits are not wholly qualified by these checks.

Final receipts are `catalog-final-check.json`, `catalog-scoped-followup.json`,
`shared-product-validation-tests-final.log`, `fixture-privacy-followup.log`,
`server-suite-source-complete.log` and `current-runner-real-packages.log`.
All disposable jobs and their child work completed; scratch was cleaned by
`run-with-temp`. Exact commands are in the receipts and replay scripts. Python
bytecode was disabled for the queued checks.

Still required: a qualified signed-candidate path, complete bounded action
discovery and actual cross-module scan, compatible immutable published Builds,
exact committed/fresh-main/ownership/commitlint pre-push verification, onboarding,
remote preparation, registration/render/gitlink and authenticated validation,
App delivery, normal `check.py`, credential/immutable-release cleanup, green
adopted CI and the next central nightly. No registration or adoption is claimed.

## Changes

Removed agent/BMAD/npm repair tests, release/source-authority and CI-report
evidence tests, root tool-only npm manifests, the npm repair script and the
CI-result validator. Removed story/document/agent/skip-governance architecture
tests. Extracted the AppHost SDK/catalog invariant and catalog-reader test into
`AppHostDependencyTests.cs` and the no-UI-project boundary into
`ScaffoldGovernanceTests.cs`. Other source/dependency/privacy tests remain.

The three retained package test classes (`InventoryTests`,
`ConsumerRestoreTests`, `RestoreBackedValidatorTests`) are byte-identical in
`scripts/tests/test_product_packages.py`. All six test projects, live-Dapr and
performance opt-ins, package validators, AppHost and fixture/privacy scripts
remain. Legacy release scripts remain until qualified adoption replaces callers.

Prepared `tools/product-validation.json` and six product-only C# consumer sources
copied from existing contract snippets. No hook or registry entry is enabled
against unpublished support. `local-input-check.json` confirms twelve existing
owned files/portions/modes/gitlinks unchanged against local `origin/main` and
records exact consumer input hashes. Whole instruction/settings files were
unchanged, preserving foreign and owned portions. This is not remote freshness
or exact committed pre-push qualification.

New Builds files implement the shared prerequisite:
`Github/lib/product_validation.py`, `Github/product-validation/action.yml`,
its README and `Github/lib/tests/test_product_validation.py`. The generic runner
packs existing Release outputs with `--no-build --no-restore` and their evaluated
version; checks package/symbol inventory; delegates product payload/dependency
assertions; independently restores/builds/executes each consumer; verifies exact
archive bytes/source/version including transitives; asserts compiled assembly
informational version; freezes feed and original assembly/symbol bytes; stops at
the first failure; cleans scratch. Consumer audits and shared required signatures
and trusted signers remain enabled.

## Initial verification and identities (historical)

All disposable jobs used `run-with-temp`; their useful logs are saved here.

| Check | Result | Evidence |
| --- | --- | --- |
| Retained package validator tests | 30 passed | `package-validator-tests.log` |
| Selected-index tests | 30 passed | `selected-index-tests.log` |
| Standalone Release architecture build/suite | 95 passed; no skips | `architecture-build.log`, `architecture-tests.log` |
| Shared runner behavioral subprocess tests | 25 passed | `shared-product-validation-tests.log` |
| Real SDK 11/net10 synthetic package | Built once and packed existing outputs at 2.3.4; expected NU3004 unsigned-candidate refusal | `runner-real-sdk-probe.{json,log,py}` |
| Module/new runner whitespace | `git diff --check` passed | Commands recorded in implementation session |
| Module contract/ownership | Six exact IDs; retained test classes unchanged; twelve owned paths unchanged | `local-input-check.json` |

`local-preparation-check.py` tested a standalone local clone, the cleanup patch
and committed direct dependencies without initializing nested submodules in CiCd.
`local-preparation-check.json` records full canonical module/Builds/EventStore/Works
revisions, commands and patch/source hashes. The module's actual Builds input was
`39973bfccb26ae98a3d25856a8f85950fecdf02a`, not the dirty live Builds checkout.
The broad job exited 1 because the full Release/package build failed restore.

Builds HEAD advanced concurrently during local runner development; the source
was not a frozen commit qualification. Observed HEAD before runner implementation
was `b1edf82c9b74963918a5f27545961a2619e17f0a`. After runner checks, HEAD was
`1e4f68d3f7e5925d33acffdadbf224e186711b5b` and local `origin/main` was
`acf8cfd709e920b7cd46b47a46d2443e83f6f9fc`. The checks exercised the uncommitted
runner files; these concurrent changes were preserved. CiCd HEAD was
`eba7514e02904c741f6a0a80930d85eb358d385c`.

## Initial blockers (historical)

The final result above supersedes the local build/test blockers below. Signed
consumers, published support and rollout acceptance remain open as listed above.

`release-package-build.log` records five `NU1202` errors against net10:

| net11-only package | Version | Affected projects |
| --- | --- | --- |
| Hexalith.PolymorphicSerializations | 2.0.0 | Works, Works.Tests |
| Hexalith.Commons.UniqueIds | 3.0.0 | Works, Works.Tests |
| Microsoft.AspNetCore.Mvc.Testing | 11.0.0 | IntegrationTests |

Qualify a finite Timesheets net10 catalog view for these packages and the entire
dependency closure, retaining SDK `11.0.100`, net10 consumers and other consumers'
catalogs. The prior investigation also requires compatible EventStore assets
(`4.2.0` was investigated as net10; `5.1.1` Client/Contracts are net11-only), with
matching OpenAPI/hosting dependencies. These are inputs to verification, not
validated version selections. No module dependency override was added.

The real SDK probe demonstrated `NU3004`: the existing strict NuGet policy
refuses unsigned candidate packages. Qualify a supported signed-candidate path
before enabling the runner; no signature waiver or broad source exemption was
added. Fake-SDK tests establish process behavior, not real package acceptance.

Still open: full solution build and all six suites; retained compiled AppHost and
fixture/privacy execution; six real consumers; compatible published Builds;
bounded discovery for the complete actual hook with negative dynamic-execution
proofs; a real cross-module duplicate scan; and the exact committed preparation
procedure/commitlint/module-agent push. Then complete maintainer preconditions,
registration/render/gitlink against a remotely available revision, committed
candidate render/authenticated validation, App delivery, normal `check.py`,
immutable-release/legacy-credential cleanup, green hosted CI and next nightly.
No scanner change/exclusion, registration or live runtime acceptance is claimed.
