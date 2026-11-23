---
title: 'Resolve five deferred CI/CD validation findings'
type: 'bugfix'
created: '2026-11-23'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

Close five open findings in the CiCd backlog. Select nightly release outcomes
from the current run attempt (DW-33), discover case variants of workflow YAML
extensions (DW-40), and document the existing forbidden paths and entries in
the generated ownership instructions (story 10-2 B4). Verify and record the
upstream repairs to the routing-snapshot fixture (DW-12) and the shared guide's
pre-push checker scope (story 10-2 B1).

</frozen-after-approval>

## Implementation Notes

- CiCd baseline `9e452b04505780d5483c25461340159560ccdb7d`. The App inventory
  policy binds the exact nightly controller bytes. The attempt filter changes
  outcome selection after dispatch and keeps the existing target and token rules.
- Timesheets release run 44421310299, attempt 2, started at
  `2026-11-18T23:45:47Z`. The run-wide API listed two unexpired
  `publication-verification` artifacts: 14481568753 at `23:37:54Z` and
  14482189561 at `23:45:58Z`. That upload predates the shared producer and
  omits the overwrite setting. Builds v6.6.2 uses `overwrite: true` for
  `hexalith-release-outcome`. The local fixture verifies defensive selection
  for that artifact name. [Hosted run](https://github.com/Hexalith/Hexalith.Timesheets/actions/runs/44421310299)
- Workflow discovery includes case variants of `.yml` and `.yaml` for
  App inventory and the explicit parent and rendered lint inputs. This change
  establishes the local validation policy. Pinned zizmor 1.32.0 requires
  lowercase extensions, so global lint reports each affected path. GitHub's
  execution behavior for uppercase extensions remains unverified.
- Builds `b74b467ac5ce5d9f9fc440f43e279b7093b539de` corrected the routing
  snapshot descriptor fixture. Blob `f07fa2cab376672b3d02c82867f6dd092b47f1ee`
  matches Builds main, pinned v6.6.2 at
  `2d9ef8b454ff897daca0149f3549844f584b634a` and the passing hosted
  source `2dc16bba3053c1efc871a221a4e782a8c3da72ab`.
  [Hosted job](https://github.com/Hexalith/Hexalith.Builds/actions/runs/43519435001/job/132209687921)
- The checker scope was corrected upstream in AI.Tools
  `736687b79c1e4fa8beabdab75c4675bb76c466b9`. Main at
  `0cb4b837ebcb1607b6cae14d180606efadc7ca6d` retains that wording in
  guide blob `2cda6714f426cb5c419d3b15d28a20e57dd7b039`.
- The seven rendered perimeter manifests contain the new ownership text.
  Their enforcement selectors are identical to the baseline.
- The reviewed nightly source is
  `d509d01f7fbc636075a82fa489d08bad0924cc94`.
  Its controller SHA-256 is
  `0b2a40887544255b8fdd851d0d9b39111277288b44d84305b7a983ff9897876d`.
- The locked suites passed: 49 nightly, 52 renderer, 20 App inventory and 21
  global validation tests. The nightly rerun, perimeter and lint-entry tests
  also passed after review. The render check found no drift.
- Builds v6.6.2 commitlint accepted the two exact messages with SHA-256
  `cdac16d38b0cc228e5ff0908c06a76f53e53eac28b84d78ab6bff9359f60cc8c` and
  `5474bd07e562f7f21432099eb42955f66b6acefc0f736bd66bd3943eb488bbc9`.
  The Node CLI loader refused the ESM config, so verification used the pinned
  lint API with the same parser, rules and plugin. It rejected a skip-marker
  control. The environment could not complete npm signature downloads.

## Review Triage Log

- Medium, fixed. The pinned linter rejects uppercase extensions. Global lint
  now identifies every affected path before collection, and its entry point is
  tested with both extensions.
- Low, fixed. The inventory already requires lowercase for reviewed paths.
  Documented this rule and tested refusal for a case-variant privileged file.
- Low, declined. A dot-only name such as `.YML` has no extension under the
  path-suffix semantics used by CiCd and zizmor.
- Medium, fixed. The hosted evidence and local fixture describe the distinct
  legacy upload and shared overwrite modes.
- Medium, deferred. The baseline terminal error path can miss an attempt
  change during an artifact read failure. The backlog records the follow-up.
- Medium, fixed. The regression now gives the two attempts distinct starts
  and places the previous artifact between them.
- Low, fixed. Documented which forbidden patterns are root-relative.
- Low, fixed. Named the four dependency sections from the perimeter manifest.
- Low, fixed. Included the exact recursive response-file and agent-tooling globs.
- Low, fixed. The render test checks the documented top-level JSON keys.
- Low, declined. The shared timestamp diagnostic already refuses malformed
  input. Field-specific wording would add separate exception handling.
