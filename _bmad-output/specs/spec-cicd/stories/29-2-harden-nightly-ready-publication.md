---
title: 'Harden nightly ready publication'
type: 'fix'
created: '2026-11-24'
status: draft
context: []
---

<intent-contract>

## Intent

Central Nightly completes a `ready` draft using the original build archive and
inventory verified by the exact successful target attempt. The maintainer
approved pre-write checks and immutable readback for the remaining work from
[Story 12](12-migrate-ai-tools.md#maintainer-acceptance--2026-11-24).

## Boundaries & Constraints

- Keep the central `publish-ready` job, scoped GitHub App access and pinned
  Builds finalizer. Package and container publication stay in the target run.
- Reuse the authenticated target-attempt artifact handoff. Keep App job
  artifact reads bounded and in memory under AD-7. Preserve older-source,
  GitHub-only and container-only completion.
- GitHub updates the release by ID. A concurrent change after the last
  pre-write check can be detected after an immutable release is created. Report
  the row as failed if readback observes a conflict or cannot verify the
  result. Send at most one publication request for the handoff. [GitHub release update API](https://docs.github.com/en/rest/releases/releases#update-a-release)

## Acceptance

- Given a successful `ready` attempt, when Nightly authenticates its evidence,
  then the original producer run, archive ID and digest, and verified package
  and container inventory match the selected draft and original artifact.
  The canonical `hexalith-package-publication.v1.json` asset matches the same
  identity and exact package IDs, including an empty list for container-only
  or GitHub-only releases.
- Given missing, malformed, or conflicting evidence, or a change to the attempt,
  marked draft, version tag, or asset observed before publication, when the
  finalizer checks the handoff, then the row fails without a publish PATCH.
- Given a publish request, when Nightly reads back the result, then it reports
  success only for the same verified attempt and immutable release ID, the same
  publication asset ID, size and digest, and a peeled version tag at the
  original source. A later observed mismatch or an unreadable result fails
  the row without a second write.

</intent-contract>

## Implementation & Verification

- [ ] In Builds `Github/lib/release_publish.py` and `Github/publish/action.yml`,
  expose the original archive identity and inventory already verified by the
  publisher in authenticated evidence tied to the exact `ready` attempt.
- [ ] In CiCd `tools/nightly.py`, `tools/nightly_publish.py`, and
  `tools/nightly_runtime.py`, authenticate that evidence, compare it with the
  draft and publication asset, and check the attempt and release through
  readback. Keep a compatible rollout between released Builds and CiCd.
- [ ] Extend the existing publication fixtures in
  `tools/tests/nightly_publish_cases.py` and the relevant Builds release tests.
  Cover a mismatched archive, a superseded attempt at the final asset read,
  and a conflict observable only after publication. Exercise package-bearing,
  container-only and GitHub-only inventories.
- [ ] Qualify one hosted package-bearing `ready` handoff through the central
  writer. Record the immutable Builds pin, exact run and attempt, original
  archive and publication asset identities and digests, and verified release
  and peeled tag. See the [Story 12 review](12-migrate-ai-tools.md#2026-11-24--hosted-acceptance-and-finalizer-re-review)
  for the reproduced race and archive verification gaps.
