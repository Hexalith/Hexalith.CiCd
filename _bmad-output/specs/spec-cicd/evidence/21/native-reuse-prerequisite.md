# Native execution prerequisite discovered during local preparation

The existing native integration, lifecycle and attached-lifecycle scenarios are
preserved. Their assemblies compile with EventStore 5.1.1, but the released
execution interface cannot currently run them from the shared initial build.

Parties pins module CLI 5.2.2. Its source tag resolves locally to
`02ed624aa19781cac75d2c9112940e9bd830441a`. At that exact tag,
`src/libraries/Hexalith.Builds.Tooling/Runtime/NativeTestExecutor.cs:146`
constructs `dotnet test --project` without `--no-build` or `--no-restore`.
The selected execution at line 573 additionally chooses a new private
`test-builds` artifacts directory. `CompositionEngineOptions.NativeDotnetCommand`
is internal test injection, with no matching public CLI option. These are local
Git-object observations of the pinned source, not remote release verification.

The tool issues and verifies the private authenticated test-environment
descriptor, owner/access channels, deadline, source mapping, report path and
cleanup plan. The retained tests cross-check these bindings. Starting the same
DLL with invented environment values, changing the declared executor, or
relabeling old CI receipts does not establish equivalent native coverage.
Calling the existing tool in a hook would perform another restore/build and
therefore fails the approved reuse requirement.

A generic published interface needs to accept an explicitly bound prebuilt test
artifact while retaining all current descriptor, access, cancellation, process,
report and cleanup behavior. It must validate the exact source, dependency
cohort and artifact bytes and execute without rebuilding or moving the build
into a new output context. Qualify the real native scenarios and negative
controls, release the capability, and select a compatible verified tool pin
before enabling the native hook. No shared runtime code is changed by this run.

The separate product build-graph experiment is retained in
`runtime-graph-prototype.patch`. Static restore preserved per-edge properties.
The original Parties Tenants gitlink refused EventStore 5.1.1; a local prototype
using the qualified Tenants source
`292dbf164f26bcf376ef86d749b149b075f8b502` advanced past restore. A normal Admin UI
project edge then propagated native and wrapper compressed assets together,
failing on duplicate `css/app.css.gz`; see
`runtime-asset-conflict-{build.log,verification.json}`. Runtime configuration
propagation, static-asset ownership and receipt creation still need product
qualification. The prototype and temporary gitlink update were removed from
the active tree; all native assertions and existing runtime preparation remain.

This dependency is additional to the separately approved frozen publisher-created
timestamp prerequisite. Neither prerequisite has been implemented or released
by this preparation run.
