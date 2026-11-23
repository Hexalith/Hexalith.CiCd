---
title: 'Remove raw evidence from the tree'
type: 'chore'
created: '2026-11-23'
status: done
baseline_revision: 0c05f8bf368828515f0b9d2cfb4a97ff6d24c3ae
review_loop_iteration: 0
followup_review_recommended: false
context: []
warnings: []
deferred: []
---

<intent-contract>

## Intent

**Problem** — Raw outputs from past qualifications and publication attempts enlarge every new checkout. The retained story records and receipts carry the decisions and source identities.

**Approach** — Apply the approved proposal’s D3b R1 cleanup and §4.1 acceptance criteria after stories 28-3 and 28-6. Remove only unreferenced raw evidence from the current Hexalith.CiCd tree in one ordinary deletion commit per evidence root.

## Boundaries & Constraints

Separate maintainer approval is required before implementation. Preserve Git history, decision records, retained receipts, frozen inputs, and files referenced by tracked files outside evidence. Preserve inputs to any live procedure, including references within evidence. Keep a path whenever its role or a plausible reference remains unresolved. Leave shared tooling, workflows, policies, and submodule gitlinks untouched. Keep disposable inventories and logs under `run-with-temp` and record compact identities and digests here.

For story 28-8, the unchanged EventStore `derivedFrom` diagnostic may satisfy the repository-input check for proceeding to workflow review only under the exact baseline comparison in Verification. Record the suite as failed when it reports that diagnostic. Run all checks as written and leave repository gates and their pass criteria intact.

</intent-contract>

## Code Map

- `_bmad-output/planning-artifacts/sprint-change-proposal-2026-11-18.md:145` and `:284` define D3b R1 and the story’s three acceptance criteria. D3 names `fix-publication-20261116/cicd-merged-candidate.patch`, a generated output in a sibling implementation packet. Group such packets with `_bmad-output/implementation-artifacts/evidence/` under the implementation-artifacts root. The other root is `_bmad-output/specs/spec-cicd/evidence/`. Story records at either location are protected.
- `_bmad-output/specs/spec-cicd/stories/28-3-executable-fixtures-out-of-evidence.md` and `28-6-evidence-policy-and-growth-stop.md` record completed prerequisites. `tools/tests/test_repository_inputs.py` covers active input boundaries. `tools/repository_inputs.py:evidence_dependencies` omits planning output and selected prose, so the deletion audit must also cover those tracked sources.
- `.github/workflows/evidence.yml` calls `tools/check_evidence.py`. Its `changed_entries` checks additions, modifications, and type changes. Use its policy to check the story receipt and as a source of candidate suffixes.
- `_bmad-output/specs/spec-cicd/gate-classification.md:36` links `evidence/17/gate-classification.json`. `docs/pre-adoption-publication.md:77` links `evidence/18/folder-owner-prerequisite.md`. Use both as preservation checks for relative path resolution.

## Tasks & Acceptance

**Execution**

- [x] `_bmad-output/implementation-artifacts/` and `_bmad-output/specs/spec-cicd/evidence/` — after approval, pin the clean implementation baseline by full commit and tree ID. Inventory committed paths, blob IDs, modes and sizes. Build a path-level manifest by root for confirmed raw logs, transcript dumps, generated patches and tree dumps, package and test outputs, and superseded attempt payloads. Use content or provenance to establish ambiguous kinds such as JSON. Size, extension, or an attempt directory name alone is insufficient.
- [x] `docs/`, `setup/`, `_bmad-output/` and the rest of the tracked superproject — audit candidates against committed sources, including retained stories, policies, scripts, and symlinks. Resolve repository-root, source-relative, and URL paths, bare filenames, and directory or computed selectors that could read candidates. Distinguish current targets from paths in another repository, output destinations, and filenames embedded in captured diffs. Verify the two known preservation checks and retain unresolved candidates. Historic links solely within evidence can use the recorded ancestor when their target is removed. Repeat the audit if the starting revision changes.
- [x] Both evidence roots — stage only the verified manifest paths. Check each staged diff before committing. Make one deletion commit per root with the full direct parent SHA in its message. Verify that parent contains every removed path with its original blob and mode.
- [x] This story file — record the baseline and last deletion commit and their tree IDs, each cleanup commit and its parent, per-root path counts and bytes, and the reference audit’s result and digest. Measure the net tracked-tree change and report the receipt’s own size separately.

**Acceptance Criteria**

1. Given the pinned starting tree, when the cleanup diff is compared with the audited manifest, then every change in the cleanup commits is a deletion of positively identified raw evidence with no tracked reference outside evidence or live internal consumer. Decision records, receipts, and referenced paths retain their original blobs.
2. Given the cleanup branch, when its commits are inspected by evidence root, then exactly one deletion commit covers each root with removals. Its message names the full SHA of the direct parent, which is the last commit on that branch containing all paths removed by the commit.
3. Given the baseline and final trees, when `git ls-tree -r -l -z` is summed over blob entries once per tracked path, then the story records the before and after totals and actual reduction in bytes and MiB alongside the proposal’s estimate of about 280 MiB.
4. Workflow review requires a passing cleanup audit and both evidence checks. The full repository-input suite must pass on both trees or reproduce precisely the sole baseline failure specified in Verification.

## Spec Change Log

## Review Triage Log

### 2026-11-23 — Review pass

- verdicts: 10 findings — high 0, medium 5, low 5, false 0, maybe-false 0
- findings:
  - `[medium]` `[patch]` The initial cleanup removed `preservation-final.json`. The adjacent README binds the final preservation decision to that file. The replacement tree keeps its original blob.
  - `[medium]` `[patch]` The initial cleanup removed `provision-cleanup-incomplete-1.json`. It records 122 successful CodeQL deletions absent from the successful retry. The replacement tree keeps its original blob.
  - `[medium]` `[patch]` The initial cleanup broke Story 4-1's checksum set. The retained `SHA256SUMS` includes `inventory.json`. The replacement tree keeps its original blob.
  - `[low]` `[reject]` The initial push-event log covers only the deletion tree. The unit suite and push-event check cover different surfaces. Final verification runs the push-event checker on the exact receipt commit.
  - `[low]` `[reject]` The initial manifest digests lack a documented encoding. This receipt records the encoding of the replacement manifests and how to reproduce them from Git.
  - `[medium]` `[reject]` The resumed workflow diff initially showed only the receipt. Its baseline was the cleanup tip when this run resumed. Review also inspected both original deletion commits, and the replacement branch diff uses the original cleanup baseline.
  - `[low]` `[reject]` The deletion-only evidence run has zero entries under the checker's additions, modifications and type changes filter. Final verification covers the receipt commit.
  - `[low]` `[reject]` The receipt first enters the checker's scope at the receipt commit. Final verification covers that commit.
  - `[medium]` `[reject]` The tracked-tree acceptance criteria concern the earlier Git trees identified in the initial receipt diff. Review inspected those commits, followed by a direct comparison of the replacement trees.
  - `[low]` `[reject]` The recorded verification scope ended before the receipt commit. The comparison remains tied to the exact deletion tree. The final push-event check covers the receipt commit itself.

## Design Notes

The planning snapshot at `0c05f8bf368828515f0b9d2cfb4a97ff6d24c3ae`, tree `7a9a522df40bddf3aedda0f4b1460ea4a5ad34c2`, contains 8,384 tracked blobs totaling 543,985,515 bytes. The two planned roots contain 231,755,151 and 261,947,193 bytes respectively, including retained material. Recompute from the approved implementation baseline.

## Verification

- Compare `git diff-tree -r --name-status -z --no-renames` for each parent and cleanup commit with the manifest. Check retained modes and blobs, parent ancestry, and `git diff --check`.
- Run `run-with-temp python3 -B -m unittest discover -s tools/tests -p test_repository_inputs.py` in clean checkouts of the original pre-cleanup baseline `0c05f8bf368828515f0b9d2cfb4a97ff6d24c3ae` and the final cleanup candidate. Record both trees' identities, outcomes and log digests in the receipt. Accept two passing runs or the following exact match:
  - Each run reports one failure in `RepositoryInputsTests.test_tracked_active_repository_inputs_have_no_evidence_dependency` with the sole diagnostic `tools/qualification/pre-adoption/eventstore/qualify-eventstore-snapshot-candidate.py:173: active input references evidence`. Every other test passes on both trees.
  - The flagged script has blob `eb707ce0ecca6263a7801595f3b0abe280f52609` on both trees.
- Run `run-with-temp python3 -B -m unittest discover -s tools/tests -p test_check_evidence.py` on the final candidate. Run `python3 -I tools/check_evidence.py` with `GITHUB_EVENT_NAME=push`, `GITHUB_SHA` set to the checked-out candidate and `EVIDENCE_PUSH_BEFORE` set to the original pre-cleanup baseline. Both checks must pass.

## Cleanup Receipt

The maintainer separately approved implementation of story 28-8 on
2026-11-23 before the cleanup began. The implementation baseline was
`0c05f8bf368828515f0b9d2cfb4a97ff6d24c3ae`, tree
`7a9a522df40bddf3aedda0f4b1460ea4a5ad34c2`. The original worktree
and index matched that tree at the start of the audit.

| Evidence root | Deletion commit | Direct parent | Commit tree | Removed paths | Removed bytes |
| --- | --- | --- | --- | ---: | ---: |
| `_bmad-output/implementation-artifacts/` | `07e989a5ff784a2cc2ea983b32dd94cf031643ff` | `0c05f8bf368828515f0b9d2cfb4a97ff6d24c3ae` | `f55e7e72bfc933a0ebfa4ed9e38d4e394b099555` | 19 | 80,839,007 |
| `_bmad-output/specs/spec-cicd/evidence/` | `fb2d4af6b6a0ee3e079942fc2a6dcf16e8e5bc9e` | `07e989a5ff784a2cc2ea983b32dd94cf031643ff` | `0e6f6055555feaaa46deafb76298da379b3af39b` | 160 | 54,437,042 |

The replacement commits are on `story/28-8-reviewed-cleanup`. The initial
attempt remains available on `story/28-8-remove-raw-evidence` at
`cfc89a1d61229fa93abd57e64e572013ef2aed7c`. Both branches descend from
the original baseline.

Summing `git ls-tree -r -l -z` over blobs once per tracked path gives
8,384 blobs and 543,985,515 bytes before cleanup and 8,205 blobs and
408,709,466 bytes after the second deletion commit. The decrease is
135,276,049 bytes (129.01 MiB) against the proposal’s estimate of about
280 MiB. Including the 16,615-byte receipt, the tree has 8,206 blobs and
408,726,081 bytes, a net reduction of 135,259,434 bytes (128.99 MiB).

### Preservation Audit

The baseline inventory covered 8,402 tracked entries, including 18 gitlinks
and zero symlinks. The first audit classified 1,031 raw-output candidates.
Review narrowed the 383-path draft removal list by retaining 204 additional
paths. The supplemental scan checked full and source-relative paths
(including sibling basenames) in 8,173 tracked text blobs and repeated the
path search in newly retained files. It kept protected receipts and paths
identified by retained evidence, including checksum manifests, frozen
qualification packets and historical inventories with plausible consumers.
The audit file was sorted unique UTF-8 lines of candidate path, tab, and
source location or rationale. Its SHA-256 was
`b4cc42d07c146276abb0509f1e1893a77f2dec8413513aa53ba908e91875b622`.

Classification of the remaining deletions used command streams, unified
diffs, ZIP and xUnit signatures, JSON tree and response schemas, and
superseded qualification provenance. Each deletion is within its designated
root. The large `cicd-merged-candidate.patch` is the generator's
output and a size entry in the proposal inventory. Its generator uses
`write_bytes` at that destination. The historical
`Projects-candidate.patch` is identical to the retained
`Projects-pending.patch` (blob `d622000ce309d818b9bafc45859447cf65b95496`),
which supplies the hash in the retained qualification record.

These protected blobs were verified on both the pre-cleanup and cleanup trees.

| Record | Original blob |
| --- | --- |
| Projects final preservation | `b6e67a3379b960c226068cb44cfd2b1a79191b70` |
| Works provisioning attempt | `471b02d8d9ffe2ce9af1f4e27a4b8c12a236e275` |
| Story 4-1 checksum inventory | `f739a64faffef67f41452ca8640a9d50a7645f08` |
| Story 3-7 approved-removals packet | `72ab7238b3b33bb6606897fca730bdde54a7c016` |
| Gate classification | `7e8501dd3b936e6b6ca697b9641740f111b99e3b` |
| Folders owner prerequisite | `9190e6757475b6906d922e01ffbbacf73e131bc5` |

Each direct parent holds the removed paths with their original modes and
blobs. Git tree comparison confirmed the reviewed deletion lists and the
original mode and object ID of every retained path. The SHA-256 values of the
NUL-delimited path manifests from
`git diff-tree -r --no-commit-id --no-renames --diff-filter=D --name-only -z <parent> <commit>`
are `b040c31793da9ab9bd000a8091d7127981d991f30818c1eacf3a0c6798d75e74` for
implementation artifacts and
`bc2831b9cbbb06e6a6c17711d1da4cb892020e30b6c37bc41d509f5a4bcd8e60` for
specification evidence. `git diff --check` passed for both deletion commits.

Independent review also checked all 179 removals by path, Git blob ID and
SHA-256 and verified the three restored records against the original tree.

### Verification Results

- The clean baseline repository-input run had 38 passes and one failure in
  `RepositoryInputsTests.test_tracked_active_repository_inputs_have_no_evidence_dependency`.
  The sole diagnostic was
  `tools/qualification/pre-adoption/eventstore/qualify-eventstore-snapshot-candidate.py:173: active input references evidence`.
  The [flagged script](../../../../tools/qualification/pre-adoption/eventstore/qualify-eventstore-snapshot-candidate.py#L173)
  records a historical source path in `qualificationSource.derivedFrom`.
  That source path was absent from the baseline and remains absent from the
  cleanup tree. The flagged script is blob
  `eb707ce0ecca6263a7801595f3b0abe280f52609` on both trees.
  Baseline log SHA-256
  `6de70c75c5f581f128782873b52195e8ebeab9bd695cfe52e1245dd70667a14d`.
- The clean replacement candidate run had the same sole failure and 38
  passes. The exact diagnostic and script blob matched the baseline.
  Candidate log SHA-256
  `978013c5fee42c0c6836510854b3b4a76b6030c5ceac1de84ffaab18f58c9033`.
- `test_check_evidence.py` passed all 8 tests at the replacement deletion tip.
  Log SHA-256 `94934a18bedabecccf7e61399882a7e8cd705548d7b8893301eb0d0bbb121e66`.
- The push-event evidence checker passed on the replacement deletion tip
  with the original pre-cleanup baseline. Log SHA-256
  `cb394d5a683b9e54b112566e7d1477cf61a94dcc3c0d856642b2b483e16fa74d`.
- Story 4-1's `sha256sum -c SHA256SUMS` verified all 16 retained files.

## Auto Run Result

Status: done

- Removed 19 raw outputs under implementation artifacts and 160 under
  specification evidence. The commit table identifies the deletion paths
  by root and direct parent. This story receipt is the sole added file.
- Review patched one medium issue in the removal selection, covering three
  finding rows. Seven findings about the initial review scope or receipt
  verification were rejected for code patching. The triage rows record the
  verification or documentation provided for each. No findings were deferred.
- Follow-up review recommendation is `false`. Patched entries by verdict
  were zero high, one medium and zero low.
- Git tree and parent checks, the Story 4-1 checksum check, all eight evidence
  unit tests, and the push-event checks passed. The final push-event check
  covers the committed receipt as the sole added or modified entry.
- Both repository-input suites reported the baseline EventStore failure.
  The identical diagnostic and blob satisfied this story's criterion for
  workflow review. All other repository-input tests passed on both trees.
