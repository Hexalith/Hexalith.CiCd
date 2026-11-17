---
title: '20 — Migrate EventStore'
type: 'chore'
created: '2026-11-16'
status: 'in-review'
baseline_commit: 'd3f3ef864c08cd89e390246d1a5d1dedffc4a92b'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/specs/spec-cicd/evidence/20/planning.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** EventStore's legacy pipelines and live-test contracts have outgrown
the historical migration inventory.

**Approach:** Preserve product coverage through managed actions, add a narrow
manual qualification job contract, release Builds, then register and adopt
EventStore through delivery. Require green CI and an actual nightly outcome.

## Boundaries & Constraints

**Always:** Follow AD-21 ordering, product-only gates, explicit named secrets,
module-agnostic Builds code and compatible minor API evolution. Preserve Azure
owner authority, private networking, expiry, source binding, custody and pinned
fixture runtimes. Use module-agent credentials for EventStore product writes,
CiCd-agent for CiCd/Builds, and command-local maintainer access for approved
administration. Work from fresh main.

**Never:** Edit owned module portions directly, alter frozen Builds files,
weaken audits/tests, manufacture authority or execution evidence, auto-run Azure
faults, initialize nested submodules, or expose the App key.

**Human decisions, 2026-11-16:** Apply the dedicated manual Azure job and
EventStore-only bootstrap recommendation. Ordinary CI retains offline coverage
without Azure secrets. A setup-enabled qualification job runs only on an explicit
manual request after green CI for the same commit, using its designated private
runner, approval environment, two explicitly named secrets and exact authority
digest. Build once on that runner; retain fixture runtimes. Amend the job/runner
constraints narrowly; keep Azure secret names out of ordinary shared CI inputs.

Before actual adoption only, replace the unavailable normal checker for
EventStore product-preparation pushes with shared Release package-mode build/unit
routines, applicable product/package/consumer tests, commit/action/audit-policy
validation, complete owned-portion byte/mode/gitlink comparisons and immediate
base/head freshness checks. Any required failure blocks the push. Use isolated
exports under `run-with-temp`; preserve authority checks and credentials. The
exception expires at App adoption; normal `check.py` is then mandatory.

## I/O & Edge-Case Matrix

| State | Expected behavior |
| --- | --- |
| Missing authority, expired receipt or source mismatch | Fail before cloud calls. |
| Missing precondition, compatible release or product action | Block adoption and record exact failure. |
| Mixed product/workflow assertion file | Remove workflow assertions; retain product checks. |
| Existing modules use old config | Additive API preserves their behavior. |
| Delivery or release fails | Preserve last accepted render; report actual outcome. |

</frozen-after-approval>

## Code Map

- `evidence/20/planning.md` under the main spec folder: exact revisions, product
  paths, 20 workflow-coupled files, Azure requirements and preflight failures.

## Tasks & Acceptance

**Execution:**

- [ ] `evidence/20/` — refresh identities and AD-21 readiness before product
  preparation; preserve legacy publishing until adoption.
- [ ] `_bmad-output/specs/spec-cicd/{SPEC.md,stories.yaml,pipeline-stages.md}`,
  architecture spine AD-12/14/21 — record human decisions and current gate
  inventory; resolve runner/runtime and bootstrap dependencies explicitly.
- [ ] Builds `schemas/hexalith.ci.v1.json`, `Github/lib/ci_config.py`,
  `.github/workflows/ci.yml`, `Github/prepare/action.yml` and corresponding
  library tests — implement the narrow qualification/preparation contract with
  backward compatibility; release through the interactive shared process.
- [ ] EventStore `.github/actions/`, `Hexalith.EventStore.slnx`, `scripts/`,
  `tools/`, `tests/`, root npm files and `docs/ci.md` — retain package, consumer,
  compatibility, browser, payload and broker checks; reuse shared Release
  outputs; route live projects explicitly; delete CI/governance assertions
  and tool-only npm assets. Apply the approved preparation checks before pushes.
- [ ] `templates/.github/workflows/ci.yml.j2`, `tools/tests/test_render.py`,
  `tools/tests/test_validate.py`, `setup/README.md` — render and validate the
  manual qualification contract with explicit secrets; test failures and old configs.
- [ ] `builds-version`, `setup/Hexalith.EventStore.yml`, `rendered/`, EventStore
  gitlink — pin the acceptable release and validate one committed adoption
  candidate after actions exist on live main. Let delivery replace owned files.
- [ ] `evidence/20/` — authenticate adoption, enable immutability, retire legacy
  grants, and record normal-checker, CI, qualification and nightly outcomes.

**Acceptance Criteria:**

- Given the approved job model, when ordinary CI runs, then retained offline
  product coverage executes without Azure authority or duplicate module builds.
- Given a compatible released Builds API and satisfied preconditions, when
  delivery adopts EventStore, then its perimeter matches the accepted render
  and retained product checks stay enabled.
- Given adopted green main, when the next scheduled night completes, then
  successful publication or a valid no-release result is recorded before done.

## Implementation Notes

- Fresh-main integration uses the existing generic `execution_jobs` /
  `shared_ci_call` model and separate `qualification.yml`, replacing the earlier
  duplicate CI-dispatch implementation. Explicit `job=payload-azure` and
  `authority-sha256` bind fresh green-source CI to the same private runner,
  environment and literal secrets. The action consumes generic
  `HEXALITH_AUTHORITY_SHA256` / `HEXALITH_SOURCE_SHA` environment values through
  its unchanged strict validator. This changes no frozen approval or adoption
  prerequisite; the default nightly selection never selects Azure.

- Preparation uses a labeled EventStore-only stages 1–3 projection validated by
  the exact selected released Builds contract (including v6.0.6). Preserve
  ordinary routes and SDK prerequisites, reject unsupported enabled policy,
  and map only the known Azure live exclusion to its offline authority-schema
  hook. This does not create an adoption configuration or remove the compatible
  released API requirement before adoption. See the stage-projection patch
  evidence under `evidence/20/`.

- The human approved scope and continuation. Implement sequentially with no
  pushes or remote operations at this stage; prepare operational handoffs and
  report pending provisioning/release/adoption evidence for publication.

## Spec Change Log

## Review Triage Log

| Finding | Verdict | Route | Evidence |
| --- | --- | --- | --- |
| B1 | high | patch | Legacy CI invokes verify-process-packages.py after checkout/SDK only. Its new unconditional --no-build prevents the still-active job from producing packages. Managed offline checks already call the packer independently, so restore the standalone default. |
| B2 | high | patch | Legacy folded-snapshot CI likewise has no prior build. The script now unconditionally refuses build/restore; select reuse only in the managed hook and preserve the standalone default. |
| B3 | medium | patch | The new private supervisor pulls a mutable 1.18.2 tag; resolving its image ID only within a run does not pin later runs. Use an official reviewed content digest while retaining the runtime version check. |
| B4 | medium | patch | integration() performs an ambient Docker pull before prepare-route-catalog-tools.py rejects remote/conflicting contexts. Validate and bind the local Docker selection before any mutation. |
| B5 | medium | patch | Catalog binaries use RUNNER_TEMP and global GITHUB_ENV although the caller already passes selectors. They outlive the private wrapper workspace. Keep them under TMPDIR and remove unused global exports. |
| B6 | high | patch | The executable digest comparison is a Python assert, removed by -O/PYTHONOPTIMIZE. Replace it with an explicit exception and exercise optimized execution. |
| B7 | medium | patch | The verifier accepts an HTTP 404 substring without first proving intended account/repository/ref access. Add a known-main readback before interpreting accepted-ref absence; never infer absence from an authorization failure. |
| B8 | medium | patch | Broad tools/scripts/tests prefixes include legacy publication helpers despite the preparation-only approval. Bind this verifier to the reviewed exact preparation paths. |
| B9 | high | patch | Endpoint tree equality alone admits an intermediate owned-file edit followed by a revert. Range-wide commitlint exists, but ownership must also be checked for each introduced commit. |
| B10 | medium | patch | A readiness timeout removes owned containers before their native startup logs are retained. Emit bounded diagnostics for verified owned IDs on exceptional cleanup. |
| E1 | medium | patch | fetch origin main can leave origin/main stale under a custom fetch mapping; fresh() then compares the stale ref. Fetch main into the exact tracking ref explicitly. |
| E2 | medium | patch | Same unchecked adoption-404 root cause as B7; the guard must establish successful known-ref access before deciding the accepted ref is absent. |
| E3 | high | patch | Same optimization-removable checksum check as B6; normal download integrity must not depend on assertions being enabled. |
| E4 | medium | patch | AppendDurabilityRaceLiveSidecarTests inspects redis:6 even though the private supervisor selects a separate pinned image. Inspect the actual observed Redis image ID and label the probe truthfully. |
| E5 | medium | patch | The removed mixed Azure workflow method also evaluated IsPackable=false for three companion projects. No equivalent independent assertions remain; restore their product-only packaging check. |
| E6 | medium | patch | The retained cross-language fixture builds an Interop project referencing current Contracts, so ordinary managed hooks restore/build the current module again. Consume its prebuilt Release output/package in package mode while preserving isolated fixture compilation. |
| V1 | medium | patch | Pre-verified gap: helper tests call validate_qualification_request directly, while entrypoint tests cover prepare/build only. Add executable request-phase rejection controls demonstrating no preparation effects. |
| V2 | medium | patch | Pre-verified gap: existing fixture tests call close() manually. Exercise the actual context manager on success, startup failure and body failure, asserting owned cleanup and restored handlers. |
| S1 | high | defer | The unchanged conservative source-discovery model reports 56 unsupported-coverage diagnostics for 22 candidate files. This existing pipeline capability is a blocking activation prerequisite; preserve the audit and do not publish/adopt on an incomplete result. |
| P1 | medium | patch | A real disposable Git branch adding then deleting a leading-newline scripts/ci-product-checks.py path passed the first history fix because the Git adapter stripped leading whitespace. Preserve NUL-delimited paths; the exact regression now belongs to preparation-history verification. |
| P2 | high | patch | The actual approved preparation run refused future CI fields against immutable Builds v6.0.6 before product checks. Preparation needs released stages1–3, while future job/tool settings belong to adoption; project only the exact reviewed plan and disabled defaults, preserving all actual checks and verifying the additional SDK. |
| P3 | medium | patch | The first projection preserved extra legacy Windows jobs that v6.0.6 accepts; an added exclusion could therefore remove an ordinary project without executing that job. Require the exact sole approved Azure job, with a regression for extra windows-latest jobs. |
| P4 | medium | patch | The current-main Windows forwarding fixture directly renders the CI template without the new manual_jobs context, causing the only renderer error on both Python versions. Supply the empty nonmanual context; all forwarding and legacy assertions remain, and the exact case passes on both versions. |
| P5 | medium | patch | The required full Client run failed when its 100ms discovery deadline beat corrupt-registry validation under parallel collection load. Under the explicit fix request, reuse the existing nonparallel admission collection; production deadline, exact exception assertion and every test remain unchanged. All17 class cases pass with no skips. |
| P6 | medium | patch | The next required full run exposed the same process-wide admission contention in ReminderDiscoveryOwnershipTests. Reuse the existing Process read slots collection; all5 focused cases pass without changing assertions, recovery counts or deadlines. The preparation verifier now completes every classified unit project, retains every shared PipelineError and still fails before package checks if any project fails. All17 bootstrap controls pass on Python3.12 and3.14. |
| P7 | medium | patch | The complete 21-project run found one failure: the unchanged tracked-content secret scan flagged seven upstream fixture expressions. Fresh main already fixes six; preserve those changes and replace only the remaining V2 literal with a runtime canary. The whole V2 fixture (105 cases) and the real unchanged tracked scanner pass, with zero skips. Keep scanner policy, every assertion and source scope intact; the exact preparation allowlist now has62 paths. |
| P8 | medium | patch | A real OCI archive publish reused an MSBuild worker with a deleted earlier job's temporary directory. Add the standard --disable-build-servers flag to the fixture's two publish commands. All21 product fixture cases, including real multi-RID publication, pass with zero skips; no shared workers, assertions, timeouts or environment policy are changed. |
| P9 | medium | patch | The activation drain test released native success before its fake guard observed protocol cancellation; legitimate successful cleanup could then remove the outbox row. Add an explicit cancellation-observation barrier before native resume, preserving all four scenarios, existing five-second bounds and every shutdown/lease/outbox assertion. All34 activation-worker cases pass without skips; production semantics remain unchanged. Only the exact Drain.cs path is added (63 allowed paths). |
| P10 | medium | patch | Concurrent main added the generalized qualification workflow and renderer, superseding this draft's CI-dispatch implementation. Preserve that upstream model and adapt the unpublished Azure action to its generic authority/source environment. Renderer46, validator54 and strict Azure request5 controls pass on both Python versions; actual composite refusals block service execution. |
| P11 | medium | patch | The retained paired-checkout product fixture assumed root node_modules existed. Its managed hook now provisions the signed, locked CLI in disposable scratch and passes the exact policy, retaining legacy policy before retirement and canonical selected-Builds policy afterward. Paired legacy/canonical checks, wrong-policy refusal, shipped roles and hook controls pass. All source-trust assertions remain; only the exact loop7 path is added (64 allowed paths). |
| P12 | medium | patch | Dapr qualification rejected the migrated fixture against old source bindings. Preserve both historical lock hashes by restoring exact historical fixture bytes in the trusted archive, and refresh only the Platform descriptor's current fixture/helper/archive bindings. All159 affected controls and both drift refusals pass; validators, tests and runtime/image/binary/chart/authority identities remain unchanged. Three exact product paths bring the preparation allowlist to67. |
| P13 | medium | patch | The keyed-semaphore test released its lease before setting the flag a resumed waiter asserted, so valid acquisition raced the marker. Replace the delay/flag protocol with a real pending acquisition assertion while the first lease is held, then prove ownership and final cleanup after release. All4 cases pass without skips; production code is unchanged. Only this exact test path is added (68 allowed paths). |


## Local Implementation Handoff

Source changes, repairs and complete preparation qualification are recorded in
`evidence/20/execution.md` and `evidence/20/source-publication-status.md`.
EventStore preparation is published. Operational release/adoption/nightly gates
remain pending; this story is not complete.

## Verification

- Run affected Builds loader/pipeline/API suites and CiCd renderer/validator
  suites on Python 3.12 and runner Python under `run-with-temp`.
- Run retained product tests and approved qualification; report unavailable prerequisites.
- Run locked `tools/check_global.py` and `tools/validate.py` on the committed
  candidate; require normal module `check.py` after adoption.
- Record revisions, readbacks and run links without secret contents.

## Review Verification Disposition

The original 19 patch findings and subsequent verification repairs are resolved.
The complete approved preparation gate passes on the published EventStore commit
22e2e2470ed5d692b2bf4970251d02b5c1823f9f; its authenticated push/readback is
recorded. See evidence/20/source-publication-status.md and the exact receipts.
The human's later main-publication instruction authorizes source publication;
this does not mark the migration complete.

Keep this spec in review. S1's saved 58-diagnostic scan is historical; adoption
requires a fresh complete scanner qualification against the selected released
API and current source. A compatible immutable release, owner worker/authority
prerequisites, registration/delivery, normal checker, live qualification and
actual hosted/nightly acceptance outcomes remain pending. No production pin,
registration, adoption, authority run or release is claimed by preparation.
