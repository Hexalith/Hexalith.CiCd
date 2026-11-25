# Works scanner and CI readback

## Hosted CI on the current Works base

The CiCd-agent branch read and the restricted Works API read both returned
`8c40da783cd37d0259cec515690f6c4950d87a6b`, tree
`75206d1d17fdea303148dddd2ee5e7bb15078670`. The delivered Builds pin is
immutable `v6.8.1`, commit `bf8a28b4bbcec619e8d9764d335f786f2bafb69e`.
The shared Build and tests job succeeded in run `45488107270`, attempt 2.
Platform parity failed in the custom action after its shared Linux preparation
passed. In attempt 1, Builds had failed while binding the Dapr scheduler port
`50006/tcp`. The recurrence investigation remains with Builds, including
identifying the socket owner on the affected hosted runner. [Shared job](https://github.com/Hexalith/Hexalith.Works/actions/runs/45488107270/job/138843136671) · [Platform job](https://github.com/Hexalith/Hexalith.Works/actions/runs/45488107270/job/138848044459) · [Builds triage](hosted-ci-triage-20261124.md#build-auto-maintainer-and-runner-recheck)

The authenticated attempt 2 Platform artifact `14975621829` matched GitHub's
archive SHA-256
`368e383fb2fd1f6e4eb58d01cbc29e66e4111d93fc38f598f25d72b976a5ec28`.
Its ledger, SHA-256
`38eb9987b37d598baf346f6bd5f9e28aecb92c1005d87f801cc8c511ac0c6dbb`,
records the sealed Platform export at
`99a17baaf6de626d5f59311544a6aa8f9865b695` and fails `platform-recovery`.
The Works test
`WorksSdkRecoveryPipelineSmokeTests.SdkRemindersAndCascadeConvergeThroughPersistedReceiptsAcrossRestart`
failed at startup because the Works resource never became healthy within the
startup budget (`State=Running; Health=Degraded; ExitCode=none`). The earlier
run reached the test's wait for a committed cascade target. The Works and
Platform owners still need to establish the root cause. The log SHA-256 is
`9154fede3731918d9328263acfd73ca631d0537372ed37ed2d99d948b156c03c`.
The xUnit XML SHA-256 is
`53c856853f2c05a4ed6e14ffeee7d5718831ebf16de79dc32ec83d640f7c4b8e`.
Both hosted jobs need to pass on the same base and Builds pin.
[Platform artifact](https://github.com/Hexalith/Hexalith.Works/actions/runs/45488107270/artifacts/14975621829)

## Scanner increment

The controller can acquire a literal direct dependency from the exact committed
gitlink after validating the CiCd setup and the module's `.gitmodules`.
It reads regular blobs in a private bare object store and records the pinned
revision in the module row. Discovery recognizes standalone, source-relative
Bash launchers, including the Works wrappers and Platform's Python verifier
launcher. A signature-verified detector fixture follows a launcher to its
imported helper at the gitlink revision after the dependency's live branch
changes. Negative fixtures reject unresolved and missing targets, traversal,
missing or duplicate declarations, a substituted origin, missing setup
authorization, a missing gitlink and a symlink. Both focused fixtures and the
locked renderer passed.

All 134 scanner tests passed in six disposable shards with Python 3.12 and
Node 24.22.1.

| Shard | Tests | Log SHA-256 |
| --- | ---: | --- |
| 0 | 23 | `7f79550bd57d68f3084f2412cc8557ea6fc149a30c3de4d9e3f26813d9cd07cd` |
| 1 | 23 | `6b4fb9a56e335576dc9a1a9f4fc918c6f210f600451f04fe95f373e280094722` |
| 2 | 22 | `5b0581071ab829862edd989de921195cde5cb7645f098a5cd3eed916dac569fb` |
| 3 | 22 | `05ee650c81189fcc77d9f23d657fbdc32bd8fa3952d4552c2add451fae2c98a2` |
| 4 | 22 | `af43a876d200b00170ed7e08b48ff9e38f1b8481b44644a64e934eac633d7b6e` |
| 5 | 22 | `cb9b28c859700779270212757b0220090462822f69b092e0194dbf7e13b56491` |

The exact-input controller probe ran with disposable CiCd revision
`c64949fb2a48ab0b056e8d9abb5c457c141bc9af`, tree
`46076eeade64e450610ebb10005458fef6e4d52a`. The production policy SHA-256
was `abd8c8ad7ad31d1b315f6fe73742e410b245016f0b63c6ceabecc8615c41ffd8`.
Both scans verified jscpd 5.4.3 signatures. The base run used the normal
production transport. The candidate run changed only the Works fetch to
select its exact local commit. Both scans reported zero run-level errors,
zero duplicate findings and six selected Works files. Both Works rows
failed discovery.

| Controller source | Git blob |
| --- | --- |
| `tools/delivery_runtime.py` | `f49d1429d6f5afea9f46c427976978fc0dd7b4c4` |
| `tools/scan.py` | `e0c52e1e904c1ddf8240eb3eae6ac2e3159abc92` |
| `tools/scan_discovery.py` | `b46f87e29f1524412df3282c55b441755026afe8` |
| `tools/tests/test_scan.py` | `dee6ccbf7cf97a656eee236ce1dd31915b046c06` |

| Exact Works input | Works diagnostics | Report SHA-256 |
| --- | ---: | --- |
| `8c40da783cd37d0259cec515690f6c4950d87a6b` | 24 | `f87175762f266f77f91ab910febf35e2c34da364f91d98ea34dae861e449df45` |
| `2a019b1889feb9494fc65b57f9d9fc7a36c3bfbd` | 15 | `b68b3336ea9d4ee435c6c47a86d170509deb8e23569d11dee7713e9e02ad2de4` |

The remaining Works diagnostics match the earlier tables for [the base and
candidate](platform-scanner-prerequisite.md#literal-gitlink-discovery-qualification)
after resolving the coordinator wrapper at base lines 4–5 and candidate
line 8. On the base, the preparation script still needs proof for the shell
substitutions, detached clone and environment export. On the candidate, the
equivalent Python preparation still needs proof for computed subprocess
environment, the clone and child argv, and the fixed-key environment append.
On both, the coordinator still needs proof for the fixed import, clone,
sealed export and forwarded invocation. Both inputs still fail source-debug
cwd and process resolution.

An independent diagnostic probe used the same discovery code and the
production Git transport to fetch the exact Platform gitlink for each Works
input. The fetched tree was `9bf9b18422df53b99e922419becebc1134ac7aed`.
The probe supplied [five verified entry-point blobs](platform-scanner-prerequisite.md#cicd-scanner-prerequisite)
directly to discovery. This reached 43 files on each Works input and
identified 128 Platform diagnostics on each. The shared Platform diagnostic
array SHA-256 is
`a0a2c06eb4f4812a5c77ae738dd4aa35cfa5d4220e9289d7325b5bbb148b2e64`.
The production controller still needs to reach these scripts from the
Works actions through the computed checkout and export.

| Platform source at the pinned revision | Remaining diagnostics |
| --- | --- |
| `eng/bound_builds.py` | Computed subprocess cwd at 31, 41, 46. Computed subprocess env at 71. |
| `eng/builds_tool_lock.py` | Computed Python invocation at 104. |
| `eng/builds_tuple.py` | Subprocess positional or options expansion at 72, 86, 93. |
| `eng/current_catalog_view.py` | Computed subprocess cwd at 126. |
| `eng/ext-host-1/prepare_acceptance.py` | Unsafe or unresolved forwarding at 114. Python search-path mutation at 130, 148, 216. |
| `eng/ext-host-1/test_prepare_acceptance.py` | Computed Python invocation at 12. Computed subprocess env at 17. |
| `eng/ext-host-1/test_verify_full.py` | Python search-path mutation at 124. Computed subprocess env at 164. Computed Python invocation at 326, 327. Computed subprocess cwd at 724, 730, 741, 753, 766, 770. |
| `eng/ext-host-1/verify_full.py` | Computed subprocess cwd at 103, 361, 374, 385. Python search-path mutation at 466. |
| `eng/ext-secrets-1/local-transport/run.py` | Computed subprocess executable at 47. |
| `eng/isolated_daprd.py` | Reflective use of `os.execv` at 50. |
| `eng/prepare_builds_artifacts.py` | Computed subprocess cwd at 22. Computed Python invocation at 122. |
| `eng/retained_works_host.py` | Computed Python invocation at 30. |
| `eng/test-local-dapr-security.py` | Computed Python invocation at 25, 26, 146, 227, 229, 230, 231. Unsafe or unresolved forwarding at 98. Computed subprocess env at 162. |
| `eng/test_bound_builds.py` | Computed subprocess env at 19. Computed Python invocation at 104, 109, 151. |
| `eng/test_current_catalog_view.py` | Computed subprocess cwd at 44. |
| `eng/test_isolated_daprd.py` | Unsafe or unresolved forwarding at 78. |
| `eng/test_local_dapr_security_cleanup.py` | Unsupported `compile` and `exec` at 34. |
| `eng/test_verify_platform_pins.py` | Unsafe or unresolved forwarding at 61, 118. Computed Python invocation at 71, 105, 135, 205, 226, 252, 264. Computed subprocess cwd at 159. |
| `eng/test_verify_works_host.py` | Computed subprocess env at 731, 756, 766. Computed subprocess cwd at 748, 867. |
| `eng/test_works_host_snapshot.py` | Unsafe or unresolved forwarding at 57. Computed Python invocation at 114, 132. |
| `eng/test_works_toolchain.py` | Computed Python invocation at 38. Reflective use of `subprocess.check_output` at 133. |
| `eng/test_works_verifier_command.py` | Subprocess positional or options expansion at 234. Computed Python invocation at 305. |
| `eng/verify-agents-host.sh` | Unsupported shell compound or subshell execution at 11, 15, 17, 18, 22, 23, 27, 28, 33, 34, 39, 40, 45, 49, 50, 53, 54, 55, 58, 63, 83, 87, 88, 90, 93, 104, 106. Command substitutions at 5, 59, 64, 68, 73, 75, 77, 80. Computed `case` at 16, 48, 52, 57, 62. Computed command `$BUILDS_ROOT` at 67. Unresolved `$ROOT` at 70. Computed `rm` at 74. Stdin-fed interpreter at 89. Unresolved `$ROOT/eng/verify-platform-pins.py` at 91. Computed `-d` at 98. Unresolved `$ROOT/eng/ext-host-1/verify_full.py` at 108. Computed `dotnet` at 113. |
| `eng/verify_works_host.py` | Computed Python invocation at 1029, 1149. Unsafe or unresolved forwarding at 1049. |
| `eng/works_host_snapshot.py` | Unsafe or unresolved forwarding at 59. |
| `eng/works_toolchain.py` | Computed Python invocation at 77. |
| `eng/works_verifier_command.py` | Computed subprocess cwd at 87. |

The latest completed normal hosted CiCd scan readback was run `45404275797`,
attempt 1, on controller `191369dfdd7b385856f40e4d373ce872b653ccf8`.
Hosted qualification of the scanner increment and complete discovery of the
computed paths remain open with CiCd. The candidate stays local on
`fix/works-parity-discovery-8c40da78`. Its exact standalone Builds checker
passed in the previous verification. [Hosted scan](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45404275797) · [Exact candidate verification](hosted-ci-triage-20261124.md#build-auto-maintainer-and-runner-recheck)

## Independent verification

The command-local GitHub maintainer profile authenticated as account `6775094`
against Works repository `1264171182`. Both token overrides were unset. The
live `hexalith-release` environment allows only `main` and holds the two
original dedicated publisher secret names. Immutable releases and publishing
are enabled. Both exact rulesets are active with empty bypass lists. Default
CodeQL setup is unconfigured, Dependabot security updates are disabled, push
protection is enabled, and repository and organization retention are 90 days.
There are zero draft releases. The CiCd App selects all repositories. Works
is absent from all eight legacy secret selections. The Zot key selection
still covers EventStore, Memories, Parties and Tenants. Projected ruleset,
draft and organization readback SHA-256
`1da8820cb92d3b0c98c9f64dfa85a4b77c1d116f4e6c8e85291354c443f0cca1`.

Zot deployment generation `26` has one ready replica. ConfigMap version
`49008107` grants the Works publisher read, create and update on `works`
and `works/**`. The legacy identity still has global create, update and
delete permissions. Projected ACL SHA-256
`8211c64da0b0987ff8f9714699d829845d82b9ddd0524e064bea3cc39baebf7b`.
The prior authenticated NuGet policy readback shows `27451` active for
`Hexalith.Works*` and `20087` removed. The provisioning receipt shows they
coexisted before cutover. The maintainer still needs to prove the historical
`NUGET_API_KEY` can no longer publish Works IDs and qualify the remaining
Zot consumers before retiring the shared key.
[NuGet provisioning](nuget-policy-verification.json) · [NuGet cleanup](nuget-cleanup-verify-cleanup.json) · [Legacy key readback](hosted-ci-triage-20261124.md#build-auto-maintainer-and-runner-recheck)

The first delivery is an ancestor of current Works `main`. Current CiCd
`main` and its accepted Works delivery ref agree on setup, render, perimeter
and `builds-version`. The old root npm files and `.husky/` are absent.
XML inventories of the preparation base, preparation commit and current
`main` found zero `NuGetAuditSuppress` elements across 23, 23 and 24 files,
respectively. Current inventory SHA-256
`696f6ce65f522ec4b234a2510594c82e42c67657ac41e444874920efcf20f7dd`.
The historical `Directory.Build.props` mention is an XML comment.
[Original delivery](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/44616302631)

The attempt 2 xUnit stack locates the Platform failure at the restart on
`WorksSdkRecoveryPipelineSmokeTests.cs:546`. The health diagnostic says
`works/ready=Degraded` because the SDK reports unresolved or incomplete
recovery. The same log records tenant discovery admission exhaustion and a
timeout. Separate route-catalog readiness and EventStore admin metadata
warnings appear in the artifact. The artifact does not establish their causal
relationship to the restart failure. Works and Platform own the exact-source
recovery investigation. Builds owns the earlier scheduler port conflict.
[Works restart source](https://github.com/Hexalith/Hexalith.Works/blob/8c40da783cd37d0259cec515690f6c4950d87a6b/tests/Hexalith.Works.IntegrationTests/WorksSdkRecoveryPipelineSmokeTests.cs#L546) · [Parity artifact](https://github.com/Hexalith/Hexalith.Works/actions/runs/45488107270/artifacts/14975621829)

Python source-relative parent traversal now stops at the acquired dependency
root. The focused regression passed with output SHA-256
`95f819596021ec861c8259c0f54183b7b0457c3eabbc020c40c19c87cbe289de`.
All 135 tests passed in six disposable shards on the final scanner and
fixture sources. The fixture blob is `9fd799fa05d6ddc5811ca623c60f2da87d9a9350`.

| Shard | Tests | Log SHA-256 |
| --- | ---: | --- |
| 0 | 23 | `7bcf881517b8ced51829dd02bcc037269d2d7916fb98837e4d146942ddf0a1fd` |
| 1 | 23 | `339db6149e041ad4536e6b092141f992c8244e6743cf1391833d051b6561e4b8` |
| 2 | 23 | `ff82279d26cef95093664b145cbb377b9afc5b9d975b0fb21a04a5fe247fb54d` |
| 3 | 22 | `f57904751b32327100877179ea66e335b4308657317f0a3c24be89944c370cad` |
| 4 | 22 | `3e147822a77e4dab02905522232bd8b9670fee88ca265ee5af62f9ac6e77faf9` |
| 5 | 22 | `7fc167eee72f137427c15e19fe4d18514ee115fe3ff4282610953c929b3d0919` |

The production controller probe at disposable commit
`2c5dcfb61bc92ce5563bec825c6e2b05f59beb5e`, tree
`070d7b0371ec2a50bb2b7c6200ff819aebeaf3e4`, used scanner blob
`a00b6395e84faa01dee8304b5f7fa22441e6f926` and verified the production
policy and detector signatures above. It independently reproduced six
selected Works files, zero run-level errors and zero duplicate findings on
both inputs. Works discovery still failed. Neither row recorded a Platform
pin because the computed checkout and sealed export remain unresolved.

| Exact Works input | Discovery errors | Report SHA-256 |
| --- | ---: | --- |
| `8c40da783cd37d0259cec515690f6c4950d87a6b` | 24 | `650636081d036b80d42224accfd00126b1f261e657d4928f6983bb0eea2bc01d` |
| `2a019b1889feb9494fc65b57f9d9fc7a36c3bfbd` | 15 | `bb3f65ea38211c812f6a628a410718fb86eb32e6ab49e4323c78bf11f225570c` |

The standalone Builds checker exited 0 on exact candidate
`2a019b1889feb9494fc65b57f9d9fc7a36c3bfbd` with authenticated `origin/main`
`8c40da783cd37d0259cec515690f6c4950d87a6b`. The checkout matched all 15
direct gitlinks and used the exact delivered `v6.8.1` and producer `v6.6.2`
tags. The guard passed, Release compilation had 18 warnings and zero errors,
and all 386 architecture, 3 property and 603 unit tests passed with zero
skips. IntegrationTests was in the integration partition. The checkout
finished clean. Gitlink inventory SHA-256
`990c1e89a0a2a1c9b2cff16acf263842200a7af1a1295fccd6fddd0874a1014f`.
Checker output SHA-256
`6682761bb1caec3b2db203b6dcd36a23782890c1940899d1037df90980ed75d7`.

The locked renderer check exited 0, with output SHA-256
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
The most recent completed scheduled Nightly still fails Works acceptance.
`python3 tools/nightly_acceptance.py --run 45394054346 --module Hexalith.Works`
exited 1, output SHA-256
`eecd984497fdc7d918fc319debadd89d457ad992968973c418a550065f4ab638`.
Both CodeQL jobs passed. Release and scan acceptance failed on the prior
dispatch commit `ae9dbe8eccd58ff1e9c0276cc17ed0a2e70d03bf`.
[Scheduled Nightly](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45394054346)
