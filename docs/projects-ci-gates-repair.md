# Projects existing-gate prerequisite repair

This is a separate pre-adoption correction following the delivered catalog
acquisition commit `146d0f7e9964c82da23d31b51e6ab62efdcfdda6`. The user requested
“fix” after exact-source hosted CI exposed a malformed renderer fixture and
Commitlint failed before validation because its npm install metadata was absent.
The original catalog manifest, patch, action and closed path list stay unchanged.

The preparation commit removed `RendererFixture`'s class body while leaving
its decorator, deleted three suites still invoked by the unchanged CI, and
removed package metadata still required by the unchanged legacy shared
Commitlint workflow. This repair restores only those prerequisites: the fixture
class body, the exact three historical suites, and Commitlint-only npm metadata.
The lock is pruned offline from the historical graph; all 74 retained dependency
entries are unchanged, including versions, registry URLs and integrity hashes. It keeps the intentionally deleted renderer YAML assertion
absent. Other migration preparation and concurrent user changes are preserved.
The 424 unused release-related entries are excluded. Locked install, signature
verification, and vulnerability audit pass on Node 24.22.2, with zero reported
vulnerabilities; the unchanged module policy accepts the delivery subject and
rejects malformed messages.

The user's explicit requirement to preserve every existing gate governs this
pre-adoption compatibility repair. It does not change the adoption policy on
tooling-only module gates. No workflow, action, gate command, commit policy,
Builds execution reference, dependency pin, gitlink or mapper changes in Projects.
No publication, deployment or v2 activation is performed.

`docs/proposals/projects-ci-gates.json` and `.patch` bind the nine exact paths,
input commit/tree, patch digest, individual before/after blobs and full result
tree. The final perimeter has nine files: three review-derived corrections make
FrontComposer build fresh Release inputs in its separate job and narrowly
classify the exact executable fixture's four host edges, with behavioral tests.
No library reference rule or other consumer is exempted. A separate closed `ci-gates` owner profile reuses the catalog controller's
bounded private-Git transport, owner/module source rereads, absence checks for
the full writer, non-forced single child push and retained failure receipts.
The existing catalog profile is not widened. Unknown profiles or cross-profile
qualification plans fail closed. No module code runs in the credentialed writer.

The dedicated dispatch-only workflow uses the same `cicd-app` environment,
existing pinned App action, and `deliver-owned-writes` job mutex. Its App token
requests only Projects Contents write; this repair contains no workflows. The
secret-free qualification job runs behavioral suites before binding the exact
current owner source and complete module tree. A mandatory closed validation
artifact binds independently checked local module results, exact output tree,
patch digest and six named log hashes into the plan. Missing, failed or stale
evidence fails closed. Both new jobs allow 40 minutes, exceeding the bounded
36-minute controller budget with receipt margin. The continuing owner authorization
is limited to this reviewed nine-file repair and its unchanged product gates.

Local validation uses `run-with-temp` and retains results outside disposable
workspaces: 61 affected test cases, the remaining existing workflow gate
commands, locked npm install/signature verification on hosted Node 24.22.2,
and positive/negative message cases against the unchanged module commit policy.
The delivery profile also requires real-Git controller qualification, refusal
cases and review before dispatch. Local results do not establish hosted G-6
acceptance. After delivery, collect new CI/Commitlint/G-6 observations bound to
the actual committed Projects SHA and retain any further failure without
weakening gates or restoring unrelated publication configuration.

Evidence is retained under
`_bmad-output/implementation-artifacts/evidence/projects-g6-hosted-gate-repair-2026-11-16/repair-20261116T194959Z/`.
Story 1.17 tracking remains outside this task.

The initial six-file candidate exposed two failures in the preserved workflow
regression/invariant checks: retained-output assumptions and executable-fixture
misclassification. Their failed logs remain retained. The final three targeted
corrections pass all 17 regression cases (including eight new behavior cases)
and the actual PowerShell invariant; the other nine gate commands passed. No
success is inferred from the earlier failed logs. Hosted Projects CI/G-6
acceptance remains pending actual owner delivery and a fresh module run.

Current-source requalification preserves concurrent Projects `e8fe81416f714c45f666dc3574c85c9b14b7aff9`
and its eleven advanced gitlinks. The unchanged repair patch produces complete
tree `2a7fdf8f1559190d80257dbc5a79dc1c06069aeb`. All 192 known module cases, three
script checks and actual invariant pass against this source; the closed
validation artifact has SHA256 `8f3a9ebe6e802c6ae813d2a07f099b0810eceae797fe98b65ef22e49571b7715`.

The proposal uses Git binary-patch encoding to preserve historical CRLF blobs
without trailing-whitespace in a textual patch. Independent bare-Git application
produces the identical complete reviewed output tree; no source byte changed.
