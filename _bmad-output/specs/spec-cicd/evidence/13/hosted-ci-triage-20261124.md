# Works hosted CI triage

## Maintainer preconditions and cutover readback

The preflight used the command-local maintainer profile
`/home/administrator/.config/gh`, authenticated as `jpiquot` (ID `6775094`)
against Works repository ID `1264171182`, with no `GH_TOKEN` or `GITHUB_TOKEN`
override. CiCd App installation `179966090` selects all repositories. The
active `main` and `v*` rulesets `27474176` and `27474178` match AD-21. The
two published `v*` releases account for both tags and there are zero drafts.
Four historical analyses of retired `.github/workflows/codeql.yml:analyze`
remain, distinct from 26 analyses of the current release workflow. Default
CodeQL setup is `not-configured`, Dependabot security updates are disabled,
push protection is enabled, and repository and organization retention are
90 days. Organization workflow permissions default to `read` and all external
fork contributors require approval. The Codex connector installation `77847816`
reports `all`, wider than AD-7. Cursor reports `selected`. Its organization
installation repositories route returned HTTP 404, so the exact selection
remains unverified by that read.

`hexalith-release` allows only `main`, with no reviewers or wait timer. It
has the two dedicated publishing secret names from the provisioning receipt,
both last updated `2026-11-17T16:22:27Z`. `HEXALITH_RELEASE_PUBLISH_ENABLED`
is `true`. Immutable releases are enabled. All eight legacy Actions secret
selections exclude Works. It retains the Actions and Dependabot registry pull
pairs and the `HEXALITH_NUGET_USER` variable. The repository Actions and
Dependabot secret inventories and `production` environment secrets are empty.
[Provisioned Works identity](provision-registry.json) · [Original GitHub cutover](post-adoption-github-cleanup.json)

The authenticated NuGet policy page returned 23 rows. The Works policy
`27451` is present with glob `Hexalith.Works*`, and `20087` is absent.
Projected response SHA-256
`9e20e80b4f04eb65364b5fd44a24f80ca483e1769ade4f650073a21a9950bf3b`.
The original receipt confirms `27451` was added beside `20087` for
`release.yml` and `hexalith-release`. A fresh API Keys view returned
`Authenticated NuGet API Keys document unavailable`. The earlier authenticated
read showed key `954800` expired. The GitHub maintainer read verified selected
secret metadata and membership for `NUGET_API_KEY`. GitHub does not expose its
backing key through that metadata, so key disposition remains open.
[Additive provisioning](nuget-policy-verification.json) · [Policy removal](nuget-cleanup-verify-cleanup.json) · [Earlier authenticated key inventory](reconciliation-20261124.md#maintainer-readbacks)

The ready Zot deployment is at generation `26` and ConfigMap resource version
`49008107`. It grants `hexalith-works-publish` read, create and update on
`works` and `works/**`. The mapped legacy key's owner still has global read,
create, update and delete. The projected readback SHA-256 is
`b4efad30ec72369083e7e3cabaad7d063334dab68c50b45627cea2b41bbe57d9`.
Both legacy Zot secret selections still include EventStore, Memories,
Parties and Tenants. The previous authenticated key inventory recorded the
mapped key active and unscoped. The maintainer cutover requires qualified
replacement access for all four consumers, continuity proof and key
retirement. [Current consumer mapping](../23/legacy-zot-human-mapping.json) · [Previous authenticated key inventory](reconciliation-20261124.md#maintainer-readbacks)

## Exact source and adoption

The restricted module-agent profile fetched Works `main` at
`8c40da783cd37d0259cec515690f6c4950d87a6b`, tree
`75206d1d17fdea303148dddd2ee5e7bb15078670`. The authenticated branch readback
matched the fetch. The adopted perimeter matches the preceding reconciliation.
Works still uses immutable Builds `v6.8.1` at
`bf8a28b4bbcec619e8d9764d335f786f2bafb69e`. The CI workflow blob is
`d5314356f9795abccba97c12eafcf8036fd40000` and the independent Platform
gitlink is `99a17baaf6de626d5f59311544a6aa8f9865b695`.

CiCd registration commit `74ca332e839fb37d41354f932a28d3d5e98242b8` added the
Works setup, render and perimeter with product gitlink
`4053907d5764bc8833c95dd79ea337bc8faba159` in its tree. Delivery run
`44616302631`, attempt 1, succeeded on CiCd
`a7aab9c52d382202d071fc2b208ab3f4303a26e0` and adopted Works at
`3996de28eecf32972e8469cbcd7426eaa56f24ab`, tree
`3ad3484ed0fd73a83cdc65890d04b5632435fc08`. That commit is an ancestor of
current Works `main`. The live `delivered/Hexalith.Works` ref
`191369dfdd7b385856f40e4d373ce872b653ccf8` and current CiCd `main`
`eba76b2d4680eab1a02b7a88df6021a5f4cb3b5f` agree on the Works setup,
render, perimeter and `builds-version`. Current Works `main` has no root
`package.json`, `package-lock.json` or `.husky` and zero `NuGetAuditSuppress`
items across 24 tracked `.props`, `.targets` and `.csproj` files. No Works
waiver transfer is required. [Delivery run](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/44616302631) · [Exact adoption receipt](authenticated-adoption.json)

## Stage 4 and Platform parity

- On Works `7bd9b18c02985ea5fc320735d16bd6ee0d2f6019`, the Stage 4 setup and
  source-identity hook passed. `LiveFactsRequireExplicitSelection` failed
  because the expected inventory omitted the new explicit measurement
  `WorksQueueMeasurementTests.WhatsNextMeasuresUnpagedEligibleResponses`.
  Works commit `63c07f566abf2043ebcfcc62d47aaf01e7564689` added the inventory
  entry and preserved the measurement's `Explicit` flag. That fix is on
  `main` and the shared job passed on its exact source. Failed job log
  SHA-256 `a3d03568cb1f4588f246402e206f0c361b9acd132d165a6e5f01686c560dee9b`.
  [Failing integration job](https://github.com/Hexalith/Hexalith.Works/actions/runs/45480464147/job/138751886952) · [Merged Works fix](https://github.com/Hexalith/Hexalith.Works/commit/63c07f566abf2043ebcfcc62d47aaf01e7564689) · [Passing shared job](https://github.com/Hexalith/Hexalith.Works/actions/runs/45482017535/job/138757371900)
- For run `45482017535`, attempt 1, Platform Linux preparation succeeded and
  the sealed gate ran against that same Works commit and Platform gitlink.
  The `platform-recovery` check failed inside the Works test
  `WorksSdkRecoveryPipelineSmokeTests.SdkRemindersAndCascadeConvergeThroughPersistedReceiptsAcrossRestart`.
  Startup and readiness passed. The test was canceled in its wait for a
  committed cascade target after delayed child creation, at line 520.
  The product and parity owners still need a current-head reproduction to
  determine the underlying cause. This run used the same Builds pin as
  current `main` and its producer lookups succeeded in both jobs. The
  parity job log SHA-256 is
  `9f700f8fa3d22b062ba82a1d36184dc6463c6efe415f3a4bb82b842739f97128`.
  Authenticated artifact `14964817981` (`works-platform-parity`) matched its
  archive SHA-256
  `a6fe469a08e63a9ba53de8ac9d117a288aec6a079cec0d15cbcdec5dcd7c001e`.
  Its recovery log SHA-256 is
  `771fb1479ef7641d42d867be6f6749befc350caaa159a0f15f7a3781d931c12f` and
  its ledger SHA-256 is
  `ad5d959754879d9f3acd394a68bc512c281275663266fc52e8d0b20598872639`.
  [Platform job](https://github.com/Hexalith/Hexalith.Works/actions/runs/45482017535/job/138762380777) · [Parity artifact](https://github.com/Hexalith/Hexalith.Works/actions/runs/45482017535/artifacts/14964817981)
- On current Works `8c40da783cd37d0259cec515690f6c4950d87a6b`, hosted run
  `45488107270`, attempt 1, passed Stages 1–3. Stage 4 failed in Builds
  `Github/lib/ci_environment.py` while its pinned Dapr 1.19.2 initialized.
  Docker could not bind `0.0.0.0:50006/tcp` for `dapr_scheduler`. This is
  the same failure as run `45477706952` on `64919bc8`. The socket owner is
  unverified. The shared Builds environment setup owns this failure. The
  source-identity hook, integration tests and Platform parity were skipped.
  The latest job log SHA-256 is
  `5b0609aa1bd914bcf5e4d020dde70aa9827ca3f15be007bd94639a238854c945`.
  [Current Stage 4 job](https://github.com/Hexalith/Hexalith.Works/actions/runs/45488107270/job/138778815834) · [Earlier Stage 4 job](https://github.com/Hexalith/Hexalith.Works/actions/runs/45477706952/job/138742220256) · [Builds initialization](https://github.com/Hexalith/Hexalith.Builds/blob/bf8a28b4bbcec619e8d9764d335f786f2bafb69e/Github/lib/ci_environment.py#L160)
- The earlier producer lookup returned `HTTP Error 403: rate limit exceeded`
  in shared Stage 2 and, on a separate run, Platform Linux preparation.
  Current immutable Builds `v6.8.2` (`29923b011061347e7f61ece16d59095889bde91a`,
  release `456766489`) has the same anonymous lookup and Stage 4 initialization.
  The recorded CiCd-agent rerun refusals on `45397690202` and `45437993140`
  were `HTTP 403 Resource not accessible by personal access token` on
  `rerun-failed-jobs`. The account was `6775094`, repository `1264171182`,
  with no token overrides. The run readbacks succeeded and both attempts
  stayed at 1. A separately authorized Actions operator is required for a
  rerun. [Earlier producer failures and exact refusal](auto-run-20261124.md#follow-up-verification) · [Builds v6.8.2](https://github.com/Hexalith/Hexalith.Builds/releases/tag/v6.8.2)

## Hosted scan and Nightly

The latest completed hosted duplicate scan observed was `45404275797`,
attempt 1, on CiCd `191369dfdd7b385856f40e4d373ce872b653ccf8`.
Artifact `14924224437` (`hexalith-nightly-scan-1`) SHA-256
`9ec2857db2830cf006f5034b026f4d4f2febfc740a16ef1eb3691254acef5b81`
covers the earlier Works `ae9dbe8eccd58ff1e9c0276cc17ed0a2e70d03bf` and fails
Works discovery. Hosted scan qualification on the current candidate base
remains open. [Hosted scan](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45404275797) · [Scan artifact](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45404275797/artifacts/14924224437)

`python3 tools/nightly_acceptance.py --run 45394054346 --module Hexalith.Works`
returned 1 again with report SHA-256
`eecd984497fdc7d918fc319debadd89d457ad992968973c418a550065f4ab638`.
Both CodeQL jobs passed. The release outcome and Works scan failed on the
older dispatch commit `ae9dbe8eccd58ff1e9c0276cc17ed0a2e70d03bf`. Acceptance
Nightly is pending AD-21 cleanup, passing exact-source hosted CI and qualified
scanning. [Scheduled Nightly](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45394054346)

## Refreshed local discovery candidate

The seven reviewed Works files were reapplied from `4f9639fc` onto freshly
fetched `8c40da78` with identical blob IDs. The exact candidate is
`2a019b1889feb9494fc65b57f9d9fc7a36c3bfbd`, tree
`aa0f5125b791546831dcc59c6ccf63306bcad776`, on local branch
`fix/works-parity-discovery-8c40da78`. The rendered workflow, configuration
and Dependabot blobs match live `main`. The candidate preserves the current
owned perimeter, retained tests, package audit and direct dependency pins.
The registry still selects the source-identity hook and the separate
180-minute Dapr and Aspire job. [Candidate source blobs](platform-scanner-prerequisite.md)

- Released Builds `v6.8.1`'s npm signature verification and commitlint passed.
  Commit message SHA-256
  `dbc53a26b6ee9b44af9a7c5b136d5c1aa27c51979aa2719f4754cf1127caf46b`.
- The standalone checkout verified all 15 direct pins and initialized zero
  nested checkouts. Inventory SHA-256
  `ca68e774b8b890893822482b594cb55217a6468b8e115f73d2e4a60d87473b1b`.
- The 48 Platform and 20 source-identity fixtures passed, with logs SHA-256
  `e47198b5bdc3cdbbfa4ed0efde2a8bbb794746423f69e0ba64234b2f1f5010ee` and
  `6d56f43e51f38ef11107761fc79349a2d498ef7e048c0e3d1ad368fccccb0da8`.
- `python3 references/Hexalith.Builds/check.py` exited 0 with the exact
  candidate checked out and authenticated `origin/main` recorded at its
  parent. It passed the ownership and action guard, Release package build,
  and ArchitectureTests, PropertyTests and UnitTests. The standalone checkout
  finished clean. Checker output SHA-256
  `62db2e729744173bb0c650a4c957bbc443c44033c87765a9180cd31ea93dbe5c`.
- The locked CiCd renderer exited 0. Output SHA-256
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

Both exact-source local scans used the committed production controller at
`eba76b2d4680eab1a02b7a88df6021a5f4cb3b5f`. Only Works' Git transport pointed
to local commit objects. Both runs verified jscpd `5.4.3` signatures and used
policy SHA-256 `abd8c8ad7ad31d1b315f6fe73742e410b245016f0b63c6ceabecc8615c41ffd8`.
Each run had zero run-level errors and zero measured copies. Both Works rows
failed discovery.

| Exact Works input | Selected files | Works diagnostics | Report SHA-256 |
| --- | ---: | ---: | --- |
| `8c40da783cd37d0259cec515690f6c4950d87a6b` | 6 | 26 | `3b7998a0ba077b2d89c6d3264c31b92de0c5d2d4995cdd7f81191271a5076b43` |
| `2a019b1889feb9494fc65b57f9d9fc7a36c3bfbd` | 6 | 16 | `e6e69fe1977db8c5da980eaa1407e7ac761c37fa74c7e2c91481755e1d260b17` |

The candidate's diagnostic array has SHA-256
`5de16938d7b1e1ca002a7ae68ff82ca4e4e89627423d9749bbc306db44186db9` and
matches the earlier source-and-line table exactly. The CiCd scanner owner
still needs to qualify the verified Platform execution boundary. The candidate
stays local pending passing hosted scan discovery, exact candidate discovery,
and both hosted Works jobs passing at the same fresh `main` base and Builds pin.
[Scanner diagnostics and prerequisite](platform-scanner-prerequisite.md#follow-up-works-candidate)

## Build Auto maintainer and runner recheck

The command-local maintainer readback against Works repository `1264171182`
confirmed the main-only release environment, its original pair of Zot secret
names, immutable releases, both exact rulesets and all eight legacy secret
exclusions. The scoped pull grants remain in Actions and Dependabot. The live
NuGet Trusted Publishing page showed Works policy `27451` with
`Hexalith.Works*`, `release.yml` and `hexalith-release`. The page had no
`20087` policy row. The original receipt establishes that `27451` was added
alongside `20087`. The API Keys page returned
`Authenticated NuGet API Keys document unavailable` during this check.
The stored `NUGET_API_KEY` still has no verified mapping to expired key
`954800`. The projected GitHub ruleset, release and secret-selection readback
SHA-256 is
`2eb9d0d41df8d48117e4a4fcd557f54960db1cae384e0e2a58abe01c5368e4ce`.
[Additive NuGet policy receipt](nuget-policy-verification.json)

Authenticated Zot metadata returned HTTP 200 and confirmed legacy key
`099585e7-fd9e-4aac-9042-56426c1add7b` is unexpired and unscoped. The projected
response SHA-256 is
`2be9f64d8e1120967b03d912351dad7a325b48106015e414f0cf1412f4a0a426`.
The current ACL still grants the legacy key owner global write. Of the four
remaining consumers, Tenants alone has a dedicated release-environment pair and
publisher ACL for its repositories. EventStore, Memories and Parties have no
`hexalith-release` environment. Both organization grants still select all four.
The following verified live workflow blobs reference both legacy secrets.

| Repository | Exact live `main` | `release.yml` blob | `recover-partial-release.yml` blob |
| --- | --- | --- | --- |
| EventStore | `208af26a5817da3bfb40da0bf968fbc3b578d83a` | `e08272bff06157faaa7964215c5ff01de1024ecd` | |
| Memories | `742a3e99ade83a19ca15a6effac87421dcb40ef0` | `d26582d0158f3c8356a4da97da8d7a8874f1e89e` | `c22dcd4eaa037a2cff915c4f97738ca3aec7fc2b` |
| Parties | `2851be5c79d4ccc9d98858fbeea96e11fc4ab289` | `a9d84a562f9b8aef1de28ef79f157bfbe5535ffa` | |
| Tenants | `d58f24d8d6909d7498ecec34955e7f17720c1ba0` | `dbf97b1fe63f5ec9f3fb8d2b2b0abecc83fc657d` | `e0d20f3bab309bb175d2b909895128b83aef5bcc` |

Zot exposes create, list and revoke for API keys. Retiring the shared key
requires scoped replacements and release-path continuity evidence for those
workflows. The Works credential remains scoped to `works` and `works/**`.
[Confirmed legacy consumer map](../23/legacy-zot-human-mapping.json) ·
[Zot API reference](https://zotregistry.dev/v2.1.22/developer-guide/api-reference/#zotauthapikey)

The Builds handoff traces both `50006/tcp` failures to Ubuntu 26.04 image
`20261116.202`. On the same Builds pin, the intervening successful shared job
used image `20261116.88` and proceeded through integration tests. That job log
has SHA-256 `b88b22886bee2073476bf1b3cbb1c769ca5970d4288103971babd3a43b383aa6`.
The runner-image association is observational. The affected jobs did not record
the socket owner. The released `v6.8.1` and `v6.8.2` have identical
`ci_environment.py` blobs
(`48eec2326b9857a607259b0e8ad5ff0ac5f0423c`) and identical producer-lookup
blobs (`3caa3b6773a6cd33e66b388d7ee14751716feac4`). The prior Builds port
wait applies to the older `Github/dapr-init` action. Shared CI and Linux
preparation use `Github/lib/ci_environment.py`, which calls the pinned CLI
directly. The pinned CLI's scheduler host mapping is fixed at `50006` on
Linux, and this number falls within the default Linux ephemeral range. A
hosted reproduction needs numeric socket and Docker-port observations around
the single pinned initialization to identify the conflict while preserving the
initialization receipt and existing Dapr test behavior.
[Failing shared job](https://github.com/Hexalith/Hexalith.Works/actions/runs/45488107270/job/138778815834) ·
[Passing shared job](https://github.com/Hexalith/Hexalith.Works/actions/runs/45482017535/job/138757371900) ·
[Earlier Builds port fix](https://github.com/Hexalith/Hexalith.Builds/commit/c171c7265e70806f09f6ac54130aa6e28ef74395) ·
[Pinned Dapr CLI port mapping](https://github.com/dapr/cli/blob/v1.19.1/pkg/standalone/standalone.go) ·
[Dapr scheduler documentation](https://docs.dapr.io/concepts/dapr-services/scheduler/#failure-behaviour)

The standalone Builds `v6.8.1` checker passed again on candidate
`2a019b1889feb9494fc65b57f9d9fc7a36c3bfbd` and authenticated base
`8c40da783cd37d0259cec515690f6c4950d87a6b`. The exact checkout matched all
15 direct pins and initialized zero nested dependencies. The guard, Release
package build, and 386 architecture, 3 property and 603 unit tests passed
with zero skips. The checkout finished clean. Checker output SHA-256 is
`27ccb9f1a45b5a27f8800114768756d8d442093e11a62bc210723c161d70e5ef`.

An XML inventory of the Works preparation base, preparation commit and live
`main` found zero `NuGetAuditSuppress` items in 23, 23 and 24 tracked
project and MSBuild files, respectively. The root Node tooling and
`.husky/` are absent from live `main`. The existing delivery therefore
required no Builds waiver transfer.
