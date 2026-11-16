# Story 26 shared support design

The 2026-11-16 `fix` instruction authorizes implementing the already approved
separate prerequisite. This source work remains separate from Platform migration,
registration, adoption and CAP-16. CiCd baseline is
`9c2a65cbf1d523609000fffb525fba5cf5e8b4b3`; Builds baseline is
`05bda4e01d70afacb5048d5c336f383a301c0974`. Both identifiers were read from Git.
Preserve concurrent Projects work. The selected published Builds contract remains
v6.0.6; newer checkout source does not establish a qualified release.

## Reuse and missing behavior

`Github/lib/module_preparation.py` already owns one authenticated producer
lifetime across shared CI, local checking and release builds. Its managed mode
requires a separate direct Platform checkout and exports seven source-mapping
values. Platform itself cannot enable that mode: it instead needs the historical
signed Builds Module.Cli archive bound by `eng/builds-tuple.json` and the existing
`HexalithBuildsPublishedToolRoot` input before evaluation.

`Props/Directory.Packages.props` already selects SDK4.2.0, Tenants7.0.7,
Memories3.0.27, Parties3.1.1 and McpCli2.0.1 for the exact named Platform
Composition/CatalogBuilder identities. Preserve these finite catalog views.
Composition needs no new default/version overrides. Its existing product
assertions can consume the ordinary built DLLs. Active catalog authentication
must be independent of the historical producer catalog; Platform's old
`builds_tuple.verify_catalog` cannot establish both identities at once.

CatalogBuilder has real additional compatibility builds for SDK 3.130.0,
3.130.1, 3.130.2, 3.132.1, 4.1.0 and 4.2.0. Shared `restore_and_build` currently
builds only the root solution. Its hooks cannot generate/build these consumers.
The new shared input is a bounded list of real repository project paths and
finite catalog version selections. Platform preparation will materialize the
needed product fixtures and change verifier build sections into read-only
consumers in story 26, after the prerequisite release. This source change does
not edit those module scripts or claim their product qualification passed.

`release_build` already discovers evaluated packability, builds once, and packs
original artifacts with no build/restore. `release_draft.artifact_inventory`
authenticates those bytes. Preserve this interface and artifact handoff.
`release_publish.verify_packages` already checks public ID/version/source, but
not the signature or equality of the complete nonsignature body. Platform's
`verify-published.py` requires both. Its ordinary package assertions can later
run as a read-only `AfterTargets="Pack"` product target in the unprivileged
build; no new hook or privileged module callback is needed.

## Additive contract

- Nullable optional `publishedBuilds` is a safe regular repository-relative JSON
  path, default null, mutually exclusive with `moduleManifest`, and unavailable
  with `solution: none`. It selects the existing `eng/builds-tuple.json` closed
  handoff shape. Neither arbitrary URLs, executable names, exports nor module
  callbacks are inputs. Its exact tool-manifest version must agree with the
  historical tuple. Reject any unverified/candidate authority.
- Shared preparation authenticates the current clean accepted delivered config,
  active exact Builds tag/checkout, module revision and binding bytes separately
  from the official historical producer tag/source/catalog blob/SHA. Port or reuse
  the strict tuple and `builds_publication.verify_handoff` controls without their
  false active-equals-historical assumption. Check official release body markers,
  successful original release run, bound manifest, archive SHA, NuGet signature,
  safe bounded extraction, Tooling SHA, required EventStoreHost file and the
  executable's full version plus source. Download only fixed official endpoints,
  bound transport/process time and size, and keep credentials off downloads and
  executable invocations. Do not initialize nested repositories. Export only
  `HexalithBuildsPublishedToolRoot` and Release for this mode. Revalidate source,
  inputs, checkout identity and producer bytes on every reuse, restoring ambient
  environment and cleaning private scratch on failure and completion.
- Optional `buildProjects`, default [], has at most 32 entries with unique
  kebab-case `id`, safe `.csproj` `project`, and `versions` mapping only the
  existing finite EventStore/Tenants/Memories catalog version
  properties to exact stable versions. Require preparation when enabled. These
  are committed non-test compatibility consumers and never enter release package
  discovery or publishing; actual test projects remain classified
  from the root solution. Refuse policy/import/source/audit overrides, unknown
  properties, unsafe/symlink/foreign paths, duplicate selections and test-project
  entries. Shared code evaluates/restores/builds them in declaration order after
  the root build, with private per-case SDK artifacts paths and the same CI
  package-mode flags. Release uses its existing audited/versioned flags without
  weakening or replacing its targets. Stop at the first failure. Export a
  validated output-location mapping for read-only product actions, keep it alive
  through their job and clean it at the owning preparation lifetime. Existing
  callers without these options keep the same behavior. No build is added to
  a hook. Linux/local/release support is required; reject unsupported custom
  platform combinations explicitly rather than silently omitting work.
- Opt-in evaluated `HexalithVerifyPublishedPackage=true` enrolls a real packable
  project in strict public archive verification. Validate consistent booleans
  across TFMs. Carry the flag in that package's authenticated manifest entry;
  omit it when false so old artifact bytes/results remain unchanged. Preserve
  the original member-body inventory in authenticated private publisher state.
  The public package may differ in ZIP encoding and root `.signature.p7s` only.
  Require signature presence plus bounded `dotnet nuget verify --all`, comparing
  every other member's SHA-256. Reject unsafe/duplicate entries and added,
  removed or changed bodies immediately. Signature verification runs with the
  publisher's existing credential-free private process environment. Never run
  module code, rebuild, repack or grant push credentials to verification.

Before editing runtime code, record the additive inputs, finite shared project
orchestration and strict archive verification in the architecture spine. Document
only implemented schema/reader/consumer behavior in setup/README.md and Builds
docs. Renderer/validator fixtures must use matching schema and readers; production
`builds-version` and registrations stay unchanged until an acceptable release.

## Qualification and release boundary

Use `run-with-temp` for every disposable job. Exercise genuine archive parsing,
source/digest/signature refusals, preparation-before-evaluation, state reuse,
independent catalogs, six isolated declared SDK selections, build failure/audit
preservation, strict public-package round-trip, credential isolation and legacy
unchanged behavior. Test actual SDK artifact isolation with small nonshipping
projects where feasible, not only command mocks. Run narrow shared regression
suites and renderer/validator checks. Record executed cases, failures and exact
source identities; fixture success is not Platform adoption.

Publishing remains the existing authorized central release process. An acceptable
exact bot-authored published immutable tag/source and genuine Platform producer,
compatibility and package qualification remain required before story 26 consumes
the support. Do not manufacture a release or change pins to untagged source.


## Implemented source candidate (2026-11-16)

The additive schema/reader, historical handoff preparation, finite shared project
orchestration and authenticated strict package policy are implemented in Builds.
The existing preparation entry points supply the producer before CI/local/release
evaluation and revalidate it for job reuse and every declared compatibility case.
Per-case SDK artifacts live beside immutable producer files, so their writes do
not mutate the authenticated producer inventory. Product actions consume
`HexalithBuildProjects` as the JSON `{id: {project, versions, artifactsPath}}`
mapping through the existing job lifetime. Evaluated empty/false package policy
omits the new manifest key, preserving the legacy artifact entry shape.

CiCd renderer/validator fixtures export matching candidate schema/reader bytes
through synthetic local Git tags; production tags and registrations are unchanged.
The real six-case SDK probe qualifies selected properties and output isolation
with small nonshipping projects. It does not restore or qualify Platform's actual
six package cohorts. Historical archive/signature success uses explicitly labeled
process controls; a real `dotnet nuget verify --all` rejects the invalid signature
probe. Genuine signed Platform producer and public-package qualification remain
release/adoption dependencies.

During implementation another session committed pending source and advanced CiCd
and Builds HEADs. Those commits were preserved. The final source hashes, original
baseline-to-current patches, executed command results and matrix coverage are in
`prerequisite-verification.json` and `prerequisite-verification.md` beside this
file. They identify the tested source candidate independently of current HEAD.
No remote repository operation, release, source pin change or Platform edit was
performed by this implementation.
