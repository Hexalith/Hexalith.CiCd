# Works Platform scan prerequisite

## Works candidate

The product change starts from the freshly fetched Works `main` commit
`d55cda77c2a42bc523aa3664647cdafb87c87be5`. The disposable verification commit
is `ce91a2893e766364b4ee59f1d7520f36fe08f762`, tree
`75929f99b18b8c1114df4d09867c04e9e1d62f54`. The candidate is local.

The parity action invokes the published Builds preparation in Python, with a
compatibility shell entry point. The preparation still inspects the physical
Platform checkout and refuses dirty or hidden-index inputs, makes the same
isolated checkout without initializing nested submodules, calls the same
producer verifiers, validates the returned tooling directory, and appends the
same GitHub environment output only after the final source check. The parity
coordinator, 180-minute job and its fixture commands keep their existing
inputs, runtime requirements and artifacts.

| Candidate source | Git blob |
| --- | --- |
| `.github/actions/platform-parity/action.yml` | `f9f3b0c6a104542748fe74ecac58396b54b9ef1b` |
| `scripts/prepare-platform-builds.py` | `828c0fd10edbe70285fb697af75e21c25d19702f` |
| `scripts/prepare-platform-builds.sh` | `655a04530d3dbccc85bbf01a05215caadd7c7e60` |
| `scripts/tests/test_platform_builds_preparation.py` | `52b96b77c55da70ccb7e16bab7ad36e4c0bbd567` |

All 47 Platform preparation, parity and proof-input fixtures passed on the
disposable candidate with 15 direct dependencies and zero nested checkouts.
Fixture output SHA-256
`c2b3ff247bb3bbe752b47d884365870d0f8ff4e37878432e35187f89ac426099`.
Direct pin inventory SHA-256
`931e483c0db184bbc4c2021ed25ecca2d1659c721ab329985e92fe86e5925280`.
All 20 source-identity fixtures passed on the same candidate, including the
actual preflight under ambient Git redirection. Combined output SHA-256
`1ff7099db1991132985c002f8d3c61049579893f99e09eccf3be2778091a04db`.
The standalone released Builds `check.py` exited 0 on the exact candidate
with authenticated `origin/main` at its parent. The owned-content and action
guard passed, the package-mode Release build finished with zero errors, and
ArchitectureTests, PropertyTests and UnitTests passed. IntegrationTests
remained in the integration partition and the test exclusion list was empty.
The disposable worktree finished clean. Checker output SHA-256
`2b29106d5703a9d5104ba526ec1589540d68136d0deb9355b85d6d29fe826c8b`.
CiCd's locked renderer check exited 0.

## Controller reproduction

CiCd `eba76b2d4680eab1a02b7a88df6021a5f4cb3b5f` scanned the exact candidate
using the production controller and policy, with only Works' Git transport
pointing to the disposable source. jscpd 5.4.3 verified signatures. The policy
SHA-256 was `abd8c8ad7ad31d1b315f6fe73742e410b245016f0b63c6ceabecc8615c41ffd8`.
There were zero run-level errors and zero measured copies. The coverage row
failed, with 18 diagnostics across six discovered files, compared with 26
diagnostics on the Works baseline. The report SHA-256 was
`82752ac41f48a42c8b470a6828247a5c9956011c9f254be6758d65c6be818ef2`. The
Works diagnostic array SHA-256 was
`018980ac3bfa63abc33729618e7b604b47a3ed74e8cf18e0c54a5851c291c9fc`.

| Candidate source and lines | Remaining scanner diagnostic |
| --- | --- |
| `scripts/prepare-platform-builds.py:25,29,33` | `unresolved computed subprocess env` |
| `scripts/prepare-platform-builds.py:48,50,52,55` | `unresolved computed Python script invocation` |
| `scripts/prepare-platform-builds.py:65` | `unsupported Python access to GITHUB_ENV; coverage unsupported` |
| `scripts/verify-platform-parity-ci.py:44` | `unresolved computed Python script invocation; unsafe or unresolved forwarding` |
| `scripts/verify-platform-parity-ci.py:69` | `unsupported Python process/import API: importlib.util.spec_from_file_location` |
| `scripts/verify-platform-parity-ci.py:118,119` | `unresolved computed Python script invocation` |
| `scripts/verify-platform-parity-ci.py:338,341` | `unresolved computed subprocess env` |
| `scripts/verify-platform-parity-ci.sh:4` | `unsupported shell command substitution` |
| `scripts/verify-platform-parity-ci.sh:5` | `unresolved local-script target: $root/scripts/verify-platform-parity-ci.py` |
| `scripts/verify-source-debug.py:67` | `unresolved computed subprocess cwd` |
| `scripts/verify-source-debug.py:78` | `unresolved computed Python script invocation` |

## CiCd scanner prerequisite

The Works `references/Hexalith.Platform` gitlink selects
`99a17baaf6de626d5f59311544a6aa8f9865b695`, tree
`9bf9b18422df53b99e922419becebc1134ac7aed`. The pinned entry points were read
from committed Git objects.

| Platform source | Git blob | Works execution boundary |
| --- | --- | --- |
| `eng/bound_builds.py` | `f43bee8737747b8b89f56574edc9b17736f7b024` | Preparation executes it from the detached local clone. |
| `eng/prepare_builds_artifacts.py` | `d1cdfedfd7323bd6f37a3d78a8e3d3c8708e8ad6` | Preparation uses the recorded producer to verify and select the tooling directory. |
| `eng/works_host_snapshot.py` | `78088bfe04b8a68f1b366d2e129a0635141a7320` | The coordinator imports the fixed file from the initialized Platform checkout. |
| `eng/verify-works-host.sh` | `571c2ae624770ddf39fbe8a167956b739cd0e724` | The coordinator invokes this path after exporting and binding the sealed Platform checkout. |
| `eng/verify_works_host.py` | `94519455edc0bf5ac024206fe88bf13b9c3dd4e3` | The shell entry point resolves and executes the canonical verifier. |

Seeding static discovery from the first four Platform sources reached seven
files and returned 13 unique diagnostics. Among them were computed subprocess
cwd and environment in `eng/bound_builds.py:31,41,46,71`, unresolved invocation
in `eng/prepare_builds_artifacts.py:122`, unresolved forwarding in
`eng/works_host_snapshot.py:59`, and unsupported command substitution and
unresolved `$ROOT/eng/verify_works_host.py` in `eng/verify-works-host.sh:3,4`.
The probe SHA-256 was
`d8964483e41438f804339441617964a4f015133c553ed65d9f3bf62763426c44`.
Directly seeding the canonical Python verifier for diagnosis reached 37 files
and returned 130 unique diagnostics, including unresolved execution at
`eng/verify_works_host.py:1029,1049,1149`. The second probe SHA-256 was
`963c4ec516fb36625d4e6758a1ed4ec60855e3dcd949ef1a178df77798b772a9`.

The controller work must prove ownership and exact revision from committed
gitlinks and declarations, identify the materialized execution root and
script bytes with committed inputs, and follow the reachable sources beyond
the initial Platform entry points. Qualification needs a positive pinned
fixture and failing cases for unresolved targets, substituted references and
unsafe paths. The normal CiCd scan workflow must then report complete
discovery for the exact Works revision. The local detector and the manually
seeded probes leave that qualification open.

## Follow-up Works candidate

A fresh fetch of official `origin/main` returned
`d55cda77c2a42bc523aa3664647cdafb87c87be5`.
The disposable verification commit `c2d787e653dfe695cafeb9bc0c299aa6bf5056cf`
has tree `3d089ab7156d0ece9716c133a9d129ffba70f20f`. Builds `v6.8.1`'s
locked npm signature verification and commitlint passed on its commit message.
The corresponding product changes remain in the Works worktree on
`fix/works-parity-discovery`.

This candidate extends the preparation above in three source files. The
coordinator sends both the bootstrap help probe and the full CI profile
through one fixed `bash` call to `eng/verify-works-host.sh` under the sealed
Platform export. The full invocation retains the Works and SDK roots, snapshot
binding, artifact location and environment. The shell compatibility entry
point resolves its adjacent Python coordinator with `BASH_SOURCE[0]`
without a command substitution. The fixtures execute that entry point from
outside Works and by basename, and check the complete CI argv and source
binding in the normal Python path.

| Follow-up source | Git blob |
| --- | --- |
| `scripts/verify-platform-parity-ci.py` | `3da6f5ab2dd67658c913b21783015e896ebbfb78` |
| `scripts/verify-platform-parity-ci.sh` | `fb6a0ea750675f4ca6972caa4c135c4c8902e2b3` |
| `scripts/tests/test_platform_parity_ci.py` | `cbc3f51bd0edc8334dfd63a65e80f8f916ca615a` |

CiCd's locked renderer check exited 0 with output SHA-256
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

The standalone checkout matched all 15 direct dependency pins and initialized
zero nested checkouts. Direct pin inventory SHA-256
`1959b47b3a4fb143121b223e5163d17d8acf486fdd756ef2aa929f5f78125db5`.
All 48 Platform preparation, parity and proof-input fixtures passed, with
output SHA-256 `c08d46430398f1765684f81219abbecae8d22147e8fd32ad58fe1a851f5b29a7`.
All 20 source-identity fixtures passed, with output SHA-256
`e9cede3f06c5ded81edf5044a56e0bea3662480d30d07bf5310d84ceedc98291`.
The released `python3 references/Hexalith.Builds/check.py` exited 0 on the
exact candidate. The ownership and action guard passed. The Release
package-mode build had zero errors and 18 warnings. ArchitectureTests,
PropertyTests and UnitTests passed 386, 3 and 603 tests respectively, with
zero skipped. The IntegrationTests project was in the integration partition
and the exclusion list was empty. The disposable checkout remained clean.
Checker output SHA-256
`8a6d7e3e6897cecc2d9564e6cfae3f243bc8c56f1d5dadb8628966fe2074d920`.

CiCd `eba76b2d4680eab1a02b7a88df6021a5f4cb3b5f` ran the production scanner
against this commit, with only Works' Git transport directed to the local
candidate. It verified jscpd `5.4.3` signatures and used policy SHA-256
`abd8c8ad7ad31d1b315f6fe73742e410b245016f0b63c6ceabecc8615c41ffd8`.
The seven-module run recorded zero run-level errors and zero observed copies.
The Works row failed with 16 diagnostics across six selected files, down
from 18 on the preceding candidate. Commons, Conversations, McpCli and
PolymorphicSerializations also failed their own discovery rows. Report
SHA-256 `ed30662cdd0bf3a0d842bf8755644787ce299ed64ed87bacf8d1e90d0dd51b61`.
Works diagnostics SHA-256
`5de16938d7b1e1ca002a7ae68ff82ca4e4e89627423d9749bbc306db44186db9`.

| Follow-up source and lines | Remaining scanner diagnostic |
| --- | --- |
| `scripts/prepare-platform-builds.py:25,29,33` | `unresolved computed subprocess env` |
| `scripts/prepare-platform-builds.py:48,50,52,55` | `unresolved computed Python script invocation` |
| `scripts/prepare-platform-builds.py:65` | `unsupported Python access to GITHUB_ENV; coverage unsupported` |
| `scripts/verify-platform-parity-ci.py:44` | `unresolved computed Python script invocation; unsafe or unresolved forwarding` |
| `scripts/verify-platform-parity-ci.py:69` | `unsupported Python process/import API: importlib.util.spec_from_file_location` |
| `scripts/verify-platform-parity-ci.py:118,119` | `unresolved computed Python script invocation` |
| `scripts/verify-platform-parity-ci.py:201` | `unresolved computed subprocess env` |
| `scripts/verify-platform-parity-ci.sh:8` | `unresolved local-script target: ${script%/*}/verify-platform-parity-ci.py` |
| `scripts/verify-source-debug.py:67` | `unresolved computed subprocess cwd` |
| `scripts/verify-source-debug.py:78` | `unresolved computed Python script invocation` |

The scanner prerequisite also needs to account for the bounded Git operations,
the fixed-key GitHub environment append, and the legacy shell entry point's
source-relative anchor. The separate source-identity hook needs proof of the
bounded executor's working directory and argument forwarding, including the
fixed Windows `taskkill` call with a process ID argument. No further narrow
Works-only change was found that keeps those runtime behaviors and entry
points while resolving these observations with the current scanner. Complete
discovery and hosted scanner qualification remain open.

## Candidate refreshed from live Works main

The restricted Works profile fetched live `origin/main` at
`64919bc8481ec6bf084ca31e31bee4477d67cfdd`, tree
`53b7b60fd342e05f7a77b26279f237054beadf17`. The advance from `d55cda77`
changed one documentation file. The seven Works-owned candidate paths above
were reapplied with identical blob IDs to the fresh base. The candidate is
`4f9639fc8cfdc454fdc32fae7a5da2310f2e4646`, tree
`9e227a6352b3e392922ce716eba4b49cb0332fd6`, retained in the Works repository
on local branch `fix/works-parity-discovery-64919bc8`.

The exact base comparison passed for the adopted perimeter, all direct
dependency pins and the delivered workflow. Builds `v6.8.1`'s locked npm
signature verification and commitlint passed on the exact commit message,
SHA-256 `dbc53a26b6ee9b44af9a7c5b136d5c1aa27c51979aa2719f4754cf1127caf46b`.
The standalone candidate checkout matched all 15 direct pins and initialized
zero nested dependencies. Direct pin inventory SHA-256
`ca68e774b8b890893822482b594cb55217a6468b8e115f73d2e4a60d87473b1b`.
The locked CiCd renderer exited 0, output SHA-256
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
All 48 Platform preparation, parity and proof-input fixtures passed, output
SHA-256 `cad1872bddeeb9d2bd612388f64d91e6a6ce16ff8c409ac6c2464ea659b9aca4`.
All 20 source-identity fixtures passed, output SHA-256
`793ecf4273e044411a94db79162af208d1c1ba5abedf4ee840f419d8dcd17777`.
The released standalone `python3 references/Hexalith.Builds/check.py`
exited 0 on this exact candidate. The ownership and action guard passed,
the Release package build reported 18 warnings and zero errors, and
ArchitectureTests, PropertyTests and UnitTests passed 386, 3 and 603 tests
respectively, with zero skips. IntegrationTests remained in the integration
partition with an empty exclusion list. The disposable checkout finished
clean. Checker output SHA-256
`65cef5dd51d07e9041df92eadeaccdd1486a88988633cebcc9d7660c8164fda1`.

The local production controller at `eba76b2d4680eab1a02b7a88df6021a5f4cb3b5f`
used the committed detector policy, SHA-256
`abd8c8ad7ad31d1b315f6fe73742e410b245016f0b63c6ceabecc8615c41ffd8`.
Only the Works Git transport selected local exact commit objects. Both
Node 24.22.1 runs verified jscpd 5.4.3 signatures and reported zero run-level
errors and zero measured copies. The Works row failed discovery on both
revisions.

| Exact Works input | Selected files | Diagnostics | Report SHA-256 |
| --- | ---: | ---: | --- |
| Live `main` base | 6 | 26 | `8a10684efdd42ea4b3796a9181e501fdd3e150de68c464d70f62dcd82e85b177` |
| Local candidate | 6 | 16 | `293a3e2435f41b4e6d0ae1c89a7c55c8417a0b2261be84225d86fabcb2af2c2f` |

The candidate diagnostic array matched the preceding candidate's table
exactly, SHA-256
`5de16938d7b1e1ca002a7ae68ff82ca4e4e89627423d9749bbc306db44186db9`.
CiCd's pinned execution-boundary discovery and hosted qualification are the
remaining scanner prerequisites for publication.

During verification, Works `origin/main` advanced to
`7bd9b18c02985ea5fc320735d16bd6ee0d2f6019`, tree
`e67815dfdb6133773826e26f5c66b834cb75d9d2`. The advance touched
`scripts/measure-projection-delivery.py`, queue measurement tests and story
records. The exact candidate on `64919bc8` remains local. Refresh it from
fresh Works `main` before publication and bind hosted base discovery, local
candidate discovery and the standalone checker to the resulting revisions.

## Literal gitlink discovery qualification

The CiCd scanner now resolves a literal execution target under
`references/Hexalith.Platform/` against the exact Works gitlink. The
controller checks the committed CiCd setup and Works `.gitmodules`
declaration, fetches the exact commit into a private bare object store and
continues static discovery into its reachable regular files. The Works report
row records the acquisition revision in `pinnedSources`.

The positive fixture selects an imported helper at the recorded commit after
the dependency's `main` changes that helper. The negative fixtures cover
computed or overridden paths, traversal before and after acquisition, a wrong
working directory, missing setup or gitlink, a substituted origin, duplicate
declarations, a symlink and a missing script. They use the normal controller,
real Git objects and the signature-verified detector. Both focused tests
passed with output SHA-256
`51770faaf0c19841f6d4014e837fd4b0e8928a5382d8c86b3a203c4774c126ff`.
The full locked scanner suite passed all 134 tests across six disposable
shards with Node 24.22.1 and Python 3.12.

| Shard | Passed tests | Log SHA-256 |
| --- | ---: | --- |
| 0 | 23 | `e6291d9b54b6767b6223c54356073788dac213feff595d575a1b56edb8867260` |
| 1 | 23 | `b2e1fad105e4d430a26a9b11d30dd95786bbb7bd4c85085c7131e06daba1c0f9` |
| 2 | 22 | `67b573356d1a26bfb2831de93ddb55f830b380f34ac0eea4f9dc1ba22216bcf0` |
| 3 | 22 | `6d12cc736cef6de945a3d91d290b78ce7dbb5c9e86eadcdd2977f9cdec4d07b6` |
| 4 | 22 | `6a3c04713e57382213dd4f04c47b6990bbf37a086fb22d945c547b69a631e055` |
| 5 | 22 | `3a62db75731f9659866acac5fb571a3854c9f4a3b64e6fd7934e3fb92e16f700` |

An independent read using the exact Works `main` gitlink and the scanner's
production transport fetched Platform
`99a17baaf6de626d5f59311544a6aa8f9865b695`, tree
`9bf9b18422df53b99e922419becebc1134ac7aed`. It read the five required
Platform entry point blobs listed above. Readback SHA-256
`73efc95fe3199f22b71019c69bc6746f2ff834b37b43ba16547ae30ac6d5b105`.
The locked renderer passed with output SHA-256
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

The restricted Works fetch still selected
`8c40da783cd37d0259cec515690f6c4950d87a6b`, tree
`75206d1d17fdea303148dddd2ee5e7bb15078670`. Its local child
`2a019b1889feb9494fc65b57f9d9fc7a36c3bfbd`, tree
`aa0f5125b791546831dcc59c6ccf63306bcad776`, remains on
`fix/works-parity-discovery-8c40da78`. Both Works fixture suites passed again
in a disposable checkout of that candidate. The Platform suite ran 48 tests
with log SHA-256
`e429bddeed8f3b9673ed3b6cbcb8c04d58a988f1193f6eb75ed8e54e9a85f977`.
The source-identity suite ran 20 tests with log SHA-256
`3ee8628ea25de4cf43b66705c69237484105f777c41d1274c4da7969ad1b7b4c`.

Both exact-input controller runs used disposable CiCd commit
`c0af7c604314a7dd645d592e57bf60eaa7047138`, tree
`7b639c035aae9656f77a66c8bad6aed04f2b6510`. Only Works' Git fetch was
directed to local exact commit objects. The controller used the committed
production policy, SHA-256
`abd8c8ad7ad31d1b315f6fe73742e410b245016f0b63c6ceabecc8615c41ffd8`, and
verified jscpd 5.4.3 signatures. Both recorded zero run-level errors and zero
duplicate findings.

| Scanner revision path | Git blob |
| --- | --- |
| `tools/delivery_runtime.py` | `87fd63944ee432cecaac7b7ff88bed6e5566771c` |
| `tools/scan.py` | `d80d85068f05cc7a3dfc3e9bb74245f05c0aac5a` |
| `tools/scan_discovery.py` | `d4190226719f2ced6304464b65bd4b62b77cf5d7` |
| `tools/tests/test_scan.py` | `2094634ab333c1e1ec06978d09d8af0e4df233ec` |
| `docs/duplicate-scan.md` | `423ecd2669549b80de7ed07c0b55400a5b6bb624` |

| Exact Works input | Selected files | Discovery errors | Report SHA-256 | Diagnostic array SHA-256 |
| --- | ---: | ---: | --- | --- |
| `8c40da783cd37d0259cec515690f6c4950d87a6b` | 6 | 26 | `bc00710876834d83f5eca8dd8a8cd8dea0450f8c4fc5abc5f7682ae72e31ca50` | `4964df529dfed1e66781fd55caded4f2edbe24c30b7a01b390c2640a763b8da8` |
| `2a019b1889feb9494fc65b57f9d9fc7a36c3bfbd` | 6 | 16 | `cae4637d16be1c9904c0fcd6be21492f229b70cad2f1699231f1b1eb6b288f1b` | `5de16938d7b1e1ca002a7ae68ff82ca4e4e89627423d9749bbc306db44186db9` |

Both Works rows lack `pinnedSources`. The actual paths are reached through
the computed preparation clone and sealed export before a literal gitlink
target can be proved. The candidate's source diagnostics still match the
[follow-up table](#follow-up-works-candidate). The exact live `main` diagnostics
are below.

| Works `main` source and lines | Diagnostic |
| --- | --- |
| `scripts/prepare-platform-builds.sh:5` | `unresolved computed operand of unknown command: for` |
| `scripts/prepare-platform-builds.sh:6` | `unresolved computed operand of unknown command: unset` |
| `scripts/prepare-platform-builds.sh:9,12,15,19,23,34,39` | `unsupported shell command substitution` |
| `scripts/prepare-platform-builds.sh:13` | `unsupported shell compound/subshell execution` |
| `scripts/prepare-platform-builds.sh:25` | `unresolved computed operand of unknown command: rm` |
| `scripts/prepare-platform-builds.sh:29,30` | `unresolved computed operand of unknown command: git` |
| `scripts/prepare-platform-builds.sh:31` | `unresolved local-script target: $workspace/Hexalith.Platform/eng/bound_builds.py` |
| `scripts/prepare-platform-builds.sh:43` | `unresolved $GITHUB_ENV write: unsupported destination or producer` |
| `scripts/prepare-platform-builds.sh:44` | `unresolved $GITHUB_ENV write: computed environment name or output` |
| `scripts/verify-platform-parity-ci.py:44` | `unresolved computed Python script invocation; unsafe or unresolved forwarding` |
| `scripts/verify-platform-parity-ci.py:69` | `unsupported Python process/import API: importlib.util.spec_from_file_location` |
| `scripts/verify-platform-parity-ci.py:118,119` | `unresolved computed Python script invocation` |
| `scripts/verify-platform-parity-ci.py:338,341` | `unresolved computed subprocess env` |
| `scripts/verify-platform-parity-ci.sh:4` | `unsupported shell command substitution` |
| `scripts/verify-platform-parity-ci.sh:5` | `unresolved local-script target: $root/scripts/verify-platform-parity-ci.py` |
| `scripts/verify-source-debug.py:67` | `unresolved computed subprocess cwd` |
| `scripts/verify-source-debug.py:78` | `unresolved computed Python script invocation` |

The CiCd scanner prerequisite remains open for the computed materialization
and execution paths in both Works sources and the full reachable Platform
closure. Hosted qualification and the Works discovery PR remain pending.
