---
title: 'Story 1: Maintainer preconditions and remaining checks'
type: 'chore'
created: '2026-11-08'
status: 'in-progress'
route: 'dispatch'
baseline_commit: 'd4e4faa5d0c2e1470e8edb266a4231aa6fd46920'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The new pipeline can't run yet: there's no CiCd App, `cicd-app` or CiCd ruleset; Builds' `main` still needs PRs and checks; four agent Apps can write workflows in CiCd and Builds; the org lacks the `HEXALITH_*` credentials; and agent sessions use the maintainer's `gh` login. Two spine checks are also open: whether package mode reads submodules beyond Builds, and whether a ruleset can restrict `v*` creation.

**Approach:** The agent writes the checklist below and prepares its data, runs both checks and records the answers in the spec. The maintainer makes every change, and the agent then verifies each item read-only through the API.

## Boundaries & Constraints

**Always:**
- The maintainer makes every org, repo, App, nuget.org and Zot change, including the temporary probe ruleset. The agent reads the API with the maintainer's login only until the CiCd-agent token is wired. After that it uses only that token.
- Order: the App before CiCd's rulesets (it is their bypass actor), and Builds' orphan `v*` tags deleted before the `v*` ruleset (enforcement.md, Not used). Builds' nuget.org policy for `builds-release.yml` is added beside the existing one; nothing is removed.
- Rulesets are exactly the AD-21 set, with no bypass actors except on `delivered/**`:
  - CiCd `main`: deletion, non_fast_forward.
  - CiCd `delivered/**`: creation, update, deletion, non_fast_forward; bypass the App only.
  - Builds `main` (cut "Protect main"): deletion, non_fast_forward.
  - Builds `v*` tags: update, deletion.
- The CiCd-agent token is exactly AD-7: Builds and CiCd only, Contents, Workflows and Actions write, at most 366 days.

**Decisions (2026-11-08):**
- The checklist lives in this spec, as the `[maintainer]` tasks. Later stories cite AD-21, not a copy.
- Agent sessions get the CiCd-agent token through a separate gh config: `gh auth login --with-token` into `~/.config/gh-cicd-agent`, and this repo's `.claude/settings.local.json` (globally git-ignored) sets `env.GH_CONFIG_DIR` to it. The maintainer's own gh login stays unchanged.
- The spec is kept whole above the token target. Story 1 was kept unsplit on purpose.

**Never:** change Builds files (story 2-1); install the App on modules, or create `hexalith-release`, immutable releases or `HEXALITH_RELEASE_PUBLISH_ENABLED` (stories 3-7 and 11–26); touch module settings beyond push protection, agent-App scope and legacy-secret visibility; edit the adopted spine; write a precondition-check script.

</frozen-after-approval>

## Code Map

- spine AD-7 (l.209), AD-19 (l.487), AD-21 (l.541), Deferred (l.709): the rules this checklist implements. Read-only.
- `_bmad-output/specs/spec-cicd/pipeline-stages.md:29` and `SPEC.md:162`: the submodules lines. Replace with the answer.
- `_bmad-output/specs/spec-cicd/enforcement.md:117`: the `v*` residual. Replace with the answer.
- `_bmad-output/specs/spec-cicd/module-inventory.md:49,76-85`: the Builds rulesets row and the org evidence. Update to the post-story state, dated.
- `_bmad-output/specs/spec-cicd/.memlog.md`: append one `(event)` entry with both answers.
- Live state, 2026-11-08:
  - No CiCd App. `claude`, `cursor`, `chatgpt-codex-connector` and `semgrep-app` (workflows or single_file write) are installed on all repos. `codacy`, `codecov` and `sonarqubecloud` are read-only, so keep them.
  - Org: default workflow permission `read` (OK); fork approval `first_time_contributors`; retention 30 days. The legacy secrets (`NUGET_API_KEY`, `HEXALITH_ZOT_*`, `AZURE_*` ×4, `SONAR_TOKEN`) are visible to all repos. No `HEXALITH_*` credentials and no Dependabot org secrets exist yet.
  - CiCd has no rulesets, environments or secrets, and push protection is off. Collaborators are `jpiquot` and `tinouit`, the two org owners, and there are no deploy keys. Builds is the same apart from the next point.
  - Builds' "Protect main" (id 19196298) requires a PR and three status checks (Codacy, SonarCloud, `commitlint / commitlint`) and lets `jpiquot` bypass. There is no `v*` ruleset.
  - 15 Builds `v*` tags have no release: v4.21.0–v4.21.7, v4.22.0, v4.27.5, v4.28.0, v4.29.0, v4.31.0, v4.31.1, v4.40.0.
  - `build-release.yml` publishes through NuGet/login with `vars.NUGET_USER` in environment `production` (reviewer `jpiquot`, branch `main`). Builds reads legacy secrets only inside `domain-release.yml`, where callers pass them, so excluding Builds is safe.
  - Push protection is on only for Builds, Commons and PolymorphicSerializations.
  - Module workflows that name legacy secrets: `NUGET_API_KEY` in Agents; `HEXALITH_ZOT_*` in EventStore, Memories, Parties and Tenants; `AZURE_*` in EventStore and Timesheets. `secrets: inherit` callers and unmanaged repos come on top.
- AD conflict: AD-20 has CiCd agents close Dependabot PRs on frozen files, but AD-7's token has no Pull requests write. Built to AD-7 (Precedence), and named as a spine follow-up in the memlog entry.
- `v*` evidence: REST `bypass_actors` accepts `Integration`, but sources disagree on whether `GITHUB_TOKEN` (the GitHub Actions app, 15368) can bypass, so it gets a probe.
- Submodule answer (static reading, 2026-11-08): **yes**, so the spine's `submodules` knob is needed (story 2-3). In package mode, 8 modules read sibling submodules through ungated AppHost or test-host references, sibling sources compiled with no condition, root `.slnx` files that list sibling projects, or tests that read sibling files:
  - ChatBot: EventStore, Platform, Tenants, Parties, Projects, Memories, Commons, FrontComposer, Timesheets.
  - Commons: PolymorphicSerializations (root `.slnx`; `Commons.Standalone.slnx` is clean).
  - Folders: Platform (`AppHost.csproj:33-34`), plus 5 more in the root `.slnx`.
  - Parties: EventStore (test hosts, tests).
  - Platform (stale checkout): EventStore, Memories.
  - Projects: EventStore, Tenants.
  - Tenants: Platform (`AppHost.csproj:34-35`), EventStore (tests), plus `.slnx` siblings.
  - Works: Platform, Parties (`IntegrationTests.csproj:37-63`).

  The other 9 are clean. Gates use `'$(UseHexalithProjectReferences)' == 'true'`, or per-dependency `*FromSource` switches. `SPEC.md:162` ("CI checks out only the Builds submodule") changes with this.

## Tasks & Acceptance

**Execution:**
- [x] `[agent]` org code search -- list the repos whose `.github/` names each legacy secret or uses `secrets: inherit`, and the modules with `codex/*` PRs and their last dates -- the maintainer needs these lists for steps 5 and 8.
- [x] `[agent]` GitHub REST docs -- confirm that AD-7's App permissions (contents, workflows and actions write; administration and security_events read) cover every call AD-6 and AD-18 make, and note any gap -- this is "verify what the App's permissions allow".
- [x] `[maintainer]` 1. Create the App with those permissions, no webhook, installable on this account only, and install it on CiCd and Builds.
- [x] `[maintainer]` 2. Create CiCd `cicd-app` with branch `main` only, no reviewers and no timer, holding secret `HEXALITH_CICD_APP_PRIVATE_KEY` and variable `HEXALITH_CICD_APP_CLIENT_ID`.
- [x] `[maintainer]` 3. Create CiCd rulesets `main` and `delivered/**`.
- [x] `[maintainer]` 4. Builds: delete the 15 orphan tags, cut "Protect main", and add the `v*` ruleset.
- [x] `[maintainer]` 5. Set `claude`, `cursor` and `semgrep-app` to no managed repo, and `chatgpt-codex-connector` to the modules you keep.
- [ ] `[maintainer]` 6. Create the CiCd-agent token and wire it through `GH_CONFIG_DIR` (Decisions).
- [ ] `[maintainer]` 7. Create a pull-only Zot account. Add Actions and Dependabot secrets `HEXALITH_REGISTRY_PULL_USERNAME` and `_PASSWORD` and variable `HEXALITH_NUGET_USER`, all with selected visibility: Builds.
- [x] `[maintainer]` 8. Restrict the legacy secrets to the reader list, never CiCd or Builds.
- [x] `[maintainer]` 9. Set org retention to 90 days and fork approval to all external contributors, and turn on push protection for CiCd, Builds and all 17 modules.
- [x] `[maintainer]` 10. On nuget.org, add the `Hexalith.Builds*` policy for `builds-release.yml` with environment `production`.
- [x] `[agent]` probe on CiCd -- push branch `probe/tag-ruleset` with a push-triggered workflow that creates tag `probe-<run_id>` with `GITHUB_TOKEN` (`contents: write`), under a maintainer-created ruleset that restricts `probe-*` creation. Run once without a bypass actor and once with `Integration` 15368. The answer is yes only if the first run is refused and the second succeeds. The maintainer then deletes the ruleset, and the agent deletes the branch and tags.
- [x] `[agent]` `SPEC.md:162`, `pipeline-stages.md:29`, `enforcement.md:117`, `module-inventory.md`, `.memlog.md` -- record both answers with their evidence (the submodule list per module above), the post-story state, and one memlog event. If the probe says yes, also name the spine follow-up. -- story 1 owns both spine Deferred checks.

**Acceptance Criteria:**
- Given steps 1–10 are done, when the agent runs Verification, then every API-readable item matches the Boundaries, and each mismatch is listed with its item.
- Given an agent session started in this repo after step 6, when `gh auth status` shows the `~/.config/gh-cicd-agent` login and the session runs `git push --dry-run` against CiCd and against Commons, then CiCd is accepted and Commons is refused.
- Given both checks have run, when the companions are read, then `pipeline-stages.md` and `enforcement.md` state each answer with its evidence. If the probe says yes, the spine follow-up "AD-21 adds the `v*` creation rule" is named in the memlog entry.
- Given the items the API can't read (Zot pull-only, the nuget.org policy, token expiry), when the story closes, then each is recorded as maintainer-attested with a date.

## Implementation Notes

**Session 2026-11-08** (agent, read-only, maintainer's `gh` login, since `~/.config/gh-cicd-agent` doesn't exist yet).
- Done: both prep tasks (data below) and the submodule answer in `SPEC.md:162` and `pipeline-stages.md:29`.
- Blocked on the maintainer: steps 1–10. None has started, and the live state re-read today still matches the Code Map. After them come the probe (it needs step 6's token and the probe ruleset), the `v*` answer in `enforcement.md:117`, the dated post-story state in `module-inventory.md`, and the single `.memlog.md` `(event)`. That entry is held back so both answers land in one entry, as the Code Map requires.

**Step 5 data: `codex/*` PRs** (every PR head on the 17 modules, Builds and CiCd, 2026-11-08). None is open. All were pushed to the module repo itself.

| Module | PRs | Last opened | Authors |
| --- | --- | --- | --- |
| EventStore | 27 | 2026-10-09 | `jpiquot` 15, `QuentinDV` 12 (last 2026-05-28) |
| Commons | 2 | 2026-07-01 | `jpiquot` |
| Folders | 1 | 2026-05-11 | `jpiquot` |
| FrontComposer | 4 | 2026-05-05 | `jpiquot` |
| Parties | 2 | 2026-05-04 | `jpiquot` |
| Memories | 1 | 2026-04-30 | `jpiquot` |
| AI.Tools | 1 | 2026-04-26 | `jpiquot` |

No other module, and neither Builds nor CiCd, has a `codex/*` PR. Org-wide there are 42 on 9 repos. The other 4 are on the unmanaged AI.Project and GitDocumentStorage repos, 2 each, the last on 2026-04-26.

**Step 8 data: legacy secret readers.** This is every `secrets.<NAME>` in workflow YAML under `.github/` on the default branch of all 67 non-archived org repos, read on 2026-11-08. No repo uses `secrets: inherit` (the only hits are Builds docs) or reads `secrets` dynamically. The other `NUGET_API_KEY` hits in modules are `steps.nuget-login.outputs.NUGET_API_KEY` (Trusted Publishing), not the secret. Builds names `NUGET_API_KEY` and `HEXALITH_ZOT_*` only in `domain-release.yml`'s `workflow_call` secrets, which Agents passes.

| Secret | Managed modules | Unmanaged repos |
| --- | --- | --- |
| `NUGET_API_KEY` | Agents | Hexalith, Applications, ChatClient, DaprIdentityStore, Documents, Documents_OLD, Domains, Dynamics365Finance, EasyAuthentication_old, EventStores, ExternalSystems, GitStorage, IdentityStores, Inventories, KeyValueStorages, MarkdownEditor, MyNewModule, MyNewPackage, NetAspire, Oidc, Oidc_old, Parties.Old, Sales, Security, Security_OLD, Streams, HexalithApp_old, Hexalith_old |
| `HEXALITH_ZOT_USERNAME`, `HEXALITH_ZOT_API_KEY` | EventStore, Memories, Parties, Tenants | none |
| `AZURE_SUBSCRIPTION_ID`, `AZURE_TENANT_ID` | EventStore, Timesheets | Contacts, Documents_OLD, Security_OLD, semantic-kernel (fork) |
| `AZURE_APPLICATIONID`, `AZURE_APPLICATIONSECRET` | none | Contacts, Documents_OLD, Dynamics365Finance, ExternalSystems, Inventories, Parties.Old, Sales, Security_OLD, HexalithApp_old |
| `SONAR_TOKEN` | none | DaprIdentityStore, Dynamics365Finance, EasyAuthentication_old, ExternalSystems, Inventories, Oidc, Oidc_old, Parties.Old, Sales, Security_OLD, Hexalith_old |

Not covered: workflows that exist only on other branches. Outside step 8: the org variables `AZURE_REGISTRY` and `HEXALITH_ZOT_REGISTRY` are visible to all repos, but they are variables, not credentials.

**REST check: AD-7's App permissions against the calls AD-6 and AD-18 make.** Sources: the docs.github.com pages "Permissions required for GitHub Apps", "Repository rules" and "Releases", read 2026-11-08. Result: **no gap.**
- Contents write, with Workflows write as the extra permission, covers:
  - pushes to modules and to `delivered/<Repo>` (git push, or `POST /git/refs` and `PATCH /git/refs/{ref}`);
  - publishing a draft (`PATCH /releases/{id}`).
- Contents read covers compare, `git/ref`, contents, branches and `releases/tags/{tag}` (the acceptable-tag check). Draft releases are listed only for push access, so publish-ready's Contents write token is also what lets it read the draft.
- Actions write covers `POST /actions/workflows/{id}/dispatches`. Actions read covers workflow runs, one run, jobs, run artifacts, artifact metadata (the digest) and artifact download.
- Administration read covers code-scanning default setup, `automated-security-fixes`, repo retention and `immutable-releases` (AD-18 dispatch).
- Metadata read, which every App gets, covers `GET /rulesets` and `/rulesets/{id}`. `bypass_actors` is returned only to callers with write access to the ruleset, so the App can't read it, as AD-3 says.
- `GET /installation/repositories` and token minting need no permission. Keepalive's enable call and bump-push use `GITHUB_TOKEN`.
- Code scanning alerts read has no caller in AD-6 or AD-18, because the release `codeql` job uses its own `GITHUB_TOKEN`. It is not a gap, so the App keeps it as AD-7 states.

**Data for steps 1, 4 and 7.**
- Step 1: Actions, Contents and Workflows are read and write. Administration and Code scanning alerts are read only. Metadata read is implied. The webhook stays inactive.
- Step 4: the 15 orphan tags were re-checked today and are unchanged. Builds has 211 `v*` tags, 15 of them without a release, and no drafts.
- Step 7: Builds' repo variable `NUGET_USER`, which `build-release.yml` logs in with, is `jpiquot`.

**Verification baseline** (2026-11-08, before steps 1–10). Every item is still open:
- No CiCd App installation exists.
- CiCd has no rulesets and no `cicd-app` environment.
- Builds has only "Protect main", with `deletion`, `non_fast_forward`, `pull_request` and `required_status_checks`, and `jpiquot` (`User` 6775094) can bypass it.
- Org settings: retention 30 days, fork approval `first_time_contributors`, default permission `read`.
- All 8 legacy Actions secrets have visibility `all`. No `HEXALITH_*` secret or variable and no Dependabot org secret exists.
- Push protection is on only for Builds, Commons and PolymorphicSerializations.

**Verification gaps.**
- `GET /user/installations/{id}/repositories` returns 403 with the maintainer's `gh` OAuth token. That endpoint is needed to prove that no `selected` installation writes to CiCd or Builds. For the closing check, try the step-6 token. If it is refused too, the maintainer attests the installation repository lists from the org's GitHub Apps settings, with a date.
- `travis-ci` (app 67, selected repos) is not in the Code Map. It holds `contents: read` and `repository_hooks: write` and is not a Contents, Workflows or single_file writer, so AD-21 doesn't require removing it.

**For the closing memlog `(event)`:** the submodule answer, the probe answer, and the AD-20/AD-7 follow-up from the Code Map. If the probe says yes, it also needs "AD-21 adds the `v*` creation rule". A suggested extra spine follow-up: AD-12's "Only the Builds submodule is checked out" becomes "Builds plus the `submodules` knob".

**Maintainer runbook** (2026-11-08). Order: 1 → 2 → 3 → 6, then the probe can start in parallel with 4, 5, 7, 8, 9 and 10. Every command runs with the maintainer's own `gh` login. `R=repos/Hexalith`.
1. App, in the UI: Org settings → Developer settings → GitHub Apps → New.
   - Webhook: inactive. Repository permissions: Actions, Contents and Workflows read & write; Administration and Code scanning alerts read. Installable only on this account.
   - Generate a private key and note the Client ID and the App ID.
   - Install it on *Only select repositories*: `Hexalith.CiCd`, `Hexalith.Builds`.
2. `gh api -X PUT $R/Hexalith.CiCd/environments/cicd-app -F 'deployment_branch_policy[protected_branches]=false' -F 'deployment_branch_policy[custom_branch_policies]=true'`
   `gh api -X POST $R/Hexalith.CiCd/environments/cicd-app/deployment-branch-policies -f name=main -f type=branch`
   `gh secret set HEXALITH_CICD_APP_PRIVATE_KEY -R Hexalith/Hexalith.CiCd -e cicd-app < key.pem`, then delete `key.pem`. The key exists only in `cicd-app` (AD-7).
   `gh variable set HEXALITH_CICD_APP_CLIENT_ID -R Hexalith/Hexalith.CiCd -e cicd-app -b <client-id>`
3. `gh api -X POST $R/Hexalith.CiCd/rulesets --input -` with:
   - `{"name":"main","target":"branch","enforcement":"active","conditions":{"ref_name":{"include":["~DEFAULT_BRANCH"],"exclude":[]}},"rules":[{"type":"deletion"},{"type":"non_fast_forward"}],"bypass_actors":[]}`
   - `{"name":"delivered","target":"branch","enforcement":"active","conditions":{"ref_name":{"include":["refs/heads/delivered/**"],"exclude":[]}},"rules":[{"type":"creation"},{"type":"update"},{"type":"deletion"},{"type":"non_fast_forward"}],"bypass_actors":[{"actor_id":<App ID>,"actor_type":"Integration","bypass_mode":"always"}]}`
4. Deleting the tags can't be undone:
   - `for t in v4.21.{0..7} v4.22.0 v4.27.5 v4.28.0 v4.29.0 v4.31.0 v4.31.1 v4.40.0; do gh api -X DELETE $R/Hexalith.Builds/git/refs/tags/$t; done`
   - Then `gh api -X PUT $R/Hexalith.Builds/rulesets/19196298 --input -` with `{"name":"Protect main","target":"branch","enforcement":"active","conditions":{"ref_name":{"include":["~DEFAULT_BRANCH"],"exclude":[]}},"rules":[{"type":"deletion"},{"type":"non_fast_forward"}],"bypass_actors":[]}`.
   - Then `gh api -X POST $R/Hexalith.Builds/rulesets --input -` with `{"name":"v tags","target":"tag","enforcement":"active","conditions":{"ref_name":{"include":["refs/tags/v*"],"exclude":[]}},"rules":[{"type":"update"},{"type":"deletion"}],"bypass_actors":[]}`.
5. UI: Org settings → GitHub Apps → Configure.
   - `claude`, `cursor`, `semgrep-app`: *Only select repositories* listing the unmanaged repos you still use them on, or uninstall. None of the 17 modules, Builds or CiCd.
   - `chatgpt-codex-connector`: only the modules you keep (step 5 data above), never Builds or CiCd.
6. UI: your Settings → Developer settings → Fine-grained tokens. Resource owner `Hexalith`, expiry at most 366 days, repositories `Hexalith.Builds` and `Hexalith.CiCd`, and Actions, Contents and Workflows read & write.
   - `GH_CONFIG_DIR=$HOME/.config/gh-cicd-agent gh auth login --with-token < token.txt`, then delete `token.txt`. Don't run `gh auth setup-git`; the global helper already reads `GH_CONFIG_DIR`.
   - Create `.claude/settings.local.json`: `{"env":{"GH_CONFIG_DIR":"/home/administrator/.config/gh-cicd-agent"}}`. It takes effect in sessions started afterwards. Until then the agent prefixes commands with `GH_CONFIG_DIR=…`.
7. Create the pull-only Zot account (read on every repository, no push), then:
   - `gh secret set HEXALITH_REGISTRY_PULL_USERNAME -o Hexalith -v selected -r Hexalith.Builds`
   - Repeat it for `_PASSWORD`, and for both with `-a dependabot`.
   - `gh variable set HEXALITH_NUGET_USER -o Hexalith -v selected -r Hexalith.Builds -b jpiquot`
8. UI: Org settings → Secrets and variables → Actions. On each legacy secret, set *Repository access* to *Selected* with its row of the step 8 table. The value can stay unchanged.
9. `gh api -X PUT orgs/Hexalith/actions/permissions/artifact-and-log-retention -F days=90`
   `gh api -X PUT orgs/Hexalith/actions/permissions/fork-pr-contributor-approval -f approval_policy=all_external_contributors`
   `for r in CiCd AI.Tools Agents ChatBot Conversations EventStore Folders FrontComposer McpCli Memories Parties Platform Projects Tenants Timesheets Works; do gh api -X PATCH $R/Hexalith.$r -F 'security_and_analysis[secret_scanning][status]=enabled' -F 'security_and_analysis[secret_scanning_push_protection][status]=enabled'; done`
   If CiCd or Builds still shows 30 days afterwards, run `gh api -X PUT $R/<repo>/actions/permissions/artifact-and-log-retention -F days=90`.
10. nuget.org → Trusted Publishing → add a policy for owner `Hexalith`, repo `Hexalith.Builds`, workflow `builds-release.yml`, environment `production`, scoped to `Hexalith.Builds*`. Keep the existing `build-release.yml` policy.

**Probe push authorized** by the maintainer on 2026-11-08. The agent pushes `probe/tag-ruleset` to CiCd with the CiCd-agent token once steps 3 and 6 are done, and deletes the branch and the `probe-*` tags afterwards. This is an exception to bmad-build's no-push rule during implementation.

**Session 2026-11-08/09** (attended, option A in the Spec Change Log). The agent made the API changes with the maintainer's `gh` login. It drove the browser-only steps in a separate Windows Chrome profile, where the maintainer signed in and handled 2FA. Each change below was read back through the API or from the settings page.
- **Step 1, the App:** created through the manifest flow.
  - Slug `hexalith-cicd`, App ID 5671811, client ID `Iv23liRwXrNRB9QVzmuh`, private, no events, webhook inactive.
  - Permissions are exactly AD-7: actions, contents and workflows write; administration and security_events read; metadata read.
  - Installation 179966090 is `selected` on `Hexalith.Builds` and `Hexalith.CiCd` only (read from its settings page).
  - The manifest flow also created a client secret. Nothing uses it and it was never stored, so the maintainer may delete it.
- **Step 2:** `cicd-app` has deployment branch policy `main` (id 65975204), no reviewers and no wait timer. It holds secret `HEXALITH_CICD_APP_PRIVATE_KEY`, piped from the manifest conversion, and variable `HEXALITH_CICD_APP_CLIENT_ID`. The local copies were shredded.
- **Step 3:** CiCd ruleset `main` (26812262) has deletion and non_fast_forward, with no bypass. Ruleset `delivered` (26812547) on `refs/heads/delivered/**` has creation, update, deletion and non_fast_forward, with bypass `Integration` 5671811 `always`. GitHub refused that bypass actor (422, "must be part of the ruleset source or owner organization") until the App was installed on CiCd.
- **Step 4:** the 15 orphan tags were checked again and then deleted. All were lightweight, and they can be recreated from these SHAs:
  - v4.21.0 `f3a5c3c8`, v4.21.1 `14ef97cf`, v4.21.2 `cd4333bf`, v4.21.3 `8a3c5baa`, v4.21.4 `041897f0`, v4.21.5 `08b57086`, v4.21.6 `437c4c02`, v4.21.7 `7b0f8101`;
  - v4.22.0 `deabd7e0`, v4.27.5 `23f4798e`, v4.28.0 `bea892ef`, v4.29.0 `08319154`, v4.31.0 `61f632e8`, v4.31.1 `e3be1d4e`, v4.40.0 `0c13c898`.

  "Protect main" (19196298) now has deletion and non_fast_forward, with no bypass. The new `v tags` ruleset (26812219) on `refs/tags/v*` has update and deletion, with no bypass.
- **Step 5** (maintainer's choice, 2026-11-09):
  - `claude`, `cursor` and `semgrep-app` are uninstalled. `cursor[bot]` reviews stop on Platform, Builds, Parties, EventStore and Memories, which had 13, 6, 6, 4 and 1 comments in the last 120 days.
  - `chatgpt-codex-connector` is `selected` on `Hexalith.EventStore` only.
  - Still left: `codacy-production`, `codecov` and `sonarqubecloud` are on all repos, but none holds contents, workflows or single_file write. `travis-ci` is selected on `Hexalith_old` only.
- **Step 6:**
  - The fine-grained token "Hexalith CiCd agent" has owner Hexalith and repositories CiCd (1379430755) and Builds (952945989). It has Actions, Contents and Workflows write, Metadata read and nothing else, and expires on 2027-11-09 (366 days).
  - It was piped from the page into `gh auth login --with-token` under `~/.config/gh-cicd-agent` (files 0600) and never printed.
  - AC-2 dry run with `GH_CONFIG_DIR` set and only the gh credential helper: CiCd accepted, Commons refused with 403 "Permission … denied".
- **Step 7, partial:** `HEXALITH_NUGET_USER` = `jpiquot`, visibility selected: Builds. The Zot pull-only account and the `HEXALITH_REGISTRY_PULL_*` Actions and Dependabot secrets stay with the maintainer, because the Zot server is out of the agent's reach.
- **Step 8:** all 8 legacy secrets are `selected`, matching the step 8 table. Neither CiCd nor Builds is on any list. The org is on the Free plan, where org secrets can't serve private repos, so the dialog doesn't offer the 5 private repos (EasyAuthentication_old, Oidc_old, Parties.Old, HexalithApp_old, Hexalith_old). They had no access before either. Resulting counts:
  - `NUGET_API_KEY` 24;
  - `HEXALITH_ZOT_*` 4 each;
  - `AZURE_SUBSCRIPTION_ID` and `AZURE_TENANT_ID` 6 each;
  - `AZURE_APPLICATIONID` and `AZURE_APPLICATIONSECRET` 7 each;
  - `SONAR_TOKEN` 7.
- **Step 9:** org retention is 90 days (CiCd and Builds also read 90), fork approval is `all_external_contributors`, and the default workflow permission stays `read`. Push protection is `enabled` on all 19 repos. Not in the checklist and left alone: the org's `can_approve_pull_request_reviews` is `true`.
- **Step 10** (nuget.org, in the browser, 2026-11-09): the new policy "Hexalith.Builds builds-release" is Active.
  - Package owner Hexalith, GitHub Actions, repository `Hexalith/Hexalith.Builds` #952945989, workflow `builds-release.yml`, environment `production`.
  - Scope: push new packages and package versions, with glob `Hexalith.Builds*` and no unlist.
  - The existing "Hexalith.Builds" policy (`build-release.yml`, `production`) is kept. Its glob is `*`, so until the rename it can push any Hexalith package ID. AD-21 deletes it after adoption.
- **Browser session:** the debug Chrome was closed, and its profile, holding the GitHub and nuget.org sessions, was deleted.
- **Probe, answer "no":**
  - Run 1, without a bypass actor ([run 42526410704](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/42526410704)): `GITHUB_TOKEN` with `contents: write` was refused both through REST `POST git/refs` (422 "Reference update failed") and through `git push` (GH013 "Repository rule violations").
  - Adding `Integration` 15368 (GitHub Actions) as a bypass actor was rejected by the API: 422 "Actor GitHub Actions integration must be part of the ruleset source or owner organization". The spec counts that rejection as the answer.
  - No `probe-*` tag was ever created. The probe ruleset and branch are deleted.

Probe rulesets, once steps 3 and 6 are done:
- Create: `{"name":"probe-tag-creation","target":"tag","enforcement":"active","conditions":{"ref_name":{"include":["refs/tags/probe-*"],"exclude":[]}},"rules":[{"type":"creation"}],"bypass_actors":[]}`.
- After run 1, PUT the same ruleset with `"bypass_actors":[{"actor_id":15368,"actor_type":"Integration","bypass_mode":"always"}]`. If the API rejects that, the rejection is itself the answer.
- At the end: `gh api -X DELETE $R/Hexalith.CiCd/rulesets/<id>`.

## Spec Change Log

- **2026-11-08, maintainer renegotiation (not a review finding).**
  - Trigger: in an attended session the maintainer asked the agent to make the changes itself and chose option A, which splits the work by what the API can do.
  - Amended: the Always rule "The maintainer makes every org, repo, App, nuget.org and Zot change, including the temporary probe ruleset", and, for this session only, AD-7's "agent sessions never run with the maintainer's personal `gh` login".
    - The agent now makes the API-scriptable changes with the maintainer's `gh` login, while the maintainer watches:
      - step 2;
      - step 3 and the probe ruleset;
      - step 4;
      - step 9;
      - step 7's `HEXALITH_NUGET_USER` variable;
      - the App manifest conversion in step 1;
      - `.claude/settings.local.json` in step 6.
    - The maintainer makes the browser-only changes:
      - creating and installing the App in step 1;
      - step 5;
      - creating the token in step 6;
      - step 7's Zot account and pull secrets;
      - step 8, because `PUT /orgs/{org}/actions/secrets/{name}` requires `encrypted_value`, so visibility can't change without the value;
      - step 10.
  - Avoids: leaving story 1, and every story after it, blocked while the maintainer types API commands an agent can run identically.
  - KEEP: the Boundaries order, the exact AD-21 ruleset set, and the AD-7 token scope. Before deleting anything, the agent checks again that the 15 tags still have no release, and it records each tag's SHA in Implementation Notes so a tag can be recreated. From the moment `settings.local.json` exists, later sessions use only the CiCd-agent token.

## Review Triage Log

## Verification

**Commands:**
- `gh api orgs/Hexalith/installations --jq '.installations[]|{app_slug,repository_selection,permissions}'` -- expected: the App is selected with exactly the AD-7 permissions, and no other writer is on CiCd or Builds (check `GET /user/installations/{id}/repositories`).
- `gh api repos/Hexalith/<CiCd|Builds>/rulesets` plus `/rulesets/{id}` -- expected: exactly the Boundaries set.
- `gh api repos/Hexalith/Hexalith.CiCd/environments/cicd-app` plus `/secrets` and `/variables` -- expected: branch `main` only, no protection rules, and both names present.
- `gh api orgs/Hexalith/actions/permissions/{artifact-and-log-retention,fork-pr-contributor-approval,workflow}` -- expected: 90 days, `all_external_contributors`, `read`.
- `gh api orgs/Hexalith/{actions,dependabot}/secrets` plus `/{name}/repositories` -- expected: `HEXALITH_*` selected and including Builds; legacy secrets selected, with neither CiCd nor Builds.
- `gh api repos/Hexalith/<repo> --jq .security_and_analysis.secret_scanning_push_protection.status` for the 19 repos -- expected: `enabled`.
