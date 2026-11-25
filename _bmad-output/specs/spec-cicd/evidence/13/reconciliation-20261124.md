# Works migration reconciliation, 2026-11-24

## Maintainer readbacks

GitHub administration used the command-local maintainer profile
`/home/administrator/.config/gh`, account `jpiquot` (ID `6775094`).
`GH_TOKEN` and `GITHUB_TOKEN` were unset. The target was
`Hexalith/Hexalith.Works` (ID `1264171182`), default branch `main`.
The CiCd App installation `179966090` now selects all repositories. The
historical receipt recorded selected-only access with Works already included.
[Historical AD-21 readback](ad21-live.md)

| Check | Current result |
| --- | --- |
| Rulesets | Active `27474176` blocks deletion and non-fast-forward updates of `refs/heads/main`. Active `27474178` blocks deletion and updates of `refs/tags/v*`. Both have empty bypass lists. |
| Publishing | Immutable releases enabled. `hexalith-release` allows exactly the branch `main` and holds `HEXALITH_REGISTRY_USERNAME` and `HEXALITH_REGISTRY_PASSWORD`. `HEXALITH_RELEASE_PUBLISH_ENABLED` is `true`. The existing `production` environment has an empty secret inventory. |
| Controls | Default CodeQL setup `not-configured`. Dependabot security updates disabled. Push protection enabled. Repository and organization retention 90 days. Organization workflow default `read` and fork approval `all_external_contributors`. |
| Legacy releases and CodeQL | Release inventory had zero drafts. The read of `refs/tags/v1.0.0` returned HTTP 404, verified with the same profile that read Works `main` successfully. Four `refs/heads/main` analyses for retired `.github/workflows/codeql.yml:analyze` from 2026-11-18 remain since the initial cleanup. IDs are `2195754216`, `2195505517`, `2195321919` and `2193710346`. The 26 analyses from `.github/workflows/release.yml:codeql` are the distinct retained category. The reconciliation only read historical analyses. |
| Legacy org secrets | Works is absent from all eight selected Actions secrets in the legacy families: `AZURE_APPLICATIONID`, `AZURE_APPLICATIONSECRET`, `AZURE_SUBSCRIPTION_ID`, `AZURE_TENANT_ID`, `HEXALITH_ZOT_API_KEY`, `HEXALITH_ZOT_USERNAME`, `NUGET_API_KEY` and `SONAR_TOKEN`. No legacy entries in the organization Dependabot secret inventory. Works' repository Actions and Dependabot secret inventories are empty. |
| Shared pull access | Works retains the selected registry pull pair in both Actions and Dependabot, and the selected `HEXALITH_NUGET_USER` Actions variable. Each selection covers nine repositories, including Works. |

- **NuGet trusted publishing.** A fresh authenticated browser read loaded 23
  policy rows. The Works row is active policy `27451`, package owner
  `Hexalith`, repository owner ID `80614290`, repository ID `1264171182`,
  `release.yml`, environment `hexalith-release`, package glob
  `Hexalith.Works*`, with push of new packages and versions only. The Works
  legacy `production` policy `20087` is absent. Readback SHA-256
  `72745844267dee7438d072e9c68f988555ecc097d0c2d7bb33cb8e0dd7e8797c`.
  [Provisioning receipt](nuget-policy-verification.json) and [cleanup receipt](nuget-cleanup-verify-cleanup.json)
- **NuGet legacy API key.** The fresh authenticated API Keys page showed one
  row, `954800` (`Github Hexalith`). It is **Expired**, owner `Hexalith`,
  glob `Hexalith.*`, push of new packages and versions. The glob includes
  Works package IDs, and expiration leaves this key without live publishing
  access. The mapping from the encrypted GitHub org secret to an account key
  remains unverified. Browser readback SHA-256
  `d1a0d6c746c090d12da7a96122cda73fbb59fb829adaf4e6a88a9cf81cbdd5df`.
  [Earlier authenticated key readback](../15/nuget-api-key-metadata.json)
- **Scoped Zot identity.** ConfigMap `distribution-registry-config` resource
  version `49008107` grants `hexalith-works-publish` read/create/update on
  exactly `works` and `works/**`, with no admin grant. The deployment
  observed generation `26` and had one ready replica. Projected ACL readback
  SHA-256 `5848d56c280236456454a374ee0200a43de12d1ac39121c03e3cf17d5f449b27`.
  The original receipt binds the release environment pair to this identity and
  records HTTP 403 for foreign write probes.
  [Zot provisioning receipt](provision-registry.json)
- **Shared legacy Zot key.** The account's authenticated `GET /zot/auth/apikey`
  returned HTTP 200 and confirmed key `099585e7-fd9e-4aac-9042-56426c1add7b`
  remains active with `scopes: null`. Its owner, `jpiquot@itaneo.com`, has
  global read/create/update/delete through `adminPolicy`, which also covers
  Works. The live GitHub selections for the mapped pair are EventStore,
  Memories, Parties and Tenants. Revoking this key affects those repositories,
  and dropping one Works ACL row leaves its global admin authorization in
  effect. The shared removal remains open pending a scoped replacement for
  the other consumers. Metadata response SHA-256
  `f9abbf28fa7906c03a13d170ce1da1eb3e9a663bc226ee3da8c4bdc207ad5998`.
  [Owner-confirmed mapping](../23/legacy-zot-human-mapping.json) and [Zot authorization rules](https://zotregistry.dev/v2.1.22/articles/authn-authz/)

## Product preparation and delivered perimeter

| Revision | Commit | Tree |
| --- | --- | --- |
| Product preparation | `18853d2af196c02ca80d0b40a46418f9866797d1` | `494745dee30899da656987ebf5f1534280653931` |
| First delivery input | `4053907d5764bc8833c95dd79ea337bc8faba159` | `71ece8756a69e0718a04b12c6950f5bea64a1cb9` |
| First adopted Works | `3996de28eecf32972e8469cbcd7426eaa56f24ab` | `3ad3484ed0fd73a83cdc65890d04b5632435fc08` |
| Live Works `main` | `ae9dbe8eccd58ff1e9c0276cc17ed0a2e70d03bf` | `4cb1fc575b9523210df666d7abb37d423eabe557` |
| Live accepted CiCd delivery ref | `191369dfdd7b385856f40e4d373ce872b653ccf8` | `555aec6a92178b960709bb7b5032d147af538a66` |
| CiCd checkout | `eba76b2d4680eab1a02b7a88df6021a5f4cb3b5f` | `f4e4fc28da166af58bbc7a2b231c8d292052179d` |

- The raw Git comparison against preparation base
  `e63d857f0b75023b3b8ca9d786e5d5254e23b4b2` found zero changes to owned
  objects or modes, plus preserved `commitlint.config.mjs` and `global.json`.
  The historical proof passed package-mode build, stage 3 and 4 tests,
  consumer validation, commitlint, audit lint and source identity on the
  recorded candidate tree. [Preparation receipt](prepare-proof.json)
- Replaying the original accepted perimeter at CiCd
  `a7aab9c52d382202d071fc2b208ab3f4303a26e0` with Builds `v6.4.2` produced
  the exact first adoption tree from its parent in a disposable Git index.
  Both custom action blobs and modes survived first delivery. The live
  accepted ref and the CiCd checkout also agree on the Works setup, renders,
  perimeter and Builds version. The `v6.8.1` comparator found zero drift
  across all 17 entries against live Works `main`. Verification output SHA-256
  `b15dd58ae1bd51ee60dfb6c6739cecc6ff21b77cc0b63cc96aa3872ddd09d4c9`.
  [First delivery](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/44616302631)
- Shared CI still uses stages 1–4, with the source-identity
  `after-unit-tests` action (`24c2fbc9669907bde88f6b182859ef27cb5496d8`).
  The Platform R1–R11 action (`bd41393a5ec2eba423a0d185a6de265bc108337b`)
  runs in its own Ubuntu job with Dapr, Aspire and 180 minutes. The CI caller
  schedules that job after the shared job succeeds, as it did at first
  adoption. The solution retains ArchitectureTests, PropertyTests, UnitTests
  and IntegrationTests, with all nine Explicit Platform-lane facts still in
  IntegrationTests. The preparation's retired CI/story tests, root
  semantic-release/npm files, `.husky/` and old commitlint configuration
  are absent. The package audit is enabled in `all` mode. There are no
  `NuGetAuditSuppress` items to transfer. The historical `NU1901`–`NU1904`
  warning-severity setting remains outside the waiver transfer.
  [Works gate classification](../../gate-classification.md#works-classification-story-13)
- Registration blob `2015476973c684c6ee93f5e0e0722e9297736e5f`, perimeter blob
  `d9b4df7c4c1dfa9cbae9965ee6483964277ff784`, and CiCd Works gitlink
  `9e2529e4f81f127c4e09fe4a262d2a09ea4c4f50` are recorded in the CiCd checkout.
  Registry output files matched the live blobs for
  `.github/hexalith-ci.json` (`a7d49477a425611335dfc6a774e63ff790476c09`),
  `ci.yml` (`d5314356f9795abccba97c12eafcf8036fd40000`),
  `release.yml` (`a077849f70c030906ebb30b0eab5d1c4235d1e0f`) and
  `dependabot.yml` (`42d2ea0d0f8496bfb142cd35904c798e05e619d3`).
  The delivered Builds gitlink is `bf8a28b4bbcec619e8d9764d335f786f2bafb69e`,
  authenticated as the commit for immutable release `v6.8.1` (ID
  `456644518`). Works' `eng/published-builds.json` blob
  `034f49bc5643582a4bafeefc8c99e34396ad70f7` independently binds the reviewed
  `v6.6.2` producer publication, release ID `454690032`, producer source
  `2d9ef8b454ff897daca0149f3549844f584b634a` and artifact `14769162640`.
  [Immutable Builds release](https://github.com/Hexalith/Hexalith.Builds/releases/tag/v6.8.1) and [producer run](https://github.com/Hexalith/Hexalith.Builds/actions/runs/45057509167)

## Verification

- `run-with-temp uv run --locked --script tools/render.py --check` exited
  0. Combined output SHA-256
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- `run-with-temp python3 references/Hexalith.Builds/check.py` exited 0
  on the exact Works `main` commit and tree above with all 15 declared direct
  submodules at their committed pins and zero initialized nested submodules.
  The package-mode build had 0 errors. ArchitectureTests passed 386,
  PropertyTests passed 3, and UnitTests passed 603, with zero skipped in
  each suite. The checker identified IntegrationTests in its integration
  partition. Hosted stage 4 and Platform parity remain distinct acceptance
  evidence. The disposable checkout stayed clean. Combined output SHA-256
  `d4895b2e9a21a4dad22d441d1a7040df3799ee402574d5fb788c7d5c0c67f75b`.

## Hosted acceptance

- The last successful hosted CI was on Works
  `dbd742bd41f3db1deffc49a5bade3625e443cdc3` with Builds `v6.6.2`. Shared
  stages 1–4, the source-identity hook, and Platform parity passed.
  [CI run 45195632178](https://github.com/Hexalith/Hexalith.Works/actions/runs/45195632178)
- CI on current Works `main` failed before compilation in Stage 2 with
  `managed producer validation refused: HTTP Error 403: rate limit exceeded`.
  The tagged `Github/lib/published_builds.py` reads GitHub's REST API without
  authorization headers in `read_official`. The newly published `v6.8.2`
  (`29923b011061347e7f61ece16d59095889bde91a`) retains that implementation.
  The Stage 2 log SHA-256 is
  `0d49aa0ae7b33ffd4a7bc6fcccff887282ab2d3794b68ed9eebec2463c3b3794`.
  [Stage 2 job 138457721036](https://github.com/Hexalith/Hexalith.Works/actions/runs/45397690202/job/138457721036) · [Released lookup implementation](https://github.com/Hexalith/Hexalith.Builds/blob/bf8a28b4bbcec619e8d9764d335f786f2bafb69e/Github/lib/published_builds.py#L143)
- The CiCd-agent profile could read that run (`HTTP 200`, `actions=read`
  endpoint), but GitHub refused `POST
  /repos/Hexalith/Hexalith.Works/actions/runs/45397690202/rerun-failed-jobs`
  with `HTTP 403 Resource not accessible by personal access token`. Both
  token override variables were unset. The repository was confirmed by ID
  `1264171182`, the authenticated account was `jpiquot`, and run attempt 1
  remained unchanged. The rerun endpoint requires Actions write access.
  [Rerun API permissions](https://docs.github.com/rest/actions/workflow-runs#re-run-failed-jobs-from-a-workflow-run)
- The scheduled Nightly dispatched Works on the same live commit. Both
  release CodeQL jobs passed, and release identity refused the failed CI.
  Its log SHA-256 is
  `d91ef50c58e1e84fc61fc65235b3d99a35b9ae70508dde8a97a6ef9fddacf57f`.
  The exact-head duplicate scan recorded 23 Works discovery errors, starting
  with unsupported shell command substitution at
  `.github/actions/platform-parity/action.yml:10`. Scan archive SHA-256
  `9ec2857db2830cf006f5034b026f4d4f2febfc740a16ef1eb3691254acef5b81`.
  [Release identity job](https://github.com/Hexalith/Hexalith.Works/actions/runs/45402064131/job/138472970840) · [Duplicate scan artifact](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45404275797/artifacts/14924224437)
- `python3 tools/nightly_acceptance.py --run 45394054346 --module Hexalith.Works`
  exited 1 for the failed release and the failed Works scan row. The
  authenticated Nightly archive SHA-256 is
  `d6f17694a10ab3319ca784728fb359cc49cf47cb36c108b837b1a5aea622fa73` and
  the acceptance report SHA-256 is
  `eecd984497fdc7d918fc319debadd89d457ad992968973c418a550065f4ab638`.
  [Scheduled Nightly](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45394054346) · [Nightly artifact](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45394054346/artifacts/14924558700)
