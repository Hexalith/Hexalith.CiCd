# CiCd validation fix, Works readback and Platform reachability, 2026-11-25

## CiCd validation regression

Delivery run [45652152586](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45652152586),
attempt 1, on CiCd `850b1ce87e53c5260dae28ed71533bdb58a8c786` failed its
`validate` job `139339216124`. All seven module validations passed. The
global tool suites failed one test:
`test_repository_inputs.py` `test_tracked_suites_do_not_read_the_real_setup_or_rendered_registry`
reported `tools/tests/test_scan.py:1903: suite reads repository-root rendered/`.

The cause was a review patch from the scanner increment. That test bound the
production Works workflow digest to the live
`rendered/Hexalith.Works/.github/workflows/ci.yml`, and repository rules keep
suites off the live registry. The increment's verification ran the focused
tests, the scanner suite and the renderer check, but not `tools/validate.py`.

The fix removes that read and the unused `re` import. The renamed
`test_works_platform_production_export_is_a_loaded_entry_target` still
requires each export implementation path to be a fixed entry target. The
boundary test still covers the masked fingerprint, its retagged cases and its
rejections, using patched constants. A CiCd suite no longer flags drift in
the rendered Works workflow outside its Builds tags. The hosted scan then fails
the Works row with
`unproved computed Platform source: .github/workflows/ci.yml`.

## Verification of the fix

All commands ran from CiCd with Python 3.12.13, as
`run-with-temp env UV_NO_CACHE=1 uv run --locked --script --python 3.12 <suite>`.

| Check | Result | Output SHA-256 |
| --- | --- | --- |
| `tools/tests/test_repository_inputs.py` | 39 tests passed | `0339097fc45221822fc0f6eb1daa3581908368de3ebcfe7f64b968b81b7febc0` |
| `tools/tests/test_scan.py` | 137 tests passed | `a31f33da381915f2b156d25fc122dcdddf27861d153b67df9b0f0cb8dd00c0cf` |
| `tools/tests/test_delivery_workflow.py`, run alone | 26 tests passed | `d33f30bd50147d6cf9bc537efe18485ec3c45c7bd3819b2e94935fb49cfd3fbc` |
| The other 26 non-pin `tools/tests` suites | passed | |
| `tools/check_global.py --suites pin` | See below | `f6b949bbb4073d423c651332885f2a2d4425d5886f62f4fdf292fcf50a9f5637` |

The `check_global.py --suites pin` run had three outcomes:

- **Passed.** The inventory, committed render inputs, committed render, render
  reproducibility and schema checks, and four pin suites.
- **Exceeded the local limit.** `test_delivery_workflow.py` passed its 600-second
  limit and then passed when run alone.
- **Not run.** The bootstrap, Builds publication and workflow-lint checks need a
  read-only GitHub token. They did not run locally.

The full `tools/validate.py --scope full` exceeded its 1800-second global-check
limit on this workstation. All seven module validations passed in that run,
so the suites ran as above. The EventStore pre-adoption suite did not run
locally. Delivery on the pushed commit is the complete gate.

## Works `main` readback

Works `main` is `2e4f9a23818d51747bb21bc3e233703774602220`, tree
`10a81f54b4a03c695f28eaae466a8d8e8f1b84d4`. Since `96d231d5` it changes
only four integration-test files. The workflow, both actions, the three
scanned Works scripts, the Platform gitlink `3bcac63c6fe20b46687b6e0bb7a333ea8c66fb4d`
and the Builds gitlink `62876129eaa035e78bd0324419231f07d43a07b8` keep the
blobs recorded in [the export-byte proof](export-byte-proof-20261125.md).

Hosted CI run [45648021145](https://github.com/Hexalith/Hexalith.Works/actions/runs/45648021145),
attempt 1, ran on that commit.

- **Shared CI.** Job `139324206731` passed.
- **Platform parity.** Job `139327830633` failed in the `platform-recovery`
  lane. Artifact `15040548279` has GitHub digest
  `979ca3da8ec2ed757b5209c6ed221b9908c8d9a716dfd957af45f9188e52cfa6`.
  - Ledger SHA-256 `600fb524b3e64ebe55500b85013517e6231f0ab7d6bd4a1605d365deea1d66dd`, status `incomplete`.
  - `platform-recovery.xml` SHA-256 `8acefe9cb24bdf594cc86d4614ce151f57e773f6052ce51c64d89de58b7cae4d`
    reports 10 tests: 8 passed and 2 failed.
  - The same two `WorksSdkRecoveryPipelineSmokeTests` tests fail, at lines
    164 and 301/732. The `MintToken` `ObjectDisposedException` is gone.
    Each body now ends in `TaskCanceledException` after startup and readiness
    passed. The host logs repeat `ProcessEvidenceUnavailableException` from
    `WorksSourceStreamReader.ReadCoreAsync` through
    `EventStoreGatewayClient.SendWorkloadAsync`.

This remains a Works defect for the Works owners.

## Platform reachability check

The scanner could not have reached the 128 Platform diagnostics through a
broad or spurious reference: Works CI runs that code. At Platform
`3bcac63c`, tree `a0acae2d4ea008333e5b88933660f73e39e426de`, entry target
`eng/verify-works-host.sh` (blob `571c2ae624770ddf39fbe8a167956b739cd0e724`)
execs `eng/verify_works_host.py` (blob `386bf4b142e65435884076174e36080ee3077e86`).
Its lanes run:

- **Lines 1443–1444.** `evidence-gate-tests` and
  `component-evidence-gate-tests` run Platform's own `unittest` modules.
- **Lines 1450 and 1453.** `agents-full-refusal` and `agents-local-scaffold`
  run `eng/verify-agents-host.sh` (blob `9e5769a3e87e806875d1d36c04441f83c4d28557`).

The parity artifact above holds the logs of all four lanes.

| Location | Diagnostics |
| --- | ---: |
| `eng/verify-agents-host.sh` | 48 |
| Platform test modules | 51 |
| Other Platform Python | 29 |

By kind, the diagnostics are:

| Kind | Count |
| --- | ---: |
| Computed Python script invocation, including 8 with unresolved forwarding | 38 |
| Shell compound or subshell execution | 27 |
| Computed subprocess `cwd` | 20 |
| Computed subprocess `env` | 8 |
| Shell command substitution | 8 |
| Other | 27 |

Narrowing traversal clears none of them without changing the detection policy.

## Remaining owners

- **CiCd.** Record the hosted scan from the next scheduled run on the fixed
  scanner. Settle the next scanner increment through a spec update.
- **Works.** Fix the recovery-lane failure above.
- **Maintainer.** The legacy Zot cleanup from [the export-byte proof](export-byte-proof-20261125.md#ad-21-maintainer-readback)
  is unchanged.
- **Builds.** Diagnose the recurring `50006/tcp` scheduler bind failure.
