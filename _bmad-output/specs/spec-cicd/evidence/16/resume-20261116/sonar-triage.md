# Supporting Builds security-check triage

The external check reports Security E / Reliability C against a new-code period
starting 2026-07-09. It includes older and concurrent work, so it is not evidence
that all findings originated in story 16. No finding was suppressed, marked
accepted or removed from a quality gate.

At source `fa6dc2864ac65c6244b111fa9ecc5e7a78722e3e`:

- `module_preparation.py`, S8707, issue `AaHl5MqBAsyMT0ogpN0o`:
  `_inputs` checks the actual clean root/identity and rejects symlink/reparse
  input paths and paths outside the module. `_real` validates the supplied scratch
  directory; `mkdtemp` creates the private output directory. Producer invocation
  uses an argument list. The reviewed flow has no demonstrated traversal bypass;
  the scanner's taint report still needs a security disposition.
  A subsequent contract check found that scratch spellings containing `..` or
  control characters were accepted by the old helper. This narrow refusal gap
  is fixed in `27e8fba9736a4825d44c40c638c5e6f9b65ab81e`, before fetching or
  creating output. The [before/after proof](path-guard-baseline-proof.json) and
  [152-case regression receipt](path-guard-verification-final.json) record it.
  This fix does not assert that the scanner's report has been cleared.
- `qualification_tools.py`, S2083 at its staged-file writes: `read_manifest`
  restricts names to the closed separator-free `NAME` pattern. Archive bytes are
  read through an exact regular member without extraction. Writes use exclusive
  creation inside a fresh private directory validated outside the repository.
  No demonstrated traversal bypass was found in this flow.
- `perimeter.py`, S5850: the right alternative intentionally anchors the final
  unterminated physical-LF record at EOF. The other alternative consumes a
  terminated record. The existing preservation test exercises CR and Unicode
  separators as data, so replacing this with Unicode-aware `splitlines` would
  alter the ownership semantics.

Existing producer-preparation, qualification-tool and perimeter controls were
executed separately; see [their receipt](sonar-triage-controls.json). These tests
support the reviewed guards. They do not clear the external check or establish
the safety of the remaining findings in other files.
