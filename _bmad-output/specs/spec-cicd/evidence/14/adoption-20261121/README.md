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
- Delivery, the post-delivery product fix, credential cleanup and the nightly
  are pending; this section is updated as each completes.
