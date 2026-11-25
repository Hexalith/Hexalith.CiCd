# Works AD-21 and hosted readback, 2026-11-25

## Adoption and publishing

The command-local maintainer profile authenticated as account `6775094`
against `Hexalith/Hexalith.Works` repository `1264171182`. Both token
overrides were unset. The active CiCd App `179966090` selects all
repositories. Rulesets `27474176` and `27474178` have the required refs
and rules, active enforcement and empty bypass lists. Immutable releases and
push protection are enabled. The release environment holds the two registry
secret names and permits only `main`. The publish variable is `true`.
Repository and organization retention are 90 days. The organization defaults
workflows to `read`, and Works requires approval for all external fork
contributors. Default code scanning is unconfigured. Dependabot security
updates are disabled. The release inventory has two published releases and
zero drafts. Four analyses from the retired CodeQL caller remain historical.
[Works settings](https://github.com/Hexalith/Hexalith.Works/settings) ·
[Release environment](https://github.com/Hexalith/Hexalith.Works/settings/environments)

Works is excluded from all eight legacy organization Actions secret selections.
It retains the shared registry pull pair in Actions and Dependabot and the
`HEXALITH_NUGET_USER` Actions variable. The native NuGet policy page showed
scoped policy `27451` for `Hexalith.Works*` and the absence of legacy
policy `20087`. The projected readback SHA-256 is
`f114478e00c5fbcb401be0fbc349ad144671407f341fb206d2fee7193465bd68`.
The provisioning receipt binds the scoped policy to `release.yml` and
`hexalith-release` and verifies it was added alongside `20087`.
The maintainer still needs to bind the historical `NUGET_API_KEY` grant
to the underlying credential and prove it cannot publish Works packages.
[Trusted publishing provisioning](nuget-policy-verification.json) ·
[Previous API key readback](reconciliation-20261124.md#maintainer-readbacks)

Zot ConfigMap `49008107` and deployment generation 26 with one ready
replica confirm `hexalith-works-publish` retains read, create and update
on `works` and `works/**`. The legacy owner still has global write and
write on both Works patterns. Both legacy organization Zot grants select
EventStore, Memories, Parties and Tenants. The maintainer owns qualification
of scoped replacements for those consumers and proof of the legacy key's
retirement and loss of Works write access.
[Dedicated publisher provisioning](provision-registry.json) ·
[Legacy key and consumers](computed-platform-checkpoint-20261125.md#current-works-and-release-state)

The original CiCd registration `a7aab9c52d382202d071fc2b208ab3f4303a26e0`
bound Works gitlink `4053907d5764bc8833c95dd79ea337bc8faba159`,
setup blob `651fd7903783d398a4520cbcfaedbb2ed9c60599` and perimeter blob
`74bdccd9b4d0266d5d695511a3402241eda750e1` at Builds `v6.4.2`.
Delivery adopted it at Works commit `3996de28eecf32972e8469cbcd7426eaa56f24ab`.
The initial Works `main` readback at `f934f53682fb6f8250370289103a19df65e9480e`
and tree `e050be7214752cb0113586fdf7ce60752b3ef6a6` retains the two
registered product actions and the Builds `v6.8.1` gitlink
`bf8a28b4bbcec619e8d9764d335f786f2bafb69e` from immutable release
`456644518`. Its CI configuration, Dependabot configuration and both
workflow blobs match the rendered bytes. The current source has no
`NuGetAuditSuppress` item. The lone textual occurrence in
`Directory.Build.props` is a comment. The tool-only npm files and
`.husky/` remain absent. No audit waiver transfer was needed.
[First delivery](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/44616302631)
· [Immutable Builds tag](https://github.com/Hexalith/Hexalith.Builds/releases/tag/v6.8.1)

## Exact-source CI and scan

Works run `45581571905`, attempt 1, used the initial `main` above.
Stage 3 reported 385 passing architecture tests and one failure, without
skips. The architecture test at
`tests/Hexalith.Works.ArchitectureTests/FitnessTests/EventStoreApiSurfaceCharacterizationTests.cs:115`
reported that its two current-source markers differed from the consumed
EventStore gitlink `70e1f765d21ec93f1461c21e4a460b4b14dc7b66`.
The independent Platform job was skipped. Job log SHA-256 is
`29046d90c4a5012f840f9303037dedf38c360013917a00cfbec9d5989547007c`.
The generic dependency advancement `4cc94085203110b3fe99584480ef33ae3af5bacc`
changed both governed gitlinks. The reviewed manifest still binds EventStore
`f2ade96970f929dd96e8865075339954233e61ed` and PolymorphicSerializations
`94ae242d609d0126735a8ab387960ec41265a4f7`. The separate Works correction
restores those exact pins and preserves the existing documentation markers,
source-identity hook and Release package versions.
[Current shared job](https://github.com/Hexalith/Hexalith.Works/actions/runs/45581571905/job/139092641327)

The correction `4c96591bf94f2345f4d2b7fa8f5077001182054e`, tree
`61ec491630ae75911a5870b454e299942fe8ae52`, changes only those two
gitlinks. The released commit validator accepted its message, and the
source-identity preflight exited 0. Its report SHA-256 is
`33b3205c8b1468ed72430bf2aba7a797f3d5e8bb7a221bdd7a818cda81e44fe3`.
The first standalone job initialized all 15 exact direct gitlinks but
fetched only the delivered Builds tag. The checker exited 1 during
producer preparation, reporting `git --literal-pathspecs failed (128)`.
Log SHA-256 was
`67b6d5ef233730471f9e38e539897304e8f38d6235b534327e5f16b921ca3fa2`.
The retry verified Builds `v6.6.2` alongside `v6.8.1`. The checker
exited 0 after the guard, Release build and 386 architecture, 3 property and
603 unit tests passed with zero skips. Log SHA-256 was
`a2b99e98cbb8996f1a9070f4f1616b928f8cbba7642e63fc2b1cb6065a2f8636`.
The Works module-agent credential published that exact source as PR 26.
Authenticated readback confirmed the exact base and head and two modified
gitlinks. In CI run `45590548959`, attempt 1, hosted job `139123325353`
passed shared Stages 1–4 and the source-identity hook. Source-pairs artifact
`15011586948` matched GitHub's ZIP SHA-256
`edcf0819a88fd46d48bf08c036fe763eb183ba507e145388718c8e26233c8fca`.
Its passing report SHA-256
`850f96c87ded4ab65209a8046867a89968889536dbbf3d138c92c7ed30336fa2`
records the two reviewed revisions and Release package versions.
The PR merge commit `5639dcc686e1d682187231d6f22e3e9b799b1862` had the
same tree as the candidate and parents equal to the recorded base and head.
[Works PR 26](https://github.com/Hexalith/Hexalith.Works/pull/26) ·
[PR CI](https://github.com/Hexalith/Hexalith.Works/actions/runs/45590548959)

Independent Platform parity job `139132633108` failed while preparing
the published Builds artifacts at Platform pin
`616e27789f935ebb7f7f33406150ecf2dc9913a2`. The tuple at
`eng/builds-tuple.json` names tag `v6.7.0`, resolving to
`763fc0e937413cb44e533391e573c43640263b40`. Its committed Builds gitlink is
`80928033b28e7a9726e93c8850389a081d3a2cb6`. Platform's
`eng/builds_publication.py:49` rejected that pairing before execution of
the canonical R1–R11 gate. Log SHA-256 is
`29aa1949aa643a7e6e7ad5811bf611c766625492012b72c4e009be362f60e64d`.
Platform owner `main` at `6046e6f15d220b84a12488178cd1114778e7e81b`
has the same tuple tag and gitlink. The Platform owner needs to reconcile
the pair and qualify the corrected input before Works consumes it.
[PR Platform parity job](https://github.com/Hexalith/Hexalith.Works/actions/runs/45590548959/job/139132633108) ·
[Platform tuple](https://github.com/Hexalith/Hexalith.Platform/blob/616e27789f935ebb7f7f33406150ecf2dc9913a2/eng/builds-tuple.json)

While the PR ran, Works `main` independently advanced to
`0f7963233e721cd758e56000c1bff4da76706756`, tree
`c8c727d0737b93ff82696c4250571afe405b27b2`. Its source records and
manifest now match EventStore `70e1f765d21ec93f1461c21e4a460b4b14dc7b66`
and PolymorphicSerializations `a8093f273cd095a3cb86bf59e6042c1843f4d086`.
The delivered Builds pin, Platform pin and all parity and source-identity
entry blobs stayed identical. PR 26 was closed as superseded to preserve
the reconciled source records. Exact successor run `45592491388`,
attempt 1, passed shared Stages 1–4 and source identity in job
`139130009115`. Its independent parity job `139135384855` reproduced
the same tag-to-gitlink mismatch before the canonical gate. Log SHA-256
was `931dfa1c16b14fb9841dc1c876179d98774de23b954c3dfd8fc7ce53dd891875`.
[Works successor](https://github.com/Hexalith/Hexalith.Works/commit/0f7963233e721cd758e56000c1bff4da76706756) ·
[Successor parity](https://github.com/Hexalith/Hexalith.Works/actions/runs/45592491388/job/139135384855)

On the preceding Works base `6dc406e07e64e7f4d2b79851b56ba67d25f76300`,
shared CI passed and Platform parity failed in run `45575363008`,
attempt 1. Authenticated artifact `15007775144` matched GitHub's ZIP
SHA-256 `4c637061eba1ae4232dab278c072526d04cbc361347266c52b78d7c5eda4819d`.
The ledger SHA-256 is
`411969e3406ae61509e42173fc698b43c72b0d4fe1aaa2105eb8226ce67b8a5c`.
The projection xUnit report SHA-256 is
`6a186f75e3bf3996dd4beac1567ce289ea6d93a6ad07a39e75a4339f934be9b7`.
The same `ActualPlatformSharedRebuildAndConcurrentCatchUpPreserveCompleteFamily`
test again failed after startup and readiness. Works and Platform own the
runtime investigation. Builds owns the separate Stage 4 scheduler failure
on `50006/tcp`.
[Parity artifact](https://github.com/Hexalith/Hexalith.Works/actions/runs/45575363008/artifacts/15007775144) ·
[Builds handoff](hosted-ci-triage-20261124.md#build-auto-maintainer-and-runner-recheck)

Hosted scan `45587963703`, attempt 1, ran the controller at
`eeb0fbffd0ea65d514296529b77519498c56417f` against exact Works
`f934f53682fb6f8250370289103a19df65e9480e`. It verified jscpd
5.4.3 signatures and policy SHA-256
`abd8c8ad7ad31d1b315f6fe73742e410b245016f0b63c6ceabecc8615c41ffd8`.
Works selected six files and failed on 16 discovery diagnostics, including
the unproved Platform gitlink. The report has zero run-level errors and zero
findings involving Works. Artifact `15009548200` matched GitHub's ZIP
SHA-256 `18bd792aad0e1f6c60d40b7cbb2fa5771e41d43512b04d8466d7894dca32accc`.
Report SHA-256 is
`13fcfaca4e351081f08560046803bb46b80c72a44e12305666b1b13d711206b6`.
[Hosted scan artifact](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45587963703/artifacts/15009548200)

Hosted Delivery validation of that CiCd revision failed with
`tools/delivery_runtime.py: trusted selector source differs from reviewed policy`.
Job log SHA-256 is
`5870c2f1078e132e8c93bdf12e6b7f6d7f2defb2758b0bf9016104c419854da0`.
The scanner-only transport moved into `tools/scan.py`, restoring delivery
runtime blob `e53d73c39a1d0ae87ef85ff34991a3405fc14977` byte-for-byte.
The renderer check, inventory checker and all 21 inventory tests passed
locally. The broader locked `tools/validate.py` check passed all seven
module readbacks and exited 1 after its global suite exceeded the
1,800-second limit. Log SHA-256 was
`b6fa28c26364c565e5781e44bc7f0d516ad8e8d3b5d6d710183260cd9ca1ab0e`.
[Hosted validation job](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45579645787/job/139100805009)

The acceptance reader for the latest completed scheduled Nightly,
`45394054346`, attempt 1, exited 1. Its report SHA-256 was
`eecd984497fdc7d918fc319debadd89d457ad992968973c418a550065f4ab638`.
Both release CodeQL jobs passed. Works release and duplicate scan failed
on the older dispatch commit `ae9dbe8eccd58ff1e9c0276cc17ed0a2e70d03bf`.
[Scheduled Nightly](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45394054346)
