---
title: 'Correct pre-adoption publication verification'
type: 'bugfix'
created: '2026-11-16'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
baseline_commit: 'f95d46357e5378f2ed8a3da186fb4a543dc7b7ff'
context: []
---

<frozen-after-approval reason="user requested fixing the reported publication blocker">

## Intent

The push preflight incorrectly required adopted-module configuration from
unadopted Folders, Parties and Projects despite their separately approved,
module-specific preparation verification substitutes. Correct the CiCd
publication guidance to select those existing approvals before diagnosing
missing adoption configuration. Require every approved product, policy,
commit and preservation check on the exact proposed source, with fresh
remote-main verification at publication. After adoption require the normal
standalone Builds checker. Missing configuration, historical passes, or an
approval by itself never grants publication.

Preserve the normal checker, canonical delivered policy, module-owned content
and every existing test/audit requirement. Record the corrected route and
current evidence limitations without reclassifying failed or unrun gates as
passes. This correction creates no new exception and performs no adoption or
credential changes. Continue the earlier authorized publication only where
the actual required qualification and repository boundaries permit.

</frozen-after-approval>

## Implementation Notes

- The user explicitly requested fixing the reported failure in the existing
  dirty shared workspace. Preserve other sessions' staged, unstaged and
  submodule changes.
- Investigation: frozen approvals are in migration specs 17, 18 and 21.
  Builds local_check.run intentionally requires adopted configuration.
  Correct route selection in AGENTS.md and a linked publication guide;
  leave the canonical ownership template and checker unchanged.
- This is a small, reversible guidance correction with no unresolved intent
  gap or new external side effect. Any publication remains separately gated
  under the user's earlier push-all authorization.
- Existing Parties qualification binds another preparation tree. Folders
  records failed historical audit declarations and incomplete retained
  product prerequisites. Projects' package/G-6 qualification depends on a
  separately qualified Folders owner. Revalidate current inputs before
  making a publication claim; do not rerun stale hardcoded runners blindly.
- Updated AGENTS.md and docs/pre-adoption-publication.md to select the existing
  approved substitutes, retain all their requirements, and restore the normal
  checker at adoption. Neither the canonical delivered template nor the
  normal checker was changed by this correction.
- Local link validation and whitespace checks pass. Snapshot policy results
  are retained separately from complete module qualification; a policy-only
  pass never grants publication or adoption.
- Verification and review results are retained in
  [the correction packet](evidence/pre-adoption-publication-routing-20261116T201455Z/README.md).
  Released audit checks pass for the recorded Parties and Projects trees and
  the later Folders tree; the earlier Folders failure is preserved. All twenty
  concurrent historical archives match their original Git blobs and hashes.
  Follow-up review reports no additional concrete findings.
- The guidance correction is complete. Full exact-input preparation qualification
  and fresh remote-main verification remain required before the previously
  authorized publication; no incomplete product obligation was waived.
  No commit or push was made because repository Git rules require module
  qualification and publication to finish before the superproject commit.

## Review Triage Log

- medium, patched: the original guide described a singular candidate message.
  It now requires successful pinned validation of every full message in the
  fetched origin/main..candidate push range, matching normal checker coverage.
- medium, patched: umbrella ordering alone did not explicitly protect consuming
  modules from unavailable dependency commits. The guide now requires
  dependency-first publication and authenticated required-remote/ref availability
  before each consumer push, preserving the Folders-owner prerequisite.
- medium, patched: runner identity alone did not bind the released policy it
  imports. The guide now requires the exact acceptable immutable Builds release,
  authenticated release proof, pinned tool-lock identity and setup evidence;
  dirty or unreleased policy cannot supply the required released-policy pass.
