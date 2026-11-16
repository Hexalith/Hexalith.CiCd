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

## Integration and delivery blocker

`docs/proposals/projects-g6-catalog.patch` is an **unapplied owner proposal**.
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

An owner-supported delivery path for this pre-adoption source-preparation change
is therefore required. Do not apply the patch directly in a module checkout,
register Projects to bypass this gap, or edit delivered workflows with a different
credential. No delivery, push, dispatch or rerun was performed. Fresh corrected
exact-source hosted CI/G-6 remains blocked until that owner path is available.

Retained proof and full source identities are in Folders:
`_bmad-output/implementation-artifacts/evidence/story-1-17-g6-catalog-acquisition-2026-11-16/`.
The historical publication/audit/A8 work and Story 1.17 tracking are unchanged.
