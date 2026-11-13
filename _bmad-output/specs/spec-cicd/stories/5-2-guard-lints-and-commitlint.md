---
title: 'Guard lints and commitlint'
type: feature
created: '2026-11-13'
status: in-review
review_loop_iteration: 0
followup_review_recommended: false
baseline_revision: abb9e11576bff5f1407696acc481224ea0424aae
implementation_repository: references/Hexalith.Builds
implementation_baseline_revision: ceb3257147917002a2433be0ce9aac7db99e7698
context:
  - '{project-root}/_bmad-output/specs/spec-cicd/SPEC.md'
  - '{project-root}/_bmad-output/specs/spec-cicd/enforcement.md'
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md'
warnings: [oversized]
deferred: []
---

<intent-contract>

## Intent

**Problem:** Story 5-1 checks committed ownership and enabled-action availability, but does not lint custom actions, reject module-file audit bypasses, or run commitlint in the guard. The remaining audit-waiver gap was explicitly deferred from story 3-3 to this story.

**Approach:** Extend the existing first-stage guard with custom-action lint, audit lint and trusted pinned commitlint under CAP-9/14 and AD-8/11/19. Retire Builds' independent commitlint caller in the implementation change that supplies its working replacement, after verifying story 1's ruleset cut. This invocation delivers planning only and halts before implementation.

## Boundaries & Constraints

**Always:** Read pinned committed Git objects through the existing snapshot APIs. Preserve ownership comparison before module configuration parsing and all new lint execution; preserve enabled-action availability. Action lint reads all workspace-root `.github/actions/**/action.yml` and `action.yaml`, including dormant actions. Audit lint reads the module snapshot, or only the sample subtree in Builds. Sample commitlint covers the entire Builds repository's event range, independently of changed paths. Builds root bypasses new lints/commitlint and delivered lookup; validate fixture inputs before bypass. Preserve escaped deterministic diagnostics, the fixed ownership message, read-only job permissions and the internal drift flag: only actual perimeter drift emits `true`.

Runtime policy stays in stdlib Python >=3.12. External tools come from trusted action-source manifests and integrity-locked dependencies, installed outside the module with `npm ci --ignore-scripts` followed by `npm audit signatures`. Use explicit action-sourced `--config`; never load module npm/commitlint configuration, npm hooks, plugins or JavaScript. Preserve every effective existing commitlint rule, including merge linting and footer limits. Reuse the existing guard composite and CI job; do not introduce another gate/job.

**Never:** Delete `commitlint-caller.yml` during planning, before fresh confirmation of the ruleset cut, or independently of working sample guard commitlint. Change frozen `.github/workflows/commitlint.yml`, domain workflows or legacy module-consumed runtime. Modify release resolve/build behavior, SDK/catalog/dependency pins outside the new guard tool package, ownership schemas, delivery/restore, production setup/adoption or administrative settings. Add workflow-text assertions, transitive script discovery, a general shell/MSBuild evaluator, or a runtime Python package dependency. Earlier story 5-1 verification exceptions do not apply.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|---|---|---|---|
| Matching module | Accepted owned tree, valid actions/audit files/messages, including `solution: none` | All guard checks pass before prepare; no product or module code executes inside lint | Tool/install/signature errors fail closed |
| Existing ownership failure | Drift, missing expected ref, invalid fixture controls | Existing ownership verdict precedes new checks; no npm tool installation or successor product stage | Preserve existing drift authorization semantics |
| Custom-action scope | Nested/dormant metadata of either extension; dirty/staged/sparse workspace | Inspect every committed workspace-root metadata blob, regardless of enablement or module-root | Nonregular metadata, invalid encoding/YAML or invalid action structure fail with logical path |
| Custom-action structure | Composite action with steps; ordinary YAML quoting, flow syntax or aliases | Require a single mapping document with `runs.using: composite`; validate actual step `uses` values, not strings inside run blocks | Node/Docker actions, duplicate keys, unsafe tags, multiple documents or malformed structure fail |
| Custom-action references | Local subaction or remote action | Permit normalized `./.github/actions/<directory>` with committed regular metadata, or third-party `owner/repo[/path]@<40-hex-SHA>` | Reject other local paths, traversal, expressions, floating/tag refs, Docker refs and Builds references at any pin; pins are checked textually |
| Deny list | Metadata contains checkout, setup-dotnet, actions/cache, `dapr init`, solution-wide dotnet build/test, nuget push, registry login or semantic-release | Name the offending action and rule; accept existing explicit-project sample test commands | Conservative textual matches may reject occasional legitimate text; no indirect-script interpretation |
| MSBuild audit bypass | Any tracked file with XML root Project, regardless of extension/namespace; element or attribute declarations | Reject blocking NoWarn codes under any parent, NuGetAuditSuppress, MSBuildWarningsAsMessages, NuGetAudit-prefixed TreatAsLocalProperty tokens, auditSources and the two prohibited test-filter properties | Report path/rule; fail malformed identified project XML, never evaluate imports/expressions |
| Response/config bypass | Case-insensitive `.rsp`, NuGet.Config or structurally identified NuGet configuration, including custom names | Apply the same textual forbidden declarations; include comma/semicolon/whitespace warning/property lists | Fail malformed/undecodable selected inputs; do not follow symlinks or gitlinks |
| Benign audit data | NoWarn NU1901/NU1902 or unrelated warnings/local properties, ordinary source/binary files, XML comments | No finding; trusted Builds root fixtures/Props are outside sample audit | No blanket rejection of all XML parse failures or every NuGetAudit property |
| PR event | Event base/head full SHAs, title, checkout possibly at synthetic merge | Lint every commit in base..head and the PR title, retaining existing title coverage | Reject invalid/missing endpoints; never substitute checkout merge/HEAD or narrow to last commit |
| Push event | Event before/after full SHAs, including multi-commit pushes | Lint all before..after commits; all-zero before means all commits reachable from after | All-zero after or unavailable nonzero endpoint fails; valid empty range passes |
| Dispatch/local interface | workflow_dispatch or explicit trusted local range | Dispatch lints exactly frozen HEAD; reusable explicit range supports later origin/main..HEAD integration | Unknown events/missing context fail; never silently fall back from a malformed event |
| Commit policy | Any raw selected message/title | Retain conventional 21.2.4 rules: existing ten types, header/body 200, footer 100, defaultIgnores false; additionally reject the five GitHub skip-marker forms and skip-checks trailer keys | Fail with commit identity/rule, safely escaped; markers checked anywhere in the raw message, including merge messages |
| Builds root/sample | Existing two CI calls and dependent Windows job | Root performs no new lint/tool install; sample audits its subtree, lints root actions and Builds-wide messages once; Linux/hooks/Windows remain green | Lint-only failure emits drift=false and prevents successor preparation/build/test/hook work |

</intent-contract>

## Code Map

All paths are Builds-relative unless marked CiCd. Anchors refer to the implementation baseline above.

- `Github/lib/guard.py:24,55` — `run(...)` emits false, validates context, compares, calls `require_clean`, loads sole CI config and checks enabled actions; `main()` supplies CLI/env/error handling. Extend this entrypoint rather than adding a parallel workflow stage.
- `Github/guard/action.yml:7` — single isolated Python invocation and drift output today. Add explicit pinned Node 24 setup only for linting contexts, without package-manager auto-detection/cache; keep npm/YAML/commit policy orchestration in Python after successful perimeter comparison.
- `Github/lib/expected_state.py:41,49,105,118,134,143,191` — `ExpectedStateError`, safe `Git`, context validation, sole-loader adapter, `tree_snapshot`, `Comparison`, comparison routing. `.actual` is the module/sample tree; `.workspace` is the full tree. Reuse these distinctions and escaped ownership diagnostics; release uses only comparison and stays unchanged.
- `Github/lib/perimeter.py:99,136` — `Snapshot.items` carries paths/modes/OIDs and `.read(path)` reads cached blob bytes; regular modes 100644/100755. Do not materialize module actions/projects or dereference nonregular entries.
- `.github/workflows/ci.yml:56,68` — nonrecursive/nonpersistent shallow checkout and first validation guard. Acquire complete event history with checkout `fetch-depth: 0`; preserve guard before prepare and all existing outputs/permissions. No separate commitlint step.
- `.github/workflows/builds-ci.yml:7,25,36,46` — root/sample calls and Windows delegation. Preserve title-edit coverage with explicit PR activity types including edited; sample is the sole Builds guard-commitlint execution. Existing setup-node pin is `949feb2413d6458794dcd2491c4babbbce0c15c1` (v7.1.0), with Node 24 and package-manager-cache false.
- `commitlint.config.mjs:1`, `package.json:50`, `package-lock.json` — existing policy and exact CLI/preset 21.2.4. Preset supplies footer 100 and other conventional rules, including its URL behavior. Root lock already pins `js-yaml` 4.3.2; its existing CLI can convert YAML stdin to JSON without custom JavaScript policy. New guard package makes all three dependencies explicit and exact; leave legacy root release configuration/dependency declarations intact.
- `node_modules/js-yaml/bin/js-yaml.js` — inspected installed third-party CLI, not a source dependency path to hard-code: YAML input becomes JSON, while JSON input becomes YAML. Prefix input with a YAML comment to force YAML-to-JSON even for JSON-style action documents, without introducing an extra document; require one mapping result. Flow/alias probes passed; duplicate keys and unsafe tags failed. Call the installed CLI from the isolated locked tool directory.
- `Github/lib/release_version.py:96` — `tool_environment`/`Plugins` demonstrate disposable trusted npm installation, sanitized npm/Node/Git/token environment and signature verification. Reuse the pattern without importing release-state behavior or installing semantic-release into the guard.
- `Github/lib/release_build.py:45`, `Github/release-build/release.targets:5` — existing global audit/warning/source controls; leave untouched. `Github/lib/tests/test_release_build.py:105,128,148` already exercises real vulnerable-package and warning-exemption behavior.
- `.github/actions/after-unit-tests/action.yml`, `.github/actions/sample-windows/action.yml` — both valid composites with explicit-project `dotnet test`; no action rewrite is needed. Workflow-owned `$/Github/prepare` in builds-ci.yml is outside action lint scope.
- `Github/lib/tests/test_guard.py:43`, `test_guard_adapter.py:125` — successful fixtures currently contain opaque/invalid YAML. Replace with valid composites and retain malformed cases as negative tests. Adapter currently concatenates run steps; upgrade it to execute actual composite uses/conditions/env, rather than skipping new Node/tool work.
- `Github/lib/tests/test_ci_environment.py:34,176,672` — expression-aware `CompositeHarness`, committed fixture setup and guard-failure successor checks. Extend with actual event payloads, Node mappings and tool accounting; distinguish command doubles from real pinned-policy evidence. `test_expected_state.py:31,58` supplies temporary Git repositories/anonymous transports.
- `Hexalith.Builds.slnx:23` — live caller file entry to remove with caller deletion. `Github/commitlint/tests/test_commitlint_workflow.py:10` has an unused caller constant; preserve its meaningful frozen-workflow execution tests. Delete any actual tests asserting deleted workflow text if found, including in frozen directories; retain historical docs/evidence.
- `Tools/ci/README.md:410,500`, `Samples/Hexalith.Sample/README.md:36` — current deferred-migration descriptions to update at implementation. `Tools/ci/run_python_tests.py:24` discovers new lib test files automatically on both interpreter lanes.
- CiCd story `1-*` and `module-inventory.md` — completed ruleset cut. Fresh scoped-profile read on 2026-11-13: Builds Protect main id 19196298 active on default branch, rules exactly deletion/non_fast_forward, bypass_actors empty. Read again before deletion; authorization failure leaves the prerequisite unverified.
- CiCd stories `2-*`, `3-*`, `4-*`, `5-1-*` — all done, execution checked. Historical attribution of caller retirement to 5-1 is superseded by 5-1's explicit retention. Renderer placeholders/empty production registry, deferred release-dispatch security questions and unrelated package-catalog findings remain outside this story.

## Tasks & Acceptance

**Execution:**

- [ ] `Github/guard/package.json`, `Github/guard/package-lock.json`, `Github/guard/commitlint.config.mjs`, `Github/guard/commitlint_bridge.mjs`, `Github/lib/commit_policy.py` (new), and root `commitlint.config.mjs` — create isolated exact CLI/preset 21.2.4 and js-yaml 4.3.2 tool pins; preserve the complete effective conventional policy and make root validation use the same added skip rule. Keep JavaScript limited to tool configuration/bridge; implement skip detection in stdlib Python, invoked by the custom rule over raw messages. Resolve preset/dependencies only from the trusted installed tool directory while passing explicit action-path config.
- [ ] `Github/lib/guard_tools.py` (new) — install only trusted manifest/lock bytes in a private temporary directory, with scripts disabled and signatures required. Sanitize npm/Node/Git/token configuration; pass YAML/messages via stdin/argument arrays, never shell interpolation. Expose parser/commitlint calls for test injection; no production remote/config override. Bound subprocess failure and safely report tool errors without raw control sequences or private paths.
- [ ] `Github/lib/guard_actions.py` (new) — enumerate committed root metadata, invoke the pinned parser, validate composite/step/reference structure and local targets, then apply the exact deny list. Cover ordinary YAML syntax without a handwritten restricted parser; validate resolved alias/flow references and retain readable deterministic path/rule diagnostics.
- [ ] `Github/lib/audit_lint.py` (new) — enumerate module snapshot blobs, identify Project XML by root rather than extension, and inspect all descendants/attributes using namespace-local, case-insensitive names. Add conservative response-file/NuGet-config scanning and exact blocking-token recognition described below; preserve safe unrelated sources and no filesystem traversal.
- [ ] `Github/lib/guard_commitlint.py` (new) — parse validated event data, freeze explicit full commit endpoints, enumerate whole messages with Git objects, and invoke the trusted CLI with explicit config. Keep PR title coverage, fail missing nonzero endpoints, support zero-before/empty ranges and later explicit local ranges. Never use module package discovery or path-filter the selected commits.
- [ ] `Github/lib/guard.py`, `Github/guard/action.yml`, `.github/workflows/ci.yml` — integrate checks into the existing guard, validate context before Builds-root bypass, acquire history, and configure trusted Node without caching or implicit package-manager setup. Preserve ownership-before-config/check ordering, frozen snapshot identities, false drift on lint-only errors and fail-fast successor suppression. Install npm tools once per guard execution after a successful comparison, sharing them between parser and commitlint.
- [ ] `Github/lib/tests/test_guard_actions.py`, `Github/lib/tests/test_audit_lint.py`, `Github/lib/tests/test_guard_commitlint.py`, `Github/lib/tests/test_commit_policy.py`, `Github/lib/tests/test_guard_tools.py` (new), plus existing guard/adapter/environment tests — execute the full matrix through real committed Git fixtures and actual composite/job mappings. Migrate opaque success metadata. Include real pinned CLI/config/parser tests alongside isolated tool-error controls, all policy length boundaries, fork/merge checkout differences, poison module npm/config/Node variables, malicious log controls and unchanged index/worktree checks.
- [ ] `.github/workflows/builds-ci.yml`, `.github/workflows/commitlint-caller.yml`, `Hexalith.Builds.slnx`, `Github/commitlint/tests/test_commitlint_workflow.py` — first reconfirm ruleset 19196298 with read-only API evidence and execute replacement sample guard coverage; then remove only the Builds caller and live readers in the same implementation change. Preserve title edited trigger coverage and frozen commitlint workflow execution tests. If the cut cannot be verified, retain the caller and report the implementation blocker; never infer absence from an API denial.
- [ ] `Tools/ci/README.md`, `Samples/Hexalith.Sample/README.md`, `docs/cicd-5-2-guard-lints-and-commitlint-results.md` (new at implementation) — explain lint scopes, event ranges, tooling trust and accepted text-lint limitations; retain real focused/dual-Python/lint/API and exact-source hosted root/sample/Windows results, including absence of independent caller execution. No implementation evidence is claimed by this planning run.

**Acceptance Criteria:**

- Given a module CI invocation, when any new guard check fails, then the actual guard composite fails before prepare/SDK/build/tests/hooks, reports the offending logical path or commit/rule plus ownership message, and emits no repair authorization unless the prior perimeter comparison actually found drift.
- Given a matching module with no solution, when CI executes, then action, audit and commit-message policy still run; successful enforcement does not depend on a product build being configured.
- Given committed actions or audit inputs that differ from dirty, staged, sparse or missing working-tree copies, when the guard CLI/composite executes, then its verdict depends only on pinned committed objects and leaves module content/index unchanged.
- Given a PR or multi-commit push, when the shared CI guard executes with the real event mapping, then the actual pinned commitlint CLI enforces every selected complete message and PR title with the trusted action-sourced policy, including merge commits, footer limits and skip rules; synthetic checkout commits and module config/plugins cannot alter the selection or policy.
- Given valid owned content and an allowed explicit-project custom action, when the action metadata is linted, then it passes ordinary YAML quoting/flow/alias forms and the existing sample actions remain runnable; any deny-listed primitive or disallowed actual uses reference fails even in a dormant nested action.
- Given an extensionless MSBuild project or PackageReference metadata that suppresses a blocking NuGet warning, when guard runs, then it fails before product work, closing the story-3-3 deferred gap without weakening or duplicating the release's existing real audit.
- Given Builds' existing root/sample/Windows topology, when exact-source Builds CI runs after caller retirement, then sample guard commitlint covers Builds-wide changes exactly once, root avoids module lint, and all retained product/quality/Python/Windows checks pass; no story-5-1 verification exception is inherited.
- Given fresh evidence of the completed ruleset cut and executable replacement coverage, when the implementation is delivered, then commitlint-caller.yml and live solution references are removed together, PR title edits retain validation, and the frozen reusable commitlint workflow and legacy module consumers remain intact.

## Spec Change Log

- 2026-11-13 implementation dispatch: the user invoked bmad-build-auto for this ready-for-dev story, instructed work/commit/push in references/Hexalith.Builds, and reiterated that caller deletion must follow story 1 ruleset cut. This dispatch resumes implementation; planning-only delivery wording in the original intent and historical result describes the prior completed planning run. Current execution includes all implementation tasks and gates above. Preserve the intent contract. The superproject already has the prior plan and Builds gitlink staged; preserve them, stage the final story and pushed gitlink, and leave its commit/push to the caller. The implementation starts at Builds `ceb3257147917002a2433be0ce9aac7db99e7698`; baseline_revision remains the current superproject HEAD.

## Review Triage Log

### 2026-11-13 — Review pass
- verdicts: 18 review-layer findings — high 0, medium 11, low 1, false 6, maybe-false 0
- review fixes are committed and pushed as `fe03043ab126a8c27fc3e4f799d4714dda7e73d2`; each patched row records its correction and regression evidence.
- findings:
  - `[medium]` `[patch]` Edge: a valid explicit-project command hides a later solution-wide command on the same line — parent reproduced `dotnet test Good.csproj && dotnet build` returning no deny finding; fixed by checking invocation prefixes separately, with chained-command regressions.
  - `[medium]` `[patch]` Edge: quoted primitive tokens bypass the deny list — parent reproduced `docker "login"`, `"nuget" push` and `dapr "init"` returning no finding; fixed with consistently quoted primitive-token patterns and real committed fixtures.
  - `[false]` `[reject]` Intent: retained historical planning-only wording describes an alternative reading — current user dispatch explicitly resumes this ready-for-dev story and authorizes Builds commit/push; the dispatch log records that interpretation without changing the frozen intent contract. No current scope defect follows.
  - `[false]` `[reject]` Intent: a source diff alone does not prove commit/push — parent verified actual full Builds HEAD and scoped GitHub exact-source run, and will verify the final remote ref; repository-state evidence supplies the separate surface, so no publication gap remains.
  - `[false]` `[reject]` Intent: final file absence alone does not prove ruleset-cut chronology — fresh filtered ruleset readback and real sample CLI success were retained before the implementation agent deleted the caller; parent read the evidence and implementation chronology. The supplied invocation did not request another administrative mutation.
  - `[false]` `[reject]` Intent: doubled harnesses and hosted execution are distinct evidence — tests label the doubles, real pinned CLI/Git integration tests pass, and all seven exact-source hosted jobs passed. The change makes no claim that a command double establishes npm signatures or hosted behavior.
  - `[false]` `[reject]` Intent: commitlint cannot start a GitHub-suppressed workflow — the intent contract explicitly documents that limit and detects raw markers whenever guard is invoked. No promised surface is missing.
  - `[false]` `[reject]` Intent: the full baseline includes native-process test grouping — Git history attributes it to independent upstream `02ed624aa19781cac75d2c9112940e9bd830441a`; story commits were rebased onto it, and results identify that boundary. It was not authored as part of this feature.
  - `[medium]` `[patch]` Blind: greedy command scanning misses a second solution-wide invocation — independently reproduced; shares the first edge finding's root cause; the same invocation-prefix fix and chained-command regressions apply.
  - `[medium]` `[patch]` Blind: actual Helm and crane registry-login verbs are absent — parent reproduced `helm registry login` and `crane auth login` returning no finding; fixed by adding the actual literal verb sequences and replacing ineffective fixtures.
  - `[medium]` `[patch]` Blind: ordinary quote handling is inconsistent across prohibited primitives — independently reproduced; shares the second edge finding's root cause; the same quote-aware primitive patterns and regressions apply.
  - `[medium]` `[patch]` Blind: quoted executable paths hide solution-wide dotnet calls — parent reproduced `"/usr/bin/dotnet" test` returning no finding; fixed with literal basename recognition plus Unix/Windows path regressions.
  - `[medium]` `[patch]` Blind: output redirection rejects a valid explicit-project command — parent reproduced both `dotnet test Tests.csproj > results.log` and `... 2>&1` receiving a solution-wide finding; fixed by consuming ordinary redirection operands separately; positive and chained negative controls pass.
  - `[medium]` `[patch]` Blind: quoted response-file property names bypass NoWarn matching — parent reproduced `/p:"NoWarn"=NU1903`; reviewer also observed real MSBuild returning NU1903 for that declaration. Fixed by recognizing matched ordinary property-name quotes; response-file regressions pass.
  - `[medium]` `[patch]` Blind: response values are truncated at XML delimiters — parent reproduced `/p:NoWarn="NU1901;<unrelated>;NU1903"` passing; reviewer verified real MSBuild preserves the complete value. Fixed by retaining literal assignment values; positive and blocking-token regressions pass.
  - `[medium]` `[patch]` Blind: malformed Project start tags after DOCTYPE evade classification — parent reproduced `<!DOCTYPE Project><Project NoWarn="NU1903>` returning no XML finding; fixed with lexical prolog classification, including external-DTD controls that never load entities.
  - `[medium]` `[patch]` Blind: malformed env/with step fields pass structural lint — parent reproduced run-step `env: "not a mapping"` and uses-step `with: []` yielding no findings; fixed with mapping-type checks and valid/invalid metadata controls.
  - `[low]` `[reject]` Blind: setup-node infrastructure failure precedes Python's ownership verdict/output — the ordering does leave drift unset, but no lint/module code or repair authorization runs; repair requires explicit true. Checkout/runtime acquisition already fail closed on unavailable infrastructure. Encountering this extra startup failure is uncommon, and moving comparison across the external action requires split phases or duplicate work rather than a direct correction. The retained guard comparison still precedes all npm install, config-driven lint and product execution.

Additional parent verification (separate from the 18 layer findings):

- `[medium]` `[patch]` Parent supplemental probe: BOM-less declared UTF-32 Project XML hides literal NU1903 — `_xml` currently accepts the encoded Project without a finding; fixed by classifying/decoding standard LE/BE signatures in both parse/probe paths; both encodings have valid and malformed controls.
- `[medium]` `[patch]` Parent patch inspection: the newly added DOCTYPE fallback backtracked exponentially on an unterminated internal subset containing repeated comments — isolated subprocess probes with 20 and 25 comments each exceeded two seconds; fixed by atomic internal-subset tokens. Isolated 20/25/1,000-comment regressions complete within the two-second bound.


### 2026-11-13 — Focused post-fix verification
- verdicts: 2 findings — high 0, medium 2, low 0, false 0, maybe-false 0
- findings:
  - `[medium]` `[patch]` Quoted absolute primitive paths bypass the first quote-aware patterns — the edge reviewer reproduced committed `"/usr/bin/docker" login`, `"/usr/local/bin/dapr" init` and a quoted Windows docker.exe invocation with the pinned YAML parser; the production pattern confirms it only matches a bare basename inside quotes. Fixed with a shared Unix/Windows executable-basename matcher without resolving/executing paths. Independent post-fix committed-fixture checks pass.
  - `[medium]` `[patch]` Strict env/with dictionary checks reject valid whole-map expressions — the edge reviewer reproduced valid fromJSON expression scalars being rejected. Parent read GitHub actions/runner v2.331.0 PipelineTemplateConverter: ConvertToStepEnvironment and ConvertToStepInputs accept expression tokens, and ConvertToStep passes allowExpressions:true. Fixed by lexically recognizing one whole-map expression token as unevaluated data, retaining nonmapping-literal and mixed expression/text failures. Independent post-fix checks pass.

The focused reviewer verified 20 exact cases against pushed `9ca3ffd520510567cd2af4c7db0a3d5db299c7be`: denied primitive paths and chained commands fail, whole-map env/with expressions pass unevaluated, and literal text/lists/numbers/booleans/null fail. No remaining failure was found in that requested scope.

## Design Notes

Use the pinned js-yaml CLI as an external data parser, with all lint decisions in Python. Planning probes used the root lock's existing 4.3.2: flow/aliases passed and duplicate keys/unsafe tags failed. Prefix a harmless YAML comment to prevent the CLI's reverse JSON-to-YAML mode while preserving an existing document marker. Reject a nonmapping/multidocument result; do not evaluate custom tags or module scripts. No runtime PyYAML import or JavaScript lint implementation is needed.

The action deny scan covers metadata text, including run blocks; indirect scripts are not recursively discovered. Recognize checkout/setup/cache references case-insensitively; literal shell/PowerShell command forms of dapr init, nuget/dotnet nuget push, semantic-release/npx semantic-release and registry login (including docker/podman/helm/oras/crane/skopeo login, az acr login, docker/login-action, azure/docker-login and aws-actions/amazon-ecr-login). Treat dotnet build/test with no explicit project, a directory or `.sln`/`.slnx` argument as solution-wide. Explicit positional `.csproj` and `--project <file.csproj>` forms are allowed, including quoted paths; sample commands are positive controls. Text pins and ordinary command recognition do not claim to defeat shell indirection.

Audit properties are matched by XML local name, including attributes and item metadata under any parent. NoWarn blocking codes are whole case-insensitive tokens NU1900/NU1903/NU1904/NU1905, separated by comma, semicolon or whitespace. TreatAsLocalProperty is tokenized the same way and rejects every NuGetAudit-prefixed token. Preserve NU1901/2 and unrelated local properties. Parse XML bytes with BOM/declared encodings and namespaces; ignore XML comments. A recognizable Project root followed by malformed XML fails; ordinary non-XML/binary files do not. Never expand property expressions or follow computed imports: obfuscated NoWarn/computed imports are accepted residuals in enforcement.md.

Identify canonical NuGet.Config case-insensitively and custom-named NuGet configuration by a configuration root with NuGet sections (including auditSources/packageSources/packageSourceMapping/trustedSigners). Probe tracked XML without an extension allowlist so custom filenames cannot hide a literal auditSources section. Known NuGet config names with malformed contents fail. Response files use conservative text recognition of the same declarations, including quoted `/p:`/`-p:` forms; harmless comments there may match. Selected nonregular sources fail without following their targets. This lint does not forbid every NuGetAudit property: existing release global flags already override ordinary local assignments.

Implement skip detection case-insensitively over the full raw message: bracketed skip ci, ci skip, no ci, skip actions and actions skip, allowing horizontal whitespace; reject any line declaring a skip-checks trailer key regardless of value. The five forms and true-trailer syntax are documented by [GitHub](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/skip-workflow-runs). This conservative policy does not promise to run a workflow GitHub already suppressed; it detects such messages whenever the guard is invoked, including a later containing range or dispatch. Preserve defaultIgnores=false so conventional merge-message failures are not hidden.

Use complete checkout history rather than silently retrying with --last. PR selection uses event base/head objects, while content lint continues to inspect the frozen checkout commit, including GitHub's merge checkout. A zero-before creation push denotes the empty base and validates all reachable after commits; an unavailable nonzero base fails. Explicit local ranges are an API seam only; adding check.py belongs to its later story.

Planning delivery follows the earlier Builds plans: commit/push the Builds plan only, then stage the canonical CiCd story with the updated pushed Builds gitlink. Leave the superproject commit/push to the caller. At implementation time review both the Builds diff since implementation_baseline_revision and CiCd diff since baseline_revision; a superproject gitlink alone is not the implementation diff.

## Verification

Implementation verification on 2026-11-13: all 14 matrix rows have executed passing coverage in both locked local lanes (14/14 groups, 878 tests per lane under Python 3.12.13 and 3.14.4 with Node 24.22.1). The final two regressions passed focused checks afterward and appear in both exact-source hosted lanes (14/14 groups, 880 tests each, 464 lib tests). Parent checks passed guard 57, audit 15 and raw policy 3. Online workflow lint and public API checks passed. Full source `af34585a72b220753d7f83bcb48a400a301b6eac` passed normal hosted run 43464051267 with all seven retained jobs green, including root/sample/Linux/hooks and dependent Windows. The source run listing contains only builds-ci.yml. Fresh ruleset readback and real sample guard replacement execution preceded caller deletion. Initial fixture/token/event-path failures were fixed and rerun without exemptions. Details are in Builds docs/cicd-5-2-guard-lints-and-commitlint-results.md.

Run implementation commands from `references/Hexalith.Builds`; they are future gates, not results of this planning run.

**Commands:**

- `python3 -m unittest discover -s Github/lib/tests -p 'test_guard*.py' -v` and equivalent `test_audit_lint.py`, `test_commit_policy.py` discovery — matrix, real-Git, CLI/composite and policy cases pass. Ensure required pinned tools are installed, and separately identify real-tool versus doubled subprocess evidence.
- Locked `uv run --no-cache --locked --script --python 3.12 Tools/ci/run_python_tests.py` and the same command with the captured runner interpreter — every discovered group passes on both lanes; no skip/allow-failure for new guard tests.
- `python3 Tools/ci/lint_workflows.py` — pinned actionlint/zizmor, online audits and tool-signature prerequisites pass; no blanket suppressions.
- `python3 Tools/ci/check_public_api.py` — no unapproved public interface removals; exempt fixture inputs remain fixtures.
- `GH_CONFIG_DIR=/home/administrator/.config/gh-cicd-agent gh api repos/Hexalith/Hexalith.Builds/rulesets/19196298` — immediately before deletion, confirm active default-branch protection, exactly deletion/non_fast_forward and no bypass actors; retain filtered readback without credentials.
- Repository pinned commitlint CLI against exact proposed commit-message file; `git diff --check` and frozen-file/scope inspection — clean and conventional policy validation passes.
- Exact implementation commit's normal `builds-ci.yml` run — all retained jobs, both Python lanes, root/sample/Linux/hooks and dependent Windows pass; retain full source SHA/run/job identities and independent review before completion. No production release/adoption is needed for qualification.

Planning validation is limited to contract/code investigation, fresh ruleset readback, parser probes, spec/path/metadata inspection, whitespace and exact-message commitlint. No runtime, workflow, test, dependency, ruleset or caller change is authorized in this planning delivery.

## Auto Run Result

Status: ready-for-dev

Halted after planning as explicitly requested. The ready-for-development gate passed after contract/continuity investigation with three subagents, direct source inspection and self-review. All implementation tasks remain unchecked; no implementation or implementation-verification result is claimed.

The Builds planning document `docs/cicd-5-2-guard-lints-and-commitlint-plan.md` is committed and pushed to main as `ceb3257147917002a2433be0ce9aac7db99e7698`. The full identifier was obtained with git rev-parse HEAD and independently matched the remote refs/heads/main readback. Builds is clean. This canonical story and that pushed gitlink are staged together in CiCd; its commit/push remains with the caller.

Planning checks passed: full baseline identities and frontmatter, complete intent/matrix/tasks, Given/When/Then acceptance, both repositories' whitespace checks, safe pinned-parser controls, and the exact commit message under @commitlint/cli 21.2.4 (zero problems/warnings). Scoped-agent GitHub readback confirmed the completed story-1 ruleset cut without administrative changes. The plan requires another readback before caller retirement and working replacement coverage in the same implementation change. `commitlint-caller.yml` remains unchanged and present.
