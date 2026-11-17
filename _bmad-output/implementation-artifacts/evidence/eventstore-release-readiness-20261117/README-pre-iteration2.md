# EventStore query-contract readiness

The frozen query API and a synthetic consumer of the actual candidate packages
compile. Complete release acceptance is **false**. The original whole Contracts
run remains failed, and normal publication still requires ordered adoption and
the central nightly gates. No producer correction was demonstrated or made.

| Frozen input | Commit |
| --- | --- |
| EventStore | `3b2350e7c1fff640131f8101596c78a59e31a03f` |
| Builds, producer gitlink | `16cf0db6f843eb4defdc87105804d42eded634d6` |
| AI.Tools, producer gitlink | `cfd1ebea92587cdea41b9aa2cff47358bf2f32f6` |
| Tenants, producer gitlink | `0e0e85fd646da904c5528854e271b71a2b0b9066` |

The later remote observation at 2026-11-17T00:49:04Z still names that producer.
This evidence qualifies its frozen source and the stated local package probe;
it does not establish acceptance for a later main. Shared producer checkouts,
Projects preparation `3361f2e3b5655fa1ad50a2d12c640bbd5edcbb4b`, published package
pins, concurrent jobs and module policy remain untouched.

## Original results, preserved

| Attempt | Native result |
| --- | --- |
| [01: whole projects](attempt-01/result.json) | All three Release/package builds pass. Generators: 203/203 passed, exit 0. Contracts: 1,809 total, 1,807 executed, 1,805 passed, 2 failed, 2 skipped, exit 2. |
| [02: local package setup](attempt-02-local-packages/result.json) | Full consumer validation refuses the too-low local `0.0.0` label with NU1605; exact three-package reminder probe passes. |
| [03: fourteen packages](attempt-03-local-packages/result.json) | Real fourteen-package inventory and 13 library/1 tool consumers pass using an unpublished local label; reminder probes pass. |
| [04: authority](attempt-04-authority/result.json) | All 73 projects pass, exit 0, 364.903 seconds within the unchanged 480-second limit. |

The original Contracts failures are stale literal agent-instruction assertions
and the unchanged eight-minute authority timeout. Two package-dependent cases
skip without a supplied inventory; the projection probe returns early although
its row reports Passed. Their native logs, TRX rows, helper snapshots, exact
inputs and exits remain intact. Supplemental passes never turn this suite green.
The [owner migration patch](retire-agent-policy-assertions.patch) remains checked
and unapplied, preserving actual commitlint enforcement.

Historical dependency graphs are unavailable because the original scratch trees
were removed. The historical process-group receipts did not establish custody
of session-escaping descendants or cancellation cleanup. Their original claims
remain preserved; the current report does not repeat them as full-tree proof.
The nonce-based attempt 05, public inspection and revision-controls-01 through
04 receipts also do not establish custody after a descendant clears its
environment. Their package/API results remain valid; their custody claims are
limited to the cases that their retained helper versions actually exercised.
[Original report snapshots](readiness-pre-revision.json) and the
[original narrative](README-pre-revision.md) retain the previous aggregation.

## Re-derived verification

[verify.py](verify.py) retains the existing CLI and frozen inputs, with
[verification_core.py](verification_core.py) supplying the boundaries. Before
Git or build jobs it clears repository/index/object/config selectors and
`EVENTSTORE_PACKAGE_CONTRACT_DIR`, preserving credential-profile selection and
ordinary platform settings. Local package mode selects only its generated
inventory. Every subprocess uses owned-descendant custody, native-exit recording
and exception-safe cleanup; SIGINT, SIGTERM, timeouts and `setsid` descendants
are exercised without killing or reaping an unrelated process. Ordinary jobs
retain their unbounded budget; authority remains bounded at 480 seconds.
The corrected helper uses ancestry and newly adopted child identities, excluding
pre-existing foreign child trees by PID/start ticks. It reads no process
environments. Cancellation is deferred through child creation so cleanup always
has custody, including signals received during handler setup or `Popen` startup.

Frozen qualification requires the captured 203/1,809 test-name inventories and
both actual `TypedGatewayQueryGenerationTests` compilation cases. Final HEADs
must equal their recorded commits, with diffs against those commits. New attempts
save compact resolved libraries/content hashes and sanitized effective sources.

[Attempt 05](attempt-05-query-api-packages/result.json) packs only real Contracts,
Client and RestApi.Generators archives from the frozen producer. An attributed
synthetic `Owner.Contracts` assembly and a consumer using the packaged analyzer
compile in Release with auditing, analyzers and warnings-as-errors. The consumer
calls the generated typed query extension, whose retained
[binding](attempt-05-query-api-packages/TypedGatewayQueries.g.cs) uses the declared
result and existing wire query without creating REST routes. Archive SHA-256
hashes, actual package library/content hashes, sanitized sources for 11 restored
projects, native commands and final repository identities are retained. These
disposable candidates were never published or supplied to Projects.

[Pinned public inspection](public-api-recheck-02/result.json) uses
`dotnet-inspect` **0.28.0**, recording its package hash, reported version and every
exact command. Official Contracts 5.1.1 and 5.2.0 match the original archive hashes:
`QueryResultContractAttribute` is absent (native type-not-found exit 1), while the
known-present `SubmitQueryRequest` resolves from each package's metadata (exit 0).
All earlier API inspection logs remain unchanged.

[Executable audit](audit_evidence.py) replays retained inputs/logs/inventories,
tests incomplete or substituted results, sentinel selectors, real changed-HEAD
checkouts, policy guards and owned-process controls under Python optimization.
[Its retained broad receipt](revision-controls-04/result.json) passes **450 checks**.
No large producer suite or unrelated package consumers were rerun. Initial
verification-script mistakes remain visible in `revision-controls-01` and
`public-api-recheck-01`; later directories contain their corrected checks.

The subsequent [focused review-fix receipt](review-fix-controls-01/result.json)
passes 18 optimized controls for the corrected ancestry/adoption helper, including
fast double-fork/`setsid`/empty-environment exec, startup cancellation, original
native exits/bounds and foreign-tree survival. It also verifies the layout-only
split of synthetic `Result.cs` and `Query.cs`. No producer/package run was needed;
all previously executed helper snapshots remain unchanged. The 450-check receipt
above identifies the preceding helper version and is not retroactive proof for
the new lifecycle implementation.

## Reproduce the narrow revision

From the CiCd root, choose a fresh output directory for each invocation:

```sh
run-with-temp python3 -O -B _bmad-output/implementation-artifacts/evidence/eventstore-release-readiness-20261117/audit_evidence.py --output /absolute/path/outside-scratch/fresh-controls
run-with-temp python3 -B _bmad-output/implementation-artifacts/evidence/eventstore-release-readiness-20261117/verify.py --query-api-package-probe --output /absolute/path/outside-scratch/fresh-query-probe
run-with-temp python3 -B _bmad-output/implementation-artifacts/evidence/eventstore-release-readiness-20261117/inspect_public_api.py --output /absolute/path/outside-scratch/fresh-public-inspection
```

The audit replays the named retained successful revision attempts; it does not
rerun producer tests. The original baseline, `--local-package-probes` and
`--authority-probe` CLI modes remain available for an independently needed run.
All scratch work uses `run-with-temp`; useful results remain outside scratch.

## Remaining gates

The [machine-readable readiness](readiness.json) remains false for complete
release acceptance. Remaining gates include the original failed whole Contracts
run, exact-current-main green hosted CI/commitlint, full retained product,
security, compatibility, container and fourteen-package real-release acceptance,
released infrastructure and browser/live/private/Azure qualification, complete
EventStore adoption delivery and a clean standalone Builds checker. EventStore
has no setup selection, delivered adoption ref/configuration or approved
pre-adoption push substitute. Apply
[ordered adoption](../../../../docs/ordered-module-adoption.md) and
[pre-adoption publication](../../../../docs/pre-adoption-publication.md).

No commit, push, tag, dispatch, manual release, adoption, credential change,
live configuration write, owned module edit or parent-gitlink change was made
by this implementation. Normal publication remains the central nightly route;
Projects acceptance awaits actual published API availability.
