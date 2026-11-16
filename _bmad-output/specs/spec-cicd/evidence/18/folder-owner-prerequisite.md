# Folder owner prerequisite for the package product matrix

The actual `Hexalith.Folders.Server` executable must expose its existing command
policy factory through the SDK's public `RouteCatalogAdapterSourceAttribute`.
The prior package fixture attempted to load `Hexalith.Folders.EventStore.dll`
from the Server output. That DLL is outside its dependency closure; the actual
Server had no compiled adapter factory. The SDK requires the factory in the
selected actual owner image or its real dependency closure.

The repair changes these Folder-owned product files:

- `src/Hexalith.Folders.Server/Hexalith.Folders.Server.csproj` links existing
  same-module policy implementations and their shared factory into the owner.
- `src/Hexalith.Folders.Server/FolderServerCatalogAdapterSource.cs` exposes the
  owner's compiled factory through the public SDK attribute.
- `src/Hexalith.Folders.EventStore/{FoldersCatalogAdapterSource,FoldersCatalogAdapters}.cs`
  preserve the existing gateway API and share its unchanged eighteen policies.
- `tests/Hexalith.Folders.Server.Tests/{Hexalith.Folders.Server.Tests.csproj,FolderServerCatalogAdapterSourceTests.cs}`
  qualify complete declaration coverage and all thirty-six retained golden
  intent variants from the existing product fixture.

No Debug/source guard changes, new external source-library reference, new
adapter policy, or product command behavior are introduced. Projects uses the
already released `Hexalith.Folders` 2.0.0 library and EventStore 5.1.1 APIs.
`package-folder-api-inspection-2.log` records the public type/signature checks.
The absent `Hexalith.Folders.EventStore` NuGet package is **not** a publication
prerequisite: the repaired Server is an actual nonpackable owner executable.

Before delivery, the corrected owner source must exist in a separately
qualified, authenticated remote Folder commit. Its normal checker and push
prerequisites apply; Projects' preparation exception does not cover Folders.
No unpushed owner revision may be recorded as a delivered gitlink. This local
implementation authorizes no Folder push or publication and requires no new
adapter NuGet package or version.

Local qualification is recorded in `matrix-folder-product.log` (exit 0):

- Release/package owner, Server tests and gateway tests compile with zero
  warnings/errors and all analyzers/audits enabled.
- Two focused owner controls pass: eighteen exact declarations and thirty-six
  retained golden semantic-intent/scope variants.
- Server: 1,439 discovered, **1,428 passed**, zero failed/skipped, eleven explicit
  not run; 510.353 seconds. The two new controls are included in that count.
- Gateway: 124 discovered/passed, zero failed/skipped/not-run; 8.421 seconds.
- The same snapshot's fixture safety/credential lane: 36 passed, zero failures/skips.

The eleven not-run rows belong to
`EnrolledWorkloadSourceBoundaryTests.ActualIssuerAndIndependentSdkGuardEverySourceRequest`:
`none`, `credential`, `caller`, `tenant`, `audience`, `signature`, `scope`,
`expired`, `malformed`, `missing-proof`, `cancelled`. They verify real Keycloak
issuer/SDK metadata-source refusal boundaries using a mocked source transport.
They do not test the new command policy factory or establish actual enrollment.
The existing shared owner CI allowlists these exact rows as delegated to
Platform's `infrastructure/keycloak-workload-binding/verify_component.py`.
That verifier builds the provider and provisions a private real Keycloak
component, then supplies `HEXALITH_WORKLOAD_COMPONENT_FILE`; the `none` row also
requires exact Debug/source SDK runtime hashes and paths. Those requirements
were not fabricated from Release binaries or bypassed.

Separately, the existing owner after-unit wrapper
`tests/tools/run-complete-project-tests.ps1` enables explicit tests without
provisioning that source verifier. This is an existing pipeline limitation;
its missing prerequisite is not repaired or hidden by this migration. The
ordinary Server/gateway and new factory results above remain distinct from
those eleven unexecuted component rows. No Explicit/skip/source guard changed.
The log records exact baseline revisions and candidate content hashes.
