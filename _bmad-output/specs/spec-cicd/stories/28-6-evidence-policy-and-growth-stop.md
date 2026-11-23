---
title: 'Evidence policy and growth stop'
type: 'feature'
created: '2026-11-23'
status: 'done'
baseline_revision: 'c1da22205bb9004f85908dddf6a953024126e44f'
review_loop_iteration: 0
followup_review_recommended: true
context: ["{project-root}/AGENTS.md"]
warnings: []
deferred:
  - summary: >-
      Delivery's shared concurrency group can replace a pending main push before its evidence check runs.
    evidence: |-
      The existing workflow-level group uses GitHub's single pending slot. If a later run replaces the pending push, that next push compares against its own previous SHA. A replay or concurrency redesign affects Delivery scheduling.
    location: >-
      .github/workflows/deliver.yml:20
    severity: medium
  - summary: >-
      Nightly's observers consume the aggregate Delivery run status and conclusion.
    evidence: |-
      An evidence-only failure can make an otherwise qualifying post-bump Delivery run red to the propagation observer. The pre-dispatch barrier also waits for the aggregate run to finish.
    location: >-
      tools/nightly_delivery_wait.py:331 and tools/nightly.py:205
    severity: medium
---

<intent-contract>

## Intent

**Problem.** Tracked raw evidence and executable artifacts have grown despite the evidence rule in `AGENTS.md`.

**Approach.** Add an independent `evidence` job to Delivery. Compare committed evidence paths to the PR event's base or the push's previous SHA. Keep one compact qualification receipt in the pre-adoption procedure.

## Boundaries & Constraints

- Evidence runs on pushes and PRs with a read-only checkout, no persisted credentials or environment secrets, and a failed job for policy violations. Delivery continues to consume its existing dependencies, verdict, tokens and accepted refs.
- Check added, modified, mode-changed and renamed-in paths. Permit exactly 256 KiB per the job threshold. Leave historical, unchanged paths and deletions alone. Reject executable Git modes and non-regular entries.
- Preserve Git history. Historical cleanup is subject to the separate 28-8 decision.

## I/O & Edge-Case Matrix

| Scenario | Input | Expected result |
| --- | --- | --- |
| Compact record | Small receipt, prose, or exactly 262,144 bytes | Pass |
| Raw or executable | `.log`, `.jsonl`, `.patch`, `.diff`, `.nupkg`, `.snupkg`, `.trx`, `.binlog`, `.zip`, `.gz`, `.tar`, `.py`, `.js`, `.mjs`, `.ps1`, `.sh`, or executable Git mode | Fail and report affected path and reason |
| Large entry | New or modified file of 262,145 bytes or more | Fail with byte count and limit |
| Non-regular entry | Symlink or gitlink | Fail with affected path and reason |
| Historical output | Unchanged file or deletion, regardless of old type or size | Pass |
| Missing baseline | Invalid or unreadable event comparison | Fail evidence job with a diagnostic. A push creating the ref uses the empty tree. |

</intent-contract>

## Code Map

- `.github/workflows/deliver.yml` defines the PR/push/schedule/dispatch triggers, the scoped validation outputs and delivery's sole `needs: validate`. Use its pinned checkout action.
- `tools/check_evidence.py` will use a shallow sparse checkout and Git metadata. Fetch the exact baseline shallowly when required and query sizes of changed blobs.
- `tools/tests/test_check_evidence.py` qualifies the entry point using fixture commits and a shallow transport. `tools/tests/test_delivery_workflow.py` covers job wiring. `tools/check_app_inventory.py` checks the privileged dependency closure.
- `AGENTS.md` already includes the approved Evidence section. `docs/pre-adoption-publication.md` already names one receipt and `$TMPDIR`. Clarify durable receipt contents while preserving exact-input and explicit EventStore report requirements.

## Tasks & Acceptance

**Execution**

- [x] `tools/check_evidence.py` and `.github/workflows/deliver.yml` implement and wire the standalone check.
- [x] `docs/pre-adoption-publication.md` clarify durable receipt contents and scratch output.
- [x] `tools/tests/test_check_evidence.py` and `tools/tests/test_delivery_workflow.py` exercise the matrix and event wiring. Verify App inventory and workflow lint.
- [x] This story records commit, tree and blob identities, local results and log digests. Measure the implementation's added evidence bytes separately and record a complete seven-day baseline under the proposal's blob-entry method.

**Acceptance Criteria**

- Given a PR or main push with a committed evidence change, when the job runs on the event checkout, then it evaluates only candidate changes against the exact event baseline, follows the matrix above and produces a red check for violations.
- Given an evidence failure or an event other than PR or push, when Delivery evaluates its jobs, then evidence has no dependency or module verdict input. The PR/push job needs no environment secret.
- Given a successful pre-adoption qualification, when recording the result, then the procedure retains one receipt with exact revisions, tree IDs, digests and outcomes, with raw output in `$TMPDIR`.
- Given two main snapshots seven days apart, when summing blobs per path under `_bmad-output/` using `git ls-tree -r -l`, then the receipt records net change against 5 MiB/week and the story's added evidence separately. Production target acceptance requires a full post-rollout week.

## Spec Change Log

## Review Triage Log

### 2026-11-23 — Review pass

- Verdicts: 15 findings, high 0, medium 11, low 4, false 0, maybe-false 0.
- Findings:
  - `[medium]` `[patch]` The oversized fixture had only one distinct blob. A smaller blob now precedes it, so processing only the first result fails the test.
  - `[medium]` `[defer]` GitHub can replace a pending main push in the existing concurrency group. A later event's baseline can contain the unexamined addition. [GitHub concurrency semantics](https://docs.github.com/en/actions/concepts/workflows-and-actions/concurrency)
  - `[medium]` `[reject]` A PR can change its checker. The approved check uses the ordinary PR workflow trust model, and enforcing owner-controlled source would require a separate trust boundary.
  - `[medium]` `[patch]` Missing blobs triggered individual fetches. The checker now asks for only missing changed blobs in one fetch and reads their sizes locally.
  - `[medium]` `[reject]` The reviewed receipt measured an earlier snapshot. This finding concerned the story record, whose final verification records the submitted byte count.
  - `[medium]` `[defer]` A scheduled run can replace a pending evidence push through the existing workflow concurrency group. Same cause as the pending-slot finding.
  - `[medium]` `[defer]` Nightly's existing observers read aggregate Delivery status. A qualifying red push can fail propagation observation even when its writer passes, and the barrier waits for all running jobs.
  - `[medium]` `[reject]` A PR changes the workflow and checker together. Owner-controlled enforcement requires a trust change outside the approved job.
  - `[medium]` `[patch]` Individual fetches can exceed the timeout and transfer oversize blobs. The batch removes repeated negotiation. Git still supplies changed blobs so their uncompressed sizes can be read.
  - `[low]` `[reject]` Small raw JSON and text dumps can pass the extension check. The approved job checks the enumerated suffixes and size. The full retention convention remains in AGENTS.md.
  - `[medium]` `[reject]` The earlier receipt did not bind the final checker and fixtures to one tree. The final story record binds the qualified source and reports the resulting evidence addition.
  - `[low]` `[reject]` AGENTS.md says “under,” while the approved job threshold says “over 256 KiB.” The exact-limit fixture follows the latter, and the maintainer's existing Evidence section is already landed.
  - `[low]` `[reject]` Other raw content can fit within the approved suffix and size rules. Determining which ordinary text or JSON is raw output is outside those rules.
  - `[low]` `[reject]` The local workflow harness and the real Git CLI fixtures cover different surfaces. Hosted rollout and its observation are recorded as pending.
  - `[medium]` `[reject]` The alignment review compared the 7,205-byte earlier figure to the submitted story. Finalization measures the submitted blob. It also records the pre-rollout counts confirmed by the reviewer.

## Verification

- Run the evidence and workflow fixture suites with `run-with-temp`, the App inventory suite, configured `actionlint`, and `git diff --check`.

### Local qualification receipt

The implementation baseline is commit
`c1da22205bb9004f85908dddf6a953024126e44f`, tree
`4603435dbf4d930fa7fbf55303db1bef8a8e6e22`. The clean disposable checkout
qualified the reviewed sources at commit `8023c9fdfb2a454cf143b1143403a3e64c495922`,
tree `dd7d6ae1092c0be5d3fd1a33f3144db4dae02f67`, with Builds gitlink
`2d9ef8b454ff897daca0149f3549844f584b634a`. This story record was added
after taking the source snapshot.

| Source path | Qualified Git blob ID |
| --- | --- |
| `AGENTS.md` | `1672e802cfddbdb5d2ebdec41ce07cd3e2177d23` |
| `.github/workflows/deliver.yml` | `13ea5674b9bd229c04dcbf34173fedb38f6cdb60` |
| `docs/pre-adoption-publication.md` | `9af0193759ac69a7ee059949afe0eb6a1bb8b6be` |
| `tools/check_evidence.py` | `1e46f644e544d912d5f5015e5fdbc036de073aab` |
| `tools/tests/test_check_evidence.py` | `596f232f2b3135c0953d371deacd06bf923bd762` |
| `tools/tests/test_delivery_workflow.py` | `48916e30d4e7c4f1ef4e6e5da7ea1db8e086e437` |

| Local check | Outcome | Output SHA-256 |
| --- | --- | --- |
| Evidence fixtures | 8 passed | `a6099e7db69f40a43eb63ce1901709ed116f48ebfe41cc2021888ed191dea4f9` |
| Delivery workflow fixtures | 26 passed | `c70ca36c1120a84644bc501fd8b69f9b84b7264449c47d02312beb05ca725590` |
| App inventory suite | 20 passed | `e6a51c6de54a5b62f51378cccce269ff2382ad96b41646017883396c17e96003` |
| Repository-input suite | 39 passed | `4c24703ec461391a2102791de63e326d5bb47064a954c1762293998bc6179d30` |
| Configured `actionlint` 1.7.12 | 7 workflows passed | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `git diff --check` | Passed | No diagnostics |

The checker also passed against public GitHub Git transport from a blobless
shallow checkout. The exact previous commit was
`d509d01f7fbc636075a82fa489d08bad0924cc94`, tree
`ed3abf611c682a6eec38f7886034dfc89c9aea32`. The candidate was
`0e3ab54ecf9958b6986296d361c53ca52bc68e44`, with its tree listed below.
The trace recorded two fetch requests after checkout, one for the baseline
and one for the two changed blobs. Output SHA-256
`43ae2c70853ae0b3fff1d92ecec1ff54d298adfe792863b943fa6df4e3ca00bb`.

### Seven-day evidence baseline

The pre-rollout window runs from `2026-11-16T12:49:56+01:00` through
`2026-11-23T12:49:56+01:00`. Each snapshot uses the latest first-parent
commit on the local `origin/main` record as of its cutoff. The sum uses
`git ls-tree -r -l` and counts each blob path under `_bmad-output/` once,
including separate paths that share a blob.

| Snapshot | Commit | Root tree | Blob paths | Bytes |
| --- | --- | --- | ---: | ---: |
| Start | `f002539f6fbaddaa9b621a9cbf75a1263eee5dea` | `a28e71688efb8758d10c4eb3ea7b886f53261700` | 295 | 10,493,514 |
| End | `0e3ab54ecf9958b6986296d361c53ca52bc68e44` | `9f43d465e72fb58b70fb1deb7038e1c4cddb7bc2` | 4,752 | 496,638,693 |

Net pre-rollout growth was **486,145,179 bytes** over seven days, above the
**5,242,880-byte (5 MiB)** weekly target. At the local implementation
baseline, 4,752 existing evidence blob paths total **496,652,598 bytes**.
This story record is the sole added evidence path and accounts for
**13,270 bytes**. The reviewed change brings the local total to
**496,665,868 bytes** across 4,753 paths. Hosted execution and a complete
post-rollout week remain pending.

## Auto Run Result

Status: done. The Delivery evidence job checks PR and main-push changes against
the exact event baseline and reports violations independently of Delivery's
module verdict and writer. The job uses read-only checkout with credentials
discarded before the checker runs. The existing Evidence section satisfies
the approved rule.

- `.github/workflows/deliver.yml` wires the event check as an independent job.
- `tools/check_evidence.py` enforces the approved suffix and size policy using
  committed Git objects.
- `docs/pre-adoption-publication.md` specifies the one durable receipt and
  where to keep raw results.
- `tools/tests/test_check_evidence.py` and `tools/tests/test_delivery_workflow.py`
  cover the CLI, Git transport, and workflow job wiring.
- This story retains the qualification and growth measurements.

The four review layers yielded 15 findings. Two medium entries were patched,
two issues were deferred, and the triage log gives the rejected findings and
their reasons. The post-review source passed 93 focused tests, configured
workflow lint, and the public Git transport check.

Follow-up review is recommended to observe the exact hosted PR checkout and
baseline and blob fetches together. Delivery's existing pending-slot behavior
can skip a superseded push. Nightly's propagation observer can see an aggregate
Delivery failure from an evidence-only red check even if the writer succeeds.
