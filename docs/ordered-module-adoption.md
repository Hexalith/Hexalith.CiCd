# EventStore, FrontComposer and Tenants adoption

Adopt **EventStore → FrontComposer → Tenants**. Complete shared runtime work and
qualification before each module's cutover. Adoption has separate changes and
green CI evidence; it never creates a product version or publishes product
packages/images. Keep `HEXALITH_RELEASE_PUBLISH_ENABLED` disabled during cutover.

The supported configuration is documented in [the setup contract](../setup/README.md)
and Builds' `docs/module-adoption-execution.md`. The latter covers native reports,
exact scoped coverage, shared consumer mechanics, prerequisite preparation and
side-by-side historical qualification tools. Schema, strict reader, resources and
runtime must all come from the same acceptable immutable Builds release.

## Infrastructure delivery prerequisite

The new execution contract is an infrastructure change to Builds and CiCd. It
requires its own reviewed Builds release and infrastructure qualification before
changing `builds-version`. Then render and run global validation against that
exact tag, and deliver the complete owned perimeter. A synthetic candidate tag
used in an isolated test repository is test evidence only; it is never an
acceptable publication or a substitute for released bytes.

This implementation changes no module registration, Builds pin, publication
switch, release metadata or live GitHub setting. The existing selected tag keeps
its existing contract and generated callers. Ordinary push/PR CI and separate
qualification workflows perform no release operation. The existing release
workflow retains its publication switch, security checks, audits and original
artifact authentication.

## Required product preparation

| Module | Preparation and qualification still required |
| --- | --- |
| EventStore | Extract retained product actions, include payload projects explicitly, classify live/Azure tests correctly, resolve browser failures, retain published compatibility and exact broker/runtime profiles, preserve the Platform deferral, and qualify opt-in kind and private Azure execution. |
| FrontComposer | Establish the package-only evaluated Release graph, split product checks from CI/story/evidence governance, retain CLI/ApiCompat/pacts/accessibility/browser checks, and qualify all three engines plus independent mutation segments and complete aggregate reports. |
| Tenants | Enforce the intended standalone package graph, retain catalog consumers and authentication/persistence/removal behavior, keep `rest`, `persisted`, `anonymous-ui` and `authenticated-ui` in isolated workers, and preserve the exact existing line/branch coverage scopes and comparisons. |

Enabled actions and their inputs must exist on live `main` before registry
validation. An exclusion delegates execution to one enabled hook/job, including
its complete action inventory; it grants no permission to omit product behavior.
Debug/source-mode checks remain developer/upstream responsibilities. Shared
mechanics belong in Builds, so module actions contain product startup/assertions,
fixtures, archive/API rules, mutation scoring and truthful qualification results.

The optional qualification caller is separate from `release.yml`, with centrally
authored scheduling and manual dispatch. Long mutation/property work does not
become a per-release gate. Protected manual jobs run from `main` only; the selected
job's dependency closure runs and receives explicit noncredential parameters.
Private runner secrets reach only that action step. A declaration of a protected
environment/runner group is not proof of its live protections or ephemerality.
Private execution additionally requires an explicit owner authority digest and
fresh green CI for the same source; shared preparation preserves its existing
fixture runtimes instead of installing or initializing replacements.

## Adoption blockers and evidence boundaries

1. Publish and qualify the Builds infrastructure release separately; verify its
   acceptable immutable release metadata before selecting it in CiCd.
2. Verify live permissions, runner groups, environments, explicit secret custody,
   private execution/network boundaries and publication-disabled settings.
3. Measure retained workloads and select budgets; fresh hosted execution must
   qualify browsers/APT/TLS, Dapr/Aspire/backend ownership, matrix isolation,
   mutation resources, report completeness, and live/private product scenarios.
4. Finish the product extraction, Release graph and action preparation in order,
   then validate/deliver one complete perimeter and record exact green adoption
   CI identities. Preserve foreign instruction/settings content.
5. Run the mandatory clean committed standalone local checker before pushes;
   its stages 1–3 evidence does not certify integration, setup, hooks or custom
   qualification. Local candidate smoke tests are not hosted adoption evidence.
6. If a required published upstream package is unavailable, handle that upstream
   product release separately under its own authorization, then resume adoption.
   Adopting FrontComposer never authorizes publishing a FrontComposer version.

Validation commands, source boundaries and blockers are recorded in the
[shared adoption evidence report](shared-adoption-validation.md). Unrelated work
already present in these checkouts is outside this change and must remain intact.
