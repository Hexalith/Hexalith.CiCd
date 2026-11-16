---
title: 'Repair Projects publication qualification'
type: 'bugfix'
created: '2026-11-16'
status: 'draft'
route: 'dispatch'
baseline_commit: 'ec481fd50b280e2d41f9baecbd03945c833e4538'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="user requested fixes for the two reported publication failures">

## Intent

Repair the Projects preparation checks blocking the already requested push. Load each selected prebuilt owner's declarations and adapters in one dependency-resolved assembly context, preserving exact artifact identity and shared SDK contract identity without rebuilding. Losslessly gzip only the twelve historical XML artifacts rejected by the released audit; preserve original paths, modes, Git identities and hashes in a manifest with scratch-only reconstruction instructions. Keep historical receipts, active product inputs, audit enforcement, all product assertions and owned module portions unchanged. Verify assembly collisions and shared-contract refusal, archive roundtrips and active audit negative controls, then rerun the complete approved Projects preparation proof. Continue the existing authorization to push all qualified changes using their intended credentials, preserving concurrent work. No adoption or product/package release is authorized by this repair.

</frozen-after-approval>

## Implementation Notes

- Existing push/fix authorization covers the dirty preparation. Preserve concurrent migrations and the approved Projects-only pre-adoption publication procedure.
- `Assembly.LoadFrom` unified differing same-identity images. Use one context per owner, including split Tenant adapters. Share only byte-identical SDK/JSON contracts; retain SHA/MVID checks and framework-only fallback.
- Released audit examines every blob's XML root. Gzip preserves twelve inactive historical inputs; verify baseline bytes/modes and active rejection controls. Original receipts stay intact.
- Focused qualification now passes 57 cases with no warnings, failures or skips, including functional assembly replacement, transitive binding, real owner factories and diagnostic safety. Full-tree audit and twelve archive roundtrips pass. Preserve concurrent improvements.
- Replan trigger: fresh Projects main now requires an unreleased SDK API. Published EventStore 5.1.1 and latest 5.2.0 lack QueryResultContractAttribute. Full qualification stops at fourteen compile errors; a release is beyond this repair. Scoped checks use retained binaries and cannot qualify current main. See the evidence packet's README for exact results and preserved candidates.

## Code Map

- `tests/Hexalith.Projects.PackageFixtures.AppHost/PackageOwnerLoadContext.cs`: isolated artifact resolution; retain hash/MVID guards.
- `tests/Hexalith.Projects.Integration.Tests/PackageOwner*Tests.cs`: functional loading and real factories.
- `evidence/fix-projects-publication-20261116/`: immutable archive audit, source snapshots, SDK evidence and failed full proof.

## Open Questions

1. Prepare EventStore release readiness too, retaining normal nightly publication, or leave this repair scoped until its normal SDK release? No package release or new SDK version can be assumed.

## Review Triage Log

- High, patch — cached loaded images could survive atomic replacement. Frozen per-path hashes and actual module-ID checks now reject drift; the functional replacement regression exercises different implementations.
- High, patch — sharing an identical ordinary intermediary could bind the host's differing transitive dependency. Sharing now applies only to SDK/JSON contracts; a functional root/middle/leaf probe requires the owner's implementation.
- Medium, patch — lazy SDK loading could create a second contract identity. Recognized contracts now resolve through Default before their full identity, bytes and loaded module are checked; missing canonical contracts are refused.
- Maybe-false, deferred (medium if reproduced) — no selected adapter factory requiring a separately resolved native library was demonstrated. A native factory/dependency reproduction would establish whether explicit unmanaged dependency resolution is needed; this repair makes no new native-loading promise.
- Medium, patch — initial regressions did not execute a transitive dependency graph. Functional replacement and root/middle/leaf probes now accompany the original collision/SDK controls; the retained browser product hook exercises real adapter composition.
- Medium, patch — Python optimization could remove reconstruction assertions. The verifier and documented extraction use explicit checks that remain active under optimization.
- Medium, patch — manifest modes were self-validated. The verifier now compares source Git tree modes, manifest modes and candidate archive modes before reconstruction.
- Medium, patch — twelve rows could duplicate paths. The verifier now requires twelve unique originals, unique archives, exact mappings and the original reported scope.
- Medium, patch — worktree reads were not bound to the audited candidate. The verifier now freezes a Git tree first and reads archive/manifest bytes and original-path absence from that immutable snapshot.
- Low, patch — compression reproduction was unspecified. The manifest records Python/zlib, level 9 and timestamp 0; the reconstruction README records the exact compression call and hash check.
- Medium, patch — malformed escaped surrogate strings threw from transport diagnostics. Catch InvalidOperationException and cover the reproduced input; never replace the original fixture failure.
