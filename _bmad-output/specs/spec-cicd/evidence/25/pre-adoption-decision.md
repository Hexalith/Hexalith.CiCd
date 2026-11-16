# Timesheets preparation-push decision

## Approved resolution, 2026-11-16

The human selected the Timesheets-only pre-adoption procedure with **"approve"**
after the options, tradeoffs and recommendation were explained. This approves
the verification policy below; it does not claim that verification has run or
approve a broader bootstrap redesign.

The root CiCd `AGENTS.md` requires successful
`python3 references/Hexalith.Builds/check.py` before module pushes. Timesheets
needs product preparation before registration: remove tool-only manifests and
story/agent/CI evidence tests, and preserve its product checks as an enabled
custom action. AD-21 prohibits writing the owned configuration manually.

`pre-adoption-check.json` records the literal checker in a disposable standalone
clone with its real committed direct Builds pin. That pin contains the checker;
it exits 1 because `.github/hexalith-ci.json` is absent. This is not merely an
uninitialized-checkout problem. The checker also needs an accepted delivered
perimeter. Copying another checker, inventing a delivered ref, overlaying owned
configuration or retargeting Builds would not satisfy the current contract.

The approved pilot resolution in `evidence/11/pre-adoption-check-resolution.md`
explicitly excludes other modules. This separate decision covers Timesheets.

## Approved procedure, before adoption only

For every Timesheets product-preparation push:

1. Fetch current `origin/main`, start the product branch there, and record full
   canonical module/Builds/dependency revisions. Use a standalone disposable
   clone for direct dependencies; never initialize nested submodules in CiCd.
2. Require the exact candidate's Release/package-mode build, all six test
   projects and applicable package/consumer/product checks. Preserve the
   existing explicit live-Dapr/performance opt-ins; do not create new skips or
   infer runtime acceptance. Fix product failures. Pipeline defects remain
   blockers unless the human explicitly resolves their sequencing.
3. Validate Conventional Commit messages with pinned Builds commitlint. Prove
   bytes, modes and gitlinks of every owned portion unchanged from freshly
   fetched main, including partial instruction/settings/.gitmodules ownership.
4. Save the exact commands, input revisions, results and ownership comparison
   before the push. Push only with the module-agent identity; an unavailable
   credential or refusal remains a blocker.
5. After actual App adoption, require the ordinary successful
   `python3 references/Hexalith.Builds/check.py` before every product push.

This decision does not authorize owned edits, weaker audits/tests, bypassing
discovery, broader credentials or a post-adoption exception. It changes only
the pre-adoption verification requirement for this module.

The alternative bootstrap redesign was not selected. The approved procedure
does not remove package-compatibility, complete discovery, shared-support or
maintainer prerequisites. The human subsequently approved the overall migration
spec and requested stopping before implementation; the spec is ready for
development, with no implementation or validation claimed complete.
