---
title: 'Migrate AI.Tools'
type: 'chore'
created: '2026-11-23'
status: blocked
baseline_revision: 1b566fc3b8fc97784d79f842cfb5531f09c350b2
implementation_repository: 'references/Hexalith.AI.Tools'
implementation_baseline_revision: '91fd549794c72e99d22b69d33ff24e403aede938'
review_loop_iteration: 0
followup_review_recommended: true
context: []
warnings: [oversized]
deferred:
  - summary: >-
      Preserve a verifiable dispatch-head identity on the stale-draft no-op outcome.
    evidence: |-
      The existing Builds reducer returns the selected draft SHA for the AD-17 stale-draft-deleted no-op. The acceptance reader requires the dispatch SHA for nothing outcomes. The current AI.Tools draft has a valid original artifact and follows the ready path.
    location: >-
      references/Hexalith.Builds/Github/lib/release_outcome.py
    severity: medium
---

<intent-contract>

## Intent

Bring AI.Tools under the shared CI and release pipeline and verify its own CAP-16 nightly outcome. Apply AD-21 in order using the approved AI.Tools package-free scope.

The Story 12 re-drive owns the two shared pipeline repairs raised by nightly `45276260491`:

- **GitHub-only publication.** When the authenticated original build inventory has zero packages and zero containers, `publish-ready` completes the same marked draft using its existing `hexalith-package-publication.v1.json` asset. Verify the asset and its empty package list against the draft's repository, version, original source, producer run, artifact ID and digest. Missing, invalid or conflicting evidence fails publication. Preserve the existing package and container publication checks for nonempty inventories and the draft, source, version and tag checks for every release.
- **Complete-mode acceptance.** Under AD-16 through AD-18, accept a release source older than the dispatch head only when authenticated evidence ties the correlated release run to completion of the same original bot-marked draft. Prove the original producer run and artifact identity and digest, prove that the original release SHA is an ancestor of the exact dispatch head, and verify that the immutable release and peeled version tag identify that original SHA. A `ready` outcome still requires verified publication by that same central nightly. Keep exact dispatch-head checks for the correlated release run, CodeQL and duplicate scan, and retain the existing delivery checks.

## Boundaries & Constraints

Use the module-agent credential for any product preparation and CiCd-agent for registration. Delivery owns the module perimeter. Verify the current source and the exact immutable Builds pin. The approved `solution: none` configuration requires a main-only `hexalith-release` environment and GitHub release behavior. It omits a module Zot push pair and scoped nuget.org policy until AI.Tools gains a package or container target. [AD-21](../../../planning-artifacts/architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md#ad-21--onboarding-sequence) · [Approved Story 12 scope](../../../implementation-artifacts/spec-12-migrate-ai-tools.md)

**Human resolution, 2026-11-23.** Story 12 closes only after both gates pass:

- The maintainer restores the approved AD-7 selection for `chatgpt-codex-connector` installation `77847816` and reloads its authenticated GitHub organization settings page after saving. The reloaded page must show `selected` with no pending changes. Compare the complete saved list by name against the 48 repositories in `github.unrelated_repository_ids` in the Story 11 repair receipt plus `Hexalith.EventStore`. The sets must match exactly. `Hexalith.EventStore` is the sole managed module in the list, and `Hexalith.CiCd` and `Hexalith.Builds` are excluded. Record the fresh readback with its timestamp, installation URL, digest and exact comparison result. This authenticated settings reload is sufficient evidence for the connector gate after the repository-list API's HTTP 403. [GitHub App settings](https://github.com/organizations/Hexalith/settings/installations/77847816) · [Story 11 repair receipt](../evidence/11/ad-7-ad-21-maintainer-repair-20261122.json)
- CiCd uses an authenticated immutable Builds release containing both first-release handoff fixes identified in Verification and any Builds-side changes required by the shared pipeline repairs. Verify delivery of that exact pin to AI.Tools. After the repairs land, a fresh eligible central nightly on `main` must dispatch AI.Tools against the delivered pin and pass `tools/nightly_acceptance.py --module Hexalith.AI.Tools`. A scheduled run or a manual run with `qualify-bump` false qualifies.

</intent-contract>

## Code Map

- `references/Hexalith.AI.Tools` is a documentation and skills repository. The published preparation removed the private commitlint npm package and lockfile. Its `commitlint.config.mjs` blob `0616fb937bb77b75355c94334276f9aa337b7c1f` and mode `100644` survived preparation and were removed by delivery. The current inventory has no `.husky/`, custom actions, workflow YAML tests, package or container targets, or NuGet waivers to move to `Props/`.
- `setup/Hexalith.AI.Tools.yml` (`948f5fe8202ca7f2298a1c8a58313ebe0bf214a6`) selects `solution: none`. `rendered/Hexalith.AI.Tools` tree `ecfced602751980efd8999184757a66b6eb2ad15`, perimeter blob `87afd3b1220fab4c5ce8163935b4c56efb4dd689`, and the module gitlink are committed in CiCd tree `d40fc938bc817f8c3752c2ae325bd804770d1ddc`.
- At the pause, `builds-version` blob `6fdce8f909b5307d0159bc0fc76748328ebe5f18` selected `v6.6.2`. The module's direct Builds gitlink and the authenticated immutable release both resolved to `2d9ef8b454ff897daca0149f3549844f584b634a`, tree `d610c1dd857908d8eda420c92cf8efcd5bf4b614`. [Builds release](https://github.com/Hexalith/Hexalith.Builds/releases/tag/v6.6.2)
- `tools/nightly_publish.py` completes ready drafts using the pinned Builds publisher. `tools/nightly_acceptance.py` judges the AI.Tools row. The first-release handoff lives in Builds `Github/lib/release_outcome.py`, and the package publication asset contract and finalizer live in `Github/lib/package_publication.py` and `Github/lib/release_publish.py`.

## Tasks & Acceptance

- [x] Check AD-21 with the maintainer profile. Story 11 was accepted on November 22. Live readback confirms the active CiCd App `179966090` covers all repositories, exact no-bypass `main` and `v*` protections (`27440691`, `27440693`), main-only release environment, publish switch `true`, 90-day Actions retention, read-default workflow permissions, approval for all external fork contributors, push protection, disabled Dependabot security updates and unconfigured default code scanning. The API reports no code scanning analysis (HTTP 404). The only draft is the marked `v1.0.0` draft `449697813`; the tag list is empty. [Pilot acceptance](11-pilot-migration-commons-and-polymorphicserializations.md#maintainer-acceptance--2026-11-22) · [GitHub release environment](https://github.com/Hexalith/Hexalith.AI.Tools/settings/environments)
- [x] Verify published preparation, registration and application. The module preparation `cfd1ebea92587cdea41b9aa2cff47358bf2f32f6` (tree `660ea16a129113d510b931cf91a6472955820989`) is the parent of the App adoption `180ca5692637a018c3f5547daf657e2a90bd5288` (tree `0fa5b0693699362a2358e4630f5d788d267b15c6`). The adoption artifact digest matches `34748d07f843d605163650ab1c844820663bcbfc61108c7d68165efe1d67f95c` for CiCd source `cc4b8cc46f4e254e20518c46726fc5a57ed1164f`. Scheduled delivery at current accepted ref `211d8a5f90afee49deab4bc428429e6592e385c5` reports AI.Tools unchanged with no reasons (artifact SHA-256 `b8acadd3cd90d7b8329552d4a096d403c6e9c175011fef8fb43423a760f7df68`). [Product publication record](../evidence/12/publication.md) · [Adoption artifact](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/44040325762/artifacts/14309624943) · [Current delivery artifact](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45205145141/artifacts/14834872679)
- [x] Check applicable post-adoption GitHub settings. Immutable releases are enabled. The only inherited Actions secrets are the two registry pull secrets, both also granted for Dependabot. `HEXALITH_NUGET_USER` is granted. Repo and release-environment secret inventories are empty. This establishes absence from the legacy GitHub org secret grants. The approved package-free disposition requires no package-ID or registry-repository revocation. External NuGet policy/key and Zot ACL inventories were not verified in this run. [Historical cleanup readback](../evidence/12/live-run-20261117.md)
- [x] Repair the GitHub-only `publish-ready` handoff and complete-mode nightly acceptance. Verify the package-free ready path and older-source proof, including refusal with missing or conflicting publication evidence, unproven ancestry or a mismatched release or tag. Record the repaired source revisions.
- [ ] Record the maintainer's authenticated settings reload and exact 49-repository comparison after restoring the Codex connector's approved AD-7 selection. At the pause, the installation API reported `all` with Workflows and Contents write.
- [ ] Record the immutable Builds tag and full source commit containing the required fixes, its delivery to AI.Tools, and the authenticated acceptance receipt for a fresh nightly that dispatched AI.Tools against that pin after the shared repairs landed.

### Acceptance Criteria

- Given the adopted current module, when delivery verifies its perimeter, then authenticated AI.Tools source matches the accepted render and retains its foreign content.
- Given adopted `main`, when the CI workflow and standalone Builds checker run for it, then both pass with `solution: none`.
- Given the saved Codex connector selection, when the maintainer reloads the authenticated installation settings and compares the full saved repository list, then the readback shows `selected`, no pending changes and exactly the approved 49 repositories above.
- Given a successful package-free `ready` outcome and its verified empty publication asset, when central `publish-ready` completes the original draft, then the immutable release retains the same draft identity and its version tag resolves to the original source. Missing or conflicting proof fails the row.
- Given an older release source, when the acceptance reader authenticates complete-mode provenance and verifies publication at the original SHA, then the source check passes while the dispatch-run, CodeQL and scan checks still use the exact dispatch head. An older source without that proof fails the row.
- Given the repaired central pipeline and the verified Builds pin delivered to AI.Tools, when a fresh eligible central nightly dispatches AI.Tools against that pin, then the authenticated acceptance receipt records a successful release or an authentic nothing-to-release outcome and passing associated rows.

## Verification

- Reconstructed complete adoption and current delivery trees from their exact parents and released perimeter implementations. Both matched, including foreign content. Current module tree `7430f8e5302865b4d90a1382c0f3484e88b11643` derives from parent `0cb4b837ebcb1607b6cae14d180606efadc7ca6d` and CiCd render `0e3ab54ecf9958b6986296d361c53ca52bc68e44`. Result SHA-256 `ee53f291f42abe9bcf8df6606d3bfdca183ca052ac03dbda8c461419baa6f0c9`.
- `run-with-temp uv run --locked --script tools/render.py --check` passed (empty output SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`). Standalone `python3 references/Hexalith.Builds/check.py` passed on exact live module main with its direct Builds dependency, using `run-with-temp`. Output SHA-256 `7abbc37921cb15ec007c157b0036da245fd917d2cbecf7848e7c2f3a431c45ee`. Hosted CI passed on the same SHA. [Hosted CI](https://github.com/Hexalith/Hexalith.AI.Tools/actions/runs/45173745983)
- AI.Tools' independent scan row passed at the current module SHA. The same nightly stopped before release dispatch at the delivery barrier. Its acceptance receipt SHA-256 is `49a5fd6a27b970ed4bd6f8299b9432cebfbe74ee999fff026c4671ba8a82cfaf`. The timeout predates the barrier policy now on CiCd `main`. [Scan artifact](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45185339361/artifacts/14827575107) · [Nightly dispatch artifact](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45185339361/artifacts/14825544696)
- The latest nightly that dispatched AI.Tools failed with `release publisher handoff has an invalid artifact digest or last tag` on Builds `v6.6.1`. The draft authentication job succeeded. Failure log SHA-256 `45d43113b896a9b7048fdbd4cd9daeca1dc79ee417e2ebebf1506e27de6dc00f`; nightly acceptance receipt SHA-256 `9aa7ecb4b01a3ae8d25d9d80cf52ef683559ab525e4a10abadae1b4d14d6d582`. [Nightly](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45130643695) · [Failing publisher handoff](https://github.com/Hexalith/Hexalith.AI.Tools/actions/runs/45130733380/job/137545531777)
- The existing first-release handoff regression in test blob `5af8434c4a8476886872708a12d3090679b3e63d` reproduced the failure against released `v6.6.2` reducer blob `7fc4b0f7f72ea303431f19eec4e8d64e0d734738` (exit 1, SHA-256 `db3bb47a20e3ffec282fb5a2476344c2d68e70dcf2ffbf2b10082012a1865552`) and passed against fixed reducer blob `9a6f1e2a45c31b099a951831d23dd7e05bb23c9d` (exit 0, SHA-256 `d10ffbd9f0faa72cd6837063279524e199b59fbc3d035051302a1e8dbc4b36ad`). The authenticated Builds `main` `763fc0e937413cb44e533391e573c43640263b40` contains both fixes. [First fix](https://github.com/Hexalith/Hexalith.Builds/commit/fb930d31a137ca1ffb58256260a42941353b29f6) · [Follow-up fix](https://github.com/Hexalith/Hexalith.Builds/commit/1252f0abea44f222dc82ef38c8ce59fade35dd59)
- Authenticated release and delivery readback at `2026-11-23T21:54:52Z` confirmed immutable `v6.7.0` at `763fc0e937413cb44e533391e573c43640263b40`, with both fixes verified as ancestors. CiCd `main` and `delivered/Hexalith.AI.Tools` were `2df38b66a14b72002a4339e58060905e5df843e2`, with `builds-version` blob `3f3ac79a6c52d34af2cbdda7ce596df71bbdccdf` selecting `v6.7.0`. AI.Tools `main` `d299ce98bfb60189a2f724d573e74bd25f7cf88d` (tree `07c9c0a01ff502040cfb3c29cc9300ce7817ca3b`) has the delivered manifest blob `28cf840a1f5c947f8d4b9e4b0f31bb56f9b287b7` and direct Builds gitlink to that release commit. The hosted delivery artifact archive SHA-256 is `fc3f6dcd8a0191def1cbc7c58fc66320ffbc858a4f316f3632cb6aec79172979`. Hosted CI passed on that exact module commit. [Immutable release](https://github.com/Hexalith/Hexalith.Builds/releases/tag/v6.7.0) · [CiCd pin](https://github.com/Hexalith/Hexalith.CiCd/commit/2df38b66a14b72002a4339e58060905e5df843e2) · [Delivery artifact](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45237926247/artifacts/14852066306) · [Hosted CI](https://github.com/Hexalith/Hexalith.AI.Tools/actions/runs/45241800150)
- At the same readback, the latest central nightly was the earlier failed run at CiCd `2a8f5254881c93703eb252384f5c3d0d680bdd98`. A passing AI.Tools nightly receipt against delivered `v6.7.0` remained pending. [Latest nightly at readback](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45185339361)
- Reapplied the accepted CiCd `2df38b66a14b72002a4339e58060905e5df843e2` render to AI.Tools parent `91fd549794c72e99d22b69d33ff24e403aede938` in a disposable Git index using the released `v6.7.0` perimeter. The complete tree matched delivered `07c9c0a01ff502040cfb3c29cc9300ce7817ca3b`, including foreign content. Result SHA-256 `484f6b82a3ce2a071aca68e75987b8a1a5d38b7ed2be937f2603626fc8a22322`. The locked renderer check passed with that pin (log SHA-256 `c67cb121bbae9b713cd6100517688ab6c3213075a7dfd04f4437ee1455101762`). The standalone Builds checker passed on checkout `d299ce98bfb60189a2f724d573e74bd25f7cf88d` with the direct `v6.7.0` gitlink (log SHA-256 `7abbc37921cb15ec007c157b0036da245fd917d2cbecf7848e7c2f3a431c45ee`). The authenticated delivery archive hash matched the readback above and recorded `application: pushed` at the same module commit, with no reasons. [Delivery artifact](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45237926247/artifacts/14852066306)
- Manual Nightly `45276260491` attempt 1 ran on `main` at `2df38b66a14b72002a4339e58060905e5df843e2` with `qualify-bump` false. The authenticated `hexalith-nightly-dispatch-1` archive `14868020706` (SHA-256 `f5bd1a955b2bf6008943077a8bad8f449a2ecd4d13968ddf284ff4a46a7e84b4`) identifies Builds `v6.7.0` at `763fc0e937413cb44e533391e573c43640263b40` and dispatches AI.Tools release run `45276512877` attempt 1 on `d299ce98bfb60189a2f724d573e74bd25f7cf88d`. The release run succeeded and its `hexalith-release-outcome` archive `14868036116` (SHA-256 `2213a8793cb4cd6403ac04e12daa80788772a3703308d779fd999a03fa490cb0`) reported `ready` for original draft `449697813` (`v1.0.0`) at saved source `3a4a78d91b36849c4700e8bc9aae74a1b91f2fba`. [Dispatch artifact](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45276260491/artifacts/14868020706) · [Release outcome](https://github.com/Hexalith/Hexalith.AI.Tools/actions/runs/45276512877/artifacts/14868036116)
- Independent scan `45276303430` attempt 1 passed the AI.Tools row at the exact dispatch commit `d299ce98bfb60189a2f724d573e74bd25f7cf88d`. The deciding `hexalith-nightly-scan-1` archive `14868790288` had SHA-256 `d066b1ac5c43c3578e63b42e9be28aa28aab99332c7edde7a2e04ea3b3002d6f`, no run-level errors and no duplicate findings. [Scan artifact](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45276303430/artifacts/14868790288)
- Central `publish-ready` failed AI.Tools with `verified package publication is unavailable`. The immutable Builds `Github/lib/release_publish.py` blob `d9480baac2ea567de22efa7c9ef13d29b646135f` calls `ensure_package_publication` before attempting publication for every release. CiCd's `tools/nightly_publish.py` blob `00b7173251ad83a02b8f2cd90abe20ae19c0d2ab` passes the authenticated ready-draft identity to that finalizer without a package-publication document, and the approved AI.Tools configuration has no package targets. Authenticated GET requests for the published release and tag ref both returned HTTP 404 at `2026-11-23T22:34:54Z`. [Publish job](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45276260491/job/138064195112) · [Builds finalizer](https://github.com/Hexalith/Hexalith.Builds/blob/763fc0e937413cb44e533391e573c43640263b40/Github/lib/release_publish.py#L399)
- The unmodified `tools/nightly_acceptance.py` blob `afa017ecb81c78fd3bb6437c72c69fdcb0be57f7` exited 1 for `--run 45276260491 --module Hexalith.AI.Tools`. It accepted the scan row and reported both failed `ready` publication and a source mismatch. The authenticated original draft source is an ancestor 15 commits behind the dispatch head, and the reader requires equality. The report SHA-256 is `72852fd38e56591c724da9e6810e787257fdb07d63d3d6c52c04b19c4677e91f`. The compact receipt SHA-256 is `de998f30c77a2620bce923b675873f0bdb9e717e992cc69eb723be16ee97b97c`. The release acceptance gate remains open. [Acceptance receipt](../evidence/12/nightly-receipt-45276260491.json) · [Final nightly artifact](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45276260491/artifacts/14869501497)
- Fresh AD-21 readback confirmed the active CiCd App is set to `all`, the release environment permits only `main` and contains zero secrets, and immutable releases are enabled. AI.Tools has 90-day Actions retention and receives only the two registry pull secrets through Actions and Dependabot. The exact delivered AI.Tools tree has no package, container, .NET, tool-only npm or custom action files. The approved package-free scope applies to the requested Zot push pair, NuGet policy and waiver transfer. [AD-21 applicability decision](../../../planning-artifacts/architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md#ad-21--onboarding-sequence)
- At `2026-11-23T22:38:09Z`, the authenticated Codex connector settings page showed the saved `all` mode with Save disabled. The exact comparison with the 48 unrelated repository names from the Story 11 receipt plus `Hexalith.EventStore` failed. The compact readback SHA-256 is `c64569da8297b261fb972be9d7676424df139c488fd113282b8f1e4b422c0fe5`. The maintainer profile's `GET /user/installations/77847816/repositories` returned HTTP 403 and reported the missing `read:user` OAuth scope. [Connector settings](https://github.com/organizations/Hexalith/settings/installations/77847816) · [Expected repository inventory](../evidence/11/ad-7-ad-21-maintainer-repair-20261122.json)
- The interactive maintainer readback for this re-drive again found the CiCd App set to `all`, exact active no-bypass rulesets, a main-only `hexalith-release` environment with zero secrets, immutable releases enabled, a `true` publish switch and 90-day retention. AI.Tools receives both pull secrets through Actions and Dependabot and has access to `HEXALITH_NUGET_USER`. The live tree at `d299ce98bfb60189a2f724d573e74bd25f7cf88d` selects the immutable `v6.7.0` Builds release at `763fc0e937413cb44e533391e573c43640263b40`. Its standalone checker passed again with output SHA-256 `7abbc37921cb15ec007c157b0036da245fd917d2cbecf7848e7c2f3a431c45ee`. The connector API still reports `all`. The repository-list API returned HTTP 403 and reported the missing `read:user` scope. [Repository environment](https://github.com/Hexalith/Hexalith.AI.Tools/settings/environments) · [Connector settings](https://github.com/organizations/Hexalith/settings/installations/77847816)
- The original producer `44266698194` had an overall failed conclusion and a valid build artifact `14410252741`. The archive contains only `release-manifest.json` and authenticates to SHA-256 `e34869ffcbfdcc701d16ea4e375d8a46d3b24bc9c9ea97d1c23f4fd28cfc9033`. Draft `449697813` still has the uploaded 310-byte publication asset `784721641` with an empty package array and SHA-256 `163acdf2042c61ed9ce6d20721330291e23a230b25ec0edc9baa23b5bfdff270`. GitHub's authenticated compare identified the original source as an ancestor 15 commits behind the dispatch head. [Original run](https://github.com/Hexalith/Hexalith.AI.Tools/actions/runs/44266698194) · [Original artifact](https://github.com/Hexalith/Hexalith.AI.Tools/actions/runs/44266698194/artifacts/14410252741)
- The repaired reader rejected historical nightly `45276260491` with exit 1 and reason `ready release was not published by this run (publication failed)`. Initial verification output SHA-256 `eea140f8d3231b89939d6cefec7932d313b3949046c5a0430ea831bb66f4e377`. The next pre-fix nightly `45283314675` also failed `publish-ready` and made no pin bump. [Historical nightly](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45276260491) · [Pre-fix follow-up](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45283314675)

## Review Triage Log

### 2026-11-24 — Review pass

- Verdicts cover 20 findings — high 4, medium 11, low 0, false 5, maybe-false 0.
- Findings
  - `[false]` `[reject]` The fixture could stand in for a released Builds publisher — the tag is authenticated for the existing ready contract and the additive published contract is tested at its own source. The required release, delivery and hosted gate stay open.
  - `[high]` `[patch]` A rerun can supersede acceptance proof reads — confirm the run and attempt after reading the outcome and publication evidence.
  - `[high]` `[patch]` The pre-finalizer run check leaves time for a rerun — repeat it at the publish adapter immediately before PATCH.
  - `[medium]` `[patch]` Historical exact-head ready acceptance required a newer asset contract — use the authenticated nightly's publication verdict for that existing path.
  - `[false]` `[reject]` Editable release notes weaken proof — the immutable asset anchors producer and artifact identity. Missing or conflicting markers fail the row as required. [GitHub release editing rules](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository#editing-a-release)
  - `[medium]` `[patch]` Acceptance accepted invalid payload paths and coerced hashes — apply the v1 package record rules, including exact digest types and case-folding checks.
  - `[medium]` `[defer]` The stale-draft no-op carries the old source SHA — the existing reducer and exact-head outcome rule predate this repair. The current live draft follows the ready path.
  - `[medium]` `[patch]` The fixture did not exercise the archive-to-draft inventory check — test matching archive metadata and an empty draft with an incompatible original inventory.
  - `[medium]` `[patch]` The receipt did not connect an outcome artifact to its module — record the outcome ID and digest with the module proof.
  - `[false]` `[reject]` The review transition closed the hosted blockers — the checklist retains them and the terminal result records each open gate.
  - `[high]` `[patch]` A draft asset may change before publication — verify the immutable release retains the same uploaded asset ID, byte count and digest after PATCH.
  - `[medium]` `[patch]` A numeric 40-digit tag object caused an exception — require a string SHA before walking a tag object.
  - `[medium]` `[patch]` Invalid payload map values could be treated as evidence — test matching byte metadata with malformed package records.
  - `[high]` `[patch]` A newer rerun's outcome may be attributed to an earlier attempt — add the post-proof run readback with a dedicated rerun case.
  - `[medium]` `[defer]` A stale-draft deletion may fail the exact-head check — retain the same deferred producer issue above.
  - `[medium]` `[patch]` The acceptance binary request was not proven through the GitHub adapter — execute the older-source verdict with a fixture that serves asset bytes only for the binary header.
  - `[medium]` `[patch]` The refusal test only corrupted bytes — add a conflicting artifact identity with correctly recomputed byte metadata.
  - `[medium]` `[patch]` The published artifact test could lose the added outcome fields — assert the draft ID and last tag in a successful upload from the composite path.
  - `[false]` `[reject]` The installed-tag producer does not yet emit the local patch's fields — this is a verified rollout dependency. The story already requires the newer immutable pin and an eligible hosted run.
  - `[false]` `[reject]` The local diff has no new package provisioning or registration — authenticated live state confirms the approved package-free registration and adoption. This re-drive repairs the shared release path and retains the live acceptance requirements.

## Auto Run Result

Status: blocked

Blocking condition: hosted acceptance requires an authenticated settings
reload showing the exact 49-repository Codex connector selection and an
eligible nightly pass against the immutable Builds release containing the
repair, delivered to AI.Tools. The connector still reports `all`. The
maintainer profile's repository-list API refused the read with HTTP 403
and reported `read:user`. The newest released and delivered pin at this
check is `v6.7.0`. This unattended build-auto run produces local commits.

The CiCd publisher authenticates the original empty build archive and the
existing publication asset. It rechecks the correlated attempt before
publishing the same draft and verifies asset retention on the immutable
release. Nightly acceptance verifies the older source against the exact
correlated attempt, original producer, archive digest, ancestor relation,
immutable release and peeled tag. Existing exact-head checks cover dispatch,
CodeQL and scan.

- `tools/nightly_publish.py` blob `a54a0c617585a1a0b6914859b7566b3de94d2d25` enforces the draft publication checks.
- `tools/nightly_runtime.py` blob `92d4025f64153afe92a779f42914f9d3d31dad66` supplies bounded, scoped archive and asset reads.
- `tools/nightly_acceptance.py` blob `a0e8b452c35a05af0e09ee4919c2dcc8836a9053` records verified older-source provenance in the module receipt.
- Builds commit `52e6ad6e9c36bd03014b59298e3af3e9c6735262`, tree `7629fa25d7ffa049ea5dee4d9db10c943e28f0bf`, preserves draft identity in published outcomes. The publisher blob is `49febc747d26bf27ef3729b0892f2c37e8e907a0`.
- CiCd and Builds tests cover the historical compatible path and refusal for wrong archive or asset identities, missing proof, reruns, ancestry and release/tag mismatches. The clean-checkout instructions include the authentic `v6.7.0` nightly fixture.

Review applied three high and eight medium patches after grouping. The
deferred stale-draft no-op case predates this re-drive. The triage log records
the rejected findings. A follow-up review is recommended because GitHub's
post-publication asset readback and the corrected older-source acceptance
still need to pass together in a fresh hosted run.

Verification used Python 3.12. The locked renderer check exited 0 with
empty output. The acceptance suite passed 47 tests (output SHA-256
`76aec28fc969fd9a7ce4fddd33dc244df8a5a9cfc9998d7f6ede9bb204201077`)
and the runtime suite passed 42
(`f084e33402cd004c6366a7676bfa7d6e327441627e929b5c9b4cb2e19ad3c1b1`).
The nightly controller passed 58
(`24fc2748ee47b6be69b53fe236232899890ff92721aed26e395191e36f8b406b`),
the nightly workflow suite passed 34
(`bb964b60013a8ae156bef9586eb27e65bc99cfe2b068da5867219ee1cb17b241`),
and the delivery workflow suite passed 26
(`f9b96ee57b5285ba87467475de915d24d42844231b125e188b188ab7a35b65f6`).
The Builds publisher passed 22, including the composite upload
(`b8f626d03500f1afdadb04f2819e24c10d22d42b42e09c630b449fe5a8bfe9f7`),
and the Builds outcome suite passed 38
(`db1166ad39d94b2a527309f20f3dbf162c1f1c30dca1b3eb397c6b37714d2f47`).
The final reader still rejects pre-fix run `45276260491` for unverified
publication (receipt SHA-256
`27e64f5fd09d4255b955bc098cda2c80ad964093ec9116f06893c5734fc7ba74`).
