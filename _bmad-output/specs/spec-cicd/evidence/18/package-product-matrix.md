# Package product preservation map

The original `SupportedProjectReadDistributedTests` and its guarded source
fixture/profile remain unchanged. The separate always-compiled
`PackageReadScenarios` executes their four product scenarios explicitly from
`PackageFixtureRun`; they are not extra live `[Fact]` tests in ordinary units.
The driver requires all four ordered completions and reports per-scenario
passed/failed/skipped counts. A failed setup is not a passed product row.

| Scenario | Preserved product assertions | Actual transport and observation |
| --- | --- | --- |
| main (9 rows) | authorized paging/continuation/open; public/workload trust negatives; foreign/absent identical safe denials with timing floor; real Projects restart with retained cursor and unchanged metadata/state; exact durable inspection/quarantine audit deltas/fields/TTL/privacy; real audit-write refusal and recovery; real Folder revocation/head advance/cursor invalidation; real Folder stop/start unavailability/recovery; authenticated commands/projections | Public authenticated gateway queries/commands/stream reads; actual gateway-hosted SDK callbacks; Aspire resource commands plus actual process IDs/start times/executable hashes; immutable owned Redis identity with binary/ETag/key-set observation and real ACL fault |
| duplicate | duplicate and fresh-message projection delivery across both tenants and both projects, exact unchanged bytes/ETags/heads/watermarks and retained successful/foreign-denied reads/cursors | Actual gateway workload issuer + catalog-fenced `project/v2` HTTP callback; public source reads and independent Redis binary snapshots |
| full-replay | incomplete/mismatched prefix refusal; real negative callback credentials; complete replay; only exact expected projection ETag changes while bytes/truth/watermarks agree; old cursor rejected before expiry; unchanged post-read state | Same actual owner/gateway SDK HTTP path for `project/rebuild/v1`, complete original stream prefixes, exact key/byte/version snapshots and public query continuation |
| tenant-access-recovery | genuinely stale unchanged projection and HTTP 404; anonymous/foreign refusal without mutation; eight same-ID retries append one event; fresh later ID appends one event; exact membership/status/version/watermarks; same OIDC user returns to HTTP 200 | Fresh real private Keycloak/TLS authority, non-admin reader tokens, public `RefreshTenantAccess` commands/status/stream reads and independent persisted projection observation |

The three native surface/negative matrices use a private user issuer with a
key separate from workload trust. Native human claims preserve agent/operator,
inspection permission, quarantine role and foreign coarse-admission distinctions.
The recovery and both browser phases use real Keycloak. Administrator setup and
source observations use separate bootstrap tokens; recovery keeps the same
non-admin reader token for positive, negative and final list controls.

`PackageHostingStartup` loads into the original prebuilt actual applications
under explicit private Development guards. It resolves their real public SDK
services, exposes only the finite private callback/source proof protocol, and
never activates the old Debug-only diagnostic registrations. Published 5.1.1
API signatures and the released Folder 2.0.0 types are recorded separately.
The actual Folder owner exposes its own existing policy factory after the local
producer repair described in `folder-owner-prerequisite.md`.

Owner metadata uses the concurrent `PackageOwnerLoadContext` implementation,
reconciled to share byte-identical SDK contracts while loading actual same-name
owner images independently. Three real owner collision controls and an altered
SDK refusal pass. No child metadata build is performed.

Both browser contexts remain mandatory: compatibility startup/auth smoke,
complete Chromium suite, repeated lifecycle, retry/cleanup probes and real SDK
host/store-client restart; then a fresh actual-owner browser journey with its
existing browser/state/privacy assertions. These browser checks do not replace
any native row above.

Runtime results are not yet acceptance: retained iteration 1 failed before
writer activation on changing startup inventory; iteration 2 passed the full
native-backup/reconciliation/activation sequence and failed later with a bounded
seeding/readiness cancellation. Main has not passed; duplicate, full-replay and
recovery have not executed. Iteration 3 adds safe method/seed checkpoints to
identify that exact readiness operation. All contexts are torn down before
another iteration. Private corrections and complete input hashes are saved
outside TMPDIR; live files have not been overwritten with unqualified deltas.
