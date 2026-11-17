# EventStore query-contract release readiness

The frozen producer's query-contract API compiles and its functional generator
tests pass. Complete release acceptance remains blocked: the unchanged whole
Contracts suite failed, and this packet does not certify hosted CI, adoption or
publication. No product defect in the verified query-contract behavior was
demonstrated, so no product correction was manufactured.

## Exact inputs and custody

| Input | Commit |
| --- | --- |
| EventStore | `3b2350e7c1fff640131f8101596c78a59e31a03f` |
| Builds, producer gitlink | `16cf0db6f843eb4defdc87105804d42eded634d6` |
| AI.Tools, producer gitlink, read by Contracts governance tests | `cfd1ebea92587cdea41b9aa2cff47358bf2f32f6` |
| Tenants, producer gitlink, read by Contracts package ownership tests | `0e0e85fd646da904c5528854e271b71a2b0b9066` |

[verify.py](verify.py) creates separate standalone copies from the root-declared
object stores beneath the wrapper's private `TMPDIR`. It initializes no nested
submodules. Every attempt retains its exact helper snapshot/hash, source trees,
committed-input blob/hash manifest, commands, native exits and useful logs.
Tracked source comparisons passed for every disposable repository. The shared
EventStore checkout stayed clean at `54f83e3b6a6eca3c8cf0caeb734cbcad30e18e41`.
The later observed remote `main` at `2026-11-17T00:20:30Z` still equalled the
frozen producer; no later source was substituted. All four wrappers completed
and their disposable trees were removed. [Readiness](readiness.json) and
[integrity](integrity.json) provide the aggregate machine-readable results.

## Baseline results

[Attempt 01](attempt-01/result.json) ran ordinary package-mode Release restore
and builds with `-warnaserror`, then both entire projects using
Microsoft.Testing.Platform with no test filters or assertion changes.

| Check | Result | Native exit |
| --- | --- | --- |
| RestApi.Generators.Tests restore/build | Passed; build had 0 warnings/errors | 0 / 0 |
| Contracts.Tests restore/build | Passed; build had 0 warnings/errors | 0 / 0 |
| Gateway restore/build | Passed; build had 0 warnings/errors | 0 / 0 |
| Entire RestApi.Generators.Tests | 203 total/executed/passed; no failure/skip | 0 |
| Entire Contracts.Tests | 1,809 total; 1,807 executed; 1,805 passed; 2 failed; 2 skipped | 2 |

Both `TypedGatewayQueryGenerationTests` passed, compiling generated bindings for
source and referenced contracts while preserving the existing REST route
behavior. The source includes public `QueryResultContractAttribute` with its
typed result, domain and existing wire discriminator.

The Contracts failures remain visible in the [native log](attempt-01/contracts-test.log)
and [TRX](attempt-01/test-results/contracts/contracts.trx):

- `CopilotInstructionsDelegateCommitlintContractToSharedInstructions` requires
  stale literal agent-instruction wording. This tooling/governance gate is not
  a query-contract product defect; no instruction, workflow or assertion was edited.
- `SharedConsumerAuthorityValidatorPassesForEveryTrackedMsBuildSurfaceAsync`
  reached its unchanged eight-minute timeout. A direct reproduction passed
  below; the original whole-suite timeout and failed exit remain unchanged.
- `PackagedReminderApiRunsWithoutWorksTypes` and
  `NamedPackagesExposeTrustedEffectContracts` skipped because
  `EVENTSTORE_PACKAGE_CONTRACT_DIR` was unset. The projection package test also
  returned early, although its runner row reports Passed. Supplemental package
  checks below do not turn this original suite green.

[Additive evaluated-policy evidence](attempt-01-policy-validation.json)
confirms Release/package mode, auditing enabled for all dependencies at low
severity, warnings-as-errors and enabled .NET analyzers. Executing the SDK's
`_ComputeSkipAnalyzers` target confirmed neither analyzer skip is enabled.
The frozen catalog retains its existing `NU1901`/`NU1902` warning exceptions and
existing `NoWarn` entries; this packet does not claim every vulnerability is an
error. The [helper checks](helper-validation.json) exercised explicit guards
and incomplete-result rejection under Python optimization.

## Package boundary and remaining release gates

[Attempt 02](attempt-02-local-packages/result.json) packed all fourteen real
manifest-listed archives in separate private scratch. Its local-only
`0.0.0-local-readiness.3b2350e7` label was below Tenants.Contracts' genuine
EventStore.Contracts `>=5.1.1` minimum; full consumer validation correctly refused
with `NU1605`. The exact three-package reminder probe passed. This verification
setup failure and all archive hashes are retained.

[Attempt 03](attempt-03-local-packages/result.json) used the unpublished
`5.2.1-local-readiness.3b2350e7` label above that dependency floor. All fourteen
actual `.nupkg` archives packed successfully. The committed full validator
passed 13 isolated library consumers and 1 tool consumer (native exit 0), and
the exact three-package reminder invocation passed (native exit 0). All
archive hashes are retained. This is supplemental package evidence; the
original whole Contracts failure and skips remain unchanged.

[Attempt 04](attempt-04-authority/result.json) reproduced the exact authority
command once, without exclusions, in another frozen-source copy. It passed
all 73 projects with native exit 0 in 364.903 seconds, within the original
480-second bound. Its process tree was fully waited and no descendants
remained. The [active-process snapshot](attempt-04-authority-active-processes.json)
captures only this attempt's argv/cwd, showing progress through a tracked
catalog evaluation. This supplemental pass never rewrites the failed suite.

The frozen specification records published SDK 5.2.0 as missing this query API.
Local archives are disposable candidates, never a published version or consumer
fallback. Projects' preparation at
`3361f2e3b5655fa1ad50a2d12c640bbd5edcbb4b` was not changed or retested.

Normal publication remains the central nightly route. Concrete remaining gates
include exact-current-main successful push CI and commitlint (required by
`scripts/verify-release-source.sh`), full retained product/security/compatibility
qualification, all fourteen real release packages and container acceptance,
and verified production publication prerequisites. EventStore is absent from the
three-module setup registry and has no delivered ref/adoption configuration or
approved pre-adoption push substitute. Infrastructure release, retained workload
and private/browser/Azure qualification, complete adoption delivery and a clean
standalone Builds checker remain required under
[ordered adoption](../../../../docs/ordered-module-adoption.md) and
[pre-adoption publication](../../../../docs/pre-adoption-publication.md).

No module push, release, tag, dispatch, adoption, parent-gitlink edit, owned
module policy edit, or credential change was performed by this implementation.
Concurrent sessions and their files/jobs were preserved. An independent session
committed root evidence while this verification ran; that does not establish
producer publication or change the tested source.

## Owner-controlled correction proposal

The [checked patch](retire-agent-policy-assertions.patch) retires the
`CommitMessagePolicyTests` class of instruction, Markdown and hook/configuration
assertions under CiCd's gate rule. [Its source binding](retire-agent-policy-assertions.json)
records a successful Git apply check at the frozen producer and the unchanged
actual commitlint workflow, configuration and hook. The patch is a migration
proposal; it was not applied to a module checkout or the tested source. Product
test and release qualification remain required after an owner applies it.

## Reproduce

From the CiCd root, use a fresh output directory for every attempt:

```sh
run-with-temp python3 -B _bmad-output/implementation-artifacts/evidence/eventstore-release-readiness-20261117/verify.py --output _bmad-output/implementation-artifacts/evidence/eventstore-release-readiness-20261117/recheck-baseline-01
run-with-temp python3 -B _bmad-output/implementation-artifacts/evidence/eventstore-release-readiness-20261117/verify.py --local-package-probes --output _bmad-output/implementation-artifacts/evidence/eventstore-release-readiness-20261117/recheck-packages-01
run-with-temp python3 -B _bmad-output/implementation-artifacts/evidence/eventstore-release-readiness-20261117/verify.py --authority-probe --output _bmad-output/implementation-artifacts/evidence/eventstore-release-readiness-20261117/recheck-authority-01
```

The helper returns nonzero for failed or incomplete checks. Each native child
exit remains in its result report. Rerunning the current hardened helper does
not rewrite the historical helper versions saved with earlier attempts.
