# Projects catalog correction — delivered; downstream hosted failure retained

[CiCd owner run 43939511545](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/43939511545)
succeeded at exact owner source `2a1128e0106baed22999c4687d7d15e7639f22cf` after
the user completed the App repository-access grant. Its secret-free acquisition
(17), controller (28), and workflow (17) tests passed; production qualification
and the existing scoped Projects App-token mint succeeded. The same CiCd owner
mechanism made one successful non-forced push. No maintainer module push or
direct module-checkout workflow edit was used.

## Exact actual delivery

Projects commit [`146d0f7e9964c82da23d31b51e6ab62efdcfdda6`](https://github.com/Hexalith/Hexalith.Projects/commit/146d0f7e9964c82da23d31b51e6ab62efdcfdda6)
has sole parent `4511105bb1f00b8cf762097523de74acc828a001`. It changes exactly:

- `.github/workflows/ci.yml`: acquisition invocation before Conversations prepare-build.
- `.github/actions/prepare-g6-catalog/action.yml`: unchanged reviewed owner payload.
- `.github/actions/prepare-g6-catalog/prepare.py`: unchanged reviewed owner payload.

The complete corrected tree is `c5425f42f16a8fe328ae5ec9f7c3d3ad81bd0047`.
Patch SHA256 remains `3b4e5540391f585c778f21953f4b2a37be1a87aa9df9ae7e2b56b6e05cefb588`.
[Independent complete-tree proof](delivered-source-proof.json), executed with
`run-with-temp`, checks both untruncated hosted trees, every leaf entry, all
gitlinks and the sole parent. All other 25,100 existing leaf entries, every
dependency pin, unrelated workflow and existing gate are preserved. The mapper
is unchanged, offline and fail-closed. Projects remains absent from the full
CiCd registry and accepted delivery refs at the owner's final pre-push check.
No full adoption occurred.

## Fresh exact-source hosted result

[Projects CI 43940159468](https://github.com/Hexalith/Hexalith.Projects/actions/runs/43940159468)
is a fresh push run bound to the delivered SHA. It failed at the existing
`Validate shared skill renderer` step:

`python3 -m unittest tests/tools/test_render_skill.py -v`

The unchanged source blob `b539b15c99f38b05e445b9a161ef35ffede9e4ec` has
`@dataclass(frozen=True)` at line 26 decorating the `_write_text` function at
line 29. Import fails with `AttributeError: 'function' object has no attribute
'__mro__'` before tests execute. This blob is identical in the reviewed parent
and delivered source. G-6 job `133555960523` is **skipped** because its existing
`needs: workflow-gates` dependency failed. Neither acquisition nor prepare-build
nor runtime qualification ran in Projects; CI produced zero artifacts. No
fresh catalog acquisition artifact or G-6 runtime acceptance is claimed.

[Commitlint 43940159230](https://github.com/Hexalith/Hexalith.Projects/actions/runs/43940159230)
also failed, at `Install dependencies`, before inspecting the message:
`npm ci --ignore-scripts` exits 1 with EUSAGE because Projects has no
`package-lock.json` or `npm-shrinkwrap.json`. Both files, and `package.json`,
are absent before and after delivery. Its unchanged caller resolves Builds
`commitlint.yml@main` to exact source `6db97d4e9da392ef691ed3f367e73f1b7d2ef318`.
The caller, resolved shared workflow, exact fixture and both failed-job logs
are retained. These failures need separate owner corrections before a new
exact-source CI/G-6 run can establish runtime acceptance. This task did not
remove gates, restore concurrent files, add npm metadata, change pins, or rerun
the failed gates against unchanged source.

## Retained evidence and limits

[Final result](final-result.json) separates qualified implementation, successful
actual delivery and unsuccessful hosted acceptance. [Failure diagnosis](hosted-failure-diagnosis.json)
binds the precise commands, job IDs, unchanged source blobs and resolved shared
workflow revision. Owner qualification/delivery JSON archives and digest
receipts, completed CI metadata/steps, artifact inventory and raw masked job
logs are retained in this directory. `verify-delivered.py` provides the
independent read-only tree verification. No nested submodules were initialized.

Story 1.17 tracking, publication/audit/A8 work, deployment and v2 activation
remain outside this task. The narrow delivery implementation and diagnosis are
complete; the parent story still needs successful runtime evidence. No claim is
made that the skipped hosted acquisition or G-6 succeeded.
