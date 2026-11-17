# Story 24 session handoff — stopped at the user's request

The user said: “stop and save, I will contionue in a new session.” Do not resume
implementation until the user starts the next session. Current files are saved
in the worktree; no commit, push, release or FrontComposer adoption was performed.

## Where to resume

- Working directory: `/home/administrator/projects/hexalith/cicd-story-24`.
- Branch: `story/24-migrate-frontcomposer`; CiCd HEAD remains
  `66e3a5a3a0e9bb01dd161c19349953594e01a22f`.
- Active prerequisite spec:
  `_bmad-output/implementation-artifacts/spec-24-shared-runtime-compatibility.md`.
  Status is `in-progress`, `review_loop_iteration: 5`. This is the final allowed
  loopback; another bad-spec/intent-gap loopback would exceed the workflow limit.
- Main story spec:
  `_bmad-output/implementation-artifacts/spec-24-migrate-frontcomposer.md`.
  Story 24 remains in progress. The approved architecture does not need another
  approval; qualification/release/adoption are separate unfinished gates.
- Companion:
  `_bmad-output/implementation-artifacts/prerequisite-24-frontcomposer-shared-compatibility.md`.
- Rendered BMAD workflow already exists. Do not render it again:
  `/home/administrator/projects/hexalith/cicd/_bmad/render/bmad-build/cicd-24343c124152/7e5058bea218030e62f6/`.
  Steps 01–04 were read; current phase is step 03 re-derivation. Step 05 is unread.
- Read the active spec completely, including all KEEP/change-log/triage entries,
  and load its frontmatter context files before continuing.

## Review and current implementation

Review pass 5 completed all three independent reviewers before triage. All 14
findings have individual verdicts in the spec. B5-4/E5-1 share one defect; the
remaining groups are distinct. Nine bad-spec groups triggered iteration 5;
four small fixes/test gaps are moot during re-derivation but still required.
No finding was deferred or an intent gap. Frozen intent remains unchanged.

Only the 56 saved prerequisite source paths (16 CiCd, 40 Builds) were reset
before fresh implementation. Recovery patches, docs/evidence, original
FrontComposer preparation and completed provider settings were preserved.
The fresh context-free implementer was `/root/rederive_shared_runtime5`.
That session was interrupted on the user's stop. Its cleanup-only follow-up is
complete: all nine asynchronous owned jobs and the synchronous jobs were already
completed/joined; no active child required termination. Its stopped handoff is
under the evidence directory listed below. No implementation/tests ran after stop.

Core corrections now cover edge properties, defining-file context, inline task
DLLs, declarative file reads, TFM collisions, final effective SDK identity, tool
output preflight, SRI, source/output overlap, tag metadata and collector failure.
The latest pre-stop work additionally handles read-dependent conditions/import
selectors and moves primary test discovery behind private Release/package
preflight. That primary view uses `require_all_sources=False`; supplementary
closure still requires all reviewed projects. Preserve actual primary ownership
and package behavior. These latest changes are not fully verified yet.

Diagnostics retained (not final candidate qualification):

- `iteration-5-targeted-diagnostic-3.log`: 12 native/shared tests passed in
  83.194s. This predates the latest read-branch/primary-discovery corrections.
- `iteration-5-tool-delivery-diagnostic-2.log`: explicit Dapr/Aspire Linux
  prepare → subsequent hook passed (2.276s). Real locally packed/installed
  net10 Aspire.Cli fixture version 13.6.5; only package provisioning and Dapr
  archive bytes substituted. Do not claim real hosted/product tool qualification.
- `iteration-5-collector-diagnostic-3.log`: three caller tests passed (34.961s),
  including checkout failure with green targets, preventing unreduced seeds
  from scan/bump writers, and preserving valid reduced-failure bump behavior.
- Earlier diagnostic failures are retained honestly. Full locked verification
  matrix, final source manifest, coordinator audit and next independent review
  have not run for iteration 5.

Next, after explicit resumption: finish/audit the latest read-branch and primary
preflight changes, run appropriate targeted checks then the spec's full required
verification sequentially, join every job, create/read the complete candidate
diff, audit all tasks and frozen matrix rows, then follow step 04. Use a fresh
context-free implementation handoff if the old agent cannot be continued.
Do not increment the review counter merely for resumption.

## Durable evidence and recovery

Evidence directory in the worktree:
`_bmad-output/specs/spec-cicd/evidence/24/shared-runtime/`.

- `session-stop-2026-11-17-resume-state.json` saves session metadata, baseline/
  review trees, exact prior prompts and recovery inventories. Old TMP paths in
  that metadata are closed; use the durable recovery files.
- `iteration-5-stopped-handoff.md` is the implementer's completed cleanup/current-
  state handoff. Read its exact unfinished issues, including the still-unverified
  direct/indirect read-dependent Import/Choose case, broad taint-name heuristic
  and relocated primary-discovery caller negative.
- `session-stop-2026-11-17-checkpoint.json` records the final stop checkpoint.
  WIP backups outside the worktree are
  `/home/administrator/projects/hexalith/cicd-story-24-stopped-2026-11-17-cicd.diff`
  (5,463,682 bytes; SHA-256
  `84cb001ded38b33622ec5cc665a8f39eea68b158f62799b9b417f10434fe33e3`)
  and the corresponding `...-builds.diff` (477,220 bytes; SHA-256
  `19ad3b0f62793dfa36e79115c988036d14bb90343ba9f1f68e841fd127bcdb7e`).
  Snapshot trees are CiCd `80e7e8214e2ab35ed6940aa3876e1f30c54427f1`
  and Builds `657c269efcc2e1b839f10b5b7937ba84f299530b`. Subsequent save-only
  handoff/metadata edits are outside those snapshots. Three HEADs and staged
  content are unchanged; the save itself left real indexes unchanged. Use this
  checkpoint's index hashes for later comparisons, since ordinary status refresh
  metadata may differ from the earlier reset checkpoint. All 41 protected checks
  passed; FrontComposer tree still exactly
  `4fae737467f49ca56e98fd1104aa4d63a031dc91`.
- `parent-review5-code-reset.{py,json}` proves the exact 56-path reset, unchanged
  three HEADs/real indexes, 41 protected checks and exact FrontComposer tree.
- `parent-review5-probes.{py,json,log}` preserves native evidence for TFM collision,
  escaped tool intermediates, SDK 11→10 asset mismatch, empty SRI and tag loss.
- Complete reviewed candidate before this correction pass:
  `/home/administrator/projects/hexalith/cicd-story-24-shared-review-iteration-5.diff`,
  SHA-256 `aa673821e2832dab0430eac4c4f869adc7ea9c068baec74ccec132a778764904`.
- Code-only recovery is in the corresponding
  `cicd-story-24-shared-cicd-code-iteration-5.diff` and
  `cicd-story-24-shared-builds-code-iteration-5.diff` files alongside it.
  These preserve positive source, not permission to restore known defects.
- Iteration-4 checks are superseded: 26 fresh groups, 1,132 executions,
  256 hygiene checks, source fingerprint
  `598f0e3d3e3d816092f6b5f59d0cae7c8ad6d9602483b3e677f70d7d1f5fabee`.
  They do not qualify the current modified candidate.
- When the missing-file report was checked, Builds `docs/shared-runtime.md`
  existed with 18,933 bytes, SHA-256
  `5c430ecadf2bcc06fe1e64979a057d203b3b23b1cf0d229d8b3b9919e3ab602d`,
  identical to reviewed tree `a0961d6762a82524f4157c456c6aeff17bd3f416`.
  An interim missing-file report was refuted by read-only checks. The implementer
  subsequently updated this doc for iteration 5; preserve its current WIP version.

## Completed provider setup and remaining gates

The user explicitly answered “do it yourself” to the Zot/NuGet prerequisite
question. Both are completed and independently verified:

- NuGet active policy 27339: owner Hexalith; repository
  `Hexalith/Hexalith.FrontComposer` (ID 1202567471); workflow `release.yml`;
  environment `hexalith-release`; glob `Hexalith.FrontComposer*`; push-only.
  All 22 prior policies, including legacy 18269, are preserved.
- Zot dedicated identity `hexalith-frontcomposer-publish`: read/create/update
  only `frontcomposer-ui` and `frontcomposer-ui/**`; no admin/delete/foreign
  grants. Existing rows/grants preserved, rollout passed; /v2 GET 200,
  foreign upload attempts 403. No image/package/upload was created.
- GitHub environment `hexalith-release`: main-branch-only deployment policy;
  `HEXALITH_REGISTRY_USERNAME` and `HEXALITH_REGISTRY_PASSWORD` stored there.
  Password was generated in memory, passed on stdin and never saved in evidence.
- Proof: `evidence/24/adoption-prerequisites/verification.json` (12 evidence
  hashes), SHA-256
  `cabad1aec874f6e9d4f0c17444eeafdfe0a1dc8b5426848c806ae5c7757eca98`.
  Do not repeat provisioning or rotate credentials on resumption.
- Normal authenticated NuGet browser window HWND 1642262 was left open on the
  policy. Browser storage/cookies/credentials were not extracted.

Ordinary GitHub operations use `/home/administrator/.config/gh-cicd-agent`.
Only the explicitly authorized interactive admin used command-local
`GH_CONFIG_DIR=/home/administrator/.config/gh`; the default was not changed.
Do not broaden/switch credentials around refusals. The prior App-membership
endpoint 403 remains UNVERIFIED, not proof of absence.

Remaining external work includes actual complete product source/tool/browser
qualification, reconciled released Builds/runtime pins, actual Dapr 1.18.0
digest qualification, full mutation/property/performance/resource/hosted
transport qualification, fleet capacity, online audits, fresh-main reconciliation,
immutable release, remaining AD-21 settings/App/selections/legacy cleanup,
registration/adoption/green CI/next central nightly. No provider purchases or
publication actions were inferred from the two-setting authorization.

Preserve the dirty original checkout, all FrontComposer preparation, frozen
Builds Tools/ci, production setup/render/pins/gitlinks and all old evidence.
Use `run-with-temp` for disposable jobs, keep outputs beneath TMPDIR and logs
outside, and run implementation/verification sequentially. Never add skips or
weaken assertions. Never kill unrelated SDK/Docker jobs.
