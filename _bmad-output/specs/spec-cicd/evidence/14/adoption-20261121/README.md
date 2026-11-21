# Story 14 AD-21 provisioning and adoption, 2026-11-21

The human approved "apply recommended" after a deeper options review (see the
2026-11-21 decision note in the story spec). That approval authorizes this
sequence: maintainer provisioning, registration, App delivery, the
post-delivery product fix, credential cleanup and an on-demand nightly.

The runners were disposable, Agents-retargeted copies of the story 13 runners,
kept in session scratch. Their digests are listed below. No executable code is
committed under `_bmad-output/`. Records larger than the 256 KiB evidence limit
were replaced by summaries that keep the raw record's digest.

## AD-21 step 1, maintainer preconditions (in order)

| Step | Result | Record |
| --- | --- | --- |
| App installation | Agents selected; selected-only scope; nothing pending | [`app-selection-verified.json`](app-selection-verified.json) |
| Stale-state assessment | Five tags with no nuget.org packages or published release: `v1.1.0`, `v1.2.0`, `v1.2.1`, `v1.2.2`, `v2.0.0`. Three unmarked `github-actions[bot]` drafts. Keep `v1.0.0`, `v2.0.1`, `v2.0.2` | [`legacy-tag-assessment.json`](legacy-tag-assessment.json) |
| Stale-state cleanup | Deleted 3 drafts and 5 tags, plus every legacy `.github/workflows/codeql.yml:analyze` analysis (216 deletion requests; the final inventory returns 404) | [`provision-cleanup.json`](provision-cleanup.json) |
| Rulesets | Created exactly `Protect main` (deletion, non-fast-forward) and `v tags` (update, deletion) | [`provision-rulesets.json`](provision-rulesets.json) |
| `hexalith-release` | Created with a custom branch policy for `main` only. The foreign `production` environment is kept | [`provision-environments.json`](provision-environments.json) |
| Own Zot push pair | `hexalith-agents-publish` on `agents` and `agents/**` (read/create/update). Existing htpasswd rows and ACL are byte-identical. Login returns 200; foreign writes return 403. Environment secrets set | [`provision-registry.json`](provision-registry.json) |
| nuget.org policy | Added policy 28307 `Hexalith.Agents hexalith-release`: `release.yml`, `hexalith-release`, `Hexalith.Agents*`, push only, owner/repo IDs 80614290/1277685416. All 23 earlier policies are preserved, including legacy 26964 (`production`, glob `*`) | [`nuget-policy-verification.json`](nuget-policy-verification.json) |
| Scans, switch, retention, grants | Default setup not configured; Dependabot security updates off; switch exactly `true`; retention 90 days; Agents added to the Actions and Dependabot pull pair and to `HEXALITH_NUGET_USER` | [`provision-settings-grants.json`](provision-settings-grants.json) |

Legacy access stays in place until authenticated adoption: `NUGET_API_KEY`,
legacy NuGet policy 26964 and the legacy Zot push.

## Disposable runner and raw-record digests (SHA-256)

- `assess_tags.py` `c65b2a16ff6344ae01d1741a4805f8c8735d447da1f999fba41c2d85e1f988c8`
- `app_selection.py` `1aefb9abdac8abc0cb8b32241dcb55c642bfc255b7ad7d3391d16a0df134ffc4`
- `provision_github.py` `8ed126e3a8792c7953264e976d3ffb90af71849b8133085fba799a4ae96d74fc`
- `provision_registry.py` `cb5de90ff19dc43d95d23a9460de0d9d0782059808b0883a3417c0967717742b`
- `nuget_policy_ui.py` `26348566c76df09da3dd0d016ae6d7f9b46fa51a50c42f3fe74f65911c4de91d`
- `tabs.py` (visible tab titles only) `878dcb011a4800756a47a58aff16d1f8ebf36dec7a24ea86d2db5fad0f6fb30e`
- Raw cleanup record `d4f839ff934e4a50ef0c8e3619ea3d09f85e3447becb6014873d95f8b0d2177d` (13,168,380 bytes)
- Raw grants record `6b94bc3a989fc342450b566c2c55f1bb2e5fc91a52a97158b06e3f87d8a352ca`
- Failed browser attempts before GitHub 2FA completed: open-window `4b00af84…`, observe `245bcacf…`

## Registration, delivery and acceptance

- Registration commit `8e43d8c59b3cc8f2798b2ba8ce90161fc653128f`
  (`build(cicd): register Hexalith.Agents for shared delivery`) is based on
  CiCd `main` `399b2f2d9102649e17b0017c4da26e07e8d4f991`. After provisioning,
  `tools/validate.py` on that commit passed with
  `{"global":true,"modules":[…,"Hexalith.Agents",…]}` (log SHA-256
  `fca59a9747d44e4d74bfe4476c7facad66e2675781c8a1e1ebadd6119700c6ff`).
- The registration and the docs commit `62dc50b18888be88d9ce27415d22f612c55c50af`
  were pushed to CiCd `main` with the CiCd-agent profile.
- Hosted delivery [44886812692](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/44886812692)
  succeeded (validate and deliver green; `failed: false`). It adopted Agents
  as `3406b3cb1f01e01d07bc71980ff15c24a99a29c5`
  (`build(cicd): apply 62dc50b1… from Hexalith.CiCd`, parent `0d03363`). The
  owned files are byte-identical to the render, the Builds gitlink is `v6.4.4`
  and foreign content is preserved. See
  [`authenticated-adoption.json`](authenticated-adoption.json).
- AD-21 step 3 maintainer cleanup, done at once after adoption:
  - immutable releases enabled ([`post-adoption-github-cleanup.json`](post-adoption-github-cleanup.json));
    the first readback lagged the 204 PUT, and a delayed readback confirms it;
  - Agents removed from legacy `NUGET_API_KEY`; it held no other legacy org
    secret, and the pull grants are preserved
    ([`legacy-org-secret-cleanup.json`](legacy-org-secret-cleanup.json));
  - legacy nuget.org policy 26964 deleted, with 28307 and every other policy
    preserved ([`nuget-legacy-cleanup.json`](nuget-legacy-cleanup.json)). The
    second deletion dialog was confirmed in the attended browser rather than
    by the runner; the readback shows the exact result;
  - legacy Zot push is a bounded no-op, as for the pilots: Agents never had a
    legacy Zot path or grant ([`zot-legacy-disposition.json`](zot-legacy-disposition.json));
  - the legacy nuget.org API key's package scope was not observable this
    session (the API Keys URL opened as Trusted Publishing). Story 11 recorded
    that key as expired, and Agents can no longer read `NUGET_API_KEY`.
- Adopted CI [44888639144](https://github.com/Hexalith/Hexalith.Agents/actions/runs/44888639144)
  passed the guard, restore/build and the five floors, then failed only at the
  hook, as the simulation predicted. The module-agent fix `6865c6e6` changes
  only the 39 reviewed version fields. Standalone `check.py` and the hook pass;
  see [`product-fix-6865c6e6.json`](product-fix-6865c6e6.json).
- CI [44889942815](https://github.com/Hexalith/Hexalith.Agents/actions/runs/44889942815)
  on `6865c6e6` is green.
- The on-demand nightly [44890586692](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/44890586692)
  (dispatched on `main` with `qualify-bump` false, CiCd-agent profile) failed
  overall on the scan, `publish-ready` and `bump` jobs and on AI.Tools'
  release. None of these is an Agents row.
  `tools/nightly_acceptance.py --module Hexalith.Agents` judges Agents
  **`pass`** with no reasons ([`nightly-acceptance-44890586692.json`](nightly-acceptance-44890586692.json);
  full output SHA-256 `0c13d1f75caee9b34c0e31ea29173d7598904e4793f5cd6a9e2090e2dc11ab69`):
  - release [44890634855](https://github.com/Hexalith/Hexalith.Agents/actions/runs/44890634855)
    succeeded at dispatch head `6865c6e6` with outcome `published` and version
    `2.0.3`. The full output lists `publication: pending`, but the GitHub
    release `v2.0.3` is published, immutable and bot-authored, and all six
    packages list `2.0.3` on nuget.org;
  - both release CodeQL jobs (C# and JavaScript/TypeScript) succeeded;
  - Agents' row in the attempt's scan job passes.
- Matrix audit: Builds `v6.4.4` (`fe68718b`) `test_ci_config`,
  `test_ci_pipeline` and `test_local_check` ran 114 tests, all OK, with no
  unittest skips (log SHA-256
  `17b738f7552195c79c8b292989661be79ad0a21f60662774ed8a606947fb7002`). They
  include the count-boundary, fail-skips, failure-order, unsupported-policy and
  renderer-default tests. A first invocation from the wrong directory failed to
  import a sibling test module (log `141b58be…`) and is not a test result.
- Still open: Agents `main` keeps the tool-only `package.json`/lock that
  `05ddee8` restored, together with the legacy semantic-release
  planner/publisher, the publish/recover/verify scripts and their tooling
  tests. Their removal awaits a human scope decision.
