# Push all changes to main

Publication is blocked by immutable Builds v6.1.0 released audit policy on the fresh Platform preparation tree.

The audit rejects `MSBuildWarningsAsMessages`, `NuGetAuditSuppress` and `VSTestTestCaseFilter` in the unchanged historical `graph-export-imports.xml` recorded in [result.json](result.json). The candidate is based on fresh Platform main and preserves owned content. Folders passes this audit, but its pending product correction depends on the unpublished Platform fixture.

The applicable approved preparation procedure requires all policy and product checks to pass. Its submodule-first rule blocks a parent commit until every changed module is published and authenticated remotely. No commit or push was performed; pending shared work and indexes were preserved. Full product qualification was not run after this mandatory policy refusal. No audit/test/protection rule or credential was changed.
