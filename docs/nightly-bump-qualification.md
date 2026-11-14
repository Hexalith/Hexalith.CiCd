# Nightly bump transport qualification

Status: **GITHUB_TOKEN transport qualified on 2026-11-14**.

Production uses the `bump-push` job's own GITHUB_TOKEN with Contents and Actions
write. It independently verifies the candidate, confirms the exact fast-forward
push, then explicitly dispatches delivery. No App fallback was selected.

## Hosted nested-path probe

The main-only `qualify-bump: true` run executed only `bump-push`; dispatch, wait,
publish-ready, bump, delivery-wait and keepalive were all skipped. Its child
changed only the inert nested file
`rendered/Hexalith.Probe/.github/workflows/probe.yml` on a disposable ref. It
neither changed main nor dispatched delivery/releases nor touched a module.

| Evidence | Observed value |
| --- | --- |
| Controller/workflow source revision | `6a7b287b7f2b40614970f10e3479c109f114d863` |
| Hosted run and attempt | [43643834124](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/43643834124), attempt 1; success |
| Captured main/base | `6a7b287b7f2b40614970f10e3479c109f114d863` |
| Probe child and actual remote commit | `d7d04da2318ec9ffada4e0205a934811b2fc7058` |
| Candidate and actual remote tree | `daea2603c740ac9d3c0f400f0c95bddc97306f8f` |
| Artifact ID and name | `14132723343`, `hexalith-nightly-bump-push-1` |
| Authenticated archive digest | `sha256:b19d4bd4e521256d92a13b38b4ab2b1319ac512477481d5191492647a5f9e646` |
| Result | `qualified`, transport `github-token`, cleanup `true` |
| Deleted probe ref | `refs/heads/nightly-bump-probe-43643834124-1-8aad84165517563d` |

The archive size and SHA-256 matched the authenticated Actions metadata. Its
sole bounded JSON member was parsed in memory without extraction and bound to
the source, run and attempt above. A separate `git ls-remote` confirmed no
`nightly-bump-probe-*` refs remain. Deleting the ref also removed the probe's
nested workflow from every live branch.

## Hosted delivery dispatch

A separate temporary main-only workflow invoked the production
`API.dispatch_delivery` with its own Actions-write job token. It did not run the
isolated probe or any release job. [Qualification run 43643836917](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/43643836917)
passed at source `6a7b287b7f2b40614970f10e3479c109f114d863`. Its strict HTTP 200 response
parser returned the authenticated run ID and canonical URLs for
[Delivery 43643848734](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/43643848734).
Independent Actions metadata confirmed event `workflow_dispatch`, branch main
and the same full source revision. Delivery was queued behind an already
running delivery when this evidence was collected; creation/trigger behavior is
the hosted assertion here, and its eventual result is reported separately.

The temporary `qualify-nightly-delivery.yml` workflow (ID 418652228) was disabled
with verified state `disabled_manually` after its successful run and its file
is removed by the qualification-cleanup commit. Production setup and delivered
refs remained empty. No hosted module CI or production adoption is claimed.
Real disposable module repositories exercise the producer/writer, repair-push,
authenticated report and first-result CI propagation paths in the locked
`test_bump_push.py` and `test_nightly_delivery_wait.py` suites.

## Findings resolved during qualification

The first probe at source `f7c76990342fcf87f719630da7a5b3b33264f893`
accepted the nested push but its artifact upload rejected a path containing
`..`. All seven nightly job directories now use canonical nonhidden siblings
outside checkout. The 21-test workflow suite checks all eight upload paths at
the action boundary.

The first dispatch proof at source
`d4b06d1215a9fe771b6338e81f548b1b72d2dc0f` created a delivery but
rejected its response because the client expected HTTP 204. The pinned
2026-03-10 API returns HTTP 200 with run details for dispatch; enable alone
returns empty HTTP 204. The corrected dispatch client shares release dispatch's
strict ID/URL validation, and malformed or uncertain writes are never retried.
See the [official workflow API contract](https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event).

## Conditional fallback

A future definite nested-path Workflows-permission rejection requires
`bump-push` in `cicd-app`, a fresh action-minted CiCd-only Contents/Workflows
write token, and the same verifier with `BUMP_TRANSPORT=app`. Its push triggers
delivery, so explicit dispatch is omitted. Pass that App token as `CICD_TOKEN`
and the same job's Actions-read GITHUB_TOKEN as `HANDOFF_TOKEN`; no credential
crosses jobs. Generic authorization, transport or uncertain-write errors leave
qualification incomplete and never justify selecting the fallback.
