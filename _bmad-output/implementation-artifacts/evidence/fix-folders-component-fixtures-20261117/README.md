# Folders Server fixture qualification

The final qualification passed on the local `origin/main` snapshot of Folders,
`3ff01eeab6f6dfe7cff83e4ef3e1ff403c50c245`, preserving its recorded dependency
gitlinks and applying the product patch from `e5760ca105652f4d89c4f240e0ca455723c9a473`.
Platform uses `8ccb479e391564ce982309f106504cf8329c0a43` plus the exact final
product delta. [qualification.json](qualification.json) records destination and
patch bases, dependency revisions, changed-file hashes, commands and exits.

- Audited Release/package and Debug/source builds: zero warnings and errors.
- Complete Server: 1,462 passed, including all eleven security cases and 23
  provenance controls; errors, failures, skips and not-run counts all zero.
- Source component lane: all eleven passed, with exact source SHA-256/MVID binding
  for three distinct SDK assemblies; all unsuccessful counters zero.
- Final fixture tests: 13 passed, plus three driver/JDK probes. The pre-review
  broader Python suite passed 55 tests under its private non-1000 workspace.
  Changed C# whitespace and analyzer checks passed.
- Both component lanes: real Keycloak 26.6.4, independent RSA, TLS verification,
  natural expiry, retained grant controls, and zero remaining containers/private paths.

[complete-server-results.xml](complete-server-results.xml) and
[source-component-results.xml](source-component-results.xml) retain sanitized
executed inventories. Their corresponding logs retain identity and cleanup
observations. [parent-matrix-audit.json](parent-matrix-audit.json) records the
independent matrix and working-byte audit. The canonical signed-NuGet content
hash is recomputed with the pinned SDK API; raw archive SHA-512 and DLL
SHA-256/MVID are checked separately.

`passing-local-base/` preserves the earlier passing 5.1.1-package snapshot and
its supplemental failure-path observations. `passing-mainline-pre-review/` retains the passing snapshot reviewed before
patches. `attempt-2/` preserves an earlier failure. Neither is presented as the final mainline qualification.

All verification used `run-with-temp`; owned children finished and disposable
workspaces were removed. Implementation and verification made no commits or pushes. The separate
[publication preflight](publication-preflight.json) authenticated the immutable
Builds release and refreshed module mains; complete approved preparation checks
and exact dependency/consumer publication remain outstanding. The required
submodule-first publication condition prevents a superproject commit.
AppHost cohort lifecycle, held FR58, protected enrollment and migration acceptance
remain independent and incomplete.

[Review resolutions](review-resolutions.json) and [final runner identity](final-runner.json) bind the post-review result. Two pre-existing issues—SIGTERM cancellation cleanup and unbounded pre-truncation capture—are recorded in the deferred ledger.
