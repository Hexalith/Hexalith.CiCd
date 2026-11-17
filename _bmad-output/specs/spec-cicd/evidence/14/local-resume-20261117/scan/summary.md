# Nightly cross-module duplicate scan: FAIL

Detector: jscpd 5.4.3. Cross-module copies belong in Builds.

- Hexalith.AI.Tools: pass; main `3a4a78d91b36849c4700e8bc9aae74a1b91f2fba`; 0 selected files
- Hexalith.Agents: pass; main `e98dab8c243286ceb8d0db8998caf3aad7f7b089`; 6 selected files
- Hexalith.Commons: pass; main `d551e5f3b67653b8793f86afedab355c8a3821da`; 4 selected files
- Hexalith.Conversations: fail; main `aa70df16fe70dc7ad907ec27bd693d59f9a96311`; 9 selected files
  - .github/actions/after-unit-tests/action.yml:11: local-script discovery: unsupported test runner with tracked module tests: unittest
  - .github/actions/after-unit-tests/action.yml:8: local-script discovery: unsupported test runner with tracked module tests: unittest
  - scripts/validate-built-packages.py:16: local-script discovery: unresolved computed subprocess cwd
  - scripts/validate-built-packages.py:27: local-script discovery: unresolved computed subprocess cwd
  - scripts/validate-consumer-package-references.py:198: local-script discovery: unresolved computed subprocess cwd
  - scripts/validate-consumer-package-references.py:56: local-script discovery: unresolved computed subprocess cwd
  - tests/compatibility/MinimalModule/run_compatibility.py:75: local-script discovery: unresolved computed subprocess cwd
- Hexalith.PolymorphicSerializations: pass; main `1f451a1ac5174b340f56763160f810d4a8364bb6`; 0 selected files

Coverage is incomplete; this result does not establish a clean scan.
