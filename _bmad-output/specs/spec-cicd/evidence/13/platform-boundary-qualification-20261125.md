# Works Platform execution boundary qualification

The current Works `main` readback was `f934f53682fb6f8250370289103a19df65e9480e`,
tree `e050be7214752cb0113586fdf7ce60752b3ef6a6`. It retains the two registered
actions and delivered Builds `v6.8.1` at `bf8a28b4bbcec619e8d9764d335f786f2bafb69e`.
It advances the Platform gitlink from `99a17baaf6de626d5f59311544a6aa8f9865b695`
to `616e27789f935ebb7f7f33406150ecf2dc9913a2`, tree
`2906422b4cf761de5f33bf855af58ef06399ae91`. The workflow and both Works
materializers match the locked blobs from the previous checkpoint.

| Works source | Git blob |
| --- | --- |
| `.github/workflows/ci.yml` | `d5314356f9795abccba97c12eafcf8036fd40000` |
| `.github/actions/platform-parity/action.yml` | `f9f3b0c6a104542748fe74ecac58396b54b9ef1b` |
| `.github/actions/after-unit-tests/action.yml` | `24c2fbc9669907bde88f6b182859ef27cb5496d8` |
| `scripts/prepare-platform-builds.py` | `828c0fd10edbe70285fb697af75e21c25d19702f` |
| `scripts/verify-platform-parity-ci.py` | `3da6f5ab2dd67658c913b21783015e896ebbfb78` |
| `scripts/verify-source-debug.py` | `9aaea5d83ed38adb40657807f8795e37a06a620b` |

The controller checks the materializer fingerprints and the committed
Platform declaration, then resolves the exact gitlink. Preparation inspects
the initialized root, clones it locally and detaches at the inspected HEAD.
It calls the two fixed scripts in that clone. Its `GITHUB_ENV` write uses the
fixed `HexalithBuildsPublishedToolRoot` key and rejects CR/LF in the returned
tool directory. The coordinator loads the snapshot implementation from the
initialized Platform owner. It copies the verified Platform bytes into a
detached clone and exports them using the pinned implementation. The
snapshot's `origin_files` rejects ordinary symlinks and `create` verifies the
copied bytes, then compares the export's ordinary inputs to the declared
upstream Platform checkout. The unchanged Works action passes only the
artifact path, so the coordinator selects its fixed CI profile and the
recorded Works and SDK inputs. The scanner uses these proofs at
the four execution callsites and continues ordinary analysis into each
target. A changed proof input or an unresolved descendant fails discovery.

| Platform source at `616e2778` | Git blob |
| --- | --- |
| `eng/bound_builds.py` | `f43bee8737747b8b89f56574edc9b17736f7b024` |
| `eng/prepare_builds_artifacts.py` | `d1cdfedfd7323bd6f37a3d78a8e3d3c8708e8ad6` |
| `eng/works_host_snapshot.py` | `52dfe0ea4b6357a3ed04a330211ff4f162885925` |
| `eng/verify-works-host.sh` | `571c2ae624770ddf39fbe8a167956b739cd0e724` |
| `eng/verify_works_host.py` | `386bf4b142e65435884076174e36080ee3077e86` |

## Local production scan

The previous production controller `eeb0fbffd0ea65d514296529b77519498c56417f`
exited 1 on this base with six selected files and 16 Works diagnostics,
including `unproved Platform gitlink for computed checkout/export` at
`.github/actions/platform-parity/action.yml:1`. `pinnedSources` was absent.
The run reported zero run-level errors and zero duplicates involving Works.
Report SHA-256 `13fcfaca4e351081f08560046803bb46b80c72a44e12305666b1b13d711206b6`.

The paired scans ran the normal controller and production policy at disposable
CiCd commit `61107dca9b0ebba153cd13f6236e1e3a663b4a1c`, tree
`cc559f173edf18c2fb7ab8ac65152047fadc79f3`, with Node 24.22.1 and Python 3.12.
Production transport fetched live Works `main` for the base. For the separate
source-pin product candidate, only the Works fetch used the local exact Git
commit. The controller used the committed registration and anonymous HTTPS
for the other modules and for the Platform gitlink in both runs. Both verified
jscpd 5.4.3 signatures and recorded policy SHA-256
`abd8c8ad7ad31d1b315f6fe73742e410b245016f0b63c6ceabecc8615c41ffd8`.

| Scanner source | Git blob |
| --- | --- |
| `tools/delivery_runtime.py` | `e53d73c39a1d0ae87ef85ff34991a3405fc14977` |
| `tools/scan.py` | `3f525f3c1afd534b5381b16fad99bb5dfa741337` |
| `tools/scan_discovery.py` | `02b8a465a1102e2e45f129a52f1d1f1ead0da09a` |
| `tools/tests/test_scan.py` | `b0aea9d2ad78b5be46b8d141255016b70c365bec` |

| Works input | Commit | Report SHA-256 |
| --- | --- | --- |
| Live `main` | `f934f53682fb6f8250370289103a19df65e9480e` | `6a679a7c86e758b6ef40673d94fdcdc117591784ab87053317336e3fbc21b039` |
| Source-pin product candidate | `4c96591bf94f2345f4d2b7fa8f5077001182054e` | `bfc466410cf8f7f03aafa5b9acd2609b943d70a2a6345aff21f9456ea04704a5` |

The candidate tree is `61ec491630ae75911a5870b454e299942fe8ae52`. Its
parent is the base above. Both rows resolved Platform
`616e27789f935ebb7f7f33406150ecf2dc9913a2` and selected 43 source files.
There were zero run-level errors and zero duplicates involving Works. Both
scans exited 1. All 13 Works parity materializer diagnostics cleared, and
128 reachable Platform diagnostics and two separate Works source-identity
diagnostics remain. The identical Works diagnostic array has SHA-256
`b952970d6771f587e8463cbd88cd09331d25bbbe595217202250a292c74640b0`.

After Works `main` advanced to `0f7963233e721cd758e56000c1bff4da76706756`,
tree `c8c727d0737b93ff82696c4250571afe405b27b2`, the production transport
scanned that exact revision. Disposable controller
`40bdb6d858aee47cdef3739dc73ea8d6bd040e7e` had the same tree and production
policy as the paired scan. It verified signatures, selected 43 files at
the same Platform pin and reported zero run-level errors and no Works
duplicates. It exited 1 with the same diagnostic array. The report SHA-256
was `38b789f43e2b832433f45c15f786f4d87e039659ed798ee720e1e690e23a925d`.

The focused normal-controller fixture passed on the final scanner sources
with Node 24.22.1 and Python 3.12. It follows the computed call into a
committed launcher and reaches the pinned helper even after the dependency's
live branch changes. It rejects a substituted materializer, local Python
import shadow, substituted gitlink, traversing target, and a computed
executable in a downstream script without discarding the pinned source.
Test output SHA-256 `52d9f9ab4eeb137a8cfa805ad81aa18364cce8f572e19effb8bebbf4a6b9471b`.
CiCd's locked renderer check exited 0.

The locked scanner suite passed all 136 tests across six disposable shards
before moving the pinned-source transport and adding the import-shadow
check. The final focused result above covers the added import-shadow case.

| Shard | Tests | Output SHA-256 |
| --- | ---: | --- |
| 0 | 23 | `6f3a5d29a4987981963677eb347321e59a10ba6f6a5e773a0120d248cbc3d011` |
| 1 | 23 | `1baf3f4bcbc6cf455c5bd9c981f8b7c793725972cede630308788b6a1be290b8` |
| 2 | 23 | `c7d5734d47136c259c97a623b6f441632b3cfc5113bf3f139218a18177c4789f` |
| 3 | 23 | `721228a186efee5ac43cf7b863d8ea0d100fefb3ee8ea521b6631f280fbcc0ea` |
| 4 | 22 | `1526070060a096c50ac2f37ad99758d9026a3233239943244b58ec8b84642727` |
| 5 | 22 | `91cc728a1a365fa700634c3348f2d59af7b116e1d886af7eff45cfc8c419052e` |

## Remaining discovery owners

The current Works materializer blobs need no source change for the proved
Platform boundary. The separate Works source-identity hook still reaches
`scripts/verify-source-debug.py` at the Works revision above. Works and
CiCd own proof of the executor's working directory and command forwarding
at line 67 (`unresolved computed subprocess cwd`) and of the Windows
`taskkill` process ID operand at line 78 (`unresolved computed Python script
invocation`). The committed verifier forwards Git and MSBuild commands through
a logging callback and retains Windows process-tree cleanup. A candidate
must preserve both behaviors.

The reachable Platform diagnostics below belong to the Platform owners and
CiCd scanner maintainers. Paths are under `references/Hexalith.Platform/`
at `616e27789f935ebb7f7f33406150ecf2dc9913a2`. Each reported message starts
with `local-script discovery: `. The shell verifier's stdin-fed Python
block, the test that compiles extracted cleanup statements, and the
runtime-opened `/proc/self/fd` executable still need an execution target
proof from committed inputs or a Platform-owned change preserving those
tests and their process-binding behavior.

| Platform source | Exact diagnostic and lines |
| --- | --- |
| `eng/bound_builds.py` | `unresolved computed subprocess cwd` at 31, 41, 46. `unresolved computed subprocess env` at 71. |
| `eng/builds_tool_lock.py` | `unresolved computed Python script invocation` at 104. |
| `eng/builds_tuple.py` | `unresolved subprocess positional/options expansion` at 72, 86, 93. |
| `eng/current_catalog_view.py` | `unresolved computed subprocess cwd` at 126. |
| `eng/ext-host-1/prepare_acceptance.py` | `unresolved computed Python script invocation; unsafe or unresolved forwarding` at 114. `unsupported Python search-path mutation` at 130, 148, 216. |
| `eng/ext-host-1/test_prepare_acceptance.py` | `unresolved computed Python script invocation` at 12. `unresolved computed subprocess env` at 17. |
| `eng/ext-host-1/test_verify_full.py` | `unsupported Python search-path mutation` at 124. `unresolved computed subprocess env` at 164. `unresolved computed Python script invocation` at 326, 327. `unresolved computed subprocess cwd` at 724, 730, 741, 753, 766, 770. |
| `eng/ext-host-1/verify_full.py` | `unresolved computed subprocess cwd` at 103, 361, 374, 385. `unsupported Python search-path mutation` at 466. |
| `eng/ext-secrets-1/local-transport/run.py` | `unresolved computed subprocess executable` at 47. |
| `eng/isolated_daprd.py` | `unsupported reflective use of a process/import API: os.execv` at 50. |
| `eng/prepare_builds_artifacts.py` | `unresolved computed subprocess cwd` at 22. `unresolved computed Python script invocation` at 122. |
| `eng/retained_works_host.py` | `unresolved computed Python script invocation` at 30. |
| `eng/test-local-dapr-security.py` | `unresolved computed Python script invocation` at 25, 26, 146, 227, 229, 230, 231. `unresolved computed Python script invocation; unsafe or unresolved forwarding` at 98. `unresolved computed subprocess env` at 162. |
| `eng/test_bound_builds.py` | `unresolved computed subprocess env` at 19. `unresolved computed Python script invocation` at 104, 109, 151. |
| `eng/test_current_catalog_view.py` | `unresolved computed subprocess cwd` at 44. |
| `eng/test_isolated_daprd.py` | `unresolved computed Python script invocation; unsafe or unresolved forwarding` at 78. |
| `eng/test_local_dapr_security_cleanup.py` | `unsupported Python process/import API: compile` and `unsupported Python process/import API: exec` at 34. |
| `eng/test_verify_platform_pins.py` | `unresolved computed Python script invocation; unsafe or unresolved forwarding` at 61, 118. `unresolved computed Python script invocation` at 71, 105, 135, 205, 226, 252, 264. `unresolved computed subprocess cwd` at 159. |
| `eng/test_verify_works_host.py` | `unresolved computed subprocess env` at 731, 756, 766. `unresolved computed subprocess cwd` at 748, 867. |
| `eng/test_works_host_snapshot.py` | `unresolved computed Python script invocation; unsafe or unresolved forwarding` at 65. `unresolved computed Python script invocation` at 123, 141. |
| `eng/test_works_toolchain.py` | `unresolved computed Python script invocation` at 38. `unsupported reflective use of a process/import API: subprocess.check_output` at 133. |
| `eng/test_works_verifier_command.py` | `unresolved subprocess positional/options expansion` at 234. `unresolved computed Python script invocation` at 305. |
| `eng/verify-agents-host.sh` | `unsupported shell compound/subshell execution` at 11, 15, 17, 18, 22, 23, 27, 28, 33, 34, 39, 40, 45, 49, 50, 53, 54, 55, 58, 63, 83, 87, 88, 90, 93, 104, 106. `unsupported shell command substitution` at 5, 59, 64, 68, 73, 75, 77, 80. `unresolved computed operand of unknown command: case` at 16, 48, 52, 57, 62. `unresolved computed command: $BUILDS_ROOT` at 67. `unresolved local-script target: $ROOT` at 70. `unresolved computed operand of unknown command: rm` at 74. `unsupported stdin-fed interpreter; coverage unsupported` at 89. `unresolved local-script target: $ROOT/eng/verify-platform-pins.py` at 91. `unresolved computed operand of unknown command: -d` at 98. `unresolved local-script target: $ROOT/eng/ext-host-1/verify_full.py` at 108. `unresolved computed operand of unknown command: dotnet` at 113. |
| `eng/verify_works_host.py` | `unresolved computed Python script invocation` at 1029, 1149. `unresolved computed Python script invocation; unsafe or unresolved forwarding` at 1049. |
| `eng/works_host_snapshot.py` | `unresolved computed Python script invocation; unsafe or unresolved forwarding` at 65. |
| `eng/works_toolchain.py` | `unresolved computed Python script invocation` at 77. |
| `eng/works_verifier_command.py` | `unresolved computed subprocess cwd` at 87. |

Complete discovery on a candidate and hosted qualification on the exact
publication base remain open. The unresolved pinned Platform sources are
independent of the Works source-identity diagnostics. The scoped Works-only
PR prerequisite cannot clear this base's diagnostics.
