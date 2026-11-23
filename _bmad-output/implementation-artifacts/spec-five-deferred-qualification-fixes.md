---
title: 'Close five deferred CiCd qualification findings'
type: 'bugfix'
created: '2026-11-23'
status: 'done'
baseline_commit: 'c60b2450ee995db520b71077a8596b20911afc62'
route: 'dispatch'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="requested batch">

## Intent

Close five open findings in the CiCd deferred-work ledger that affect confidence in release qualification. A maintainer should get reproducible maintenance checks, the complete EventStore verification suite in full validation, reliable Parties decisions under supported Python invocation modes, and an identifiable endpoint when a nightly API read cannot retry.

## Boundaries & Constraints

Use the existing CiCd entry points, the frozen qualification inputs and the scoped full-suite runner. Preserve the current nightly retry, redaction and timing rules. Exercise publication tooling with disposable sources and controlled external calls. Publish the verified CiCd change on main.

## I/O & Edge-Case Matrix

| Scenario | Input | Expected result |
|---|---|---|
| Maintenance fixture | Developer Git configuration rewrites GitHub URLs or converts CRLF | The same fixture passes, with caller trust settings available for the real source repositories. |
| Maintenance render refusal | Incomplete revision, mismatched source or branch, stale workflow, occupied output or receipt, or an out-of-scope path | The renderer identifies the matching refusal and preserves the input tree, index and outputs. |
| Nightly API read | Retry delay is invalid or the remaining budget is insufficient | The error identifies the method and validated path, omits the query and retains bounded HTTP evidence when available. |
| Full validation | The required historical Builds objects are present | The full gate runs the 17 EventStore tests once. Missing prerequisites or test failures fail the gate. |
| Parties qualification | The same controlled preparation is evaluated in normal and optimized Python | A source mismatch produces a failed receipt, while valid input passes the same checks in both modes. |

</frozen-after-approval>

## Code Map

- `tools/tests/test_maintenance.py` creates its own owner and target repositories from committed CiCd inputs and Builds objects. The existing snapshot helper checks that refused operations preserve worktree, index and output.
- `tools/nightly_runtime.py` validates each method and path before sending. The validated path excludes query parameters. `tools/tests/test_nightly_runtime.py` supplies controlled API responses and a clock.
- `tools/check_global.py` runs tool suites for full validation. The existing gate Python environment includes the locked JSON Schema validator. Full delivery and nightly bump acquire the v6.0.6 objects already required by renderer tests.
- `tools/qualification/pre-adoption/eventstore/test_pre_adoption_verify.py` tests the relocated verifier using immutable Builds inputs and local Git history. `tools/tests/test_validate.py` exercises the global discovery contract.
- `tools/qualification/pre-adoption/parties/qualify-push.py` checks source, pins, hashes, modes, trees and commit messages. `tools/qualification/exercise_relocation.py` and `tools/tests/test_qualification_relocation.py` already exercise both valid and invalid controlled inputs.

## Tasks & Acceptance

- [x] Isolate the maintenance fixture configuration and test each previously uncovered refusal in the ledger for story 28-1.
- [x] Add endpoint context to nightly retry failures and verify diagnostics, redaction and request counts.
- [x] Include the relocated EventStore suite in full validation and test discovery and failure propagation.
- [x] Make the Parties qualifier's existing acceptance predicates unconditional and exercise both interpreter modes.
- [x] Record verified resolutions against all five original backlog entries.

Given the test inputs in the matrix, when the normal entry points run, then their decisions, side effects and diagnostics match the corresponding expected results.

## Implementation Notes

The initial five targeted suites passed 162 tests. After review, the five suites passed 164 tests (28 maintenance, 40 nightly, 17 EventStore, two relocation and 77 validation). The maintenance suite also passed with a GitHub URL rewrite and automatic CRLF conversion. A separate missing-object run failed through the full-suite runner as expected.

## Review Triage Log

| Review | Verdict | Evidence and disposition |
|---|---|---|
| Blind 1 | Medium | Git repository-selection variables reach the EventStore history fixture. Isolate its Git calls before running it as a required gate. |
| Blind 2 | Medium | Required commit signing reproduced a failure during fixture setup. Isolate the disposable Git configuration. |
| Blind 3 | Medium | The release archive accepts replacement objects. Read the pinned commit with replacements disabled. |
| Blind 4 | Medium | The optimized harness loses its assertion that an exception was observed. Check the observed refusal independently of optimization. |
| Blind 5 | Medium | The controlled owning commitlint process always succeeded. Exercise a failing result in both interpreter modes. |
| Blind 6 | Low | A cached diff omits the assume-unchanged flag. Include index flags in refusal snapshots. |
| Blind 7 | Low | The new scope test exercised the directory restriction only. Add a workflow with the wrong extension. |
| Edge 1 | Medium | The EventStore fixture inherited repository and index variables. Covered by the Git isolation correction. |
| Edge 2 | Medium | The EventStore fixture inherited signing settings. Covered by the same correction. |
| Edge 3 | Low | Exhausting three transport attempts follows a distinct pre-existing terminal transport branch. The selected backlog finding concerns retry-budget and invalid-delay errors. |
| Edge 4 | Low | An overslept deadline can reach the existing request-admission timeout message. The selected change identifies explicit insufficient-retry-budget errors. |
| Verification 1 | Medium | The successful control and one digest mismatch did not exercise individual dependency-pin, staged-tree and commitlint rejections. Add both-mode cases. |
| Verification 2 | Medium | The adverse Git configuration was initially a manual run. Add a recurring regression in the maintenance suite. |
| Verification 3 | Medium | The missing-object failure was initially verified manually and mocked in the suite. Exercise actual missing-object failure in the gate test. |
| Verification 4 | Medium | The reviewer reproduced an EventStore fixture commit failure with a configured signer. Covered by the Git isolation correction. |

## Verification

Use the repository's temporary workspace wrapper for fixture and gate runs. Run maintenance, nightly runtime, EventStore, qualification relocation and validation tests. Run the full tool suite and check the staged diff for unrelated reference updates before publishing.

The full global run passed 31 of 32 tool suites (789 tests in the passing suites), including all five targeted suites. ScanTests initialization failed at the locked npm installation. A standalone install with the workspace network configuration succeeded, then npm signature verification reported a download failure. GitHub API access also blocked immutable bootstrap verification, Builds publication verification and the online workflow audit on both the pulled baseline and the candidate. Global log SHA-256: `070dcd36d9fc8176228470e1e4ea7f35aef542e57534dabc06623788f2db3f93`.

The App inventory accepted all 11 selector source digests at commit `da9f0e74997c6ec489de78031ba1650c71a61f0f`.
