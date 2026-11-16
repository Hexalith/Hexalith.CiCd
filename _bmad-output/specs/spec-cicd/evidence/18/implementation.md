# Story 18 local implementation and qualification

This records local implementation, not Projects adoption or CAP-16 acceptance.
No repository remote operation, push, administration, delivery or publication
was performed by this implementation run. Necessary locked package acquisition
and the existing read-only online security audit were authorized separately.
Jobs ran sequentially in `run-with-temp` workspaces; their child work was awaited.

## Current qualification boundary — 2026-11-17

Story 18 remains **in progress and unadopted**. The combined reconciled source
has not passed qualification. Earlier successful checks below apply only to
their recorded snapshots.

`qualify-reconciled-snapshot.py` captured immutable Git trees for all six local
modules using private indexes, then checked out standalone copies without
initializing nested submodules. `matrix-reconciled-qualification.json` records
those exact trees, source commits, flags, durations and exits. Restore passed;
the unchanged Release/package build failed with fourteen CS0234 errors because
the current Projects query declarations require `QueryResultContractAttribute`,
absent from the selected published EventStore Contracts 5.1.1. Public API
inspection also found no such type or API difference in Contracts 5.2.0
(`matrix-published-sdk-{api-diff,query-result}.log`). A fresh read of the public
NuGet index confirmed 5.2.0 is the latest stable Contracts release
(`matrix-published-sdk-versions.json`). No declaration was removed,
replacement type invented, source dependency substituted or manual release
dispatched. Dependent tests, hooks and runtime phases did not start. The child
exited 1, its private workspace was removed and no AppHost was allocated.

The fixture reconciliation preserves concurrent product changes and the earlier
qualified fixes for source-complete quiescence, setup-only exact read readiness,
atomic owned Docker ports, private Keycloak origin handoff, URL normalization,
bounded graceful shutdown and cleanup ordering. Its exact merge evidence is in
`matrix-qualified-reconciliation.{json,patch}`. These combined files remain
unqualified until the real package prerequisite is available.
Later concurrent Projects, Builds and Platform commits were preserved and were
not imported into that completed job. All eighteen reconciled fixture files
still match their recorded applied hashes. `matrix-final-live-drift.json`
records this later boundary; the next combined run must capture fresh inputs.

Scanner forwarding now supports bounded direct wrappers and literal tuple
loops. A parent audit rejected the initial opaque Git regex shortcut: identical
guard/return ASTs do not prove immutable native values. That shortcut was removed;
computed Git operands fail closed. Earlier zero-error candidate discovery and
focused interpreter results are historical observations of the rejected shortcut,
not acceptance evidence. The unchanged G6 preparation action needs supported,
qualified value provenance before its computed Git operands can be certified.
No action exclusion, path exception or delivered-action edit was introduced.

Full scanner suites passed **121 tests** on the default interpreter in 327.542
seconds and Python 3.12 in 320.034 seconds, including all six real-language
detector calibrations (`matrix-scanner-conservative-full.log` and
`matrix-scanner-final-312-full.log`). After those runs, the parent tightened
binding checks, immutable loop rows and Node global-object aliases. All eight
affected groups then passed on the final source on both interpreters: 77.741
and 73.704 seconds (`matrix-scanner-final-controls{,-312}.log`). Bound-method
escape regressions first reproduced two failures, then passed after the fix.
The final source identities and verification boundaries are recorded in
`matrix-final-verification.json`. Actual final-source
candidate discovery selected **56 files** and refused exactly
`.github/actions/prepare-g6-catalog/prepare.py:47` for computed forwarding
(`matrix-candidate-conservative-final.json`). Both G6 files remain selected.
This diagnostic is a migration prerequisite, not a passing closure verdict.

## Changes

- Builds has the complete strict `npmWorkspaces`/`dotnetTools` contract,
  stage-output forwarding and one-time trusted npm/tool/browser preparation.
  Missing, uncommitted, unsafe or floating inputs and failed installers refuse.
  Configuration propagation keeps out-of-solution project references in Release.
- Projects has separate nonpackable prebuilt AppHost/driver projects. They use
  public Aspire lifecycle and metadata APIs, private credentials/stores, normal
  authenticated commands/reads and read-only durable-state observation. Missing
  Release outputs cannot cause a build fallback. The original source AppHost,
  source diagnostic qualifier and its source-only refusal/defines are preserved.
  A test-only worker entry point composes the public production worker
  registrations/handlers with the published SDK catalog/channel boundary; it
  does not invoke the original source-only worker bootstrap.
- Generator output is retained by the shared build; the exact restored inspector
  reads it without rebuilding. Packing uses existing Release outputs. The five
  isolated real API consumers remain separate checks. Hook entry points are
  statically imported Python; the adapted PowerShell local tools remain available.
- Workflow-text assertions and root CI-only npm files were retired. All eight
  ordinary C# suites, positive/negative OpenAPI assertions and genuine owning
  EventStore PostgreSQL stop/restart/support methods remain.
- CiCd discovers six source languages, literal npm workspaces/recipes, complete
  Playwright test/config/reporters and local/tsconfig imports using a trusted
  TypeScript syntax parser. It never evaluates module configuration. Dynamic
  execution, resolution indirection and unsafe paths fail closed. Thresholds and
  cross-module semantics are unchanged. The actual Projects candidate is checked,
  not just synthetic fixtures.
- Live validation additionally requires committed regular npm/tool preparation
  inputs after a tagged reader accepts those settings. The active registry,
  rendered module, Builds pin and Projects gitlink were not fabricated or adopted.

## Earlier snapshot checks

- Builds Python 3.12: the full run passed 15/16 groups, including all 591 shared
  library tests; the remaining unchanged real online zizmor test passed in a
  focused rerun with the existing CiCd-agent credential privately supplied to
  the child. See `builds-python312-final.log` and `builds-online-policy.log`.
- Runner Python 3.14: all 116 current-candidate CI contract/environment/pipeline tests passed (`builds-runner-focused.log`).
- Scanner: all 103 tests and six real-language calibrations passed before the
  final fixed-compiler-operand extension (`scanner-full-final.log`). The actual
  candidate closure passed with 54 files and zero errors
  (`candidate-scope-final.json`). The focused compiler-boundary control passed all acceptance/refusal cases (`scanner-compiler-control.log`).
- Renderer reproducibility passed (`render-check.log`). Existing local validator
  qualification passed all 51 tests (`validator-local-final.log`). The added preparation-input control passed all nine regular/missing/symlink subcases (`validator-preparation-focused.log`).
- Ordinary Projects C# tests: 2,846 passed, one existing live-environment skip
  across all eight suites (`local-package-qualification-attempt8.log`). This
  includes the retained Client OpenAPI cases and new fixture safety controls.
  The one live SDK host/store-client restart case subsequently passed against
  the private fixture with zero skips (attempts 11/12).
- Current-candidate Release build: zero warnings/errors; inspector, all five
  package candidates, all five actual consumers, locked npm/signatures/browser
  preparation and all 20 package-tool controls passed (attempt 10).
- Owning G-6 product assertions: all exact 21 support methods yielded 33 passing
  cases; the real PostgreSQL two-process/failover/replay/expiry/authority test
  passed once in 29.8 seconds, with no skips. See `owning-*-ctrf.json` and attempt
  10. All three exact private control-plane container identities were removed
  (`owning-g6-cleanup.json`). Historical source/workflow evidence gates were not
  substituted for these product assertions.

## Earlier revision boundary

The initial Builds version was `fdda17c0a4538b0f7c99f813c20ca24b49006530`
(`v6.0.6`). A concurrent independent change advanced it to
`1e4f68d3f7e5925d33acffdadbf224e186711b5b`, which already includes the earlier
npm/tool preparation changes. EventStore also advanced independently to
`54f83e3b6a6eca3c8cf0caeb734cbcad30e18e41`; its narrow CA1822 correction is
present there. Nothing was reset, amended or overwritten. Projects remained
`981ceef13a1abc88219925e73c51a23eb9ac50c2`. Current full revisions and working
candidate hashes are in `current-candidate-identities.json`; qualification logs
name their exact cloned source revisions. The newer immutable combined boundary
is in `matrix-reconciled-qualification.json`. A working-candidate hash is not a
delivered/adoption identity.

## Remaining acceptance

All four native product scenarios, complete compatibility smoke/full/repeat/retry
and the actual-owner browser/state lane must pass on the combined source.
Earlier native iteration 4 passed the authorized-read, trust-separation and
safe-denial rows before the process-restart failure. Iteration 6 remained red:
zero of four native scenarios passed, the compatibility SDK restart passed once,
smoke passed seven of eight cases and no skips occurred. Later fixes and 78
focused controls passed on a private pre-reconciliation snapshot; none of those
results establishes acceptance of the present combined source. The current
compilation prerequisite stops the dependent lane before startup.

The accepted story-11 scheduled pilot checkpoint, acceptable released Builds
version, complete ordered AD-21 provisioning/readback, product preparation push,
App-only delivery identity/tree-preservation proof, immediate immutability and
legacy-scope cleanup, normal post-adoption checker, adopted green CI and genuine
next scheduled-night outcomes remain outstanding. The execution restriction
prohibits the repository/hosted-state operations needed to establish them.
`setup-candidate.yml` is only a review artifact outside the active registry.
