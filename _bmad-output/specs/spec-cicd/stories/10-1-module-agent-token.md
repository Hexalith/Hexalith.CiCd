---
title: 'Module-agent token'
type: 'chore'
created: '2026-11-15'
status: 'blocked'
review_loop_iteration: 0
followup_review_recommended: false
context: []
warnings: [oversized]
deferred: []
baseline_revision: cfa0aa8f569bca3f70b6c4827ceae3a62f38cda6
---

<intent-contract>

## Intent

**Problem:** CAP-7 needs live proof that the module-agent credential cannot push workflow changes or dispatch workflows. Story 10-2 also needs preliminary, live-verified answers about branch pushes from current `main` and a PR's Update branch operation; story 11 confirms those answers after a real CiCd delivery.

**Approach:** Use the maintainer-supplied AD-7 fine-grained token at `/home/administrator/.config/gh-module-agent/token`. The agent verifies its identity and permissions and exercises all four live operations on one of the 17 module repositories declared in `.gitmodules`, using existing real workflow-changing history. Prior CiCd adoption or delivery is not required for 10-1 readiness or completion. Record these results as qualification of GitHub permission/branch mechanics before adoption, not proof of the CiCd delivery path. At story 11's existing pilot checkpoint, repeat the branch-push and Update branch checks after the first real delivery and confirm or correct 10-2's recorded restrictions before accepting that checkpoint. Missing credentials, unavailable meaningful Git history or unrelated authorization failures remain blockers, never successful refusal evidence.

## Boundaries & Constraints

**Always:** Limit the token to module repositories, with Contents and Pull requests write and no Workflows, Administration, Actions, Variables or Secrets write. Use the supplied module credential explicitly for every qualification operation, preserving the default CiCd-agent profile. Keep credentials out of output, source, logs and URLs. Use `run-with-temp` for disposable repository/object workspaces and save useful evidence outside `$TMPDIR`. Record full revisions directly from Git. Preserve owned files and all module `main` refs; confine permitted branch/PR operations to disposable refs and clean up after them.

**Qualification scope:** Existing real module history is sufficient for 10-1 even while `setup/*.yml` and CiCd `delivered/*` refs are empty. Ordinary workflow-changing history is not a CiCd delivery. Keep the preliminary branch findings and the pending post-delivery confirmation distinct in the evidence handed to 10-2; do not represent the later story 11 check as already verified.

**Never:** Create or broaden the token, use the maintainer login or CiCd-agent credential as a substitute, fetch the App key, edit any owned file, register/adopt a module to manufacture this test, change the 10-2 instruction block, dispatch a release with a privileged credential, merge a probe PR, force-push, or claim that a dry run or mock proves a GitHub refusal.

</intent-contract>

## Code Map

- `_bmad-output/specs/spec-cicd/SPEC.md`, CAP-7 and Constraints; `enforcement.md`, Layer 1: authoritative token scope and required GitHub refusals.
- `_bmad-output/planning-artifacts/architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md`, AD-7 and Deferred / Story 10 checks: permission separation, branches from current `main`, and the two answers required by 10-2.
- `_bmad-output/specs/spec-cicd/stories/1-maintainer-preconditions-and-remaining-checks.md:211`: existing CiCd-agent token is scoped to CiCd and Builds, with Actions/Contents/Workflows write. Lines 248–259 distinguish account privileges, token permissions and unreadable configuration.
- `setup/README.md:3`, `.gitmodules`: production registry versus the 17 target module repositories. The registry is empty; Builds is the runtime, never a module probe target.
- `templates/partials/ownership-block.txt.j2`, `templates/partials/deny-entries.json.j2`: 10-2 placeholders, read-only in this story.
- `/home/administrator/.config/gh-cicd-agent`: configured CiCd identity, unsuitable for module qualification; preserve it as the default. `/home/administrator/.config/gh`: maintainer profile used only for the explicitly authorized provisioning preflight, never as the qualification credential. `/home/administrator/.config/gh-module-agent/token`: supplied dedicated fine-grained credential, stored as a protected file, not a `gh` login profile. Read it privately into command-local `GH_TOKEN` for qualification, removing any inherited `GITHUB_TOKEN` override and disabling HTTP debug output. Never print the value or put it in command arguments, source, logs or URLs.

## Tasks & Acceptance

**Execution:**

- [ ] `/home/administrator/.config/gh-module-agent/token` — use this supplied protected credential file with the AD-7 repository selection and permissions. Record only its local source and intended module target. Agent checks effective profile, override presence, account, target and available read-only permission metadata. A filename or successful login alone does not establish suitability; qualify the actual permission behavior through the live checks below. No session-wide authentication changes.
- [ ] `_bmad-output/specs/spec-cicd/stories/10-1-module-agent-token.md` — record a successful module-owned-content branch push as the positive control, then the workflow-change push refusal. Use existing Git objects/history for the negative candidate and disposable refs, without editing owned files. Record candidate/base revisions, actual server response, ref state and cleanup. A repository-wide 403 is not a workflow-specific refusal.
- [ ] `_bmad-output/specs/spec-cicd/stories/10-1-module-agent-token.md` — attempt dispatch of a real existing dispatchable workflow with that same token, recording endpoint, ref, permission-specific response and absence of a created run. Do not use an invalid workflow/ref/input as the negative control.
- [ ] `_bmad-output/specs/spec-cicd/stories/10-1-module-agent-token.md` — identify an existing real workflow-changing commit reachable from the chosen module's current `main`, push a product-only branch from current `main`, then exercise the PR Update branch API with a disposable PR/head whose update would introduce an existing real workflow difference from its base. Use no owned-file edits or fabricated delivery. Record each actual result, limits and exact revision; close/delete probes without merging. Missing meaningful history leaves the affected result unverified, but absence of a prior CiCd delivery does not block this pre-adoption qualification.
- [ ] `_bmad-output/specs/spec-cicd/stories/10-1-module-agent-token.md` — provide 10-2 with both preliminary branch answers and any observed restriction, explicitly label the pre-adoption scope and pending confirmation at story 11, and include final owned-state/main-ref comparisons. Mark 10-1 complete only after all four live results and cleanup are established; story 11's later confirmation is not a 10-1 completion prerequisite.

**Acceptance Criteria:**

- Given the supplied dedicated credential and existing real workflow-changing history in a declared module, when readiness is assessed, then prior CiCd adoption/delivery is not a prerequisite; identity/public-read evidence alone does not count as completed permission qualification.
- Given the maintainer-created AD-7 token and successful ordinary branch access to a declared module, when a push introducing a workflow difference is attempted, then GitHub refuses it specifically for missing workflow permission and the rejected ref is unchanged.
- Given the same credential, a real dispatchable workflow and valid request, when workflow dispatch is attempted, then GitHub refuses it for missing Actions write and creates no run.
- Given an existing real workflow-changing revision reachable from current `main` and a product-only branch created from that current `main`, when the module token pushes it, then its success or restriction is recorded with server evidence for 10-2 as a pre-adoption GitHub-mechanics result.
- Given the same token and a disposable PR whose meaningful update would introduce an existing real workflow difference from its base into its head, when Update branch is attempted, then the actual result or permission restriction is recorded for 10-2 as a pre-adoption result, separately from an already-up-to-date or conflicted request.
- Given all four live results and cleanup, when 10-1 completes, then 10-2 receives the actual preliminary findings and their limits, with post-delivery confirmation explicitly pending at story 11's existing pilot checkpoint. That checkpoint repeats both branch checks after real delivery, records delivery/base revisions and actual outcomes, and confirms or corrects the instruction restrictions before acceptance.
- Given all probes, when verification ends, then no owned file or module `main` revision has changed, temporary refs/PRs are cleaned up, and no credential has been exposed.

## Spec Change Log

- 2026-11-15 — Human approved reusing a known suitable dedicated module-agent credential, otherwise creating it privately through the maintainer. Made the explicit credential handoff and existing delivery/base scenario prerequisites to re-arm; retained all four live checks and the existing permission boundaries.
- 2026-11-15 — Maintainer supplied `/home/administrator/.config/gh-module-agent/token`; read-only preflight verified its protected storage, `jpiquot` identity and Commons metadata access. Recorded the successful handoff separately from the still-unverified write permissions and missing qualifying delivery history.
- 2026-11-15 — Human selected option 1: qualify all four GitHub operations before adoption using existing real module history, then confirm both branch cases after real delivery at story 11's existing pilot checkpoint. This supersedes the earlier pre-rearm delivery gate. Updated the contract, acceptance criteria, story 10-1/11 manifest entries and architecture's deferred Story 10 check; retained AD-7 permissions and cleanup boundaries.

## Review Triage Log

## Design Notes

The account's `admin: true` describes the account, not the PAT. Public metadata/Actions reads also do not prove write scope. A generic transport refusal or an inventory endpoint's 403 cannot establish CAP-7. Do not infer token absence in GitHub from inability to list tokens.

The workflow-change probe requires a real server-side decision; `git push --dry-run` does not exercise the workflow-content check. Existing historical objects can provide a candidate without editing an owned file. If safe, meaningful probe history cannot be established within these boundaries, stop and record the unmet prerequisite.

## Verification

- Read-only authentication preflight and exact GitHub responses; no local unit test can establish these credential permissions.
- Actual token-qualified push/dispatch/Update branch operations, with revisions and API/Git responses saved here; no dry-run substitution.
- Compare owned Git tree entries and module `main` before/after; verify probe cleanup.
- `git diff --check` and inspect the final story diff; no implementation build is needed for evidence-only changes.

## Preflight Evidence

2026-11-15, before any qualification mutation:

- `GH_CONFIG_DIR=/home/administrator/.config/gh-cicd-agent`; `GH_TOKEN` and `GITHUB_TOKEN` are absent. No module-agent token variable or separate module-agent profile was found in the checked environment/profile locations. This establishes no available handoff here, not that no such token exists in GitHub.
- `gh api user` identifies `jpiquot`, account ID `6775094`. Public repository metadata returns `admin: true` on CiCd and AI.Tools; it does not establish PAT write access. The active token is a fine-grained PAT, with API expiry header `2027-11-08 23:00:00 UTC`, matching story 1's CiCd-agent provenance.
- Workflow-list reads on CiCd and Commons return HTTP 200 with `X-Accepted-GitHub-Permissions: actions=read`. That header describes endpoint requirements, not the token's complete permission inventory.
- `GET /orgs/Hexalith/personal-access-tokens` with that profile exits 1 / HTTP 403: `Resource not accessible by personal access token`. The accepted-permissions header requires `organization_personal_access_tokens=read`. Exact organization token inventory remains **unverified**; no extra permission or maintainer-token substitution was attempted.
- A non-mutating `git push --dry-run` of Commons' existing `main` commit to the same ref, with only the explicit `gh auth git-credential` helper, exits 128: `remote: Permission to Hexalith/Hexalith.Commons.git denied to jpiquot.` / `The requested URL returned error: 403`. This confirms the current profile cannot serve as the Commons push credential; it is **not** CAP-7 evidence.
- Commons' live `main` is `fbf4e94233821f6ca336af91a06feaaeb7a16855`. Production `setup/*.yml` is empty, and the live CiCd matching-ref query for `heads/delivered/` returns `[]`. No real delivery scenario has been established for the branch checks; no adoption was manufactured.
- Continuity investigation read all 25 prior story specs, all marked done, and found no prior module-token qualification or answers for the two branch checks. The correct 10-2 template paths are under `templates/partials/` and remain untouched.

### Initial readiness repair (before credential handoff)

The following records the original failed readiness assessment. Its credential-availability failure was cleared by the later handoff; the prior-delivery gate in item 3 was superseded by the final human decision below.

The first readiness assessment failed **Sufficient**: the maintainer-created credential was unavailable. This repair made the handoff explicit, but could not satisfy it by changing the specification:

1. Reuse a known suitable existing fine-grained token supplied by the maintainer. If none is available, the maintainer creates/approves a dedicated token with Hexalith as resource owner, selecting module repositories only (exclude CiCd and Builds), with Contents and Pull requests read/write, automatic Metadata read, and no Workflows, Administration, Actions, Variables or Secrets write. Use no additional permission as a workaround for the inventory 403 or login tooling.
2. The maintainer supplies it privately through a separate local `gh` profile, preferably `/home/administrator/.config/gh-module-agent`, or an explicit protected credential-file location. Record the local source and intended module target, never the secret. Select that credential explicitly for each qualification command, check for environment-token overrides, and preserve the default CiCd-agent profile. The recommendation alone does not establish that a credential has been supplied.
3. Before re-arm, identify suitable existing managed-module delivery/base history, including the delivery's workflow-changing revision and a meaningful PR update scenario. On resumption, verify actual module access before the four qualification operations. Unavailable history stays unverified; no owned file is edited, no delivery is fabricated and no module is adopted to create it.

At that original halt, re-reading the repaired spec could not clear the dependency criterion. All four live qualification results were **unverified**. The halted attempt had created no commits, remote refs, PRs, workflow runs, tokens or configuration changes.

### Interactive resolution decision — 2026-11-15

The human selected the reuse-or-create route above. At that point the suggested module-agent profile was absent and no alternative local credential source had been supplied; the handoff is now verified below. The maintainer and CiCd-agent credentials may not substitute for qualification. The initial delivery/base prerequisite was subsequently clarified by the final human decision below. The orchestrator owns re-arm and all story-status transitions; this session leaves status unchanged. The Auto Run Result below is preserved as evidence of the original blocked attempt.

Read-only local prerequisite inspection at CiCd `cfa0aa8f569bca3f70b6c4827ceae3a62f38cda6` found no production `setup/*.yml` registrations or registration history, no local `delivered/*` branch/tracking refs, and no `.github/hexalith-ci.json` path in the available histories of the 17 modules. Commons at `fbf4e94233821f6ca336af91a06feaaeb7a16855` has workflow-changing history, but that alone does not establish a CiCd delivery. No qualifying local delivery was identified; remote delivery history remains unverified. No fetch or remote qualification operation was performed.

The human subsequently explicitly authorized this interactive session to provision the restricted token using the existing `jpiquot` account. That authorization is limited to credential provisioning; automated qualification still may not create/broaden tokens or substitute the maintainer credential. A command-local administrative preflight using `/home/administrator/.config/gh` confirmed `jpiquot` (account ID `6775094`), with no `GH_TOKEN` or `GITHUB_TOKEN` override. The organization token-list request returned HTTP 404 under that profile, leaving inventory unverified. No available tool could create the fine-grained PAT, and authenticated browser control was unavailable. A prefilled GitHub creation link and the local helper `/home/administrator/.local/bin/configure-module-agent-token` were prepared. The helper accepts the generated token through a hidden terminal prompt, checks its account and saves it as the protected file `/home/administrator/.config/gh-module-agent/token`. The maintainer then confirmed the token was saved; the read-only handoff check follows.

### Credential handoff verified — 2026-11-15

- `/home/administrator/.config/gh-module-agent/token` exists as a regular, non-symlink file, owned by the current workspace user with mode `0600`. Its fine-grained PAT format was checked without displaying the value.
- Only child commands used that source through command-local `GH_TOKEN`. Inherited `GH_TOKEN` and `GITHUB_TOKEN` were absent; the default `GH_CONFIG_DIR` remains `/home/administrator/.config/gh-cicd-agent`.
- `GET /user` with the dedicated credential returned HTTP 200 and identified `jpiquot`, account ID `6775094`. The token expiry header is `2027-11-14 23:00:00 UTC`.
- `GET /repos/Hexalith/Hexalith.Commons` with that credential returned HTTP 200. The endpoint requires `metadata=read`; this public metadata read and the identity check do not establish Contents/Pull requests write, repository-selection completeness or the absence of prohibited write permissions. Those remain subject to qualification in the development session.
- Separate read-only CiCd discovery using the unchanged default CiCd-agent profile returned `[]` for `GET /repos/Hexalith/Hexalith.CiCd/git/matching-refs/heads/delivered/` and only `README.md` for `GET /repos/Hexalith/Hexalith.CiCd/contents/setup?ref=main`. No qualifying delivery/base scenario has been identified under the current contract.
- The credential-availability blocker is cleared. All four live qualification operations remain unperformed and unverified. No remote write, dispatch, feature test, commit or story-status change was made. The delivery-ordering question was then resolved by the human as recorded below.

### Final resolution — 2026-11-15

The human selected option 1: qualify the four GitHub operations now using existing real workflow-changing module history, then confirm the two branch cases after the first real CiCd delivery at story 11's existing pilot checkpoint. Existing historical workflow changes establish the earlier GitHub-mechanics scenario only; they must never be reported as a CiCd delivery. The supplied token's source is recorded above. All four actual permission/branch outcomes still belong to the re-driven development session.

Commons is an available pre-adoption candidate: local `HEAD` is `fbf4e94233821f6ca336af91a06feaaeb7a16855`; its ancestor `5f0e751bee108b96c6575922c8e0467242106bfb` changes `.github/workflows/ci.yml` and `.github/workflows/release.yml`. These revisions were read directly from Git. The development session must re-read live current `main` and select meaningful safe probe history; no probe was performed here.

This decision removes the prior-delivery readiness gate for 10-1, keeps all four live checks and their cleanup mandatory, and preserves actual post-delivery confirmation in story 11. Story 10-2 receives preliminary findings with their limits; the pilot checkpoint confirms or corrects its instruction restrictions if real post-delivery behavior differs. The manifest and architecture deferred check carry the same schedule. The missing-credential and sequencing issues are resolved; the orchestrator may re-arm 10-1 against this corrected working-tree spec. Its status is unchanged here.

## Auto Run Result

Status: blocked

Blocking condition: spec failed ready-for-development standard

Cause: no maintainer-created module-agent credential is available in the checked workspace environment/profiles. The **Sufficient** dependency criterion remains unmet after the readiness repair. Token creation stays with the maintainer, as instructed. Organization token inventory is unverified because its read API refused the configured CiCd profile; that refusal is not proof of token absence in GitHub.

| Required live check | Result |
| --- | --- |
| Workflow-changing push with module token | Unverified — token unavailable; no actual push attempted |
| Workflow dispatch with module token | Unverified — token unavailable; no dispatch attempted |
| Branch push after delivery | Unverified — token unavailable; suitable delivery history not established |
| PR Update branch | Unverified — token unavailable; no PR created or updated |

Only this story specification was added. Owned files, submodules, GitHub authentication settings and remote state are unchanged. `git diff --check` passed for tracked content; the new story also receives a direct whitespace/frontmatter check. No implementation build or test suite applies to this evidence-only halt. No commits or pushes were made.

Resume after the maintainer supplies the separate AD-7 credential and its location. Explicitly reopen this story as `draft` for re-planning; folder+id dispatch otherwise correctly halts on an existing `blocked` story. Retain the existing evidence and frozen intent contract.
