# Story 12 isolated local resume — 2026-11-16

The authorized local preparation passes on the isolated resume base. AI.Tools
is **not adopted**, and story 12 remains **in progress and not accepted**.
The complete story and both frontmatter context files were loaded before work.
The frozen intent, original baseline and acceptance checkboxes are unchanged.

The isolated branch `story/12-migrate-ai-tools-resume` remains based at
`0f25d19ba712eee9aae59d118251b854bbffd120`, as authorized in `execution.md`.
Its held explicit `solution: none` registration and five generated files are
byte-identical to the earlier preparation. They need no runtime or product
change. The committed source already contains the approved AI.Tools-only AD-21
decisions, setup guidance and published preparation gitlink
`cfd1ebea92587cdea41b9aa2cff47358bf2f32f6`.

The older `resume-local-check.py` qualifies a historical shared source and
worktree. It is preserved as historical evidence. The new
`isolated-resume-check.py` instead clones this isolated worktree's committed
HEAD and copies only its six held registration additions. It clones the local
Builds object source without recursive submodules, checks out exact released
`v6.0.6` at `fdda17c0a4538b0f7c99f813c20ca24b49006530`, and uses those released
bytes for message validation and contract checks. Dirty source worktree files
are excluded. It does not initialize Builds in this persistent worktree.

`isolated-resume-check.json` records passing committed-input/render,
reproducibility, schema, caller-interface and direct-submodule checks, exact
message validation, six-additions-only preservation, and the no-solution empty
inventory. It also confirms the clean standalone product head, its published
gitlink using committed historical publication evidence, retired package/lock,
and exact unchanged legacy commitlint blob/mode. The existing updated renderer
and validator suites pass **35 and 52 tests**; their output is saved in
`isolated-resume-render.txt` and `isolated-resume-validate.txt`. These suites
were rerun because their sources and the renderer/validator changed since the
previous qualification. No new module test or workflow assertion was added.

The disposable candidate is `092e1c59a0d06234d3ac29c39a5d31e8fa43427a`, tree
`27a8d6c9dd18cbb3befcdc8ac335bbcf6ac24ce3`. It is an offline qualification
object, not an integrated or published adoption commit. The command was:

```bash
run-with-temp bash -c 'uv export --locked --script tools/render.py --format requirements-txt --no-header > "$TMPDIR/validation.requirements.txt" && uv run --no-project --with-requirements "$TMPDIR/validation.requirements.txt" python3 _bmad-output/specs/spec-cicd/evidence/12/isolated-resume-check.py'
```

The wrapped job and all child work finished successfully; scratch was removed.
At its start, local `main` still named
`0f25d19ba712eee9aae59d118251b854bbffd120`, while shared local
`origin/main` named `2a1128e0106baed22999c4687d7d15e7639f22cf`. These are local
ref observations, not fresh remote readbacks. This run does not integrate that
concurrent source. Fresh-main integration and renewed qualification remain
required before any publication.

No fetch, push, repository administration, App selection, dispatch, credential
change or nested submodule initialization occurred. Locked verification-tool
acquisition was permitted by `execution.md`. The original story worktree,
unrelated shared-checkout content and existing story 11 observer were untouched.
After checking the staged session diff, the parent mirrored only this story's
specification and resume evidence to the shared checkout for visibility, using
content guards against overwriting concurrent changes. Registration stays held
in the isolated worktree. The full historical-baseline diff also includes
unrelated committed work; full-story review remains pending live acceptance.

Story 11's genuine `2026-11-17T02:17:00Z` night and subsequent acceptance remain
prerequisites. Then the authorized live phase must refresh main and the
acceptable Builds release, complete ordered AD-21 preconditions, commit cause
and render together, obtain the full committed/global/live validator verdict,
authenticate App adoption and owned/foreign trees, enable immutable releases
and retire applicable legacy access, and establish green CI, the standalone
normal checker and the next genuine module release/scan/delivery outcome.
This offline proof establishes none of those live acceptance results.
