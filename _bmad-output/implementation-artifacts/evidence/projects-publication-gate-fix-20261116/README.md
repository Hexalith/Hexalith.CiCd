# Projects publication-check repairs

The local fixes are prepared and reviewed. Publication remains blocked by the
current Projects main branch's dependency on an SDK API that is not yet in a
released package. No module preparation push or superproject commit was made
in this repair turn.

## Changes

- Owning G-6 scheduler allocation reads Windows host exclusions from WSL, retries
  only bounded host-publication collisions and verifies exact container custody.
  Cleanup attempts every owned identity, preserves uncertain creates and fails
  explicitly when removal or custody cannot be verified.
- Actual-owner artifact selection retains zero/duplicate refusal and reports the
  selected output and bounded candidates. The concurrent actual Folders Server
  adapter repair remains intact.
- The package fleet enrolls independent Folder Server and Worker stream-read and
  native-scan proofs, with separate keys and issuer secrets. Grants are limited
  to the two exact fixture tenants and the Folders domain. Workers' ordinary
  reads remain metadata-only; Server full owner reads are preserved.
- Fresh cutover waits for two seconds of complete stable byte/ETag observations
  inside the original pre-backup deadline. Only the exact initial inventory
  turnover is retried. Backup, source, activation and post-backup assertions are
  unchanged. The browser advisory path gets its actual sidecar gRPC endpoint.
- Package telemetry now uses an authenticated owned Aspire receiver on dynamic
  loopback endpoints. The factory follows the pinned
  [Aspire testing setup](https://github.com/dotnet/aspire/blob/b33d222049f1ecc3bc7257ec07b622fe550b2580/src/Aspire.Hosting.Testing/DistributedApplicationTestingBuilder.cs).
  Dashboard data and per-resource Data Protection profiles stay below fixture
  scratch. Four API/browser roles have independent keys. Actual HTTP and gRPC
  exports must reject missing keys and accept the private key; the actual
  workload's endpoint, protocol and one-way key fingerprint must match.
- Safe failure diagnostics report bounded owning method identities without
  exception data, source paths or credentials.

## Verification and scope

| Check | Result | Scope |
| --- | --- | --- |
| Host allocation/custody/cleanup regressions | 23 passed | Final Python helper source |
| Owning support methods | 33 passed; no skips | Current pinned SDK source `0be0c922883d4ea61b18e843e24472162261d934` |
| Actual PostgreSQL production matrix | 1 passed; no skips | Same current SDK; provider processes stopped and scratch removed |
| G-6 control-plane cleanup | All three exact containers removed | Current SDK run; no unrelated resources touched |
| Fixture safety, credentials, lookup and load contexts | 57 passed; zero warnings/errors/skips | Earlier Projects `146d0f7` candidate, before the collector change; this does not qualify current main |
| Real native scenario progress | Folder named completion and three read/security cases passed | Earlier baseline; warmed Projects restart subsequently failed twice |
| Cold owned restart diagnostic | Passed; changed actual PID, unchanged application/runtime bytes | Earlier baseline; not full product acceptance |
| Exact-source collector runtime probe | Build and runtime passed | Actual Aspire 13.6.5 and OpenTelemetry 1.21, extracted unchanged verifier and real Web workload; not full Projects acceptance |

The collector probe requires authenticated HTTP/gRPC ingestion and proves its
actual workload's exporter wiring. It warms logs, metrics and traces, then
requires a distinct actual process with unchanged application bytes after the
normal Aspire restart. Its source-bound receipt records the measured duration.
Runtime-only DCP log-stream deletion warnings are retained in the probe log.

Useful results are in [result.json](result.json),
[current G-6 reports](current-main/g6/),
[collector probe input hashes](current-main/collector-probe-inputs.json),
[collector receiver proof](current-main/collector-probe-receiver.json), and
[collector runtime output](current-main/collector-probe-runtime.log).

## Current main blocker

Projects was safely fast-forwarded to freshly fetched
`85ff9795`; Folders to `f2bf547b`. Pending file contents and modes were preserved,
as recorded by the two `*-fresh-main-preservation.json` receipts. Remote changes
and pending paths had no overlap.

The normal Release/package Integration build fails with fourteen `CS0234`
errors: seven query DTOs require
`Hexalith.EventStore.Contracts.Queries.QueryResultContractAttribute`, while the
module pins SDK `5.1.1`. The latest published `5.2.0` was also inspected: it
contains no such type and records producer commit
`8b6d5bee5217b3f4bbd8fd689ad887aca863961b`. The type was introduced by the newer
producer commit `0be0c922883d4ea61b18e843e24472162261d934`.

See the [exact failed build](current-main/integration-build.log),
[published version metadata](current-main/published-eventstore-contracts.json),
and [released API inspection](current-main/query-result-5.2-inspection.log).
A package-version increase to 5.2.0 alone cannot fix this. The normal SDK release
must supply the new API, then the consuming package family and actual-owner
closures need alignment and complete current-input qualification. No shim,
attribute removal, source-mode fallback, audit bypass or manual release was used.

Folders' independently approved preparation procedure still requires all its
retained product/component/provider controls. Its frozen FR58 execution hold
and incomplete prerequisites were not changed. The unpublished owner adapter
cannot be claimed as an available delivered dependency.

## Review

All concrete host-port, cleanup, diagnostic, key-validation, collector storage,
Data Protection, credential-separation, startup-order and effective-exporter
findings were corrected. Broader fake authority/composition harness proposals
were classified low and rejected with evidence in the source spec. Independent
follow-up source review found no remaining concrete collector findings.
The source spec remains in progress because the required full current-main
package qualification and authorized publication have not succeeded.
