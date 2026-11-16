# Older local preparation candidate — a575 session

This report belongs only to the local candidate based on Parties
`a575021fc97a8eda664711089270b60f5e570ded`. It does not describe or qualify the
concurrent published preparation
`0f261ccd3b461102dcac35da2e074d15a195ebb4`. The root index now records that newer
published gitlink; this session did not change it. The older checkout delta is
preserved in `preparation-a575-local-candidate.patch` for reconciliation, not
delivery. Do not apply it over the published preparation without comparison.

No push, remote administration, registration, App delivery, credential cleanup,
publication or release acceptance was performed by this session. No commits or
new candidate commit messages were created. All verification children completed
and their `run-with-temp` workspaces were removed. No browser or graph-only job
was started after the concurrent implementation was identified. The shared spec
was left for the parent to reconcile; this session did not add either duplicate
baseline key or modify the other session's implementation notes/evidence.

## Changes in this candidate

- Removed the obsolete workflow/agent/controller tests and controller scripts,
  including `tests/ci-lifecycle`, root tool-only npm files and Gitlink/history
  controls. The eight owned workflows and all delivered/foreign instructions,
  Claude settings, `.gitmodules` and Builds gitlink were preserved.
- Split mixed checks into `BrowserProductTests`, `ContainerProductTests` and
  `DependencyGraphTests`; retained package inventory, browser specifications,
  OCI archives, strict calendar/source/version provenance, runtime assets and
  dependency compilation/boundary checks. Removed historical Epic 8 closure,
  owner-delivery and matrix/receipt bookkeeping. The legacy persisted-state
  compatibility fixture is still consumed by its actual projection test.
- Preserved all native integration/lifecycle/attached-lifecycle and general
  runtime test sources. Removed obsolete native build exclusions from both
  solutions and updated the standalone solution assertion accordingly.
- Declared matching Aspire orchestration/dashboard package assets in the
  existing AppHost restore, retaining CLI-bundle mode. The package dependency
  helper now verifies existing executables without restoring a scratch AppHost.
- Enrolled `parties`, `parties-mcp` and `parties-ui` through
  `HexalithPublishContainer`; mapped shared source/version and rejected
  contradictory module provenance. Existing created-time validation remains
  mandatory; no invented timestamp property or audit waiver was introduced.
- Added a dormant `after-unit-tests` product action for declarations/ACL and
  prebuilt browser scenarios, retaining reports. No registration enables it.
- Updated active CI/release/development documentation and retained the previous
  CI/release documents under `docs/history` as historical evidence.

The complete path inventory is `preparation-a575-changed-paths.txt`. The final
patch SHA-256 is
`b9ead09d433f8984e4058968bbd968e26a5e9760e648b38d537b6163b4e88464`.

## Verification and its exact limits

`local-verification.json` and `local-source-inputs.json` bind the latest complete
verification snapshot to selected Builds `v6.0.6` at
`fdda17c0a4538b0f7c99f813c20ca24b49006530` and EventStore 5.1.1. These local
dependency clones used exact Git objects without initializing nested submodules.
The actual Parties-owned Builds gitlink remained unchanged; this is selected-
Builds migration preparation, not proof of the old legacy pipeline.

| Check | Observed result |
| --- | --- |
| Package-mode standalone Release build, audit enabled, warnings as errors | Passed; zero warnings/errors, including all three native assemblies |
| Retained/changed browser-contract, package, OCI and provenance cases | 114 passed; zero failed/skipped |
| Dependency graph and retained architecture cases in that snapshot | 66 passed; zero failed/skipped |
| Product declaration render `--check` | Passed |
| Product declaration Python suite | Six passed, one failed: it still requires the removed AttachedLifecycleTests `Build Project="false"` entry |
| `uv run --locked --script tools/render.py --check` | Passed; `renderer.json` |
| Existing owned/partial-owned files and direct gitlinks | All 14 file bytes/modes and all 10 gitlinks unchanged; `owned-perimeter.json` |
| XML, changed shell and Python syntax; whitespace | Passed for the checked snapshot; `local-syntax.json` and `git diff --check` |
| Actual Playwright execution | Not reached after declaration failure; no browser qualification claimed |
| Native runtime/authentication/persistence/cleanup execution | Not executed; compilation is not live qualification |
| Guard/action lint, exact-message commitlint, full retained-suite qualification | Not completed; no preparation push was attempted |
| Committed-candidate validation, hosted CI, App delivery, nightly | Not performed by this local session |

After that verification snapshot, one existing package/source consumer loop was
extracted from the removed mixed historical matrix test into
`DependencyGraphTests.PackageAndExplicitSourceConsumersPreserveDependencyBoundaries`.
That preservation change was not built/run before the concurrent-candidate
freeze. `preparation-a575-final-state.json` identifies it as the sole module
file differing from the verified snapshot. `preparation-a575-final-source-inputs.json`
binds the final saved patch. The 66-case result must not be presented as covering
this later additional case.

Earlier successful preparation results and unsuccessful fixture/graph attempts
remain separately named: `product-preparation-passed-*`, `baseline-archive-*`,
`aspire-bundle-diagnostic-*`, `graph-metadata-diagnostic-*`,
`tenants-cohort-diagnostic-*` and `runtime-asset-conflict-*`. They are not
acceptance evidence for the newer published candidate.

## Incomplete work and blocked acceptance

The native/runtime graph experiment is inactive and preserved as
`runtime-graph-prototype.patch`. It exposed an unqualified old Tenants source
pin and then duplicate native/wrapper compressed Admin UI assets. The temporary
Tenants gitlink update and prototype code were restored; no dependency gitlink
change remains in this candidate. Configuration propagation, static-asset
ownership and initial-build receipt creation still require qualification.

`native-reuse-prerequisite.md` records the exact pinned published tool interface:
it issues the required private native channels but always builds/restores into
new test output. Its CLI has no supported prebuilt-artifact reuse option. Direct
DLL execution without equivalent authenticated issuance/provenance is not
substitute coverage. Native after-integration routing, explicit lifecycle
classification, separation of environment-sensitive general tests, compatibility
cohort routing and catalog/public-package runner reuse remain incomplete here.

Frozen publisher-created support still needs its separate acceptable release
and selected pin before Parties timestamp adaptation/adoption. This session did
not reverify/provision App selection, AD-21 settings, scoped NuGet/Zot/org grants,
or pilot/migration-order acceptance. Registration/render, App adoption,
immutability/legacy-grant cleanup, the normal adopted checker, green hosted CI
and the genuine next-night result remain open in this session. No story task or
acceptance criterion is certified complete by this report.

The concurrent published preparation supersedes this local candidate. Reconcile
the older patch with that verified work and preserve its evidence before further
implementation; the parent owns checkout alignment and the shared spec.

## Root checkout reconciliation

The separate published preparation supersedes this candidate. After all children
finished, the root agent saved the complete older working tree and untracked
files in module stash `93704e4ad8cf71e971a775b4771eb26cbc218b91`, then aligned
the clean module checkout with CiCd's recorded revision
`0f261ccd3b461102dcac35da2e074d15a195ebb4`. No remote operation or parent
gitlink change was performed. See [preservation proof](preparation-a575-checkout-preservation.json).
The canonical story baseline is retained once; this session's duplicate field
was removed. Workflow review was not entered because full tasks and acceptance
remain incomplete.
