# Projects G-6 narrow owner delivery — 2026-11-16

**Latest outcome:** The gate decision is resolved and fresh hosted owner qualification passes. Actual delivery is blocked by HTTP 404 looking up the CiCd App installation for Projects. No module push occurred. See the [final authorized-resume handoff](authorized-resume-20261116T175933Z/README.md). The earlier status below is retained history.

The CiCd-owned extension is implemented and independently reviewed. It uses a dispatch-only branch inside the existing Delivery workflow/job, preserving the `cicd-app` environment, shared delivery concurrency, scoped App token and normal delivery behavior. It never adopts Projects or writes an accepted ref.

The exact proposal still targets Projects `981ceef13a1abc88219925e73c51a23eb9ac50c2`, base tree `b8a7a8b3b5532cb954f36835685d5b8dcd9577ab`. Its only changes are the existing acquisition action's two files and its invocation before Conversations prepare-build. The complete corrected tree is `238d933a813d0453e950e1080175d74f12e82975`; every other entry, mode, dependency pin and gitlink is preserved. [Independent proposal proof](proposal-qualification.json) includes exact blob bindings and the unchanged proposal SHA256. The acquisition helper, its tests, the proposal and the offline fail-closed mapper are unchanged.

[Controller tests](controller-final.log) pass 20 cases on locked Python 3.12. [Acquisition tests](acquisition-tests-python312.log) pass 17 cases on Python 3.12, with the same result on the local runtime. [Pinned lints](lint.json) pass actionlint 1.7.12 and online zizmor 1.32.0. The full [workflow regression](workflow-regressions-final.log) passes all 15 tests in 413.228 seconds; the earlier agent-local session lost its final status and is explicitly not treated as passed in [its retained log](workflow-regressions.log). Follow-up edge and verification reviewers confirmed all reproduced findings are fixed; none is deferred.

## Pre-push prerequisite and authorization

On a clean committed disposable copy of the exact proposed Projects tree, the mandatory command `python3 references/Hexalith.Builds/check.py` exits 1 because `.github/hexalith-ci.json` is absent. [stderr](pinned-check.stderr.log) and [command/source receipt](proposal-qualification.json) retain the failure. The checker comes from Projects' unchanged pinned Builds `fdda17c0a4538b0f7c99f813c20ca24b49006530`.

The shared Hexalith baseline requires that checker before every module push. Adding its adoption configuration would exceed this task. The production manifest therefore binds `pre_push_gate: pending-owner-decision`: qualification refuses at `verify source-bound pre-push owner gate`, emits no plan and prevents token minting. The pending decision is whether the reviewed-tree CiCd gate may replace the adoption-only checker for this exact three-file correction. An unanswered question is not authorization.

No module delivery, Projects push, fresh corrected Projects CI/G-6 run or hosted acceptance is claimed. Publishing the extension and qualifying its hosted refusal are separate from delivering the module correction. Current status and any remote run/commit identities will be recorded below.

## Preservation and review

[Initial state](before.json) and [final preservation](preservation-final.json) bind workspace HEADs, raw indices, staged entries and committed gitlinks. All three indices and all gitlinks remained unchanged. Ninety-two Folders tracking/story files are protected. Concurrent work in CiCd/Projects/Folders remains outside the task-only owner commit. No nested submodule, package publication, historical audit/A8, deployment, v2 activation or Story 1.17 tracking work was performed.

The implementation spec retains individual triage for all thirteen review findings and the follow-up confirmation. [Final diff](implementation-final.diff) covers only this task's source changes. Disposable qualification runs use `run-with-temp`, with receipts/logs retained here; no active child is abandoned at completion.

Final preservation also records four concurrent CiCd file changes and eleven concurrent Projects file changes observed during this task. Their exact before/after hashes are retained; task-only publication excludes them. All workspace HEADs, raw indices, staged entries, committed gitlinks and the ninety-two protected tracking files remain unchanged.

## Final delivery boundary

The eight task-owned CiCd files were published in [`b836159cea272e5211333296936106cf82833a27`](https://github.com/Hexalith/Hexalith.CiCd/commit/b836159cea272e5211333296936106cf82833a27), directly from parent `991f7beb9be0949831415cae95c81672a94907d8` through the configured CiCd-scoped profile. [Publication receipt](owner-publication.json) binds every committed source hash; no workspace index or branch was changed. The exact source passed all local checks.

The production qualification CLI was then run locally against that exact published main, using workflow-context values to exercise the same read-only controller. It exited 1 at `verify source-bound pre-push owner gate`: `pre-push gate is pending owner decision`. [Receipt](published-source-qualification.json) records no plan and no push attempt. This was a local exact-source probe, not a hosted dispatch. No App token was minted, no Projects fetch/write was attempted by that probe, and no corrected Projects CI/G-6 run exists.

The push triggered [owner Delivery run 43920301403](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/43920301403), observed in progress with no conclusion. This is CiCd validation, not Projects/G-6 acceptance. No manual narrow delivery dispatch was made while the explicit gate is pending. [Final result](result.json) keeps local qualification, owner publication, actual module delivery and hosted acceptance separate.
