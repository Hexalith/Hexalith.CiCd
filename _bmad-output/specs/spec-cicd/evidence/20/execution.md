# Story 20 local implementation handoff

This phase makes local changes only. It creates no source commit, push, release,
adoption, GitHub administration change, Azure authority or live Azure run. The
original workspace is untouched. All disposable build/test exports used
`run-with-temp`; useful logs and results are retained beside this file.

Starting source identities for composed review are:

| Repository | Starting HEAD |
| --- | --- |
| CiCd | `d3f3ef864c08cd89e390246d1a5d1dedffc4a92b` |
| Builds | `fdda17c0a4538b0f7c99f813c20ca24b49006530` |
| EventStore | `f85419d501f279e9a813435aa73538185ad26ada` |

`local-identities.json` records paths, local origin/main identities and branch
state. These are local observations, not a fresh remote-main readback. The
planning preflight remains the last administrative readback. EventStore's entire
owned/legacy workflow, CI/dependency configuration, instruction/settings files,
Builds gitlink, `.gitmodules`, release/commitlint configuration and npm/Husky
assets remain unchanged in this worktree. The current production render check
passes; `builds-version` remains `v6.0.6`.

Builds adds a compatible manual qualification job shape, same-source CI output,
private preparation request validation and a build-only environment-preserving
mode. Existing Windows jobs retain their shape. CiCd renders explicit manual
selection, private runner/environment and literal per-action secret mappings;
ordinary reusable CI gains no Azure secret input. Bounded optional CI timeout and stable additional SDK fields
forward the existing reusable workflow inputs; module actions install no SDK. The schema preserves existing
public property paths.

EventStore adds managed offline, integration, nightly-broker and Azure actions.
The Azure live project is explicitly routed to its manual action, while its
unchanged offline authority-schema class runs in the unit hook without Azure
secrets. Payload projects are included in the shared build. Packing supports
existing Release outputs; isolated package and historical consumers retain their
own builds. The private 1.18.2 supervisor uses existing port/OQ8 overrides and
exact owned container IDs, leaving shared 1.19.1 infrastructure intact. Catalog,
payload, compatibility and Kubernetes runtime pins remain distinct. These real
fixtures have not been executed in this local phase.

The gate inventory is in `gate-migration.json`. Mixed C# retirement was checked
with syntax members and compiled through the affected Contracts test project.
ReleasePackageManifest retains 17 independent product methods and their 13
reachable helpers. PostgreSQL fixture, OCI provenance and process-consumer
assertions remain. Workflow, agent-tool and story-governance tests and the
DeferredWorkGovernance project are retired. The existing CA1822 product failure
in ProductionProfileValidationResult was fixed using initialized get-only
instance properties; no analyzer suppression was added.

Focused verification passed:

- Python 3.12: renderer 34, validator 52, loader/schema 20, fixture/request 9.
- Runner Python 3.14: renderer 34, validator 52, loader/schema 20,
  pipeline 35, local-check 37, public-API suite 28, fixture/request 9,
  and route-catalog fixture controls 6.
- Final request/preparation changes were retested with both Python versions:
  2 pipeline request tests, 2 manual-render tests and 1 manual-validator test.
- Both affected C# projects compile in isolated Release/package mode with
  mandatory analyzers enabled. Compiled focused tests pass: 9 package/fixture
  cases and 28 infrastructure selector/port/OQ8 cases, zero skips.
- The candidate public-surface probe recorded zero removals before the final
  two optional preparation input additions. Production render remains unchanged.
- The executable bootstrap verifier correctly refused the uncommitted local
  candidate before any remote access; see `bootstrap-local-refusal.json`.

Exact final C# commands and results are in `product-verification-final.json`,
`*.build-final.log` and `*.focused-final.log`. The initial whole-solution shared
Release build failed on the original CA1822 properties; its log is
`product-release-build.log`. After fixing that product failure and correcting
mixed-file pruning, the two affected project builds and focused tests passed.
The bounded integration verification below supersedes the earlier affected-
project-only build result. The complete offline package/consumer hook and live
fixtures remain pending. Earlier failed logs are retained for traceability.

Before any preparation push, run the executable `pre-adoption-verify.py` under
`run-with-temp` with exact committed base/head and a compatible acceptable
Builds tag/SHA, saving its report outside TMPDIR. It checks clean committed
source, explicit source identities, accepted-adoption absence, complete
unchanged non-product bytes/modes/gitlinks, both shared and owning commitlint,
action/audit policy, shared Release build/unit routines and offline package/
consumer coverage. It clones/detaches only already available direct Builds, Tenants, Platform and
FrontComposer repositories and never initializes nested submodules. The product
preview uses the exact selected trusted Builds release, separately records the
unchanged source gitlink, and checks clean Git worktrees. Module-agent
authentication uses its established token file as a process-local GH_TOKEN
override, never as a gh profile; secret material is redacted from command output. Missing dependencies, permissions or
required checks block the push. Repeat fresh base/head/adoption checks at the
actual push boundary. This is not a check.py mode and expires on adoption.

Operational work remains in the approved AD-21 order:

1. Refresh identity/authentication and maintainer prerequisite readbacks with
   the intended profiles. Verify installation selection, exact rulesets,
   immutable tag protection, NuGet policies, Zot identities and managed secret/
   variable selections. Provision the private runner and approval environment;
   authority/custody inputs remain owner-supplied.
2. Qualify, publish and read back a compatible immutable Builds minor release
   through the interactive shared release process. Do not fabricate a tag/pin.
3. Commit EventStore product preparation from freshly fetched main using the
   module-agent identity; require the approved verifier before every push.
   Preserve the legacy publishing/npm assets while it remains unadopted.
4. After enabled actions exist on live main, use `planned-registration.yml`
   and the acceptable released tag to create one real committed setup/pin/render
   candidate. Validate it with locked `tools/check_global.py` and
   `tools/validate.py`; these committed-candidate/remote checks are pending here.
   Delivery alone replaces EventStore's owned portions.
5. Immediately after actual App adoption, enable immutable releases, retire
   the legacy NuGet policies/grants/Zot access, and remove root tool-only npm/
   lock/Husky assets that legacy publishing still needs today. The exception
   has expired: require the normal module `check.py`, green adopted CI, and
   separately authorized qualification/prerequisite reporting.
6. Record the next actual scheduled-night publication or valid no-release
   result and its run links before completing story 20. No Azure fault run is
   implied or authorized by this handoff.

`planned-registration.yml` and `planned-configuration.json` are staged inputs,
not a production registration or adopted configuration. The full live fixture
runtime behavior of the pinned 1.18.2 image, complete
package consumers, release audit, fresh source/permission state, accepted render,
normal checker, hosted CI, manual Azure qualification and nightly outcomes remain
unverified until their prerequisites and execution are supplied.

The retained OCI provenance tests now publish a tiny isolated SDK fixture that
imports the actual module Directory.Build.targets. They retain real multi-RID
archive, manifest and provenance assertions, and malformed-input cases retain the
real target. The complete Contracts project passed these checks: 1,418 passed,
zero failed and two existing package-inventory skips. It no longer rebuilds the
current module through a second publish.

The bounded integration verification is complete. The whole-solution shared
Release build passed with zero warnings/errors on tree
`d336e56e7df1ee11e6d79010033c429a24410604`. The final source tree is
`1c24e5d1fea496e143ffefff8a1eae1787ddaaf6`: six later files restore four
evaluated container defaults, remove the synthetic stage outcome wrapper, and
annotate the four upload-artifact pins; a seventh marks the plain TestSubscriber
fixture host `IsTestProject=false` while retaining its build. No real test is
excluded by that helper correction. Native TRX and fixture reports remain.

`integration-unit-summary.json` records every project and its exact source log.
Composed local verification covers all 21 actual unit projects: **18,487
succeeded, zero unresolved failures, and 51 existing skips**. It retains the
verified unchanged prefix and 8,442 non-repeated Server successes, and replaces
its unchanged three-case ABI fixture with an authentic-cache rerun. The extra
container-default test passes once. This is explicit composed evidence; it does
not claim one fresh complete final-tree solution run.

The initial Server archive assertion failed because the developer global cache
contained the documented unsigned local same-version Tenants fixture (81a33…);
the pinned public package remains e21f5…. The existing copy target materialized
the authentic unchanged package and DLL from an empty private NuGet cache; its
signature is 12,983 bytes and all three unchanged ABI cases pass. Global cache
and pins were untouched. Bootstrap and previews now use private packages, HTTP
and plugins caches. The attempted stack sample occurred after the host exited;
no diagnostic tool was installed and no heap/environment data was captured.

A later partial-solution preview built undeclared references in Debug despite
Release test outputs. Its exact failed assertion/log is retained. Final targeted
verification instead builds projects directly with mandatory shared Release and
analyzer flags, rejects any Debug output, and passes the defaults test (1), ABI
class (3), ServiceDefaults (160), SignalR (64) and Testing (341). The exact
commands and results are in `integration-direct-release-verification.json` and
its referenced logs. All child jobs have finished.

Actual action/audit lint passes on the final tree, with the unchanged deny list.
**Activation is blocked:** the unchanged source-coverage scanner reports **56
diagnostics across 22 selected files** in `scan-source-coverage.json`, including
computed cwd/env, wrapper substitution, import/search-path changes and
environment/path exports. This is an unresolved pipeline capability defect; no
audit was weakened, excluded or bypassed. Story 20 remains in progress.

The compatible release, accepted registration/pin/delivery, required normal
checker after adoption, hosted CI, complete offline package/consumer hook, live
fixture runs, Azure qualification and nightly outcome remain pending. The
post-adoption npm/Husky retirement and normal-checker requirement above still
apply. No source commit, push, provisioning or live authority action occurred.

Review patch pass: the preceding `1c24e5d1…` tree and 18,487 composed unit
successes are historical pre-patch results, not a fresh run on these patches.
The new EventStore tree is `6e553e7c62500e4b7029a35fd4d06dd8577e2054`. Exact grouped
reviewer mappings, commands, counts and logs are in `review-patch-resolution.json`;
the leading-newline history regression is covered there without duplicating
the parent's P1 triage row.

Targeted Python 3.12 checks pass: bootstrap 9, catalog 7, product fixtures 14,
and request entrypoint/composite 3. Parent independently verified Python 3.14.
Both affected C# projects build in Release with mandatory analyzers and zero
warnings/errors. Restored Azure packaging checks pass (one test). The actual
cross-language test passes in package mode and developer default mode; package
mode preserves current Contracts DLL and restore-assets hashes and timestamps.
No complete unit suite was rerun. All patch child jobs have finished.

The official immutable 1.18.2 image index/content is now read back in
`legacy-runtime-image-readback.json` and pinned by digest. Runtime execution
remains unverified; the registry readback is not runtime qualification.
Standalone legacy jobs retain their build defaults, while managed callers
explicitly reuse shared output. Preparation scope/history/auth/freshness and
exceptional fixture cleanup controls are strengthened without changing frozen
intent or owned module portions.

Activation remains blocked by the unchanged source-coverage scanner: the latest
parent snapshot `scan-source-coverage-review.json` reports 58 diagnostics across
22 selected files. The earlier 56-diagnostic snapshot remains historical. No
audit was bypassed or weakened. Publication, registration/adoption and live
operations remain pending; source edits remain local and uncommitted.

Parent final verification is recorded in `review-parent-verification.json`.
All 19 patch findings are resolved. Actual integrity-locked action policy and
unchanged audit lint pass on the final local snapshot; all tracked whitespace
checks pass. The 59 changed EventStore paths match the fixed preparation
allowlist. The latest coverage report still blocks activation, so the BMAD
review gate stops before completion/commit; the spec remains `in-review`.
Production pin/registration/render and module-owned portions remain unchanged.
All verification jobs have finished.

User-authorized main publication, 2026-11-16: fresh main publication candidates
are in `/home/administrator/projects/hexalith/cicd-publish-story-20`. Concurrent
Builds updates required two integrations; all newer preparation, protected
checkout, platform, tooling and timeout support was preserved. Final Builds
checks pass: configuration 23, pipeline 40, preparation 34 and protected-checkout
controls 10, plus actual locked online workflow/security lints, commitlint and
public-API compatibility (2,657 entries, zero removals). Builds commit
`c751d23aa4e73e8f7d74579db26a9fcf1df4c8e5` was pushed by ordinary fast-forward
to main using the configured CiCd-agent profile; remote main readback matches.

EventStore preparation commit `fa93b05ee7f9396f83190b1f09d0c72b897ed962` is local
on fresh main. Its actual approved pre-adoption verification failed with
`.github/hexalith-ci.json: $: unknown keys: additionalSdkVersion, ciTimeoutMinutes`
against the latest acceptable published Builds release, v6.0.6. No product
build/unit/offline success on this newly integrated commit is claimed. The
full command and failure are in `publish-result.json` and
`publish-eventstore-pre-adoption.json`. A compatible immutable release must
precede successful complete verification and any EventStore push. Planned
configuration now materializes current candidate schema defaults, without
changing a production pin or registration.

The required submodules-first rule in
`references/Hexalith.AI.Tools/hexalith-git-instructions.md:82` holds the CiCd
parent before commit/push while EventStore is blocked. Its changes are retained
on `publish/story20-main`; renderer37 and validator53 passed during integration,
but final committed-candidate checks remain pending. Original worktrees are
preserved. All child jobs have finished. `publish-result.json` is the publication
handoff; it explicitly records that all changes have not been pushed.

Preparation/adoption contract correction: the EventStore-only bootstrap now
materializes a separately labeled local stages 1–3 configuration for the exact
selected immutable Builds release, including v6.0.6/fdda17c0…. It no longer
requires the future manual-job API before product preparation. Adoption still
requires a compatible acceptable released API and the normal adoption gates.
The CLI/tag/SHA trust, account, expiry, ownership/history, freshness and product
failure checks are unchanged.

The projection preserves every ordinary integration entry and exclusion/route.
It accepts only the sole exact payload-azure job and exact Azure live exclusion,
remapping that exclusion to the existing after-unit-tests offline authority-
schema hook. Azure service cases remain unexecuted and authority-owned. No
Windows job is fabricated or accepted as an extra preparation route. The
additional SDK is required to appear in actual `dotnet --list-sdks` output; no
SDK is installed. Only documented disabled/default unsupported policy may be
omitted; enabled/non-default or unknown policy fails closed. The planned and
production configurations are untouched.

Targeted verification: `run-with-temp python3 -B -m unittest discover -s
_bmad-output/specs/spec-cicd/evidence/20 -p test_pre_adoption_verify.py -v` passes
14 tests, retaining the nine existing perimeter/history/access controls. Five
new checks use the actual materialized v6.0.6 loader and schema, controlled SDK
subprocess output, route preservation and unsupported-policy refusals, including
an extra legacy Windows job. See `preparation-stage-projection-tests.log` and
`preparation-stage-projection-patch.json`. Historical results are not relabeled;
no broad product gate ran in this patch. The parent will run the actual complete
approved preparation gate. Scanner/adoption prerequisites remain unchanged.


Verification repairs under the subsequent explicit `fix` request: the first
complete preparation run reached Client tests and exposed contention against its
unchanged 100ms discovery deadline. The next run passed Client and Contracts,
then exposed process-wide admission contention in ReminderDiscoveryOwnershipTests.
The two classes now reuse existing collections that disable parallel execution;
production code, deadlines, assertions and recovery counts are unchanged.
Focused classes pass 17 and 5 cases respectively, with zero skips. Exact paths
are added to the fixed preparation allowlist (61 total).

The preparation verifier completes all classified unit projects using the
unchanged released unit runner, collects only its PipelineError failures and
raises before package checks if any fail. This improves failure reporting and
preserves nonzero outcomes. All 17 bootstrap controls pass on Python 3.12 with
pinned jsonschema and on runner Python 3.14; the initial bare 3.12 invocation
failed because that interpreter lacked jsonschema, then passed with the pinned
dependency. See fix-bootstrap-final.json and reminder-discovery-collection-fix.json.

The final CiCd publication worktree is
`/home/administrator/projects/hexalith/cicd-publish-story-20-final`. Its latest
main integration preserves the concurrent Projects gate repair, candidate-signing
work, published Builds pointer and deferred-work entries. The direct Windows
rendering fixture supplies an empty manual_jobs context; all forwarding assertions
remain. EventStore publication and committed-candidate validation are still
pending this repair record and will be recorded separately on completion.


The third complete preparation run finished all 21 classified unit projects:
18,724 successes, 51 existing skips and one failure, the unchanged tracked-
content secret scan. Seven upstream fixture expressions were reported. Fresh
main d8171e6cc18cd4b67ea310822b36e49d007fa2ec already fixes six of them; those
published fixes are preserved. Only the remaining V2 literal is changed to a
runtime-generated canary, preserving all validation and redaction assertions.
Focused builds have zero warnings/errors; the whole V2 class passes 105 cases
and the unchanged tracked scanner passes, with zero skips.

The preparation allowlist adds only that exact V2 fixture path (62 total).
Rebasing onto d817 preserved its standalone guarded-write driver and transport
fixture. The modify/delete conflict in test_phase_4_story_5_3.py was resolved by
retaining its retirement: the newly added cases certify story-completion
metadata, evidence and tooling behavior, which CiCd policy removes from module
gates. No independent product assertion from that file is lost. The fourth
actual preparation run uses this fresh base and committed head
`db9122b30252b0cc9c6183a075464d7de99bbd01`; its result remains pending here.


The fourth run passed the fresh Release build and Client suite, then failed
RealMultiRidArchiveContainsExactProvenanceInBothChildConfigs. SDK11's OCI layer
creation referenced a different, already-deleted job's temporary directory.
Read-only worker inspection confirmed a persistent MSBuild node retaining stale
scratch paths. This is a fixture process-lifetime defect, not failed provenance
assertions. The parent cancelled only that failed run's private process group;
the wrapper exited143 and removed its scratch. Other jobs and shared servers
were not signaled. This fourth run did not finish all unit projects and is not
passing verification; fix4-cancellation.json labels that limitation explicitly.

The patch adds the installed SDK's standard --disable-build-servers flag to the
two real fixture publish invocations, retaining both multi-RID provenance checks,
all timeouts and assertions. Its focused verification and the replacement full
gate are pending this entry. No allowlist expansion is needed for this existing
reviewed product fixture path.


OCI containment verification passes: the complete product fixture class runs
21 cases, including actual archive publication, with zero failures/skips. Its
Release build has zero warnings/errors. The existing allowlist stays at62.
The correction is committed as f4d749627f4e80396821c0d95ddb600e6239f0b3,
on freshly fetched d8171e6cc18cd4b67ea310822b36e49d007fa2ec. Exact owning
commitlint21.2.4 validation is in fix-oci-commitlint.json. The fifth full gate
uses those exact committed inputs; its result remains pending this entry.


The unchanged actual tracked-content scanner also passes directly against the
complete fresh-base tree at f4d749627f4e80396821c0d95ddb600e6239f0b3:
1 case, zero failures/skips, no build or restore. This closes the focused-
preview gap for newly imported upstream driver/transport files. The required
complete Server project and fifth full gate still run independently; this
focused result does not replace either gate.


The fifth run completed all21 projects. Contracts (including OCI), Client,
DomainService and the actual tracked-content secret scan all passed. Its only
failure was the canceled-protocol activation test's final recoverable-outbox
assertion. The harness released native success before observing protocol-wait
cancellation, allowing two legitimate completion paths to race. Investigation
and a test-only cancellation-observation barrier are pending this entry; no
production cleanup, lease or cancellation contract is weakened. This run is
failed verification and does not authorize a push.


The activation drain fixture now waits for its fake guard to observe protocol
cancellation before releasing native completion. Production deliberately permits
cleanup after proven success; the test now establishes the intended canceled-
protocol scenario without racing that valid path. No production code, assertion,
five-second bound or matrix case changes. The full activation-worker class passes
34 cases with zero failures/skips, and its Release build has zero warnings/errors.
Only the exact Drain.cs path is added to both preparation allowlists (63 paths).

The barrier is committed as 06a37746beabb886e8e96208852ff947b883d735 on fresh
d8171e6cc18cd4b67ea310822b36e49d007fa2ec. Its exact owning commitlint21.2.4
validation is in fix-activation-commitlint.json. The sixth complete preparation
gate uses those committed inputs; its result remains pending this entry.


Fresh-main integration retained the generalized `execution_jobs` / `shared_ci_call`
renderer, separate qualification workflow, Linux/matrix/nightly lanes and protected
Windows metadata. The duplicate CI-dispatch manual lane is removed. Explicit
`qualification.yml` dispatch selects `job=payload-azure` and `authority-sha256`;
its default nightly selection never selects manual Azure. Fresh green-source CI,
private runner/environment, literal secrets and preservation-mode preparation
remain required. The unpublished EventStore action now consumes the generic
`HEXALITH_AUTHORITY_SHA256` / `HEXALITH_SOURCE_SHA` environment contract, mapping
it to the unchanged digest/source/expiry/custody validator. No Azure execution,
registration, production version change or adoption is claimed.

The final publication root was preserved through stash/fast-forward/pop from
38c36d8196d15a55f748f00370543a90ee918049 to current main
195d03e2d0a4ef43da623c2542faa9079c80c811 (main advanced after the initial
f76fe24 inspection). The stash remains at
9a2179cadc23a85fbf912a8d8ec10e4ac553c8a5 as a reversible recovery point.
Other stories' upstream files and Story20 historical evidence remain intact.
The direct Builds checkout is the published parent pin
4a23d186f31331b856e7aa87e12aba16384f5f6a; production `builds-version` and
EventStore registration remain unchanged. Renderer 46 and validator 54 cases
pass on both Python3.12 and3.14. Strict Azure request controls pass five cases
on each. See generic-qualification-focused-tests.json for exact commands/hashes;
these results cover the integration snapshot and do not relabel historical
product gates or remove the recorded activation scanner prerequisite.

Gate6 completed all21 classified unit projects with18,725 successes and51 existing
skips. Offline authority-schema15, payload1245, invariant1 and initial package /
consumer / API controls passed before the external-protection fixture failed on
its missing root npm CLI. The paired source-trust assertions are retained. Its
hook now obtains the signed integrity-locked21.2.4 CLI in existing disposable
scratch and passes exact fixture inputs. Before adoption it preserves the root
legacy policy bytes; after retirement it uses the selected direct Builds
canonical policy. Only the exact loop7 test path is added to preparation
allowlists (64 paths). Focused paired/shipped-role checks remain separately
recorded; this correction is not a new full-gate pass.


The paired-tool correction passes focused qualification: legacy-policy1 and
canonical-policy1, shipped-role closure7, and managed-hook/Azure controls10;
all have zero failures/skips. The exact-policy mutation intentionally exits1 at
the unchanged policy assertion. Actual edited composite controls reject both
invalid digest and mismatched source before service commands; released action
lint passes. The initial optional control-driver import/signature errors remain
visible in the attempt records and are resolved by the bounded supplementary
control, with no product-suite rerun. managed-paired-commitlint-fix.json records
each actual/expected exit and the final aggregate disposition. All child jobs
finished. The parent must commit the batched module changes and run the next
complete fresh preparation gate; these focused checks do not replace it.


The adapter and paired-fixture prerequisite are committed together as
b172ba50cc835083271ecf78911c8184e0378ff1 on freshly fetched
d8171e6cc18cd4b67ea310822b36e49d007fa2ec. Exact owning commitlint21.2.4
validation is recorded in fix-qualification-contracts-commitlint.json. The
seventh complete preparation gate runs those exact committed inputs. Earlier
all-unit success remains bound to06a37746; it does not relabel this new gate.


Gate7 again passed all21 .NET unit projects and the earlier offline Azure-schema,
payload, package, consumer and API checks. External-protection139 cases passed
with the previously recorded configured-component skip. Dapr qualification then
failed on a stale bound fixture hash; this remains failed full-gate evidence.
The two historical Dapr lock files are immutable. Their1.19.1 fixture bytes are
now retained exactly from c94e6fffaf2d689c94bb288f151a65e10a2fea82 using the
existing trusted historical-input archive resolver. The Platform schema3 file is
a working current-source descriptor: only its changed fixture/helper/test-source
and transitive archive bindings are refreshed. Runtime, binary, image, chart,
source tuples and authority fields remain byte-for-byte equivalent as values;
no historical packet or validator is edited. The AppendDurabilityRace class is
not selected by these runtime lanes, so no unrelated binding is added.

The complete affected `test_dapr*qualification.py` discovery (including imported
Platform configuration controls) passes159 cases with zero failures/skips on
the actual gate interpreter Python3.14.4. Helper byte drift and a resealed helper
substitution are both rejected by the unchanged validator. The first focused
attempt remains failed historical evidence: it missed the archive manifest's
transitive binding and its uv Python3.12 build lacks native os.pidfd_open custody
support. That interpreter limitation was not repaired by weakening a check.
Exact commands, hashes, preview tree and results are in
dapr-current-source-bindings-fix.json; the first attempt has separate retained
JSON/logs. Both preparation allowlists add only the three reviewed product paths
(67 total). All child jobs finished; no live service or full offline rerun took
place. Parent commit and complete fresh gate8 remain required.


Dapr current-source bindings are repaired without changing either historical
lock, validator, tests, runtime/image/binary/chart/authority identity. Exact old
fixture bytes are retained with provenance in the existing trusted archive;
only the Platform current descriptor's affected source/helper/archive inventory
changes. All159 focused Python controls and two helper-drift/resealed-inventory
refusals pass under the gate's systemPython3.14.4. The first failed preview is
retained, including its additional uvPython3.12 pidfd_open limitation. Three
exact product paths bring both preparation allowlists to67.

Fresh EventStore main advanced to8d409495926a568c5e2679f726b76f7de5dd85d5.
The rebase preserves all new dependency gitlinks and upstream V2 canary repair;
the duplicate local canary commit is dropped. The newly extended story/tooling
phase4 gate remains retired per module gate policy, while its standalone
utility and unrelated source stay preserved. The referenced Builds16cf commit
is authenticated as an ancestor of remote Builds main. Disposable product
preview still selects the approved immutable v6.0.6/fdda release and records
the unchanged source gitlink separately.

The rebased candidate is7322215e5803365c398044d2da9abad17e33ed8e. The eighth
complete preparation gate binds it to the new fresh main and actual dependency
revisions; its result remains pending this entry. No earlier pass is relabeled.


Gate9's known Server failure is the keyed-semaphore fixture's post-release flag
race: Dispose released the mutex before the test signaled firstReleased, so a
legitimate second acquisition could observe the flag unset. The focused patch
removes that flag, Task.Run and the arbitrary50ms delay. It starts the second
AcquireAsync while the first lease remains held and asserts the returned task
is pending, then releases the first, awaits/owns the second and asserts both
its retained entry and final Count==0 cleanup. Production KeyedSemaphore and
the other three test cases are unchanged.

The complete KeyedSemaphoreTests class passes4 cases with zero failures/skips
under isolated exact Builds v6.0.6/fdda Release/package/analyzer flags. The
Server.Tests build has zero warnings/errors. Exact commands, source hash,
preview tree and rationale are in keyed-semaphore-synchronization-fix.json.
Only the exact reviewed test path is added to both preparation allowlists
(68 total). All child jobs finished and focused scratch was removed. The
independent active gate9 was untouched; this focused correction does not turn
its known failure into passing verification. Parent commit and fresh complete
gate10 remain required.


The next freshness check stopped before build when main advanced again to
3b2350e7c1fff640131f8101596c78a59e31a03f. Rebase preserves its production
profile bridge and owned workflow changes. The modified phase4-transition
wrapper gate remains retired because its new assertions certify publication /
story tooling bindings; the separate bridge source and tests are preserved.
The new complete run found one keyed-semaphore test race: a lease was released
before the flag asserted by the resumed waiter was set. The fix directly proves
that the second acquisition remains pending while the first lease is held, then
checks the second lease and final dictionary cleanup. No production change,
sleep, skip, retry or weakened assertion is introduced. All4 focused class
cases pass, zero skips, with zero Release/analyzer warnings/errors. Both
allowlists add only that exact path (68 total). The fix is committed as
22e2e2470ed5d692b2bf4970251d02b5c1823f9f; exact owning CLI validation is
in fix-keyed-semaphore-commitlint.json. Full qualification remains pending.


Final complete EventStore preparation qualification PASSED on
22e2e2470ed5d692b2bf4970251d02b5c1823f9f, base3b2350e7c..., with exact immutable
v6.0.6/fdda released policy and stages. All21 unit projects pass (18,725 successes,
51 existing skips), complete applicable offline checks, package inventory,
13 package consumers plus CLI tool and old/new folded-snapshot compatibility
pass. Immediate freshness/adoption checks pass. The established module-agent
credential pushed ordinary fast-forward to main, and authenticated remote
readback matches. GitHub reported its configured PR/required-status bypass;
this receipt claims local preparation qualification, not green hosted CI.
See source-publication-status.md and fix-eventstore-main-push.json.

The final CiCd integration advances to current main5c35859, preserves all
concurrent work and its published Builds8d89 pin, and records only the already
published EventStore revision. Parent committed-candidate validation/push remain
the final source-publication steps. Story20 stays in review; no activation,
registration, production pin change, live authority or release is performed.
