---
title: Reconcile five deferred CI/CD handoff findings
type: chore
created: '2026-11-23'
status: 'done'
route: 'oneshot'
baseline_revision: ff5bf4b7f6a037107c05a9e11f5a38b38f0c467a
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

Resolve five open findings in the CiCd backlog. Bring the checkout contract
and frozen-file Dependabot procedure into line with the shared implementation
and its permissions. Correct the two claims about the November 15 module-token
closeout using its retained evidence. Recover both pilot findings named in
DW-37 and give each a traceable disposition.

</frozen-after-approval>

## Implementation Notes

The checkout description follows the pinned Builds v6.6.2 contract at
`2d9ef8b454ff897daca0149f3549844f584b634a`. Five focused tests exercised
the emitted list for configured and absent solutions, Builds' own checkout,
direct consumer gitlinks, nested exclusions and rejection of an ordinary file
declared as a submodule. All five passed. The tag-creation decision comes from
the separate story 1 ruleset probe. [Probe](../specs/spec-cicd/enforcement.md#accepted-residuals)

From the root of the pinned Builds checkout, run

```sh
run-with-temp python3 Github/lib/tests/test_ci_pipeline.py \
  SubprocessPipelineTests.test_prepare_publishes_validated_workflow_outputs \
  SubprocessPipelineTests.test_builds_module_root_is_workspace_relative_without_builds_gitlink \
  ClassifierAndSubmoduleTests.test_consumer_cli_initializes_recorded_direct_gitlinks_only \
  ClassifierAndSubmoduleTests.test_only_explicit_root_declared_gitlinks_initialize_without_recursion \
  ClassifierAndSubmoduleTests.test_declared_path_that_is_not_a_gitlink_is_rejected_before_update
```

Story 1's credential inventory supplies the grants used for the Dependabot
handoff. Story 10-1's retained readback supplies the limits on its policy and
credential claims. All 41 evidence digests in that receipt matched the files.
[Closeout receipt](../specs/spec-cicd/evidence/10-1/closeout-verification.json)

DW-37 concerned two findings in the completed pilot story. Story 30-3 accounts
for the Docs grant. DW-44 tracks the nine other repository policies in the
November 22 NuGet receipt, including EventStore policy 16915.
[Pilot receipt](../specs/spec-cicd/evidence/11/ad-7-ad-21-maintainer-repair-20261122.json)

The 22 CiCd scope and scope-selection tests passed.

## Review Triage Log

- Medium. Qualified the inventory's PR closure instruction as Dependabot-only to match AD-20.
- Low. Linked DW-44 to the dated maintainer acceptance as well as the earlier repair receipt.
- Medium. Specified that Windows receives the full initialized path array, including Builds for a consumer solution and an empty array for a guard-only run.
- Low. Added the five test names and reproduction command for the pinned Builds release.
