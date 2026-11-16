---
title: 'Repair the existing Projects gates blocking catalog qualification'
type: 'bugfix'
created: '2026-11-16'
status: 'in-progress'
route: 'oneshot'
review_loop_iteration: 0
---

<frozen-after-approval reason="user requested fix of the retained exact hosted failures">

## Intent

Repair existing pre-adoption Projects CI/Commitlint prerequisites so fresh exact-source CI can reach the delivered catalog acquisition and runtime G-6. Keep every existing workflow and gate command, dependency/gitlink pin, module commit policy, the delivered three-file acquisition correction, and concurrent unrelated work. Restore only the missing RendererFixture type body (keep removed YAML assertion removed), the three missing legacy suites still explicitly required by CI, and exact historical package.json/package-lock.json bytes required by the unchanged legacy Commitlint contract. These targeted compatibility repairs address the preparation defects; they do not reverse other migration preparation or activate publication. Deliver one source-bound six-file repair through a separate closed CiCd owner proposal using the existing App/environment/write mutex, without broadening the original catalog whitelist or using a maintainer module push. Qualify with run-with-temp, review, then collect fresh exact-source hosted results and diagnose subsequent failures. No nested submodule initialization, adoption, deployment, v2 activation, publication/A8 repetition, or Story 1.17 tracking change.

</frozen-after-approval>

## Implementation Notes

The latest user “fix” explicitly authorizes correction of the reported fixture/Commitlint failures. Projects current source is 146d0f7e9964c82da23d31b51e6ab62efdcfdda6. Commit 7e8acbd1e17ea76f814bb2335ce4b72742f73161 deleted required install metadata, three invoked suites and RendererFixture's body while preserving the decorator. Restore only the required compatibility sources from its parent 981ceef13a1abc88219925e73c51a23eb9ac50c2; keep all other preparation. The unchanged legacy Builds caller requires module npm metadata; authoritative API confirms the workflow still exists. Restoring its exact historical lock avoids a new dependency graph and retains its signature audit and existing module commitlint policy. The retained legacy suites inspect workflow behavior; preserving the user's existing-gate requirement takes precedence over the repository guideline for adoption-time removal. New tests must exercise behavior rather than assert module YAML.

The shared Projects and CiCd checkouts contain extensive concurrent work. Implementation and commits use isolated copies under a live run-with-temp job, snapshots/bundles/logs retained outside TMPDIR. Owner workflow delivery is authorized by the continuing task; no new credentials or settings are needed. Scope is one goal: let the existing gates execute against their actual prerequisites. Story key remains unset; no sprint synchronization.

Focused module qualification passes 61 renderer/release/candidate/mapper tests. The exact historical locked npm graph passes npm ci --ignore-scripts and npm audit signatures on Node 24.22.2; unchanged module commitlint accepts the fixed delivery subject and rejects invalid type/unstructured messages. No publication command was run. The generated closed proposal binds input tree c5425f42f16a8fe328ae5ec9f7c3d3ad81bd0047 and output e41153231b15b1838a3a511b4021f8623ae0a3da; SHA256 8e8154e0197377e14d1c56ded3a2b47b05754ffc3bb8285b9bd7373e803fe35c. Full tree comparison proves exactly six paths changed and all workflows, acquisition payload, pins, gitlinks and other source entries are unchanged.

## Spec Change Log

Independent review exposed two additional prerequisite defects in the original preserved gates. The initial six-file footprint was an implementation estimate; the reviewed final footprint is nine source files. Three targeted corrections build fresh Release FrontComposer inputs in a separate job, classify only the exact executable fixture/known host edges, and test both behaviors. Existing workflow commands, library-reference rules, product gates, pins and gitlinks remain unchanged. Review also found unused historical release dependencies; offline lock pruning removes those 424 entries while retaining all 74 needed dependency objects exactly. These implementation corrections serve the same authorized fix and do not add adoption, publication, deployment or tracking work.

## Review Triage Log

- High / patch: FrontComposer retained-output assumption fails in a fresh job; packaged CLI --build and failure-propagation regression cases address it.
- High / patch: new executable fixture was treated as a library; exact path/type/edge classification plus library/other-consumer refusal cases address it.
- High / patch: workflow20 versus runtime36 minute budget; new jobs40 provide receipt margin.
- Medium / patch: bind actual independently verified module validation, output tree and patch digest to plan; mandatory closed validation artifact added.
- Medium / patch: new owner-workflow integration coverage needed; actual plan-to-writer harness cases added.
- Medium / patch: apply source/ref/race/ambiguous-push refusal cases to new profile.
- Medium / patch: credentialed CLI needs inert-token/poisoned-environment qualification.
- High / patch: ci-gates qualification must explicitly receive successful behavioral outcome; omitted/empty/skipped/cancelled refuse.
- Low / patch: documentation now distinguishes failed initial candidate from passing final192 known test cases plus script commands and local/hosted acceptance.
- High / patch: historical npm graph introduced unused dependencies and38 vulnerabilities. Offline pruning retains required versions exactly; final Node24 install/signatures/audit pass, zero vulnerabilities.

Current-source final qualification preserves concurrent Projects e8fe81416f714c45f666dc3574c85c9b14b7aff9, its334 changed paths and11 advanced gitlinks. All192 known test cases and the three script commands plus actual invariant pass. Final input tree be06009e5cdc37b4ed236914a173ddc391de67fe; result 2a7fdf8f1559190d80257dbc5a79dc1c06069aeb. Byte-preserving Git binary-patch encoding avoids textual CRLF/context whitespace; independently applied complete tree is unchanged. Current patch SHA256 2b19d9f49f129f61fc415f75a73657e34bf83d5774b7ba1c056593fd6f4e604b; mandatory validation artifact SHA256 0951208571f64690253ad6b215517d3dbab5b20e147325aac7dca6ccd0f0c682. Owner code review has no remaining material finding. No Story1.17 tracking or unrelated source was changed.

Final packaged proposal includes an explicit end comment after the mandatory binary-hunk terminator; Git independently applies it to the unchanged reviewed tree, and repository whitespace policy passes without an exception. Authoritative patch SHA256 1ecac7ac770068d35269cd8cb1d4988bd62fc81e36392aba0ff1c1c12f2ef21e; validation SHA256 8f3a9ebe6e802c6ae813d2a07f099b0810eceae797fe98b65ef22e49571b7715. Previous packaging hashes are retained history, not current bindings.
