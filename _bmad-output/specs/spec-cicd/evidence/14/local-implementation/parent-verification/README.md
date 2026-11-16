# Historical parent task and diff verification

This report records the checkpoint before the human approved the six exact
historical exclusions. The decision is now applied and the full ordered proof
passes. See [current results](../README.md) and
[the approval and qualification record](../approved-exclusions.json) for the
current source trees and acceptance state. The original findings below remain
as historical evidence.

Story 14 remains **in progress**. The six historical exclusions were proposed
to the human and have not been applied. No production or remote acceptance is
claimed. The implementation workflow cannot advance past task verification
while the full ordered product suite and adoption requirements remain unmet.

## Current local source trees

- Agents staged tree: `0b85174b9a880ea7b188003559167d1b56da4d74`.
- Builds candidate tree: `e4540657efe3d1eedc989398ae826c310f47eeda`.

`formatting-proof.json` compares Agents with the native-qualified tree
`4fc98c6b576bf4382228ed3542d09cf3a845af89`. Only two C# files' original LF
formatting, trailing blank lines in two extracted Python modules, and removal
of the now-unnecessary added attributes differ. The normalized source is
identical. No executable behavior or test expectation changed.

Compared with Builds tree `6bba67897eb0903c83f029602f0abd5e6dc4cf05`, only
the environment, release adapter, and release-build test fixtures changed.
Their complete test configurations now include the required empty floor map
and false fail-skips default. Assertions and production code are unchanged.

## Broader shared verification

The initial Python 3.12 library run executed 556 tests. It passed 508 and
reported 48 failures/errors in five groups: three stale fixture builders and
the absent CI-installed root Node dependencies. The original failed log is
retained as `builds-all-lib-python312.log`.

`verify_broader.py` copied the complete candidate beneath `run-with-temp`'s
private directory, applied its exact patch, installed locked dependencies
with `npm ci --ignore-scripts`, and verified npm signatures before rerunning
all five affected groups. Every rerun passed:

| Group | Tests |
| --- | ---: |
| Action parser and policy | 20 |
| Actual pinned guard tools | 10 |
| CI environment | 24 |
| Release resolution adapters | 14 |
| Native release builds, OCI graphs and audit enforcement | 15 |

`broader-results.json` records each exit status and the exact tested Builds
tree. All 48 initial failures are covered by these passing reruns; the other
508 tests were already passing. This is combined evidence, not a claim that
the initial command passed. Disposable child work finished and was cleaned.

The 179 existing configuration corpus cases retain their exact previous
meaning after removal of the two new default fields. Fifteen new cases cover
valid floors/fail-skips, invalid values, and missing required fields. The
extracted NuGet validation definitions are AST-identical to their originals;
existing consumer policy, path normalization and package identity functions
are also unchanged. Only exact empty generated build imports were added to
the consumer fixture's classification, with a passing negative regression
for a nonempty executable import.

## Task and acceptance audit

Only the shared configuration/executor task is complete. The remaining tasks
include unmet provisioning, the authority decision, cross-module duplication
qualification, a released Builds tag, production setup/render registration,
App delivery, immediate cleanup and scheduled nightly acceptance. Their
checkboxes remain open.

The matrix's count/skip boundary and stop ordering, invalid policy rejection,
and default compatibility have passing targeted and native tests. Package
failure cleanup and executable-input rejection have passing regressions;
the actual six-package/seven-consumer hook passes. Missing prerequisites and
the actual authority failure block dependent writes. Full product acceptance
remains failed until the identified six-path decision is resolved and the
ordered product proof is rerun; independent UI/hook successes do not replace it.

The full staged diff, including untracked implementation artifacts and both
repositories, was captured with canonical base identifiers for task checking.
Final diff whitespace checks cover newly staged files as well as tracked edits.
