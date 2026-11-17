# EventStore query-contract readiness

The frozen query API and the synthetic consumer of real candidate Contracts,
Client and RestApi.Generators packages compile. **Complete release acceptance
remains false.** The original whole Contracts suite remains failed; normal
publication still requires ordered adoption and the central nightly gates.
No producer correction was demonstrated or made.

| Frozen input | Commit |
| --- | --- |
| EventStore | `3b2350e7c1fff640131f8101596c78a59e31a03f` |
| Builds, producer gitlink | `16cf0db6f843eb4defdc87105804d42eded634d6` |
| AI.Tools, producer gitlink | `cfd1ebea92587cdea41b9aa2cff47358bf2f32f6` |
| Tenants, producer gitlink | `0e0e85fd646da904c5528854e271b71a2b0b9066` |

This qualifies the frozen source and the stated local package boundary. A later
remote-head observation is recorded in [readiness.json](readiness.json); it does
not extend acceptance to another source. Shared producer checkouts, Projects
preparation `3361f2e3b5655fa1ad50a2d12c640bbd5edcbb4b`, published pins, concurrent
jobs and module policy remain untouched.

## Original results remain preserved

| Attempt | Native result |
| --- | --- |
| [01: whole projects](attempt-01/result.json) | All three Release/package builds pass. Generators: 203/203 passed, exit 0. Contracts: 1,809 total, 1,807 executed, 1,805 passed, two failed, two skipped, exit 2. |
| [02: local package setup](attempt-02-local-packages/result.json) | Full consumer validation refuses the too-low local `0.0.0` label with NU1605; the three-package reminder probe passes. |
| [03: fourteen packages](attempt-03-local-packages/result.json) | Fourteen real archives, 13 library consumers, one tool consumer and reminder probes pass under an unpublished local label. |
| [04: authority](attempt-04-authority/result.json) | 73 projects pass, exit 0, 364.903 seconds within the unchanged 480-second bound. |

The original Contracts failures are a stale agent-instruction assertion and the
unchanged eight-minute authority timeout. Two package-dependent cases skip
without an inventory; the projection probe returns early although its row reports
Passed. Native logs, TRX rows, snapshots, identities and exits remain intact.
The [owner migration patch](retire-agent-policy-assertions.patch) remains checked
and unapplied, preserving actual commitlint enforcement. Supplemental passes
never turn the original suite green.

Original disposable dependency graphs are unavailable; no reconstruction is
claimed. [Attempt 05](attempt-05-query-api-packages/result.json) retains its valid
query-package compilation, but its eleven-file graph capture contains six
committed Windows history assets and five active Linux assets. The
[superseding provenance record](graph-provenance-correction.json) corrects that
claim without changing the old capture. Prior query project and nuspec hashes
were not recorded before execution; that historical provenance is unavailable.

Original process-group receipts lack session-escape/cancellation proof. The
later nonce helpers do not prove custody after environment clearing. The shared
supervisor's ancestry/adoption helpers also cannot distinguish a foreign tree
that double-forks after observation. The earlier 18 passing controls did not
exercise that race. Every historical receipt and valid package/API result is
preserved, with these limits; no retroactive full-tree claim is made.
[Pre-iteration-2 report](readiness-pre-iteration2.json),
[earlier report](readiness-pre-revision.json),
[earlier narrative](README-pre-iteration2.md), and
[pre-review-2 helper scaffolds](pre-review-2/manifest.json) retain the prior state.

## Iteration 2 verification

[verification_core.py](verification_core.py) creates a dedicated child custodian
for each Git, build, test or inspection command. Only that custodian becomes a
subreaper, observes descendants and reaps adopted orphans. The calling helper
never adopts or classifies unrelated trees. Private IPC carries cancellation and
receipts without saving environment values. Native exits, existing time budgets,
SIGINT/SIGTERM cleanup and custodian reaping remain explicit; incomplete custody
is a failure. Authority retains its original 480-second limit.

Before any job, the helper quarantines repository/index/object/config selectors,
`GIT_CONFIG_GLOBAL`, `GIT_CONFIG_SYSTEM`, `GIT_TEMPLATE_DIR`, package-contract and
ambient build-policy selectors. It preserves intended credential-profile
selection and ordinary platform settings. Initial and final source validation
reject unexpected ignored/untracked inputs outside designated generated outputs.
Final HEADs and diffs bind to recorded commits. Required suite qualification
continues to bind the frozen 203/1,809 inventories and both typed-query compilation
cases. Primary failures and command/cleanup receipts are saved before best-effort
graph capture; secondary capture errors cannot replace them.

[The fresh narrow query run](iteration2-query-api-02/result.json) packs the three
real archives and compiles an attributed owner assembly plus a consumer using
the packaged analyzer. All five actual producer/synthetic projects have evaluated
Release, package, audit and analyzer settings. Producer warning exceptions remain
exactly the frozen Builds `NU1901`/`NU1902` policy; the synthetic projects have no
security-warning exceptions. Additional suppression is rejected.

Only the five explicitly evaluated active `ProjectAssetsFile` paths enter the
[new graph capture](iteration2-query-api-02/resolved-package-graphs.json).
Actual package libraries/content hashes and sanitized effective sources are
retained. Input/project/config/nuspec/archive manifests are bound before consumer
execution and replayed alongside the generated binding. Exact final frozen
identities, clean tracked diffs and absence of unexpected source inputs pass.
These candidates were neither published nor supplied to Projects.

[Fresh public API inspection](iteration2-public-api-02/result.json) downloads and
pins `dotnet-inspect` 0.28.0 plus its Linux runtime archive, installs those exact
captured archives through a local-only feed, and hashes every installed payload
file against the runtime archive. The actual executed native entry point matches
that payload. Official Contracts 5.1.1 and 5.2.0 retain their original archive
hashes: `QueryResultContractAttribute` returns native type-not-found exit 1, and
known-present `SubmitQueryRequest` resolves with exit 0. Commands are registered
before execution, including interrupted-command cleanup receipts.

[Focused optimized controls](iteration2-controls-05/result.json) pass **41
checks**, including three exact foreign-orphan races, escaped/double-forked
empty-environment descendants, early/fork/active cancellation, native exits,
unchanged bounds, input/selector/policy rejection, active-graph selection,
interrupted inspection receipts and primary-error preservation when graph capture
also fails. The foreign orphans survive each job and remain waitable by their
fixture owner. No process environment is inspected.

[Executable audit](audit_evidence.py) replays historical and new receipts, logs,
committed inputs, package/project/nuspec manifests, active graphs, installed tool
payload and aggregation. It rejects changed suite inventories, missing required
cases, mutated inputs and substituted readiness identities/counters/acceptance
fields. The final audit passes **706 checks**: [iteration2-audit-04](iteration2-audit-04/result.json).
No whole producer suite or unrelated consumer was rerun. Failed helper controls
and first narrow attempts remain in their original directories, including the
initial output-path normalization, tool RID-feed and LF/CRLF policy-check mistakes.

## Reproduce

From the CiCd root, use a fresh output directory for each invocation:

```sh
run-with-temp python3 -O -B _bmad-output/implementation-artifacts/evidence/eventstore-release-readiness-20261117/iteration2_controls.py --output /absolute/path/outside-scratch/fresh-controls
run-with-temp python3 -O -B _bmad-output/implementation-artifacts/evidence/eventstore-release-readiness-20261117/audit_evidence.py --output /absolute/path/outside-scratch/fresh-audit
run-with-temp python3 -B _bmad-output/implementation-artifacts/evidence/eventstore-release-readiness-20261117/verify.py --query-api-package-probe --output /absolute/path/outside-scratch/fresh-query-probe
run-with-temp python3 -B _bmad-output/implementation-artifacts/evidence/eventstore-release-readiness-20261117/inspect_public_api.py --output /absolute/path/outside-scratch/fresh-public-inspection
```

The audit replays the named retained receipts and invokes only read-only frozen
policy inspection. It does not run producer tests. The original baseline,
`--local-package-probes` and `--authority-probe` CLI modes remain available; none
was rerun during this revision. All disposable work uses `run-with-temp`, and
useful results survive outside its cleaned scratch directory.

## Remaining gates

Complete release acceptance remains false. Remaining gates include the original
failed whole Contracts run, exact-current-main green hosted CI/commitlint, full
retained product/security/compatibility/container/fourteen-package release
acceptance, released infrastructure and browser/live/private/Azure qualification,
complete EventStore adoption delivery and the clean standalone Builds checker.
EventStore has no setup selection, delivered adoption ref/configuration or
approved pre-adoption push substitute. Follow
[ordered adoption](../../../../docs/ordered-module-adoption.md) and
[pre-adoption publication](../../../../docs/pre-adoption-publication.md).

No commit, push, tag, dispatch, manual release, adoption, credential change, live
configuration write, owned module edit or parent-gitlink change was made by this
implementation. Publication remains the central nightly route; Projects
acceptance awaits actual published API availability.
