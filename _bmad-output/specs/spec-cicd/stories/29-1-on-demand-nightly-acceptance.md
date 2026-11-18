---
title: 'On-demand nightly acceptance'
type: 'feature'
created: '2026-11-18'
status: 'done'
baseline_commit: '0b873999bc34f527a055a915328bde4b5d7d1428'
route: 'dispatch'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Story acceptance waits for a `schedule` event of `nightly.yml`, which arrives 7–9 h late, and one module's red row spoils every other module's acceptance (N1, N5). Each night also needs a new executable authenticator under `evidence/` (N6).

**Approach:** A read-only stdlib tool authenticates one completed `nightly.yml` run on `main`, scheduled or dispatched, plus its artifacts and linked release runs. It prints each selected module's verdict from that module's own rows (D2). Story 11 can add a pilot checkpoint.

**Acceptance criteria** (sprint change proposal 2026-11-18 on-demand nightly, §4.1, story 29-1, approved 2026-11-18):

1. `python3 tools/nightly_acceptance.py --run <id> --module <Repo> [--module …] [--checkpoint pilot] [--receipt <path>]` reads only through the caller's `gh` profile and writes nothing remote.
2. It accepts only a completed `nightly.yml` run on `main` whose event is `schedule` or `workflow_dispatch` and whose `dispatch` job ran, which proves `qualify-bump` was false. It rejects qualify-bump runs, other workflows or branches, unfinished runs, and any artifact whose downloaded bytes do not match its API digest.
3. Each module's verdict follows D2. The scan row comes from the run's `scan` job, or, after 28-7, from the first completed `scan.yml` run on `main` whose row for that module covers the dispatched head. A module with CodeQL languages in its committed setup fails when no Release CodeQL job succeeded.
4. Other modules' rows, Builds' row and the run's overall conclusion are reported and never change a module's verdict.
5. `--checkpoint pilot` also requires the bump report to be `no-change`, or a pushed candidate with a green `delivery-wait`, and `keepalive` to pass.
6. The JSON verdict goes to stdout. `--receipt` writes at most 16 KiB of identities only: run id, attempt, event and head; artifact ids and digests; per-module verdicts and reasons. It writes no logs.
7. Fixture tests cover: schedule and dispatch accepted; qualify-bump, non-main, other-workflow, in-progress and digest-mismatch runs rejected; `published` and `nothing` pass; `disabled`, failed, and `ready` not published by this run fail; a failed or skipped CodeQL job fails; a module's own scan error fails it, while another module's scan error or release failure leaves it passing; the pilot checkpoint fails on a failed bump (the 44264031228 shape).
8. `test_nightly_workflow.py` asserts that every job's selection is identical for `schedule` and for `workflow_dispatch` with `qualify-bump` false.
9. `docs/nightly.md` carries the proposal's §4.4 "Testing on demand" section.
10. Hosted: on 44264031228 the tool reports Commons and Poly pass and the four other targets fail. `--checkpoint pilot` fails, naming the `v6.3.0` bump.

## Boundaries & Constraints

**Always:** Every GitHub read is `gh api --method GET` in the caller's unchanged environment. Fail closed: missing, expired, malformed or mismatched evidence fails the module it belongs to, or rejects the run when it is run-level. Run suites with `run-with-temp`, keep scratch under `$TMPDIR`, record results, digests and run links in this file only, commit 29-1's paths with an explicit pathspec when green, and stop before pushing.

**Never:** Dispatch, rerun, mint, `gh auth token`, or set or clear `GH_TOKEN`/`GH_CONFIG_DIR`. Import or edit `evidence/11/authenticate-scheduled-20261118.py`. Change `nightly.yml`, the controllers, Builds or module templates. Stage another session's files.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Accepted run | completed `nightly.yml`, `main`, schedule or dispatch, `dispatch` job ran | judged | N/A |
| Rejected run | qualify-bump (`dispatch` skipped), other path or branch, not completed, artifact digest or size mismatch | no verdict, no receipt | stderr reason, exit 2 |
| Module pass | eligible, dispatched, `success` + `published`/`nothing`, or `ready` with `publication: published`; CodeQL and scan rows good; delivery green after a pushed bump | `pass` | N/A |
| Module fail | `disabled`, `failed`, unpublished `ready`, failed or skipped CodeQL for a declared language, own scan `fail`, scan revision ≠ `dispatchHead`, no delivery row after a pushed bump | `fail` with reasons | other modules unaffected |
| Pilot checkpoint | bump `failed` (44264031228) | checkpoint `fail` naming the tag and reason | exit 1 |

</frozen-after-approval>

## Code Map

- `_bmad-output/specs/spec-cicd/evidence/11/authenticate-scheduled-20261118.py` -- reference only: artifact ZIP digest and member checks :240-292, release run identity and CodeQL jobs :349-430, scan rows :466-486, blocking rules :603-617.
- `tools/nightly_runtime.py` -- values to mirror, not import: `DIGEST` :41, `ROW_KEYS`/`STATE_KEYS` :674-677, allowed row values :733-737. Its `artifact_member` allow-list rejects `report.json`/`bump.json`, so it does not fit.
- `tools/nightly_publish.py:142-149,153-177` -- publish-ready sets `publication: published` on a ready row it published; its `_verdict` passes `disabled`, which D2 fails.
- `tools/bump.py:52-138`, `tools/bump_push.py:70-102`, `tools/nightly_delivery_wait.py:139,444-457`, `tools/nightly_keepalive.py:38-39,94`, `tools/scan.py:252-316` -- schemas of `bump.json` (`no-change`/`candidate`/`failed`, `tag`, `reason`), `bump-push.json` (`pushed`/`failed`), delivery-wait `report.json` (module rows `repository, runId, conclusion`), `keepalive.json` (`result`) and scan `report.json` (rows `module, revision, result, errors`).
- `.github/workflows/nightly.yml` -- jobs `dispatch` :23 … `keepalive` :1823; artifacts `hexalith-nightly-<kind>-${{ github.run_attempt }}` uploaded at :589-1857. Unchanged.
- `rendered/<Repo>/.github/hexalith-ci.json` key `codeql` -- render of the setup's `codeql:` (`tools/render.py:607-610`); `[]` means none.
- `tools/tests/test_nightly_keepalive.py` -- suite style: PEP 723 header with `dependencies = []`, unittest, `delivery_support.load` :41-46, injected fakes. `tools/check_global.py:401-415` globs `test_*.py`, so there is nothing to register.
- `tools/tests/test_nightly_workflow.py` -- `Workflow.expression` :48-66, `PostReleaseWorkflow` :458-479, `job_condition` :600-624, existing trigger test :284-298.
- `docs/nightly.md` -- insert the new section before `## Builds bumps and rollback` (:140).

## Tasks & Acceptance

**Execution:**
- [x] `tools/nightly_acceptance.py` -- create the tool per Design Notes, with an injectable `GitHub` transport -- the one implementation the 15 stories call.
- [x] `tools/tests/test_nightly_acceptance.py` and `.lock` (`uv lock --script`) -- fixture suite for AC 7 and the I/O matrix, plus GET-only argv, the receipt's 16 KiB cap and identity-only keys, and the scan.yml fallback.
- [x] `tools/tests/test_nightly_workflow.py` -- add AC 8 (every job's `if:` evaluated under both events across the needs-output combinations `PostReleaseWorkflow` models), and a check that the tool's artifact names are those nightly.yml uploads (and `scan.yml`, when present).
- [x] `docs/nightly.md` -- add §4.4 verbatim as `## Testing on demand`.
- [x] this file -- record AC 10's hosted result: exit codes, verdicts, receipt sha256.

**Acceptance Criteria:** ACs 1–10 above. A change stays green only when both suites pass and AC 10 reproduces.

## Design Notes

- **Transport:** `subprocess.run(["gh", "api", "--method", "GET", endpoint])` with `env` unset. `json()` parses the output, and `blob()` returns the bytes from `actions/artifacts/<id>/zip`. A listing with `total_count` over 100 fails closed.
- **Run checks:** repo `Hexalith/Hexalith.CiCd`, `path == .github/workflows/nightly.yml`, `head_branch == main`, `status == completed`, and event in {schedule, workflow_dispatch}. In attempt `run_attempt`, the `dispatch` job has a conclusion other than `skipped`. Each used artifact is not expired, its `workflow_run.id` and `head_sha` match the run, and its bytes match `size_in_bytes` and `digest`. `nightly.json` has schema `hexalith.nightly.v1`, phase `nightly` and identity `{runId, attempt, source=head_sha}`. `bump.json` has a matching identity.
- **Module row (D2):** the release run (`repos/Hexalith/<M>/actions/runs/<runId>`) must match the row: path `row.workflow`, `workflow_dispatch`, `main`, `head_sha == dispatchHead`, `run_attempt == runAttempt`, and conclusion. CodeQL languages come from the rendered `hexalith-ci.json` at the row's `deliveredSha`, read through the contents API. Each declared language needs a `success` job matching `(… / )?Release CodeQL (<lang>)`, and any other Release CodeQL conclusion fails. When `bump-push.json` says `pushed`, M needs a delivery-wait row with `runId ≠ 0` and `conclusion == success`.
- **Scan source:** use the attempt's `scan` job artifact whenever that job exists. If it does not (after 28-7), use completed `scan.yml` runs on `main` created at or after the nightly's `created_at`, oldest first, one page. The first whose row for M has `revision == dispatchHead` decides. Both sources use the `hexalith-nightly-scan-<attempt>` artifact, so 28-7 must keep that name or update the constant.
- **Reporting:** non-selected targets are listed with their `nightly.json` `verdict`/`reason`, without re-authentication. Builds is listed the same way, and `--module Hexalith.Builds` is a usage error. Exit 0 when every selected module (and the checkpoint) passes, 1 when any fails, 2 for rejection, usage or transport errors.
- **Receipt:** `{schema: hexalith.nightly-acceptance-receipt.v1, run{id,attempt,event,head}, artifacts[{name,id,digest}], modules{M:{verdict,reasons}}, checkpoint}`. Each reason is capped at 200 characters. If the receipt would exceed 16 KiB, exit 2 without writing it.

## Verification

**Commands:**
- `run-with-temp uv run --locked --script --python 3.12 tools/tests/test_nightly_acceptance.py` -- expected: OK
- `run-with-temp uv run --locked --script --python 3.12 tools/tests/test_nightly_workflow.py` -- expected: OK
- `python3 -I tools/nightly_acceptance.py --run 44264031228 --module Hexalith.Commons --module Hexalith.PolymorphicSerializations` -- expected: exit 0, both pass, and AI.Tools, Conversations, McpCli and Builds listed as `fail`
- the same with `--checkpoint pilot --receipt "$TMPDIR/r.json"` -- expected: exit 1, the reason names `v6.3.0`, and the receipt is ≤ 16 KiB

## Implementation Notes

- New: `tools/nightly_acceptance.py` (stdlib, `python3 -I`, no import of the runtime or of the story 11 authenticator), `tools/tests/test_nightly_acceptance.py` and its `uv lock --script` lock. Changed: `tools/tests/test_nightly_workflow.py` (new `OnDemandNightlyTests` class only) and `docs/nightly.md` (new section). `nightly.yml` (blob `03e4599a0409d86ea10733cbd2bb17ea02a68391`), the controllers, Builds and the templates are unchanged.
- **Failure classes.** Exit 2, with no stdout and no receipt: the run's identity, its `dispatch` job, its jobs or artifacts listing (missing, over 100, or incomplete), a missing, non-JSON or malformed `nightly.json`, and any listed artifact the tool reads that fails authentication: expired, bound to another run or head, size or digest mismatch, or unexpected ZIP members. This includes the bump, keepalive and `scan.yml` artifacts, per AC 2. A gh failure other than 404 is also exit 2. Module-owned evidence (nightly row, release run, release jobs, rendered config, scan row, delivery row) that is missing, a gh 404, non-JSON or malformed fails only that module. The checkpoint's evidence (bump report, keepalive) fails only the checkpoint.
- **CodeQL languages.** `deliveredSha` is the CiCd `delivered/<M>` commit (`tools/delivery_runtime.py:402-417`). The tool therefore reads `rendered/<M>/.github/hexalith-ci.json` from Hexalith.CiCd at that commit and checks the response's git blob id and size. With `codeql: []`, Release CodeQL jobs are reported but not judged (D2). For example, AI.Tools' release has a skipped `Release CodeQL (${{ matrix.language }})` placeholder.
- **Additional fail-closed checks.** These go beyond the Design Notes' list, and each holds on 44264031228. The release outcome's `sha` must equal `dispatchHead`. The scan report's `controllerRevision` must equal its producing run's head. A report-level scan error, such as the detector failing to start, or a cross-module finding that names M fails M, because otherwise a row can say `pass` when the detector never ran.
- **Push and delivery.** A module needs a delivery-wait row only when `bump-push.json` says `pushed` with this run's bump identity and a candidate. The delivery-wait report must carry this attempt's identity and that candidate. If `bump-push` ran but its report is missing or malformed, the tool cannot tell whether a push happened, so every selected module fails.
- **Bump identity.** The bump identity is checked only for the checkpoint, because the bump never decides a module. A `failed` report without an identity is accepted as `failed`, since the producer's early-failure paths (`tools/bump.py:136-139`) and the workflow seed omit it.
- **Command line.** A duplicate `--module` is judged once. A module outside the run's registry fails. `Hexalith.Builds`, in any case, is a usage error.
- **Receipt.** The receipt is built after the verdict and written atomically before stdout. It is never written for a rejected run, and if it would exceed 16 KiB the tool exits 2 without writing it.
- **Docs.** The `docs/nightly.md` section sits before `## Builds bumps and rollback`, as the Code Map says. That is also "after the opening section", as the proposal says. Its text equals §4.4 with whitespace normalized.
- **AC 8.** The test harvests the needs outputs of nine `PostReleaseWorkflow` executions: four producers, two push failures, failed propagation, failed publication with a failed scan, and qualification. For every job it then evaluates `if:` with GitHub's job status semantics, under `schedule` (no inputs) and under `workflow_dispatch` with `qualify-bump: false`. The cases span every result × output combination of the needs the condition can observe, cancelled or not, on `main` or another ref: 15,796 situations, 0 differences. A sensitivity test adds `github.event_name == 'schedule'` to `dispatch`, `bump-push` or `keepalive` and sees exactly that job differ. A manual mutation to `inputs.qualify-bump == false` (null under schedule) is detected too. The artifact-name test executes the post-release model, then checks each `ARTIFACTS` entry's job, name and members against `nightly.yml`, and against `scan.yml` when that file exists.

### Verification record

Every run used `run-with-temp`, and its scratch was removed afterwards. Digests are SHA-256 of the combined output.

- **Inputs:** base `4bb7a2e163926d7794f2bbe3942b02a950a040e8`; `tools/nightly_acceptance.py` blob `ac21eafb36cd92fe2311b5a14034eea718a3885e`; `tools/tests/test_nightly_acceptance.py` blob `0d9764e284cf1caca61d180db2965ba9a82176fa`; lock blob `7518fc90bf78b2b347b694f695c6e1ed120d523c`; `tools/tests/test_nightly_workflow.py` blob `a5ca9e77df62c1be42d1f6e9e624c324135be874` (before: `4815fe72e19eb51fb6c37c5c41bd6fe11ce4c351`); `docs/nightly.md` blob `c65f0d9d4904023898aa514328e84aef4623f499` (before: `24aa2d2360c235c1f80c8e031dc4410bd0c5540f`).
- **Suites:** `test_nightly_acceptance.py` passed: 37 tests OK, `b1837c8b540159ab7d2993b9dff536354ded4ac1bd7ff639ab4a007b4d4a1990`. `test_nightly_workflow.py` passed: 30 tests OK, 96 s, `59804ff0b894ebd8f5a3ee50ee0fdbc74c82841ce49736aac5d71d391529076e`. That is 27 before plus 3 new.
- **Mutations:** 34 single-edit mutations of the tool each made the acceptance suite fail. They covered the run checks, the artifact checks, every D2 rule, scan fallback ordering, the delivery and checkpoint rules, the reason and receipt caps, 404 mapping, and passing `env` to `gh`.
- **AC 10, hosted, read-only:** every read was `gh api --method GET` under the caller's unchanged `GH_CONFIG_DIR` (CiCd-agent profile). Run [44264031228](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/44264031228) (`workflow_dispatch`, attempt 1, head `81e10620d4b4442b741d5c4a7420d1c8eb33ff4c`, conclusion `failure`, nightly `fail`).
  - `--module Hexalith.Commons --module Hexalith.PolymorphicSerializations`: exit 0. Commons `pass` (release [44266704721](https://github.com/Hexalith/Hexalith.Commons/actions/runs/44266704721), published 3.0.1, Release CodeQL (csharp) success, scan row at `d551e5f3…`). Poly `pass` (release [44266726524](https://github.com/Hexalith/Hexalith.PolymorphicSerializations/actions/runs/44266726524), nothing, CodeQL success). AI.Tools, Builds, Conversations and McpCli listed as `fail`. Stdout `139b41c43a3f5f6984693315b15cb184d61d02b78679f247cd16576dca0a2e02`.
  - Same with `--checkpoint pilot --receipt "$TMPDIR/r.json"`: exit 1, modules still `pass`, checkpoint `fail`: "Builds bump to v6.3.0 failed: candidate efb17b0a7d00f8d7945932fa4e919bed3de5aa02 failed shared global checks for v6.3.0". Stdout `410f67c9d228be1939f8fce84443758922b8843aa11b038d756f7a483b5d13f3`. Receipt 1,326 bytes, `ce8ab158e53994ce0ba773b83f5b568fd51185dcadc7bba0a9592bbd0618c4b9`. It names artifacts nightly 14410984147, scan 14411942153, bump-report 14414051248 and keepalive 14413692096, each with its API digest.
  - All five modules judged: exit 1. Commons and Poly `pass`. AI.Tools `fail` (release failure). Conversations `fail` (release failure, Release CodeQL (csharp) failure, scan row at `b3155063…` ≠ `c13cede6…`, own discovery error). McpCli `fail` (release failure, own discovery error). Stdout `44d3e7b204d5feaaa5e4d6ce55b1711e18554b384437e32ce345114b85fb2c61`. `--module Hexalith.Builds`: exit 2, usage error.
  - Both AC 10 commands were reproduced byte-identically after the final tool edit.

## Spec Change Log

## Review Triage Log

Pass 1 (2026-11-18), layers: Blind Hunter (BH), Edge Case Hunter (EC), Verification Gap (VG). No intent_gap or bad_spec entries, so no loopback.

| # | Finding | Verdict | Evidence | Route |
|---|---|---|---|---|
| BH1 | A missing `bump-push` job reads as "not-run", so a pushed bump stops requiring delivery rows; jobs are keyed by display name | low | `push_state` returns `not-run` for `jobs.get("bump-push") is None`; nightly.yml always defines the job, so absence only follows a rename or a `name:`, which is fail-open | patch |
| BH2 | A non-JSON module API body exits 2 instead of failing that module, unlike the Implementation Notes | low | `GitHub.json` maps parse errors to `TransportError`; Design Notes classify transport errors as exit 2, so the code is as designed and only the notes overstate; the fix edits this spec | reject |
| BH3 | Receipt lacks `createdAt`, per-module release ids and the scan producer run | low | AC 6 lists the receipt fields and the tool writes exactly those; the digest-pinned nightly artifact id binds every row's `runId`/`dispatchHead`, and run and artifact ids resolve the rest; adding fields is a schema change | reject |
| BH4 | Release outcome and delivery rows are not re-authenticated against module artifacts or CI runs | false | `nightly.json` comes from the trusted publish-ready controller, which validated each `hexalith-release-outcome` (`tools/nightly.py:344-357`); the tool authenticates that artifact's digest and each linked run's identity, as D3 asks | reject |
| BH5 | scan.yml fallback does not pin the trigger event | low | `eligible()` checks path, branch and repository but not `event`; the nightly run check pins `schedule`/`workflow_dispatch`, and the one-line pin keeps a future PR-triggered scan.yml run out | patch |
| BH6 | scan.yml fallback fails a module on the first malformed run instead of skipping to the first covering run | medium | `ScanSource.problems` returns on any `scan_report_problems`; scan.yml's seeded report (`controllerRevision: ''`, nightly.yml:1456-1458 pattern) would then fail every module for that nightly, against Design Notes' "first whose row … decides" | patch |
| BH7 | AC 8 model does not follow GitHub's null-vs-false coercion; the notes' `== false` mutation claim is overstated | low | `lookup` gives `""` for missing inputs and Python `==` is strict; for every nightly.yml condition (`!= true`, `== true`) the model and GitHub agree, so it errs only toward false alarms; the fix edits this spec's notes | reject |
| BH8 | AC 8 compares only job-level `if:` | low | AC 8 scopes job selection; grep finds no `github.event`/`event_name` anywhere in nightly.yml, and step conditions read only `inputs.qualify-bump`/`steps.*`; extending to steps is new machinery | reject |
| BH9 | AC 8 coverage floor `> 500` is far below the 15,796 evaluated | low | A shrinking harvest stays green; asserting that every job is evaluated is a direct correction | patch |
| BH10 | Rejection branches have no tests (ZIP members, unreadable ZIP, duplicate artifact name, registry/targets order) | medium | grep of `test_nightly_acceptance.py` finds none of these cases; a mutation removing them survives | patch |
| BH11 | Mirrored constants and schema strings have no drift check | medium | same root cause as VG2 | patch (VG2) |
| BH12 | `ENDPOINT` accepts `..` segments | false | every interpolated value is an int, a 40-hex SHA, a quoted path or a `Hexalith.`-prefixed name, so no caller can form a `..` segment; reads are GET only | reject |
| BH13 | Only the latest attempt can be judged; partial reruns give a misleading rejection | low | true, but it is fail-closed (exit 2); on-demand testing dispatches, never reruns (D1), and an `--attempt` option adds surface | reject |
| BH14 | API version not pinned | false | an unpinned version can only drop or rename fields, which the exact checks turn into rejection or module failure, never a wrong pass; today's responses carry every field (AC 10 reproduces) | reject |
| BH15 | Doc section omits `--receipt`, exit codes and `-I` | low | §4.4 says "Record the receipt" without the flag; one following sentence keeps §4.4 verbatim (AC 9) | patch |
| BH16 | Story record names two bases (`0b873999` frontmatter, `4bb7a2e1` record) | low | both are true (workflow baseline vs implementation parent after 28-1's commit); the fix edits this spec | reject |
| BH17 | `write_receipt` leaves `<name>.writing` on failure; no fsync; receipt written before stdout | low | `os.replace` onto a directory leaves the temporary file; the cleanup is a direct correction (patch). fsync and print ordering are negligible and rejected | patch (cleanup only) |
| VG1 | AC 8 does not vary `github.event`, so `!github.event.schedule` goes undetected | medium | pre-verified: 0 differences over 15,796 situations with that mutation | patch |
| VG2 | Mirrored `ROW_KEYS`/`STATE_KEYS`/`DIGEST`/schema strings never checked against producers | medium | pre-verified: fixtures hard-code the same literals; a producer change passes the suite and fails every real run | patch |
| VG3 | Scan artifact members are checked against the workflow model, not `tools/scan.py` | low | pre-verified: `test_scan.py` never asserts the output directory's file set; the tool rejects any extra member | patch |
| VG4 | AC 8 null-vs-false note overstated | low | same as BH7 | reject |
| EC1 | A corrupt deflate stream raises `zlib.error`, which escapes as "internal error" | low | `zlib.error` is not in the caught tuple; exit 2 either way, the message misleads; adding it is direct | patch |
| EC2 | `codeql: []` ignores a failed Release CodeQL job | false | D2 exempts modules that declare no languages ("unless M declares no CodeQL languages"); a failed CodeQL job also fails the release run itself | reject |
| EC3 | A `bump-push.json` result of `unknown` raises `KeyError`; `not-run` is fail-open | low | `push_state` returns `{"state": result}` for any non-`pushed` string; restricting to `failed` is direct | patch |
| EC4 | The publish-ready seed (`registry: []`, Builds row, errors) fails modules as "not a target" | low | confirmed at nightly.yml:898-901: `validate_nightly` accepts it; rejecting the seed with its error is direct | patch |
| EC5 | A non-JSON scan.yml report skips the receipt, re-downloads per module and loses the producer run | low | `report()` raises before `used.extend` and before caching | patch |
| EC6 | Partial rerun misleads | low | same as BH13 | reject |
| EC7 | A `--module` differing only by case fails as "not a target" | low | fail-closed with a visible reason; a typo the user corrects; fix adds a branch | reject |
| EC8 | `.writing` leftover | low | same as BH17 | patch (BH17) |
| EC9 | The artifact test fails once 28-7 moves the scan job to scan.yml | low | the subtest requires nightly.yml's scan job; checking scan.yml when that job is gone is a direct correction | patch |
| EC10 | scan.yml fallback fails on the first malformed run | medium | same as BH6 | patch (BH6) |
| EC11 | Another module's malformed scan or delivery row fails the selected module | false | a structurally invalid report is integrity failure, not another module's result; `scan.py` and `nightly_delivery_wait.finalize` always write dict rows, so this is unreachable fail-closed behavior | reject |
| EC12 | Receipt failure suppresses the stdout verdict | low | consistent with the recorded exit-2 contract (no stdout, no receipt); 16 KiB is never approached (1,326 bytes); changing it alters the contract | reject |

Pass 1 patches applied by the step-03 implementation agent (no defers). Re-verified under `run-with-temp`:
- **Blobs:** `tools/nightly_acceptance.py` `afa017ecb81c78fd3bb6437c72c69fdcb0be57f7`, `tools/tests/test_nightly_acceptance.py` `39debec45661aaea8d6349eb903476c05dd3bc14`, `tools/tests/test_nightly_workflow.py` `8c99d61e95aa6da4634f90b9dd54a23ffae8dedd`, `tools/tests/test_scan.py` `e1e6f5e42ae343e8589dc6bbf3c75d4e30706d02`, `docs/nightly.md` `d0e354cf53cd3013756ba3254cb18e28bf978652`.
- **Suites:** `test_nightly_acceptance.py` 41 tests OK; `test_nightly_workflow.py` 30 tests OK (110 s); `test_scan.py` 131 tests OK (367 s).
- **AC 10, hosted:** both commands on [44264031228](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/44264031228) reproduce byte-identically: pilots-only stdout `139b41c43a3f5f6984693315b15cb184d61d02b78679f247cd16576dca0a2e02` (exit 0), checkpoint stdout `410f67c9d228be1939f8fce84443758922b8843aa11b038d756f7a483b5d13f3` (exit 1, names `v6.3.0`), receipt 1,326 bytes `ce8ab158e53994ce0ba773b83f5b568fd51185dcadc7bba0a9592bbd0618c4b9`, no `.writing` file left.
