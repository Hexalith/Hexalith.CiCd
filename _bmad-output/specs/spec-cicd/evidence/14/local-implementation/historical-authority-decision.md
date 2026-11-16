# Exact exclusion amendment — approved

The human approved this six-path proposal with "approve" on 2026-11-16.
`approved-exclusions.json` records the exact applied inventory, original and
updated exclusion-file hashes, and unchanged historical-source hashes. The
original failure and proposal below are retained as the decision's evidence.

The whole-repository authority check fails on the following tracked historical
projects while using the exact approved `eng/package-authority-exclusions.txt`.
The failed ordered sequence is preserved in `full-suite-failed-authority.json`
and its log. No test or exclusion was changed to hide this failure.

The proposed narrow decision is to add only these exact historical paths to the
existing exclusion file, after confirming they are frozen foreign/source-proof
snapshots outside the Agents product/consumer graph. Do not exclude a directory,
glob, live source/test project, or product check. Keep the whole-repository shared
validator and all existing exclusions unchanged otherwise. Then rerun the full
ordered suites at their original floors. An alternative decision is to repair or
retire the recorded evidence sources; that also requires explicit authorization.

The current spec requires the exact existing exclusions and preservation of
foreign content, so neither decision is authorized by this implementation run.

There are 81 reported errors across 6 exact project paths.

- `_bmad-output/implementation-artifacts/tests/deferred-state-dependencies-2026-11-16/coordinator-final-dependencies/platform/catalog/20261116T134852Z-668b8b128a6b4ff098a9ce224c0649ed/artifacts/platform-components/catalog-reader/Hexalith.Platform.CatalogBuilder.csproj` — stale-absolute-import.
- `_bmad-output/implementation-artifacts/tests/deferred-state-dependencies-2026-11-16/coordinator-final-dependencies/platform/local-inputs/Hexalith.Platform/src/Hexalith.Platform.Composition/Hexalith.Platform.Composition.csproj` — foreign-catalog-mismatch.
- `_bmad-output/implementation-artifacts/tests/deferred-state-dependencies-2026-11-16/platform-corrected/platform/catalog/20261116T123849Z-724c847ff7be495aacb4b30f5f9942c3/artifacts/platform-components/catalog-reader/Hexalith.Platform.CatalogBuilder.csproj` — stale-absolute-import.
- `_bmad-output/implementation-artifacts/tests/deferred-state-dependencies-2026-11-16/platform-corrected/platform/local-inputs/Hexalith.Platform/src/Hexalith.Platform.Composition/Hexalith.Platform.Composition.csproj` — foreign-catalog-mismatch.
- `_bmad-output/implementation-artifacts/tests/deferred-state-dependencies-2026-11-16/platform-final-correction/platform/catalog/20261116T124513Z-deb728e7995344b9a55088ff50964492/artifacts/platform-components/catalog-reader/Hexalith.Platform.CatalogBuilder.csproj` — stale-absolute-import.
- `_bmad-output/implementation-artifacts/tests/deferred-state-dependencies-2026-11-16/platform-final-correction/platform/local-inputs/Hexalith.Platform/src/Hexalith.Platform.Composition/Hexalith.Platform.Composition.csproj` — foreign-catalog-mismatch.

`stale-absolute-import` means a checked-in probe imports a disposable path from
an earlier job, which no longer exists. `foreign-catalog-mismatch` means a frozen
Platform project is evaluated against a different compatibility catalog view.
The JSON companion preserves every exact diagnostic and its project mapping.
This is an approval proposal only; it grants no release, push or adoption proof.
