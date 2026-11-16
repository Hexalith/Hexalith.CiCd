# Works package metadata authentication repair

Works' existing package preparation authenticates Platform's published Builds
producer against official GitHub metadata. The pinned legacy preparation steps
did not pass a token, so hosted jobs intermittently received HTTP403 from the
anonymous API rate limit. The failures are retained in Works
[CI43957823864](https://github.com/Hexalith/Hexalith.Works/actions/runs/43957823864)
and [CI43959004190](https://github.com/Hexalith/Hexalith.Works/actions/runs/43959004190).
This correction grants neither a green run nor publication authority.

The user requested SDK/package updates, CI repairs and release publication
without further human validation. This owner-side compatibility correction
preserves the existing product gates and changes no adoption configuration,
publication protection, package catalog or root Builds gitlink.

The isolated Builds compatibility commit
`3641d6226b4e6150a4ed43c472c97373378f3679` has exactly parent
`6ad5854aa14a9950e1fbfc32d7e27953a1c4b82b`. Its complete difference is four
`GH_TOKEN: ${{ github.token }}` environment entries, scoped to the three
`domain-ci.yml` package-preparation steps and the existing
`Github/prepare-domain-release/action.yml` preparation step. No current shared
pipeline behavior is imported into the frozen callers.

`tools/repair_works_package_metadata.py` prepares a closed proposal for exactly
the five existing Works CI, CodeQL, Commitlint, Dependency Review and Release
workflow files. It replaces their common approved execution SHA and supplies
the same token to the existing direct parity preparation step. All other bytes
are retained. The owner proposal records full input commit/tree, per-file
before/after Git blobs and SHA256s, result tree, exact compatible Builds commit
and binary patch digest. The materializer validates all targets before writing,
refuses staged/unstaged workflow changes, advanced source, adoption, altered
Builds scope and patch tampering, and leaves foreign files, index, refs and
commits untouched. It performs no remote action and uses no credential.

After committing this exact owner materializer, prepare from the settled Works
source and inspect the resulting patch:

```bash
run-with-temp python3 tools/repair_works_package_metadata.py prepare \
  --module /absolute/path/to/Works --builds /absolute/path/to/compatibility-Builds \
  --builds-execution 3641d6226b4e6150a4ed43c472c97373378f3679 \
  --proposal /absolute/path/to/new-proposal
```

Use the same command with `apply` after qualification. Apply from this CiCd
checkout; preserve the proposal and application receipt outside disposable
scratch. The existing Projects delivery profiles remain unchanged and closed.
The user-authorized maintainer publishes only the validated proposed workflow
changes with matching product-side execution constants. Exact-source hosted CI
and the normal release/package-publication checks remain required.

Focused qualification uses synthetic authority and real child processes; it
does not use or record a live token:

```bash
run-with-temp python3 tools/qualify_works_package_metadata.py \
  --builds /absolute/path/to/compatibility-Builds --report /absolute/path/to/report.json
run-with-temp python3 -m unittest discover -s tools/tests \
  -p test_repair_works_package_metadata.py -v
```

All four real legacy preparation commands pass with step-scoped synthetic
authority and fail without it. Six real-Git materializer cases cover exact
application, foreign edit/index/ref preservation, workflow edits, changed
source, patch tampering, unreviewed Builds source and adopted-module refusal.
Actionlint accepts the compatibility workflow. These results do not waive any
audit, test, source or release gate.
