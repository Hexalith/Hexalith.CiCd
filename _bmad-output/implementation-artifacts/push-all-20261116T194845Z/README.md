# Push-all verification result

Publication remains blocked under the existing Projects preparation approval.
The normal adoption checker refusal was recorded separately; it is not the
reason for this attempt's refusal.

Passing checks: complete Release/package build, all eight Projects test projects
(2878 tests), real package consumers, 33 owning support tests, one PostgreSQL
runtime test, 20 package-tool regressions, nine browser-configuration tests,
released/owning commitlint, unchanged owned perimeter, CiCd render check,
35 renderer tests, 52 validation tests and 11 Tenants preflight tests.

Remaining failures:

- `npm run test:package`: the loaded owner differs from the selected executable
  artifact. The fixture's identity assertion remains intact.
- Released audit lint: 12 forbidden policy declarations in archived evidence.
  The fresh-main and candidate findings match exactly; no audit rule or archive
  was changed to obtain a pass.

See [result.json](result.json), [released audit findings](projects-released-audit.json)
and [commit/perimeter proof](preparation-policy.json). Full useful logs are saved
beside this document. Every verification child finished and run-with-temp removed
its disposable workspaces. This attempt made no source edits, commits or pushes.
