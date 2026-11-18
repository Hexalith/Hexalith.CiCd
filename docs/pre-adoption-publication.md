# Verification before module preparation pushes

The normal Builds checker requires committed `.github/hexalith-ci.json` and
the matching Builds gitlink. Before adoption, a missing configuration is an
expected input limitation of that checker. It does not prove that preparation
cannot be published, and it never authorizes skipping verification.

## Select the applicable procedure

1. Fetch the target repository's current `origin main` under the intended
   profile and inspect divergence. Determine adoption from committed inputs
   and the recorded delivery state, rather than an untracked local config.
   If remote main adopted while preparation was pending, start from current
   main and reapply only product changes; the preparation exception has ended.
2. For an adopted module, require the normal checker on clean, exact committed
   inputs in a standalone module clone, with Builds as a direct dependency:
   `run-with-temp python3 references/Hexalith.Builds/check.py`.
3. For an unadopted module, read the frozen approved migration spec. Use a
   substitute only when the human explicitly approved it for that named module
   and the proposed preparation is within its scope. Otherwise stop and report
   the missing approval. An approval for another module is inapplicable.
4. Satisfy every obligation of that approval before publishing. Revalidate the
   fresh base, proposed tree and dependency revisions against the exact tested
   inputs immediately before the push. Changed inputs require fresh affected
   qualification. An approval is permission to use the procedure, not evidence
   that it passed.

The existing approvals for the three modules reported by the failed preflight
are independent:

| Module | Approved source of authority | Required preparation evidence |
| --- | --- | --- |
| Folders | [Story 17, Human decision](../_bmad-output/implementation-artifacts/spec-17-migrate-folders.md) | Released policy and exact commit checks, unchanged owned tree, complete package-mode Release build and retained tests/product hooks, with exact revisions and results. |
| Parties | [Story 21, Human decisions](../_bmad-output/implementation-artifacts/spec-21-migrate-parties.md) | Fresh-main standalone source, package-mode build and retained product tests, released audit/action lint, pinned exact-message commitlint and byte/mode/gitlink proof of unchanged owned portions. |
| Projects | [Story 18, Human decisions](../_bmad-output/implementation-artifacts/spec-18-migrate-projects.md) | Released commitlint/audit checks, unchanged owned-tree proof, complete Release/package build/tests and retained product-hook qualification, with source/results. This approval covers no Folders push. |

These approvals end at adoption. Consult the complete frozen spec for the
remaining boundaries; this table creates no new exception, widens none, and
does not authorize registration, adoption, credential cleanup or a release.
The normal checker and canonical delivered ownership policy remain unchanged.

## Bind qualification to the proposed source

Record the full base/head revisions, proposed tree, direct dependency gitlinks,
owned-content comparison, and all required product/policy results. Validate
every complete commit message in the actual fetched `origin/main..candidate`
push range with the owning repository's pinned policy, and retain the successful
results; checking only the final message is insufficient. Include pending
tracked and untracked changes when creating the candidate; preserve the shared
worktree and index. Create standalone copies under `run-with-temp`'s `TMPDIR`
and retain useful results outside it. Initialize no nested submodules in the
umbrella checkout.

Existing runners provide reusable checks, but several bind hardcoded historical
candidates and output paths. Inspect and adapt them in a disposable job before
using them for another candidate; retain the runner's exact source identity
and invocation, and write fresh results to a new evidence directory. Do not
overwrite old qualification or treat a stale pass as covering the current tree.

Run released policy checks from the committed bytes of an acceptable immutable
Builds release. Retain the exact tag and full commit identity, its authenticated
release proof, the pinned tool-lock identity and successful locked-tool setup
evidence. A runner hash alone does not identify the policy or tools it imports;
dirty or unreleased umbrella Builds sources cannot supply a released-policy pass.

| Module | Existing check implementations | Evidence boundary |
| --- | --- | --- |
| Folders | [Product qualification](../_bmad-output/specs/spec-cicd/evidence/17/verify-product-candidate.py), [final candidate checks](../_bmad-output/specs/spec-cicd/evidence/17/verify-final-candidate.py) | Historical qualification includes audit and retained-product failures. The saved candidate excludes later owner repair; it cannot qualify that repair unchanged. |
| Parties | [Publication qualification](../_bmad-output/specs/spec-cicd/evidence/21/publication/qualify-push.py), [accepted product evidence](../_bmad-output/specs/spec-cicd/evidence/21/accepted-local-verification.json) | That pass binds one preparation tree. Additional pending source or gitlink changes require new matching evidence. |
| Projects | [Package/product qualification](../_bmad-output/specs/spec-cicd/evidence/18/local-package-build.py), [owning G-6](../_bmad-output/specs/spec-cicd/evidence/18/qualify-owning-g6.py) | Full package/runtime checks remain required. The [Folders owner prerequisite](../_bmad-output/specs/spec-cicd/evidence/18/folder-owner-prerequisite.md) includes unexecuted component cases; local smoke results do not prove complete pre-push acceptance or remote owner availability. |

Keep failed, skipped, unrun or unavailable required checks visible. Fix product
failures; report pipeline defects and permission refusals under the existing
rules. Missing configuration must not be repaired by inventing adoption JSON,
retargeting the owned Builds pin, manually editing owned module content,
weakening audits/tests, adding skips, or switching credentials.

## Continue publication only after qualification

Once the applicable procedure passes for the exact fresh inputs, use the
already authorized publication scope and the intended repository profile.
Publish dependencies first. Before pushing a consuming module, authenticate that
each newly referenced dependency commit is available on its intended remote and
the ref required by the approved spec. Publish module content before committing
the parent gitlinks, and authenticate that each recorded module commit is
available remotely. A failed module check, push or remote verification stops
the superproject commit under the existing
Git instructions. Preparation publication never claims adoption, green hosted
CI or the nightly acceptance outcome (CAP-13).
