# Projects G-6 catalog acquisition proposal

The CiCd-owned action in `.github/actions/prepare-g6-catalog/` corrects the missing
catalog object reported by [Projects run 43881420098](https://github.com/Hexalith/Hexalith.Projects/actions/runs/43881420098).
It belongs before Conversations `prepare-build`, after the direct dependencies
have been initialized. The mapper remains unchanged and performs no acquisition.

The caller supplies the full Platform revision from its committed direct gitlink.
The helper requires that revision to match Platform HEAD and the staged outer
gitlink. It derives the catalog commit from that revision's Builds gitlink,
requires the canonical root Builds declaration and effective origin, and fetches
only a missing exact commit with `--no-recurse-submodules --no-tags --depth=1`.
It verifies the commit and regular catalog blob, reports the exact bytes/hash,
and compares HEAD, raw index bytes, entries, refs and gitlinks before and after,
including on fetch failure. Git runs with isolated environment/configuration;
transport overrides and symlinked dependency paths are rejected. Timed-out Git
process groups are terminated and waited for before preservation is checked.
The action retains JSON and prints only bounded failure diagnostics.

Run its behavioral qualification from this repository:

```bash
run-with-temp python3 -B tools/tests/test_prepare_g6_catalog.py
run-with-temp uv run --locked --script --python 3.12 tools/tests/test_prepare_g6_catalog.py
```

Tests use synthetic repositories and a local transport substitution only at the
fetch boundary. The separate real-source proof retained in Folders uses the
production helper and approved GitHub Builds origin without substitution. It
starts with a depth-one Builds checkout, proves the selected commit missing,
acquires it, compares exact catalog bytes, and checks unchanged HEAD/index,
gitlinks and refs plus an idempotent second invocation. These tests qualify
acquisition only; they do not execute the mapper, restore or runtime G-6.

## Reviewed integration

`docs/proposals/projects-g6-catalog.patch` is the retained reviewed owner proposal.
It adds the local action and inserts its invocation before the existing restore
step in Projects source `981ceef13a1abc88219925e73c51a23eb9ac50c2`. The revision is
derived at execution from Projects HEAD; the historical catalog commit is never
hardcoded. All existing dependency pins and product gates are preserved.

The supported writer, `tools/deliver.py:apply_module`, requires a valid accepted
`delivered/Hexalith.Projects` ref and applies an entire rendered perimeter.
Projects is absent from `setup/` and has no observed accepted ref. The generic CI
template has no G-6 preparation extension. `templates/perimeter.json.j2` owns the
whole workflows directory and enforces the Builds pin from `builds-version`
(currently `v6.0.6`); enabling that delivery would perform the separately planned
Projects adoption in CiCd Story 18 and change policy/pins beyond this correction.

## Closed pre-adoption delivery exception

The `projects-g6-catalog` dispatch choice in the existing `deliver.yml` is a
task-specific AD-6 exception for this source-preparation correction. It keeps
AD-7's existing main-only `deliver` job, `cicd-app` environment, `deliver`
concurrency group and pinned App action. It neither registers Projects nor
creates an accepted ref, resolves a Builds version, or applies a rendered
perimeter. The architecture document and Story 1.17 tracking are unchanged.

The closed manifest `docs/proposals/projects-g6-catalog.json` binds Projects base
`981ceef13a1abc88219925e73c51a23eb9ac50c2`, its entire tree, the reviewed patch
SHA256, every input/output path and blob, and complete output tree
`238d933a813d0453e950e1080175d74f12e82975`. The only output changes are
`.github/workflows/ci.yml`, `.github/actions/prepare-g6-catalog/action.yml` and
`.github/actions/prepare-g6-catalog/prepare.py`. The action bytes are reused
unchanged. Acquisition precedes Conversations prepare-build; the mapper stays
offline and fail-closed. All pins, product gates and other tree entries survive
byte for byte.

The manifest also binds `pre_push_gate`. Its production value is currently
`pending-owner-decision`: qualification fails at `verify source-bound pre-push
owner gate`, emits no plan and prevents token minting. Only an explicit owner
decision for this exact source/proposal/result may authorize
`reviewed-tree-owner-authorized` as the pre-adoption gate. This does not alter
the normal checker, adoption policy, or any module product gate. An unanswered
question is not authorization.

The secret-free validation job runs the acquisition, narrow delivery and existing
workflow behavioral suites, then constructs a plan from current exact CiCd main
and current Projects main in private bare Git repositories. That JSON output
binds qualification to the writer's source, manifest, patch, base and result
tree. Failed qualification, a missing plan or a non-main/non-dispatch invocation
prevents the narrow write job from running. Normal triggers and the default
`full` choice retain the existing delivery behavior.

The narrow write branch checks out the exact qualified CiCd source and mints
only Projects Contents/Workflows write. It skips normal selection, accepted-ref
and freshness tokens, module slots, report finalization and the normal artifact.
Only stdlib CiCd Python and bounded Git run with that token; no module code,
build, tests, dependency initialization or mapper runs there. Proposal application
uses a private bare object store and index, never a module working tree. The
controller rejects changed source, bytes, trees, missing blobs, symlinks,
unexpected modes or extra paths before writing. It rereads owner and module main,
makes one non-forced push, then rereads the actual main SHA/tree. Refusal or a
race is retained with the exact failed operation, without retry, force, rebase
or automatic reapplication. An exact delivered tree with the reviewed base as
its sole direct parent is an idempotent no-op.

The owner invocation, after publishing and qualifying the task-owned CiCd source
and satisfying the module pre-push prerequisite, is:

```bash
gh workflow run deliver.yml --repo Hexalith/Hexalith.CiCd --ref main \
  -f delivery=projects-g6-catalog
```

Dispatch through the existing scoped CiCd profile. If the App installation cannot
mint the Projects token, retain GitHub's failed mint step and the failed delivery
receipt; do not broaden credentials. Qualification and delivery retain separate
`projects-g6-qualification` and `projects-g6-delivery` JSON artifacts for 90 days.
Receipts identify the owner source, proposal binding, observed main, actual
delivered SHA/tree, push result and exact failed operation.

Local qualification is available with:

```bash
run-with-temp python3 -B tools/tests/test_deliver_g6_catalog.py
run-with-temp uv run --locked --script --python 3.12 tools/tests/test_deliver_g6_catalog.py
run-with-temp uv run --locked --script --python 3.12 tools/tests/test_delivery_workflow.py
```

These tests qualify the delivery mechanism; they do not establish actual delivery
or hosted acquisition/G-6 acceptance. The normal exact pinned Builds checker
remains a separate pre-push prerequisite. On the clean proposed pre-adoption
Projects source, `python3 references/Hexalith.Builds/check.py` currently exits 1
because `.github/hexalith-ci.json` is absent. Do not register/adopt Projects, add
configuration, suppress the checker or weaken a gate to bypass that refusal.
Retain the prerequisite failure for owner resolution before an actual module
write. After any authorized successful delivery, inspect Projects' exact three-path
diff and collect fresh CI/G-6 logs and artifacts tied to its delivered SHA.
Diagnose any subsequent hosted failure separately from catalog acquisition.
Publishing, A8 audit, deployment and v2 activation remain outside this correction.

Retained proof and full source identities are in Folders:
`_bmad-output/implementation-artifacts/evidence/story-1-17-g6-catalog-acquisition-2026-11-16/`.
The historical publication/audit/A8 work and Story 1.17 tracking are unchanged.
