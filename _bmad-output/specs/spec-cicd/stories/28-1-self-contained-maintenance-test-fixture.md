---
title: 'Self-contained maintenance test fixture'
type: 'bugfix'
created: '2026-11-18'
status: 'done'
route: 'oneshot'
baseline_commit: '300cb754036739457693c980ddeb355cf679d0c4'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `tools/tests/test_maintenance.py` uses the enclosing checkout as the owner repository (`OWNER` = repository root, line 11), and `tools/maintenance.py:123` requires that checkout's `origin` remote. The nightly bump builds its scratch with `git init` and no remotes (`tools/bump.py:59`), so three tests errored in run [44264031228](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/44264031228) and blocked the v6.3.0 bump. The other refusal tests in that run passed only because every call refused on the missing owner origin, not for the reason each test names.

**Approach:** The suite builds its own owner repository and target clone in its temporary directory. It reads only blobs from the enclosing checkout's `HEAD` and objects from the Builds reference, so its result no longer depends on how the checkout was made. Every refusal in `tools/maintenance.py` stays unchanged.

**Acceptance criteria** (sprint change proposal 2026-11-18, §4.1, story 28-1, approved 2026-11-18):

1. Given any checkout of the candidate, when the suite runs, then it creates an owner repository in its temporary directory from the candidate's committed `tools/maintenance.py`, `policies/maintenance/story-2-8.json` and the templates that policy names, with `origin` set to `https://github.com/Hexalith/Hexalith.CiCd.git`, and it reads no remote, branch or config of the enclosing checkout.
2. Given an `actions/checkout` checkout, or a reproduced bump scratch (`git init`, no remotes), when `uv run --locked --script --python 3.12 tools/tests/test_maintenance.py` runs, then it passes.
3. Given a foreign owner or target origin, a changed executing tool, or a changed policy hash, when a render is attempted, then it refuses for that reason before any write.
4. Hosted: the next nightly bump does not fail in `test_maintenance.py`, and its run link is recorded here.

**Constraints:** Change the test fixture only; keep every refusal in `tools/maintenance.py` unchanged. Run suites with `run-with-temp` and keep all scratch under `$TMPDIR`. Record results, revisions and run links in this file only, with no logs, dumps or patches under `_bmad-output/`. Commit when green and stop before pushing.

</frozen-after-approval>

## Implementation Notes

- Changed only `tools/tests/test_maintenance.py`. `tools/maintenance.py` and every refusal in it are unchanged.
- **Owner:** `make_owner` commits the blobs from the candidate's `HEAD` (`tools/maintenance.py`, `policies/maintenance/story-2-8.json`, and the seven templates the policy names) into a new repository under the test's temporary directory. It uses plumbing (`hash-object`, `update-index --index-info`, `write-tree`, `commit-tree --no-gpg-sign`) with a fixed fixture identity, so it needs no hooks, filters or global Git identity. Its `origin` is the literal `https://github.com/Hexalith/Hexalith.CiCd.git`, not `tool.OWNER`, so a change to the tool's expected owner still fails the suite. The enclosing checkout supplies only `git cat-file blob HEAD:<path>`.
- **Executing tool:** the suite still loads the candidate's working-tree `tools/maintenance.py`. As before, an uncommitted edit to it fails the positive tests on the tool-digest refusal; it is never tested silently against older committed code.
- **Target:** `git init` plus an `objects/info/alternates` entry pointing at the Builds reference's object directory, then its own `origin` and `4.44.x` branch. This replaces `clone --shared`, so no Builds refs or remotes are read. It works for the submodule checkout and for the bump's bare, remote-less reference.
- Removed `MAINTENANCE_OWNER_ROOT`, which had no consumer. Kept `MAINTENANCE_BUILDS_SOURCE` so that a scratch copy of the candidate can run the suite against another Builds clone; the mutation checks below use it. Discovery stops at that directory (`GIT_CEILING_DIRECTORIES`), so an uninitialized Builds directory fails at setup instead of borrowing the candidate's objects.
- **Hermetic Git:** the suite removes Git's repository-local variables (`git rev-parse --local-env-vars`, for example `GIT_DIR` and `GIT_INDEX_FILE` exported to hooks) before its first Git call, so neither the fixture nor the tool can write to another repository. Both `git init` calls pin `--object-format=sha1`, which matches the Builds objects and the tool's 40-hex revision rule.
- **Committed inputs only:** the policy and templates come from `HEAD`. An uncommitted edit under `policies/maintenance/` is therefore not tested until it is committed, as before this story; Actions and the bump always test committed content.
- **Refusals are now specific:** each refusal test asserts its reason, and that the target workflows, the index and the output directory are unchanged. Surprise: in run 44264031228, three tests errored: `test_exact_named_branch_applies_only_committed_owned_templates`, `test_detached_render_is_labelled_and_cannot_apply` and `test_unrelated_dirty_content_is_preserved`. Eleven of the other twelve `refused_without_overwrite` tests passed only because the missing owner `origin` refused every call. The exception was `test_foreign_owner_origin_refuses_before_any_write`, whose clone of the enclosing checkout received a foreign `origin` and so refused for its own reason.
- **New tests:** a changed executing tool, and a changed policy hash (changed template bytes, and a changed recorded `sha256`). The positive test now also checks `ownerPolicySha256`, and that each owned maintenance file equals its committed template. The two `production_branch` tests, which use only a mocked API, moved to their own `ProductionEnvironmentTests` class, and the reviewer refusal now asserts its reason. `execute()` takes the `(directory, revision)` pair from `make_owner`, so an owner cannot be paired with another owner's revision.
- The acceptance criteria come from `_bmad-output/planning-artifacts/sprint-change-proposal-2026-11-18.md`, §4.1 (not the on-demand nightly proposal of the same date).


### Verification record

Every run used `run-with-temp`, and its scratch was removed afterwards. Digests are SHA-256 of the combined suite output.

- **Inputs:** test `tools/tests/test_maintenance.py` blob `c275ff7baf0cc0c80e601ea4da3faa52bce68458` (before: `05b32b9d28521bdc8b251a8e5f67638ba25966e1`); `tools/maintenance.py` blob `8f4facc88f29fa6bc58d04ef48b91eec4bf77a84` (unchanged); policy blob `8dc84256f01eda7c5794d1577764fd2b47dc47cf` (unchanged); Builds base `3c8096180ecf2aa539ac454815efbfceb8a92822`. The reproductions ran on candidate tree `4193ffc65bd75e88945b77d4f4f0d2e94eb5f024`, which carries these blobs.
- **Local:** `uv run --locked --script --python 3.12 tools/tests/test_maintenance.py` passed: 19 tests OK, `886d77f86230785f17b70ca3cf2c32a1cfef4319fb496bf36a7a6e078c1f16da`.
- **AC2, bump scratch:** a reproduction of `tools/bump.py` `produce()` used `git init` CiCd with the candidate detached, and a bare `git init` Builds reference with `origin/main` and every tag fetched. `git remote` was empty in both. Before the change it failed with 17 tests, `errors=3`, the same three tests as hosted (`7f6aeb3ae899fb42d5c41c5325a6f6df3f150536f2356dabb772dd0c5324fd30`). After the change it passed: 19 tests OK, `aa495d6eddd4196b7c99683df6106edd95645bde7fe6ece908219bc9de39b290`.
- **AC2, `actions/checkout` shape:** a depth-1 candidate with `origin` `https://github.com/Hexalith/Hexalith.CiCd`, and full Builds history with tags. It passed: 19 tests OK, `7f3a3c01a9af73a3b211ce61afc029c992c6b3b5dc1b491909f958ef79adec37`. Hosted: the `validate` job passed on `0b873999bc34f527a055a915328bde4b5d7d1428` in Delivery run [44286492932](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/44286492932/job/134740391892). The run's `deliver` job failed separately, with GitHub API HTTP 403 on the Builds `v6.2.0` tag and release lookups in the McpCli and PolymorphicSerializations slots. That is outside this suite.
- **Enclosing origin:** the depth-1 checkout also passed with its `origin` set to a foreign fork (19 tests OK), so the enclosing checkout's remote does not select the owner.
- **AC3, mutations:** each mutation replaced one `raise` in a committed scratch copy of `tools/maintenance.py` with `pass`. Each made exactly its own tests fail. Origin: both foreign-origin tests. Tool digest: `test_changed_executing_tool_refuses_before_any_write`. Policy hash: `test_changed_policy_hash_refuses_before_any_write`.
- **Hermetic checks:** the suite passed with `GIT_DIR` set to a stand-in repository (its refs and config were unchanged), with `GIT_INDEX_FILE` set to a scratch path (nothing was written there), and with a global `init.defaultObjectFormat=sha256`. Pointed at an uninitialized directory, setup failed with "not a git repository".
- **AC4, hosted:** passed. The first nightly bump after the push was the scheduled run [44282863616](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/44282863616), whose 02:17 UTC cron GitHub started at 10:10 UTC. Its [bump job](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/44282863616/job/134745954419) succeeded on live-main base `0b873999bc34f527a055a915328bde4b5d7d1428`. `test_maintenance.py` ran 19 tests OK, including both new refusal tests, and `global tool suites: passed`. The report `bump.json` gave `result: candidate`, candidate `ebb3b3963924876ae26756d0fb24d3acbe6bd546`, tag `v6.3.1` (job log `41db9a0d0e3b896a52a8a956308806b6936b4f63ab96521877f17e9ab5869fc9`).
- **Outside this story:** `bump-push` then refused with "CiCd main advanced beyond captured candidate parent", because `4bb7a2e1` and `8e96dc76` landed on `main` during the bump. This is the push guard failing closed, so v6.3.1 is not pinned yet. The same run's `dispatch`, `publish-ready` and `scan` failures are release and scan outcomes owned by other stories.

## Review Triage Log

Blind Hunter, one pass:

- Global Git config breaks the suite. `init.defaultObjectFormat=sha256`: **medium**, introduced by the new `git init` calls; patched with `--object-format=sha1`. `insteadOf` and `core.autocrlf`: **medium**, real but older than this story (the same `get-url` and checkout ran before); deferred.
- Inherited `GIT_DIR`/`GIT_INDEX_FILE` redirect fixture writes: **medium**. The new `update-ref refs/heads/main` could move another repository's `main`. Patched by removing `--local-env-vars` at import; verified with a stand-in.
- An uninitialized Builds directory borrows the candidate's objects: **low**. It failed loudly, but with an unclear message, and contradicted the comment. Patched with a discovery ceiling.
- The reviewer refusal used a bare `assertRaises`: **low**; patched.
- The positive test checks one owned file: **low**. Patched to cover every owned maintenance file. Rejected: comparing the receipt on disk with the return value, and an output-only-receipt check, which would add assertions no failure mode needs.
- New refusal tests run only in apply mode: **false**. The digest and hash refusals (`tools/maintenance.py:128`, `:150`) run before any code that depends on the mode.
- Untested render refusals: **medium**, a coverage gap older than this story and outside its criteria; deferred.
- Uncommitted policy or template edits are ignored: **low**; behaviour unchanged. Documented in the notes.
- `execute()` can pair an owner with another owner's revision: **low**; patched by passing the pair.
- The `production_branch` tests depend on the Git fixture: **low**; patched with a separate class.
- No Verification section: **medium**; patched (above).
- The proposal path is ambiguous and `baseline_commit` is missing: **low**. The path was added in the notes, since the frozen block stays unchanged, and `baseline_commit` was added.
- The account of the failing run is unverifiable: **low**; the notes now name the three errors and the one exception.
- `MAINTENANCE_BUILDS_SOURCE` was kept without a reason: **low**. The reason is now documented, and the ceiling check covers it.
