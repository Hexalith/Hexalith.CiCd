# Story 23 — stopped and saved on 2026-11-17

The user explicitly requested stop/save and will continue in a new session.
Resume only on their request. No story completion or adoption is claimed.

## Resume point

Continue the existing BMAD **step03 implementation**. The original workflow was
already rendered once. Do not rerender or restart routing. The most recent
child mistakenly invoked a nested initializer, received a duplicate-generation
refusal and stopped without changes; the corrected delegated handoff explicitly
continues the parent's existing step03.

- Spec: `cicd/_bmad-output/implementation-artifacts/spec-23-migrate-tenants.md`.
- Preserve original story baseline `771cfd0f01416d9adb2bdb3ff8cf8d1437d385e1`,
  status `in-progress`, review iteration0. Do not advance to step04 while tasks
  and acceptance remain incomplete.
- Snapshot: `cicd/_bmad/render/bmad-build/cicd-24343c124152/7e5058bea218030e62f6/`.
- Current scoped instructions: [cicd-discovery-handoff.md](cicd-discovery-handoff.md).
- Historical/latest detailed checkpoint: [local-product-checkpoint.md](local-product-checkpoint.md).

## Latest human decision

**Azure is outside MVP. Use the on-premises Kubernetes server192.168.1.30.**
Do not ask again for Azure workers or authority/custody files. Azure live
qualification and its private worker/environment provisioning are deferred;
preserve offline Azure product/security controls and future cloud safety rules.
Applicable product, scanner, native, release, delivery/adoption and hosted/nightly
acceptance remain required.

[mvp-onprem-target-decision.json](mvp-onprem-target-decision.json) records the
exact instruction. Read-only kubectl verified context `jpiquot@local`, API
`https://192.168.1.30:6443`, node `node1` Ready, kubeletv1.34.9. No cluster mutation
was performed in this continuation. Specs20/23 and ordered adoption docs record
the narrow clarification; those canonical planning edits are not published.

## Active implementation saved for resumption

The CiCd source-discovery prerequisite is partially implemented in:

`/home/administrator/projects/hexalith/cicd-story-23-discovery`

Branch `story/23-discovery-prerequisite`, base
`a2eb5fd22302ff4e37f6a1b2260a6f4e75a357c3`.

Two uncommitted source files are changed: `tools/scan_discovery.py` and
`tools/tests/test_scan.py`. The last observed diff was340 insertions/four
deletions. Baseline/harness files also exist under that worktree's evidence23.
The delegated agent is `/root/implement_discovery`; it has been instructed to
stop all verification, clean its own scratch and save a stop handoff. Final
closure and backup details are recorded below after cleanup.

The canonical scan using the actual locked TypeScript6.0.3 parser selected23
files and reported58 diagnostics against exact EventStore main
`d5902b78863b6920762d64c17b1276d95f2f9977`. This remains incomplete.
New bounded Python proofs cover source-relative pathlib roots/cwd, local import
roots and composed tracked paths; paired acceptance/refusal controls passed.
The full adversarial suite was interrupted by the stop request. Do not claim a
complete suite, complete scanner result or final candidate qualification.

Remaining gaps include computed env/argv, Bash wrappers/exporters and imports
crossing the Builds gitlink. Preserve uncertainty refusals, all literal/reachable
source coverage, limits and adversarial tests. Do not add repository/path/hash
allowlists or exclude dormant Azure actions from discovery. The agent correctly
retained the Builds-gitlink refusal pending a supported source contract.

Parent owns independent source inspection, exact commit-message preflight,
commits, full committed-candidate CiCd validation and publication. The prepared
[Tenants snapshot handoff](tenants-snapshot-implementation-handoff.md) stays
inactive until prerequisites and sequencing are resolved.

## Upstream snapshot feature

The additive EventStore feature is implemented and independently inspected:
optional folded capture on `EventStoreAggregate<TState>`, shared bounded capture
engine, strict actor configuration through the existing upstream host, tests and
documentation. Ordinary command dispatch and both replay paths are preserved.

Executed local commit `fb6704d173466e737fbe0f3892a6273f9c7f0a3e`, tree
`f3db94280035d32de6695f7de2eb900493395a36`, from base
`392a7e4e9daade785ee9f1ae5f40e25931002735`:

-775/775 focused executions across28 classes passed, zero skips; three audited
  Release graphs passed with zero warnings/errors.
- Full21 unit projects:18,792 passed, zero failed,51 existing skips.
- Current declared offline reports:1,261 passed, zero failed/skipped.
- Retained package/API/Python checks,13 library package consumers, one CLI
  consumer and old/new folded compatibility all passed.

**Whole verifier02 remains FAILED.** Concurrent workspace activity removed the
source worktree before its final freshness check. Keep that failure unchanged.
The first full attempt stopped earlier because its old projection stripped
fields required by Buildsv6.1.0; the second preserved all planned settings.
The resulting offline route exactly matches the separate MVP configuration.

Concurrent work merged the exact tested commit via
[PR402](https://github.com/Hexalith/Hexalith.EventStore/pull/402), squash
`bd10e1a2410027772c6588d61882cbc6204de39c`. Independently authenticated main is
`d5902b78863b6920762d64c17b1276d95f2f9977`. Its sole tree difference from the
tested commit is owned `.github/workflows/release.yml`; all10,679 other
blob/mode/gitlink entries are identical. This session did not publish that PR.

The removed worktrees `eventstore-story-23-snapshots` and
`eventstore-story-23-snapshot-recovered` must not be used as existing directories.
The canonical `/home/administrator/projects/hexalith/eventstore` contains the Git
objects/current main and is read-only to this task.

Evidence:

- [upstream implementation handoff](upstream-snapshot-implementation-handoff.md)
- [parent inspection](eventstore-snapshot-parent-inspection.json)
- [local commit](eventstore-snapshot-local-commit.json)
- [full verifier02](eventstore-snapshot-complete-qualification02.json)
- [current unit counts](eventstore-snapshot-current-unit-results02.json)
- [current offline TRX classification](eventstore-snapshot-trx-classification02.json)
- [concurrent publication/source equivalence](eventstore-snapshot-concurrent-publication.json)

The raw driver's141-TRX inventory includes138 tracked historical/dependency or
policy-fixture reports. **Do not aggregate those as current executions.** Only
declared current offline roots and the matched current unit console/results
receipts qualify the counts above. All parent sessions and wrapper scratch are
closed/removed.

At the last public read09:47UTC, Contracts/Client/DomainService/Server still list
5.2.0 latest, with no5.3.0; GitHubv5.2.0 is mutable. No compatible public snapshot
SDK release is verified. The concurrent owned workflow adds a separately
approved **Contracts-only** publisher with fixed archives. Do not widen/reuse
that controller for the whole SDK. Recheck package coordinates/source before a
release to avoid a concurrent5.3.0 collision.

## Tenants state

Workspace `/home/administrator/projects/hexalith/tenants-story-23-current` is
clean on `story/23-tenants-current` at
`a1ad5f5bb531516a49f91166a2d2306d20ef7570`, tree
`e04a10e3f6249f9c6b8e5c1c6685a1f2af11c0c3`.

No snapshot enrollment/parity implementation was added there in this
continuation. Preserve its15 owned actual files/modes and nine pins. Its selected
EventStore package is5.1.1; published Testing.Integration3.128.4 remains frozen.
Effective snapshot interval is100; the old50 comment is stale and must be
explicitly reconciled without silent tuning.

The full prior500K trial timed out at3600seconds. The later diagnostic was
intentionally interrupted and remains incomplete. Neither qualifies the
30-second NFR. Future implementation must establish genuine complete mutable
state/serializer parity and both-host enrollment through supported APIs, retain
all workload/assertion/budget/refusal requirements, and then run final native
and released-source checks. Candidate-feed diagnostics are not published or
delivered baseline proof. No native Aspire/Dapr/500K job is active.

Shared Builds prerequisite is already published as immutable bot-authored
v6.1.0/a1e0c310b1f1a50d78e6132890fae6bcba769f6d and selected in CiCd. Its earlier
delivery aggregate was not wholly green (AI.Tools refusal); do not label it
Tenants adoption or a complete delivery pass.

## Administration and remaining boundaries

Latest saved App read is [mvp-app-readback04.json](mvp-app-readback04.json):20
saved repositories include EventStore, FrontComposer and Tenants, Save disabled,
foreign selections preserved, own window closed. The earlier derived03 count
incorrectly included a description footer and is explicitly superseded. Raw
attended03 remains valid. Initial refresh02 could not identify a new tab; it
established no absence. The reader now uses a separate Chrome window.

NuGet attended policy03 authenticated jpiquot and loaded23 policy IDs, preserving
27252 and27339; EventStore card16915 is Active. Detailed EventStore policy scope
assessment is unfinished. No policy/key was created, changed or deleted here.
The reader waits for the known retained policy before treating inventory as
loaded; the earlier cold collapsed02 read is incomplete, not policy absence.

[EventStore admin readiness02](eventstore-mvp-admin-readiness02.json) is a
successful intended maintainer-profile read: two rulesets, environments copilot
and production, publishfalse, NuGet userjpiquot,215 releases,244 tags and1,257
CodeQL analyses. No cleanup assessment/deletion was performed. The CLI is
gh2.46.0, without `--slurp`; use compatible `--paginate` output handling.
[pagination clarification](eventstore-mvp-admin-pagination02.json) explains that
decoded document count is not HTTP page count. Failed readiness01 is preserved.

The human resolved the legacy Zot mapping: API key
`099585e7-fd9e-4aac-9042-56426c1add7b` backs HEXALITH_ZOT_API_KEY, with only
EventStore, Memories, Parties and Tenants consuming it. Do not reask that fact.
No rotation/revocation has occurred. Preserve personal9eba6461, otherd122a9d6,
global administrators and distinct read-only cluster-reader access. The concrete
scoped replacement plan exists but is not provisioned; retain the old pair/key
until the approved adoption/continuity boundary is met. Ordered adoption
EventStore→FrontComposer→Tenants and its implications for shared legacy-key
retirement still need careful reconciliation; do not infer early revocation.

Use ordinary CiCd-agent profile for CiCd/Builds. Module writes use the established
module-agent token in memory. Authorized interactive administration uses only a
command-local `/home/administrator/.config/gh` override. Before diagnosing403,
check effective profile, token-override presence, account/target and relevant
read-only permission metadata. Never print credentials or change profiles to
bypass a refusal.

Canonical CiCd root has uncommitted planning, docs, evidence and helper changes
from this work. Preserve concurrent work; **never globally stage/commit root or
module checkouts**. Use isolated owning worktrees and explicit paths. All ad hoc
workspace jobs use run-with-temp/private caches; never initialize nested
submodules or weaken tests/audits/coverage.

Still pending: complete S1 discovery and committed CiCd qualification, compatible
public EventStore SDK release, genuine Tenants enrollment/parity/native/final
bootstrap, registration/ordered adoption, scoped legacy cleanup, green hosted CI
and the next genuine scheduled nightly. Preserve truthful incomplete status.

## Shutdown closure

All own jobs are closed. The final scanner suite, session72798/PID1411240,
received SIGINT and exited130. Its wrapper exited, its scratch is absent and
the process census found no remaining own scratch processes. No implementation,
test, commit or remote operation ran after the cleanup directive.

- [Exact child stop handoff](cicd-discovery-stop-handoff.md)
- [Source hashes and interrupted verification state](cicd-discovery-stop.json)
- [Saved two-file source patch](cicd-discovery-stop.patch)
- [Process/scratch closure](discovery-stop-processes01.json)
- [Parent stop-state and workspace inventory](session-stop-state.json)
- [Unexecuted qualification utility backup](cicd-discovery-qualify-unexecuted.py.txt)

The utility backup is text only. Its source-root calculation depends on its
original isolated-worktree path; restore it there before reviewing/running it.
Parent independently checked both source hashes and saved patch hash against
the child manifest, backed up the utility and confirmed scratch absence. All
uncommitted work remains preserved. Resume only when requested.


## Publication update — subsequent user request

The user subsequently requested pushing all saved changes. The shared main
checkpoint is `a46a061c02f3865296cc3e98231f92abb8e36987`. The scanner source,
baseline and draft utility are now committed and remotely verified on
`story/23-discovery-prerequisite` at `efc6285bedebf0a96452952256378178e46715d5`. Its worktree is clean; its
original implementation baseline remains a2eb5fd2. The branch's
`discovery-publication-checkpoint.json` records six focused methods passing
again on the exact source, zero failures/skips, and released-policy commit
validation. Full qualification remains incomplete and implementation paused.

Resume from that published feature branch and the saved stop handoff. The
scanner changes have not been merged into main and no story completion,
release, adoption or scheduled acceptance is claimed by this publication.
