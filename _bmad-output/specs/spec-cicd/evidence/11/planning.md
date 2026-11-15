# Story 11 investigation — 2026-11-15

Planning only. No repository settings, remote refs, PRs, workflows, product
files, registrations, or credentials were changed. The initial dirty-tree
checkpoint cleared after the user committed their work.

## Exact starting revisions

| Repository | Revision |
| --- | --- |
| CiCd | `377ac2ebd97ecb6a1b97fe5e2f87a03cdf09e8fa` |
| Builds release `v5.2.2` | `02ed624aa19781cac75d2c9112940e9bd830441a` |
| Commons, local and live main | `fbf4e94233821f6ca336af91a06feaaeb7a16855` |
| PolymorphicSerializations, local and live main | `e97b56930e213f674b64c157551f499b0473ec43` |

All three working trees inspected for this story were clean. CiCd has no
production setup registrations, rendered modules, or live `delivered/*` refs.
The two pilots are one agreed migration wave in `stories.yaml` and
`module-inventory.md`; this story does not extend adoption to other modules.

## Unfinished predecessors

- Story `10-1-module-agent-token.md` remains `status: blocked`. Its latest
  evidence explicitly says the four live qualification operations remain
  unperformed. The protected credential handoff is verified separately.
- Story 10-2 has no implementation story file. The ownership partial still
  says `CI/CD ownership instruction placeholder; replaced by story 10-2.`;
  the deny partial is `[]`; root `AGENTS.md` is absent. Render tests still
  intentionally assert that interim state. Delivering now would install
  incomplete ownership instructions and deny entries.
- Do not bypass these dependencies or count story 11's later branch
  confirmation as the earlier token qualification.

During final readback, the 10-1 story changed externally to `in-progress`,
with staged and unstaged edits. This session did not change or stage that
file. Its recorded live results were still pending at readback; coordinate
with the active prerequisite run rather than launching duplicate probes.

On the next user turn, fresh evidence established that the 10-1 run was
interrupted after three live results. Current-main product branching works;
workflow-changing push and dispatch are refused. Creating an older-workflow
PR head was itself refused, so no actual Update branch operation occurred.
Read-only task status confirmed the interruption. No fourth result or
completed handoff can be inferred. A product-only probe head created before
real delivery would allow a meaningful update afterward, but deferring the
missing preliminary operation changes the four-check prerequisite and needs
an explicit human decision.

The human then selected that deferral. Three verified outcomes and cleanup
now satisfy the prerequisite handoff; meaningful Update branch remains
mandatory at the pilot checkpoint. Story 11 must create its product-only
probe head/PR before actual delivery, then update it after delivery changes
main's workflows. Story 10-2 temporarily prohibits that operation. The
manifest, architecture and current 10-1 contract reflect the decision; the
prior orchestrator status and blocked-run evidence remain historical.

## Live maintainer preflight

`preflight.json` records endpoint results and response status/permission headers.
The default profile stayed `/home/administrator/.config/gh-cicd-agent` with no
`GH_TOKEN` or `GITHUB_TOKEN` override. Both profiles identified `jpiquot`, account
`6775094`; administrative reads used a command-local
`GH_CONFIG_DIR=/home/administrator/.config/gh`. Account `admin: true` was not
treated as token permission evidence. No credential value was printed or saved.

| Check | Commons | PolymorphicSerializations |
| --- | --- | --- |
| Main and public identity | Correct | Correct |
| Ruleset inventory, including parents | Empty | Empty |
| Environment inventory | Only `production` | Only `production` |
| Release kill switch, correct Actions variable route | Exactly `true` | Exactly `true` |
| Artifact/log retention | 90 days | 90 days |
| Code scanning default setup | `not-configured` | `not-configured` |
| Dependabot security updates | `enabled: false` | `enabled: false` |
| Secret-scanning push protection | Enabled | Enabled |
| Immutable releases | Disabled; enable immediately after adoption | Same |
| Draft releases | None | None |

All current tags and releases fit in the requested 100-item inventories.
These `v*` tags have no published release and require an AD-21 assessment of
incomplete legacy release state before tag protection is enabled:

- Commons `v2.30.2` → `6646e37ed4abc380333f11c22908ac40a6b80abf`.
- PolymorphicSerializations `v1.19.4` → `98de6e013840ece9f0fa7c68ab7dcdf2bba3b375`.
- PolymorphicSerializations `v1.19.0` → `5ef1b2773b651c264f1c1506ec4623d35e40e977`.

The CiCd App installation exists with the AD-7 permissions and selected-repo
scope. Its exact repository selection remains **unverified**: under the intended
maintainer profile, `GET /user/installations/179966090/repositories` returned
HTTP 403, “You must authenticate with an access token authorized to a GitHub
App, a personal access token, or basic auth in order to list repositories for
an installation.” This requires an authorized credential for that read or
maintainer attestation from the installation settings, followed by delivery's
own scoped-token checks. No token refresh or scope expansion was attempted.

Both Actions and Dependabot org pull-secret pairs and `HEXALITH_NUGET_USER`
currently select only Builds. Neither pilot has the `hexalith-release`
environment. Their own Zot push identities and package-scoped nuget.org
Trusted Publishing policies cannot be established from GitHub metadata;
maintainer provisioning/evidence is required. Preserve existing policies and
legacy credential access until the actual adoption commit, then perform the
AD-21 immediate cleanup.

The first two variable lookups in the raw report used an invalid route and
prove nothing. The subsequent `/actions/variables` inventories correct that
mistake and establish both kill-switch values.

The user subsequently authorized this session to complete 10-2 and the
required provisioning. Read-only access discovery verified the existing
signed-in Windows Chrome NuGet Trusted Publishing session for `jpiquot`,
including both pilot policy cards; `nuget-access-readback.json` preserves
sanitized visible-page metadata. Existing Kubernetes context `jpiquot@local`
can read registry ConfigMap `registry-distribution/distribution-registry-config`.
Only configuration field names and ACL repository patterns were printed;
no password, cookie, token, private key or registry credential was exposed.
These reads establish available authenticated access, not completed
provisioning or a proof of every write permission. No settings were submitted.

## Delivery compatibility finding

GitHub returned HTTP 200 with `{"enabled":false,"paused":false}` from both
`automated-security-fixes` endpoints, including when explicitly requesting
the controller's API version `2026-03-10`.
`tools/deliver.py:app_checks` currently accepts only the transport's `None`
result for HTTP 404, so it incorrectly rejects the observed disabled state.
`dependabot-disabled-probe.log` reproduces that rejection with every preceding
App check satisfied. Fix and test the controller to recognize a strictly
boolean disabled response, retaining authorization/error rejection and the
existing administrative preflight. Do not change repository settings to hide
the parsing error. The [GitHub endpoint documentation](https://docs.github.com/en/rest/repos/repos?apiVersion=2026-03-10#check-if-dependabot-security-updates-are-enabled-for-a-repository)
identifies the endpoint; the saved live responses establish the observed body.

## Product and runtime map

Both modules pin SDK `11.0.100` with `latestPatch` and
`Microsoft.Testing.Platform`. Preserve those pins. Shared
`Github/lib/ci_pipeline.py` supports MTP and package-mode Release builds.
No Dapr runtime, browser, Windows job, or additional package-mode submodule
dependency was identified. Confirm by executing the package-mode build in a
disposable workspace; never initialize nested submodules in this workspace.

Commons has eight C# test projects: base, Aspire, Diagnostics, Http,
Publication, Serialization, ServiceDefaults and TenantAccess. Its Aspire
tests inspect models/annotations without starting an AppHost. Poly has one
C# test project for its library and code generator. Preserve all product tests.
Neither module contains a security audit waiver. Commons' `NU5104` suppression
is a packaging warning, not a NU190x waiver; leave it intact.

Commons' `scripts/pack-release-packages.py`, `validate-nuget-packages.py` and
`validate-consumer-package-references.py` check the exact 12-package set,
net11 payloads, symbols, version consistency and package-only consumption.
These are product checks. An `after-unit-tests` composite can pack the 12
explicit project outputs without rebuilding or restoring, validate the
packages, then compile only its generated `Consumer.csproj`. Adapt commands
to package-mode Release/audit-off flags; copy the module's `global.json`
into the isolated consumer and keep its NuGet cache inside its own cleaned
temporary directory. No solution-wide custom build/test or tool setup.
Shared release artifacts intentionally exclude symbols, so the current
symbol-requiring validator belongs in CI rather than being run unchanged
against the release artifact.

Both modules also have nearly identical `tools/verify_nuget_release.py`,
`test_verify_nuget_release.py`, and a module-specific `release-packages.json`.
Legacy release workflows run the verifier against the live NuGet feed after
publishing; unit tests cover incomplete feeds, retry/indexing delay, identity,
source commit and authorization failures. Enabling two hooks that call their
tests would make these duplicated sources scanner-reachable. Resolve their
product coverage through shared runtime reuse before enabling hooks; do not
silently discard the live publication guarantee or weaken the scan threshold.

Inspection confirmed that Builds `release_publish.py:push_packages` pushes
with `--skip-duplicate` and then proceeds to finalization without live NuGet
readback. Hoist bounded feed/source verification into that publisher before
`finalize_release`, reusing the authenticated inventory and
`release_draft.py:package_identity`; release Builds before retiring the two
module copies and their unit tests. A module nightly hook executes before
publication, so it cannot replace this product check. With the duplicates
retired, Poly needs no custom hook; Commons retains only its distinct
package/consumer hook. Neither pilot requires a waiver transfer.

The root `package.json` and lockfiles exist only for legacy
semantic-release/commitlint. Product preparation may delete those under the
story's explicit exception. Delivery deletes legacy release/commitlint configs
and workflows. No `.husky/` was found. No direct edit to any owned perimeter
file, including the Builds pointer, is permitted in a module-agent change.

## Implementation and observation boundaries

Use `tools/render.py` and the tagged schema/library, existing render/validate
fixtures, `tools/check_global.py`, `tools/validate.py`, the App delivery report,
and `docs/nightly.md`. Full global checks evaluate committed inputs/render;
verify a local candidate commit before pushing adoption. Product hooks must
exist on live module main before delivery's anonymous validation can pass.

The current delivery message is `build(cicd): apply <accepted-sha> from
Hexalith.CiCd`, while AD-21 describes `build(cicd): adopt Hexalith.CiCd`.
Record actual messages and authenticate adoption by report/ref/parent/tree
identities. Do not introduce a message-only runtime change to prove adoption.

After real delivery, repeat the two branch operations using only the protected
module credential. Record delivery and current base revisions, successful
product-only push and meaningful workflow-different PR Update branch outcome,
then close/delete every probe without merging. Confirm or correct the 10-2
restrictions. Wait for a real scheduled nightly and its CodeQL, release,
Builds bump/no-bump and delivery outcomes; manual dispatch or fixtures cannot
substitute for the story's real-night checkpoint.
