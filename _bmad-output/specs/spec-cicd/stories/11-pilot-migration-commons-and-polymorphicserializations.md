---
title: 'Pilot migration: Commons and PolymorphicSerializations'
type: 'chore'
created: '2026-11-22'
status: 'done'
baseline_revision: '9f7a56fd1e0de05f6b8a8789fba983c072ce3db6'
review_loop_iteration: 0
followup_review_recommended: false
context:
  - '{project-root}/_bmad-output/specs/spec-cicd/evidence/11/planning-context-20261122.md'
warnings: [oversized]
deferred:
  - 'CiCd App 179966090 also selects Hexalith.Docs.'
  - 'Nine other repositories have active NuGet wildcard policies that overlap the pilot package IDs.'
---

<intent-contract>

## Intent

**Problem:** Story 11 has no id-keyed record, although its legacy spec records completed pilot migration and checkpoint acceptance. Reconcile that evidence against the requested AD-21 sequence and current maintainer state before affirming the checkpoint; live App installation scope has drifted.

**Approach:** Check maintainer preconditions first, preserve authenticated completed work, resolve the current precondition failures, and validate the actual pre-delivery/post-delivery restricted-token proofs and existing nightly receipt. This invocation stops after planning.

## Boundaries & Constraints

**Always:** Preserve the original approved legacy intent and dated acceptance. Separate historical proof, current observations and unverified access. Module product writes use only `/home/administrator/.config/gh-module-agent/token`; CiCd/Builds writes use CiCd-agent. Explicit interactive maintainer administration uses command-local `GH_CONFIG_DIR=/home/administrator/.config/gh`; unattended work must stop at any maintainer-only boundary. Preserve foreign policy content, SDK pins, all product tests and later product improvements. Use `run-with-temp` for disposable jobs, standalone module copies and outputs beneath its `$TMPDIR`; wait for children. Keep only identities, digests, decisions and links in evidence; executable procedures belong under `tools/`.

**Never:** Edit owned module files/portions directly; mutate owned content or a module `main` ref during probe operations; merge probe PRs; broaden module credentials; obtain the App key; weaken audits/tests, add skips/trailers, or add module workflow-text tests. Do not repeat completed adoption, recreate a pre-adoption timeline, restore legacy credentials, or remove another repository's grants. Historical acceptance must prove the original sequence: module-agent product cleanup → CiCd-agent Builds `Props/` waivers where needed → acceptable released `builds-version` containing them → product-only pre-delivery probe → one CiCd submodule/setup/render commit → actual delivery → immediate maintainer immutable-release/legacy-credential cleanup → post-delivery probes → policy qualification → nightly acceptance. Repair any current gaps under the already-adopted procedure.

</intent-contract>

## Code Map

- `../evidence/11/planning-context-20261122.md` — investigation, exact baseline/probe/delivery identities, current AD-21 findings and evidence digests; implementation map for this handoff.
- `_bmad-output/implementation-artifacts/spec-11-pilot-migration-commons-and-polymorphicserializations.md` — historical `done` authority, approved pilot-only pre-adoption substitute and 2026-11-19 checkpoint. Preserve its frozen contract and completed tasks.
- `../SPEC.md`, companions and architecture spine AD-7/AD-21 — ownership, credentials and sequence. All 29 other id-keyed stories are done; use later dated results over historical blocked/planning notes.
- `references/Hexalith.Commons/.github/actions/after-unit-tests/action.yml`, `references/Hexalith.Commons/scripts/{pack-release-packages,validate-nuget-packages,validate-consumer-package-references}.py` — retained product packaging/consumer checks; preserve twelve payload/symbol pairs and isolated consumption.
- `references/Hexalith.PolymorphicSerializations/.github/actions/after-unit-tests/action.yml`, `references/Hexalith.PolymorphicSerializations/scripts/validate-readme-sample.py` — later retained product hook; preserve it. Both pilots' tool-only root npm manifests are already removed; no original `.husky/` or NU190x waiver existed. Preserve Commons' distinct NU5104 packaging treatment.
- `references/Hexalith.Builds/Props/Directory.Packages.props`, `builds-version`, `setup/Hexalith.{Commons,PolymorphicSerializations}.yml`, `rendered/` — central audit treatment, current exact `v6.6.1`, both solution/hook selections and owned desired state. Read schemas/runtime from the selected release, not the mutable Builds checkout.
- `templates/partials/ownership-block.txt.j2:25`, `tools/tests/test_render.py`, `10-1-module-agent-token.md` and `10-2-agent-instructions-and-deny-entries.md` beside this story — already corrected Update branch rule and qualification addenda. Author any necessary correction here and deliver it.
- `tools/nightly_acceptance.py:749`, `docs/nightly.md` — GET-only run/artifact judgment and small identity receipt; use the completed pilot run, not a new release dispatch for this reconciliation.

## Tasks & Acceptance

**Execution (resumed 2026-11-22, with readback and maintainer acceptance below)**

- [x] `../evidence/11/planning-context-20261122.md` and new identity receipts beside it — refresh AD-21 inventory before checkpoint work. In an explicitly authorized interactive maintainer session, repair Cursor installation `182926560` to exclude managed repositories and connector `77847816` to the modules that use it, excluding CiCd/Builds; preserve unrelated installation selections. Verify CiCd App `179966090` membership through available authorized settings access. Preserve exact 403 if access remains unavailable; do not switch tokens to evade it. The maintainer acceptance below records the additional CiCd App grant.
- [x] `../evidence/11/` — authenticate current main-only `hexalith-release`, both module-specific Zot ACLs and environment binding using provisioning identities without exposing credentials; verify sole scoped NuGet policies `27048`/`27049`, package IDs, `release.yml`, environment and legacy key scope through authenticated NuGet access. Reconcile legacy key `954800` as expired/unmapped unless actual scope proves otherwise. Preserve historical additive-then-cleanup order, complete legacy-org-secret exclusions and narrow legacy Zot no-op. Verify stale CodeQL/draft/tag inventory, exact rulesets, scan/security settings, grants and retention. Record each success, failure and unverified item separately. The maintainer acceptance below records the cross-repository NuGet policy overlap.
- [x] `../evidence/11/` and the legacy completed spec — verify product cleanup, retained hooks/tests, central waiver disposition and acceptable release pin from exact source trees. Both pilots are already adopted; use the normal standalone `python3 references/Hexalith.Builds/check.py` before any new module push. If a genuine product gap exists, fix only its module-owned source with the restricted credential after fresh-main qualification; central policy changes belong in CiCd/Builds. Do not invent waivers or rerun registration just to populate this record.
- [x] `../evidence/11/` — revalidate historical base/head/preparation/adoption/update objects and HTTP outcomes from the digest-bound sources in the companion. Verify pre-delivery workflow equality, actual delivery workflow difference, fresh post-delivery branch parent and successful push, both Update branch HTTP 202 responses and exact resulting workflow/owned-tree imports. Bind the evidence to the restricted credential source, not account `admin:true`. Confirm PRs 52/19 remain closed unmerged and all recorded disposable refs absent. Keep the stale `remote_push_performed:false` discrepancy visible with the successful server readbacks; preserve raw historical files.
- [x] `templates/partials/ownership-block.txt.j2`, `_bmad-output/specs/spec-cicd/stories/10-2-agent-instructions-and-deny-entries.md` and this story — confirm the published correction matches the actual allowance: GitHub permits importing workflows via Update branch with the restricted token, while agent policy forbids using it for owned CI/CD changes and requires a fresh-main product branch. Preserve observed commitlint failure on service-generated merge subjects; do not claim those probe heads passed product tests. Change canonical text/tests/render only if an actual mismatch remains, then validate and deliver through the normal path.
- [x] `tools/nightly_acceptance.py` and a new compact receipt under `../evidence/11/` — read-only rejudge run `44566082537` for both pilots and `--checkpoint pilot`; bind authenticated artifacts, release CodeQL, release-or-nothing results, scan rows, bump/delivery and keepalive. Record unrelated module failures without using them to reject passing pilot rows. Evidence/access failure remains unverified and never becomes a fabricated new success. Record the reconciliation decision and any exceptions expressly accepted by the maintainer.

**Acceptance Criteria:**

- Given the existing adopted pilots and current App-scope drift, when maintainer checks and repairs finish, then recorded server state satisfies AD-7/AD-21, each module retains its own main-only publish identity and sole package-scoped NuGet policy, and all unavailable checks remain explicit until resolved.
- Given the original migration evidence, when its exact sources and delivery are authenticated, then product gates/tests survive, forbidden tooling and module audit waivers are absent, any necessary shared waiver predates the selected Builds release, and submodule/setup/render adoption and immediate cleanup are proved in order without another adoption.
- Given each unchanged-workflow pre-delivery probe and its real delivery, when the restricted-token server evidence is validated, then fresh post-delivery product pushes and actual Update branch 202 imports are distinguished from fixture-creation refusal and merge-subject CI failure, with full canonical revisions, no probe merge/main mutation and complete cleanup.
- Given the verified server allowance, when canonical and delivered 10-2 instructions are checked, then they accurately state that allowance and prohibit importing owned CI/CD through Update branch while directing agents to fresh-main product branches.
- Given authenticated nightly `44566082537`, when both pilots and the pilot checkpoint are judged, then each pilot's CodeQL, release-or-nothing and scan evidence passes, bump/delivery and keepalive satisfy the checkpoint, and the resulting decision preserves the dated historical acceptance without claiming this planning run implemented anything.

## Earlier execution revalidation — 2026-11-22

The [execution reconciliation](../evidence/11/execution-reconciliation-20261122.md)
and compact receipts record completed source/probe/policy qualification and
read-only nightly rejudgment. Tasks 3–5 pass without changing product or policy
source. Both selected nightly rows and the pilot checkpoint pass, exit 0;
final reconciliation in task 6 remains gated by current prerequisites.

Tasks 1–2 remain incomplete: Cursor and connector retain all-repository scope;
CiCd App membership GET returns authenticated HTTP 403 and its settings browser
requires Confirm access; refreshed NuGet redirects to Sign In. Current sole
policy/package/key scope remains unverified. No installation selection is
changed, and no connector module selection is inferred. Existing settings,
Zot ACLs, grants, stale release/tag/CodeQL inventory and the immutable release
pin otherwise qualify. The legacy `done` spec and original evidence remain
unchanged. No renewed checkpoint acceptance is asserted.

## Current AD-7 and AD-21 readback — 2026-11-22

The [maintainer repair receipt](../evidence/11/ad-7-ad-21-maintainer-repair-20261122.json)
records authenticated settings and NuGet readbacks, repository and source
identities, and request and readback digests. Receipt SHA-256
`f67ac3de9ace8527817e746558214daeb49b8abfdd3e7489dc49f31333d4942d`.

- Saved and reloaded Cursor installation `182926560` with all 48 unrelated
  repositories. It excludes the 17 modules, Builds and CiCd. Saved and
  reloaded Codex connector `77847816` with the same 48 unrelated repositories
  plus `Hexalith.EventStore`, the only managed module in the maintainer's
  recorded allowlist. Both installations report selected scope through the
  maintainer API. [Allowlist decision](1-maintainer-preconditions-and-remaining-checks.md#implementation-notes)
- The CiCd App `179966090` settings reload confirmed all 19 required
  repositories following the maintainer API's HTTP 403. The page also lists
  `Hexalith.Docs`. Required inclusion passes. The additional grant remains
  open against the AD-7 repository scope and was outside the authorized
  repairs. [AD-7](../../../planning-artifacts/architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md#ad-7--credentials)
- The refreshed NuGet inventory for `jpiquot` shows one active push-only policy
  per pilot repository. Commons policy `27048` covers all 12 Commons IDs
  through `Hexalith.Commons*`. Policy `27049` covers
  `Hexalith.PolymorphicSerializations` through
  `Hexalith.PolymorphicSerializations*`. Both bind `release.yml` and
  `hexalith-release`, which match the exact GitHub workflow blobs and main-only
  environment settings. Legacy key `954800` is **Expired**, with owner
  `Hexalith`, glob `Hexalith.*` and push scope for new packages and versions.
  Its GitHub secret mapping remains unverified.
- Nine active policies for other repositories have a `*` push scope under
  the same `Hexalith` package owner. This includes EventStore policy `16915`.
  Those scopes overlap the pilots' package IDs, so AD-7 publishing isolation
  remains open. [NuGet policy scopes and ownership](https://learn.microsoft.com/en-us/nuget/nuget-org/trusted-publishing#select-scopes)

The repair receipt records the blocked verdict at the end of verification.

## Maintainer acceptance — 2026-11-22

After reviewing the repair results and the two open findings, the maintainer
responded `accept`. Story 11 is done with the `Hexalith.Docs` App grant and the
nine overlapping wildcard policies recorded as open AD-7 exceptions for this
acceptance. The authenticated CiCd App settings readback established required
membership, and the authenticated NuGet readback established the pilot policies
and the expired key's configured scope. The November 19 pilot acceptance and
run `44566082537` remain the historical checkpoint.

## Spec Change Log

## Review Triage Log

## Design Notes

Execution resumed 2026-11-22 by explicit user invocation. The user authorizes AD-21 maintainer administration in this interactive session with the command-local maintainer profile; ordinary CiCd and module operations retain their designated identities. Check maintainer preconditions first. Preserve existing completed adoption and qualify historical proofs rather than recreating their sequence. Resolve only scoped, authorized settings changes whose exact desired selections are established; access refusals remain unverified and halt dependent acceptance. The existing untracked story and planning companion are supplied planning inputs, not unrelated changes.

This is a planning handoff for reconciling an existing completed checkpoint. The legacy `done` record remains unchanged. Known live administration failures become explicit execution tasks; `ready-for-dev` means the plan is actionable, not that AD-21 currently passes or that a second checkpoint has been accepted. Initial product preparation/adoption tasks have authenticated historical completion; they must not be repeated to resolve story placement.

## Verification

- Before each applicable new module push: from its clean standalone committed module root, `run-with-temp python3 references/Hexalith.Builds/check.py`; require exit 0 and unchanged owned inputs, exact source/dependency identities and complete message validation.
- For a genuine canonical policy change: `run-with-temp uv run --locked --script --python 3.12 tools/tests/test_render.py`, renderer `--check` and the scope-appropriate committed validator. Expect policy/preservation tests and actual per-module verdicts to pass. No runtime change or broad test run is required solely for this documentation reconciliation.
- Read-only acceptance under CiCd-agent: `run-with-temp python3 -I tools/nightly_acceptance.py --run 44566082537 --module Hexalith.Commons --module Hexalith.PolymorphicSerializations --checkpoint pilot --receipt _bmad-output/specs/spec-cicd/evidence/11/checkpoint-revalidation-receipt.json`; expect exit 0, both module verdicts and checkpoint `pass`, or preserve the exact failed/unverified result. Keep stdout logs in scratch and record digest/result.

## Auto Run Result

Earlier automated verdict: blocked
Blocking condition: current AD-7/AD-21 App installation scope fails; CiCd App membership requires authenticated settings access (HTTP 403 / Confirm access); refreshed NuGet requires Sign In, leaving current sole-policy/package-ID and legacy-key scope unverified.

Execution result — 2026-11-22: the rendered entrypoint ran exactly once for this invocation. One implementation subagent completed the independently executable reconciliation. Tasks 3–5 passed; tasks 1–2 and final acceptance in task 6 remain incomplete. Nightly `44566082537` rejudgment passes both pilots and the pilot checkpoint, and renderer `--check` passes. Exact historical restricted-token probe, delivery, Update branch HTTP 202 and cleanup proofs are revalidated. The published 10-2 correction is accurate and needs no source change. Historical acceptance remains preserved; this run does not renew it. No remote mutation, credential change, product change, probe replay, dispatch, adoption, commit or push occurred. See [execution reconciliation](../evidence/11/execution-reconciliation-20261122.md) for exact settings failures, revisions, digests and required access.

Prior planning result: ready-for-dev

Halted after planning as explicitly requested, 2026-11-22. The rendered bmad-build-auto entrypoint ran exactly once; three investigation subagents completed and their findings are recorded in the companion. The ready-for-development gate passed after rereading the workflow and saved spec. Checked planning YAML, canonical root baseline, unique story path, intent-contract delimiters, six unchecked execution tasks, five Given/When/Then acceptance criteria, nine historical evidence digests, file size/whitespace and unchanged legacy spec identity.

Execution prerequisites remain: repair the observed Cursor/connector all-repository installation scope; verify exact CiCd App membership after the recorded maintainer-profile 403; obtain authenticated current NuGet policy/key-scope visibility and finish the listed inventory checks. These are explicit actionable dependencies, not a claim that current AD-21 passes. Historical adoption, probe outcomes, cleanup, 10-2 correction and accepted nightly evidence remain preserved. No implementation, probe replay, publication, adoption, maintainer repair, commit or push was performed in this planning invocation.
