# Story 18 local implementation and qualification

This records local implementation, not Projects adoption or CAP-16 acceptance.
No repository remote operation, push, administration, delivery or publication
was performed by this implementation run. Necessary locked package acquisition
and the existing read-only online security audit were authorized separately.
Jobs ran sequentially in `run-with-temp` workspaces; their child work was awaited.

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

## Completed checks

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

## Revision boundary

The initial Builds version was `fdda17c0a4538b0f7c99f813c20ca24b49006530`
(`v6.0.6`). A concurrent independent change advanced it to
`1e4f68d3f7e5925d33acffdadbf224e186711b5b`, which already includes the earlier
npm/tool preparation changes. EventStore also advanced independently to
`54f83e3b6a6eca3c8cf0caeb734cbcad30e18e41`; its narrow CA1822 correction is
present there. Nothing was reset, amended or overwritten. Projects remained
`981ceef13a1abc88219925e73c51a23eb9ac50c2`. Current full revisions and working
candidate hashes are in `current-candidate-identities.json`; qualification logs
name their exact cloned source revisions. A working-candidate hash is not a
delivered/adoption identity.

## Remaining acceptance

The full compatibility smoke/full/repeat/retry and actual-owner browser/state
lane must pass. Attempts 8 and 10 retained genuine startup failures and cleaned
their private resources. Attempt 8 exposed authority health TLS trust; attempt
10 progressed past it and exposed source-only worker bootstrap and UI readiness
selection. Distinct fixture composition corrections are under qualification.

The accepted story-11 scheduled pilot checkpoint, acceptable released Builds
version, complete ordered AD-21 provisioning/readback, product preparation push,
App-only delivery identity/tree-preservation proof, immediate immutability and
legacy-scope cleanup, normal post-adoption checker, adopted green CI and genuine
next scheduled-night outcomes remain outstanding. The execution restriction
prohibits the repository/hosted-state operations needed to establish them.
`setup-candidate.yml` is only a review artifact outside the active registry.
