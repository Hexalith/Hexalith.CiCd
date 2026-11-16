# Story 17 resume qualification

Status: **in progress; preparation and adoption remain blocked**. The approved
step-03 boundary permits local implementation and verification only. No remote
Git operation, provisioning, adoption, credential change or release dispatch was
performed. The prior story checkout and its Folders checkout remain clean; the original shared workspace is preserved. Production setup,
rendered delivery and the Folders gitlink are unchanged.

The resumed checkout is CiCd `b836159cea272e5211333296936106cf82833a27`.
Folders remains the published candidate
`d27487f405cb52dabdc6ce8dc16af543b2ddd625`, tree
`447b78de825d385ddbb7123a3a2746271a26b9e5`, with sole parent
`a448d20873dc9e809623f85da206e8d8a13bb9ab`. Released Builds remains
`fdda17c0a4538b0f7c99f813c20ca24b49006530` (`v6.0.6`). Direct checkouts were
populated from existing local Git objects; no nested submodule was initialized.
The module's owned tree and working tree remain unchanged.

## Current local results

[The verification record](resume/verification.json) contains revisions,
commands, exit codes, output paths and hashes. Disposable work used
`run-with-temp`; its recorded workspaces are removed.

| Check | Result |
| --- | --- |
| `uv run --locked --script tools/render.py --check` | Passed for unchanged production delivery. |
| Render proposed registration in a private local CiCd clone, then `--check` | Passed; all five Folders output hashes exactly match the archived candidate. |
| Local validator render, committed inputs/render, candidate documents/schema and Folders caller interfaces | Passed. |
| Complete-project strict-runner qualification | All nine boundaries passed, including empty/ambiguous summaries, unsuccessful counters and native exit propagation. |
| Released shared project classification | Matches the saved six-project hook ownership and automatic IntegrationTests classification. |
| Released audit lint | Failed on the same eight historical `auditSources` blobs; each is unchanged from the product base. |
| Current local-script discovery | The same 12 selected files and 940 diagnostics, byte-equivalent in content to the saved diagnostic inventory. |

Full `tools/validate.py` was not run because it clones/fetches live module
repositories. Its checked local boundaries do not establish the full verdict.
The normal module checker remains unavailable before adoption without the
forbidden nested checkout; the approved preparation substitute remains red.
Previously passing product suites were not duplicated on unchanged sources.

## Remaining product and pipeline prerequisites

[The blocker analysis](resume/product-blocker-analysis.json) records exact
saved test failures, current source blobs, dependency revisions and owners.
The prior disposable commit object is no longer present, so its source tree was
reconstructed from the saved binary patch and base in a private bare repository.
The resulting tree exactly matches recorded tree
`edcf1e20599b8d501f1d8fba95a794239519ef36`. The three failing test source files
and sprint execution controls are byte-identical to that qualified source.

- **Platform and EventStore qualification owners:** all 11 explicit Server
  controls fail without the real Keycloak component launcher manifest. Their
  positive control also requires loaded EventStore assemblies to match Debug
  source binaries. Platform's existing launcher selects that class only. A
  complete-project integration compatible with the required package-mode
  Release proof is needed; fabricated manifests, removed source-identity
  checks or extra overlapping subset executions would not satisfy this spec.
- **Platform workload authority and Folders AppHost owners:** the six explicit
  controls fail without genuine component/run-owned manifests. The two
  existing launcher modes select different methods in separate processes.
  They need a complete-project integration retaining their actual TLS,
  process ownership and cleanup before the complete hook can pass once.
- **Folders product owners:** opted-in FR58 fails because
  `LivePathPrerequisitesSatisfied()` is unconditionally false. The sprint
  execution hold keeps Story 10.8 gated on its product prerequisites. The
  saved diagnostic calls 12.1 backlog, while current status marks it done;
  the false gate and the other missing dependencies persist. This migration
  does not authorize implementing held product stories or flipping that gate.
- **Folders provider maintainers:** retained operator evidence still needs
  approved isolated HTTPS deployments, three distinct credential references
  and binding targets. The passing Alpine smart-HTTP smoke supplies its own
  real provider evidence but cannot replace the separate mutation lane.
- **Builds audit policy and Folders evidence owners:** resolve the eight
  rejected historical declarations without rewriting prior proof or weakening
  audit policy. No new dependency vulnerability waiver was indicated by the
  saved audited build.
- **CiCd discovery owner:** resolve the ordinary PowerShell syntax defect;
  the saved minimal literal-callee repro still matches the current scanner
  source. No discovery exemption or replacement module setup action was added.

The composites, runtime changes, gate removals and registration proposal were
already present in the exact published candidate; no further product edit was
justified by this resume inspection. Local qualification does not establish
passing complete retained coverage, predecessor acceptance, ordered AD-21
administration, authenticated adoption, green delivered CI, credential
retirement or the next genuine scheduled release. All incomplete acceptance
items remain unchecked.

## Subsequent publication authorization

After this local qualification, the human requested `push all changes to main`.
The resume spec update and evidence are being committed for publication on
current CiCd main. The local-only statements above describe the qualification
phase. Publication does not establish passing product checks, adoption or story
acceptance.

## CiCd PowerShell discovery correction, 2026-11-16

The isolated `fix/17-powershell-discovery` branch starts from freshly fetched
CiCd main `2adf156b24e0a8053de42d7d4bf9b7c15a8b82e4`. The original shared
workspace edits and prior story worktrees are preserved. The correction uses
PowerShell's AST parser on inert stdin, with profiles disabled; module source
is never evaluated. Parameter declarations, local variable assignments,
arrays, hashtables, function bodies and control flow no longer become Bash
compound-execution or computed-command diagnostics. Literal direct, call
operator and dot-source invocations are followed inside nested expressions.

[The verification record](powershell-discovery/verification.json) records exact
source hashes, parser version and the unchanged published Folders candidate
`d27487f405cb52dabdc6ce8dc16af543b2ddd625`. The saved minimal reproduction
executes unchanged in a disposable CiCd copy and now has **zero diagnostics**
(previously two). Its original saved result is preserved.

The frozen main scanner reproduces the saved **940 diagnostics and 12 files**
exactly. The corrected scanner selects the **same 12 files**, with **318
remaining diagnostics**, saved in full in
[the Folders result](powershell-discovery/folders.json):

| Remaining diagnostic category | Count |
| --- | ---: |
| Computed operands of unknown commands | 193 |
| Unsupported PowerShell method invocation | 63 |
| Computed PowerShell command operand expressions | 39 |
| Unsupported property/index assignment targets | 18 |
| Computed commands | 2 |
| Unresolved argument splatting | 2 |
| Unsupported wrapper options | 1 |

These are retained coverage failures, not exemptions. Even apparently ordinary
method or unknown-cmdlet operands remain red where discovery cannot establish
their execution behavior. Focused regressions cover computed execution text,
attached parameters, splatting, pipeline evaluation, sensitive assignments and
increment/decrement, process/reflection, cwd changes, alias mutation, parser
failures and inert source handling. No diagnostics, exclusions, security gates
or product checks were suppressed.

All disposable verification used `run-with-temp`. Production render also
passes in a disposable CiCd copy with its exact pinned direct Builds checkout;
the fresh implementation worktree itself has no initialized submodules.
Scanner suite results are saved alongside the verification record.

**Story 17 remains in progress.** Full discovery still fails on the diagnostics
above. The eight saved historical audit failures, genuine product/workload and
provider prerequisites, predecessor/AD-21 adoption checks, delivered green CI,
credential retirement and genuine scheduled-night acceptance remain separate
requirements. This fix does not claim to rerun or satisfy them and changes no
production registration, rendered delivery or module gitlink.
