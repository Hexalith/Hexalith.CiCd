# Sprint change proposal for organization-wide CiCd App access

**22 November 2026 · Minor scope · Approved and implemented**

## 1. Issue summary

The maintainer wants the Hexalith CiCd GitHub App to cover every current and future repository in the Hexalith organization. GitHub already reports **All repositories** for the active `hexalith-cicd` installation `179966090` (App ID `5671811`). The course correction is to bring the CiCd contract and operator guidance into line with that setting. AD-7 still specifies selected repositories, and AD-21 still tells the maintainer to add each repository by hand. [GitHub installation](https://github.com/organizations/Hexalith/settings/installations/179966090) · [Architecture spine](architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md)

Story 30-1 recorded selected mode and an HTTP 403 on the repository-enumeration endpoint earlier on 22 November. Story 11 recorded `Hexalith.Docs` as an accepted extra under the selected-mode policy. Those observations describe the earlier baseline. The fresh organization installation response directly establishes the current mode. [Story 30-1 evidence](../specs/spec-cicd/evidence/30-1/hosted-readback-20261122.json) · [Story 11](../specs/spec-cicd/stories/11-pilot-migration-commons-and-polymorphicserializations.md#current-ad-7-and-ad-21-readback--2026-11-22)

### Hosted readback

Authorized interactive GETs ran as `jpiquot` using command-local `GH_CONFIG_DIR=/home/administrator/.config/gh`, with both `GH_TOKEN` and `GITHUB_TOKEN` unset. The account returned active Hexalith organization administration. The ordinary CiCd-agent token received HTTP 403, “Resource not accessible by personal access token,” on the organization installations endpoint. The maintainer requests below each returned HTTP 200. Times are UTC on 22 November 2026, and the digests identify response bodies.

| Read | Time and GitHub request ID | SHA-256 |
|---|---|---|
| `GET /orgs/Hexalith/installations?per_page=100` | 16:59:04 · `D280:3A5B54:886C24:FA19E3:6B031F58` | `bbd5382cbf66698ef56dfdf8915dee52411c5497a5d608f825ed6e13837a11b5` |
| CiCd `GET /environments/cicd-app` | 16:59:05 · `D294:35FB30:134CE799:1D2114A6:6B031F59` | `62b5d307d91b9f2e0432c2cba4e16ce1bbf6438faf61e915f4dffb23a4350ca1` |
| CiCd `GET /environments/cicd-app/deployment-branch-policies` | 16:59:05 · `D239:E2627:85DBBD:F77893:6B031F59` | `fa563aefcf72e6b38b6932dcaa5e26a4d7c7263b58b9e63cd804dd6e304993ed` |
| CiCd `GET /environments/cicd-app/variables/HEXALITH_CICD_APP_CLIENT_ID` | 16:59:06 · `D243:1CDDC1:140B908C:1E2FA5C8:6B031F59` | `33d9b6cfa44eee053fef18a81a47163efcf225fccf65cff29278ce1330e6ac1b` |

The organization response reports `repository_selection: all` and `suspended_at: null`. Grants match the preceding inventory readback: Actions, Contents and Workflows write, and Administration, Metadata and Code scanning alerts read. The environment variable matches the installation's client ID. The environment uses a custom deployment policy with sole branch `main`. The readback uses GitHub's installation configuration and leaves the earlier selected-list refusal in the historical receipt. [GitHub organization installations API](https://docs.github.com/en/rest/orgs/orgs#list-app-installations-for-an-organization)

## 2. Impact analysis

- **Requirements and backlog.** CiCd uses [SPEC.md](../specs/spec-cicd/SPEC.md) as its requirements contract and [stories.yaml](../specs/spec-cicd/stories.yaml) as its ordered implementation backlog. Use those canonical artifacts for the PRD and epics assessment. The change affects the credential constraint and the 30-series inventory work. Story 30-1 can finish its source inventory review under its existing criteria. Add a narrow follow-up after 30-1 and before the next AD-21 provisioning checklist is used. Story 30-2, the other audit stories, the completed pilot and the planned adoption order can proceed on their existing criteria. The MVP still covers the existing managed fleet.
- **Architecture and operations.** AD-7 defines the GitHub App installation and token boundaries. AD-21 defines the maintainer's provisioning sequence. AD-3 already checks each candidate with its scoped token and checks repository settings, so the preflight still applies. The source checker and migration controllers enforce repository and permission limits. The operator interface is GitHub's existing **Repository access** setting. Product UX and runtime interfaces are outside the scope of this change. [Delivery preflight](../../tools/deliver.py#L31) · [App workflow inventory](../../docs/cicd-app-inventory.md) · [GitHub settings instructions](https://docs.github.com/en/apps/using-github-apps/reviewing-and-modifying-installed-github-apps#modifying-repository-access)
- **Risk.** The App's existing grants now cover unmanaged repositories and repositories added to the organization. Anyone who can obtain the App key can request a more broadly scoped token. GitHub issues a token covering the installation if the mint omits its repository restriction. Keep the existing explicit owner, repository and permission inputs, main-only key environment and reviewed selector bounds. Preserve fixed migration routes, registered-module and accepted-ref targeting, and existing onboarding and publication checks. [GitHub installation token scoping](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-an-installation-access-token-for-a-github-app)
- **Historical evidence.** Once the new rule is approved, Docs is ordinary installation coverage. Preserve the historical exception, the earlier HTTP 403 and the pilot decision as recorded. The unrelated NuGet residual, diagnostic isolation discrepancy, ungranted optional Pull requests permission and migration-owner retirement decisions each retain their existing disposition. [Story 11](../specs/spec-cicd/stories/11-pilot-migration-commons-and-polymorphicserializations.md) · [Owner dispositions](../../docs/cicd-app-inventory.md#migration-owner-dispositions)

## 3. Recommended approach

Directly reconcile the specification and runbook with the verified setting. Allow roughly half an engineer-day for the edits, source check and fresh hosted readback. Schedule the documentation update before the next module provisioning pass. Side-by-side readback and source verification cover the two different risks: installation setting drift and overly broad credentials in workflow jobs.

Returning the installation to selected mode would reintroduce per-repository provisioning and fail the requested coverage. Revising the MVP would expand the change into fleet adoption, which already has its own requirements. The live installation satisfies the proposed setting, so implementation can proceed through read-only verification and local documentation and backlog updates.

## 4. Proposed edits

| Artifact and section | Before | Proposed wording or action |
|---|---|---|
| [Architecture AD-7, The App](architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md#ad-7--credentials) | “It is installed on selected repos: the 17 modules, Builds and CiCd.” | “The active `hexalith-cicd` installation on the Hexalith organization uses **All repositories**, covering current and future organization repositories. Every workflow token explicitly restricts owner, repositories and required permissions to its reviewed job. The committed setup registry, accepted delivery refs and fixed migration profiles govern automation targets.” Update the hosted-evidence paragraph with the latest mode and retain its earlier account as history. In the structural diagram, label the module and Builds edges as scoped App-token paths. |
| [Architecture AD-21, maintainer preconditions](architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md#ad-21--onboarding-sequence) | “add the repo to the App installation” | “Verify the active Hexalith CiCd App installation is set to **All repositories** as an organization precondition. For each adoption, retain AD-3's repository access check with the scoped token and complete the remaining repository preconditions in order.” |
| [SPEC, Constraints → Credentials](../specs/spec-cicd/SPEC.md#constraints) | One org App delivers, dispatches and publishes. The hosted paragraph still cites the current selected-list refusal. | “One organization GitHub App is installed on all Hexalith repositories. Its reviewed workflow tokens explicitly scope owner, repository set and permissions. CAP-4 and CAP-16 govern which repositories enter managed CI/CD.” Cite the fresh hosted setting and date the earlier refusal. |
| [Enforcement, Layer 1 and Accepted residuals](../specs/spec-cicd/enforcement.md#layer-1-token-scoping) and [module inventory, Org-wide Apps](../specs/spec-cicd/module-inventory.md) | Layer 1 describes the selected-list refusal as current. The inventory describes the initial Builds/CiCd installation. | Record `repository_selection: all` as the current hosted setting and keep the earlier records dated. Document the organization-wide App key impact in the accepted residuals when the proposal is approved. |
| [App inventory runbook, Hosted observations](../../docs/cicd-app-inventory.md#hosted-observations-on-22-november-2026) | The earlier readback shows selected mode and requests an authorized reader for that list. | Add the later timestamped `all` readback, deployment policy, identity binding and grant summary. Use the organization installation endpoint to verify mode, and the existing offline inventory to verify workflow token scope. Keep both receipts and date the earlier mode and refusal. |
| [Story backlog](../specs/spec-cicd/stories.yaml) and [deferred-work ledger](../implementation-artifacts/deferred-work.md#dw-38-complete-current-app-selected-repository-membership-remains-unverified) | Story 30-1 covers the source inventory and earlier hosted reconciliation. DW-38 requests a fresh selected-repository list. | Add proposed story **30-3, Reconcile organization-wide CiCd App access**, immediately after 30-1. Its acceptance is given below. Resolve DW-38 against the approved current mode and evidence. Keep its historical refusal and link the story 11 Docs disposition to the new decision. |

## 5. Implementation handoff

**CiCd developer — proposed story 30-3.** Apply the edits above after approval and link the compact hosted and source evidence. Accept when the canonical documents agree on **All repositories**, onboarding has no per-repository installation step, and the existing offline checker and all inventory tests pass. Confirm the workflow sources, token policy, configured targets and managed-module perimeter have identical Git blob or tree identities before and after the implementation.

**Hexalith organization owner — hosted acceptance.** Confirm the same active installation reports `repository_selection: all`, matches the environment client ID, and retains the recorded grant set and sole allowed deployment branch `main`. Record a fresh authenticated read at implementation. The existing installation satisfies the setting, so there is no configuration write to perform. Some per-repository checks are available only with their scoped token and remain with normal workflow execution.

## 6. Proposal verification

- Source baseline `5883ebcb4dde154ec67d044c778fcccc355c7c33`, tree `c67f12891a92b4653add6deb7e99aeff669cecb6`, reviewed token-policy blob `414ab95013dcabc715f8a85ae6db271b54681373`. Story 30-1 already had a worktree edit when this proposal started.
- Offline App inventory passed with 7 workflows, 10 jobs and 76 reviewed mint steps, log SHA-256 `cab51597e110aee7f381529c56d13f41fdbdf9f948888c7289bdd3a2cfb9d22b`. All 17 inventory tests passed, log SHA-256 `d7f7583e8db4d73a8ce2780a53130ff9e59b00ebe04a93a076f1523ee7bf21eb`.
- Checklist 1.1–1.3, 2.1–2.5, 3.1–3.2, 3.4, 4.1–4.4, 5.1–5.5 and 6.1–6.5 complete. Item 3.3 is inapplicable. This project tracks the sprint in `stories.yaml`.

## 7. Approval and implementation record

The maintainer approved the proposal in the interactive session on 22 November
2026. The CiCd developer applied the specification, architecture and runbook
updates and added story 30-3 immediately after 30-1 in the story backlog. DW-38
is done. The follow-up read under the organization owner's profile again
confirmed the active App's `all` setting, grants, client-ID binding and sole
deployment branch `main`. The source check and 17 inventory tests passed against
the same workflow, token policy, configured targets and perimeter identities.
[Implementation and verification](../specs/spec-cicd/stories/30-3-reconcile-organization-wide-cicd-app-access.md)
