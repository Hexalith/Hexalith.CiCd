# Hexalith.CiCd agent guidance

Hexalith.CiCd owns the module workflows, CI configuration, Dependabot
configuration, Builds gitlink and its `.gitmodules` section, delivered CI/CD
instruction blocks, and required Claude deny entries. Author that policy here
in [the canonical ownership template](templates/partials/ownership-block.txt.j2)
and [project-local deny template](templates/partials/deny-entries.json.j2).
Delivery and the shared Builds perimeter library preserve foreign instructions,
allow/deny entries, unrelated settings and other submodule sections. Do not edit
owned portions directly in module checkouts.

Keep module gates that check the product: compilation, tests, security and
dependency scans, commit format and package publishing. Keep module-specific
product checks as custom actions enabled through the setup registry. Delete
module gates that check CI itself, agent tooling, story evidence or workflow
YAML text, including repository tests that assert workflow YAML. Classify
unresolved gates against this rule during migration; the initial inventory is
in [gate classification](_bmad-output/specs/spec-cicd/gate-classification.md).
CiCd's own renderer and perimeter qualification verify the policy it produces.

Require successful `python3 references/Hexalith.Builds/check.py` before adopted
module pushes. Before adoption, consult the module's approved migration spec
and use only its explicitly approved preparation verification substitute, if
one exists, with all required exact-input checks. Missing adoption configuration
alone neither grants publication nor invalidates an existing scoped approval.
See [pre-adoption publication](docs/pre-adoption-publication.md). Without an
approved substitute, stop before pushing. Fix product failures; report pipeline
defects and permission refusals
without weakening audits or tests, adding skip markers or trailers, editing
owned portions, or switching credentials. Product branches start from freshly
fetched current `main`. GitHub permits PR Update branch to import changed
workflows with the restricted module credential. Do not use it to import owned
CI/CD changes; create a branch from current `main` and reapply only product
changes. Releases follow the central nightly process.

Launch Claude Code from the module root so the delivered project-local `Edit`
denies anchor at that root. Keep reads available and keep denies out of
machine-wide settings. File-level rules cannot distinguish owned JSON entries,
instruction blocks or `.gitmodules` sections; instructions and the shared guard
protect those portions. Preserve foreign content when changing policy.

# Disposable job workspaces

Use `run-with-temp COMMAND [ARGUMENT ...]` for ad hoc builds, tests, or
verification jobs that create disposable workspaces. It supplies a private
`TMPDIR` (also `TMP` and `TEMP`) and removes it when the command exits.

Create temporary repository copies, package feeds, and build outputs beneath
`$TMPDIR`; explicitly named `/tmp/...` paths bypass the wrapper. Save requested
results outside that directory; for a useful log, record its result and digest
as the Evidence section says. Wait for child work to finish before returning.
Commands with their own reliable scratch cleanup can keep it.

# Evidence

Git keeps decisions and identities, not raw output. A story record keeps the
decision, exact source revisions (commit, tree and blob ids), digests, and run
and artifact links. Raw logs, tree dumps, generated patches, packages, test
results and earlier attempts stay in the producing Actions run or under
`$TMPDIR`; record their digest and a one-line result instead. Code that tests
or procedures execute lives under `tools/`, never under `_bmad-output/`. Files
added under `_bmad-output/` stay under 256 KiB.
