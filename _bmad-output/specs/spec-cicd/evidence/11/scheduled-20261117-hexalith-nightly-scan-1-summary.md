# Nightly cross-module duplicate scan: FAIL

Detector: jscpd 5.4.3. Cross-module copies belong in Builds.

- Hexalith.AI.Tools: pass; main `3a4a78d91b36849c4700e8bc9aae74a1b91f2fba`; 0 selected files
- Hexalith.Commons: fail; main `aa694ae3d43f1645f741ae0844987ca2e7e0d347`; 4 selected files
  - .github/actions/after-unit-tests/action.yml:10: local-script discovery: unresolved computed operand of unknown command: rm
  - .github/actions/after-unit-tests/action.yml:9: local-script discovery: unsupported shell command substitution
  - scripts/pack-release-packages.py:47: local-script discovery: unresolved computed subprocess env
  - scripts/validate-consumer-package-references.py:159: local-script discovery: unresolved computed subprocess cwd
- Hexalith.Conversations: fail; main `6f1f2ea05466982e013a782b5c79cfab0ecb0e26`; 9 selected files
  - .github/actions/after-unit-tests/action.yml:11: local-script discovery: unsupported test runner with tracked module tests: unittest
  - .github/actions/after-unit-tests/action.yml:8: local-script discovery: unsupported test runner with tracked module tests: unittest
  - scripts/validate-built-packages.py:16: local-script discovery: unresolved computed subprocess cwd
  - scripts/validate-built-packages.py:27: local-script discovery: unresolved computed subprocess cwd
  - scripts/validate-consumer-package-references.py:198: local-script discovery: unresolved computed subprocess cwd
  - scripts/validate-consumer-package-references.py:56: local-script discovery: unresolved computed subprocess cwd
  - tests/compatibility/MinimalModule/run_compatibility.py:75: local-script discovery: unresolved computed subprocess cwd
- Hexalith.PolymorphicSerializations: pass; main `1f451a1ac5174b340f56763160f810d4a8364bb6`; 0 selected files

Coverage is incomplete; this result does not establish a clean scan.
