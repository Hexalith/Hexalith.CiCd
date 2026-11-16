# Story 12 execution handoff — 2026-11-16

The human answered "do recommended", approving both concrete alternatives in
the displayed draft and continuation of the scoped work. Both answers are
recorded in the frozen intent; there are no remaining Open Questions. Do not
ask again for those decisions or silently expand their scope.

Use these dedicated persistent implementation workspaces:

- CiCd: `/home/administrator/projects/hexalith/cicd-story-12`, branch
  `story/12-migrate-ai-tools`, from freshly fetched `origin/main` at
  `7d32df03405c876df6f098aec4036207bf35af1d`. Another session advanced
  origin/main during worktree creation; this is the actual full starting HEAD,
  which includes the merged local evidence and published diagnostic source.
- Standalone AI.Tools: `/home/administrator/projects/hexalith/ai-tools-story-12`,
  branch `docs/cicd-adoption-12`, from freshly fetched module main at
  `736687b79c1e4fa8beabdab75c4675bb76c466b9`.

All relative implementation paths in the spec refer to those owning
repositories. Do not edit the shared original module checkouts. The original
CiCd checkout contains concurrent stories and a scheduled story 11 observer;
preserve its branch, index, other specs and gitlinks. Mirror only this story's
spec/evidence back there for user visibility after local implementation.

This is bmad-build step 03, which states "No push. No remote ops." Prepare and
verify locally; do not push, provision settings, alter App scope, publish or
dispatch anything during this phase. Dependency/tool downloads required for
local verification are permitted. Product preparations, central policy
documentation, registration and render can be prepared on these isolated
branches while the external pilot gate is pending. Never record an unpushed
product commit as a CiCd gitlink; leave that integration pending with exact
evidence. Do not report a local preparation as actual adoption.

The live scheduled-night GET was repeated after the human's answer: latest
is still failed pre-adoption run `43842471669` from 2026-11-16. Story 11's
required next genuine night is 2026-11-17 02:17 UTC, followed by its acceptance.
Do all independent local work, record remaining dependent tasks, and return
the exact blocker without marking the story done. Do not duplicate or change
the existing observer.

Use the existing released Builds contract and guard primitives for the
approved preparation proof. A successful normal checker is impossible before
adoption and must not be simulated by creating owned files. No product build
or tests exist. Avoid adding implementation-mirroring tests for documentation;
run meaningful preservation, audit, exact-message, reference and renderer
checks instead. Save useful logs/evidence in this story's evidence directory;
disposable verification clones, feeds and outputs go beneath the wrapper's
TMPDIR.
