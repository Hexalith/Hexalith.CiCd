---
title: 'Verify EventStore producer readiness for Projects query contracts'
type: 'bugfix'
created: '2026-11-17'
status: 'in-progress'
route: 'dispatch'
baseline_commit: '92e4e0b0acf0a256078c330419734eafa69b84ed'
context:
  - '/home/administrator/projects/hexalith/cicd/AGENTS.md'
  - '/home/administrator/projects/hexalith/cicd/docs/pre-adoption-publication.md'
  - '/home/administrator/projects/hexalith/cicd/docs/ordered-module-adoption.md'
review_loop_iteration: 0
---

<frozen-after-approval reason="user answered yes to extending the repair to EventStore release readiness while retaining normal nightly publication">

## Intent

Prepare EventStore release readiness for the query-contract API required by Projects. Verify the current producer source and repair a demonstrated product defect if necessary. Keep normal nightly publication and all current audit, compiler, test and security enforcement. No manual release, adoption, synthetic published version, compatibility shim or attribute deletion is authorized. Do not weaken product checks or edit owned module workflows/configuration. Preserve every concurrent change and job.

## Tasks & Acceptance

- [ ] Create a reproducible source-bound verification helper and result report under `_bmad-output/implementation-artifacts/evidence/eventstore-release-readiness-20261117/`. Given the frozen producer `3b2350e7c1fff640131f8101596c78a59e31a03f` and its Builds pin `16cf0db6f843eb4defdc87105804d42eded634d6`, when creating disposable standalone copies, then use those exact committed inputs, record their identities and initialize no nested submodules.
- [ ] Run ordinary Release/package restore/build with auditing, analyzers and warnings-as-errors for whole Contracts and RestApi.Generators test projects plus Gateway compilation. Given the existing query generator's functional compilation tests, when running both whole test projects with their supported runner, then retain exact totals, native exits and every skip/unrun/failure without changing filters or assertions.
- [ ] If a demonstrated product failure occurs, make its smallest correction from freshly fetched main in an isolated persistent worktree and rerun relevant checks. Given no failure, when the checks pass, then leave product source unchanged and do not manufacture a correction. Preserve the original failure if a later source or attempt changes.
- [ ] Write a concise readiness report with API/source/package boundaries and the central release route. Given passing focused producer checks but unavailable adoption/publication prerequisites, when reporting readiness, then distinguish the verified API from complete release acceptance and identify concrete remaining gates. No release, adoption, module push or parent-gitlink change occurs during implementation.

</frozen-after-approval>

## Code Map

- Producer objects: `/home/administrator/projects/hexalith/cicd/references/Hexalith.EventStore`; its shared checkout remains old and clean. Freeze the stated fetched commit without checking it out there.
- Producer `Directory.Build.props`, `Directory.Packages.props`, `.editorconfig`, `.gitattributes`, `global.json`, `AGENTS.md` and normal CI show package-mode properties and build guidance; inspect committed bytes.
- `src/Hexalith.EventStore.Contracts/Queries/QueryResultContractAttribute.cs`: new public API, absent from published 5.1.1/5.2.0.
- `tests/Hexalith.EventStore.RestApi.Generators.Tests/TypedGatewayQueryGenerationTests.cs`: two tests actually compile generated typed bindings and retain existing REST route behavior. Run the entire project, not these two alone.
- `tests/Hexalith.EventStore.Contracts.Tests/` and `src/Hexalith.EventStore.Gateway/`: whole contract regression and actual Gateway compilation.
- `scripts/verify-release-source.sh`, `tools/release-packages.json`: exact-main green CI/commitlint and fourteen-package release inventory.
- Build dependency objects are in root-declared `references/Hexalith.Builds`. Disposable standalone dependency copies beneath `TMPDIR` are permitted; do not initialize any nested submodule. If another dependency is needed, use its actual producer gitlink and root-declared object store; record it.
- Root setup currently selects three other modules. EventStore has no delivered ref or adoption config and no approved pre-adoption push substitute. These are publication blockers, not permission to invent configuration or claim adoption.

## Implementation Notes

- The user's original push-all authorization remains, but publication stays gated. Implementation performs no Git commits, pushes, dispatches, credential changes, releases, tags or live configuration writes. Do not edit another session's evidence or shared worktree files.
- Run ad hoc jobs with `run-with-temp`; all clones/build outputs remain under its private `TMPDIR`. Save useful logs/results to the new evidence packet. Wait for children and wrapper cleanup before returning.
- Projects preparation is already published at `3361f2e3b5655fa1ad50a2d12c640bbd5edcbb4b`; never reapply old patches or retest it with unreleased-package/source fallback. Current published SDK remains 5.2.0. The current source's missing package API blocks consumer acceptance.
- A concurrent guarded-write job in `/home/administrator/projects/hexalith/eventstore` must remain untouched. Other sessions keep advancing producer main; report the frozen tested source and any later observed head rather than silently changing subjects or claiming latest-main acceptance.
