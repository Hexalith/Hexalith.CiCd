# Works export-byte proof and current readback, 2026-11-25

## Scanner proof inputs

The scanner no longer accepts the Works Platform gitlink from a fixed commit
list. After the normal setup and `.gitmodules` checks, it acquires the exact
committed gitlink. It then requires the reviewed bytes of the Platform export
implementation in that commit's tree. That implementation is
`eng/works_host_snapshot.py`, Git blob
`52dfe0ea4b6357a3ed04a330211ff4f162885925`, SHA-256
`a80fb6fa9be866236fed99bd337eeee716440ea5f36ee5615033e0e5260a8a77`. The
coordinator loads it from the initialized checkout and runs the shell verifier
from its sealed export. The proof assumes this export behavior and does not
trace it. Platform `616e2778`, `4de0bfff` and `3bcac63c` carry this blob.
Platform `99a17baa` carries blob `78088bfe04b8a68f1b366d2e129a0635141a7320`,
so the scanner no longer proves it.

Before hashing, the Works workflow fingerprint replaces each immutable
`v<major>.<minor>.<patch>` release tag of a `Hexalith/Hexalith.Builds`
reference with the literal `vX.Y.Z`. Input that already contains that literal
is unproved. The reviewed `v6.8.1` rendering
(SHA-256 `489af3156c4404594cc585efbd556c306c89934baceff872b03b620549ffc252`)
and the delivered `v6.8.3` rendering (SHA-256
`dacc0de507f72593f0e54869e3c3a03041abbaf66be1c04ab440db71a2c41058`) mask
to SHA-256 `528c2bb1cafa7a77df61731089671981b4e791fb7b02bafed0341f0cc485502e`.
The exact action and materializer fingerprints are unchanged.

A missing or non-commit gitlink still fails with
`unproved Platform gitlink for computed checkout/export: references/Hexalith.Platform`.
A changed or missing export implementation fails with
`unproved computed Platform source: references/Hexalith.Platform/eng/works_host_snapshot.py`.
The loader can run committed bytecode instead of the reviewed source. The
scanner therefore rejects any `eng/__pycache__/works_host_snapshot.*` item, and
any non-directory `eng/__pycache__`, with
`unproved computed Platform source: <item path>`. Platform `3bcac63c` and
`616e2778` commit no `__pycache__` items.

| Scanner source | Git blob |
| --- | --- |
| `tools/delivery_runtime.py` | `e53d73c39a1d0ae87ef85ff34991a3405fc14977` (unchanged) |
| `tools/scan.py` | `3f525f3c1afd534b5381b16fad99bb5dfa741337` (unchanged) |
| `tools/scan_discovery.py` | `8ec16256f74e20f98fc7149e70d6800b8f504069` |
| `tools/tests/test_scan.py` | `ae1dfe2b5f7bb81530dab5004094f18996c01724` |

## Verification

The extended boundary test first proves the original pin. It then proves a
later Platform commit that keeps the export bytes and changes a traced helper.
In that case the workflow advances its two Builds tags to `v6.8.3` and
`v6.10.0`. Discovery records the new gitlink in `pinnedSources` and follows
the changed helper. The test rejects each of these cases with the exact
diagnostic:

- the workflow changed outside its tags, a mutable Builds branch, a
  prerelease tag, a tag-like branch, the literal mask, and the tag of a
  lookalike repository or a lookalike owner
- a changed action, a substituted materializer or an import shadow
- a changed or missing export implementation, committed bytecode for it and a
  symlinked bytecode cache, each keeping the examined gitlink in
  `pinnedSources`
- a missing gitlink, or a blob or symlink in the gitlink's place

A traversing target and an unresolved Platform descendant still fail. A
second test uses the unpatched production constants. It binds the workflow
digest to `rendered/Hexalith.Works/.github/workflows/ci.yml`, before and
after retagging every Builds release tag to `v99.0.1`. It also requires each
export implementation path to be a fixed entry target.

All test results below used Node 24.22.1, Python 3.12.13 and the documented
locked command from [the duplicate-scan guide](../../../../../docs/duplicate-scan.md),
`run-with-temp env UV_NO_CACHE=1 uv run --locked --script --python 3.12 tools/tests/test_scan.py -v`.
The focused runs and shards add test names before `-v`. Both focused tests
passed with output SHA-256
`bdc583c1e3a8d71da02160375490ce79647eefbd29ec5c4a2d8278d5c0bdb7ee`.
Each of the following changes made a focused test fail:

- removing the export byte check
- removing the bytecode guard, or limiting it to cache files
- removing the mask
- accepting the literal mask
- loosening the tag grammar
- dropping the Builds repository anchor or its owner lookbehind, which failed
  the lookalike owner case
- renaming the export implementation away from its entry target
- changing the workflow digest

The locked scanner suite passed all 137 tests in six disposable shards.

| Shard | Tests | Output SHA-256 |
| --- | ---: | --- |
| 0 | 23 | `2e9dc00f952e1bf823ced8cb7be3e18aa8f65c6e74f3f06509dc40303164d21d` |
| 1 | 23 | `812c40ffc71aa4b161471647bbfb8efb738cbc30ecafb0cd6338c3b29ef6511c` |
| 2 | 23 | `d2a73a0c1ebe9267fb83bce9348b3b9b1056e83ebfe49ec5dcc1d6dbacf30be6` |
| 3 | 23 | `589ddb438f01afe421c365a7b7c76e70b0f42b871ea3389f73195b6cfadf7c3a` |
| 4 | 23 | `93a6815ff891a199ef48fcb29eb7bc8976a62bbc154206be2ac21042bf98c6c4` |
| 5 | 22 | `0c4127d8acfee75829627542d8f763d47b2aeef27c0de59c047f169fe0abeee0` |

The locked renderer check exited 0 with empty output after the local Builds
reference fetched the `v6.8.3` tag at
`62876129eaa035e78bd0324419231f07d43a07b8`.

## Local production scan of current Works `main`

Anonymous readback of Works `main` returned
`96d231d54bc0a8b33004e828ebdeb1becb3bd15e`, tree
`070edaeea81d28191e538c07259dab25fe3d2de2`. It pins Platform
`3bcac63c6fe20b46687b6e0bb7a333ea8c66fb4d`, tree
`a0acae2d4ea008333e5b88933660f73e39e426de`, and Builds `v6.8.3` at
`62876129eaa035e78bd0324419231f07d43a07b8`. The workflow blob is
`e00325d529394d45255bb8e638f38b4e00660ff2`. The action and both
materializer blobs match the [previous qualification](platform-boundary-qualification-20261125.md).

Both runs used the normal controller with production transport, Node 24.22.1,
Python 3.12.13 and verified jscpd 5.4.3 signatures. Both recorded production
policy SHA-256
`abd8c8ad7ad31d1b315f6fe73742e410b245016f0b63c6ceabecc8615c41ffd8`.
Both reported zero run-level errors and no duplicate findings.

| Controller | Works row | Report SHA-256 |
| --- | --- | --- |
| `0a02af88c7ba4824d7cbc40198c6cded77abaca3`, tree `2fb62b332c84316c1eedf8cfcc391b4ab448c70a` | Fail, 6 files, 16 diagnostics led by `unproved computed Platform source: .github/workflows/ci.yml`, no `pinnedSources` | `737fc5687f6576dca1f43669fc78b21752dda6e9220ce78d4178a661eecbf77d` |
| Disposable `2917c0f252984fb1c62c4c93636185b1c97f2e3f`, tree `f1ffe8b661d2dc64f986a6e109ff2b9e78c48e74` | Fail, 43 files, 130 diagnostics, `pinnedSources` Platform `3bcac63c6fe20b46687b6e0bb7a333ea8c66fb4d` | `736f8f99249564700164e175ea4322257113e60365183bbba7706b6fb3858289` |

The disposable controller is CiCd `0a02af88` plus the two scanner sources
above. The Works boundary diagnostic is gone. The selected-file list has
SHA-256 `283c7553f6721fad2a045da8d11f51db028c77d4a8afa0915522d51ccddfed07`,
computed over its `path sha256` lines with LF line endings. It contains 37
Platform files and these 6 Works files:

- both registered actions
- both materializers
- `scripts/verify-platform-parity-ci.sh`
- `scripts/verify-source-debug.py`

Of the 130 diagnostics, 128 are in Platform and 2 are the Works
source-identity diagnostics at `scripts/verify-source-debug.py` lines 67 and
78. The compact JSON diagnostic array has SHA-256
`b952970d6771f587e8463cbd88cd09331d25bbbe595217202250a292c74640b0`. This
matches the array recorded at Platform `616e2778`. The [owner table](platform-boundary-qualification-20261125.md#remaining-discovery-owners)
applies unchanged at `3bcac63c`.

## Hosted CI on current Works `main`

Platform `3bcac63c` names tuple `v6.8.3` with Builds gitlink
`62876129eaa035e78bd0324419231f07d43a07b8`. The authenticated Builds tag
ref resolves to the same commit.

The hosted CI result was run `45627444691`, attempt 1, on the exact Works
`main` above.

- **Shared CI.** Job `139251312243` passed.
- **Platform parity.** Job `139257523856` failed. Its log has SHA-256
  `1a783be66f2c14b222561ace72afd37be099f4361fca8aa2d2eb02565e868a7a`.
  - **Preparation.** The published Builds preparation succeeded, which
    resolves the earlier tag-to-gitlink failure.
  - **Canonical gate.** The gate exported Platform `3bcac63c` and ran
    through `retained-host-preflight`. It then failed the
    `platform-recovery` lane.

Authenticated artifact `15030304406` has GitHub digest and ZIP SHA-256
`6d5f6d5c2a6f36dbfe6d1232ea83b0e18523122283702e63ca25242cd862cbc1`.

- **Ledger.** SHA-256
  `29c81eb054bd22818c805204eb35b512687a59ca2fc49f761dfa334c739218b9`. The
  ledger is `incomplete`.
- **Recovery results.** `platform-recovery.xml`, SHA-256
  `ce9786f9c0c04bbdd7fea290a2fe2dfbe8900590a6f5a2217748ba5e3d42260a`,
  reports 10 tests: 8 passed, 2 failed and 0 skipped.
- **Failed tests.** Both are in `WorksSdkRecoveryPipelineSmokeTests`:
  - `SuccessfulCallbacksRegisterSdkReminderAndProcessWithoutPeriodicRecovery`,
    line 164
  - `SdkRemindersAndCascadeConvergeThroughPersistedReceiptsAcrossRestart`,
    lines 301 and 732
- **Failure.** Startup and readiness passed. The innermost exception is
  `System.ObjectDisposedException` for `RSAOpenSsl`. It is thrown from
  `WorksAppHostSmokeHarness.MintToken`, at
  `tests/Hexalith.Works.IntegrationTests/WorksAppHostSmokeHarness.cs:1018`
  (blob `e4a78de4ae60969b619c9a7a5b9530b2d26685fa`).

The failing method came from Works
`1ce938a44e8d0946d2b0ab933f0a5e6b47c7a95d`, `fix(tests): mint Platform
recovery commands with the proof RSA issuer`. It signs with a `using RSA`
instance and a fixed key ID. This is a Works test defect for the Works owners,
to be fixed through a separate Works PR that keeps the retained tests. A
likely cause is a reused signing provider that still refers to a key disposed
after an earlier mint.

The shared job showed no Stage 4 scheduler bind failure. Builds still owns the
recurring `50006/tcp` diagnosis.
[CI run](https://github.com/Hexalith/Hexalith.Works/actions/runs/45627444691) ·
[Parity artifact](https://github.com/Hexalith/Hexalith.Works/actions/runs/45627444691/artifacts/15030304406)

## AD-21 maintainer readback

The command-local maintainer profile authenticated as account `6775094`
with both token overrides unset. It confirmed the following for Works
repository `1264171182`:

- **Releases and rulesets.** Immutable releases are enabled. Rulesets
  `27474176` and `27474178` are active.
- **Release environment.** `hexalith-release` allows only `main` and holds
  `HEXALITH_REGISTRY_USERNAME` and `HEXALITH_REGISTRY_PASSWORD`.
- **Publishing.** `HEXALITH_RELEASE_PUBLISH_ENABLED` is `true`.
- **Secret inventories.** The repository and Dependabot secret inventories
  are empty.
- **Legacy grants.** Works is absent from all eight legacy organization
  secret selections, including `NUGET_API_KEY`. The legacy Zot pair still
  selects EventStore, Memories, Parties and Tenants.
- **Pull grants.** The shared pull pair remains granted to Works in Actions
  and Dependabot.

The projected readback has SHA-256
`204bf2070d67a97af8c42ab65516943f8467855c12b04ffe71025bcfcd803ecf`. Scoped
NuGet policy `27451` and the absence of `20087` come from today's
[native policy readback](ad21-and-hosted-readback-20261125.md#adoption-and-publishing).

The Zot ConfigMap is unchanged at resource version `49008107`. The
deployment is at generation 26 with one ready replica.
`hexalith-works-publish` keeps read, create and update on `works` and
`works/**`. The legacy owner still has global admin and write on both Works
patterns. The projected ACL has SHA-256
`3ac5d062d0ea6a135dbf357812de3d22f1d51c5c901d8114970b7a98374955a0`. This
increment includes no qualified replacement, continuity proof or retirement
for the remaining Zot consumers.

## Nightly acceptance

The acceptance reader exited 1 on the latest completed scheduled Nightly,
`45603058797`, attempt 1. The output SHA-256 is
`61b2f617711853f16d343630c5e73b41f7c08f95162036995d64474f3d9c9c66`. Both
CodeQL jobs passed. Works release `45603549559` refused dispatch head
`0f7963233e721cd758e56000c1bff4da76706756` because its CI run
`45592491388` had not succeeded. No scan covered that head, and the first
delivery-wait CI failed after the pushed bump.
[Scheduled Nightly](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45603058797)

## Remaining owners

- **CiCd.** Publish the scanner through the normal CiCd path. Then qualify
  the exact Works `main` with the normal hosted scan at that scanner revision
  and production policy. The latest hosted scan, `45615203576`, predates this
  change.
- **Platform owners and CiCd scanner maintainers.** The 128 reachable
  Platform diagnostics at `3bcac63c` are unchanged.
- **Works and CiCd.** `scripts/verify-source-debug.py` still reports
  `unresolved computed subprocess cwd` at line 67 and
  `unresolved computed Python script invocation` at line 78.
- **Works.** The recovery-lane `MintToken` disposal failure above blocks
  passing Platform parity on the exact base.
- **Maintainer.** Qualify scoped Zot replacements for EventStore, Memories,
  Parties and Tenants and prove continuity. Then retire key
  `099585e7-fd9e-4aac-9042-56426c1add7b` and prove that the legacy owner
  cannot write Works repositories.
- **Builds.** Diagnose the recurring `50006/tcp` scheduler bind failure.
