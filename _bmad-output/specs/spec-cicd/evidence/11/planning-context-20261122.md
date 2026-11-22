# Story 11 planning context — 2026-11-22

Planning only. Three investigation subagents completed read-only source, continuity and maintainer checks. No remote setting, registry resource, ref, PR, credential, product file, setup, render or Builds pin changed. All later execution tasks remain unchecked. The pre-existing legacy story is `done`; its accepted checkpoint is historical evidence, not an outcome of this invocation.

## Source identities

Full local identifiers obtained directly from Git:

| Repository | Planning HEAD | Tree |
| --- | --- | --- |
| CiCd | `9f7a56fd1e0de05f6b8a8789fba983c072ce3db6` | `3379e0b784c11f45591e1a71df4637aacfb4c9f7` |
| `references/Hexalith.Commons` | `258f9d20e33bd0ae411cf8b3836a26a131f5b9ae` | `a3cbbafafef801a4a8f192db992203b1ffc38b22` |
| `references/Hexalith.PolymorphicSerializations` | `c6d0dfce6dc4f9a0699a51f80baf021ba5ef5d60` | `0206debac908e04439df46ab3d8ac13068a8e4db` |
| `references/Hexalith.Builds` | `3060b20abfcf4ea804ad31816d435e5c754fc129` | `20e305bd6ceebafcf2200d72d1a2f14c2fa8af6e` |

The root baseline always identifies CiCd, not a submodule. If later product work is necessary, the affected path above is its `implementation_repository` and its listed HEAD is the planning `implementation_baseline_revision`; execution must additionally bind freshly fetched actual candidate inputs. Review both module source differences and root differences, not just gitlinks.

`git add --refresh -- .` succeeded and root/submodules were clean. Root branch `main` fits this epic. API-observed live mains during preflight differ from local pins: Commons `5f646d4e49279cca0d31ab577e91719c3ed7e434`; Poly `99c2344f08d3e3560a891f79ab63f8722fa14e60`. These are observations, not freshly fetched execution baselines.

Canonical root blobs at baseline:

| Path | Blob |
| --- | --- |
| `_bmad-output/implementation-artifacts/spec-11-pilot-migration-commons-and-polymorphicserializations.md` | `e71dcb4661c23e6e9a3a06fdc1357215b55afd9d` |
| `_bmad-output/specs/spec-cicd/stories/10-2-agent-instructions-and-deny-entries.md` | `f555b1b9f7104104ad55d63169e70f18088b8de7` |
| `builds-version` | `ecb8b9a7d5cd90f97c08600ef5730590df82cdc4` |
| `setup/Hexalith.Commons.yml` | `e88d5d75586650dad2aa96e8fb1badb06e4d9e41` |
| `setup/Hexalith.PolymorphicSerializations.yml` | `e7eb1038a65e20918180db06cc0c520e9d4872e3` |
| `templates/partials/ownership-block.txt.j2` | `fe59f37fc84bb9b95099b073ef79e479d549fdd5` |

## Maintainer preconditions checked first

Read-only checks completed around 12:01 UTC using command-local maintainer profile `/home/administrator/.config/gh`; authenticated account `jpiquot`, ID `6775094`. Default remains `/home/administrator/.config/gh-cicd-agent`; neither `GH_TOKEN` nor `GITHUB_TOKEN` override was present. Account administrator status was not treated as token permission evidence. No credential values or credential hashes were exposed.

| Requirement | Observed outcome |
| --- | --- |
| Agent App exclusions | **Fail:** `GET orgs/Hexalith/installations` complete seven-entry inventory reports Cursor `182926560` and Codex connector `77847816`, each `repository_selection: all`. Cursor must exclude managed repositories; connector must be limited to modules using it and exclude CiCd/Builds. Claude and semgrep-app absent from this inventory. Preserve unrelated repositories when repairing selections. |
| CiCd App membership | **Unverified:** App `179966090` is selected-scope with required API permissions, but listing exact installed repositories returns 403. Earlier actual deliveries prove historical access only. |
| Stale release/CodeQL state | Earlier provisioning/cleanup is recorded. Fresh complete stale configuration, draft and orphan-tag inventory remains an execution check; do not delete legitimate releases or infer absence. |
| Exact rulesets | Pass: Commons `27356310`/`27356311`, Poly `27356312`/`27356313`; active `main` deletion/non-fast-forward and `v*` update/deletion only, no bypass actors or extra conditions. |
| Publish environments | Pass metadata: each `hexalith-release` accepts only custom branch policy `main`, no reviewer/wait timer; contains exactly `HEXALITH_REGISTRY_USERNAME` and `HEXALITH_REGISTRY_PASSWORD`, timestamps unchanged since 2026-11-16. GitHub cannot reveal stored values, so binding still relies on original provisioning receipt. |
| Own Zot push identities | ACL read pass: `hexalith-commons-publish` only `commons`/`commons/**`; `hexalith-polymorphicserializations-publish` only `polymorphicserializations`/`polymorphicserializations/**`; each read/create/update, neither in adminPolicy. ConfigMap `distribution-registry-config`, namespace `registry-distribution`, context `jpiquot@local`, resourceVersion `49008107`. No registry mutation or credential use. |
| Scoped NuGet policies | Historical persisted reload verified Active push-only `27048` (`Hexalith.Commons*`, repo ID `952960148`) and `27049` (`Hexalith.PolymorphicSerializations*`, repo ID `957156862`), owner Hexalith ID `80614290`, `release.yml`, `hexalith-release`. Added beside legacy policies, then legacy `20233`/`20232` removed. **Current scope unverified:** no connected authenticated NuGet document session. |
| Scan/security/release settings | Pass both: CodeQL default setup `not-configured`, Dependabot security updates false, push protection enabled, release switch exactly `true`, immutable releases enabled, retention 90 days. |
| Organization settings | Pass: retention 90 days, default workflow permission read, fork approval all external contributors. |
| Required grants | Actions and Dependabot pull pairs plus `HEXALITH_NUGET_USER` select both pilots. Complete selected-org-secret inventories exclude both from `NUGET_API_KEY`, `HEXALITH_ZOT_*`, `AZURE_*`, `SONAR_TOKEN`. Repository Actions/Dependabot and old `production` environment secrets empty. |
| Legacy key/Zot cleanup | Earlier accepted bounded Zot no-op: package-only pilots had no tracked container publisher/legacy grant. Legacy key `954800` was Expired; its mapping to the GitHub secret was never proved. Current package/key scope remains unverified. Do not revoke global administrator identities, invent a key mapping or claim a fresh removal. |

Exact membership failure: `GET user/installations/179966090/repositories?per_page=100` returned HTTP/2 403, request ID `D291:36376F:10FFAFE8:19B812ED:6B02D9B9`. Response requires an authorized installation/user access mechanism. Response accepted scopes were `read:user,user`; profile reports `admin:org,gist,read:packages,repo,workflow`. Required access is authenticated installation-selection/settings visibility; absence was not established. Use an available authorized interactive settings surface or report the access boundary, without obtaining the App key or broadening the module token.

Historical administration sources: `provisioning-status.md`, `nuget-policy-verification.json`, `nuget-cleanup-verify-cleanup.json`, `post-adoption-cleanup-plan.md`, `zot-pilot-legacy-disposition.md`, `post-adoption-github-cleanup.json` beside this file. Existing oversized/raw evidence is not copied into new records.

## Product and dependency disposition

Original `planning.md:132` inventories no NU190x waivers or `.husky/` in either pilot. Both tool-only npm manifests/lockfiles are gone. Do not invent removal work. Commons' NU5104 packaging warning treatment is separate; CI packaging audit-off flags are not release audit waivers. Keep release auditing enforced.

Commons hook runs its three package scripts and validates twelve payload/symbol pairs plus isolated consumers. Poly now has its own README-sample product hook, added after initial adoption. Both setup files select their `.slnx` and `after-unit-tests`. Preserve later improvements rather than reverting to original no-hook Poly setup.

Initial generic feed-publication verification shipped in acceptable Builds `v6.0.6`, canonical commit `fdda17c0a4538b0f7c99f813c20ca24b49006530`, release run [43838534329](https://github.com/Hexalith/Hexalith.Builds/actions/runs/43838534329). Current `builds-version` is `v6.6.1`, tag commit `27fe4d62ca1f3cce07a9f19e1e30b02cbaa51357`, distinct from the root's Builds checkout. Reauthenticate release acceptability before relying on it for new changes; use exact tagged policy/schema/runtime. Any genuinely needed module audit waiver goes in Builds `Props/` through CiCd-agent and must be present in the selected released pin before adoption. For these already adopted pilots, normal standalone checker qualification is mandatory before a new push; the legacy approved preparation substitute has ended.

## Actual restricted-token timeline

Historical objects below were verified directly with Git commit/parent/tree inspection. Evidence names the protected module-token source. No probe or ref operation was performed during planning.

| Identity | Commons | PolymorphicSerializations |
| --- | --- | --- |
| Pre-delivery current-main base | `ab5e92faa3bab1fa43b8ecadd423432dfe652bb2` | `476cfccac3c5ba694a8e0ef11b1157728b9ec093` |
| Product-only pre-delivery head | `e3d4da366a2e8c6b6216f4a7b57c15241313da79` | `dbea7efd64ec75e2b92920665cb1ebffda15fa88` |
| Disposable PR | [52](https://github.com/Hexalith/Hexalith.Commons/pull/52) | [19](https://github.com/Hexalith/Hexalith.PolymorphicSerializations/pull/19) |
| Preparation parent of adoption | `a83959832ebdad9fe5a5ea268fb0224c49cfa8ea` | `c547c763a20e1fbf6b7a5c9d3b4791260fb61149` |
| Actual adoption commit | `5169f6b6165482d4b1499ccc5958eb897101be4f` | `49fbe97f7224e2795ffb3293330d9efde6c0f561` |
| Adoption tree | `e1bfdb71421d68e5fd9e706afc5dd255f5bc8a40` | `704aa5df44841f882e45b77f9110cdb10e80222d` |
| Fresh post-delivery product head | `47d51c025ec2413ad758d74b552772fcd275e446` | `1a2e079a7e1d77beb71a3ec09f7ca5fd175ae591` |
| Actual Update branch resulting head | `517c1af6036e7a0074a8ea5cf081f1046c6f58fe` | `e571f080f58f80519786063ada4f60a236cf1efb` |

Real App delivery [43860977581](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/43860977581), source `f002539f6fbaddaa9b621a9cbf75a1263eee5dea`, adopted both pilots. Fresh product heads each parent the actual adoption and were successfully pushed with the restricted credential after normal checker success. Both meaningful Update branch operations returned **HTTP 202**; resulting parents are exactly `[pre-delivery probe, actual adoption]`. Actual adopted workflow/owned bytes, modes and gitlinks imported exactly; only `pilot-ci-probe.md` differs from adopted main. Both PRs closed unmerged; all four remote probe branches and local refs were removed with exact-SHA guards.

`post-adoption-fresh-branch-outcomes.json` has stale `remote_push_performed:false` metadata alongside `push_attempted:true` and `push_confirmed:true`. Successful push/readback/deletion evidence and `resume-prior-acceptance-audit.json` explicitly resolve that inconsistency. Preserve it as an annotated historical defect, not a reason to invent missing pushes.

The updated probe merge heads failed strict commitlint on service-generated merge subjects (`subject-empty`, `type-empty`); product stages did not run on those heads. Codacy passed. This establishes server allowance plus a commit-message compatibility limit, not product-green evidence or a token refusal.

The factual scoped correction is already canonical at `templates/partials/ownership-block.txt.j2:25` and in 10-1/10-2 dated addenda. It was published in `3427f041c5f686c460c1fa027cf6f835791209c1` and actually redelivered by [43869480499](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/43869480499). Keep the distinction: GitHub permits Update branch workflow imports; agent instructions prohibit using it to import owned CI/CD and require a freshly fetched current-main product branch.

## Existing nightly acceptance

Legacy acceptance dated 2026-11-19 names [44566082537](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/44566082537), attempt 1, `workflow_dispatch`, `qualify-bump:false`, source `6b413de903926c52a355472f018d3ebcdbc8e144`. Both pilot rows and pilot checkpoint pass; bump no-change and keepalive pass. Commons release [44566233481](https://github.com/Hexalith/Hexalith.Commons/actions/runs/44566233481) and Poly release [44566277325](https://github.com/Hexalith/Hexalith.PolymorphicSerializations/actions/runs/44566277325) reported nothing to release with successful Release CodeQL and scan rows. Unrelated failed rows stay recorded, not decisive for pilot verdicts. Read-only rejudgment is planned; no new nightly was dispatched.

All 29 other id-keyed story files were loaded for continuity: 218 execution checkboxes checked, zero unchecked. Later completion addenda supersede historical Auto Run Result planning/blocked entries. SPEC and all companions were investigated. No runtime change is justified solely by reconciling story placement. Missing access to evidence remains unverified; it does not erase previously authenticated history.

## Evidence SHA-256 identities

Paths below are relative to this directory. Digests were computed during this planning run; existing files remain unchanged.

| Source | SHA-256 |
| --- | --- |
| `pre-delivery-probes.json` | `6f49e6d41cbd4da49a86472b9feeb8d773ab4f0237db500abb930761da0516b4` |
| `authenticated-adoption.json` | `82097ebc568d76d0d9251ecf17e66e8be2f596b36433f7ce5a9516b2b4ce99e3` |
| `post-adoption-fresh-branch-outcomes.json` | `8ad437da41b01c27482fc7967dc7f2577951502f8c7dc49ff7243eae79d09fba` |
| `post-delivery-update-branch.json` | `ac6b49453e512941424057c6a8d40209adc54c0110acd438bf0ccd41775047ed` |
| `product-probe-cleanup.json` | `1ff61047132d4f2d5d2e2accb710fce114d0460d12654b40f3b62e4a29c76c64` |
| `nuget-policy-verification.json` | `c84f74706313909892c9fc60138f49ace5911c4aaaacf0c9c61c259bb51b108f` |
| `nuget-cleanup-verify-cleanup.json` | `77e81a82b760409368ac0b33ab77d49918e2a455efd7a2e59b7400cd65218317` |
| `resume-prior-acceptance-audit.json` | `319c85713afa215212c19ad854f04194355d53b9066adc3ae5a0b6005bd15bb7` |
| `pilot-checkpoint-receipt-44566082537.json` | `88ad73321566120dfa2421c3bf58e3a1df60b408a3afe676fa4abdfffec3a016` |
