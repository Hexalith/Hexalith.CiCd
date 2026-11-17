---
title: '11 — Pilot migration: Commons and PolymorphicSerializations'
type: 'chore'
created: '2026-11-15'
status: 'in-progress'
baseline_commit: '37e73a99dfe82c3b7741554d6f4ff2207711644b'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/specs/spec-cicd/evidence/11/planning.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Both pilots still use legacy pipelines. Adoption must preserve product checks and establish real delivery, restricted-token behavior and nightly release evidence.

**Approach:** After stories 10-1/10-2 and AD-21 preconditions pass, prepare product changes, release shared publication verification, register/render both modules, and let App delivery adopt them. Accept only after the real-night pilot checkpoint.

## Boundaries & Constraints

**Always:** Follow AD-21 ordering and the gate rule. Use the protected module token for module product writes and probes; CiCd-agent for CiCd/Builds; command-local maintainer profile for authorized administration. Preserve SDK pins, all product tests and foreign instruction/settings content. Use disposable verification workspaces under `run-with-temp`; save evidence outside scratch.

**Never:** Directly edit module-owned-perimeter files, obtain the App key, initialize nested submodules, weaken checks or duplicate-scan policy, adopt another module, manufacture delivery/nightly evidence, or merge probe PRs. Only delivery/restore writes owned files. Remove legacy credentials only immediately after actual adoption.

**Human decisions, 2026-11-15:** This session owns 10-2 after 10-1 and then resumes story 11. Required provisioning is authorized through existing authenticated access; report concrete access failures separately from authorization.

**Human decision, 2026-11-16:** The human completed Microsoft/NuGet authentication and explicitly approved the documented pre-adoption verification proposal ("1 done, 2 approve"). For product-preparation pushes to these two pilots before App adoption only, replace the unavailable shared checker with package-mode product builds/tests and applicable package/consumer checks, policy and commit validation, and byte/mode/gitlink comparisons proving all owned content unchanged from freshly fetched main. Save exact inputs and outcomes before each push. After actual App adoption, the normal `python3 references/Hexalith.Builds/check.py` requirement applies. This exception grants no owned-file edits, nested-submodule initialization, test weakening, alternative credentials or probe merges.

**Deferred check:** The human accepted 10-1's three verified outcomes and cleanup as the prerequisite handoff. Create a restricted-token product-only probe branch/PR before real delivery; after delivery changes main's workflows, test that PR's Update branch and repeat fresh-main product branching. Keep 10-2's temporary prohibition until the actual result establishes its behavior. Record exact revisions, outcomes and cleanup before pilot acceptance.

## I/O & Edge-Case Matrix

| State | Expected behavior |
| --- | --- |
| Missing dependency, policy or credential | Stop before adoption; record the unmet prerequisite. |
| Disabled Dependabot response | Accept boolean `enabled: false` or authenticated legacy 404 after administrative preflight; reject enabled/malformed/error responses. |
| Package indexing delay or conflicting existing version | Bounded retry for transient absence; mismatched ID/version/source fails before GitHub publication. |
| Delivery race or failed module | Existing bounded forward-only delivery applies; retain per-module report and do not claim adoption. |
| No Builds update or releasable change overnight | Record authenticated no-bump/nothing-to-release outcome; do not force a release. |

</frozen-after-approval>

## Code Map

- `evidence/11/planning.md` under the main spec folder: exact revisions, preflight, API failure, gate assessment and command details; `preflight.json` and `dependabot-disabled-probe.log` substantiate it.
- `tools/deliver.py:app_checks`, `tools/tests/test_deliver.py`: disabled-response compatibility; preserve permission checks.
- Builds `Github/lib/release_publish.py`, `release_draft.py:package_identity`, `tests/test_release_publish.py`: authenticated package inventory, publisher and shared regression coverage.
- Builds `Github/lib/tests/test_release_complete.py`: actual recovery-to-publication fixture, sharing the local feed adapter while retaining byte identity, retry outcomes and credential-boundary assertions.
- Commons `scripts/{pack-release-packages,validate-nuget-packages,validate-consumer-package-references}.py`: distinct product package/consumer checks.
- Both modules `tools/{verify_nuget_release,test_verify_nuget_release}.py`: duplicated post-publication checks to hoist, then retire.
- `tools/render.py`, `tools/check_global.py`, `tools/validate.py`, `docs/nightly.md`: reuse rendering, committed-candidate checks, live validation and observation.

## Tasks & Acceptance

**Execution:**

- [x] `evidence/11/` — recheck completed predecessors and document AD-21 provisioning: App scope, stale release/tag assessment, exact main/v* rulesets, main-only release environment, module push identities, scoped NuGet policies, org grants and security/retention settings. Preserve existing publication access until adoption.
- [x] `tools/deliver.py`, `tools/tests/test_deliver.py` — handle the observed disabled response; test false/true/malformed/404/authorization-error cases and sibling isolation.
- [x] `references/Hexalith.Builds/Github/lib/release_publish.py` and its tests — add generic bounded live NuGet verification before finalization, reusing authenticated inventory and package identity parsing; preserve missing/indexing-delay/source-conflict coverage. Release through the interactive shared pipeline and await an acceptable tag before adoption.
- [x] Both module `tools/` and root `package.json`/lockfile — after shared coverage exists, retire duplicated legacy verification code/tests/manifests and tool-only npm files using the module token. Let delivery remove owned legacy configuration/workflows.
- [x] Commons `.github/actions/after-unit-tests/action.yml` and its three package scripts — retain payload/symbol and isolated-consumer checks without another module build/restore; fix consumer SDK/cache isolation and CI audit-off/package flags. Test real package consumption; preserve all C# suites.
- [x] `builds-version`, `setup/Hexalith.{Commons,PolymorphicSerializations}.yml`, `rendered/`, direct gitlinks — pin released shared behavior, use each `.slnx`, enable Commons' hook and default C# analysis. Before adoption, create the disposable product-only probe branch/PR from current module main and record base/head. Render and validate one committed candidate before pushing; hooks must already exist on live main.
- [ ] `evidence/11/` — authenticate both delivery commits/refs/reports; immediately enable immutable releases and remove other NuGet policies and legacy secret/key/Zot access. Record green CI, the scheduled night and post-delivery branch/Update-branch outcomes; clean probes and confirm/correct 10-2 restrictions.

**Acceptance Criteria:**

- Given satisfied prerequisites, when delivery adopts the pilots, then both owned trees match accepted perimeters and product files/tests remain intact.
- Given missing or wrong-source published packages, when shared publication verifies the feed, then it cannot report successful GitHub publication.
- Given adopted main revisions, when restricted-token branch probes run, then actual server outcomes and complete cleanup are recorded without owned-file edits or probe merges.
- Given green pilot CI, when one real scheduled nightly finishes, then CodeQL, releases or valid no-release outcomes, scan, Builds bump/no-bump and delivery are evidenced before checkpoint acceptance.

## Implementation Notes

- Current resume checkpoint, 2026-11-17 13:18 UTC: a read-only CiCd-agent
  observer is sleeping until `2026-11-18T02:16:00Z`, then will bind the
  earliest genuine `nightly.yml` schedule event on main at/after
  `2026-11-18T02:17:00Z` attempt 1. Manual dispatch/rerun remains forbidden.
  A systemd backup is armed at 02:20/11:00/16:00 UTC and cannot take the
  flock while this observer holds it. Authentication uses
  `authenticate-scheduled-20261118.py` after the parent is terminal. The last
  execution task stays unchecked and story 11 stays open.
- Prior resume checkpoint, 2026-11-17 13:10 UTC: the Commons package-hook
  discovery fix is on live main as `d551e5f3b67653b8793f86afedab355c8a3821da`,
  sole parent `aa694ae3d43f1645f741ae0844987ca2e7e0d347` (the 17 Nov scan
  head). The exact spec diff was applied from freshly fetched origin/main;
  owned workflows/config/gitlink/instruction bytes were unchanged. Released
  `v6.2.0` commitlint accepted the message. `python3 references/Hexalith.Builds/check.py`
  exited 0 in a standalone job root with the committed gitlink worktree
  (`0ccd12af6576a3aac601340dec7dba53e86768c3`). All eight C# suites passed
  (9+16+16+9+21+14+70+202=357, zero skipped). The rewritten pack/validate/
  consumer scripts produced twelve payload/symbol pairs and a successful
  isolated consumer. Local-script discovery on that head reports zero errors
  and the same four selected files. Protected-token fast-forward push to
  `main` was confirmed; GitHub CI `44089607938` attempt 1 succeeded on that
  exact source, including the live hook lines. Poly needed no product change.
  Conversations discovery remains out of scope. Manual dispatch/rerun remains
  forbidden. Story 11 stays open for the genuine 2026-11-18 02:17 UTC night.
- Prior resume checkpoint, 2026-11-17 12:50 UTC: the genuine scheduled
  parent is authenticated as run `44067556763`, event `schedule`, attempt 1,
  source `639d8a7032108bbc7eb1f0e054c4ee55b6f87f90` (descendant of diagnostic
  fix `d04c9ab7` and final pilot policy `3427f041`). GitHub started it at
  10:44 UTC rather than 02:17 UTC. No later same-day schedule run exists and
  none was substituted. Digest-matched artifacts show the night failed in
  dispatch because the 30-minute delivery barrier never cleared: concurrent
  main `deliver.yml` pushes and the 11:14 UTC hourly run stayed busy through
  11:19 UTC, so no Commons, Poly or Builds release was dispatched and this
  night produced no CodeQL or publication outcomes. Keepalive passed and
  Builds bump reported authenticated no-change for `v6.2.0`. Scan covered
  both live pilot heads with jscpd 5.4.3; Poly passed with zero files, while
  Commons failed local-script discovery on this story's package hook
  (`mktemp`/`rm` and computed subprocess env/cwd). Conversations also failed
  discovery and is out of this story's product scope. Direct CodeQL
  inventories still return HTTP 403 (`security_events=read`). Diagnostic
  delivery `43889937298` completed success with both pilots application
  unchanged. A local Commons discovery-only fix
  (`scheduled-20261117-commons-scan-fix.diff`) clears those four errors
  without changing the selected file set; it is not pushed because
  `python3 references/Hexalith.Builds/check.py` has not been run on that
  head. Manual dispatch/rerun remains forbidden. Story 11 stays open.
- Prior resume checkpoint, 2026-11-16 14:50 UTC: diagnostic fix
  `d04c9ab7a8fa43dc6dac1f15d34135aba8e79551` passed all 14 suites/399 tests,
  the complete unchanged committed/global/live-module gate and released shared
  commitlint, then was pushed using CiCd-agent. Actual push-created delivery
  `43889937298` is in progress; no completed delivery outcome is inferred.
  The prior exact candidate also passed 399 tests, but a concurrent main advance
  was caught before any push. Final qualification preserves that main's story
  evidence/gitlinks and the unchanged original index. The one-shot observer is
  enabled for 2026-11-17 02:20 UTC (03:20 Paris), waiting for the genuine
  02:17 UTC schedule event and then resuming acceptance and full-story BMAD
  review. It uses only CiCd-agent, performs no manual dispatch/rerun and cannot
  close this story without all criteria passing. Direct CodeQL inventories are
  separately unverified: both return actual HTTP 403 requiring
  `security_events=read`; exact scheduled upload, completed processing and
  security-gate evidence must establish CodeQL or the criterion stays open.
- Resume, 2026-11-16: the requested failed scheduled run `43842471669`
  predates pilot adoption and contains no registered modules. Its authenticated,
  digest-matched publish-ready artifact identifies an anonymous
  `GET /repos/Hexalith/Hexalith.Builds/releases/tags/v5.2.2` HTTP 403 during
  trusted-source initialization, before any publication mint. The original
  transport discarded response bodies and headers; permission denial versus
  rate limiting cannot be established retrospectively. Fresh anonymous and
  existing CiCd-agent reads both return 200 for that exact public release.
  Fix only the confirmed diagnostic loss in `tools/nightly_runtime.py`, with
  bounded/redacted response evidence and unchanged retry, credential and trust
  policy. `tools/tests/test_nightly_runtime.py` covers rate-limit versus
  permission responses, refusal/no-write-retry, redaction, bounded/unreadable
  bodies and retry-budget exhaustion. The exact scheduled checkpoint remains
  pending for 2026-11-17 02:17 UTC (03:17 Europe/Paris); no manual dispatch or
  future success is inferred. Original approvals and baseline remain intact.
- Current execution checkpoint, 2026-11-16 13:06 UTC: real delivery run
  `43860977581` succeeded and both App adoptions are authenticated by report,
  digest, accepted refs, sole preparation parents and complete tree comparisons.
  Immutable releases and immediate legacy-policy/no-op credential cleanup are
  verified; both adopted-main CI runs pass all 372 C# tests, Commons package and
  isolated consumer checks. Both normal-checker-qualified fresh-main product
  pushes succeeded, and both meaningful Update branch requests returned 202
  with actual delivered-tree imports. Probe PRs closed without merging and all
  probe refs are removed. The factual scoped policy follow-up
  `3427f041c5f686c460c1fa027cf6f835791209c1` passed its full locked gate
  and is pushed. Real delivery `43869480499` is successful and authenticated,
  both final-main CI runs pass, and both original module checkouts are clean on
  those delivered mains after guarded ordinary checkout/fast-forward. Only the
  genuine scheduled-night checkpoint remains pending. Earlier
  checkpoints below are retained as history and do not override this state.
- The predecessor recheck confirms 10-1 and 10-2 are done; the approved deferred
  Update branch qualification and temporary prohibition remain intact.
  [Implementation readiness](../specs/spec-cicd/evidence/11/implementation-readiness.md)
  distinguishes completed local source work from outstanding provisioning,
  publication, adoption and live-night acceptance.
- Delivery accepts boolean `enabled: false` and authenticated legacy 404 after
  administrative preflight, while rejecting enabled/malformed/authorization
  responses with sibling isolation. The API rejects successful JSON `null` on
  absence-enabled reads, so it cannot be mistaken for 404 absence; other
  consumers retain their existing response-shape and identity diagnostics.
- Builds now verifies the authenticated inventory on the live NuGet feed
  between push and GitHub finalization, with bounded pending-package retry and
  reused ID/version/source parsing. Publisher regressions pass on Python 3.12
  and runner Python. At the initial local checkpoint no shared release had been
  published, so the composite release task remained unchecked and legacy module
  copies were retained. The subsequent completed release is recorded below.
- Added Commons' package/consumer hook and CI packing flags; the isolated
  consumer uses its unchanged SDK pin and cleans its private NuGet caches.
  Both pilot package-mode builds, all 372 C# tests across nine suites, all twelve
  Commons payload/symbol package pairs and real isolated consumption passed.
  The existing payload/symbol validator and all C# tests remain intact.
- Initial local preparation performed no module adoption, owned-file edit,
  probe branch/PR, remote mutation or credential cleanup. Protected-token fetches refreshed the local
  module checkouts to current remote mains. Production setup/render and the
  Builds version pin remain unchanged.
- The initial provisioning attempt was blocked before its first step: the intended maintainer API
  cannot enumerate the App installation's selected repositories (HTTP 403), and
  the existing signed-in browser requires human **Confirm access** at the
  installation settings. Its selection remains unverified. No authentication
  bypass or access broadening was attempted; the browser stays on that prompt.
- Before the subsequent human decision, product-preparation pushes had a separate prerequisite failure:
  `python3 references/Hexalith.Builds/check.py` exits 2 in both pilot roots
  because the nested script is absent. Current shared local checking also
  requires the adopted configuration, which does not exist yet. The recorded
  package-mode results did not replace that then-mandated command. No nested
  submodule or owned-file bootstrap was created to bypass it; a pre-adoption
  check/bootstrap resolution remains necessary before the first module push.
- The first 2026-11-16 read-only refresh confirmed both blockers persisted. The intended
  maintainer API still returns HTTP 403 and the browser still requires human
  **Confirm access** at the exact App installation URL. Both required module
  checks again exit 2. Their legacy Builds pin
  `9f5d751f7ab0b7a621dcd18b589bf061fabac6ec` contains no checker, so nested
  initialization alone could not repair the gap. Current checking additionally
  requires adopted configuration and genuine delivered state. The concrete
  sequencing/verification decision is recorded in
  [pre-adoption check resolution](../specs/spec-cicd/evidence/11/pre-adoption-check-resolution.md);
  no frozen constraint was changed or exception assumed. No additional local
  source gap was found, and publication/adoption tasks remain incomplete.
- After the human completed GitHub **Confirm access**, saved App selection and
  verified it after browser reload: exactly Builds, CiCd and both pilots.
  Completed the authorized stale CodeQL/three orphan-tag cleanup, exact
  main/v* rulesets and main-only `hexalith-release` environments. Installed
  distinct scoped Zot identities and each environment's secret pair, preserving
  legacy access. Real authentication/foreign-write refusals and preservation
  checks pass. Full current details are in
  [provisioning status](../specs/spec-cicd/evidence/11/provisioning-status.md).
- The initial scoped NuGet policy attempt was incomplete: the first Commons submission
  returned a generic creation error, and refreshing exposed an expired NuGet
  session. Normal Microsoft sign-in now requires human face/fingerprint/PIN
  or security-key authentication. No new policy or specific duplicate/permission
  limitation is proved. Later settings/org-grant writes wait for this AD-21
  policy step. No module push, shared release, adoption, credential removal or
  pre-adoption-check substitution occurred; both human prerequisites remain
  separate from the already authorized provisioning.
- After the human completed Microsoft/NuGet authentication, verified both
  Active additive policies after browser reload: Commons `27048` and Poly
  `27049`, exact owner/repository IDs, `release.yml`, `hexalith-release`, each
  package-prefix glob, and push packages/versions only. An intermediate Commons
  UI readback included Stage/Unlist; narrowed only the new policy and verified
  the persisted correction. All old policy IDs remain. Completed subsequent
  settings/org grants in AD-21 order; both pull-secret namespaces and the NuGet
  variable now select Builds plus the two pilots. No legacy access was removed.
- Refreshed Builds main advanced twelve unrelated commits. Fast-forwarded
  without altering the staged verifier, validated the exact commit and range,
  and reran all seventeen publisher regressions on that base. Pushed
  `65fd22f37b9fad64b595841923cdbe050563ab99` with CiCd-agent. Exact-source CI
  run `43830524672` is running; shared publication remains pending its success.
  Refreshed package-catalog inputs require new module product verification
  under the eventual released pin. Prepared `pre-adoption-verify.py` for that
  approved verification, without yet executing it or removing legacy copies.
- Full hosted qualification exposed a recovery-fixture integration gap: the
  real publisher's feed read had no local transport in that separate composite
  test. A bounded unmodified reproduction observed the publisher sleeping after
  forty seconds and terminated/waited its entire process group. Shared the
  local feed adapter and served the original authenticated package bytes in
  recovery; the focused test passes in 4.949s, and all seventeen publisher plus
  twenty-two recovery tests pass on both interpreters. Production verification
  is unchanged. Pushed fixture correction
  `fdda17c0a4538b0f7c99f813c20ca24b49006530`; corrected CI run `43834424445`
  has both Python suites green and remains in progress for other jobs. The old
  run's Python jobs actually exceeded their thirty-minute limits; its retained
  annotations substantiate that failure rather than a manually cancelled run.
- Prepared exact immediate cleanup targets in
  [post-adoption cleanup plan](../specs/spec-cicd/evidence/11/post-adoption-cleanup-plan.md).
  Neither pilot currently receives any legacy org secret, repository secret,
  production-environment secret or deploy key. Legacy NuGet policies are
  concrete IDs; the sole visible API key remains expired under the prior
  disposition, without an asserted secret mapping. Zot's global admins cannot
  be revoked by a narrower namespace-policy edit, and their legacy automation
  role remains unverified. The human identity/maintainer-only disposition is
  pending before actual adoption; no shared administrator was altered.
- Corrected Builds CI `43834424445` completed successfully on exact source
  `fdda17c0a4538b0f7c99f813c20ca24b49006530`. Dispatched the interactive
  shared release once and correlated its returned run `43838534329`. It
  completed success and published stable immutable bot-authored `v6.0.6` at
  that exact source. Authenticated the sole `published` outcome artifact by
  producing run/head, ZIP size/digest and closed schema; fetched the tag and
  confirmed it equals the source and is ancestral to current main.
- Prepared product probe commits from freshly fetched original
  mains: Commons `e3d4da366a2e8c6b6216f4a7b57c15241313da79`, Poly
  `dbea7efd64ec75e2b92920665cb1ebffda15fa88`. They retain legacy tooling,
  add the probe document plus Commons' three product-hook files, and preserve
  every other byte/mode/gitlink. Both owning/shared pinned commit policies pass;
  both complete released-pin product verification sets now pass: package-mode
  builds, all 372 tests in nine suites with zero skipped, twelve Commons
  payload/symbol pairs, isolated consumption and all policy/commit checks. Each
  probe's main/head was checked again immediately before its protected-token
  push. Commons PR #52 and Poly PR #19 are open and unmerged; no Update branch
  result is claimed before delivery. Temporary worktree metadata is removed and
  original nested paths stay empty.
- Local retirement commits are Commons
  `a83959832ebdad9fe5a5ea268fb0224c49cfa8ea` and Poly
  `c547c763a20e1fbf6b7a5c9d3b4791260fb61149`, on fresh-main preparation
  branches. They pass the second complete approved verification set under
  `v6.0.6`, preserving every other byte/mode/gitlink and all SDK/C# content.
  No preparation main push occurred: legacy workflows still reference the
  retirement targets, so adoption must be able to follow promptly.
- Prepared local `v6.0.6` pin, both `.slnx` registrations and ten rendered paths.
  Render reproducibility, released schemas/caller interfaces and the actual
  acceptable-release check pass. Exact inputs and desired direct gitlinks are
  saved; original root staging is byte-identical before/after. No CiCd candidate
  commit or delivery-triggering push occurred, and full committed/live-main
  candidate validation remains pending.
- The required pending identity question is: identify any remaining legacy Zot
  automation principal and its pilot scope, or attest that `jpiquot` and
  `jpiquot@itaneo.com` are maintainer-only and no legacy pilot publisher remains.
  No credential mapping is inferred. Preparation main publication and adoption
  wait for this answer; scoped namespace edits cannot revoke a global admin.
- The human cannot attest to global administrator key usage. Read-only
  investigation and root's independent assessment supersede that overly broad
  blocker with the bounded no-op in
  [pilot Zot disposition](../specs/spec-cicd/evidence/11/zot-pilot-legacy-disposition.md).
  Complete pilot workflow/container histories and fresh full secret inventories
  identify no legacy Zot publisher path or grant for these package-only pilots.
  Recheck that scope/exclusion at cleanup. Current logs positively show admin
  containerd pulls for Memories, which must remain. Global API-key mapping is
  unverified: the documented browser GET reached login, and the bounded later
  attempt obtained no metadata or reachable SSO control. No key, credential,
  cookie/storage, administrator or other-module grant was changed. This applies
  AD-21 to the actual pilot publishing scope without a frozen exception or a
  global guarantee about maintainer keys; ordered implementation can resume.
- A subsequent exact-window read classified the documented Zot GET's missing
  document as a native username/password prompt (`IsPassword: true`). Cancelled
  without reading or entering values. Key metadata/mapping remains unverified;
  this access limit does not change the accepted pilot-specific no-op.
- Final legacy PR readback is not uniformly green. Poly's owned old commitlint
  caller omits the required `pull-request-title` input; the completed job says
  that input is required, while its product Verify, CodeQL and dependency review
  pass. Exact committed messages passed both owning/shared local policies.
  Commons' product CI, verifier tests, commitlint, CodeQL and dependency review
  pass. Codacy's read-only current output/annotation reports one new minor-or-
  higher warning at consumer script line 159, asking to check subprocess input,
  against a zero-new-issue threshold. The explicit-list `dotnet` call uses no
  enabled shell; exploitability or a waiver is not established. Saved exact
  metadata/annotation and the pipeline diagnostic without an authentication or
  settings flow, owned edit, suppression, weakening or rerun. No adopted-main
  green-CI result is claimed.
- After the scoped Zot no-op was accepted, prepared isolated committed CiCd
  candidate `ba62ae71d148d3c5951f4508f7ebaf1bf49ab858` from fresh main
  `37e73a99dfe82c3b7741554d6f4ff2207711644b`. Its causal inputs/render,
  released schema/caller contracts and commit/range policy pass. Original root
  staging is unchanged. Fresh released-source, main/base, local-head and clean
  checks passed immediately before each protected-token preparation-main push;
  both exact tested commits are confirmed remotely with their recorded sole
  parents. Full locked committed/live-main candidate validation is running;
  no delivery-triggering CiCd push has occurred.
- Checked every legacy package ID at the three removed orphan versions: all
  twelve Commons `2.30.2` and both Poly `1.19.4` nuspec reads return 404; both
  Poly `1.19.0` packages exist with source `1eefc400cf972288c8b6e44b5de9f1d6b3ffddd0`.
  The unmodified released resolver with real locked plugins and fresh anonymous
  Git/tag objects selects newer bases Commons `v3.0.0` and Poly `v2.0.0`, and
  reports nothing to release on both exact preparation mains. No version,
  release or dispatch was forced; the actual scheduled night remains required.
- Initial candidate `ba62ae71d148d3c5951f4508f7ebaf1bf49ab858` failed only
  two permission-contract test fixtures whose implicit pin had gained restore
  permissions. Made the synthetic pre-restore baseline explicit and retained
  literal read/write expectations and strict permission rejection; production
  rendering/validation is unchanged. All 32 renderer tests pass on Python 3.12
  and runner Python. An initial concurrent 3.12 attempt encountered uv script
  environment replacement; preserved that log and reran sequentially with a
  private cache, without changing locks or tests for the environment failure.
  The revised full gate used its own private cache and passed on exact `f002`.
  Both completed gate reports/logs remain separately saved. Refreshed normal
  NuGet UI inventory and exact legacy-delete/new-keep controls before the push;
  no legacy policy has yet been removed.
- Delivery `43860977581` adopted Commons
  `5169f6b6165482d4b1499ccc5958eb897101be4f` and Poly
  `49fbe97f7224e2795ffb3293330d9efde6c0f561`, with exact sole preparation
  parents and accepted source `f002539f6fbaddaa9b621a9cbf75a1263eee5dea`.
  The authenticated sole artifact is `14223904289`; the unchanged shared ZIP,
  digest and closed-schema validator authenticates it before tree inspection.
  Both unmodified expected-state comparisons and full owned-repair/foreign
  byte-mode-gitlink proofs pass; 143/24 C# files, SDK pins and original empty
  nested paths are preserved.
- Enabled immutable releases immediately, receiving 204 and `enabled: true`
  on both repositories. Deleted only legacy NuGet policies `20233`/`20232` and
  verified after Reload that new `27048`/`27049` plus every other policy remain.
  Fresh complete GitHub inventories confirm the legacy pilot secret/deploy-key
  no-ops and retain the selected NuGet login `jpiquot` and new secret pairs.
  A readback helper initially confused login with package owner, stopped after
  the immutable writes, and resumed read-only with the existing login preserved;
  its initial evidence is retained. The package-only Zot no-op is rechecked,
  ACL exactly preserved, global key mapping still unverified. Removed only six
  regenerated old `codeql.yml:analyze` analyses; other configurations untouched.
- Adopted-main CI runs `43864267698`/`43864363785` succeed on those exact
  App commits. Saved full logs show 357/15 C# passes, zero skipped, twelve real
  Commons payload/symbol pairs and successful isolated consumer execution.
  CodeQL/release/nightly scan and bump outcomes still require the actual night.
- The exact normal checker passed sequentially on fresh-main product heads
  Commons `47d51c025ec2413ad758d74b552772fcd275e446` and Poly
  `1a2e079a7e1d77beb71a3ec09f7ca5fd175ae591`, then both protected-token
  pushes succeeded after final all-module and immediate per-push freshness
  checks. Both meaningful Update branch requests returned 202. Server merge
  heads `517c1af6036e7a0074a8ea5cf081f1046c6f58fe` and
  `e571f080f58f80519786063ada4f60a236cf1efb` have the old probe plus actual
  adopted main as parents and differ from adopted main only by the probe doc.
  This establishes the allowed server operation and token-layer residual;
  it is not a refusal. Both PRs are closed without merging, and four remote
  plus four local probe refs are removed with exact-identity guards.
  Actual updated-PR Codacy checks pass on both heads, while Stage 1 rejects
  GitHub's service-generated `Merge branch 'main' ...` subjects with commitlint
  `subject-empty`/`type-empty`; no product build/test ran on those probe merges.
  This is the observed compatibility constraint, not a token refusal or product
  regression. Preserve the guard and closed probes without rewrite or rerun.
- Corrected the canonical policy in CiCd to prohibit importing owned CI/CD
  changes through Update branch and require current-main branches with only
  product changes reapplied. It accurately states GitHub's allowance and does
  not ban unrelated product-only updates or change token permissions. Updated
  renderer assertions, regenerated the two manifests and superseded provisional
  tracking outside historical frozen contracts. Python 3.12's 32 renderer
  regressions pass. Committed candidate `3427f041` then passed all fourteen
  suites/392 tests and the complete committed/global/live-module gate, with
  original staging preserved and disposable metadata removed. The exact
  reviewed source is pushed and bound to real run `43869480499`. That run
  succeeded; its sole artifact `14228292488`, source/attempt, accepted refs,
  actual sole parents and complete expected/foreign trees are authenticated.
  Final policy App commits are Commons `49187d47da882d5470deac982bb383486c90202c`
  and Poly `2cbec6a66e2174adc7c5d431c1b1f0d28abd5647`.
  Final-main CI `43871882227`/`43871975251` passes all 372 C# tests with zero
  skips plus the Commons package/consumer hook. The scoped policy follow-up is
  complete. The original two clean module workspaces were then intentionally
  checked out/fast-forwarded to those authenticated mains with command-local
  hooks suppression and no recursion, separately recorded from earlier
  preservation proofs. Both nested Builds paths stay empty and the original
  CiCd HEAD/staged index remain unchanged.

## Spec Change Log

- 2026-11-16 — Human approved the documented pre-adoption verification path for the two pilots' product-preparation pushes. Recorded the limited exception in the frozen constraints; all ownership, product checks, credential boundaries and post-adoption checker requirements remain in force.

## Review Triage Log

- 2026-11-16 — Diagnostic follow-up only: all three BMAD code lenses ran
  independently. Corrected Unicode truncation, missing context when retry-header
  validation refuses, URL retention, ambiguous body omission and field clipping;
  clarified that artifact-download diagnostics are unchanged. Added bounded
  job/token/caller and expired-budget coverage, all write-method no-retry cases,
  cross-token redaction and terminal 429/503 evidence. The verification lens's
  exact `body_status` assertion gap is fixed and passes on both interpreters.
  All three lenses report no unresolved findings. This scoped review does not
  replace the remaining full-story review after genuine scheduled acceptance.
  See `nightly-diagnostics-bmad-review.json` in the evidence folder.

## Verification

Completed logs under [evidence/11](../specs/spec-cicd/evidence/11/):

- `failed-nightly-{run,artifact-metadata,api-response,diagnosis}.json`, its
  saved publish-ready log and digest-matched artifact members: actual failed
  scheduled source, anonymous request, fresh exact-endpoint HTTP 200 responses,
  and the explicitly unverified historical refusal/rate-limit classification.
- `resume-prior-acceptance-audit.json`: independent immutable-object and
  hash verification of completed initial/final adoptions, preservation, actual
  green CI, shared publisher coverage, protected-token probes and cleanup.
  The stale `remote_push_performed: false` field in earlier probe evidence is
  annotated; raw successful pushes, readbacks and deletions remain preserved.
- `nightly-response-diagnostics-qualified-python312.log` and `-runner.log`:
  all 36 final runtime tests pass on both interpreters; subsequent exact
  omission-status assertions pass in `nightly-response-status-python312.log`
  and `-runner.log`. Superseded qualification attempts are retained explicitly
  and made no push; only the final candidate may establish deployment evidence.
- `nightly-diagnostics-candidate-5.json`, `nightly-diagnostics-full-validation-5.log`,
  `nightly-diagnostics-final-commitlint.json` and `nightly-diagnostics-push.json`:
  exact fresh-main source passes all 399 tests/global/live checks, released
  commitlint and confirmed ordinary push. `nightly-diagnostics-push-stale-base.json`
  records the earlier pre-push stop; no failed or uncertain write was retried.
  `nightly-continuation-schedule.json` authenticates the active local one-shot
  timer and unchanged intended profile. `scheduled-night-preflight.json`
  retains actual analysis-inventory permission refusals without inferring
  absence. `resume-matrix-coverage-audit.json` maps all five frozen rows to
  27 executed tests; its sole live gap remains the actual scheduled night.
- `builds-publisher-python312.log` and `builds-publisher-python314.log`: 17
  publisher regressions passed on each interpreter, including actual composite
  rejection of missing, wrong-source and unauthorized feed responses.
- `package-mode-verification.py` and `package-mode-python314.log`: both builds,
  372 passing C# tests with zero skipped, twelve Commons payload/symbol package
  pairs and isolated consumer restore/build. Final Commons source hashes match
  the recorded successful overlays; disposable scratch was removed.
- `deliver-python312.log`: 20 delivery tests passed; the subsequent null guard
  receives a separate focused follow-up. `deliver-python314.log`: all 20 passed
  on runner Python 3.14.4 in 426.449 seconds, including the final null case.
- `deliver-null-python312.log`: all malformed/null/authorization sibling
  subcases passed in the focused Python 3.12 test. The initial broader runtime
  check exposed a diagnostic regression from globally rejecting null; its log
  is retained. The correction limits rejection to absence-enabled reads and
  gets direct runtime coverage without weakening any response validation.
- `delivery-runtime-python312.log` and `delivery-runtime-python314.log`: all 12
  runtime tests passed on the final code in 15.038s and 13.119s, including the
  null-versus-404 path and unchanged ancestry-identity diagnostics.
  `render-check.log`: wrapped locked renderer `--check` exited 0; no production
  registration, render or Builds pin changed.
- `final-local-checks.json`: frozen intent and original baseline preserved,
  source hashes, SDK/C# and owned-boundary checks, unchanged default
  authentication, evidence credential scan and whitespace checks. This is
  local readiness evidence; the committed adoption-candidate/global checks and
  live checkpoint remain unperformed.
- `recheck-preflight.{py,json,log}` and `module-fetch.log`: authenticated live
  GET observations, exact failure and remotely reachable source revisions;
  no provisioning or delivery claim follows from these reads.
- `app-selection-browser-blocker.json` and
  `pre-adoption-prepush-blocker.json`: fresh read-only authentication state and
  both exact failed mandatory module-check commands; no push was attempted.
- `resume-prerequisites.{py,json,log}`: 2026-11-16 authenticated maintainer
  preflight, exact browser URL/prompt, both failed check commands and successful
  Git tree inspection proving the legacy pin lacks the checker. No UI or remote
  mutation occurred; the default profile and absent overrides are unchanged.
- `app-selection-*.json`, `provision-*.{json,log}` and
  `provisioning-after.json`: actual saved App scope, stale configuration/tag
  cleanup, exact protections, main-only environments and scoped Zot credentials,
  including preservation and real registry outcomes. `provisioning-status.md`
  separates completed administration from pending policy/grant and adoption work.
- `nuget-commons-{proposed,submit,readback}.json`,
  `nuget-session-expired.json` and `nuget-signin-result.json`: exact failed
  creation/readback and subsequent human authentication boundary; no saved
  additive NuGet policy is claimed.
- `nuget-policy-verification.json` and `nuget-commons-readback-6.json`: both
  actual Active policies, exact bindings and push-only scopes after browser
  reload, with every existing policy ID preserved. `provision-settings-grants`
  reports successful ordered settings checks and additive org grants.
- `builds-precommit.log`, `builds-prepush.log`, `builds-publication-source.json`
  and `builds-ci-observation.*`: seventeen passing publisher tests on refreshed
  main, exact pinned commit/range validation, authenticated source push and
  ongoing exact-run observation. No shared release is claimed yet.
- `builds-recovery-reproduction.{json,log}`, `builds-recovery-focused.log`,
  `builds-{publish,complete}-fixture-python{312,314}.log`,
  `builds-recovery-fixture-source.json` and `builds-corrected-ci-binding.json`:
  bounded integration failure, complete process cleanup, real local-feed
  verification, all affected regressions and the exact corrected source push.
  `builds-original-python-outcome.json` records GitHub's actual timeout
  annotations for the original source, without cancelling or rerunning it.
- `builds-released-pin.json`, `builds-release-outcome.json` and
  `builds-publisher-live-verification.json`: successful exact-source CI/release,
  published immutable bot tag `v6.0.6`, authenticated sole published outcome,
  and both actual live-feed verifications before GitHub finalization.
- `pre-adoption-{probe-,}verification.{json,log}`, `pre-delivery-probes.json`
  and `local-product-preparation.json`: both complete released-pin verification
  sets, exact bases/heads, unchanged ownership proof, successful protected-token
  probe pushes/PR creation and local-only retirement commits. Probe PRs remain
  open and unmerged for post-delivery qualification and cleanup.
- `local-registration-preparation.{json,log}`: local pin/setup/render bytes,
  tagged schema/caller contracts and actual acceptable release pass; original
  root staging is preserved. No committed-candidate or live adoption verdict is
  claimed.
- `checkpoint-status.json`, `pre-adoption-proof-summary.json`,
  `checkpoint-intent-audit.json` and `checkpoint-checks.{json,log}`: exact current
  refs/PRs/check states, both complete product proof summaries, only the approved
  frozen paragraph delta, credential/whitespace checks, preserved staging and
  no active local job processes. `legacy-poly-commitlint-failure.json` records
  the old caller's actual missing-input defect; it is not a product-test bypass.
  `legacy-commons-codacy-check.json` retains the current quality threshold and
  exact subprocess warning without claiming a confirmed vulnerability or waiver.
- `render-permission-fixture-qualification.json`, both interpreter logs and
  retained initial isolation-failure log: all 32 final renderer regressions
  pass sequentially with explicit contract fixtures. `candidate-validation-2`
  JSON/full log/progress authenticate the successful exact `f002` global and
  live-module verdict, unchanged original staging and complete worktree cleanup.
  `cicd-candidate-push.json` binds fresh inputs, the confirmed nonforce push and
  unique real delivery run. `nuget-commons-readback-22.json` and refreshed
  `nuget-cleanup-readiness.json` record live prepush cleanup readiness.
- `authenticated-adoption.json`, `delivery-report.json`,
  `post-adoption-github-cleanup{,-initial}.json`,
  `nuget-cleanup-verify-cleanup.json` and
  `post-adoption-legacy-codeql-cleanup.json`: authenticated actual adoption,
  preserved foreign/SDK/C# content, successful immediate settings/policy cleanup,
  and explicitly bounded no-ops without administrator or other-module revocation.
- `adopted-main-ci-proof.json` and both full CI logs, `post-adoption-check`
  JSON/log, `post-adoption-fresh-branch-outcomes.json`,
  `post-delivery-update-branch.json` and `product-probe-cleanup.json`: real green
  CI/product outcomes, exact normal checker, protected-token fresh pushes,
  allowed server merge/tree proofs, no PR merge and complete probe cleanup.
- `qualified-policy-render-python312.log`, `qualified-policy-candidate.json`
  and its full/progress logs: factual canonical-policy correction, 32 passing
  minimum-interpreter renderer tests and the successful exact full follow-up
  gate. `qualified-policy-push.json` binds fresh inputs, confirmed source push
  and unique actual delivery run without dispatch. `authenticated-policy-redelivery.json`,
  `qualified-policy-delivery-report.json`, `final-main-ci-proof.json` plus full
  CI logs, and `original-module-workspace-sync.json` record successful actual
  rollout, unchanged foreign/SDK/C# content, final green CI and intentional
  guarded workspace sync. `nightly-checkpoint-pending.json` names the then-pending
  acceptance event without inferring a future result.
- `scheduled-20261117-{run,jobs,artifact-metadata,authentication,diagnosis}.json`,
  digest-matched `hexalith-nightly-*-1-*.json` members, scan summary,
  `scheduled-20261117-codeql-inventory.json`, diagnostic delivery
  `43889937298` report, hourly delivery `44072144087`, and
  `scheduled-20261117-commons-scan-{discovery.json,fix.diff}`: genuine
  delayed schedule parent, barrier-blocked dispatch, authenticated bump
  no-change and keepalive pass, Commons discovery reproduction, and the
  then-unpushed local hook/script fix that cleared those four discovery errors.
- `nightly-continuation-20261118-schedule.json` and
  `run-nightly-continuation-20261118.py`: armed read-only observer/authenticator
  for the genuine 2026-11-18 02:17 UTC night. No dispatch is configured.
- `land-commons-scan-fix.{py,json,log,commitmsg}`, `land-commons-scan-fix-commitlint.log`,
  `land-commons-scan-fix-attempt-1.json`, `land-commons-scan-fix-ci.json` and
  `land-commons-scan-fix-ci-proof.json`: check.py-qualified land of Commons
  `d551e5f3` from night main `aa694ae3`, zero remaining Commons discovery
  errors with an unchanged selected file set, 357 C# tests, twelve
  payload/symbol pairs, isolated consumer, confirmed protected-token main
  push, and GitHub CI `44089607938` success. Attempt 1 stopped before commit
  when `--edit` commitlint was run outside the module worktree; no push
  occurred. Nested Builds paths stayed empty; temporary worktrees were removed.

Remaining verification for checkpoint acceptance:

- Delivery compatibility, shared publication regressions, both full pre-adoption proof sets and both exact post-adoption normal checkers pass with saved logs. No module workflow-text assertions were added.
- The initial committed/global/live-module gate, real adoption artifacts, immediate settings/credential cleanup, green adopted-main CI and all restricted-token outcomes/cleanup are complete. Candidate `3427f041` passed its full locked gate and actual redelivery, with authenticated tree/foreign-content and final green-main CI proof. Original module workspaces are intentionally synced and clean; CiCd's staged entries remain preserved.
- Genuine 2026-11-17 scheduled parent `44067556763` is authenticated and failed: delivery barrier timeout, no pilot/Builds dispatch, Commons scan discovery errors, Conversations sibling scan errors. Builds bump no-change and keepalive passed. See `scheduled-20261117-{run,authentication,diagnosis,commons-scan-discovery}.json`. Manual dispatch cannot replace it.
- The Commons hook/script discovery fix is landed and check.py-qualified on live main `d551e5f3`; GitHub CI `44089607938` passed. Leave Conversations to its owning story. Wait for the next genuine scheduled night (2026-11-18 02:17 UTC) that actually dispatches both pilots and Builds; prove CodeQL upload, SARIF processing and the processed-findings gate from those release jobs. Direct analysis inventories remain 403 under CiCd-agent. A sibling Conversations discovery failure would still fail the shared scan job. The 30-minute delivery barrier remains fail-closed if hourly `deliver.yml` overlaps that night.
