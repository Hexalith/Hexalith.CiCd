---
title: 'Fix Projects package-fixture and G-6 publication checks'
type: 'bugfix'
created: '2026-11-16'
status: 'in-progress'
route: 'oneshot'
review_loop_iteration: 0
baseline_commit: 'ec481fd50b280e2d41f9baecbd03945c833e4538'
context: []
---

<frozen-after-approval reason="user requested fixing the two reported publication failures">

## Intent

Restore the retained Projects package-fixture and owning G-6 checks that blocked the authorized push. In `_bmad-output/specs/spec-cicd/evidence/18/qualify-owning-g6.py`, make scheduler host-port selection respect the Docker host's Windows exclusions when running from WSL, with bounded handling of publication collisions and exact cleanup of probe-owned containers. Preserve the advertised scheduler port, private loopback binding, original product assertions and error propagation; do not restart Docker, change shared settings or stop unrelated containers.

The package fixture attempted to discover a Folders EventStore executable outside the actual Folders Server output closure. Preserve the concurrent producer repair that compiles the existing eighteen policies into Server and the consumer's actual-owner selection. Improve zero/ambiguous artifact diagnostics in `PackageActualOwnerInfrastructure.Load` without selecting an arbitrary match, searching unrelated outputs, or substituting a fake owner. Add behavior regressions and verify actual Server composition plus its eighteen declarations and thirty-six golden variants. Treat the concurrently repaired Folder owner as an explicit prerequisite: qualify local snapshots honestly and do not claim remote availability, registration or pre-push acceptance for unpublished inputs. Preserve all concurrent changes and owned CI/CD portions. Use run-with-temp for disposable jobs, retain useful evidence and await every child before returning. Once the fixes are qualified, continue the earlier authorized publication only where all repository gates and credential boundaries permit.

</frozen-after-approval>

## Implementation Notes

- User explicitly requested fixing the known failures in the existing dirty shared workspace; this continues the prior authorized work and preserves other changes. No fresh permission is needed to work in those files.
- Investigation: Windows netsh lists 51801–51900 as excluded, including failed port 51825; WSL's local socket cannot detect that host restriction. Automatic placement publishing succeeded, so a global Docker outage is disproved.
- Package diagnosis: Projects base 146d0f7e9964c82da23d31b51e6ab62efdcfdda6 searched Folders Server's output for Hexalith.Folders.EventStore.dll. Pinned Folders aee8d791803e7a439d1ffdc9b2174ac6487394a6 has no such executable dependency. The prior per-file snapshot was removed, so this is strongly supported rather than stack-trace-confirmed. Current concurrent Folder repair and product results are documented in ../specs/spec-cicd/evidence/18/folder-owner-prerequisite.md.
- Small local implementation scope; no unresolved choice affects the code fix. External publication retains its separately applicable pre-push constraints. This is not approval of a new module exception or adoption.

- Implemented host exclusion discovery with a WSL fallback when Windows interop is absent from PATH. The real Docker probe reproduced the original HTTP 500 on 51825, then proved an eligible scheduler reachable; both owned probes were removed and their absence verified.
- Frozen local qualification compiled with zero warnings/errors and passed forty initial artifact/safety/credential cases. The owning G-6 run passed all thirty-three retained support cases and its one actual PostgreSQL production matrix, with three exact owned-container removals verified.
- The real package path exposed an existing startup inventory turnover. Added a two-second complete, byte/ETag-stable quiescence observation inside the original thirty-second pre-backup budget. Only its exact turnover exception is retried; malformed/source failures, backup, post-backup comparison and activation remain fail-closed and unretried. Five initial behavior cases brought the focused lane to forty-five passing cases. The actual run retained native backup validation, reconciliation, authenticated activation and actual SDK readiness receipts.
- Further live setup reached Folder creation but timed out awaiting named projection delivery. The preserved stack identifies WaitForSeedNamedDeliveryAsync. Investigation found the operational-status projection requires the SDK's existing native-source scanner, while the private fixture supplies only stream-read enrollment/proof. This is missing actual-owner fixture setup, not permission to weaken the completion observer or fabricate delivery state.

## Review Triage Log

- medium, patched: native Docker can report host publication collisions with alternate messages; accept the finite allocation/bind variants only for exit 125, with bounded retries and representative tests. Image/authentication/runtime failures still propagate.
- medium, patched: a timed-out create may leave no valid CID receipt. Reconcile that uncertainty through the exact unique container name and namespace label, validate full IDs and keep exact custody checks before removal. Missing/empty/invalid CID and read refusal controls cover this path.
- medium, patched: successful removal followed by failed verification could abort later cleanup. Track successful remove commands independently, retry only absence verification, attempt every owned identity and persist partial failure receipts while retaining failure status.
- low, patched: missing/ambiguous artifact errors lacked the selected output directory and bounded candidate paths. Include those details and distinct build/duplicate guidance; refusal semantics are unchanged.
- medium, patched: stability tests did not interrupt an already accumulating window. Added settled/interrupted/settled cases for both nonquiescence and inventory turnover, requiring a complete new two-second interval.
- low, rejected: direct artifact-lookup unit tests do not execute the entire actual-owner catalog composition. Their purpose is the exact missing/ambiguous lookup behavior; the separate real fixture already loaded actual owners, authenticated bootstrap and cutover, and processed the Folder create before the later named-delivery setup failure. A second fake assembly/composition harness would add substantial machinery without replacing that required real-runtime evidence.

- Follow-up review: medium, patched — retain uncertain create names through final cleanup, reconcile a late matching owned container and fail explicitly when custody remains unresolved. The final Python lane has twenty-three passes.
- Follow-up review: low, patched — validate all four Folder read/scan RSA pairs, exact pair matching and independent key identities, plus distinct server/worker issuer secrets, before launch. Generated, missing, malformed, mismatched and reused inputs are exercised by the actual fixture preparation test.
- Follow-up review: low, rejected — a second offline authority graph test would cover hypothetical future wiring changes. Reviewed grants remain restricted to each actual workload, the two exact fixture tenants and folders domain; real native runtime now proves source scan and named completion. Generic SDK authority refusal semantics were not changed. A separate fake authority/graph harness adds substantial scope beyond the concrete repair.
- Follow-up review: low, rejected — separate synthetic receiver tests could protect future metadata-only flag movement. The actual SDK branch was checked: the flag applies only to ordinary worker read requests, with server full reads and independent native scans preserved. No current receiver scope defect was found; full actual-owner execution remains required.
- Added bounded safe owning method identities to fixture failures, excluding exception data and source paths; its behavior test passes. Restored the actual eventstore sidecar gRPC endpoint needed by the copied browser advisory readiness path.
- Latest focused Release verification: fifty-seven cases pass with zero warnings/errors/failures/skips. Final owning G-6 rerun also passes thirty-three support cases plus its PostgreSQL matrix; retained provider and control-plane cleanup receipts confirm awaited processes and owned removal.
- Live native proof now reaches real Folder operational-status completion, Project projection completion and three main read/security cases. Two full attempts fail at the unchanged actual Projects restart assertion because DCP cannot stop the warmed process; a bootstrap-only restart succeeds with a new actual process. Exact Aspire13.6.5 factory source and actual Projects process configuration identify missing telemetry setup: the factory disables its dashboard/collector but supplies localhost4317 to all three active OTLP exporters, with no listener. OTel1.21 shutdown may consume three sequential five-second flush budgets. A supported private collector configuration is being prepared; no timeout or product assertion is relaxed.
