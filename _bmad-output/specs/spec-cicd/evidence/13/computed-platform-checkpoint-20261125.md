# Works computed Platform discovery checkpoint

## Current Works and release state

Authenticated Works `main` is `6dc406e07e64e7f4d2b79851b56ba67d25f76300`,
tree `9ce8bbf9565938248e5a1e3568865a88a94f319f`. It already contains
the previous discovery candidate `2a019b1889feb9494fc65b57f9d9fc7a36c3bfbd`
through the `/pushall` merge. There is no newer Works candidate in this
change. The source-identity action, independent 180-minute Platform job,
adopted CI workflow blob `d5314356f9795abccba97c12eafcf8036fd40000`,
and Builds `v6.8.1` gitlink `bf8a28b4bbcec619e8d9764d335f786f2bafb69e`
are present at this base. The original adoption commit
`3996de28eecf32972e8469cbcd7426eaa56f24ab` remains an ancestor and
identifies CiCd registration commit `a7aab9c52d382202d071fc2b208ab3f4303a26e0`.
That registration contained the Works gitlink, setup and render at Builds
`v6.4.2`. The current Works tree contains zero `NuGetAuditSuppress` items,
so the migration required no transfer to Builds.
[First delivery](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/44616302631)

The released standalone Builds checker exited 0 on an exact clean Works
checkout with 15 matching direct gitlinks and zero nested checkouts. It used
the delivered Builds pin above and the published producer `v6.6.2` at
`2d9ef8b454ff897daca0149f3549844f584b634a`. The ownership and action guard,
Release build, and 386 architecture, 3 property and 603 unit tests passed
with zero skips. IntegrationTests remained in the integration partition.
Direct gitlink inventory SHA-256
`ca68e774b8b890893822482b594cb55217a6468b8e115f73d2e4a60d87473b1b`.
Checker output SHA-256
`2923ec10235f8dce5c88da0fae087282fdf9ed71ef173b95194637f2bedc729a`.

The command-local maintainer readback authenticated as account `6775094`
on Works repository `1264171182`, with both token overrides unset. It
confirmed immutable releases, enabled publishing, main-only
`hexalith-release` and the original publisher secret names. Works is
excluded from all eight legacy GitHub grants. EventStore, Memories, Parties
and Tenants remain selected by both legacy Zot grants. The projected
readback SHA-256 is
`84833359a0335a251716967ec82a7130fb63a5ac52f2d87867fc51cbe6f8dd92`.
The App selects all repositories. The `main` and `v*` rulesets remain
active. Repository and organization retention are 90 days. The shared
pull pair remains granted to Works in both Actions and Dependabot, as
does the selected `HEXALITH_NUGET_USER` Actions variable. The NuGet
provisioning receipt shows active policy `27451` for `release.yml` in
`hexalith-release`, scoped to `Hexalith.Works*`, was added alongside
`20087`. The authenticated cleanup readback shows `20087` removed and
`27451` retained.
[NuGet provisioning](nuget-policy-verification.json) ·
[NuGet cleanup](nuget-cleanup-verify-cleanup.json)

The authenticated Zot deployment readback reports generation 26 and one
ready replica. ConfigMap version `49008107` still grants the dedicated
Works publisher read, create and update on `works` and `works/**` and
retains the legacy owner's global write grant. Projected ACL SHA-256
`5592e37dc538e0c8404ef3ddc3aabcf42736d15feefb0fc2056c027687c65d11`.
The maintainer still owns continuity and scoped replacement proof for those
consumers, retirement and effective write loss for legacy Zot key
`099585e7-fd9e-4aac-9042-56426c1add7b`, and the disposition of the
credential behind the historical `NUGET_API_KEY` grant.
[Prior authenticated credential readbacks](hosted-ci-triage-20261124.md#build-auto-maintainer-and-runner-recheck)

All four selected repositories still reference the legacy Zot pair in
their live release paths. Current source confirms the handoff scope.

| Repository | Main revision | Release workflow |
| --- | --- | --- |
| EventStore | `ae1143bdc831ca6f2cf61726648a3efe946d68a2` | `.github/workflows/release.yml:238` |
| Memories | `45e165d88d358c1349dbcb772e2e2a8a0f2218ce` | `.github/workflows/release.yml:142` |
| Parties | `2851be5c79d4ccc9d98858fbeea96e11fc4ab289` | `.github/workflows/release.yml:359` |
| Tenants | `d58f24d8d6909d7498ecec34955e7f17720c1ba0` | `.github/workflows/release.yml:594` |

On Works `6dc406e07e64e7f4d2b79851b56ba67d25f76300`, run
`45575363008`, attempt 1, passed shared CI. Platform parity was in progress
at readback. The preceding commit `00ecd1338b8ba1de2b8b44193d65a5668b8b4327`
passed shared CI and failed Platform parity in run `45566346523`,
attempt 2. Authenticated artifact `15002743510` matched GitHub SHA-256
`88574765b7321c56e528fd81c53a40f6b35e3753cfd63cd7f2ece97b833313aa`.
Its ledger SHA-256
`552fbe359a0bd2867c7496656d9390c6c1fd5dbe1d572a83d8d3eb192aeef864`
reports `platform-projection` failing. The xUnit XML SHA-256
`5f1f553a2b2a3d2ab254d7f00a91396b9c7a80abe8fd70b3893658488cc2cf2f`
identifies `WorksPlatformProjectionPipelineSmokeTests.ActualPlatformSharedRebuildAndConcurrentCatchUpPreserveCompleteFamily`
and reports a runtime failure after startup and readiness passed. Its
inner `TaskCanceledException` originates at
`WorksPlatformProjectionChecks.VerifyConcurrentDeliveryAsync`, line 355
of `tests/Hexalith.Works.IntegrationTests/WorksPlatformProjectionChecks.cs`
at that revision. Works and Platform own the root-cause investigation. Builds still owns the
separate recurring Stage 4 scheduler bind failure on `50006/tcp`.
[Current CI run](https://github.com/Hexalith/Hexalith.Works/actions/runs/45575363008) ·
[Prior parity artifact](https://github.com/Hexalith/Hexalith.Works/actions/runs/45566346523/artifacts/15002743510) ·
[Builds handoff](hosted-ci-triage-20261124.md#build-auto-maintainer-and-runner-recheck)

## Computed path discovery

The scan controller now follows the verified Works action's computed
Platform checkout, fixed snapshot import and sealed export. It binds the
registration's workflow, action and two materializer blobs by SHA-256, then
uses the normal committed setup and `.gitmodules` checks to acquire the
exact Platform gitlink. Ordinary analysis follows the four entry points
into the dependency. Changed source inputs, an unproved pin, an unsafe path
or downstream computed execution remains a failure.

The normal local controller with production transport ran at disposable
commit `cc1a4ec529224c92331bd58f40cab86b6f4678ff`, tree
`71fc6573ad635130b01ebecb1a4011bc2ee4dd9e`. The `tools/scan.py` and
`tools/scan_discovery.py` blobs were
`8f7a6811a1a297b51452b8b4d508397df10b700f` and
`3611621d5dac8cea0e443df61416d374bfb99660`. The production detector
policy SHA-256 was
`abd8c8ad7ad31d1b315f6fe73742e410b245016f0b63c6ceabecc8615c41ffd8`.
The controller verified jscpd 5.4.3 signatures and reported zero run-level
errors and zero duplicate findings involving Works. The Works row selected
43 source files and recorded Platform
`99a17baaf6de626d5f59311544a6aa8f9865b695`, tree
`9bf9b18422df53b99e922419becebc1134ac7aed`. The Works row failed on
143 discovery diagnostics. Report SHA-256
`a76e37d76d4b24757b894011134092e1cb2536a1a773f64b1bc831126d20229c`.
There was no manual seeding of the Platform scripts.

The scanner tests followed a committed launcher to its pinned imported
helper despite a change on the dependency's live branch. They rejected a
changed materializer, substituted gitlink, traversing target, and an
unresolved computed executable in a reachable script. The focused result
SHA-256 was
`d02293303a6d096edca14e3a92ea7fea830eb4775df757dd66f4c1883ba51901`.
The final fixture blob is `0db8450521c523fe05dea9e081eefe5eb42d07ca`.
All 136 scanner tests passed in six disposable shards with Node 24.22.1.
CiCd's locked renderer check exited 0.

| Shard | Tests | Output SHA-256 |
| --- | ---: | --- |
| 0 | 23 | `4819e2148995cba52dc6c7e21b12075b2d57e80c48315c141ba5984f1e94eb94` |
| 1 | 23 | `1600a070448c22f00bdcf3a04e44a60ddfef6c2b587dc494d79cf7a858884148` |
| 2 | 23 | `2fb84f456d2b0921e12627d478259c6a3185eef25cc4feeaa5cefa28fcf0b516` |
| 3 | 23 | `f37189f1330199bc930b8f6b91e00fab6e42c57509b255e05717c2c710b6a4a9` |
| 4 | 22 | `a4918f9f8c24c7b8443692558e18c6a90f8323e729cbdd9d24b87fc87b3c1e78` |
| 5 | 22 | `d9a5632f996ad4d9f739da7f1433d348f3f3134527cb241b60d59a9e2204eedb` |

## Remaining discovery handoff

All diagnostics have the prefix `local-script discovery: `. At the
authenticated Works revision above, CiCd owns proof of the computed
preparation and export operations and the two owners must coordinate any
behavior-preserving Works source changes.

| Works source | Exact diagnostic and lines |
| --- | --- |
| `scripts/prepare-platform-builds.py` | `unresolved computed subprocess env` at 25, 29, 33. `unresolved computed Python script invocation` at 48, 50, 52, 55. `unsupported Python access to GITHUB_ENV; coverage unsupported` at 65. |
| `scripts/verify-platform-parity-ci.py` | `unresolved computed Python script invocation; unsafe or unresolved forwarding` at 44. `unsupported Python process/import API: importlib.util.spec_from_file_location` at 69. `unresolved computed Python script invocation` at 118, 119. `unresolved computed subprocess env` at 201. |
| `scripts/verify-source-debug.py` | `unresolved computed subprocess cwd` at 67. `unresolved computed Python script invocation` at 78. |

The remaining 128 diagnostics are in Platform at the pinned source above.
Platform owns the verifier and test implementations. CiCd owns scanner
support for execution forms that can be proved from their committed inputs.
Paths below are relative to `references/Hexalith.Platform/`.

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
| `eng/test_works_host_snapshot.py` | `unresolved computed Python script invocation; unsafe or unresolved forwarding` at 57. `unresolved computed Python script invocation` at 114, 132. |
| `eng/test_works_toolchain.py` | `unresolved computed Python script invocation` at 38. `unsupported reflective use of a process/import API: subprocess.check_output` at 133. |
| `eng/test_works_verifier_command.py` | `unresolved subprocess positional/options expansion` at 234. `unresolved computed Python script invocation` at 305. |
| `eng/verify-agents-host.sh` | `unsupported shell compound/subshell execution` at 11, 15, 17, 18, 22, 23, 27, 28, 33, 34, 39, 40, 45, 49, 50, 53, 54, 55, 58, 63, 83, 87, 88, 90, 93, 104, 106. `unsupported shell command substitution` at 5, 59, 64, 68, 73, 75, 77, 80. `unresolved computed operand of unknown command: case` at 16, 48, 52, 57, 62. `unresolved computed command: $BUILDS_ROOT` at 67. `unresolved local-script target: $ROOT` at 70. `unresolved computed operand of unknown command: rm` at 74. `unsupported stdin-fed interpreter; coverage unsupported` at 89. `unresolved local-script target: $ROOT/eng/verify-platform-pins.py` at 91. `unresolved computed operand of unknown command: -d` at 98. `unresolved local-script target: $ROOT/eng/ext-host-1/verify_full.py` at 108. `unresolved computed operand of unknown command: dotnet` at 113. |
| `eng/verify_works_host.py` | `unresolved computed Python script invocation` at 1029, 1149. `unresolved computed Python script invocation; unsafe or unresolved forwarding` at 1049. |
| `eng/works_host_snapshot.py` | `unresolved computed Python script invocation; unsafe or unresolved forwarding` at 59. |
| `eng/works_toolchain.py` | `unresolved computed Python script invocation` at 77. |
| `eng/works_verifier_command.py` | `unresolved computed subprocess cwd` at 87. |

The hosted scan for controller `191369dfdd7b385856f40e4d373ce872b653ccf8`
was run `45404275797`, attempt 1. Authenticated artifact `14924224437`
matched archive SHA-256
`9ec2857db2830cf006f5034b026f4d4f2febfc740a16ef1eb3691254acef5b81`.
Report SHA-256
`a8c032fe58ed005c5cc6460cb3286d40644ab54e412d41fac89c3687e6b6a212`.
It used the same production policy and failed discovery at Works revision
`ae9dbe8eccd58ff1e9c0276cc17ed0a2e70d03bf` with 23 diagnostics and zero
run-level errors. Hosted qualification, complete Works
discovery and AD-21 cleanup remain open. With those and the exact-source CI
result outstanding, the checkpoint gates further Works publication and
acceptance Nightly. [Hosted scan artifact](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45404275797/artifacts/14924224437)

The latest completed scheduled Nightly `45394054346`, attempt 1, was
authenticated again. Its acceptance checker exited 1 with report SHA-256
`eecd984497fdc7d918fc319debadd89d457ad992968973c418a550065f4ab638`.
Both CodeQL jobs passed. Release and scan failed on the earlier Works
dispatch commit `ae9dbe8eccd58ff1e9c0276cc17ed0a2e70d03bf`.
[Scheduled Nightly](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45394054346)
