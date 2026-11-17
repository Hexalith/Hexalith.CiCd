# Active upstream snapshot implementation slice

The human approved `snapshot-compatibility-proposal.md` on 2026-11-17, including
implementation and release of an additive EventStore prerequisite. This context
narrows the current implementation slice; the parent retains the complete story.
The original story baseline stays unchanged.

Work only in `/home/administrator/projects/hexalith/eventstore-story-23-snapshot-recovered`,
branch `story/23-snapshot-recovered`, fresh fetched base
`392a7e4e9daade785ee9f1ae5f40e25931002735`. An external concurrent operation
removed the preceding isolated worktree and branch after final01 completed.
The parent recovered its authenticated exact patch onto freshly fetched main;
see `eventstore-snapshot-recovery.json`. Main changed only `.gitmodules` and
gitlinks, which must be preserved. The canonical checkout remains untouched.
Tenants remains clean
at `a1ad5f5bb531516a49f91166a2d2306d20ef7570`; do not edit it in this slice.

Read the worktree's AGENTS.md, .editorconfig, .gitattributes and relevant build,
test, architecture and configuration guidance before edits. Its direct AI.Tools
folder contains only five ordinary instruction Markdown files exported from its
exact declared pin (no Git initialization). This supplies the permitted baseline
without nested submodules. Read its hexalith-llm-instructions.md and applicable
Git/state guidance. Never load skills from references. Use the installed allowed
dotnet-inspect skill when querying package/API contents; verify actual CLI help.

The parent already inspected the known native baseline: exact package producer
f792bba6c0564d3c36dda6ad1c2fc55b0b0a6331 and approved executable pin3b2350e7
have identical 21 inspected runtime/source blobs. Current main's twelve newer
commits change no snapshot/actor runtime enrollment files. The native parent job
successfully starts that host and processes real actor commands but confirms
FoldedSnapshotQualificationAbsent and no automatic snapshots. The full preceding
60-minute workload failure and later explicitly interrupted diagnosis remain
failed/incomplete. No parent native workload is active. In this child slice,
perform focused in-process builds/tests/API inspection only; no Aspire/Dapr,
500K workload, external runtime, credentials or publishing operation.

Read product-folded-contract-handoff.md, product-folded-contract-conflict.json,
the scratch FoldedSnapshotContractProbe.cs and snapshot-compatibility-proposal.md.
They establish:

- Actual ordinary TenantAggregate discovery/command/replay cannot capture folded
  state. DomainProcessorBase<TState> has capture but lacks aggregate replay and
  convention discovery, so substituting bases would lose required capabilities.
- The domain router requires a matching genuinely qualified bounded V1 producer;
  declaring a profile alone cannot enable safe capture.
- Actor registration supports actor-only metadata without a domain state assembly,
  but unchanged EventStore Program exposes no deployment configuration hook.

Implement a reusable additive solution in EventStore's owning libraries and
executable. The actor executable must be able to consume validated deployment
configuration for explicit reviewed profile identities and finite capture limits,
using its supported actor-only qualification contract and without a Tenants
assembly reference, arbitrary assembly loading, startup injection or copied host.
Absent configuration retains existing unenrolled behavior. Supplied malformed,
duplicate, incomplete or invalid declarations must fail safely rather than grant
unbounded capture or silently disappear. Reuse existing identity, qualification,
serializer and limit validation; document the exact supported configuration.

Supply the minimum supported processor/registration compatibility needed for an
existing EventStoreAggregate<TState> consumer to opt into folded capture while
preserving ordinary command dispatch, discovery and both existing replay routes.
Choose the narrowest compatible public API; keep existing bases/signatures and
unenrolled behavior compatible. Reuse the existing bounded capture mechanisms;
do not fork their security/admission algorithms or invent default qualification.
Module-specific state copying, event serializers, parity evidence and finite
resource declarations remain module-owned opt-in work for the next Tenants slice.
A generic test-profile declaration is not module qualification.

Inspect and modify only the required product sources, focused product tests and
configuration/upgrade docs. Likely areas are Client/Aggregates and Handlers,
Client/Registration, DomainService/EventStoreDomainServiceExtensions and router,
Server configuration, and src/Hexalith.EventStore/Program.cs. Do not remove or
weaken replay/readability/digest/identity/serializer bounds, failed-capture safety,
event-batch preservation or cancellation. No CI/story/evidence/YAML policing tests.
No audit demotions, warning suppressions, skips, version rollback or threshold
changes. One C# type per file; follow the actual repository formatting rules.

Meaningful focused verification must cover opt-in successful capture/restore/tail
parity through the actual aggregate discovery and domain router; normal commands
and old sync/async replay; unenrolled compatibility; mismatched domain/aggregate/
profile and invalid configuration; duplicate declarations; finite serializer and
capture refusals; cancellation/failure without corrupting the pre-command state
or valid result/event batch. Use realistic mutable state and success/rejection/
no-op cases rather than only a counter. Verify actual host configuration wiring
through behavior, never tests asserting Program/YAML source text. Run affected
existing suites, including existing aggregate discovery/replay, folded capture,
bounded producer/router and startup/configuration tests, plus a clean audited
Release build. A focused failure is fixed or reported precisely, never hidden.

Use run-with-temp for all disposable jobs. Keep copies, package feeds, package
caches and outputs under its TMPDIR, including private HOME/DOTNET_CLI_HOME/XDG
paths. Materialize only directly needed owning-repo dependencies from actual
pinned Git objects; never initialize nested references or import unrelated dirty
work. Preserve sanitized useful logs/results outside scratch and close all jobs
before handoff. Bind final evidence to full base, normalized candidate tree,
changed raw files and exact dependency revisions. Preserve failed attempts.

All 29 protected files and ten pins in eventstore-snapshot-recovery.json
must retain their actual bytes/modes and gitlink values. The historical original
baseline and final01 receipts remain valid only for their original graph.
Finish the production-helper formatting correction, verify token preservation,
and rerun the 28 affected classes and three audited Release builds on this fresh
graph. Adapt the local qualification utility's source path; it must materialize
the new exact Builds pin `a327bc5cf0eb2bd715deed6f1ea278a8f6946a2f` from available
Git objects, without nested initialization or changing any gitlink. Read the
actual new-pin guidance (its applicable baseline text is unchanged).
No workflows, Builds pin,
.gitmodules, agent instructions or owned settings edits. No edits to either parent
isolated workload utility. Parent owns final inspection, commitlint/commits,
complete exact-source qualification, module-agent publication, released prerequisite
verification and later CiCd graph refresh. The EventStore-only pre-adoption
substitute is recorded separately in the frozen story20 spec; it is not a pass
for this candidate or permission to fabricate adoption. Do not commit or push.

Report final code/API behavior, precise red/green counts and input binding, all
preservation/resource closure facts and remaining release/native/Tenants work.
