# Push to main: required policy refusal

This attempt created no commits and performed no pushes. It refreshed the root
and every declared module main, captured complete staged/unstaged/untracked
module changes using private indexes, and reapplied them to fresh-main copies
under `run-with-temp`.

Immutable Builds **v6.2.0**, commit
`0ccd12af6576a3aac601340dec7dba53e86768c3`, supplied the policy code and locked
tools. Its release was authenticated; locked installation, tool signatures,
exact proposed commit messages, owned-tree preservation and action lint passed.
Folders' captured candidate also passed released audit lint.

Platform's released audit failed on the existing committed artifact:
`_bmad-output/implementation-artifacts/evidence/3-2/release-adoption-20261109/shared-restore-import-closure/graph-export-imports.xml`.
It reports forbidden `MSBuildWarningsAsMessages`, `NuGetAuditSuppress` and
`VSTestTestCaseFilter` declarations. The artifact was not changed by this fix.
No audit, test, owned file or credential was changed to bypass that result.

During verification, another session advanced the shared module checkouts and
published their fixture changes. Authenticated remote-main reads confirm:

- Platform: `647c0dd0a18c995c12d2e23db532cf836fcc092a`; its complete tree equals
  this attempt's failed policy candidate.
- Folders: `438b8a0b9e3416669ac05152633301bc1bae76fb`; its tree differs from
  this attempt's earlier captured candidate, so that earlier pass is not claimed
  as exact qualification of the concurrently published tree.

The shared Git/publication rules stop this attempt before a parent commit after
a required module check fails. All concurrent changes were preserved. Full
product/publication acceptance remains unclaimed. All verification children
finished and private scratch was removed.

See [result.json](result.json), [candidate-policy.json](candidate-policy.json),
[release proof](released-policy-proof.json), and [runner](prepare-publication.py).
