# Story 15 local implementation handoff — 2026-11-16

This is a partial implementation, not adoption or release acceptance. No remote
settings, product refs, packages, releases or delivered refs were changed. The
parent session is continuing the ordered administrative work. Every task in
the approved story remains open until its complete acceptance is observed.

The candidate shared-runtime changes are in the direct Builds checkout on
`feat/mcpcli-runtime-support`, based on freshly fetched main
`fdda17c0a4538b0f7c99f813c20ca24b49006530`. No commit or push was made. McpCli
remains clean at freshly fetched main
`e2e3db7ba2d45d61feacc39c41b3051310fbc57f`. No nested submodule was initialized.

The Builds schema and independent loader accept macOS product jobs and the
optional native `aspire` and complete-job `job-timeout-minutes` fields. Old
complete v1 documents remain valid and unchanged. Native Aspire requires
`dapr: true`; the job budget accepts JSON integers from 1 through 360. The
shared unit-stage/composite outputs forward the capability only after unit
success. Windows and macOS prepare consume validated outputs and share the
existing PowerShell implementation without reading module configuration.

Shared environment setup authenticates the Aspire 13.6.5 release archive and
executable, compares every extracted DCP/dashboard bundle file, checks the
exact Core/ASP.NET runtime 11.0.0 inventory and native libraries/tools, and
probes private namespaces. A failed namespace probe permits a bounded sysctl
adjustment only on disposable GitHub-hosted runners, followed by a second
probe. Every new setup process has a deadline and TERM/KILL bounds. The private
Python environment installs jsonschema 4.26.0 and its fully pinned transitive
wheel set with required hashes. Generic setup performs no module build or test.

CiCd's template emits the existing reusable timeout input only for a selected
non-default bound and renders `macos-<name>` job IDs. Windows IDs and existing
registration output bytes are preserved. The SPEC, architecture decisions and
setup instructions describe this approved expansion and its compatibility
behavior. The renderer tests exercise candidate Git-object fixtures; they do
not establish that the candidate is an acceptable published Builds tag.

Verification used `run-with-temp`; disposable test workspaces, package feeds,
SDK fixtures, downloaded assets and Python environments were private and
removed after their commands exited. Logs are retained beside this file.

- Shared `test_ci_*.py`: 109 tests passed on Python 3.12.13 and 3.14.4, in
  `shared-python{312,314}-final.log`. The first run caught an omitted composite
  output; that defect was fixed before these passing runs.
- After the final native timeout/locked-tooling changes,
  `test_ci_environment.py`: all 30 tests passed on both interpreters, in
  `native-locked-python{312,314}.log`.
- After JSON-integer schema/loader parity qualification,
  `test_ci_config.py`: all 18 tests passed on both interpreters, in
  `config-final-python{312,314}.log`.
- `uv run --locked --script --python <3.12|3.14>
  tools/tests/test_render.py`: all 35 tests passed on each interpreter.
- `uv run --locked --script tools/render.py --check`: passed against the
  unchanged existing `builds-version` release; `render-check.log`.
- Real hash-required Python wheel installation passed on 3.12 and 3.14;
  `python-toolchain{312,314}.log`.
- The actual Aspire archive and executable matched the approved digests;
  `aspire-authenticated-assets.log`. The downloaded executable was not run.
- The real local Linux native prerequisites and private user/PID/network/mount
  namespace probe passed without any sysctl change;
  `linux-native-prerequisites.log`. This is not a complete live lane result.
- Root and Builds `git diff --check` passed.

`preflight-recheck.json` preserves the intended maintainer profile, account,
repository identity, token-override absence and exact API responses. The App
repository-list API returns 403. The existing installation page displayed the
four previously selected repositories, but it was not reloaded. The selector
eventually exposed a repository search; entering `Hexalith.McpCli` collapsed
the menu before a repository choice could be observed. No choice or Save was
invoked. `app-selector-observation.{py,json}` records the exact controls and
search attempt. This interaction is not diagnosed as an administrative access
barrier; the parent will continue it.

CodeQL's filtered and unfiltered analyses and alerts endpoints all returned
404 with the typed body `no analysis found`. The accepted-scope header includes
`repo`, which the intended profile holds. GitHub's official OAuth-scope
documentation confirms that the narrower security scope is unnecessary when
repository-code access is granted. The CLI refresh hint does not establish a
permission failure. `codeql-corroboration.json` retains the raw observations,
official references and their limits. No stale analysis deletion target was
identified; no token or scope change was requested.

Remaining work includes completing ordered AD-21 provisioning/readbacks,
qualifying and publishing an acceptable Builds release, all McpCli product
preparation and real cross-platform/live results, registration/pins, committed
global/per-module candidate checks, authenticated App adoption, immediate
legacy-access cleanup and the next genuine nightly outcome. Product source
fixtures still need the approved one-build/cache refactor; no product gate
retirement or package-pair qualification has been claimed. `acceptance.json`
explicitly records the absent acceptance evidence. Do not commit the CiCd
candidate ahead of its published shared-runtime dependency.


## Parent continuation — local qualification and authentication boundary

The parent added a hosted `sample-macos` job, a test that asserts macOS before
exercising the sample product, and matching sample/expected configuration. The
Builds candidate is staged on `feat/mcpcli-runtime-support`; no commit, push or
release was made. `builds-runtime.patch` now includes those additions.

`platform-actions-python{312,314}.log` records all 28 platform-action checks
passing after that addition. `workflow-lint.log` records actionlint and online
zizmor success, with the ten existing exact frozen findings and zero new ones.
`sample-candidate-build.log` records a private package-mode Release restore and
build of the entire sample solution: zero warnings/errors, all four executable
Linux unit/hook/integration cases passing with no skips, and discovery of the
new macOS case. Its OS assertion was not executed on Linux. A real macOS run and
the complete McpCli lane still remain required.

The canonical action contract now distinguishes retained product test reports,
fixture/package provenance and diagnostics from alternative pipeline verdicts
and forbidden story/agent evidence gates, preserving the approved native
product assertions.

A real refresh of installation settings exposed GitHub's **Confirm access**
prompt, recorded in `app-selection-reload-result.json`. The earlier page and
selector were stale; no repository choice or Save was invoked. The parent
requested human authentication through the existing browser and has not read
or filled authentication controls. `app-selection.py` is a bounded additive
helper; Save requires an exact refreshed baseline comparison and preserves
selected-only scope. No baseline or saved addition is claimed.

`local-qualification.json` binds this candidate's staged tree and source bytes
to the checks and explicitly lists incomplete operational/product acceptance.
The story remains in progress; all original tasks remain unchecked because
each includes completion that has not yet occurred.


## Authentication resumed and App scope saved

The human replied **done** after completing GitHub Confirm access. Fresh UI
readback showed the unchanged four-repository selection with Save disabled.
The parent scrolled the selector into view, searched for the exact McpCli
repository, selected only that repository, and invoked Save after an exact
additive comparison. A subsequent actual browser reload confirmed exactly
Builds, CiCd, Commons, McpCli and PolymorphicSerializations, selected-only scope,
and no pending Save. `provisioning-status.json` and timestamped
`app-selection-*.json` retain these observations.

The initial offscreen selector was an interaction issue; scrolling it into view
resolved it. No new GitHub token or broader scope was used. Required GitHub
administration, Zot/NuGet provisioning, product pushes and shared publication
remain authorized by the approved story; do not request that authorization
again. Continue the remaining AD-21 sequence from the saved App selection.

## Continued implementation and remote prerequisites, 2026-11-16 16:42 UTC

Ordered provisioning resumed after the authenticated App selection. The exact rulesets and main-only hexalith-release environment were created and read back. The distinct registry identity hexalith-mcpcli-publish has only mcpcli/mcpcli/** read/create/update grants; authenticated registry access passed and unrelated upload attempts were rejected. NuGet policy 27180 was created and verified after an actual browser reload, with only Hexalith.McpCli* new-package/version push scope. Existing policies, including legacy 20113, were preserved. Required settings and selected Actions/Dependabot pull-secret/NuGet-user grants passed readback. Actual release/tag and CodeQL inventory required no stale-state deletion. The CodeQL response is specifically `no analysis found`; the accepted repo scope is already present, so this is not a missing-scope diagnosis.

The immediate cleanup plan and fresh GitHub/registry metadata are retained in immediate-cleanup-plan.md, legacy-access-inventory.json and registry-acl-preflight.json. Legacy NuGet policy 20113 must be removed and immutable releases enabled immediately after authenticated adoption. Current legacy API-key package scopes remain unverified: navigation to the actual account API-key page led to GitHub Confirm access for @jpiquot. nuget-api-keys-readback.json preserves exact visible controls. No credential values or authentication controls were read/invoked. The parent requested attended authentication; the prompt is untouched. Absence of GitHub secret grants is not treated as proof that a shared API key cannot publish McpCli.

Shared Builds changes, including the real hosted macOS sample, were committed/pushed normally as 397af8f4351f6b10266821b132d0e730e48603ff. Real CI 43903831934 passed both Python lanes, .NET build/tests, Linux and Windows samples, and workflow/public API checks. It failed on the added macOS project's missing catalog consumer evidence. The macOS job separately failed before executing any step because no hosted runner was acquired; exact annotations document arm64 capacity constraints. No macOS acceptance was claimed.

The owning package-audit generator refreshed only xunit against committed source 397af8f. The deterministic validator, all 113 generator and 109 validator scenarios passed. Explicit comparisons proved all package selections and the 156 unrequested families unchanged. The exact follow-up commit message passed pinned commitlint and npm signature checks. Audit follow-up 107ba962d6136e3fabaf1ef7c82c038b4271b3c6 was pushed to Builds main; normal CI 43909723959 is running. No new release/tag or acceptable Builds release is claimed yet.

McpCli product preparation remains an uncommitted draft. It fixes Core packability, removes retired YAML/release gate tests and tool-only npm manifests, extracts retained payload/analyzer-consumer tests and product package helpers, removes repeated platform builds, enforces the v1 benchmark in ordinary units, and makes enrolled replay consume existing production host outputs without restore/build. Private sample/packaged fixtures retain their distinct builds. Independent exact-pinned qualification uses a sibling archive of McpCli's actual e2e3db7b Builds pin 65fd22f37b9fad64b595841923cdbe050563ab99; nested paths remain uninitialized. All 20 Abstractions tests pass with zero build warnings/errors, and the entire evaluated solution's pack set is exactly Hexalith.McpCli.Abstractions plus Hexalith.McpCli. product-independent-focus.log binds these inputs. The prior failed product-focus workspace materialized a forbidden nested Builds clone and is not accepted qualification; it was cleaned and superseded by this sibling-archive run.

Full product restore is blocked by genuinely unpublished Hexalith.Projects.Contracts 2.0.0-story66.3. projects-dependency-investigation.json, the public nuspec/type-attribute inspection and introducing commits document the intended main enrollment ahead of publication. Public 1.2.4 lacks the required query decoration and introduces explicitly excluded UI/runtime closure; downgrading would change required behavior. The existing pin/enrollment remain intact. The parent is coordinating this external publication prerequisite; no Projects change, fake/local substitute, product push or adoption occurred.

The new native_audit.py is independently qualified but not integrated into ci.py. It restores distinct exact-package fixtures under fresh package/HTTP caches, requires unsuppressed all/low fatal warnings, verifies complete original package/content/archive-byte coverage, and independently fetches every advisory page with HTTP 200 to reject stale/cache-only consumed data. Five focused tests cover transitive/byte omissions, feed outages, weakened policy, stale index/page, cache-only responses and output drift. Real public two-package transitive audit passes; Newtonsoft.Json 9.0.1 fails with NU1903; original assets and built-output sentinels remain unchanged. native-audit-real-qualified.log and native-audit-real-receipt.json retain the local evidence. This is not complete module-native audit or live acceptance. Native one-build/source-fixture isolation, helper integration, product actions, actual product CI and all adoption/nightly tasks remain incomplete.


## NuGet API-key inventory resumed after attended authentication

The human replied **done**. The first helper read a stale background Confirm access document while the selected tab had returned to Trusted Publishing. Invoking its observed API keys navigation link opened the actual authenticated API Keys page; an actual reload and new metadata-only readback confirmed exactly key954800, Github Hexalith, Expired, Hexalith owner, Hexalith.* push scope. No credential values or key actions were used. `nuget-api-key-metadata.json` and the original reload/readback resolve the account inventory prerequisite. The immediate cleanup plan still removes only trusted policy20113 after adoption and enables immutable releases; no live legacy key revocation target was found in this account. Product publication/adoption remains held for the unavailable Projects contract and incomplete product/shared release qualification.

## Independent product/runtime continuation, 2026-11-16 17:58 UTC

The NuGet account inventory is resolved by the parent's actual navigation,
reload and metadata readback: only expired key 954800, Github Hexalith,
Hexalith.* push scope was observed. It is preserved. No values or key actions
were used. The complete immediate cleanup plan still deletes trusted policy
20113 and enables immutable releases immediately after genuine App adoption;
policy 27180 and unrelated grants remain intact. The corrected CodeQL typed
`no analysis found` observation and accepted repo scope remain authoritative.

Shared Builds source 1f41d266bd4bd04acde7b64e8c907eb34233fe0f completed real hosted
CI 43914543010 successfully, including the actual native installer/bundle/Python
setup and Linux, Windows and macOS samples. The installer uses the supported
ASPIRE_LAYOUT_PATH bound to each explicit install root, preserves fatal
installer exits and compares all 490 embedded bundle files. The earlier
HOME-override reproduction is explicitly not qualification; subsequent real
private layout qualification and current tests leave HOME unchanged.

The necessary generic Windows long-path follow-up enables and verifies
core.longpaths before checkout only on disposable GitHub-hosted Windows
runners. Behavioral tests execute the actual composite boundary with an
explicit temporary GIT_CONFIG_GLOBAL; no attended desktop global setting is
changed. A tracked 313-character relative sample path is read by an actual
Windows test. The independent new main 26031f097198f001380c23f4b9fb855c3d7b88c6
was preserved during rebase. Its opt-in test floors/skips and central warning
policy are independent work, not attributed to this story. The new source
86f184164caf0733cee86c3b63ad904c96bc0934 was pushed normally, with CI 43923585572
running. Combined schema 18, prepare 31 and environment 30 tests passed on each
Python 3.12 and3.14. The complete sample compiles with zero warnings/errors;
pinned commitlint and npm signatures passed. Renderer 35 tests passed on each
interpreter, permitting only the independent safe test-default JSON additions
minimumExpectedTests={} and failSkips=false; every other registration artifact
remains byte-identical for the native capability extension. Managed defaults
are preserved. No shared release or tag was manually published. An acceptable
immutable bot-authored Builds release must come from genuine central nightly.

The McpCli product draft now includes all three registered-action candidates.
Linux packs the existing build once into a source-bound CI fixture pair;
Windows/macOS consume those identical same-run package bytes, assert actual
expected OS, reuse their already-built suites, and perform installed-tool and
isolated analyzer-consumer checks. Product source dirt, package drift, malformed
payloads and child failures are refused. Linux's preparation receipt stays
immutable: an exclusive separate discovery manifest binds its unchanged hash,
source/package identity and complete raw capture hashes. Every platform must
match the complete Linux discovery filenames and raw bytes. This fixture pair
is distinct from the central release's later single pack. Diagnostic uploads
include captured command channels and exclude installed-tool private trees,
platform suite homes and consumer caches/profile trees.

Product process supervision retains sanitized channels and failure receipts,
bounds cleanup of owned descendants and preserves unrelated processes. Real
Linux tests cover a detached TERM-resistant grandchild and foreign sentinel;
the parent's native attended Windows 3.14.2 probe also passed actual Job Object
success, exit7, timeout/grandchild termination and foreign-process preservation,
plus Git Bash's absolute Windows script path. Its copied source hash matches
the current helper. This focused Windows evidence does not establish hosted
complete module acceptance. macOS controller execution remains unqualified.

All 70 product script tests pass, including actual child CLI argument parsing,
strict payload/consumer refusals, package/source drift, OS mismatch, discovery
byte drift, immutable receipt linkage and process timeout behavior. The old
mixed release tests' pure product coverage is mapped in product-gate-coverage.json.
The complete 188 conformance tests pass. Core is non-packable; the independently
evaluated full solution pack set remains precisely Abstractions/tool and 20
Abstractions tests passed. Private qualification uses a sibling archive of the
actual e2e3db7b Builds pin 65fd22f37b9fad64b595841923cdbe050563ab99; nested
submodules remain uninitialized. Product work is uncommitted and unpushed;
mcpcli-product-preparation.patch and continuation-qualification.json retain the
concrete draft and source hashes without claiming committed acceptance.

Native preparation now consumes shared tools and reuses the module build.
Exact qualified Tenants/Parties source clones and all fixture outputs/caches
are private siblings, never nested initialized dependencies. AppHost resource
metadata suppresses rebuilds while retaining the same graph. NativeSourceFixtures
was API-looked-up, compiled and exercised against real positive/drift cases;
the changed AppHost itself builds against the pinned source imports with zero
warnings/errors. Full lifecycle/live validation remains blocked. Separate
fresh audits bind the complete restored package graph/archive bytes and every
independently fetched advisory page, reject outages/cache-only/stale coverage,
clear NoWarn/WarningsNotAsErrors and preserve low-and-higher fatal policy.
Focused negative tests, real public transitive/vulnerable-package controls and
a real 113-package AppHost audit passed with original main outputs unchanged.

Actual Integration.Tests discovery is validated against every approved
companion-plan vector plus exact GatewaySmoke and SharedHeadBoundary cases,
with missing/extra/duplicate discovery refused. All 22 vectors and two independent
cases remain. ci-budget.md records a static 360-minute bound:60.5 min non-live
(including staging),38.5 min preparation,230.5 min native execution,20 min shared
work and 10.5 min upload/final cleanup. Existing per-case 960 s and plan 45 s bounds
are retained; aggregate expiry fails and cleans up. Actual complete module
timing is still required and is not inferred from this arithmetic.

The 16 targeted native launcher regressions passed in 247.074 s. A complete final
controlled launcher suite is currently running on private Python 3.12.13 with
hash-locked jsonschema 4.26.0; ci.py/native_audit.py/native_sources.py/test_ci.py
hashes were captured before execution and remain frozen. Separately all 149
other native tests were attempted: the run failed with 9 failures and 47 subtest
errors because the real Integration.Tests/tool/ConformanceHost outputs and tool
assets are absent. native-other-suite-prerequisites.json maps each failing
stack to its actual missing input. No synthetic production output, test skip
or weakened assertion was introduced. Those tests remain required after the
real package-mode build and direct-source initialization.

The external Projects.Contracts 2.0.0-story66.3 prerequisite remains absent;
projects-publication-prerequisite.md records the actual pin, introducing
main-enrollment-ahead-of-publication history, insufficient public 1.2.4 API and
safe resume criteria. Preserve the required enrollment and coordinate genuine
publication. Final committed package-mode qualification/push, acceptable nightly
Builds release, setup/registration/render/pins, committed-candidate checks, App
delivery, immediate cleanup, actual Linux/Windows/macOS module/live timing and
the following genuine nightly remain incomplete. The story is in progress;
no review or done verdict is entered and the frozen intent/baseline is unchanged.

## Final independent local handoff, 2026-11-16 19:04 UTC

The final controlled native launcher suite passed all 109 tests in 2,539.651
seconds on private Python 3.12.13 with the exact hash-locked jsonschema 4.26.0
requirements. Before/after hashes match for ci.py, native_audit.py,
native_sources.py and test_ci.py. Its wrapper removed private scratch and all
owned test children finished. native-launcher-full-qualification.json binds the
exact log and inputs. The earlier completed 108-test attempt remains preserved
with its three discovery-era fixture expectation failures; only test fixtures
changed before the passing run. Pre-preparation growth executes all grown
cases; post-preparation/duplicate input drift fails before children, preserves
preparation/per-run bytes and writes a new failed mutable current status.

The 70 product-script and 188 conformance suites remain passed. The separate
149-test attempt remains failed with 9 failures and 47 subtest errors caused by
absent real Integration.Tests, ConformanceHost and restored-tool assets; its
full traceback classification remains required after genuine package-mode
build/direct source initialization. No fake product output, skip or weaker
assertion substitutes for those missing prerequisites. Attended native Windows
process-tree, Bash-directory and explicit UTF-8/cp1252 diagnostic probes passed
on the exact current helper; they supplement Linux focused checks and do not
establish full hosted McpCli Windows/macOS acceptance.

Shared main advanced independently during qualification. Its test-floor/skip,
Dapr receipt, timeout, npm/tool and product-validation additions were preserved.
Combined local schema 18, prepare 31 and environment 37 cases passed on each
interpreter at bf6ee6. Actual hosted 3546c4f9 passed both full Python lanes,
native-enabled Linux, Windows and macOS samples and workflow/API checks. Its
catalog failed on duplicate JwtBearer Includes introduced by the finite
Timesheets views. The earlier qualified 86-bound fingerprint-only repair was
not pushed over changed inputs; its exact patch and diagnostic remain preserved.

The parent authorized a narrow equivalent source representation. Actual MSBuild
before/after evaluation proved the complete package/version map identical in
26 cases: all 16 finite Timesheets roles, six default/nonmatching names and
explicit cohort/source/framework/view selections. Each of JwtBearer,
Mvc.Testing and TestHost now has one canonical Include, with a default 11.0.0
version property and the existing finite-view condition selecting 10.0.15.
Central validation passes all 317 entries; seven expanded evaluated-catalog
regressions pass on both interpreters. No validator or selected version changed.
The source correction is commit 4869e69d55fd8a62ce00f5e54e0dff1b2975641a,
based on preserved current main 44cb6dbc869c4d84713278d9c861c6f5ba60bec6.

The owning generator refreshed only affected dotnet-10 evidence against that
committed source. All 317 selected versions and every record in the other 156
families are unchanged; current deterministic validation passes 317 packages,
157 families and one source. Earlier 113 generator/109 validator regressions
passed with identical auditor sources and were not repeated. Generated snapshot
commit 6db97d4e9da392ef691ed3f367e73f1b7d2ef318 and its canonical source parent
were pushed normally. Exact CI43935156026 is in progress:
https://github.com/Hexalith/Hexalith.Builds/actions/runs/43935156026 .
No overall green, acceptable release or tag is claimed for this source yet.

Renderer 36 tests pass on each interpreter with current schema/loader defaults.
The explicit native timeout overrides ciTimeoutMinutes; older schemas/default
callers retain 30-minute behavior. Independent minimumExpectedTests={},
failSkips=false, ciTimeoutMinutes=30, npmWorkspaces=[] and dotnetTools=false
additions are allowed exactly, while other existing artifact bytes stay
unchanged. The actual existing v6.0.6 registry render check passes. No version
pin, registration, rendered adoption tree or committed candidate was fabricated.

ci-budget.md bounds the shared Linux job at 360 minutes; dependent Windows/macOS
jobs finish afterward. The passing local controlled suite took 42.3275 minutes
on a heavily loaded host. Complete non-live phase, native preparation/live case,
platform and overall workflow timings still require real module acceptance.
Static aggregate caps fail and clean up on expiry; they do not certify a
successful complete workflow or remove any case.

The final uncommitted McpCli draft tree is
2863bf588d0537c8603edeac23e28b70ee226b4d on baseline
e2e3db7ba2d45d61feacc39c41b3051310fbc57f. The refreshed binary-capable patch,
source hashes and owned-path comparison are retained. No owned McpCli path or
Builds gitlink changed; nested Builds remains uninitialized. Root changes also
remain uncommitted, with builds-version still v6.0.6. acceptance.json and
continuation-qualification.json distinguish every passing, failed and pending
scope. The mutable spec continuation points here; frozen intent, baseline,
status and task checkboxes are unchanged.

Remaining dependencies are genuine public Projects.Contracts 2.0.0-story66.3
publication (still absent in the parent's fresh 18:57 UTC index), exact current
shared CI success and a qualifying immutable bot release through central
nightly. Then perform complete qualification on final committed product inputs,
record the approved pre-push owned-content comparison, push product preparation,
register/render/pin and validate the committed candidate, use App delivery,
immediately enable immutable releases/delete only legacy NuGet policy20113,
and obtain actual complete module/platform/live/timing plus following genuine
nightly acceptance. Expired shared key954800 is preserved; new policy27180 and
unrelated grants stay intact. No product push, adoption, manual release/tag,
formal review or done verdict occurred in this handoff.


## User-requested push checkpoint — 2026-11-16T19:38:43.005765+00:00

The human requested **push all changes**. The original qualified module draft was committed locally as `3b8f4184c5db71f75db00c5e14d7a2c27dea4a38`. A fresh module branch `story/15-product-preparation` starts from fetched main `119a4b59e5e1391ff8ddb4587e1608ad1d1e5145` and reapplies only the product changes as `d4341dba735a4347793235b60dfa7a89c269b334`. Whole owned-file bytes/modes and the Builds gitlink compare identically to that fresh main. No nested submodule was initialized. The literal checker exits2 for the absent nested checker, and the approved alternative real package-mode restore exits1 with NU1102 for Projects.Contracts2.0.0-story66.3; no module remote push is claimed. The fresh upstream also added legacy semantic-release notes tests; their integration with the migration remains unqualified. Earlier local test counts apply to their recorded source, not a new fully qualified product commit.

`mcpcli-product-current-checkpoint.bundle` preserves the actual fresh draft commit with public main as its prerequisite; `mcpcli-product-checkpoint.bundle` preserves the original qualified-tree commit. Both passed `git bundle verify`. The complete patch remains available too. These are source backups, not release packages, delivered state or nightly evidence. `push-request.json` records hashes and destinations. The CiCd story checkpoint is published as a draft branch, without a McpCli registration/adoption or a claimed acceptable new Builds release. Other active worktrees remain untouched.

Current shared CI43935156026 has completed with macOS job133539010560 cancelled before a runner was assigned (runner_id0, no steps). All remaining source jobs passed. This is retained in push-request-shared-ci.json and does not qualify the source as overall green. The draft checkpoint neither changes SDK/package pins nor waives the product push gate.
