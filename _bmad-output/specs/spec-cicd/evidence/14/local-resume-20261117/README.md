# Story 14 local resume, 2026-11-17

Story 14 remains **in progress**. This resume ran sequential local
qualification only: no GitHub reads, pushes, provisioning, release,
registration or delivery. Concurrent product and shared-catalog changes
were preserved.

## Product restoration

Later Agents product work (`528c937`) had inverted the published audit
conformance assertion. The restored
`OrdinaryReleaseShouldEvaluateTheHighAndCriticalAuditPolicy` again requires
effective central NU1901/NU1902 warnings-not-as-errors and keeps
NU1903/NU1904/NU1900/NU1905 failing. Module-local `Directory.Build.props`
still omits `WarningsNotAsErrors`.

The current Builds catalog selects EventStore 5.2.0 and Fluent UI 5.1.0.
`eng/consumer-executable-assets.json` was reviewed and updated to those
package versions and the observed Fluent UI static-web hashes. EventStore
`.targets` SHA-256 values are unchanged. No owned workflow, dependabot,
instruction, deny or Builds gitlink bytes were edited.

## Passing local checks

[`qualification.json`](qualification.json) binds the disposable snapshots.
In `run-with-temp` clones of current Builds `e8b86ba3ae6e27c2d6cba536d6002ac8f3c5a921`
and Agents `e98dab8c243286ceb8d0db8998caf3aad7f7b089` plus the two product
files above:

- Builds schema (23), executor (51) and local-check (40) tests pass on
  Python 3.12 and 3.14. These include renderer defaults, nonpositive/unknown
  minima, unsupported runner rejection, count/skip once-per-project and
  complete-project/failure-order coverage.
- 78 focused Agents package, consumer, archive, scratch-cleanup and
  exact-exclusion regressions pass.
- SDK 11 package-mode Release restore/build of `Hexalith.Agents.slnx`
  succeeds. The two restored audit-policy facts pass with fail-skips on.
- The real hook packs six packages with `--no-build --no-restore`, validates
  archives/UI assets, compiles seven isolated consumers, prints
  `Validated six built packages and seven isolated package consumers.` and
  removes its reserved scratch.
- Current `builds-version` pin `v6.2.0`
  (`0ccd12af6576a3aac601340dec7dba53e86768c3`) contains
  `tests.minimumExpectedTests`, `tests.failSkips` and central NU1901/NU1902
  treatment. That pin is not an adoption decision.

A full ordered five-suite rerun against this exact candidate was not
repeated here. The earlier [6325-test publication proof](../publication/README.md)
and [6288-test local proof](../local-implementation/README.md) remain
historical; refresh them before the next preparation push.

## Remaining blockers

Registration, App delivery and nightly acceptance stay pending:

- Story 11 is still waiting for its genuine scheduled-night checkpoint.
- AD-21 authenticated provisioning was not refreshed (no remote operations).
- Cross-module duplication qualification still requires complete fresh
  live-main coverage. The [prospective scan](scan/summary.md) now finds six
  Agents sources and a complete local Commons snapshot, then fails on seven
  Conversations discovery expressions. Zero reported copies does not
  establish clean coverage. Those errors belong to Conversations' owning
  migration; no Agents scanner exception is approved.
- No `setup/Hexalith.Agents.yml` was registered. The candidate remains
  [`../local-implementation/Hexalith.Agents.yml`](../local-implementation/Hexalith.Agents.yml).
