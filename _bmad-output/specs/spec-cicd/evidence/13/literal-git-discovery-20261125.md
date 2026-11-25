# Works literal Git discovery, 2026-11-25

## Exact inputs

Works `main` read back as `e6e4d1928c09bbde2f8f05c6a6a0211ddce89035`, tree
`04c3a2b3c41761a0c3de108599afa2950bac1167`. It pins Platform
`3bcac63c6fe20b46687b6e0bb7a333ea8c66fb4d`, tree
`a0acae2d4ea008333e5b88933660f73e39e426de`, and immutable Builds `v6.8.3`
at `62876129eaa035e78bd0324419231f07d43a07b8`. Its delivered workflow,
Platform parity action, materializers and source-identity script retain the
following blobs.

| Works source | Git blob |
| --- | --- |
| `.github/workflows/ci.yml` | `e00325d529394d45255bb8e638f38b4e00660ff2` |
| `.github/actions/platform-parity/action.yml` | `f9f3b0c6a104542748fe74ecac58396b54b9ef1b` |
| `scripts/prepare-platform-builds.py` | `828c0fd10edbe70285fb697af75e21c25d19702f` |
| `scripts/verify-platform-parity-ci.py` | `3da6f5ab2dd67658c913b21783015e896ebbfb78` |
| `scripts/verify-source-debug.py` | `9aaea5d83ed38adb40657807f8795e37a06a620b` |

## Verification

With Node 24.22.1 and Python 3.12, the focused locked scanner run passed seven
tests. It covered the nine read-only Git modes, local acquisition with literal
flags and `--`, conditional environment keywords, tuple expansion, bounded
wrapper callers, references under a literal `cwd` and chained `-C` options,
and refusal of a linked Git directory or an executable, environment or
Git-option substitution. The
list of tests also included the exact-pinned Platform boundary fixture.
Output SHA-256
`3f01d6066c2d9116cd5052b2006b4252f2983466a04e33001d5eda3efb215e66`.
The locked renderer check exited 0. Reproduction commands are in the
[duplicate-scan guide](../../../../../docs/duplicate-scan.md#calibration-and-retuning).

The standalone `python3 references/Hexalith.Builds/check.py` exited 0 in a
clean disposable checkout of Works `e6e4d1928c09bbde2f8f05c6a6a0211ddce89035`
with all 15 direct dependencies at the recorded gitlinks and zero nested
dependencies. The checkout remained clean. Output SHA-256
`b7103a6fa410e476acc7a18791f9653f731380805fa837fc9ffb949bbadc2a2c`.
This verifies the adopted Works source for the revision examined locally.

The locked scanner suite was run in six disposable shards at the scanner
revision immediately before the literal `-C` linked-directory guard
(scanner blob `32fbdbb363e009269d9362667cc45afd9b4b1b02`). It ran all 141 tests.
Five shards failed. All 35 failing test or subtest assertions contained the
unchanged PowerShell parser's `timed out after 30 seconds` diagnostic. A
standalone parse probe completed in 29.72 seconds. The seven focused tests
above include the final linked-directory guard. The superseded unsharded
scanner attempt was interrupted after observing parser timeouts. Its output
SHA-256 was `7db094fe6de8338a6a3efbece1f8384becfe38988ea52a28476ea401979794df`.

| Shard | Tests | Result | Output SHA-256 |
| --- | ---: | --- | --- |
| 0 | 24 | Fail, 9 assertions | `66ddbc8081e59f8a99859d0c2c9d2a5c2d5e1a2661de08d6b9667e063fbef052` |
| 1 | 24 | Fail, 5 assertions | `12fe5585ee62fa1cea12bb20ee2ca5845073b1b4507e129162f7ede244260675` |
| 2 | 24 | Fail, 18 assertions | `a94439076978f984b5e05293b4c145fe9ebf952f6894e441374f4b6e600a32e5` |
| 3 | 23 | Fail, 2 assertions | `1240359c18c1b48314a1c44872391b7fc3e491210349c0ad7b483b94b852bb65` |
| 4 | 23 | Fail, 1 assertion | `93c6d894718ccf91f2b46cac03fd6f33959771b4a0698019b7d71246d9530af7` |
| 5 | 23 | Pass | `c28ad7c1eb805212e12c8ac5a6a48d7361dee399161f5696d17382b65d50c652` |

After the shards exited, an isolated retry of
`ScanTests.test_review7_powershell_environment_output_uses_separate_lines`
passed on the final tree in 13.312 seconds. It used the same locked scanner
command and the unchanged parser timeout. Output SHA-256
`14ae203b9d8876e993164bf7f62ebec3875b7acd1a3d56f1665c56546b5687c1`.
The other 11 failed methods passed in a serial retry on the final tree. The
retry took 877.832 seconds with the existing timeouts and had output SHA-256
`9995fd2dde2ab7874e8093827ef36ae785d41f9ac514be6fb323950d5e9f0bd7`.
All 12 failed methods from the original shards passed on retry.

The full global gate exited 1. Its `tools/tests/test_scan.py` child reached the
existing 600-second suite timeout on the final tree. The other 33 tool
suites passed. The immutable delivery bootstrap, acceptable Builds
publication and online workflow lint checks also remained unverified because
the command had no read-only `GITHUB_TOKEN` or `GH_TOKEN`. Output SHA-256
`137a953b8757f64bbe238388c1fb99816d630346c4505f104f704316ba68740d`.

## Local production scan comparison

Both runs used the normal `scan.scan()` controller with the committed registry
and production detector configuration. Fetches used local objects, with the
same exact Works `main`, tracked Platform gitlink and cached non-Works
`origin/main` revisions in both runs. The scanner ran no module source.
jscpd 5.4.3 signatures verified and policy SHA-256 was
`abd8c8ad7ad31d1b315f6fe73742e410b245016f0b63c6ceabecc8615c41ffd8`.
Both reports had zero run-level errors and zero duplicate findings.

| Controller commit | Controller tree | Works row | Report SHA-256 |
| --- | --- | --- | --- |
| `4556ddb1e190c2e093e2c71fa09d727cf4f9afdf` | `21eb2fbe8394d7377e772a86eb9ad519fe51ef95` | Fail, 128 Platform and 2 Works diagnostics | `7b91a34dc631e068908ee3cb53d0fd5fa4ec13a2a0621852b84c9519b7aeb903` |
| Disposable `a002e612839cab6ac726f1baa5cc1f7b9117ad99` | `00563f08a49238e22870f9bf1cf593bb168c5e2c` | Fail, 124 Platform and 2 Works diagnostics | `ed704d521e7eebf41aceea89dca8fa5ea705c8511174db23597ea180d31bd24c` |

Both Works rows recorded the Platform pin and selected the same 43 files.
The compact JSON selected-file array has SHA-256
`36517a0d8e8c349d85de6b6b46f21fe58d6f6a04995e9fd8f8b7757bcc2a6888`.
The compact Works diagnostics array changed from SHA-256
`b952970d6771f587e8463cbd88cd09331d25bbbe595217202250a292c74640b0` to
`a87abae29fb2207dbb69238491226e11dbf8787e589c681fd663dd30656116fa`.
The same rule reduced McpCli diagnostics from 99 to 89 in its cached row.
Other non-Works counts were unchanged in the paired reports above. An earlier
candidate run recorded a PowerShell parser timeout at Conversations
`.github/actions/testsupport-windows/action.yml:9`. The retry cleared the
timeout and returned the same Works result. The earlier controller
was `4189f2c7cdc3ec027edcf4b4063a3e0917ecd566`, tree
`3d71c0522298032d48509d902a4234ff1fd7b8b9`, with report SHA-256
`606a6fd2ca9ccf2acbef5f979a6ff671e471d77d430efcc380614d62755d5b1d`.

The scanner change is Git blob `f9e5fa4637b4d45faeb8c681a9a88859ae12bd7b`.
The final focused tests are Git blob `b2c655689d822af0cccd8ccca2ccb3f0a6670a87`.
The measured count fell short of the expected Platform count of 115. The rule
still requires proof where a computed value can supply an execution-sensitive
flag, an alternate executable environment, or an unproved argv expansion.
Four sites cleared on the exact pin. They are
`eng/verify_works_host.py:1029,1149`,
`eng/ext-host-1/prepare_acceptance.py:114` and
`eng/test_bound_builds.py:109`. The latter two are under the lanes to move.

## Platform owner handoff

Move `evidence-gate-tests`, `component-evidence-gate-tests`,
`agents-full-refusal` and `agents-local-scaffold` from
`eng/verify_works_host.py:1443–1454` into Platform's own CI. Move their Agents
context and remove their ledger entries from Works parity. Remove files from
`VERIFIER_HELPERS` at lines 32–44 after their execution has moved. Keep the
R1–R11 parity gates and their outputs in the independent 180-minute job.
Reconcile the amended scope against the exact Works gitlink once those changes
are available. [Gate classification](../../gate-classification.md#works-classification-story-13)

The same verifier blob `386bf4b142e65435884076174e36080ee3077e86` is present at
the pinned Platform commit and at the read-back Platform `main`
`e416dfac2a6660efd0720fa1d278f8cda3fb329d`, tree
`41649e5fa60489bd65e248ba2c7d4b6d71a2e422`. The four lanes and helper list
remain in both trees. The prior reachability inspection attributed 109
diagnostics to that part of the graph. The scan now has 107 there. The
Platform change and a Works
`main` pin of the resulting commit are pending.
[Reachability partition](validation-fix-and-reachability-20261125.md#discovery-partition)

The main verifier path has 17 remaining Platform diagnostics. The following
11 are the Git sites from the earlier estimate that still require Platform
input or a separately qualified scanner proof. Paths are relative to the
Platform tree above. Diagnostic strings omit the common
`local-script discovery:` prefix.

| Platform site | Exact remaining diagnostic | Input to reconcile |
| --- | --- | --- |
| `eng/bound_builds.py:31,41,46,71` | `unresolved computed subprocess env` | Establish the inspection environment from committed code. The wrapper at line 71 also expands `map(str, arguments)`, supplies a `-c` override and forwards a checkout without `--`. |
| `eng/builds_tuple.py:72,86` | `unresolved computed subprocess env` | The conditional keyword shape is supported. The environment carried through that keyword still needs proof. |
| `eng/builds_tuple.py:93` | `unresolved subprocess positional/options expansion` | The assigned list argv and conditional environment still need proof. A computed `diff` revision needs an option terminator. |
| `eng/prepare_builds_artifacts.py:22` | `unresolved computed subprocess env` | The imported inspection environment still needs proof. |
| `eng/retained_works_host.py:30` | `unsupported Git mode or unresolved Git options` | Add a literal option terminator before the computed `show` revision or prove its operand. |
| `eng/verify_works_host.py:1049` | `unresolved computed Python script invocation; unsafe or unresolved forwarding` | The imported `BUILD_FILES` tuple and the computed archive tree position still need proof. |
| `eng/works_host_snapshot.py:65` | `unsupported Git mode or unresolved Git options` | The wrapper's archive callers supply opaque tree identifiers before any `--`. Changes to this export implementation require fresh reviewed-byte proof. |

The six remaining non-Git main-path sites are
`eng/builds_tool_lock.py:104`, `eng/current_catalog_view.py:126`,
`eng/isolated_daprd.py:50`, `eng/prepare_builds_artifacts.py:122`,
`eng/works_toolchain.py:77` and `eng/works_verifier_command.py:87`. Settle
these with the other remaining Platform sites after Works pins the lane move.

## Outstanding gates

- **Works.** `scripts/verify-source-debug.py:67` reports
  `unresolved computed subprocess cwd` and line 78 reports
  `unresolved computed Python script invocation`. The script remains reachable
  from the registered source-identity hook. A Works change must preserve that
  hook and pass exact-candidate discovery and the standalone checker.
- **CiCd.** The scanner has to reach CiCd `main` and run in the normal hosted
  scan workflow. A local scan of the Works base does not fulfill the hosted
  scan prerequisite.
- **Works and Builds.** Both hosted CI jobs must pass on the same exact Works
  `main` commit and delivered Builds pin. The shared scheduler bind failure on
  `50006/tcp` was routed to Builds. A separate Works product correction follows
  the Works PR path. [Hosted CI triage](hosted-ci-triage-20261124.md)
- **Maintainer.** The authenticated readback excluded Works from the eight
  legacy GitHub grants, including `NUGET_API_KEY`, and confirmed the scoped
  release environment and immutable releases. The Zot replacements,
  remaining-consumer continuity and retirement of the shared legacy key still
  require authenticated evidence before acceptance Nightly.
  [AD-21 readback](export-byte-proof-20261125.md#ad-21-maintainer-readback)
