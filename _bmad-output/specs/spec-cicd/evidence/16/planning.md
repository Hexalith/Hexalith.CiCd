# Story 16 planning and maintainer preflight

Investigated on 2026-11-16. This is planning evidence, not adoption evidence.
No product edits, builds/tests, external configuration writes, dispatches or
pushes were performed. Subagents investigated module source and administrative
preconditions independently. Their module findings are in
[module-investigation.md](module-investigation.md).

## Workspace and contract

The human authorized an isolated worktree after the original workspace acquired
unrelated changes. Worktree `/home/administrator/projects/hexalith/cicd-story-16`
uses branch `story/16-migrate-conversations`, based on freshly fetched CiCd main
`d04c9ab7a8fa43dc6dac1f15d34135aba8e79551`. Its initial working tree was clean.
Only direct root Builds, Conversations and AI.Tools submodules were initialized;
nested submodules remain uninitialized. The original workspace is untouched.

Canonical intent is entry `16`, Migrate Conversations, in
`_bmad-output/specs/spec-cicd/stories.yaml`. It belongs to the sequential migration
plan, not a numbered epic/story pair; no sprint-status key was resolved.
Use SPEC-cicd CAP-5/10/16 and spine AD-3/12/13/14/15/20/21. Previous pilot
implementation is continuity evidence, not authorization to extend its exceptions.

## Read-only administrative observations

The investigation checked the effective default
`/home/administrator/.config/gh-cicd-agent` profile and the absence of
`GH_TOKEN`/`GITHUB_TOKEN` overrides without printing credential values. The
intended command-local maintainer profile `/home/administrator/.config/gh`
authenticates `jpiquot` (account ID `6775094`); its administrative GETs below
succeeded. No default profile was changed.

Conversations repository ID is `1231551514`; observed live main is
`9e24c280efd5e9c13826eab9bc8b8b687a7bee09`.

| Item | Observed state |
| --- | --- |
| Repository rulesets | Empty; exact main and v* protections must be provisioned. |
| Environments | Only production; hexalith-release is not provisioned. |
| Release kill switch | Exactly true. |
| Actions retention / push protection | 90 days / enabled. |
| CodeQL default / security updates | not-configured / disabled. |
| Immutable releases | Disabled; enable immediately after actual adoption. |
| Drafts and orphan version tags | No drafts; all nine v* tags have published releases. |
| Legacy CodeQL | First page has 100 analyses from .github/workflows/codeql.yml:analyze; enumerate fully before cleanup. |
| Deploy keys / repo Actions and Dependabot secrets / production secrets | Complete authenticated inventories empty. |
| Variables | Release kill switch and legacy NUGET_TRUSTED_PUBLISHING_USER=jpiquot. |
| Org grants | Conversations is excluded from all ten Actions secrets, both Dependabot pull secrets and the shared NuGet variable. |
| Zot ACL | No Conversations namespace/principal in observed distribution-registry-config resourceVersion 46533286. This does not establish absence of an account or global API-key use. |
| NuGet Trusted Publishing | Contents unverified; no usable authenticated policy document was visible. Do not infer absence. |

App `hexalith-cicd`, installation `179966090`, has selected-repository mode and
the expected permission classes. Conversations membership is **unverified**:

- `GET user/installations/179966090/repositories?per_page=100` returned HTTP 403:
  "You must authenticate with an access token authorized to a GitHub App, a personal access token, or basic auth in order to list repositories for an installation."
  The CLI additionally mentioned `read:user`.
- `GET repos/Hexalith/Hexalith.Conversations/installations` returned HTTP 404.
- Singular repository `/installation` and `orgs/Hexalith/installation` returned
  HTTP 401: "A JSON web token could not be decoded."

Use the existing installation-settings UI for membership verification/addition;
preserve all concurrent onboarding selections. These endpoint failures do not
establish exclusion or justify broadening credentials.

## Reuse map

Relative to `evidence/11/` in the same spec folder:

- `provision-github.py`: ordered stale cleanup, exact rulesets, main-only release
  environment and additive org grants.
- `provision-registry.py`: memory-only new credential, scoped ACL, preservation,
  rollout and readback. Never revoke global administrators or another module.
- `cleanup-adopted-github.py`: authenticate adoption before immutable-release
  enablement and precise legacy access cleanup.
- `nuget-cleanup-ui.py`: UI interaction pattern; use new Conversations policy
  identities, exact repository ID, release.yml, hexalith-release,
  Hexalith.Conversations* package scope and push-only access. Pilot IDs do not
  apply.
- `pre-adoption-verify.py`: exact-input verification pattern only. The protected
  module profile credential is at
  `/home/administrator/.config/gh-module-agent/token`; use subprocess-local
  credential handling without output, default-profile changes or alternate
  credentials for module writes.

## Human decisions, 2026-11-16

The human selected both recommendations with **"apply recommended"**:

1. Include generic shared preparation/protected Windows checkout, shared
   qualification and its Builds release in story 16.
2. Approve a Conversations-only pre-adoption preparation verification path:
   exact-input package-mode builds/tests and applicable product checks,
   policy/commit validation and owned byte/mode/gitlink preservation before
   preparation pushes; require normal check.py after adoption. No owned-file
   edits, fabricated producer metadata or weaker tests/audits are authorized.

This answers the two questions; it does not claim any verification has run or
that the final implementation spec has passed its approval checkpoint.

## Plan facts

**Intent gap:** before-adoption product pushes cannot satisfy the mandatory
normal checker: Conversations has no committed .github/hexalith-ci.json or
accepted delivered state. Its current Builds pin **does contain check.py**;
missing script is not the diagnosis. The pilot exception explicitly excludes
other modules. The decision above now authorizes the narrow Conversations path;
no replacement verification has run.

**Irreversibles/external effects:** subsequent work provisions protections,
publication access and credentials; publishes a shared Builds release; pushes
product/adoption commits; and removes legacy access immediately after adoption.
Perform these only in AD-21 order with preservation and authenticated readbacks.

**Footprint:** module actions, a fixture build adapter, classified test/tooling
retirement, waiver relocation, setup/render/gitlink changes, and potentially
shared enrollment/Windows-checkout support plus its release. The original story's
Windows-only description understates current-main prerequisites.

The proposed shared extension must be generic and opt-in, prepare genuine
producer-selected imports before restore/project evaluation, work consistently
in CI/local check/Windows/release, and obtain Windows checkout inputs from
validated CI outputs. It must not invent producer metadata, add module names to
Builds, change frozen legacy implementation, or relax Windows path protection.
The initial module companion records fixture/checkout risks; the completed
design and feasibility work below supersede its unresolved design suggestions.

## Completed planning after the human decisions

The clean direct Conversations checkout was deliberately refreshed from its
parent's old pin to current origin/main
`9e24c280efd5e9c13826eab9bc8b8b687a7bee09` for accurate source investigation.
That is the intentional working gitlink difference in this isolated worktree;
no module product bytes were edited and no nested submodule was initialized.

The final planning companions are:

- [Gate inventory](gate-inventory.md): complete source-bound method/helper/link
  dispositions, mixed-test extractions, retained package/consumer coverage and
  exact destinations. Product assertions and Linux-specific TestSupport coverage
  survive; forbidden CI/story/evidence checks do not.
- [Shared preparation](shared-preparation-design.md): nullable moduleManifest,
  genuine new managed authority using the accepted central catalog while keeping
  truthful Platform provenance and legacy producer semantics. The distinct
  candidate-qualification command supports the explicitly approved pre-adoption
  proof without owned overlays or fabricated acceptance. Ordinary entry points
  reject qualification receipts.
- [Windows and fixture design](windows-and-fixture-design.md): nullable
  windowsCheckout with exact immutable excluded-directory tree identities,
  protected cone sparse-index checkout, safe metadata/direct-dependency operations,
  external fixture adapter/import isolation and in-memory native test reporting.

The Platform tuple conflict is real: independent AD-6/AD-10 Builds bumps cannot
satisfy the old producer's equality-to-Platform-catalog check. Canonical AD
precedence determines central active-catalog authority. The new explicit producer
contract implements that rule; it does not suppress HXW009 in legacy modes or
relabel the Platform pin. A new minor shared producer/runtime release and module
tool-pin update are required before adoption. A qualified existing released
Platform identity can replace the untagged module product pin; no Platform
repository write or early Platform migration is required.

Four retained native Windows probe JSONs establish the sparse-index approach and
its index-expansion/submodule-helper limitations. All 49,415 current nonarchive
paths passed native protected index-input/readback validation. This is preliminary
checkout feasibility, not actual module execution or GitHub runner qualification.
All scratch work/children finished; useful observations remain here. No product
build/test qualification or external configuration mutation has occurred.

The human completed the bmad-build spec-approval checkpoint with **"approve and
stop"**. The implementation spec is `ready-for-dev`; its frozen intent is
human-owned. Resume from this isolated worktree and the approved spec. New code,
actual product verification, provisioning, publication, adoption and scheduled-night
acceptance remain outstanding. Implementation has not started.
