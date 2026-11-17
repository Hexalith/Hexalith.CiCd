# Authorized publication to main

The user repeated `push all changes to main` immediately after the explicit
question about publishing despite failed audit/tests and incomplete required
qualification. This publication uses that confirmed exception. It does not
change enforcement or claim successful qualification, adoption or release.
Earlier blocked-publication receipts remain historical results of their runs.

- Platform: `647c0dd0a18c995c12d2e23db532cf836fcc092a` is verified on remote main.
  GitHub reported a bypass of the pull-request requirement for this direct push.
- Folders: `438b8a0b9e3416669ac05152633301bc1bae76fb` is verified on remote main
  and records that exact published Platform dependency.
- Every other root-declared module head was also authenticated as available
  on remote main. All 18 module worktrees were clean before the parent commit.

Both modules were advanced to freshly fetched main before committing product
changes. Owned portions were preserved. Exact complete messages passed the
pinned commit policy, including locked tool installation and signature checks.
No policy, audit, test, skip marker or credential restriction was weakened.

CiCd incorporates current remote main and preserves its incoming EventStore
gitlink. Its one merge conflict contained independently appended deferred-work
entries; all three were retained. Pending source contents were preserved, 90
Python sources parsed successfully, and source whitespace checks passed. The
full staged whitespace check reports 260 findings in retained patch artifacts
and a synthetic consumer fixture; those evidence bytes are preserved under the
confirmed publication exception. The earlier
Folders focused qualification includes 1,462 passing Server cases and eleven
passing source component cases; complete publication qualification remains
incomplete and is not replaced by those focused results.

See `authorization.md`, `commitlint.json`, `module-inputs.json`, the module
commit/publication records, `root-reconciliation.json` and
`published-module-gitlinks.json`. The parent commit records these outcomes and
the remaining authorized evidence/source changes. Its identity is available
from Git history; final push verification is retained outside this checkout.
