# Nightly cross-module duplicate scan: FAIL

Detector: jscpd 5.4.3. Cross-module copies belong in Builds.

- Hexalith.Agents: pass; main `c5c22620cafaa0af2625896cf41022e614e9b490`; 6 selected files
- Hexalith.Commons: fail; main `49187d47da882d5470deac982bb383486c90202c`; 4 selected files
  - .github/actions/after-unit-tests/action.yml:10: local-script discovery: unresolved computed operand of unknown command: rm
  - .github/actions/after-unit-tests/action.yml:9: local-script discovery: unsupported shell command substitution
  - scripts/pack-release-packages.py:47: local-script discovery: unresolved computed subprocess env
  - scripts/validate-consumer-package-references.py:159: local-script discovery: unresolved computed subprocess cwd
- Hexalith.PolymorphicSerializations: pass; main `2cbec6a66e2174adc7c5d431c1b1f0d28abd5647`; 0 selected files

Coverage is incomplete; this result does not establish a clean scan.
