---
title: 'Spike: OCI containers and NuGet/login in the publish composite'
type: feature
created: '2026-11-10'
status: ready-for-dev
review_loop_iteration: 0
followup_review_recommended: false
baseline_revision: 2f775b7f362b74c94d16e5c41e4b44626a7c775c
implementation_repository: references/Hexalith.Builds
implementation_baseline_revision: b99c0d9a5b9b2eeebacc19ea1aebf1b0f656afba
context: []
warnings: [oversized]
deferred: []
---

<intent-contract>

## Intent

**Problem:** AD-17 depends on publishing previously built OCI archives and on NuGet Trusted Publishing from a remotely resolved composite. Neither boundary is proven; signed build provenance is a separate deferred decision that story 3-2 needs settled.

**Approach:** Run an isolated hosted spike, record verifiable results, and update the spine and spec companions. Prove nested NuGet/login or its prescribed caller-login/key-input fallback; decide provenance from explicit evidence. This invocation produces the plan only.

## Boundaries & Constraints

**Always:** Work in Builds on main; use new files, Python >=3.12 standard library, SDK from global.json, Release/package mode and Builds restore trust. Separate source-building from a publisher with no repository checkout; resolve trusted scripts from GITHUB_ACTION_PATH. Pin actions by full SHA and downloaded tools by version and integrity. Use a caller-owned hexalith-release job with explicit credentials and id-token: write. Preserve archive/index/child digests and retry the original artifact without rebuilding. Record full Git revisions, artifact identity and hosted run links.

**Never:** Change frozen module-facing actions/workflows, the existing builds-release.yml, production release behavior, Git tags, published NuGet packages, module pins or stories.yaml orchestration fields. Do not turn missing policy/credentials or a service outage into a composite-failure verdict. Do not implement the release state machine or treat OCI labels as signed attestations. During this planning invocation, do not create executable spike files, dispatch workflows or publish anything.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
| --- | --- | --- | --- |
| OCI handoff | One build's archive and authenticated artifact identity; linux amd64 and arm64 | Clean remote publisher pushes the version tag; registry root, child manifests and blobs match the archive | Digest/platform mismatch fails the proof |
| Retry | Same original artifact and destination version | Identical content, no compile/pack, no replacement from another build | Conflicting destination digest fails |
| Invalid artifact | Wrong run/ID/digest, corrupt archive or incomplete graph | Stop before registry writes | Nonzero diagnostic; retain sanitized evidence |
| Nested login | Matching caller policy/environment and OIDC permission | SHA-pinned NuGet/login inside remote composite returns a masked nonempty temporary key | No NuGet package publication is needed |
| Fallback | Nested login fails while caller login succeeds under the same policy | Caller login first; explicit nuget-api-key input reaches the composite successfully | Both failing is environment-blocked, not fallback proof |
| Missing prerequisite | No matching spike policy, scoped push identity or usable environment | Stop hosted experiment with the exact missing prerequisite | Do not weaken or replace existing policy |
| Provenance | Downloaded package bytes and immutable image digests | Adopt only after verifiable subject/source identity and supported permissions; otherwise record a reasoned exclusion | Infrastructure failure alone leaves the spike blocked |

</intent-contract>

## Code Map

Builds-relative unless prefixed with CiCd. Read-only investigation was performed by parent and one subagent; no experimental proof exists yet.

- `.github/workflows/builds-release.yml:36,71` — production caller login and temporary-key handoff already exist; preserve bytes. Recorded nuget.org policy names this workflow and production, not the proposed spike.
- `Github/publish-containers/publish-containers.sh:189` — frozen direct build-and-push implementation, not archive reuse. `oci_registry_validator.py:212,268,299,348` supplies read-only graph-validation examples.
- `Props/ContainerProvenance.targets:4` — build-time OCI labels; `.github/workflows/domain-release.yml:1067` — frozen signed package-attestation example.
- `Github/lib/ci_pipeline.py` (`build_flags`, `restore_and_build`), `NuGet.ci.Config`, `global.json` — reuse SDK/trust/package-mode conventions without changing shared CI. Sample from 2-6 remains unchanged.
- `Tools/ci/{lint_workflows,run_python_tests,check_public_api}.py` and README — existing lint, dual-interpreter discovery of Github/lib/tests, and Git-object API checks. package.json/lock and commitlint.config.mjs pin commitlint 21.2.4.
- New `docs/cicd-3-1-publish-composite-spike-plan.md` — committed Builds execution plan, prerequisites, decision rules and primary-source links. New `docs/cicd-3-1-publish-composite-spike-results.md` — implementation's final evidence and production-interface handoff.
- CiCd spine `AD-7/9/10/11/17/20` and Deferred; `SPEC.md`, `pipeline-stages.md`, `enforcement.md`, `.memlog.md` under `_bmad-output/specs/spec-cicd/` — authoritative decision write-back. Prior stories establish the freeze, shared build flags and sample; their unrelated deferred CI/Windows issues are outside this spike.

## Tasks & Acceptance

**Execution:**

- [ ] `docs/cicd-3-1-publish-composite-spike-results.md` — begin with prerequisite evidence: main-only hexalith-release, a matching publish-spike.yml nuget.org policy, HEXALITH_NUGET_USER, and an isolated Zot destination with its scoped push pair. The maintainer supplies unavailable policy/credentials; record blocked and stop if absent. Retain existing policies and legacy environment. This check precedes executable probe deployment.
- [ ] `Samples/PublishSpike/{PublishSpike.csproj,Program.cs}` and `Tools/spikes/publish_spike.py` — create an isolated SDK-container fixture and build/archive driver; emit both platforms once plus a local-only package for optional provenance. Select and integrity-pin Skopeo distribution in new `Tools/spikes/publish-tools.json`; inspect actual SDK archive compression/layout and reconcile containers/*.tar without rebuilding images.
- [ ] `Github/lib/publish_spike.py`, temporary `Github/publish-spike/action.yml` and `.github/workflows/publish-spike.yml` — build in a read-only job, transfer its artifact, and publish through a full-SHA remote action reference in a separate job without checkout. Use Skopeo copy --all --preserve-digests as the candidate; verify remote graph and replay the original artifact. Resolve support scripts through GITHUB_ACTION_PATH; reserve Github/publish for the production story.
- [ ] `Github/publish-spike/action.yml` and `.github/workflows/publish-spike.yml` — prove nested login and the same-context caller control; implement and exercise key-input fallback only on discriminating failure. Evaluate signed package/container provenance with truthful builder/source identity, no extra build or source execution; adopt only when both subject classes verify and added permissions remain confined to publish. Record inclusion or exclusion with rationale.
- [ ] `Github/lib/tests/test_publish_spike.py` — exercise artifact, graph, retry-conflict and login-failure cases above through real helper/command effects; no workflow-text assertions. Local controls supplement hosted proof.
- [ ] `docs/cicd-3-1-publish-composite-spike-results.md`; CiCd `_bmad-output/planning-artifacts/architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md` and `_bmad-output/specs/spec-cicd/{SPEC.md,pipeline-stages.md,enforcement.md,.memlog.md}` — settle tool/distribution pins, archive format/naming, login placement/input, provenance and permissions consistently before 3-2. Update only affected clauses; append the evidence event. Remove `.github/workflows/publish-spike.yml` and `Github/publish-spike/action.yml` after retaining exact-source evidence; retain the reproducible fixture/helpers/tests. No Builds release while the experimental action exists.
- [ ] `docs/cicd-3-1-publish-composite-spike-plan.md`, CiCd gitlink `references/Hexalith.Builds` and this id-keyed story file — validate, commit/push implementation when resumed; review the Builds delta from implementation_baseline_revision plus CiCd delta from baseline_revision. Stage the updated Builds gitlink with this story. For this invocation, commit/push only the Builds plan, record planning checks, set ready-for-dev and halt.

**Acceptance Criteria:**

- Given the deployed experimental action, when the hosted caller runs without a repository checkout in publish, then its registry tag resolves to the entire graph built in the separate job and replay succeeds from that job's original artifact.
- Given valid caller publishing prerequisites, when both NuGet login placements are exercised, then the results document identifies a proven placement and any required public key input, with sanitized exact-source hosted evidence.
- Given the completed spike, when story 3-2 reads the spine and spec companions, then OCI tooling/format, login placement and provenance have consistent final decisions and the OCI/login and provenance Deferred entries are resolved.
- Given this planning-only invocation, when its delivery is inspected, then Builds contains only the new plan document, this story is ready-for-dev with all implementation tasks unchecked, and no experimental run or publication is claimed.

## Spec Change Log

## Review Triage Log

## Design Notes

The Builds plan is the repository-local execution companion; this id-keyed file remains the canonical workflow status and intent contract. Experimental outcomes are work to perform, not intent gaps. Prerequisite unavailability has an explicit blocked outcome; planning readiness does not attest that publish credentials or a new NuGet policy already exist. SDK archive support and Skopeo options are documentary feasibility evidence only. A successful login exchange proves authentication without publishing a package. Signed provenance from a publishing job must accurately describe its relation to the original build.

## Verification

Planning: parse frontmatter, inspect dependency order and Given/When/Then criteria, check local document links, git diff --check, verify a documentation-only Builds delta, and validate the exact commit message with installed pinned commitlint before commit/push.

Implementation, when resumed: run `python3 -m unittest discover -s Github/lib/tests -p test_publish_spike.py` on Python 3.12 and runner Python; run locked `Tools/ci/run_python_tests.py` on both, `python3 Tools/ci/lint_workflows.py`, and locked `Tools/ci/check_public_api.py` after commit. Require exact-SHA hosted experimental runs and original-artifact replay for the external proofs; local mocks and existing release successes are insufficient. Compare frozen blobs against the implementation baseline and leave existing Builds CI green.

## Auto Run Result

Status: **ready-for-dev**. Halt after planning, as requested. No implementation step was entered.

- Resolved only story 3-1 from the requested spec folder. Loaded the epic contract, its companions and prior-story continuity; parent and one read-only investigation subagent mapped relevant Builds code and primary documentation.
- Re-read the rendered workflow and this on-disk specification for the readiness gate. Every task has a file path and action; ordering, Given/When/Then acceptance, hosted observation surfaces, explicit prerequisite-failure behavior and experimental decision rules are defined. No unanswered intent question remains. The oversized warning is retained.
- Prepared the Builds-local execution plan and this canonical story. Architecture/spec decision clauses remain unchanged until actual spike evidence is available. All seven implementation tasks remain unchecked.
- Planning checks passed: both frontmatter documents, creation date, complete intent block, no template placeholders, local Markdown targets, final newlines, full Git baseline identities and the four Given/When/Then criteria. Runtime tests and hosted experiments were not run for this documentation-only change.
- Required implementation preflight: verify/provision a matching NuGet policy, main-only hexalith-release environment and scoped spike registry push identity. Existing recorded production policy is insufficient evidence for the new caller. These are execution prerequisites, not claims of configured live access.

- Builds planning delivery: `15c108131c7127dbff10dbbb53d1701f123dfe29` (`docs(cicd): plan publish composite spike`), pushed successfully to origin/main. Remote ref was read back and equals the full local revision; Builds is clean. The commit adds only `docs/cicd-3-1-publish-composite-spike-plan.md`; every existing tracked file remains unchanged.
- Exact-message validation: pinned @commitlint/cli 21.2.4, zero problems and warnings; stored commit message is byte-identical to the validated candidate. Evidence: `/tmp/cicd-3-1-planning/commitlint.log`. Staged whitespace checks passed. Fetch before commit showed zero divergence; push was a fast-forward.
- CiCd delivery: this canonical story and the updated Builds gitlink are staged together. No CiCd commit/push, manual workflow dispatch, spike execution or package/container publication was performed. Existing push-triggered Builds CI is not experimental acceptance evidence and was not awaited for this documentation-only planning halt.
