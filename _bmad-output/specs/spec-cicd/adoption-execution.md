# Additive adoption execution contract

This extends the initial Windows-only custom-job and fixed-budget design for
EventStore → FrontComposer → Tenants adoption. Complete and qualify shared work
before cutting over each repository. Adoption is separate from product releases;
publication remains disabled until a later separately authorized release.

The new fields are additive to `hexalith.ci.v1` and must be delivered only from an
acceptable immutable Builds release that declares them. Existing released pins
retain their original schema, defaults, reader and rendered caller bytes.

- CiCd centrally controls CI/release/nightly durations and independent custom-job
  budgets, hosted Linux/Windows/macOS execution, literal include matrices,
  concurrency bounds, dependency DAGs and failure-aware report aggregates.
- Builds owns the immutable mutation resource profile, preparation/runtime code,
  browser/tool/APT/TLS installation, test reports, coverage and package-consumer
  mechanics. Modules keep product hosts, fixtures, archive/API rules, authentication,
  mutation scoring, cleanup assertions and qualification/eligibility decisions in
  enabled actions. Exclusions delegate execution to enabled owners.
- Optional `qualification.yml` is whole owned perimeter content, rendered only
  when scheduled/manual product jobs are enabled. Its centrally authored schedule
  is independent of nightly release orchestration and has no publisher. Full
  mutation testing remains scheduled qualification rather than a per-release gate.
- Private jobs require main-only manual selection, a protected environment,
  explicit private Linux runner group and secret names/mappings, a bounded lifetime,
  explicit owner authority digest, and fresh green shared CI at the same source.
  Builds validates the request before checkout and preserves the owner-prepared
  fixture environment. Credentials reach only the selected product action.
- Explicit additional test projects outside the solution receive the same stage-2
  Release/package restore/build and evaluated discovery. Independent platform jobs
  prepare these outputs too. Complete project/target-framework execution and
  existing count/skip policies remain required.
- Native MTP/VSTest reports use fresh per-project/framework paths. Missing, empty,
  malformed or changed required evidence fails; an original product failure keeps
  precedence. Unit-only coverage gates apply in stage 3, including the local
  checker; cross-stage coverage gates apply after hosted integration.
- Coverage uses declared product scopes and comparisons. Preserve Tenants' line
  coverage strictly greater than 80%, 100% branch coverage on its exact named
  files, line union and existing best-per-line branch calculation. FrontComposer
  reporting introduces no threshold. Validate scopes against actual source paths.
- Dapr catalog initialization, Aspire preparation and exact historical tool/archive
  staging are distinct capabilities. An explicit historical runtime can use Builds'
  full initializer only with a verified CLI on a fresh hosted Linux worker, with
  the same job-bound backend receipt and no preexisting initialization. Private
  workers retain owner preparation. Verified installation grants no product runtime
  qualification, promotion or eligibility. Private archives and historical profiles
  must retain their selected identities.

See [the setup contract](../../../setup/README.md) for the actual supported fields
and action parameter protocol, and [ordered adoption](../../../docs/ordered-module-adoption.md)
for remaining product preparation and delivery blockers. Before each cutover,
verify applicable live runner and environment protections, resource bounds,
secret custody, elapsed workloads and fresh hosted success for the enabled
qualification routes. EventStore's MVP requires applicable on-premises
Kubernetes/kind qualification and offline Azure schema, payload, invariant and
security checks without Azure secrets. Azure runner, approval environment,
authority and secret custody provisioning and live qualification are post-MVP.
Use hosted evidence to establish live outcomes.
