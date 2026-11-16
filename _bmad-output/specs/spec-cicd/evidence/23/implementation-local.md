# Story 23 local shared prerequisites

This is local implementation evidence, not provisioning, publication, delivery
or Tenants adoption evidence. The approved spec's current stage forbids remote
repository/service operations and leaves AD-21 unsatisfied. Tenants product
preparation and registration therefore remain gated.

## Source and changes

- CiCd: `/home/administrator/projects/hexalith/cicd-story-23`, baseline
  `771cfd0f01416d9adb2bdb3ff8cf8d1437d385e1`.
- Builds: isolated owning-repository worktree
  `/home/administrator/projects/hexalith/builds-story-23`, branch
  `story/23-tenants-shared-prerequisites`, baseline cached `origin/main`
  `fdda17c0a4538b0f7c99f813c20ca24b49006530`. No fetch was performed in this
  local implementation stage. The original dirty Builds checkout was preserved.
- `shared-local-changes.json` records the source files' final SHA-256 hashes
  and modes for this uncommitted implementation.

Builds now creates a mode-0600, exclusive Dapr initialization receipt under
`RUNNER_TEMP` before its single central `dapr init`. It records current
repository/run/attempt/job identity, UTC start, preexisting container/volume
inventory and, after successful init, actual newly observed container IDs,
creation times, mounts and mounted-volume identities/times. Only complete
evidence is exported through `HEXALITH_DAPR_INITIALIZATION_RECEIPT`.
Retained/malformed/symlink receipt files, supplied receipt paths and invalid job
identity refuse initialization. Failed initialization or metadata inspection
keeps unpublished incomplete evidence. Private Docker capture never logs partial
inspection stdout/stderr on failure; diagnostics retain the operation and exit
code. The shared action README documents the format and consumer obligations.

The complete Builds CI schema and strict loader now require
`ciTimeoutMinutes`, integer 1–360, with renderer metadata default 30. Builds'
own document records its existing 60-minute allowance; sample and test fixtures
materialize 30, including the tracked sample expected-state document. CiCd forwards the validated knob to the existing numeric
`job-timeout-minutes` input only when the selected tagged contract declares it.
The current `v6.0.6` pin and its rendered output retain their existing contract.

## Verification

Every disposable verification job used `run-with-temp`. CiCd tests ran from
temporary snapshots with local shared Builds clones inside the wrapper's
`TMPDIR`; the persistent story worktree's Builds path remains uninitialized.

- `builds-ci-python312.log`, `builds-ci-python314.log`: 107 CI config,
  environment, pipeline and prepare tests passed on each interpreter before
  the private Docker capture follow-up.
- `render-python312.log`, `render-python314.log`: locked renderer suite,
  34 tests passed on each interpreter, followed by successful locked
  `tools/render.py --check`. Includes old-tag compatibility, materialized
  default/custom/boundary allowances, invalid values, callable input typing,
  reproducibility and atomic refusal behavior.
- `builds-config-final-python312.log`,
  `builds-config-final-python314.log`: 18 tests passed on each interpreter,
  including the complete schema/strict-reader positive and negative corpus.
- `builds-environment-final-python312.log`,
  `builds-environment-final-python314.log`: 31 tests passed on each interpreter,
  including actual composite execution and unpublished failed-inspect evidence
  with private markers in partial JSON stdout and stderr.
- `builds-contract-python312.log`, `builds-contract-python314.log`: affected
  consumer qualification completed 148 tests on each interpreter: all 117
  expected-state, guard adapter, release state, release build and local checker
  cases passed. These runs began before the final Docker diagnostic correction;
  their sole failure was the retained environment assertion, subsequently
  corrected and verified by the complete final environment suites above. It
  showed that `PipelineError` inherits `ValueError`: the JSON wrapper had
  replaced Docker's exit 55 with 1. Capture now occurs outside the parsing try
  block; the final environment suites above verify the correction.
- `builds-expected-state-final-python312.log`,
  `builds-expected-state-final-python314.log`: 17 tests passed on each
  interpreter after updating the tracked sample expectation. The additional
  case compares the actual checked-in sample documents through the real
  expected-state path and strict loader, then proves the existing whole-file
  perimeter rejects a timeout change. No remote transport is permitted in
  that sample comparison.

Verification commands used Python 3.12 and 3.14 with pinned PyYAML 6.0.3 and
jsonschema 4.26.0. Renderer commands used the adjacent locked script environments.
`git diff --check` passed in both owning worktrees.

## Remaining gates

No remote settings, product files, gitlinks, registration, Builds pin, delivered
ref or release were changed; no push, dispatch, delivery or credential cleanup
was performed. No nested submodule was initialized.

The compatible shared Builds release must be reviewed, published and pinned
before Tenants registration. AD-21 must complete before Tenants product work.
All product graph/test/action/bootstrap migration, candidate validation against
the acceptable published release and live actions, App adoption, immutable
release/legacy-access cleanup, green adopted CI and next scheduled nightly
outcome remain incomplete. Local controlled-tool tests do not qualify real
hosted Dapr/Docker freshness, private provisioning or preserved Tenants workload
duration; those require their later authorized execution stages.
