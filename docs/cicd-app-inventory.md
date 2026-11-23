# CiCd App source inventory and hosted reconciliation

The reviewed source contains seven App-consuming workflows, ten privileged jobs
and 78 token-mint steps. The package visibility matrix executes its
single mint once for each of two fixed owners. All tokens name owner `Hexalith`.
The [reviewed policy](../tools/app-workflow-policy.json) records each exact job,
condition, environment, token step, action pin, repository selection and requested
permission. A passing source check establishes this inventory; hosted settings
and owner retirement decisions have separate evidence below.

| Workflow | Privileged job | Mint steps | Repository and requested permissions |
|---|---|---:|---|
| `deliver.yml` | `deliver` | 19 | CiCd: Contents/Workflows write, Actions read; 17 module slots: Contents/Workflows write and conditional Administration read; manual Projects catalog: Contents/Workflows write |
| `nightly.yml` | `dispatch` | 21 | Three CiCd barrier mints with Actions read. 18 target slots with Actions write and Administration read except for Builds. |
| `nightly.yml` | `wait` | 9 | Pending dispatched targets: Actions read |
| `nightly.yml` | `publish-ready` | 18 | One successful target per slot: Contents/Workflows write, Actions read |
| `nightly.yml` | `delivery-wait` | 4 | CiCd and authorized module delivery targets: Actions read |
| `qualify-package-owner-access.yml` | `qualify` | 1 | One fixed matrix owner, EventStore or Projects: Contents read |
| `propose-eventstore-contracts-prerequisite.yml` | `propose` | 2 | EventStore branch: Contents/Workflows write; optional separate draft-PR token: Contents read, Pull requests write |
| `deliver-contracts-prerequisites.yml` | `deliver` | 2 | EventStore/Projects publisher: Contents/Workflows write; Projects pins/policy: Contents write |
| `dispatch-contracts-prerequisites.yml` | `dispatch` | 1 | One selected EventStore/Projects owner: Actions write, Contents read |
| `deliver-projects-ci-gates.yml` | `deliver` | 1 | Projects nine-file repair: Contents write |

## Source enforcement

Run `run-with-temp uv run --locked --script tools/check_app_inventory.py`.
`tools/check_global.py` invokes the same secret-free check before the other global
checks; failure contributes to the existing global verdict and later checks
still run. The module verdict shape and accepted-source repair behavior remain
unchanged. Module workflows, generated perimeters and product gates are unchanged.
The parent tool-suite discovery includes the locked mutation suite.

Discovery parses every parent `.yml` and `.yaml`, including case variants,
using the renderer's strict, duplicate-rejecting YAML reader. Either an
environment **name** equal to `cicd-app` or an App-key reference independently
identifies a consumer. Reviewed paths use lowercase extensions. Global workflow
lint reports case variants in parent and rendered paths because pinned zizmor
requires lowercase extensions. Unrelated names such as `cicd-app-preview` and
environment URL text do not select the App.
Dynamic environment names and unresolved computed `secrets[index]` expressions
fail closed because their runtime value could select the environment or key.
Literal references to unrelated secrets remain allowed. An unreviewed job-level
reusable workflow call also fails, with or without `secrets: inherit`: its callee
can select its own environment without naming it in the caller. Any future
allowed call requires an explicitly reviewed dependency-job digest and review of
the callee's environment/secret boundary; the current inventory has no such calls.
Discovery matches case-insensitively, including mixed-case secret references;
reviewed source values still require their exact spelling.
Key references outside jobs fail. Missing consumers, unknown jobs, changed token
identities, omitted permissions and additional inputs all fail with the responsible
workflow/job/step or field. Malformed input and nonregular files fail closed.

The policy records complete workflow context, job boundaries and explicit token
steps, including all manual input choices and the visibility matrix. Semantic
SHA-256 digests bind non-token selector/consumer steps and prerequisite jobs;
comments and YAML formatting do not alter these digests. Controller source hashes
bind the candidate controller implementations. Delivery slot selection is the
exception: the `deliver` job runs `delivery_bootstrap.py` and its sibling
`delivery_runtime.py` from the literal commit pinned in its bootstrap checkout
step, so that step's digest binds the selector. The working-tree hashes bind the
candidate `deliver.py` and `delivery_runtime.py` that the bootstrap exports and
runs after a passing candidate verdict. This conservative boundary
requires renewed policy review when controller bytes or this execution context
change. There is no checker option that regenerates or approves a policy.

Dynamic selectors retain their existing limits:

- Delivery selects at most 17 validated module names from the committed setup
  registry and valid ancestral `delivered/<Repo>` refs. Candidate validation or
  an accepted historical source selects trusted tools; Builds is excluded from
  module names. Administration read is requested only for candidate registry checks.
- Nightly selects at most 17 committed registered modules plus fixed Builds,
  giving 18 target slots. State and handoffs are validated against that inventory.
  Poll tokens cover only pending targets. Publishing selects successful targets.
- Delivery propagation reads CiCd plus at most 17 modules from the confirmed
  bump registry and independently validated delivered refs.
- The four prerequisite profiles are `eventstore-publisher`, `projects-publisher`,
  `projects-pins` and `projects-prerequisite-policy`. The first two select one
  named publisher with Workflows write; the latter two select only Projects
  Contents write. Dispatch owner choices are `eventstore`/`projects`, and operation
  choices are `publish`/`verify`. Catalog and `ci-gates` retain separate closed
  Projects path lists and full-writer exclusion checks.

Expression equality alone is insufficient to establish runtime targets. The
policy therefore binds the workflow producers and the trusted controller source;
existing controller suites continue to qualify their accepted-registry, state,
transport and time-budget behavior.

## Renewing the reviewed policy

1. Review the source change and its complete selector/callee context. Confirm
   workflow/job identity, conditions, environment, App identity, repository owner
   and selection, every requested permission/input, matrix/manual choices and
   runtime bounds. Preserve product gates and pending owner retirement conditions.
   Record the full 40-character commit of the reviewed bound source as
   `reviewed_revision`; it identifies source reviewed before the policy update.
2. Parse YAML with `tools/render.py`'s `yaml_document`. For semantic digests use
   `check_app_inventory.semantic_digest(value)`, equivalently SHA-256 of UTF-8
   `json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"),
   allow_nan=False)`. Hash the complete non-token step or dependency-job mapping.
   Workflow context excludes `jobs`; privileged-job boundary excludes `steps`.
   Keep each full token mapping and its actual zero-based step index explicit;
   indices across token/context entries must cover the complete step list.
   For each trusted selector, hash its exact file bytes with SHA-256 and review
   the accompanying human-readable `bound` statement.
3. Manually edit only the reviewed entries in `tools/app-workflow-policy.json`.
   Review the source and policy diffs together, including added/removed consumers,
   changed hashes and unchanged expression producers. The checker has no policy
   regeneration or approval mode; calculating a digest supplies no scope approval.
4. Run the locked inventory checker and mutation suite under `run-with-temp`,
   the affected controller/workflow suites, validation compatibility and renderer
   checks. Record the source revision, candidate identities and compact results;
   refresh separate hosted observations if the reviewed App boundary needs them.

## Hosted observations on 22 November 2026

At 17:07 UTC, the organization installations API returned HTTP 200 for App
`hexalith-cicd`, App ID `5671811`, installation `179966090`, with
`repository_selection: all` and `suspended_at: null`. **All repositories**
covers current and future Hexalith repositories. The installation grants Actions,
Contents and Workflows write, and Administration, Metadata and Code scanning
alerts (`security_events`) read. The environment's nonsecret
`HEXALITH_CICD_APP_CLIENT_ID` matched the installation client ID.
The custom deployment policy allows the single branch `main`.
[Implementation receipt](../_bmad-output/specs/spec-cicd/stories/30-3-reconcile-organization-wide-cicd-app-access.md#hosted-verification)

For hosted mode, read `GET /orgs/Hexalith/installations` and match installation
`179966090`, the App identity, `repository_selection` and suspension state. Check
the effective grants, environment client ID and deployment branch policy in the
same readback. For source token scope, run the offline inventory check above.
Each reviewed job explicitly selects repositories and permissions. AD-3 still
requires delivery to check the adoption candidate using its scoped token.

### Earlier selected-mode readback

The [story 30-1 receipt](../_bmad-output/specs/spec-cicd/evidence/30-1/hosted-readback-20261122.json)
records the earlier observation, HTTP statuses, request IDs, response/body
hashes, source commit/tree/workflow blobs, account and effective profile.
Both readbacks used the command-local maintainer profile for interactive reads,
with `GH_TOKEN` and `GITHUB_TOKEN` unset.

AD-7 keeps the CiCd-agent token for interactive sessions and keeps the
maintainer's personal `gh` login out of agent sessions. Its one exception is a
read-only GET that the user explicitly authorizes in an interactive session, run
with command-local `GH_CONFIG_DIR=/home/administrator/.config/gh` and
`GH_TOKEN`/`GITHUB_TOKEN` unset. These readbacks used that exception.
Unattended BMAD Loop sessions currently run with the CiCd-agent profile; that is
a recorded deviation from AD-7 awaiting a separate decision, not an approved use.

- Environment `cicd-app` returned HTTP 200 with custom deployment-branch policy
  enabled and protected-branch policy disabled. Its one protection rule is branch
  policy; the branch list contains exactly one entry, `main`, type `branch`.
  No reviewer or wait-timer rule was returned. Admin bypass is enabled
  (`can_admins_bypass: true`): administrators can force deployments past
  configured protection rules, and this readback does not establish whether that
  extends to the branch policy. It is not counted as main-only proof for
  administrators; it falls within the accepted residual that org owners can reach
  the key through `main`. No setting was changed.
- The earlier organization installation response reported selected-repository
  mode, with the same App identity and grants as the later readback.
- The nonsecret environment variable `HEXALITH_CICD_APP_CLIENT_ID` matched that
  installation's `client_id`, binding the variable used by every reviewed mint
  to live App `5671811` / installation `179966090`. A separate repository-variable
  GET returned HTTP 404 and is retained without inferring absence; the readable
  environment value establishes the identity binding independently.
- The selected-repository API returned HTTP 403. Its exact endpoint, message,
  request ID and digests are in the receipt. The full membership of the earlier
  selected set remains unverified. The later HTTP 200 establishes the current
  installation mode through the organization endpoint.
- The optional EventStore PR token requests Pull requests write, which the
  effective installation grants do not include. Its retained `pr-blocked` receipt
  agrees with that limitation.
- [Story 11](../_bmad-output/specs/spec-cicd/stories/11-pilot-migration-commons-and-polymorphicserializations.md#current-ad-7-and-ad-21-readback--2026-11-22)
  verified required membership and recorded `Hexalith.Docs` as an extra grant
  under the selected-mode policy. The 22 November decision makes that coverage
  ordinary under AD-7 and resolves the selected-mode exception prospectively.
  [Approved change](../_bmad-output/planning-artifacts/sprint-change-proposal-2026-11-22.md)

The visibility diagnostic uses inline `python3 -` without `-I`, a discrepancy
against AD-7's isolated `python3 -I` controller rule. Its exact source is retained
in the policy; source-inventory acceptance does not certify that exception away.
Nightly's four App jobs each also run two short isolated `python3 -I -c` steps,
seeding conservative state and reporting an unavailable checkout, and the
prerequisite `dispatch` job initializes its failure receipt with an isolated
`python3 -I -` heredoc. These snippets use only the standard library and run
isolated, but they are not files under CiCd's `tools/`: a literal deviation from
AD-7's wording. The policy binds their exact text through step digests. The
remaining known discrepancy is the ungranted optional PR scope above.

## Migration owner dispositions

The [approved 19 November proposal](../_bmad-output/planning-artifacts/sprint-change-proposal-2026-11-19.md#app-key-inventory),
[owner routes](contracts-prerequisites/owner-routes.md),
[Projects repair](projects-ci-gates-repair.md) and named
[approver scope](contracts-prerequisites/approver.json) provide scoped historical
authority. None supplies retirement consent. Every route/profile below is
**retained pending its owner's explicit confirmation**. Standing delivery and
nightly remain owned by the CiCd maintainer.

The [artifact reconciliation](../_bmad-output/specs/spec-cicd/evidence/30-1/hosted-route-artifacts-20261122.json)
binds authenticated run/artifact identities, GitHub archive digests, matching
download hashes and compact extracted receipt hashes. Artifact-list requests
retain request IDs and response/body digests, and every artifact's authenticated
`workflow_run` binding matches its selected run. It retains failures as well
as successes. These historical results establish only the stated observations.

| Route/profile | Owner | Retained result or discrepancy | Exact condition before removal |
|---|---|---|---|
| Package visibility / EventStore | EventStore package owner with CiCd maintainer | [Run 43984971766](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/43984971766): one-target Contents-read result qualified; inline isolation discrepancy remains | Both package owners retain their visibility results, finish using this diagnostic and explicitly confirm retirement; one matrix job serves both owners |
| Package visibility / Projects | Projects package owner with CiCd maintainer | Same run: separate Projects one-target result qualified | Both package owners retain their visibility results, finish using this diagnostic and explicitly confirm retirement; one matrix job serves both owners |
| EventStore proposal / branch and optional PR | EventStore owner with CiCd maintainer | [Run 44048869488](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/44048869488): branch proposed; optional PR `pr-blocked`, no scoped PR token | Named proposal is resolved and EventStore owner explicitly confirms the route is no longer needed |
| `eventstore-publisher` | EventStore owner with CiCd maintainer | [Run 44040325658](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/44040325658): qualified, direct push failed with ambiguous remote outcome; proposal route is separate | EventStore and Projects owners reconcile the approved publisher, pin and policy results and identify the last live profile; the EventStore owner explicitly confirms this profile's retirement |
| `projects-publisher` | Projects owner with CiCd maintainer | [Run 44040329397](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/44040329397): delivered `8b53d6b917957762949d39c21bc5de0919811413`; delivery is not final publication acceptance | EventStore and Projects owners reconcile the approved publisher, pin and policy results and identify the last live profile; the Projects owner explicitly confirms this profile's retirement |
| `projects-pins` | Projects owner with CiCd maintainer | Approved signed-archive and exact pin perimeter retained; no matching hosted delivery receipt in the sampled runs | Both signed prerequisite archives and the approved pin result are verified; EventStore and Projects owners reconcile the publisher, pin and policy results and identify the last live profile; the Projects owner explicitly confirms this profile's retirement |
| `projects-prerequisite-policy` | Projects owner with CiCd maintainer | [Run 44047185889](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/44047185889): delivered `78633a653c1a6768a795678203d836b3caac2c12` | EventStore and Projects owners reconcile the approved publisher, pin and policy results and identify the last live profile; the Projects owner explicitly confirms this profile's retirement |
| Dispatch / EventStore publish | EventStore and Projects owners; EventStore selected | Fixed release profile and source retained; no sampled corresponding dispatch receipt | EventStore and Projects owners accept their final prerequisite publication or verification receipts; the EventStore owner explicitly confirms retirement of this route |
| Dispatch / EventStore verify | EventStore and Projects owners; EventStore selected | Fixed verification profile retained; no sampled corresponding dispatch receipt | EventStore and Projects owners accept their final prerequisite publication or verification receipts; the EventStore owner explicitly confirms retirement of this route |
| Dispatch / Projects publish | EventStore and Projects owners; Projects selected | [Run 44047986587](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/44047986587): dispatch `correlated`; release completion unproven here | EventStore and Projects owners accept their final prerequisite publication or verification receipts; the Projects owner explicitly confirms retirement of this route |
| Dispatch / Projects verify | EventStore and Projects owners; Projects selected | [Run 44050298566](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/44050298566): dispatch `correlated`; publication verification completion unproven here | EventStore and Projects owners accept their final prerequisite publication or verification receipts; the Projects owner explicitly confirms retirement of this route |
| Projects `ci-gates` repair | Projects owner with CiCd maintainer | [Run 43951248000](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/43951248000): nine-file repair delivered `7da7e95b670838de3181e946709e1246695a0e72`; local/hosted delivery success is not owner CI/Commitlint/G-6 acceptance | Projects owner accepts hosted CI, Commitlint and G-6 for repaired source and explicitly confirms retirement |
| Delivery `projects-g6-catalog` | Projects owner with CiCd maintainer | [Run 43939511545](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/43939511545): catalog delivered `146d0f7e9964c82da23d31b51e6ab62efdcfdda6`; later sampled G-6 runs 43967083172 and 43982007709 failed despite acquisition receipts marked prepared | Projects owner confirms the catalog consumer has retired and explicitly approves removing this fixed profile |

Every listed route remains pending the owner's explicit retirement confirmation.
A missing sampled receipt remains pending evidence. Story 11's completed pilot
and historical decisions are recorded in its own receipts.
