# Story 12 investigation — 2026-11-16

Planning only: no implementation, registration, render, repository settings,
remote refs, credentials or module files changed by this session. Two research
subagents performed read-only investigation. `planning-preflight.py` records
fresh GitHub GET observations in `planning-preflight.json`.

## Revisions and concurrent work

- Initial CiCd HEAD: `a968a4212b8181fcca509a15446b50ec8131f038`;
  initial working tree clean. Live main and origin/main:
  `d04c9ab7a8fa43dc6dac1f15d34135aba8e79551`. Their production-code trees agree;
  local work contains additional story 11 evidence.
- During investigation another session advanced root HEAD to
  `b276193cc9d4169992c95da4c57db3c3ea08a674`, advanced multiple submodule
  checkouts and created `evidence/11/resume-nightly-final-handoff.json`.
  Preserve all of these changes. This session neither stages nor resets them.
  Implementation must recheck ownership of concurrent work and establish a
  clean story branch from freshly fetched main without dropping local evidence.
- A subsequent external `/pushall` commit,
  `eebeb80284da2bd23cc9fbaa3a4647915d77f094`, included this session's draft and
  planning files along with that other work. This session did not create that
  commit. Committing the draft does not approve it or resolve its open questions.
- AI.Tools initially checked out at
  `7ef8166ef87e1365f86d1a1b3aaf0235545177d4`; authenticated live main and
  subsequently observed local main are
  `736687b79c1e4fa8beabdab75c4675bb76c466b9`. Re-investigate the fresh source
  before implementation rather than treating the initial checkout as current.
- `builds-version`: `v6.0.6`, peeled source
  `fdda17c0a4538b0f7c99f813c20ca24b49006530`. Adoption must revalidate the
  currently selected published immutable release rather than freeze this
  planning observation as an authorization to use a stale pin.

## Source and scope

AI.Tools is a docs/skills repository without workflows, a solution, projects,
product tests, packages, NuGet waivers, containers, .husky, .gitmodules or a
Builds gitlink. Its root commitlint manifests are tool-only. There is no
product action to preserve or waiver to transfer. Do not invent either.

The setup contract supports `solution: none`; empty setup `{}` defaults to
empty test/hook/job/CodeQL/submodule arrays and false environment flags.
Use an explicit `solution: none` registration for readability. Dependabot
renders `updates: []`. Existing schema/renderer/validator tests already cover
this shape; this story needs no new runtime API or module YAML-asserting tests.

The module's README and entrypoint Git guidance refer to its pinned npm
commitlint. Retire the tool-only manifests and now-unused local config while
updating those references to the released shared validation. Preserve universal
guidance and synchronized normalized entrypoints outside the delivered block.
The main shared guide's stale provisional Update branch wording should align
with the canonical qualified rule: GitHub permits the operation, but agents
must not import owned CI/CD changes with it. Use fresh main and reapply only
product changes. Preserve unrelated migration/agent instructions.

## Live preflight

Default profile remains `/home/administrator/.config/gh-cicd-agent`; neither
`GH_TOKEN` nor `GITHUB_TOKEN` is present. Both configured profiles identify
`jpiquot`; this does not equate their token capabilities. Administrative GETs
use only command-local `/home/administrator/.config/gh`.

Authenticated AI.Tools observations:

- Rulesets: empty; environments: empty. The release-enable variable GET returns
  HTTP 404, so an exact `true`/`false` value is not established.
- Artifact/log retention: 90 days; push protection enabled; default CodeQL
  `not-configured`; Dependabot security updates `enabled: false`.
- Immutable releases disabled; zero tags, releases, workflows and runs.
  Historical CI failure rate and duration are unavailable, not zero.
- App installation selection remains unverified. Intended maintainer
  `GET /user/installations/179966090/repositories?per_page=100` returns
  HTTP 403: “You must authenticate with an access token authorized to a
  GitHub App, a personal access token, or basic auth in order to list
  repositories for an installation.” The CLI also names `read:user`.
  Use the existing maintainer settings UI for selection/readback; do not
  infer absence, switch credentials or request a new token from this result.
- NuGet policy inventory, Zot identity/grants and org selected-repository
  grants are not established by these GETs. Recheck them before adoption.

## Dependencies and human decisions

Story 11 remains in progress. `evidence/11/nightly-checkpoint-pending.json`
requires the genuine 2026-11-17 02:17 UTC scheduled night and subsequent full
story acceptance. The latest authenticated scheduled run is failed run
`43842471669`, created 2026-11-16 09:44:33 UTC from
`37e73a99dfe82c3b7741554d6f4ff2207711644b`; it predates adoption. The one-shot
observer is already configured; do not dispatch or duplicate it. Plan now,
hold AI.Tools adoption until that checkpoint is accepted.

Two contract choices cannot be inferred:

1. AD-21 unconditionally requires a module Zot identity and package-scoped
   NuGet policy, but this module has neither publication target. Recommend a
   narrow package-free exception: retain main-only `hexalith-release`, normal
   org grants and GitHub release behavior; omit unused publishing identities
   and policies, and require them before adding any package/container target.
   Alternatively provision reserved `Hexalith.AI.Tools*`/registry scopes despite
   there being no current payload. This needs a human decision, not a schema
   workaround or a silent relaxation of the architecture.
2. Root AGENTS requires successful
   `python3 references/Hexalith.Builds/check.py` before module pushes. AI.Tools
   does not yet contain that file or delivered config. Story 11's approved
   exception explicitly covers its two pilots only. Recommend a narrowly
   approved pre-adoption substitute for AI.Tools' preparation push: use a
   disposable standalone clone at fresh main, pin/export the released guard
   commitlint and audit lint, validate exact commit messages and changes,
   preserve all owned bytes/modes/gitlinks, check removal/reference consistency
   and normalized entrypoint synchronization, and record exact revisions and
   outcomes. Do not create an owned bootstrap or claim the normal checker
   passed. After delivery, require the normal checker in a standalone clone
   with direct Builds dependency. Without approval, preparation pushes remain
   blocked; do not silently reorder AD-21 product preparation.

## Release and verification behavior

Pinned Builds skips .NET setup/build/tests and CodeQL for this configuration.
`release_build.py` supports an empty manifest inventory; NuGet/login is gated
on packages and registry push on containers. `release_version.py` still
analyzes Conventional Commits. Existing `feat` history without stable tags can
produce an initial GitHub-only release, likely v1.0.0; exact version/outcome
must come from the real nightly. Empty solution does not imply no-release.
Propose enabling publishing (`true`) under the selected package-free/literal
provisioning decision; disabled is not a substitute for CAP-16 acceptance.

Reuse the released loader/guard/commitlint, `tools/render.py`, committed
`tools/validate.py` and authenticated delivery artifacts. Run disposable jobs
through `run-with-temp`; save useful logs here. Capture zero-scope duplicate
scan behavior, actual green CI, normal local checker and next scheduled
release success or valid nothing-to-release. No pre-adoption tests or
production/global validation were run during planning.

The wrapped mandatory checker was attempted from the actual AI.Tools root:
`run-with-temp python3 references/Hexalith.Builds/check.py` exited 2 because the
script is absent. `pre-adoption-check.json` records the exact result. No nested
dependency was initialized and no module push followed. Planning script syntax,
final newlines and whitespace pass. The draft measured 1,207 tokens with
`o200k_base` before the final code-map filename correction, within the workflow
scope target; no implementation acceptance is implied.
