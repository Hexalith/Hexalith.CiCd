# Story 16 local implementation and qualification

The implementation worktree is `/home/administrator/projects/hexalith/cicd-story-16`.
The original CiCd baseline, original module gitlinks, production Builds pin and
registration are preserved. This implementation phase permits local source
changes and qualification only. It does not publish a Builds release, push
product preparation, perform App delivery, alter repository administration or
observe live CI/nightly acceptance.

## Managed build-order isolation

The producer's ordinary retained-property guard rejects import replacement on
project references. The existing frozen MinimalModule fixture needs a separate
build root and independently locked package graph. A generic, managed-only
contract now permits this narrow build-order edge while retaining the ordinary
reconciliation guard for all other edges and legacy commands.

`HexalithIsolatedBuildContract` selects a closed `hexalith.isolated-build.v1`
source declaration. The declaration binds the actual owner, explicit child
projects, tracked source roots, target framework, external props/targets and a
reserved-prefix-safe namespace for fixture options. Its owner must be a
non-test, non-packable, non-publishable project with default compile disabled;
the edge must have `ReferenceOutputAssembly=false` and package Release mode.

The producer checks every declared tracked source byte against the authenticated
module Git revision. Descriptor, owner, children and import files must themselves
be tracked within those roots. Module-local authored imports outside the checked roots refuse. The exact two
SDK-originated `.nuget.g.props`/`.nuget.g.targets` imports are independently
regenerated in private scratch using the authenticated child properties,
tracked successor lock and the active catalog's NuGet configuration. Their
bytes and the assets target/library graphs must match. This verifies restored
outputs without admitting arbitrary obj files or module-authored imports.
It performs a bounded additional locked restore solely for this verification;
it does not compile the child or rebuild the root. Witnesses are removed before
the task returns. Imports from the actual active catalog are separately checked against
that catalog's Git revision. Reparse paths, changed source and stale identities
refuse. The allowed property set is closed: framework/package selection, locked
restore, exactly the selected external imports, the real catalog root, preserved
inherited common-targets chain, empty warning demotions and namespaced fixture
options. No arbitrary managed AdditionalProperties are admitted. Child evaluation
must remain nonshipping, import both exact external files and preserve the
inherited release-targets chain. The common cross-targeting chain and global
release audit properties continue through normal MSBuild inheritance.

This shared support is source-bound and generic; the producer contains no
Conversations project names or exception paths. The module descriptor and
adapter supply its product-specific graph. The four historical fixture projects
and their original locks remain unchanged and outside the root solution; only
the new non-test adapter joins the root solution.

## Evidence and scope

`run-source-qualification.sh`, invoked through `run-with-temp`, copies exact
working source inputs into private scratch, builds with warnings as errors,
packs a private source-only 6.1.0 tool, installs it from an exclusive local feed
and invokes its commands. This version is not a release or a production pin.
The focused managed/candidate/isolation tests include a real Git positive case
with a distinct external catalog, both actual actions/checkout HTTPS origin
forms, and credential/query/fragment/alternate-origin refusals.

The broad Workspace run did not pass: it reported HXR021 readiness failures,
three context-dependent skips and was terminated after exceeding twenty minutes.
Its causality is unverified; it contributes no claimed passing matrix coverage.
See `broad-workspace-regression.log` for the retained failure output. Focused new
feature cases are reported separately in `managed-producer-tests.log`.

The standalone fixture and adapter source qualification logs establish package
lock and seven-case behavior only. Native Windows protected-checkout evidence
is in `windows-implementation-qualification.json`. Full Windows module/product
acceptance remains dependent on the real released prerequisites and adopted CI.

Root npm files are deliberately preserved during product preparation. After App
delivery removes its owned selectors, a later product cleanup may remove the
remaining files only after verifying selector absence and normal checker success.
The candidate qualification mask preserves whole partial-owner files, including
npm files, and offers no owned-selector exception.

## Local Dapr lifetime

Candidate qualification uses the digest-verified shared CLI installer. A scoped
shim invokes that exact executable with its private runtime path and rejects
child replacement/init/uninstall. PATH is restored even on failure; HOME is
never repurposed. The retained product tests require host control-plane ports,
so the qualifier refuses existing standard Dapr containers or occupied ports
instead of changing runtime assertions or using network-only initialization.
The setup marks init-created containers through its private Docker shim and
uses a unique labeled scheduler volume. Cleanup checks ownership labels and
removes exact IDs only; unrelated containers appearing after preflight survive.
An ownership-replaced volume is preserved and cleanup fails visibly.

The actual workspace has all four existing user Dapr containers. The real
occupied-host preflight refused before download/init/volume creation and a
before/after readback confirmed container IDs/names unchanged. Genuine product
qualification therefore also requires an unused local Dapr control plane. The
seven controlled isolation cases establish successful/failed cleanup and exact
child executable selection separately; they do not claim live runtime success.
Pinned CLI behavior was checked against its [init source](https://github.com/dapr/cli/blob/v1.19.1/cmd/init.go)
and [standalone control-plane source](https://github.com/dapr/cli/blob/v1.19.1/pkg/standalone/standalone.go).

## Windows history and native TestSupport fixtures

Protected source fetch now obtains the exact selected commit with complete
ancestor history, rather than a depth-one clone. The bootstrap refuses a shallow
result and verifies the revision walk. This is generic source checkout policy,
with no module-specific commit IDs. A real-Git control reads an ancestor's exact
bytes after the fetch and verifies ancestry; the retained historical TestSupport
root is an actual ancestor of the Conversations baseline.

Native TestSupport source qualification supplies the unchanged signed data files,
source declaration and authentic Git commit object required by its complete DLL.
Its temporary repositories live beside the owning fixture checkout, matching the
runner's workspace/TEMP boundary. The Windows machine has no .NET 11 runtime;
qualification installs exact 11.0.0 under disposable NTFS scratch only and checks
the archive SHA-512 from [Microsoft release metadata](https://builds.dotnet.microsoft.com/dotnet/release-metadata/11.0/releases.json).
The real module action continues to run the entire already built DLL without
filters; fixture execution is distinct from released-input adopted Windows CI.

The partial-volume creation path is also owned: cleanup records the create
attempt before invoking Docker, then probes the exact nonce/name and ownership
label even when the client fails after server-side creation. Absence is accepted;
foreign ownership is preserved. The create-then-client-failure control leaves no
owned volume behind.

Caller generation retains the three-input interface for older tagged schemas.
Only a contract declaring both additive nullable fields receives the seven-input
Windows caller. Offline source-interface and pinned-interface regressions qualify
both paths before any supporting release or registration is selected.

## Final handoff

Local source checks are complete. All task-local wrapper jobs exited and removed
their scratch, including the private native Windows runtime. No commits, pushes
or repository administration were performed. All three worktrees pass whitespace
checks. Root npm files, module tool/Platform prerequisites, owned files, frozen
fixture source, production Builds pin and actual registration/render remain
preserved as recorded in `verification-results.json`.

| Completed scope | Result | Retained evidence |
| --- | --- | --- |
| Python 3.12.13 | 233 passed across 13 groups | `python-3.12.13-results.json` and per-group logs |
| Python 3.14.4 | 233 passed across 13 groups | `python-3.14.4-results.json` and per-group logs |
| Strict .NET source build | 0 warnings/errors | `managed-producer-build.log` |
| New producer/contracts | 12 passed, 0 skipped | `managed-producer-tests.log` |
| Selected legacy producer/root/Platform | 138 passed, 0 skipped | `legacy-producer-regression.log` |
| Private source CLI package | pack/install/invoke; real external-catalog positive | `source-package-qualification.log`, `managed-producer-tests.log` |
| Adapter and locks | audited restore/build; 7 fixture and 3 overlay cases; tampering refused | `managed-adapter-source-qualification.log` |
| Changed product test projects | 3 strict builds; 1 projection-key and 20 portable assertions | `managed-adapter-source-qualification.log` |
| Packages | 5 payload/symbol pairs; public and testing consumers passed | `managed-adapter-source-qualification.log` |
| Native Windows TestSupport | full unfiltered DLL: 44 passed, 0 skipped/not-run | `testsupport-native-windows-source.log` |
| Native protected sparse-index checkout | complement, archive identities, aliases and protection passed | `windows-implementation-qualification.json` |
| Offline renderer / validator | 33 / 51 passed | `renderer-regressions.log`, `validator-regressions.log` |
| Render / qualifier lock | unchanged / valid | `render-check.log`, `qualification-lock-check.log` |

The next concrete dependency is an acceptable published Builds/CLI release that
contains this source support. Select the real released module tool and Platform
prerequisites, recheck successor locks against that release's actual catalog, and
then run the committed exact-input qualification. Source-only private version
6.1.0, the synthetic identity fixtures and these package outputs grant no
production or adoption authority.

AD-21 administration, real product preparation/push, released registration/render,
App delivery/preservation, full released-input CI and adopted normal checker,
immutable release readback, legacy access retirement and scheduled nightly remain
pending. Existing Dapr containers also prevent genuine local integration on this
host; they were preserved. The failed broad Workspace run remains excluded from
passing coverage and its causality remains unverified. No passing broader suite,
actual adoption or nightly outcome is claimed.
