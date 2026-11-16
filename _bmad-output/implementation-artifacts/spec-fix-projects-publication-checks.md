---
title: 'Repair Projects publication qualification'
type: 'bugfix'
created: '2026-11-16'
status: 'in-progress'
route: 'oneshot'
baseline_commit: 'ec481fd50b280e2d41f9baecbd03945c833e4538'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="user requested fixes for the two reported publication failures">

## Intent

Repair the Projects preparation checks blocking the already requested push. Load each selected prebuilt owner's declarations and adapters in one dependency-resolved assembly context, preserving exact artifact identity and shared SDK contract identity without rebuilding. Losslessly gzip only the twelve historical XML artifacts rejected by the released audit; preserve original paths, modes, Git identities and hashes in a manifest with scratch-only reconstruction instructions. Keep historical receipts, active product inputs, audit enforcement, all product assertions and owned module portions unchanged. Verify assembly collisions and shared-contract refusal, archive roundtrips and active audit negative controls, then rerun the complete approved Projects preparation proof. Continue the existing authorization to push all qualified changes using their intended credentials, preserving concurrent work. No adoption or product/package release is authorized by this repair.

</frozen-after-approval>

## Implementation Notes

- The user's existing push-all requests and subsequent fix instruction authorize repair of the known dirty preparation; preserve it and every concurrent migration. Investigation found no intent gap. The local repair is reversible and bounded: fixture assembly loader and its product regressions, twelve compressed evidence files, archive manifest/documentation and focused archive/audit verification. Publication remains subject to the existing Projects-only pre-adoption approval and ordinary repository rules.
- Root cause: `Assembly.LoadFrom` unifies a selected child with a different default-context assembly of the same identity. The SHA-256 guard is correct and must remain. Use a context per selected executable, and the same context for split Tenant declaration/adapter assemblies. Share SDK/JSON contracts only on matching full identity and bytes; allow framework-only unresolved fallback.
- Released audit lint examines XML roots in every regular blob, so changing filename suffixes is insufficient. Gzip preserves the original evidence bytes; the original twelve paths have no live build, script, test or workflow inputs. Historical receipts stay intact. Verify roundtrip bytes/modes against the baseline Git blobs and retain active XML rejection controls.
- Initial Release qualification passes 37 existing fixture/credential controls and all six new assembly cases, with zero warnings, failures or skips. The released full-tree audit passes all twelve lossless archive roundtrips and both active XML negative controls. Review found additional image-replacement and transitive-binding cases; concurrent improvements were preserved and are included in the final qualification rather than overwritten.

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
