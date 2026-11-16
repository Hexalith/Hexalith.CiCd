# Story 16: protected Windows checkout and isolated fixture

Planning design, 2026-11-16. No production edits, pushes, external configuration
changes or product test execution were performed. Native Windows prototypes
used private Windows-accessible directories beneath `run-with-temp`'s TMPDIR;
all child work finished and scratch directories were removed. JSON observations
are retained beside this document.

## Windows problem and demonstrated solution

Conversations main `9e24c280efd5e9c13826eab9bc8b8b687a7bee09` has 49,433 tracked
entries. Exactly eighteen historical blobs lie beneath nine `http-cache`
directories whose children contain `$ps:`. Every excluded directory has tree
OID `482386e46eca707fda8582051cbde288cdb77d0d`. Exact paths and current native
index-validation results are in `windows-current-tree-path-probe.json`.

The available native Git is `2.55.0.windows.4`. Synthetic native probes with
`core.protectNTFS=true` on **every** command establish:

| Operation | Observation |
| --- | --- |
| Noncone exclusions, ordinary index | Checkout refuses the colon path. |
| Cone exclusions, ordinary index | Checkout refuses the colon path. |
| Cone exclusions **and sparse index** | Protected checkout succeeds; archive subtree remains a `040000` index tree entry; status is clean. |
| Whole-index `ls-files --stage` | Refuses expansion into invalid archive paths. |
| Targeted `ls-files --stage -- references/Builds` | Succeeds. |
| `ls-tree`, `diff HEAD`, status and `write-tree` | Succeed without expanding the excluded subtree. |
| `sparse-checkout disable` | Refuses unsafe expansion. |
| Native `submodule update --init --checkout` | Git exits 139 in this sparse-index topology; do not use it in the opt-in path. |
| Explicit contained dependency `init`/fetch/checkout | Succeeds at exact gitlink; parent status stays clean and `write-tree` equals original tree. |

See `windows-checkout-probe.json`,
`windows-sparse-index-operations-probe.json` and
`windows-direct-dependency-probe.json`. These are checkout/index prototypes,
not qualification of the actual product DLLs or GitHub runner image.

The current main's other 49,415 paths/modes/blob IDs were separately inserted
into a temporary native protected Git index. There was no diagnostic and exact
metadata readback matched. This validates current path input, not full checkout,
Windows case-collision policy, product execution or future candidates.

Pinned actions/checkout configures sparse patterns before checkout, but its cone
implementation invokes `sparse-checkout set` without `--sparse-index`. Passing
negative patterns to the current action is insufficient. The new opt-in branch
must own metadata initialization and cone sparse-index checkout.
Sources: [pinned checkout ordering](https://raw.githubusercontent.com/actions/checkout/3d3c42e5aac5ba805825da76410c181273ba90b1/src/git-source-provider.ts),
[pinned sparse command implementation](https://raw.githubusercontent.com/actions/checkout/3d3c42e5aac5ba805825da76410c181273ba90b1/src/git-command-manager.ts).

## Generic API and ownership

Add optional `windowsCheckout`, default `null`, to the versioned CI schema and
strict loader. Its nonnull shape is:

```yaml
windowsCheckout:
  exclude:
    - path: repository/relative/archive-directory
      tree: full-lowercase-git-tree-oid
```

`exclude` is a nonempty array of exact directory paths and full tree OIDs;
reject unknown fields, duplicate/case-alias/overlapping paths, absolute paths,
traversal, control characters, expressions and malformed object identifiers.
The path itself must be safe on Windows; unsafe names occur only below it.
Reject exclusions overlapping solution, SDK, manifest, enabled action or direct
dependency paths. Excluded trees must not contain symlinks or gitlinks. Their
use for immutable non-product archives is reviewed centrally; they are not a
module-owned skip mechanism. Exact tree binding refuses newly concealed bytes.

No module name, archive name or hardcoded module path enters Builds. Its shared
CI validates and exports compact `windows-checkout` JSON; rendered Windows
callers pass that output literally to `Github/prepare`. `null` keeps existing
ordinary actions/checkout behavior. Windows never reads module CI JSON to select
this behavior. Main Linux CI and release continue to see the complete tree.

Suggested new implementation: `Github/prepare/prepare_windows_checkout.py`,
called from the released remote composite using its own `GITHUB_ACTION_PATH`.
It may use the hosted runner's existing native Python with an explicit supported
version check, or equivalent PowerShell/.NET byte handling; no setup-Python,
Dapr, browser or other environment-installation step is needed on Windows.

## Opt-in bootstrap algorithm

1. Validate the input and exact requested commit before expanding any module
   source. Require a fresh contained workspace and native Git; reject ambient
   Git repository/index/object-directory selectors and disabled path protection.
   Initialize/fetch the public module's exact commit without checkout, recursion,
   persisted credentials or source execution. Keep NTFS protection enabled and
   use command-local `core.longpaths=true`.
2. Read complete NUL-delimited tree metadata. Resolve every excluded directory
   to its exact `040000` tree at that commit and require its configured OID.
   Determine the full materialized complement. Reuse the old guard's **safe**
   generic checks: native Windows ordinal case/prefix collision detection and a
   separate protected temporary native index containing the complement. Require
   exact mode/OID/path readback and no ignored/diagnosed path. Do not copy its
   `protectNTFS=false` command or its module constants.
3. Compute a cone definition from the tree, not user-supplied patterns. Begin
   with `/*` and `!/*/`. Walk ordinary directory nodes in deterministic order:
   skip an excluded directory; include an entire subtree with no excluded
   descendant; otherwise emit its parent-only state `/directory/` followed by
   `!/directory/*/` and recurse. This preserves files immediately in split
   ancestors even where no safe child directory exists. Gitlinks are leaves.
   Escape literal Git-pattern metacharacters; never insert raw input as patterns.
4. Set `core.sparseCheckout=true`, `core.sparseCheckoutCone=true` and
   `index.sparse=true` in the private repository; write the computed cone file.
   Perform protected forced detached checkout of the exact commit. The native
   prototype verifies ancestor-only states, safe siblings and excluded trees
   without a fake/sentinel directory or a protection exception.
5. Require exact HEAD and `write-tree == HEAD^{tree}`. Read
   `ls-files --sparse --stage -z`, logically expand its directory entries through
   object metadata and compare the complete map with the original tree. This is
   **not** native full-index expansion. Require the omitted workspace entries
   to be exactly the configured archive trees, with all other paths available,
   clean protected status and archives never materialized. Recheck tree bindings.
6. Initialize only validated direct gitlinks needed by Windows. Read their paths,
   URLs and exact commits from committed `.gitmodules`/HEAD metadata. Use fresh
   contained child Git repositories, anonymous HTTPS fetch of the exact commit
   and protected detached checkout, not the parent submodule helper. Reject
   existing unexpected children, traversal, URL substitution and pin mismatch;
   never recurse. Each child is a real separate checkout recognized by the
   checker/producer. After SDK setup, shared managed preparation supplies genuine
   mapping imports; normal restore/build then runs once.

The managed producer must likewise retain targeted metadata reads and never
expand the complete native index or call a parent submodule helper. Its exact
dependency checkouts already exist when preparation begins. The parallel
shared-preparation design covers this API boundary and active catalog authority.

Qualification must include real Windows Git tests for unchanged default callers,
root-only and ancestor-file cones, multiple exact exclusions, changed archive
OID, newly unsafe source, case/prefix aliases, symlink/gitlink exclusions,
malformed JSON, malicious paths, unavailable pins and dependency failures. Run
full actual Conversations protected checkout and Windows product tests before
adoption/completion; prototypes do not establish those outcomes.

## Isolated minimal fixture adapter

Add a new non-test SDK project at
`tests/compatibility/MinimalModule/Hexalith.Conversations.MinimalModule.Compatibility.csproj`.
Include only this adapter in `Hexalith.Conversations.slnx`. It declares
`IsTestProject=false`, `IsPackable=false`, `IsPublishable=false` and disables
default compile items so its directory's `RegisteredCommandTests.cs` is not
accidentally compiled into the adapter. Reference the original fixture Tests
and AppHost projects with `ReferenceOutputAssembly=false`; their internal edges
build Contracts and Server, preserving all four fixture projects outside the
root solution and their independent package configuration.

Per-reference additional properties select the existing package overlay,
`TargetFramework=net11.0`, `MinimalModuleCompatibilityMode=package`,
`MinimalModuleCompatibilityUseSuccessorLocks=true`, and the external framework/
target imports. Critically, `GlobalPropertiesToRemove` alone does not remove
producer values inherited from process environment. Explicitly override these
keys for the entire fixture reference graph:

- Blank `CustomBeforeDirectoryBuildProps`,
  `CustomBeforeDirectoryBuildTargets`, `CustomAfterDirectoryBuildTargets` and
  `AfterMicrosoftNETSdkTargets`.
- Set `CustomAfterMicrosoftCommonProps` to external `Framework.props` and
  `CustomAfterMicrosoftCommonTargets` to external `RegisteredCommand.targets`.
- Set active `WarningsNotAsErrors` to empty so the historical fixture's literal
  warning demotions cannot weaken the current graph; remove active module root
  waivers. Preserve the historical sample bytes rather than promising to both
  delete their line and preserve the same bytes.

Verify how NuGet restore graph traversal carries these properties, rather than
assuming build-only ProjectReference behavior proves restore isolation. The
adapter's `GetTargetFrameworks`/restore entry points must select the same graph,
not fall back to the old external EventStore source edges. The direct Builds
catalog/version probe must receive the new actual checkout. Deliberately update
the external overlay and four successor locks against the chosen released
catalog, then confirm an independent empty-cache locked restore leaves them
unchanged. Original locks, package defaults and seven assertions remain.

The new `after-unit-tests` action runs only the built fixture test DLL. To retain
strict missing/duplicate/skipped-result detection without writing evidence
artifacts, a product-side `run_compatibility.py` can consume the native xUnit
JSON reporter in memory: run with `-automated sync -failSkips -noAutoReporters
-reporter json`, require zero process failure/errors/skips and exactly the
existing seven fully qualified passed test identities. Reuse the expected-test
set from `verify_results.py`; keep its XML path for external local verification.
Do not add checkout, restore, build, setup or uploads to the action.
The [official xUnit reporter documentation](https://xunit.net/docs/getting-started/v3/custom-runner-reporter)
documents JSON messages on stdout and explicit reporter selection; qualify the
actual pinned 4.0.3 message protocol during implementation.

Meaningful fixture qualification: prove one root restore/build produces all
four isolated project outputs, no producer import leaks or extra source
dependency initialization, correct successor locks and exactly seven passing
assertions. Exercise missing, duplicate, failed and skipped native-result
records during CiCd's qualification of the runner; do not add a result-gate
self-test lane to module product automation. The adapter remains a design pending that execution;
there is no claimed successful product build in this planning artifact.
