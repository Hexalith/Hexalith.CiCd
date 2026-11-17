# Snapshot compatibility prerequisite for Tenants migration

Status: human-approved prerequisite, with upstream implementation under qualification.
The retained topology is unchanged. The original diagnosis below precedes implementation.
The exact-package SDK 11 DI probe matches all 11 factual capability observations
with 0 failed/0 skipped, and its Release build has 0 warnings/errors. This diagnoses
a capability gap; it does not qualify parity or performance. See
[probe packet](product-local-foldedcontract02.json) and
[actual output](product-folded-contract-02.log). The unchanged product is
a1ad5f5bb531516a49f91166a2d2306d20ef7570/tree
e04a10e3f6249f9c6b8e5c1c6685a1f2af11c0c3.

The existing nightly workload must retain 1,000 tenants, 500 commands per tenant,
100 configuration keys, concurrency 50, the 30-second rehydration assertion and
60-minute allowance. Full local qualification has not passed. Native observation
confirms the selected EventStore.Server 5.1.1 uses effective interval 100 and emits
FoldedSnapshotQualificationAbsent; automatic snapshots are skipped. Its source
comment's intended interval 50 was not exercised, and no interval was retuned.

The current contract requires three pieces that the module does not enroll:

- An actual folded-state processor, not only the legacy EventStoreAggregate base.
- The bounded domain result producer and a genuine reviewed state/serializer
  parity declaration with finite capture limits.
- Matching actor-host qualification on the upstream EventStore executable as
  well as the Tenants domain-service host. The accepted pinned executable has
  no configuration/discovery hook for that actor registration.

A registry entry in only the performance fixture would neither qualify the
actual serving topology nor prove parity. Disabling snapshot admission, reducing
workload, replacing actor calls with direct storage writes or raising the budget
would not satisfy the approved migration.

## Recommended path: additive upstream capability

Keep the named upstream executable and topology. Add a supported, validated
deployment configuration seam in EventStore that can enroll actor-only reviewed
profiles without a Tenants.Server assembly dependency. Use the existing
AddEventStoreFoldedSnapshotActorQualification contract; reject duplicate/missing
identity/evidence/limit declarations and retain existing admission and startup
behavior for unenrolled applications. Publish the additive capability through
EventStore's normal verified release process. Its current migration work is
concurrent; reconcile that work before editing or publishing there.

The typed processor base with folded capture currently lacks the aggregate replay
contract used by Tenants; replacing its base without an adapter would lose a
required existing capability. Establish a supported compatibility path preserving
ordinary commands and both existing replay contracts as well as folded capture.

Then adapt the Tenants processor through that supported folded-capture path, supply
the bounded result producer and share one immutable profile definition between
the actual actor/domain serving hosts. Qualify full-prefix versus folded-state
plus tail replay for the supported tenant event/state mix, complete state and
configuration limits, serializer behavior, source identity and refusals. A label
saying test-parity is not evidence. Preserve product/public-package compatibility.

Finally consume the released capability through CiCd-owned pins/registration,
run the complete unchanged benchmark and exact-source bootstrap, adopt, perform
the now-concrete legacy credential replacement/revocation and verify hosted CI
and the next genuine scheduled central nightly. The declared 50 versus observed 100
scenario must be explicitly reconciled from evidence as part of that work.

This adds EventStore product prerequisite work to story 23's approved CiCd/Builds/
Tenants migration. It does not authorize a module-owned substitute executable.

## Alternative disposition

Keep story 23 in progress awaiting an independently delivered EventStore
capability. Preserve the qualified local migration/progress patch, all failed
receipts and current legacy publishing; do not register/adopt Tenants or claim
performance acceptance until the prerequisite is available.

A module-owned actor executable is a different topology/source-boundary decision
and is not included in the recommended path or existing approval.

## Source binding and unchanged behavior

The actual Client/DomainService/Server 5.1.1 assemblies bind producer
f792bba6c0564d3c36dda6ad1c2fc55b0b0a6331. The retained executable gitlink
is 3b2350e7c1fff640131f8101596c78a59e31a03f. A read-only comparison to fresh
EventStore main 96363934c6fd1da4d50c2078b13929c473ecab7f records 12 new commits
without a changed actor Program or snapshot enrollment/runtime API; its new
ProductionProfileBridge SDK proof is unrelated build/deployment machinery.
See [eventstore delta](eventstore-current-main-source-delta.json). This does not
claim a newer published package is qualified without its own exact inspection.

The property/state surface includes Configuration, CreatedAt, Description,
HasMembershipHistory, Name, Status, TenantId and Users, with 21 actual Apply event
types including rejection/no-op cases. New parity evidence must cover these
existing semantics, not a reduced counter-only surrogate. The legitimate change
must preserve all existing replay consumers and public package compatibility.

[Complete contract handoff](product-folded-contract-handoff.md) and
[parent inspection](product-folded-contract-parent-inspection.json) confirm all
probe/API jobs and disposable workspaces are closed. The human approved the recommended upstream prerequisite on 2026-11-17; see
[saved authorization](snapshot-prerequisite-scope-approval.json).
